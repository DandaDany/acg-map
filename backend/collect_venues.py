#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
場館官網展覽收集器（補文化部開放資料缺漏，達成各館「完整當期展覽」）

設定驅動：要新增一個場館，只要在 VENUES 加一組設定即可：
  key   場館顯示名稱（需與 anchor/資料中的名稱一致才會被合併取代）
  city/lat/lng/url   基本資訊
  list  展覽列表頁網址
  path  展覽連結 href 需包含的字串（用來辨識哪些連結是展覽）
  exclude（選填）額外排除的標題/連結關鍵字（如導覽列、活動）

流程：Playwright 渲染列表頁 → 取展覽連結與文字 → 去除日期時間得標題、解析起迄日 →
      逐一抓詳情頁 og:image 當主視覺(KV) → 輸出 venue_extra.json。
可重複、可定期更新：直接重跑 `python3 collect_venues.py` 即可。

相依：pip install playwright ; python3 -m playwright install chromium
"""
import json, re, os, sys, tempfile, time, urllib.request
from paths import path as P
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
def log(*a): print(*a, file=sys.stderr)
TODAY = date.today().strftime("%Y/%m/%d")

def load_json_retry(path, default, tries=5, delay=0.6):
    if not os.path.exists(path):
        return default
    last = None
    for i in range(tries):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except OSError as e:
            last = e
            if i == tries - 1:
                break
            log(f"WARN read retry {i+1}/{tries} {os.path.basename(path)}: {e}")
            time.sleep(delay * (i + 1))
    raise last

def dump_json_atomic(obj, path):
    folder = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(prefix=os.path.basename(path) + ".", suffix=".tmp", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass

# 2026/07/12：依決策「官網只保留六大文創園區/特區」（華山、松山、圓山花博、駁二、嘉義文創、
# 花蓮文創）——這些場館常辦 ACG 快閃/聯名展，ACG 命中率高。純美術館/博物館（國美館、北美館、
# 故宮、奇美、臺南美、關渡、纖維工藝、港區藝術中心、蕭壠、傳藝宜蘭、新北美術館、采泥、MoNTUE 等）
# 及 collect_public.py（新竹/關渡/C-LAB）、collect_soka_art.py（索卡）已停止收錄。
VENUES = [
 {"key":"華山1914文化創意產業園區","city":"台北市","lat":25.0440,"lng":121.5292,
  "url":"https://www.huashan1914.com","list":"https://www.huashan1914.com/w/huashan1914/exhibition",
  "path":"exhibition_","exclude":r"(攻略|市集|好市|論壇|講座)"},
 {"key":"松山文創園區","city":"台北市","lat":25.0438,"lng":121.5606,
  "url":"https://www.songshanculturalpark.org","list":"https://www.songshanculturalpark.org/exhibition",
  "path":"/exhibition/activity/","exclude":r"(攻略|課程|培力|例大祭)"},
 {"key":"高雄市駁二藝術特區","city":"高雄市","lat":22.6203,"lng":120.2820,
  "url":"https://www.pier2.org","list":"https://pier2.org/exhibition/list/all/",
  "path":"/exhibition/info/","exclude":r"","kv":"content"},
 {"key":"嘉義文化創意產業園區","city":"嘉義市","lat":23.4790,"lng":120.4490,"url":"https://www.g9cip.com","list":"https://www.g9cip.com/activity/exhibitions/","path":"auto","exclude":r"(名單|公告|得獎|徵件|徵選|報名|招標|研習)"},
 {"key":"花蓮文化創意產業園區","city":"花蓮縣","lat":23.9760,"lng":121.6090,"url":"https://hualien1913.nat.gov.tw","list":"https://hualien1913.nat.gov.tw/%e6%9c%80%e6%96%b0%e6%b4%bb%e5%8b%95/","path":"auto","exclude":r"(講座|工作坊|論壇|課程|徵件)"},  # 2026/07/18 check-sources.yml 實測：GitHub Actions 雲端連此網域回 403（本機/一般網路正常），故在雲端排程排除，見 CLOUD_EXCLUDE_KEYS
 {"key":"圓山花博","city":"台北市","lat":25.0703595,"lng":121.5204969,
  "url":"https://www.expopark.taipei","list":"https://www.expopark.taipei/News_Exhibition.aspx?n=247&sms=9029&page=1&PageSize=100",
  "path":"News_Photo_Content.aspx","type_include":r"展覽活動","drop_past_start_without_end":True,
  "exclude":r"(講座|工作坊|論壇|課程|徵件)"},
]
GLOBAL_EXCLUDE = re.compile(r"(news/article|門票|售票|常見問題|交通資訊)")

# 2026/07/18：check-sources.yml 實測 GitHub Actions 雲端機器連 hualien1913.nat.gov.tw 回 403
# （其餘 7 個來源皆 200，含另一個政府網域 expopark.taipei）。研判是該政府網站對雲端機房 IP
# 的防火牆/WAF 阻擋，非程式問題。Daniel 確認：雲端排程排除此館即可，不用等它連上再研究繞過方案。
# 只在雲端（GitHub Actions 會自動設環境變數 GITHUB_ACTIONS=true）跳過；本機手動執行 update_all.py
# 時仍會照常嘗試抓這一館（若 Daniel 之後想在本機補這一館資料）。
CLOUD_EXCLUDE_KEYS = {"花蓮文化創意產業園區"}

_DATELINE = re.compile(r'^[\s\d:．.\-~/年月日上下午APMapm()]+$')
def strip_dt(text):
    """去除日期與時間 token，留下標題。"""
    t = re.sub(r'20\d{2}[.\-/]\d{1,2}[.\-/]\d{1,2}', ' ', text)
    t = re.sub(r'\b\d{1,2}:\d{2}\b', ' ', t)
    t = re.sub(r'\b[AaPp]\.?[Mm]\b', ' ', t)            # AM/PM
    t = re.sub(r'[-~｜|]+\s*$', '', t)
    return re.sub(r'\s+', ' ', t).strip(' -~｜|')

def _dedup(t):
    t = t.strip()
    parts = t.split()
    if len(parts) >= 2 and len(parts) % 2 == 0 and parts[:len(parts)//2] == parts[len(parts)//2:]:
        return ' '.join(parts[:len(parts)//2])
    n = len(t)
    if n >= 6 and n % 2 == 0 and t[:n//2] == t[n//2:]:
        return t[:n//2]
    return t

# 純分類標籤詞：某些場館（如華山）卡片會把「期間限定店／展演活動／品牌活動」等分類
# 標籤獨立成行，且常比真正展名更長，導致「取最長行」誤抓。整行都是這些詞就排除。
_TAGWORDS = {"期間限定店","期間限定","快閃店","快閃","展演活動","品牌活動","市集",
             "講座","課程","表演","活動","工作坊","論壇","體驗","免費","售票","展演"}
def _is_tagline(line):
    toks = [t for t in re.split(r'[\s,、/｜|]+', line) if t]
    return bool(toks) and all(t in _TAGWORDS for t in toks)

def extract_title(text):
    """多行：排除純分類標籤行後取最長行；單行/blob：切掉日期說明標籤後段，去重複。"""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    nondate = [l for l in lines if not _DATELINE.match(l)]
    cand_lines = [l for l in nondate if not _is_tagline(l)] or nondate
    cand = max(cand_lines, key=len) if (len(lines) > 1 and cand_lines) else text
    # 切掉「展覽日期/展期/展覽時間/展覽地點/展區/策展人…」及其後說明
    cand = re.split(r'(展覽日期|展\s*期|展覽時間|展覽地點|展出地點|展\s*區|策\s*展\s*人|地\s*址|日期[：:｜|])', cand)[0]
    cand = _dedup(strip_dt(cand)).strip()
    # 台灣展名常用「」『』《》括起；若標題開頭有引號且後面還有一堆說明，取引號內為標題
    m = re.match(r'^\s*([「『《][^」』》]{3,48}[」』》])(.+)', cand)
    if m and len(m.group(2)) > 4:
        cand = m.group(1)
    return cand.strip()

def parse_dates(text):
    # 正規化「2026年03月28日至2026年06月28日」「~ ～ 至」等格式
    text = (text or "").replace("年","/").replace("月","/").replace("日","").replace("至","-").replace("～","-").replace("~","-")
    def fmt(y, m, d):
        y = int(y)
        if 90 <= y < 1911:  # 民國年，例如 115-07-25
            y += 1911
        return f"{y}/{int(m):02d}/{int(d):02d}"
    m = re.search(r'((?:20)?\d{2,3})[.\-/](\d{1,2})[.\-/](\d{1,2})\s*[-~]\s*(\d{1,2})[.\-/](\d{1,2})(?![.\-/\d])', text)
    if m:
        y,mo,d,em,ed = m.groups(); return fmt(y,mo,d), fmt(y,em,ed)
    ds = re.findall(r'((?:20)?\d{2,3})[.\-/](\d{1,2})[.\-/](\d{1,2})', text)
    if len(ds) >= 2: return fmt(*ds[0]), fmt(*ds[1])
    if len(ds) == 1: return fmt(*ds[0]), ""
    return "", ""

def og_image(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as r:
            html = r.read(200000).decode("utf-8","ignore"); base=r.geturl()
        bm = re.search(r'<base[^>]+href=["\']([^"\']+)', html, re.I)
        if bm and bm.group(1).strip():
            base = urljoin(base, bm.group(1).strip())
        for p in [r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
                  r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)']:
            m = re.search(p, html, re.I)
            if m and m.group(1).strip():
                img = urljoin(base, m.group(1).strip())
                if not re.search(r'(og_img|logo|favicon)', img, re.I):
                    return img
        best = ""
        best_score = 0
        for tag in re.findall(r'<img[^>]+>', html, re.I):
            m = re.search(r'(?:src|data-src)=["\']([^"\']+)', tag, re.I)
            if not m:
                continue
            img = urljoin(base, m.group(1).strip())
            if not re.search(r'\.(jpg|jpeg|png|webp)(\?|$)', img, re.I):
                continue
            if re.search(r'(logo|favicon|icon|foot_)', img, re.I):
                continue
            score = 100
            if "uploads/" in img:
                score += 500
            for attr in ("width", "height"):
                mm = re.search(attr + r'=["\']?(\d+)', tag, re.I)
                if mm:
                    score += int(mm.group(1))
            if score > best_score:
                best_score = score
                best = img
        if best:
            return best
    except Exception:
        pass
    return ""

def content_image(url):
    """進活動詳情頁，抓內文區塊 <div id="thecontent"> 內的第一張 <img> 作為主視覺。
    駁二等站的列表縮圖是同一張模糊 KV，改用詳情頁內文首圖才是各活動真正的主視覺。"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read(400000).decode("utf-8", "ignore"); base = r.geturl()
        bm = re.search(r'<base[^>]+href=["\']([^"\']+)', html, re.I)
        if bm and bm.group(1).strip():
            base = urljoin(base, bm.group(1).strip())
        # 取 id="thecontent" 之後、到該區塊結束前的內容；內文只有 <p>，無巢狀 <div>，取第一個 </div> 即可
        m = re.search(r'id=["\']thecontent["\'][^>]*>(.*?)</div>', html, re.I | re.S)
        block = m.group(1) if m else html
        im = re.search(r'<img[^>]+src=["\']([^"\']+)', block, re.I)
        if im and im.group(1).strip():
            img = urljoin(base, im.group(1).strip())
            if re.search(r'\.(jpg|jpeg|png|webp)(\?|$)', img, re.I):
                return img
    except Exception:
        pass
    return ""

