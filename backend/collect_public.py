#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公共場館「客製格式」展覽收集器（非池中比對發現、文化部未收錄、且官網結構特殊者）。
與 collect_venues.py 分開，因為這幾站需要各自的日期/篩選解析：
  - 新竹市美術館：新竹市文化局「活動資訊」表格，民國年日期（115-05-26＝2026），用 [展覽] 標籤過濾。
  - 關渡美術館：當期展覽卡片（標準 2026.04.16～2026.06.14 日期）；換展期間可能無資料，屆時自動回空。
  - 臺灣當代文化實驗場 C-LAB：最新活動列表，依「展覽」類型標籤過濾，日期格式 06.06 (六) 2026 . 06.14 (日) 2026。

輸出：併入 venue_extra.json（與 collect_venues.py 相同格式），refresh_venues.py 會接手定位/分類/合併。
用法：python3 collect_public.py            # 跑全部
      python3 collect_public.py 新竹市美術館 # 只跑單站
可重複、可定期：update_all.py 會在 collect_venues 之後呼叫本檔。
相依：playwright（同 collect_venues）。
"""
import json, re, os, sys, datetime
from paths import path as P
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUTP = P("venue_extra.json")
TODAY = datetime.date.today().strftime("%Y/%m/%d")
def log(*a): print(*a, file=sys.stderr)

# 場館基本資訊（座標取自 OpenStreetMap POI，與 refresh_venues.py 的 ANCHORS 一致）
VENUES = {
 "新竹市美術館": {"city":"新竹市","lat":24.80638,"lng":120.96968,
   "url":"https://culture.hccg.gov.tw/ch/home.jsp?id=154&parentpath=0,145",
   "list":"https://culture.hccg.gov.tw/ch/home.jsp?id=452&parentpath=0,145,154"},
 "關渡美術館": {"city":"台北市","lat":25.13345,"lng":121.4715,
   "url":"https://kdmofa.tnua.edu.tw",
   "list":"https://kdmofa.tnua.edu.tw/mod/exhibition/index.php"},
 "臺灣當代文化實驗場 C-LAB": {"city":"台北市","lat":25.03957,"lng":121.53975,
   "url":"https://clab.org.tw",
   "list":"https://clab.org.tw/events/?event_category=exhibition"},   # 只列「展覽」類
}

def fmt(y, m, d): return f"{int(y):04d}/{int(m):02d}/{int(d):02d}"

def parse_roc_range(text):
    """民國年區間：115-05-26~115-08-02 → (2026/05/26, 2026/08/02)。"""
    ds = re.findall(r'(\d{2,3})-(\d{1,2})-(\d{1,2})', text or "")
    out = []
    for y, m, d in ds:
        yy = int(y) + 1911 if int(y) < 1000 else int(y)
        out.append(fmt(yy, m, d))
    if len(out) >= 2: return out[0], out[1]
    if len(out) == 1: return out[0], ""
    return "", ""

def parse_dot_range(text):
    """標準：2026.04.16～2026.06.14（或 - ~ 至）。"""
    t = (text or "").replace("～", "~").replace("－", "-")
    ds = re.findall(r'(20\d{2})[.\-/](\d{1,2})[.\-/](\d{1,2})', t)
    if len(ds) >= 2: return fmt(*ds[0]), fmt(*ds[1])
    if len(ds) == 1: return fmt(*ds[0]), ""
    return "", ""

def parse_clab_range(text):
    """C-LAB：06.06 (六) 2026 . 06.14 (日) 2026 → 年在後、含星期。"""
    pairs = re.findall(r'(\d{1,2})\.(\d{1,2})\s*\([^)]*\)\s*(20\d{2})', text or "")
    out = [fmt(y, m, d) for (m, d, y) in pairs]
    if len(out) >= 2: return out[0], out[1]
    if len(out) == 1: return out[0], ""
    return "", ""

def _keep(s, e):
    """當期或即將開展：尚未結束（end 空視為長期/未定，保留）。"""
    return (not e) or (e >= TODAY)

def collect_hsinchu(pg, v):
    # 文化局「活動資訊」非 <table>，是 div 列表；含 [展覽] 的連結即展覽，日期在上層容器（民國年）
    pg.goto(v["list"], wait_until="domcontentloaded", timeout=40000); pg.wait_for_timeout(2000)
    items = pg.eval_on_selector_all("a", """els=>els.filter(a=>/\\[展覽\\]/.test(a.innerText||'')).map(a=>{
        let row=a, n=a;
        for(let i=0;i<5;i++){ n=n.parentElement; if(!n)break; if(/\\d{2,3}-\\d{1,2}-\\d{1,2}/.test(n.innerText||'')){ row=n; break; } }
        return {t:(a.innerText||'').trim(), h:a.href, row:(row.innerText||'').replace(/\\s+/g,' ').trim()};
    })""")
    exs = []; seen = set()
    for it in items:
        s, e = parse_roc_range(it["row"])      # 前兩個民國日期＝展期（第三個是發布日，忽略）
        if not (s or e) or not _keep(s, e): continue
        title = re.sub(r'^\s*(\[[^\]]{1,6}\]\s*)+', '', it["t"]).strip().strip("《》<>「」").strip()
        if len(re.sub(r'[^\w一-鿿]', '', title)) < 3 or it["h"] in seen: continue
        seen.add(it["h"]); exs.append({"t": title[:70], "s": s, "e": e, "l": it["h"], "img": ""})
    return exs

def collect_kdmofa(pg, v):
    pg.goto(v["list"], wait_until="networkidle", timeout=40000); pg.wait_for_timeout(2500)
    for _ in range(3): pg.mouse.wheel(0, 2000); pg.wait_for_timeout(400)
    cards = pg.eval_on_selector_all("a[href*='mod/exhibition/index.php?REQUEST_ID=']", """els=>els.map(a=>{
        const box=a.closest('li,article,.item,.card,div')||a;
        return {t:(a.innerText||'').trim(), h:a.href, bx:(box.innerText||'').replace(/\\s+/g,' ').trim()};
    })""")
    exs = []; seen = set()
    for c in cards:
        t0 = c["t"].split("\n")[0].strip()      # 卡片連結首行＝展名（其後行為日期）
        if re.search(r'歷年|當期|網站導覽|簡介|紀事|館長|交通|設備|志工|實習|隱私|條款', t0): continue
        if len(t0) < 4 or c["h"] in seen: continue
        s, e = parse_dot_range(c["t"] + " " + c["bx"])
        if not (s or e) or not _keep(s, e): continue
        seen.add(c["h"]); exs.append({"t": t0[:70], "s": s, "e": e, "l": c["h"], "img": ""})
    return exs

def collect_clab(pg, v):
    # 用 ?event_category=exhibition 預先過濾「展覽」類，無需再判類型標籤；卡片連結首行＝展名
    pg.goto(v["list"], wait_until="domcontentloaded", timeout=40000); pg.wait_for_timeout(3000)
    for _ in range(4): pg.mouse.wheel(0, 2200); pg.wait_for_timeout(450)
    cards = pg.eval_on_selector_all("a[href*='/events/']",
        "els=>els.map(a=>({h:a.href, t:(a.innerText||'').trim()})).filter(x=>/\\/events\\/[^?]/.test(x.h))")
    # 同一展覽有多個同 href 連結（圖片/標題/日期），合併後再取標題與日期
    groups = {}
    for c in cards: groups.setdefault(c["h"], []).append(c["t"])
    exs = []
    for h, texts in groups.items():
        full = " ".join(texts)
        s, e = parse_clab_range(full)                            # 06.06 (六) 2026 . 06.14 (日) 2026
        if not (s or e) or not _keep(s, e): continue
        # 標題：取「不含日期、最長」的變體（即標題連結），排除日期/類型標籤變體
        cands = [t for t in texts if t and not re.search(r'\d{1,2}\.\d{1,2}', t)
                 and t != "展覽" and len(re.sub(r'[^\w一-鿿]', '', t)) >= 3]
        if not cands: continue
        best = max(cands, key=len)
        title = next((l.strip() for l in best.split("\n") if l.strip()), "")  # 標題連結首行＝展名（次行為場地）
        if len(re.sub(r'[^\w一-鿿]', '', title)) < 3: continue
        exs.append({"t": title[:70], "s": s, "e": e, "l": h, "img": ""})
    return exs

HANDLERS = {"新竹市美術館": collect_hsinchu, "關渡美術館": collect_kdmofa, "臺灣當代文化實驗場 C-LAB": collect_clab}

def run_one(pg, key):
    v = VENUES[key]; fn = HANDLERS[key]
    try:
        exs = fn(pg, v)
    except Exception as e:
        log(f"ERR  {key} {type(e).__name__}: {str(e)[:80]}"); return None
    return {key: {"city": v["city"], "lat": v["lat"], "lng": v["lng"], "url": v["url"], "ex": exs}}

def main(only=None):
    out = json.load(open(OUTP, encoding="utf-8")) if os.path.exists(OUTP) else {}
    keys = [only] if only else list(VENUES.keys())
    with sync_playwright() as p:
        b = p.chromium.launch()
        for key in keys:
            pg = b.new_context(viewport={"width":1400,"height":1800}).new_page()
            data = run_one(pg, key)
            pg.context.close()
            if data is not None:
                if data[key].get("ex"):
                    out.update(data)
                    log(f"OK   {key}: {len(data[key]['ex'])} 展覽")
                else:
                    out.pop(key, None)
                    log(f"MISS {key}（已清除舊資料，可能換展中或無當期展覽）")
                json.dump(out, open(OUTP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            else:
                log(f"MISS {key}（保留舊資料：抓取錯誤）")
        b.close()

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) == 2 else None)