# 常見「下一頁」控制項選擇器（涵蓋 a/button、rel=next、aria-label、符號箭頭）
_NEXT_SELECTORS = [
    'a[rel="next"]',
    'a:has-text("下一頁")', 'button:has-text("下一頁")',
    'a:has-text("下一页")', 'button:has-text("下一页")',
    '[aria-label*="下一"]', '[aria-label*="next" i]',
    'li.next:not(.disabled) a', 'a.next:not(.disabled)',
    '.pagination .next:not(.disabled) a', '.pager .next:not(.disabled) a',
    'a:has-text("›")', 'a:has-text("»")', 'a:has-text("Next")',
]

def _click_next(pg):
    """找到並點擊「下一頁」控制項；成功回傳 True。會略過隱藏／停用／已標 disabled 者。
    通用、保守：找不到可用的下一頁就回傳 False（讓呼叫端停止翻頁）。"""
    for sel in _NEXT_SELECTORS:
        try:
            el = pg.query_selector(sel)
        except Exception:
            el = None
        if not el:
            continue
        try:
            if not el.is_visible() or not el.is_enabled():
                continue
            cls = (el.get_attribute("class") or "").lower()
            if "disabled" in cls or (el.get_attribute("aria-disabled") or "") == "true":
                continue
            el.scroll_into_view_if_needed(timeout=2000)
            el.click(timeout=4000)
            return True
        except Exception:
            continue
    return False

def collect_one(pg, v):
    exclude = re.compile(v["exclude"]) if v.get("exclude") else None
    _JS = """(pathkey)=>{
      const auto = (pathkey==='auto');
      const seen=new Set(), out=[];
      const fromImg=(im)=>im?(im.currentSrc||im.src||im.getAttribute('data-src')||im.getAttribute('data-original')||''):'';
      const fromBg=(box)=>{ if(!box) return ''; for(const c of [box,...box.querySelectorAll('*')]){ const bg=getComputedStyle(c).backgroundImage; const m=bg&&bg.match(/url\\(["']?([^"')]+)/); if(m && /\\.(jpg|jpeg|png|webp)/i.test(m[1])) return m[1]; } return ''; };
      document.querySelectorAll('a').forEach(a=>{
        const href=a.href||''; const txt=(a.innerText||'').trim();
        const title=(a.getAttribute('title')||txt).trim();
        if(auto){ if(!/(展|個展|聯展|特展|典藏)/.test(title+' '+txt)) return; }
        else { if(href.indexOf(pathkey)<0) return; }
        if((title||txt).length<8) return;
        if(seen.has(href)) return; seen.add(href);
        const box=a.closest('li,article,.card,.item,.box')||a.parentElement||a;
        let img=fromImg(a.querySelector('img')||box.querySelector('img'));
        if(!img) img=fromBg(box);
        const boxtxt=(box.innerText||'').replace(/\\s+/g,' ').slice(0,220);
        out.push({txt:title||txt, href, img, boxtxt});
      });
      return out;
    }"""
    urls = v["list"] if isinstance(v["list"], list) else [v["list"]]
    items = []; _seen = set()
    MAX_PAGES = 15   # 翻頁上限，防無窮迴圈
    for _u in urls:
        pg.goto(_u, wait_until="domcontentloaded", timeout=40000)
        try:
            # 有些館（如北美館／北師美術館／新北市美術館）清單是 AJAX 動態載入，
            # domcontentloaded 當下 DOM 裡還沒有任何展覽項目；多等網路閒置一下再抓，
            # 已經很快的站這段幾乎立刻就過，不會拖慢整體。
            pg.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        pg.wait_for_timeout(1200)
        for _page in range(MAX_PAGES):
            for _ in range(5):
                pg.mouse.wheel(0, 2200); pg.wait_for_timeout(450)
            pg.wait_for_timeout(500)
            before = len(_seen)
            for it in pg.evaluate(_JS, v["path"]):
                if it["href"] in _seen: continue
                _seen.add(it["href"]); items.append(it)
            added = len(_seen) - before
            if _page > 0 and added == 0:
                break                       # 這頁沒有新項目 → 視為已到最後一頁
            if not _click_next(pg):
                break                       # 沒有「下一頁」控制項 → 停止
            pg.wait_for_timeout(1500)       # 等 AJAX/換頁載入
    exs=[]; seen_t=set()
    type_include = re.compile(v["type_include"]) if v.get("type_include") else None
    for it in items:
        if GLOBAL_EXCLUDE.search(it["href"]): continue
        if type_include and not type_include.search(it["txt"] + " " + it.get("boxtxt", "")): continue
        title = extract_title(it["txt"])
        # 去除前綴標籤 [ 售票 ] / 【免票】 等
        for _ in range(2):
            title = re.sub(r'^\s*[\[\(（【][^\]\)）】]{0,8}[\]\)）】]\s*', '', title).strip()
        # 丟棄純標點/過短、或週次時段片段
        cjk_alnum = re.sub(r'[^\w一-鿿]', '', title)
        if len(cjk_alnum) < 3: continue
        if re.match(r'^[周週][一二三四五六日]', title): continue
        if exclude and exclude.search(title): continue
        if title in seen_t: continue
        seen_t.add(title)
        s,e = parse_dates(it["txt"] + " " + it.get("boxtxt",""))   # 日期可能在卡片容器、非連結文字
        if v.get("drop_past_start_without_end") and s and not e and s < TODAY:
            continue
        if v["path"]=="auto" and not (s or e): continue   # auto 模式：沒日期視為非展覽，丟棄
        img = it.get("img","") or ""
        if img.startswith("//"): img = "https:" + img
        if v.get("kv") == "content": img = ""   # 忽略列表縮圖（駁二列表縮圖是同一張模糊 KV），改抓詳情頁內文首圖
        exs.append({"t":title[:70],"s":s,"e":e,"l":it["href"],"img":img,"ty":"special"})
    if v.get("kv") == "content":
        # 內文首圖為 JS 動態注入（#thecontent 於載入後才填入），需用瀏覽器渲染後取第一張 <img>；
        # 靜態抓不到時退回 content_image()/og:image。逐頁走訪（駁二活動數不多，序列化即可）。
        for r in exs:
            src = ""
            try:
                pg.goto(r["l"], wait_until="domcontentloaded", timeout=40000)
                try: pg.wait_for_selector('#thecontent img', timeout=8000)
                except Exception: pass
                src = pg.evaluate("()=>{const i=document.querySelector('#thecontent img');return i?i.src:'';}") or ""
            except Exception:
                src = ""
            r["img"] = src or content_image(r["l"]) or og_image(r["l"])
    else:
        # 列表頁無縮圖者，退而抓詳情頁 og:image
        miss = [r for r in exs if not r["img"]]
        if miss:
            with ThreadPoolExecutor(max_workers=8) as ex:
                for r,img in zip(miss, ex.map(lambda r: og_image(r["l"]), miss)): r["img"]=img
    return exs

OUTP = P("venue_extra.json")

def run_single(key):
    """單站模式：處理一個場館，印出 JSON {key: data}。崩潰只影響這一站。"""
    import subprocess  # noqa
    v = next((x for x in VENUES if x["key"] == key), None)
    if not v: print("{}"); return
    with sync_playwright() as p:
        b=p.chromium.launch(); pg=b.new_context(viewport={"width":1366,"height":1500}).new_page()
        exs=collect_one(pg, v); b.close()
    print(json.dumps({v["key"]:{"city":v["city"],"lat":v["lat"],"lng":v["lng"],"url":v["url"],"ex":exs}}, ensure_ascii=False))

def _run_site(key, timeout=90):
    """以獨立 process group 跑「單站模式」子程序；逾時則連同 Playwright 啟動的
    Chromium 子孫程序一併強制終結，避免子孫程序占住 pipe 造成主流程卡死。
    回傳 (stdout 文字, status, stderr 文字)；status ∈ {'ok', 'timeout'}。可重複呼叫、可續跑。"""
    p = subprocess.Popen(
        [sys.executable, __file__, key],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        start_new_session=True,   # 另開 process group，逾時可整組終結
    )
    try:
        stdout, stderr = p.communicate(timeout=timeout)
        return stdout, "ok", stderr
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)  # 殺整個 group（含 Chromium）
        except (ProcessLookupError, PermissionError):
            pass
        stderr = ""
        try:
            _, stderr = p.communicate(timeout=10)
        except Exception:
            pass
        return "", "timeout", stderr

def _err_tail(stderr):
    """從子程序 stderr 取最後一行非空內容（通常是例外訊息本身），截斷避免洗版 log。"""
    lines = [l for l in (stderr or "").splitlines() if l.strip()]
    return lines[-1].strip()[:200] if lines else ""

def main():
    """主控：逐站以獨立 process group 子程序處理，即時寫檔。
    單站逾時會連同 Chromium 子孫程序一併終結，不會卡住整體流程。
    成功抓到空結果時會清掉該館舊資料；逾時/解析錯誤則保留舊資料。"""
    out = load_json_retry(OUTP, {})
    is_cloud = os.environ.get("GITHUB_ACTIONS") == "true"
    for v in VENUES:
        if is_cloud and v["key"] in CLOUD_EXCLUDE_KEYS:
            log(f"SKIP {v['key']}（雲端排除：check-sources.yml 2026/07/18 實測連線 403，保留舊資料，僅本機執行才會嘗試更新）")
            continue
        stdout, status, stderr = _run_site(v["key"], timeout=90)
        if status == "timeout":
            tail = _err_tail(stderr)
            log(f"TIMEOUT {v['key']}（保留舊資料）" + (f"：{tail}" if tail else ""))
            continue
        try:
            line = [l for l in (stdout or "").splitlines() if l.startswith("{")]
            data = json.loads(line[-1]) if line else {}
        except Exception as e:
            tail = _err_tail(stderr)
            log(f"ERR  {v['key']} {type(e).__name__}（保留舊資料）" + (f"：{tail}" if tail else ""))
            continue
        if data and v["key"] in data:
            if data[v["key"]].get("ex"):
                out.update(data)
                log(f"OK   {v['key']}: {len(out[v['key']]['ex'])} 展覽")
            else:
                log(f"MISS {v['key']}（保留舊資料：空結果）")
            dump_json_atomic(out, OUTP)
        else:
            tail = _err_tail(stderr)
            log(f"MISS {v['key']}（保留舊資料：未取得有效回應）" + (f"：{tail}" if tail else ""))
    print(json.dumps({k:len(v["ex"]) for k,v in out.items()}, ensure_ascii=False))

import subprocess, signal
if __name__=="__main__":
    if len(sys.argv)==2: run_single(sys.argv[1])
    else: main()
