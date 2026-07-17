#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全台展覽地圖 — 資料更新管線
重跑即可產生最新 venues.json（資料來源：文化部開放資料 藝文活動-展覽 category=6）

功能：
  1. 抓文化部展覽資料、篩當期。
  2. 有座標者用原值（精確）；無座標者用地址解析到鄉鎮中心（區級）/縣市中心（市級）。
  3. 逐一驗證官方連結是否可連通；抓該頁 og:image 當展覽圖片；修正文化部重複黏接的壞圖網址。
  4. 併入重點館 / 文創園區（已驗證官網）。
  5. 輸出 venues.json。

相依：同目錄 town_centroids.json
快取：同目錄 enrich_cache.json（連結→{ok,img}），加速重跑；新連結才會重抓。
用法：python3 refresh_venues.py
"""
import json, re, hashlib, urllib.request, datetime, os, sys, ssl, html
from paths import path as P
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor

# 部分政府網站（如文化部 API）的憑證鏈缺少 Subject Key Identifier 欄位，
# 在新版 OpenSSL 3.x 的嚴格 RFC 5280 檢查下會被拒（CERTIFICATE_VERIFY_FAILED:
# Missing Subject Key Identifier）。此處只關閉「結構嚴格檢查」這一道旗標，
# 仍保留完整的 CA 信任鏈與主機名驗證（自簽/錯誤憑證仍會被擋）。
# 清掉未設定的旗標為無作用，故在舊版 OpenSSL／其他平台上同樣安全可重複執行。
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.verify_flags &= ~ssl.VERIFY_X509_STRICT
ssl._create_default_https_context = lambda *a, **k: _SSL_CTX

HERE = os.path.dirname(os.path.abspath(__file__))
# 2026/07/12：停用文化部（政府）API，不再收錄 moc 層（政府資料對公開端 ACG 幾乎無貢獻、
# 只增加後台雜訊與稽核成本）。若日後要恢復政府來源，改回 USE_MOC = True 即可。
USE_MOC = False
API = "https://cloud.culture.tw/frontsite/trans/SearchShowAction.do?method=doFindTypeJ&category=6"

def _norm_title(t):
    """正規化活動標題（去空白、轉小寫）供跨場館去重比對。"""
    return re.sub(r'\s+', '', (t or '')).lower()
TODAY = datetime.date.today().strftime("%Y/%m/%d")
CACHE = P("enrich_cache_v3.json")

def log(*a): print(*a, file=sys.stderr)
def s(v):
    if isinstance(v, list): return " ".join(str(x) for x in v if x).strip()
    return (v or "").strip()
def norm(x): return (x or "").replace("臺", "台").strip()
def valid(la, lo):
    try:
        la = float(la); lo = float(lo); return 21 < la < 26.6 and 118 < lo < 122.5
    except: return False
def fixurl(u):
    u = (u or "").strip()
    m = [x.start() for x in re.finditer(r'https?://', u)]
    if len(m) > 1: u = u[m[-1]:]   # 取最後一個 http(s):// 起，修重複黏接
    return u
def is_home(u):
    try:
        path = urlparse(u).path.strip("/")
        return 1 if (path == "" or path.lower() in ("index.html","index.php","home","default.aspx","ch","zh-tw")) else 0
    except: return 0
def bad_link(u):
    u = (u or "").strip().lower()
    return (not u) or u.startswith(("javascript:", "mailto:", "tel:")) or u in ("#", "/#")

def compact_title(text):
    text = html.unescape(norm(text or "")).lower()
    text = re.sub(r"(展覽名稱|活動名稱|展覽|常設展覽|常設展|特展|當期展覽|線上展覽)", "", text)
    return re.sub(r"[^0-9a-z一-鿿]+", "", text)

def title_matches(a, b):
    ca, cb = compact_title(a), compact_title(b)
    if not ca or not cb:
        return False
    if ca == cb or ca in cb or cb in ca:
        return min(len(ca), len(cb)) >= 4
    return False

def strip_html(text):
    text = re.sub(r"<script\b.*?</script>|<style\b.*?</style>", " ", text or "", flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()

def fetch_html(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=18) as r:
        data = r.read(600000)
        base = r.geturl()
    return data.decode("utf-8", "ignore"), base

def source_candidates(source):
    url = source.get("url", "")
    if not url:
        return []
    try:
        body, base = fetch_html(url)
    except Exception as e:
        log("官方展覽頁讀取失敗:", url, e)
        return []
    out = []
    for m in re.finditer(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", body, re.I | re.S):
        raw_href = html.unescape(m.group(1).strip())
        if bad_link(raw_href):
            continue
        href = urljoin(base, raw_href)
        if bad_link(href):
            continue
        text = strip_html(m.group(2))
        if len(compact_title(text)) < 4:
            continue
        out.append({"title": text, "url": href})
    return out

def apply_event_sources(venues):
    path = P("venue_event_sources.json")
    if not os.path.exists(path):
        return
    try:
        sources = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        log("官方展覽來源表讀取失敗:", e)
        return
    applied = 0
    for v in venues:
        cfg = sources.get(v["name"])
        if not cfg:
            continue
        candidates = []
        for src in cfg.get("sources", []):
            candidates.extend(source_candidates(src))
        fallbacks = cfg.get("fallbacks", [])
        for e in v.get("ex", []):
            if e.get("l") and not bad_link(e.get("l")):
                continue
            title = e.get("t", "")
            hit = next((c for c in candidates if title_matches(title, c.get("title", ""))), None)
            if not hit:
                for fb in fallbacks:
                    pats = fb.get("title_patterns", [])
                    if any(re.search(p, title) for p in pats):
                        hit = {"url": fb.get("url", "")}
                        break
            if hit and hit.get("url") and not bad_link(hit.get("url")):
                e["l"] = hit["url"]
                e["h"] = is_home(e["l"])
                applied += 1
    if applied:
        log("套用官方展覽來源:", applied, "筆")

def apply_event_kv_cache(venues):
    path = P("event_kv_cache.json")
    if not os.path.exists(path):
        return
    try:
        cache = json.load(open(path, encoding="utf-8")).get("links", {})
    except Exception as e:
        log("活動 KV 快取讀取失敗:", e)
        return
    applied = 0
    for v in venues:
        for e in v.get("ex", []):
            if e.get("img") or not e.get("l"):
                continue
            rec = cache.get(e.get("l", ""))
            img = rec.get("img", "") if isinstance(rec, dict) else ""
            if img:
                e["img"] = img
                applied += 1
    if applied:
        log("套用活動 KV 快取:", applied, "筆")

# 文化部原始 locationName 有時是「西區（臺中市）=」這類雜訊；改用主辦單位等較可靠來源
def _name_is_bad(loc):
    loc = (loc or "").strip()
    if not loc: return True
    if loc.endswith("=") or loc.endswith("＝"): return True
    if re.match(r'^[^（]{1,6}(區|鄉|鎮|市)（[^）]+）[=＝]?$', loc): return True
    return False
def venue_name(loc, master):
    loc = (loc or "").strip()
    if _name_is_bad(loc):
        m = re.sub(r'^\(中華民國\)', '', (master or "").strip())
        m = re.split(r'[、,;|]', m)[0].strip()
        if m and not re.match(r'^[^（]{1,6}(區|鄉|鎮|市)（', m):
            return m
        loc2 = re.sub(r'（[^）]+）', '', loc).rstrip('=＝ ').strip()
        return loc2 or "未具名場地"
    return loc.rstrip('=＝ ').strip()

CITY = r'(台北市|臺北市|新北市|桃園市|台中市|臺中市|台南市|臺南市|高雄市|基隆市|新竹市|新竹縣|苗栗縣|彰化縣|南投縣|雲林縣|嘉義市|嘉義縣|屏東縣|宜蘭縣|花蓮縣|台東縣|臺東縣|澎湖縣|金門縣|連江縣)'
TOWN = re.compile(CITY + r'([一-龥]{1,3}[區鄉鎮市])')
CITYRE = re.compile(CITY)
CITY_BOUNDS = {
    '台北市': (24.9, 25.25, 121.43, 121.68), '新北市': (24.65, 25.35, 121.25, 122.05),
    '基隆市': (25.05, 25.2, 121.65, 121.85), '桃園市': (24.55, 25.15, 120.95, 121.5),
    '新竹市': (24.72, 24.88, 120.88, 121.05), '新竹縣': (24.35, 24.95, 120.9, 121.35),
    '苗栗縣': (24.25, 24.75, 120.55, 121.2), '台中市': (23.95, 24.45, 120.45, 121.45),
    '彰化縣': (23.78, 24.18, 120.25, 120.65), '南投縣': (23.45, 24.35, 120.55, 121.35),
    '雲林縣': (23.45, 23.9, 120.1, 120.75), '嘉義市': (23.43, 23.53, 120.38, 120.5),
    '嘉義縣': (23.2, 23.65, 120.1, 120.8), '台南市': (22.85, 23.45, 120.0, 120.65),
    '高雄市': (22.45, 23.35, 120.15, 121.05), '屏東縣': (21.85, 22.9, 120.4, 120.95),
    '宜蘭縣': (24.25, 25.05, 121.45, 122.05), '花蓮縣': (23.0, 24.4, 121.1, 121.8),
    '台東縣': (21.9, 23.5, 120.7, 121.6), '澎湖縣': (23.1, 23.9, 119.2, 119.8),
    '金門縣': (24.35, 24.55, 118.1, 118.55), '連江縣': (25.9, 26.4, 119.8, 120.6),
}
def coord_matches_city(city, la, lo):
    b = CITY_BOUNDS.get(norm(city))
    if not b: return True
    return b[0] <= float(la) <= b[1] and b[2] <= float(lo) <= b[3]

# 圖片黑名單（會過期/短網址logo/內部）與 logo 檔名，避免顯示錯誤或失效圖片
IMG_BLACK = re.compile(r'(fbcdn\.net|reurl\.cc|bit\.ly|lihi|pse\.is|/data-service|googletagmanager|gravatar)', re.I)
IMG_LOGO = re.compile(r'(logo|toplogo|/og\.(jpg|png)|default|banner_?top|header)', re.I)
IMGCACHE = P("imgcache_v3.json")
def img_bad_host(u):
    h = re.sub(r'^https?://', '', u).split('/')[0]
    return ('.' not in h)
def validate_images(cands):
    """只保留：非黑名單/logo/內部、且實際回傳 image 型別、>2.5KB 的圖片。結果快取。"""
    cache = json.load(open(IMGCACHE, encoding="utf-8")) if os.path.exists(IMGCACHE) else {}
    pre = [u for u in cands if u.startswith("http") and not IMG_BLACK.search(u) and not IMG_LOGO.search(u) and not img_bad_host(u)]
    todo = [u for u in pre if u not in cache]
    log("圖片候選:", len(cands), "｜過濾後:", len(pre), "｜待驗:", len(todo))
    def one(u):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                ct = (r.headers.get("Content-Type", "") or "").lower(); data = r.read(60000)
            return u, (r.status == 200 and ct.startswith("image") and len(data) > 2500)
        except Exception:
            return u, False
    if todo:
        with ThreadPoolExecutor(max_workers=14) as ex:
            for u, ok in ex.map(one, todo): cache[u] = ok
        json.dump(cache, open(IMGCACHE, "w", encoding="utf-8"), ensure_ascii=False)
    return {u for u in pre if cache.get(u)}

# 2026/07/12：停政府 API＋官網只留六大園區後，ANCHORS 精簡為「保留園區」的座標錨；
# 移除純美術館/博物館的常設卡（故宮、北美館、國美館、高美館、臺南美、奇美、關渡、新竹市美術館、
# 當代館、鳳甲、臺博、MoNTUE）與未保留園區（文資園區、蕭壠、C-LAB）。
# 六大園區中 駁二／圓山花博 的座標由 collect_venues.py 提供，不需在此設錨。
ANCHORS = [
 ('華山1914文化創意產業園區','台北市',25.0440,121.5292,'https://www.huashan1914.com',False),
 ('松山文創園區','台北市',25.0438,121.5606,'https://www.songshanculturalpark.org',False),
 ('嘉義文化創意產業園區','嘉義市',23.4790,120.4490,'https://www.g9cip.com',False),
 ('花蓮文化創意產業園區','花蓮縣',23.9760,121.6090,'https://hualien1913.nat.gov.tw',False),
]

# 7 類精簡分類：混合法（展名關鍵字優先，場館類型打底，無法判斷→其他/綜合）
# 動漫遊戲(ACG) 置於最前、最高優先：含通用詞與常見授權 IP 名；英文以 (?i) 不分大小寫。
CAT_TITLE = [
    ('動漫遊戲(ACG)', r'(?i)動漫|動畫|漫畫|二次元|電玩|電競|電子遊戲|手遊|桌遊|公仔|同人誌?|聲優|cosplay|角色扮演|特攝|鋼彈|機甲|寶可夢|Pok[eé]mon|哆啦|蠟筆小新|鬼滅|航海王|海賊王|火影|吉卜力|宮崎駿|角落生物|角落小夥伴|拉拉熊|好想兔|咖波|貓貓蟲|三麗鷗|Sanrio|凱蒂貓|Hello ?Kitty|布丁狗|美樂蒂|庫洛米|CHIIKAWA|吉伊卡哇|PEANUTS|SNOOPY|史努比|OSAMU|迪士尼|Disney|數碼寶貝|麵包超人|海綿寶寶|LINE ?FRIENDS|熊大|漫威|Marvel|蜘蛛人|全知讀者|webtoon|網漫|卡通|Anime'),
    ('親子兒童', r'親子|兒童|童趣|繪本|玩具'),
    ('科學自然', r'科學|自然|生態|天文|地質|礦物|恐龍|科技|海洋|動物|植物|宇宙|氣候|標本|昆蟲|地球|國家公園|環境教育|濕地|生物多樣'),
    ('工藝設計', r'工藝|陶藝|陶瓷|玻璃|竹編|漆藝|金工|設計|文創|手作|編織|捏麵|纖維|木雕|藍染|刺繡|樂器|傳統藝術'),
    ('歷史人文', r'歷史|文物|史蹟|史前|民俗|宗教|考古|文獻|古蹟|信仰|戶籍|老照片|族群|地方|村史|文學|客家|原住民|原民|故居|故事館|文化資產|遺產|世界遺產|代天府|宗祠|沉船'),
    ('視覺藝術', r'畫|繪|攝影|書法|書畫|水墨|雕塑|版畫|油畫|膠彩|當代|個展|聯展|藝術|影像|創作|寫真|美術|典藏|臨書'),
]
CAT_VENUE = [
    ('視覺藝術', r'美術館|藝廊|畫廊|當代館|MoNTUE|藝術館'),
    ('科學自然', r'科學|科博|自然|天文|海洋生物|海生|動物園|國家公園'),
    ('工藝設計', r'工藝|陶瓷|玻璃|文創|設計|傳統藝術'),
    ('歷史人文', r'歷史|文物|史前|民俗|紀念館|文學館|文獻|客家|原住民|故事館|故居|文化資產'),
]
def classify(title, venue):
    for name, pat in CAT_TITLE:
        if re.search(pat, title or ''): return name
    for name, pat in CAT_VENUE:
        if re.search(pat, venue or ''): return name
    return '其他/綜合'

# ── 新兩軸分類（軸A主題 × 軸B形式）──────────────────────────────────────
# 軸B形式的四個最終值。Excel「活動類別 / Activity Category」欄若直接寫這四個詞，就照用（你的選擇優先）。
FORM_VALUES = ('展覽', '快閃店', '主題餐廳', '體驗活動')
EXCEL_CAT2_MAP = {
    '快閃': '快閃店', 'pop': '快閃店', '展覽': '展覽', 'exhibition': '展覽',
    '餐廳': '主題餐廳', 'cafe': '主題餐廳', '活動': '體驗活動', '音樂會': '體驗活動',
}
def map_excel_cat2(raw):
    """讀 Excel 形式欄：直接寫最終形式 → 照用；舊模糊寫法 → 對應；空白/看不懂 → 回落 classify_form 自動判斷。"""
    raw = (raw or '').strip()
    if raw in FORM_VALUES:              # 你在 Excel 直接指定最終形式，優先於自動判斷
        return raw
    raw_l = raw.lower()
    for k, v in EXCEL_CAT2_MAP.items():  # 舊的模糊寫法（快閃/餐廳/活動…）仍相容
        if k in raw_l: return v
    return ''                            # 空白或無法對應 → 交給 classify_form 自動判斷

FORM_KW = [
    ('快閃店',   r'(?i)快閃|POP\s*-?\s*UP|期間限定|限定店|主題店'),
    ('主題餐廳', r'(?i)主題餐廳|咖啡|café|cafe|茶會|主題餐'),
    ('體驗活動', r'解謎|實境|主題日|音樂會|交響|嘉年華|市集|水舞|花火'),
    ('展覽',     r'展'),
]
def classify_form(title, venue=''):
    for name, pat in FORM_KW:
        if re.search(pat, title or ''): return name
    return '其他'

THEME_ACG_KW = r'(?i)動漫|動畫|漫畫|聲優|Vtuber|遊戲|角色|IP|航海王|鬼滅|咒術|三麗鷗|Chiikawa|吉伊卡哇|寶可夢|Pok[eé]mon|哆啦|蠟筆小新|迪士尼|Disney|Sanrio|Hello\s*Kitty|布丁狗|美樂蒂|庫洛米|史努比|SNOOPY|PEANUTS|麵包超人|漫威|Marvel|卡通|Anime|ACG'
THEME_ART_KW  = r'美術|畫展|攝影|設計|工藝|陶|書法|雕塑'
def classify_theme_kw(title, venue=''):
    if re.search(THEME_ACG_KW, title or '') or re.search(THEME_ACG_KW, venue or ''):
        return 'ACG'
    if re.search(THEME_ART_KW, title or '') or re.search(THEME_ART_KW, venue or ''):
        return '藝術設計'
    return '其他文化'

def fetch_api():
    req = urllib.request.Request(API, headers={"User-Agent": "tw-exhibition-map/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    if not raw.strip():
        log("⚠️ 文化部 API 回傳空回應，視為 0 筆。")
        return []
    return json.loads(raw.decode("utf-8"))

def enrich_links(urls):
    cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
    todo = [u for u in urls if u not in cache]
    log("連結總數:", len(urls), "｜已快取:", len(cache), "｜待抓:", len(todo))
    _LOGO = re.compile(r'(logo|icon|sprite|/og\.(jpg|png)|toplogo|favicon|banner_?top|header_|btn_|_btn)', re.I)
    _BLACK = re.compile(r'(reurl\.cc/asset|fbcdn|/data-service|googletagmanager|gravatar)', re.I)
    def extract_kv(html, base):
        # 1) meta 主視覺
        for p in [r'<meta[^>]+property=["\']og:image:secure_url["\'][^>]+content=["\']([^"\']+)',
                  r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
                  r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image',
                  r'<meta[^>]+name=["\']twitter:image(?::src)?["\'][^>]+content=["\']([^"\']+)',
                  r'<link[^>]+rel=["\']image_src["\'][^>]+href=["\']([^"\']+)']:
            m = re.search(p, html, re.I)
            if m and m.group(1).strip() and not self_logo(m.group(1)):
                return urljoin(base, m.group(1).strip())
        m = re.search(r'"image"\s*:\s*"([^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"', html, re.I)
        if m and not self_logo(m.group(1)):
            return urljoin(base, m.group(1).strip())
        # 2) 內文最大張圖（爬頁面內容，挑主視覺）
        best = None; bestscore = 0
        for im in re.finditer(r'<img[^>]+>', html, re.I):
            tag = im.group(0); src = re.search(r'src=["\']([^"\']+)', tag)
            if not src: continue
            u = src.group(1)
            if not re.search(r'\.(jpg|jpeg|png|webp)', u, re.I): continue
            if self_logo(u): continue
            score = 0
            w = re.search(r'width=["\']?(\d+)', tag); h = re.search(r'height=["\']?(\d+)', tag)
            if w: score += int(w.group(1))
            if h: score += int(h.group(1))
            if re.search(r'(upload|exhibition|poster|kv|cover|news|activity|files)', u, re.I): score += 400
            if score > bestscore: bestscore = score; best = urljoin(base, u)
        return best if (best and bestscore >= 400) else ""
    def self_logo(u):
        return bool(_LOGO.search(u) or _BLACK.search(u))
    def one(u):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (compatible; ExhibitionMap/1.0)"})
            with urllib.request.urlopen(req, timeout=10) as r:
                code = r.status; html = r.read(400000).decode("utf-8", "ignore"); base = r.geturl()
            return u, {"ok": True, "code": code, "img": extract_kv(html, base)}
        except Exception as e:
            return u, {"ok": False, "code": type(e).__name__, "img": ""}
    if todo:
        with ThreadPoolExecutor(max_workers=12) as ex:
            for u, res in ex.map(one, todo): cache[u] = res
        json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    return cache

# ---- 審核決策持久層（data/manual/review_decisions.json）----
# 每日自動更新開 PR 供使用者審核；使用者「刪掉」的活動記在 rejected 名單，
# 之後每次輸出 venues.json 前都以穩定鍵過濾，避免同一活動下次又冒出來。
# 穩定鍵 = 場館名 + 正規化後活動標題 + 開始日（YYYY-MM-DD），以 "|" 串接。

_KEY_PUNCT = ("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
              "！＂＃＄％＆＇（）＊＋，－．／：；＜＝＞？＠［＼］＾＿｀｛｜｝～"
              "。、；：？！…—–─·・「」『』《》〈〉【】〔〕“”‘’〝〟﹏～　 ")


def _norm_key_text(text):
    """穩定鍵用正規化：strip、全形空白→半形並壓縮、去除前後標點、臺→台。"""
    text = norm(str(text or ""))
    text = text.replace("　", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text.strip(_KEY_PUNCT)


def stable_event_key(venue_name, title, start):
    """產生活動穩定鍵：場館名|正規化標題|開始日（日期統一為 YYYY-MM-DD）。"""
    date = str(start or "").strip().replace("/", "-")
    return f"{_norm_key_text(venue_name)}|{_norm_key_text(title)}|{date}"


def load_rejected_keys():
    """讀 review_decisions.json 的 rejected 名單，回傳穩定鍵集合；檔案缺失/壞掉時回空集合（不擋管線）。"""
    path = P("review_decisions.json")
    if not os.path.exists(path):
        return set()
    try:
        data = json.load(open(path, encoding="utf-8"))
    except Exception as err:
        log("review_decisions.json 讀取失敗（略過過濾）:", err)
        return set()
    keys = set()
    rejected = data.get("rejected") if isinstance(data, dict) else None
    for item in rejected or []:
        if isinstance(item, dict) and item.get("key"):
            keys.add(str(item["key"]).strip())
    return keys


def filter_rejected_events(venues, rejected_keys):
    """輸出前過濾：穩定鍵在 rejected 名單的活動不輸出；ex 被清空的場館一併移除。

    不改任何既有欄位，只縮減 ex 清單（additive、可回退：清空 rejected 即完全還原）。
    """
    if not rejected_keys:
        return venues
    removed = 0
    for v in venues:
        kept = []
        for e in v.get("ex", []):
            if stable_event_key(v.get("name", ""), e.get("t", ""), e.get("s", "")) in rejected_keys:
                removed += 1
            else:
                kept.append(e)
        v["ex"] = kept
    out = [v for v in venues if v.get("ex")]
    log("審核決策過濾: 依 rejected 名單移除", removed, "場活動｜移除空場館", len(venues) - len(out), "個")
    return out


def main():
    from collections import defaultdict, Counter
    cent = {tuple(k.split("|")): tuple(v) for k, v in
            json.load(open(P("town_centroids.json"), encoding="utf-8")).items()}
    citycent = defaultdict(list)
    for (c, t), (la, lo) in cent.items(): citycent[c].append((la, lo))
    citycent = {c: (round(sum(x[0] for x in v)/len(v), 5), round(sum(x[1] for x in v)/len(v), 5)) for c, v in citycent.items()}

    def jitter(name, amp=0.012):
        h = int(hashlib.md5(name.encode()).hexdigest(), 16)
        return ((h % 1000)/1000-0.5)*2*amp, (((h//1000) % 1000)/1000-0.5)*2*amp
    def locate(addr, vname):
        m = TOWN.search(addr or "")
        if m:
            key = (norm(m.group(1)), norm(m.group(2)))
            if key in cent:
                la, lo = cent[key]; dx, dy = jitter(vname); return (round(la+dy,5), round(lo+dx,5), '區級', key[0])
        m2 = CITYRE.search(addr or "")
        if m2:
            c = norm(m2.group(1))
            if c in citycent:
                la, lo = citycent[c]; dx, dy = jitter(vname, 0.03); return (round(la+dy,5), round(lo+dx,5), '市級', c)
        return None
    def cityof(addr):
        m = CITYRE.search(addr or ""); return norm(m.group(1)) if m else ""
    def clean_addr(a):
        # 去開頭郵遞區號、臺→台正規化；保留縣市+區+路段+號等完整資訊
        return re.sub(r'^\s*\d{3,6}\s*', '', (a or '').strip()).replace('臺', '台')
    def best_addr(addrs):
        # 從同場館多個來源地址中，挑「含路/街/段/號且最完整」者；皆無則回空字串（不杜撰）
        cand = [clean_addr(a) for a in addrs if a and a.strip()]
        if not cand: return ''
        cand.sort(key=lambda x: (1 if re.search(r'[路街道段巷弄號]', x) else 0, len(x)), reverse=True)
        return cand[0]
    def city_from_coord(la, lo):
        try:
            la = float(la); lo = float(lo)
        except Exception:
            return ''
        best = None
        for (c, _t), (cla, clo) in cent.items():
            d = (float(cla) - la) ** 2 + (float(clo) - lo) ** 2
            if best is None or d < best[0]:
                best = (d, c)
        return best[1] if best else ''

    if USE_MOC:
        log("下載文化部展覽資料…")
        d = fetch_api(); log("總筆數:", len(d))
        _moc_api_ok = len(d) >= 200   # 正常情況應 200 筆以上；不足視為 API 異常
        if not _moc_api_ok:
            log(f"⚠️ 文化部 API 回傳 {len(d)} 筆，遠低於正常（>=200），API 可能暫時異常；moc 層改用前次快取。")
    else:
        log("文化部 API 已停用（USE_MOC=False）：跳過政府層，不收錄 moc 資料。")
        d = []
        _moc_api_ok = True   # 視為正常，避免觸發下方 moc 快照補填把政府資料救回來
    cur = [r for r in d if not (s(r.get("endDate")) and s(r.get("endDate")) < TODAY)]

    raw = []; linkset = set()
    for r in cur:
        link = fixurl(s(r.get("sourceWebPromote")) or s(r.get("webSales")))
        oimg = fixurl(s(r.get("imageUrl")))
        raw.append((r, link, oimg))
        if link: linkset.add(link)
    cache = enrich_links(linkset)

    exact = defaultdict(list); approx = defaultdict(list)
    for r, link, oimg in raw:
        info = cache.get(link, {})
        good_link = link if (link and info.get("ok")) else ""
        img = oimg if (oimg.startswith("http") and oimg.count("http") == 1) else (info.get("img", "") if good_link else "")
        rec = {'t': r['title'].strip(), 's': s(r.get('startDate')), 'e': s(r.get('endDate')),
               'l': good_link, 'img': img, 'ty': 'special'}
        if good_link: rec['h'] = is_home(good_link)
        coord = None; addr = None; name = None
        for sh in (r.get('showInfo') or []):
            if valid(sh.get('latitude'), sh.get('longitude')):
                cand_addr = s(sh.get('location'))
                cand_city = cityof(cand_addr)
                if cand_city and not coord_matches_city(cand_city, float(sh['latitude']), float(sh['longitude'])):
                    continue
                coord = (float(sh['latitude']), float(sh['longitude'])); name = s(sh.get('locationName')); addr = cand_addr; break
        if not coord:
            for sh in (r.get('showInfo') or []):
                if s(sh.get('location')): addr = s(sh.get('location')); name = s(sh.get('locationName')); break
        if not name: name = s(r.get('showUnit')).replace('(中華民國)', '') or '未具名場地'
        name = venue_name(name, s(r.get('masterUnit')))
        if coord:
            exact[(round(coord[0],3), round(coord[1],3))].append((rec, name, addr))
        else:
            loc = locate(addr, name)
            if not loc: continue
            la, lo, prec, city = loc; approx[(city, name)].append((rec, la, lo, prec, addr))

    venues = []
    for (la, lo), items in exact.items():
        _a = best_addr([x[2] for x in items])
        vrec = {'name': Counter(x[1] for x in items).most_common(1)[0][0], 'city': cityof(items[0][2]),
                'la': round(la,5), 'lo': round(lo,5), 'loc': 'exact', 'src': 'moc',
                'ex': [x[0] for x in sorted(items, key=lambda z: z[0]['e'])]}
        if _a: vrec['addr'] = _a
        venues.append(vrec)
    for (city, name), items in approx.items():
        _a = best_addr([x[4] for x in items])
        vrec = {'name': name, 'city': city, 'la': items[0][1], 'lo': items[0][2], 'loc': items[0][3], 'src': 'moc',
                'ex': [x[0] for x in sorted(items, key=lambda z: z[0]['e'])]}
        if _a: vrec['addr'] = _a
        venues.append(vrec)

    def near(la, lo):
        for v in venues:
            if v['loc'] == 'exact' and abs(v['la']-la) < 0.003 and abs(v['lo']-lo) < 0.003: return v
        return None
    for name, city, la, lo, url, museum in ANCHORS:
        perm = {'t': ('常設展廳（展品以官網為準）' if museum else '園區展覽與活動（詳見官網）'),
                's': '', 'e': '', 'l': url, 'img': '', 'ty': 'permanent', 'h': 1}
        v = near(la, lo)
        if v: v['ex'].insert(0, perm); v.setdefault('url', url)
        else: venues.append({'name': name, 'city': city, 'la': la, 'lo': lo, 'loc': 'exact', 'src': 'curated', 'url': url, 'ex': [perm]})

    # 排除圖書館 + 郵政（依需求不收錄）：場館名或展名命中即移除
    LIB_V = re.compile(r'圖書館|圖書資訊|圖資館|圖書藝文|郵政')
    LIB_EX = re.compile(r'圖書|主題書展|借閱|郵政')
    before_v = len(venues)
    venues = [v for v in venues if not LIB_V.search(v['name'])]
    before_e = sum(len(v['ex']) for v in venues)
    for v in venues:
        v['ex'] = [e for e in v['ex'] if not LIB_EX.search(e['t'])]
    venues = [v for v in venues if v['ex']]
    log("排除圖書館場館:", before_v - len(venues), "個｜額外移除圖書館類展覽:", before_e - sum(len(v['ex']) for v in venues), "場")

    # 逐張驗證圖片，未通過者清空（寧缺勿錯）
    allimgs = {e['img'] for v in venues for e in v['ex'] if e.get('img')}
    goodimg = validate_images(allimgs)
    for v in venues:
        for e in v['ex']:
            if e.get('img') and e['img'] not in goodimg: e['img'] = ''

    # 合併「場館官網收集器」的完整展覽（venue_extra.json）→ 取代該館的占位卡
    extra_path = P("venue_extra.json")
    if os.path.exists(extra_path):
        extra = json.load(open(extra_path, encoding="utf-8"))
        for name, info in extra.items():
            exs = []
            for e in info.get("ex", []):
                end = e.get("e", "")
                if end and end < TODAY: continue   # 過期略過
                exs.append({"t": e["t"], "s": e.get("s", ""), "e": end, "l": e.get("l", ""),
                            "img": e.get("img", ""), "ty": "special", "h": 0, "src": "official"})
            if not exs: continue
            # 官網資料為準：有爬蟲的場館不再混入政府 API 展覽，避免較不精準的
            # API 標題/地點/活動型資料蓋過官網整理結果。
            base = name.split("（")[0].split("(")[0]
            old_same = [v for v in venues if (v["name"] == name or v["name"].startswith(name) or v["name"].startswith(base))]
            venues[:] = [v for v in venues if v not in old_same]
            vrec = {"name": name, "city": info["city"], "la": info["lat"], "lo": info["lng"],
                    "loc": "exact", "src": "official", "url": info["url"], "ex": exs}
            _a = best_addr([v.get("addr", "") for v in old_same])
            if _a: vrec["addr"] = _a
            venues.append(vrec)
        log("已合併場館官網資料:", list(extra.keys()))

    # 合併「索卡藝術官網」：索卡有台北/台南分館，展覽地點必須進詳情頁判斷。
    # 若官方收集器有資料，移除政府 API 的泛稱「索卡藝術」，避免沿用單一台北座標。
    soka_path = P("soka_extra.json")
    if os.path.exists(soka_path):
        try:
            soka_extra = json.load(open(soka_path, encoding="utf-8"))
        except Exception:
            soka_extra = {}
        if soka_extra:
            before_soka = len(venues)
            venues[:] = [v for v in venues if v.get("name") != "索卡藝術"]
            removed_soka = before_soka - len(venues)
            sc = 0
            for name, info in soka_extra.items():
                exs = []
                for e in info.get("ex", []):
                    end = e.get("e", "")
                    if end and end < TODAY:
                        continue
                    exs.append({"t": e["t"], "s": e.get("s", ""), "e": end, "l": e.get("l", ""),
                                "img": e.get("img", ""), "ty": "special", "h": 0, "src": "official"})
                if not exs or not valid(info.get("lat"), info.get("lng")):
                    continue
                venues.append({"name": name, "city": info.get("city") or city_from_coord(info["lat"], info["lng"]),
                               "la": float(info["lat"]), "lo": float(info["lng"]), "loc": "exact",
                               "src": "official", "url": info.get("url", ""), "ex": exs,
                               "addr": clean_addr(info.get("addr", ""))})
                sc += 1
            log("已合併索卡藝術官網資料:", sc, "分館｜移除泛稱索卡:", removed_soka)

    # 定位收斂（ACG＋話題展主打）：砍 A 行政/非展場 + B 地方文化局/中心/社區常態
    # 保留優先：官網層/編輯層、或名稱屬展館類（美術館/藝廊/藝術中心/文物館/文創/園區…）一律保留
    KEEP_NAME = re.compile(r'美術館|博物館|科學館|科博|當代館|攝影文化中心|文創|文化創意|駁二|華山|松菸|松山文創|園區|展覽館|藝術特區|傳統藝術中心|工藝研究|文學館|海洋生物|天文|藝廊|畫廊|藝術中心|文物館|紀念館|美術|藝術|藝所')
    USER_CUT = re.compile(r'史前|耘非凡美術館')   # 使用者剔除清單（歷史類、已確認政府 API 錯資料等不收）
    GOV_UNIT = re.compile(r'政府$|政府(文化觀光局|文化觀光處|文化處|旅遊處|民政局|社會局)?$|縣政府|市政府|文化觀光局|文化觀光處|文化處|旅遊處|民政局|社會局|青年職涯發展中心|^臺北市藝文推廣處$')
    GOV_KEEP = re.compile(r'文化走廊|文山劇場|大稻埕戲苑|民治市政中心')
    CUT_A = re.compile(r'事務所|區公所|鄉公所|鎮公所|市公所|公所|議會|醫院|衛生所|警察|戶政|地政|稅務|監理|分局|派出所|大學|學院|高中|國中|國小|小學|學校|百貨|商旅|酒店|飯店|糖廠|農會|車站|公司|銀行|郵局')
    CUT_B = re.compile(r'文化局|文化中心|藝文中心|生活美學館|演藝廳|文化會館|社區|活動中心|老人會|里民|香鋪|教會|代天府|宮$|廟|孔子廟|戶外')
    def keep_venue(v):
        if USER_CUT.search(v['name']): return False   # 使用者剔除優先
        if GOV_UNIT.search(v['name']) and not GOV_KEEP.search(v['name']): return False
        if v.get('src') in ('official', 'curated'): return True
        if KEEP_NAME.search(v['name']): return True
        return not (CUT_A.search(v['name']) or CUT_B.search(v['name']))
    before = len(venues)
    venues = [v for v in venues if keep_venue(v)]
    log("收斂刪除 A/B:", before - len(venues), "個場館")

    # 第3類修整：正規化場館名（去展名/樓層/展廳/館號後綴、套同義詞）→ 合併同名場館、去重展覽
    ALIAS = {
        '華山1914文創園區': '華山1914文化創意產業園區',
        '松山文創園區 5號倉庫': '松山文創園區',
        '人類文化廳二樓': '國立自然科學博物館',
        '臺南市奇美博物館': '奇美博物館',
        '財團法人中台文化藝術基金會': '中台世界博物館',  # user_supplied_2026-06-22：同一場館，基金會特展併入中台世界博物館
    }
    ROOM = re.compile(r'\s*[-－]?\s*(\d+號館|中\d+[A-Za-z]?館|[一二三四五六七八九十兩\dBF０-９]+樓.*|展覽室.*|展示室.*|特展室.*|[第].*展覽?室.*|[0-9０-９、，, ]+倉.*|倉$|Zone.*|V\.?I\.?P.*|展區.*)$')
    def canon(n):
        n = (n or '').strip()
        n = re.split(r'《|〈|【', n)[0].strip()        # 去掉接在館名後的展名
        n = re.sub(r'[（(][^）)]*[）)]\s*$', '', n).strip()   # 去尾端括號附註（全/半形）
        n = ROOM.sub('', n).strip().rstrip('-－ ').strip()
        n = ALIAS.get(n, n)
        return n or '未具名場地'
    from collections import OrderedDict
    groups = OrderedDict()
    for v in venues:
        groups.setdefault(canon(v['name']) or v['name'], []).append(v)
    rank = {'official': 0, 'curated': 1, 'moc': 2}
    merged = []
    for cname, vs in groups.items():
        vs.sort(key=lambda v: (rank.get(v.get('src'), 3), -len(v['ex'])))
        base = vs[0]
        has_official = any(v.get('src') == 'official' for v in vs)
        seen = set(); exs = []
        for v in vs:
            if has_official and v.get('src') not in ('official', 'manual'):
                continue
            for e in v['ex']:
                if e['t'] in seen: continue
                seen.add(e['t']); exs.append(e)
        base['name'] = cname; base['ex'] = exs
        merged.append(base)
    log("第3類合併:", len(venues), "→", len(merged), "個場館")
    venues = merged

    # API 異常保護：若本次 moc 層筆數遠低於正常，從前次快照補回仍有效的 moc 場館
    if not _moc_api_ok:
        _prev_snap = P("_report_prev.json")
        if not os.path.exists(_prev_snap):
            _prev_snap = P("venues.json")  # fallback
        try:
            _prev_data = json.load(open(_prev_snap, encoding="utf-8"))
            _prev_moc = [v for v in _prev_data.get("venues", []) if v.get("src") == "moc"]
            _cur_names = {v["name"] for v in venues}
            _added_moc = 0
            for _pv in _prev_moc:
                if _pv["name"] in _cur_names:
                    continue
                # 只保留結束日仍在今天或之後（或無結束日）的活動
                _exs = [e for e in _pv.get("ex", [])
                        if not (e.get("e") and e["e"] < TODAY)]
                if not _exs:
                    continue
                _pv_copy = dict(_pv)
                _pv_copy["ex"] = _exs
                venues.append(_pv_copy)
                _cur_names.add(_pv["name"])
                _added_moc += 1
            log(f"moc 補填完成：{_added_moc} 個場館（來源：{os.path.basename(_prev_snap)}）")
        except Exception as _e:
            log(f"moc 補填讀取失敗: {_e}")

    # 分類（每場展覽）：混合法
    for v in venues:
        for e in v['ex']:
            e['c'] = classify(e['t'], v['name'])

    # 砍歷史類，只保留「混合型」白名單（故宮、文資園區、文學館類、穀倉藝術館、舊打狗驛故事館）
    HIST_NAME = re.compile(r'歷史|文物|文獻|民俗|古蹟|考古|眷村|客家|原住民|族館|族文化|族.*文物|史蹟|宗祠|代天府|忠烈|孔子廟|穀倉|文化資產|故居|書院|媽祖|民藝|漁會')
    HIST_KEEP = {'國立故宮博物院', '文化部文化資產園區', '國立臺灣文學館', '臺中文學館', '池上穀倉藝術館', '舊打狗驛故事館'}
    def is_history(v):
        if v['name'] in HIST_KEEP: return False
        n = len(v['ex']); he = sum(1 for e in v['ex'] if e.get('c') == '歷史人文')
        return bool(HIST_NAME.search(v['name'])) or (n > 0 and he / n >= 0.5)
    bh = len(venues)
    venues = [v for v in venues if not is_history(v)]
    log("砍歷史類:", bh - len(venues), "個場館")

    def merge_acg_extra(path, label, source, skip_titles=None):
        if not os.path.exists(path):
            return
        data = json.load(open(path, encoding="utf-8"))
        items = data.get("venues", data) if isinstance(data, dict) else {}
        mc = 0; _skipped = 0
        for name, info in items.items():
            exs = []
            for e in info.get("ex", []):
                end = e.get("e", "")
                if end and end < TODAY: continue   # 過期略過
                # 去重：官網（official）為主，手動若標題與官網重複則不寫入（跨場館名比對）
                if skip_titles and _norm_title(e.get("t", "")) in skip_titles:
                    _skipped += 1
                    continue
                ev = {"t": e["t"], "s": e.get("s", ""), "e": end, "l": e.get("l", ""),
                      "img": e.get("img", ""), "ty": "special", "h": 0 if e.get("l") else 1,
                      "src": source, "c": "動漫遊戲(ACG)"}
                if e.get("cat2"):
                    ev["cat2"] = e["cat2"]
                exs.append(ev)
            if not exs: continue
            old = next((v for v in venues if v["name"] == name), None)
            if old:
                seen = {e["t"] for e in old.get("ex", [])}
                old["ex"].extend(e for e in exs if e["t"] not in seen)
                if info.get("addr") and not old.get("addr"):
                    old["addr"] = info.get("addr")
                if not old.get("city"):
                    old["city"] = info.get("city") or city_from_coord(old.get("la"), old.get("lo"))
            else:
                located = None
                if valid(info.get("lat"), info.get("lng")):
                    located = (float(info["lat"]), float(info["lng"]), info.get("loc", "區級"),
                               info.get("city") or city_from_coord(info["lat"], info["lng"]))
                elif info.get("addr"):
                    located = locate(info.get("addr", ""), name)
                if not located:
                    continue
                la, lo, loc, city = located
                venues.append({"name": name, "city": info.get("city") or city,
                               "la": la, "lo": lo,
                               "loc": info.get("loc", loc), "src": source, "url": info.get("url", ""),
                               "ex": exs, "addr": info.get("addr", "")})
            mc += 1

        log(label, mc, "場館" + (f"（官網已有、略過 {_skipped} 筆重複）" if _skipped else ""))

    # 去重（2026/07/12）：以官網（official）為主，手動 Excel 若活動標題與官網重複則不寫入。
    # 跨場館名比對（官網用「華山1914文化創意產業園區」、手動用「華山…東2館四連棟」名稱不同也能去重）。
    _official_titles = {_norm_title(e["t"]) for v in venues if v.get("src") == "official"
                        for e in v.get("ex", [])}

    # 合併「Excel 匯入 ACG 活動」manual_extra.json：這是 import_acg_excel.py 的產物，
    # 每次完整更新都會重建，所以不要把非 Excel 的常設資料只寫在這裡。
    merge_acg_extra(P("manual_extra.json"), "合併手動 ACG 活動:", "manual", skip_titles=_official_titles)

    # 合併「長期人工確認 ACG 補表」：不由 Excel 重建，用來保存常設動漫主題店、
    # 以及 Daniel/Codex 確認過但不適合放進 Excel 的資料。
    merge_acg_extra(P("manual_permanent_extra.json"), "合併長期手動 ACG 活動:", "manual", skip_titles=_official_titles)

    # 合併 CACO 官方 POPUP：只收標題含「快閃」且括號內有 IP/主題的項目。
    merge_acg_extra(P("caco_extra.json"), "合併 CACO 官方快閃:", "caco")

    # 合併 Cayenne 官方動漫主題餐廳活動：news 提供活動/時間，restaurant 提供分店地址。
    merge_acg_extra(P("cayenne_extra.json"), "合併 Cayenne 官方活動:", "cayenne")

    # 已確認的場館誤植修正：處理政府 API 場館名/地點錯置，但活動本身仍應保留的情況。
    # 例如 API 只給區級地點、masterUnit 又誤導成主辦單位時，可依活動標題把整筆場館改回正確場館。
    vcpath = P("venue_corrections.json")
    if os.path.exists(vcpath):
        try:
            corrections = json.load(open(vcpath, encoding="utf-8"))
        except Exception:
            corrections = []
        cc = 0
        for rule in corrections:
            old_name = rule.get("match_name", "")
            pats = rule.get("title_patterns", [])
            for v in venues:
                if old_name and v.get("name") != old_name:
                    continue
                if pats and not any(any(re.search(p, e.get("t", "")) for p in pats) for e in v.get("ex", [])):
                    continue
                if rule.get("name"):
                    v["name"] = rule["name"]
                if rule.get("city"):
                    v["city"] = rule["city"]
                if rule.get("addr"):
                    v["addr"] = clean_addr(rule["addr"])
                if valid(rule.get("lat"), rule.get("lng")) and coord_matches_city(v.get("city", ""), rule["lat"], rule["lng"]):
                    v["la"] = float(rule["lat"]); v["lo"] = float(rule["lng"]); v["loc"] = "exact"
                if rule.get("url"):
                    v["url"] = rule["url"]
                cc += 1
        if cc:
            log("套用場館誤植修正:", cc, "個場館")

    # 已人工/網路確認的場館地址覆寫表：補足政府 API 只有區域層級的地址。
    # 放在 geocode 前，讓後續 address_geocodes / geocode_venues 可自動升級 exact。
    opath = P("venue_address_overrides.json")
    if os.path.exists(opath):
        try:
            overrides = json.load(open(opath, encoding="utf-8"))
        except Exception:
            overrides = {}
        oc = 0
        for v in venues:
            info = overrides.get(v["name"])
            if not info:
                continue
            addr = clean_addr(info.get("addr", ""))
            if addr:
                v["addr"] = addr
                c = cityof(addr)
                if c:
                    v["city"] = c
                oc += 1
        if oc:
            log("套用場館地址覆寫:", oc, "個場館")

    # 已確認的 geocode 覆寫表：把有地址但原本只能區級定位的場館升級成 exact。
    gpath = P("venue_geocodes.json")
    if os.path.exists(gpath):
        try:
            geocodes = json.load(open(gpath, encoding="utf-8"))
        except Exception:
            geocodes = {}
        gc = 0
        for v in venues:
            g = geocodes.get(v["name"])
            if not g: continue
            if valid(g.get("la"), g.get("lo")) and coord_matches_city(v.get("city", ""), float(g["la"]), float(g["lo"])):
                v["la"] = float(g["la"]); v["lo"] = float(g["lo"]); v["loc"] = "exact"
                gc += 1
        log("套用 geocode 精確座標:", gc, "個場館")

    # 已確認的地址 geocode：同一地址之後即使場館名不同，也能直接升級 exact。
    def addr_key(addr):
        a = clean_addr(addr)
        a = re.sub(r'\s+', '', a)
        a = re.sub(r'[，,].*$', '', a)
        return a
    apath = P("address_geocodes.json")
    if os.path.exists(apath):
        try:
            address_geocodes = json.load(open(apath, encoding="utf-8"))
        except Exception:
            address_geocodes = {}
        ac = 0
        for v in venues:
            if v.get("loc") == "exact":
                continue
            g = address_geocodes.get(addr_key(v.get("addr", "")))
            if not g:
                continue
            if valid(g.get("la"), g.get("lo")) and coord_matches_city(v.get("city", ""), float(g["la"]), float(g["lo"])):
                v["la"] = float(g["la"]); v["lo"] = float(g["lo"]); v["loc"] = "exact"
                ac += 1
        if ac:
            log("套用地址 geocode 精確座標:", ac, "個場館")

    # 同一完整地址已有 exact 場館時，子館/樓層/展廳沿用該精準座標。
    # 只處理含路街與號的完整地址，避免「台中市西區」這類泛地址被誤併。
    def is_full_addr(addr):
        a = addr_key(addr)
        return bool(re.search(r'[路街道段巷弄].*號', a))
    exact_by_addr = {}
    for v in venues:
        a = addr_key(v.get("addr", ""))
        if v.get("loc") == "exact" and is_full_addr(a):
            exact_by_addr.setdefault(a, v)
    inherited = 0
    for v in venues:
        if v.get("loc") == "exact":
            continue
        a = addr_key(v.get("addr", ""))
        if not is_full_addr(a):
            continue
        parent = exact_by_addr.get(a)
        if not parent:
            for pa, pv in exact_by_addr.items():
                if (a.startswith(pa) or pa.startswith(a)) and min(len(a), len(pa)) >= 10:
                    parent = pv
                    break
        if parent and coord_matches_city(v.get("city", parent.get("city", "")), parent["la"], parent["lo"]):
            v["la"] = parent["la"]; v["lo"] = parent["lo"]; v["loc"] = "exact"
            inherited += 1
    if inherited:
        log("同地址繼承 exact 座標:", inherited, "個場館")

    # 各場館官方 logo：依「場館名稱」對照官方網域（venue_logos.json），不依連結來源，避免抓到 FB/通用圖示
    # 已確認活動連結覆寫表：處理政府 API 無連結、或同活動因標題別名未能自動合併的情況。
    # 格式：{"場館名": {"活動標題": "官方活動頁 URL"}}。放在所有資料源合併後，讓自動化重跑也保留修正。
    eopath = P("event_link_overrides.json")
    if os.path.exists(eopath):
        try:
            event_overrides = json.load(open(eopath, encoding="utf-8"))
        except Exception:
            event_overrides = {}
        eoc = 0
        for v in venues:
            vm = event_overrides.get(v["name"], {})
            if not vm:
                continue
            for e in v.get("ex", []):
                link = vm.get(e.get("t", ""))
                if link and (not e.get("l") or bad_link(e.get("l"))):
                    e["l"] = link
                    e["h"] = is_home(link)
                    eoc += 1
        if eoc:
            log("套用活動連結覆寫:", eoc, "筆")

    # 場館官方展覽列表頁：用可重跑的來源表補政府 API 未附連結的活動。
    # 來源表記錄官方列表頁與必要 fallback 規則；更新時自動比對活動標題，避免每次人工重補。
    apply_event_sources(venues)

    # 活動 KV 快取：在所有連結補齊後套用，讓手動/社群/後補連結也能保留已抓到的主視覺。
    apply_event_kv_cache(venues)

    # ── 最終兩軸分類 pass ────────────────────────────────────────────────
    # 建立 Excel 活動標題集（manual_extra / manual_permanent_extra）供 overlap 判斷
    import difflib as _difflib
    _excel_titles_norm = set()
    for _ep in [P("manual_extra.json"),
                P("manual_permanent_extra.json")]:
        if os.path.exists(_ep):
            try:
                _d = json.load(open(_ep, encoding="utf-8"))
                _items = _d.get("venues", _d) if isinstance(_d, dict) else {}
                for _vinfo in _items.values():
                    for _e in _vinfo.get("ex", []):
                        _t = compact_title(_e.get("t", ""))
                        if len(_t) >= 4:
                            _excel_titles_norm.add(_t)
            except Exception:
                pass
    # import_acg_excel 匯出的全部使用者 Excel 標題（含六大文創園區——這些活動在 manual_extra 被 auto_managed
    # 略過，但仍要能觸發「Excel × 文創 重疊 → 改判 ACG」；官網資訊保留、分類改用 Excel 端的 ACG）。
    _ov_titles_path = P("excel_overlap_titles.json")
    if os.path.exists(_ov_titles_path):
        try:
            for _t in json.load(open(_ov_titles_path, encoding="utf-8")):
                _tc = compact_title(_t)
                if len(_tc) >= 4:
                    _excel_titles_norm.add(_tc)
        except Exception:
            pass

    def _has_overlap(title):
        ct = compact_title(title)
        if not ct or len(ct) < 4:
            return False, False
        if ct in _excel_titles_norm:
            return True, False
        # 官網標題常被截斷（例：「MONSTER STRIKE DREAMDA…」）：任一方為另一方的子字串且
        # 夠長（≥8 壓縮字元）即視為同一活動；只往 ACG 改判、方向安全，門檻夠高避免誤判。
        if len(ct) >= 8:
            for et in _excel_titles_norm:
                if len(et) >= 8 and (ct in et or et in ct):
                    return True, False
        for et in _excel_titles_norm:
            r = _difflib.SequenceMatcher(None, ct, et).ratio()
            if r >= 0.85:
                return True, False
            if r >= 0.70:
                return False, True
        return False, False

    # 手動覆蓋（2026/07/12）：event_overrides.json 讓人逐筆指定形式(c2)或主題(c)，優先於自動分類——
    # 供 classify_form 判不出「其他」或誤判時由人決定；官網與手動來源皆適用。
    _ev_ov = {}
    _ovp = P("event_overrides.json")
    if os.path.exists(_ovp):
        try:
            _raw = json.load(open(_ovp, encoding="utf-8"))
            _ev_ov = {_norm_title(k): v for k, v in _raw.items()
                      if not k.startswith('_') and isinstance(v, dict)}
            log("讀入手動形式/主題覆蓋:", len(_ev_ov), "筆")
        except Exception as _err:
            log("event_overrides 讀取失敗:", _err)

    for _v in venues:
        for _e in _v['ex']:
            _src = _e.get('src', '')
            if _src in ('manual', 'caco', 'cayenne'):
                _e['c'] = 'ACG'
                _e['c2'] = map_excel_cat2(_e.get('cat2', '')) or classify_form(_e.get('t', ''), _v['name'])
            else:
                _exact, _fuzzy = _has_overlap(_e.get('t', ''))
                if _exact:
                    _e['c'] = 'ACG'
                elif _fuzzy:
                    _e['c'] = classify_theme_kw(_e.get('t', ''), _v['name'])
                    _e['c_flag'] = '需人工確認'
                else:
                    _e['c'] = classify_theme_kw(_e.get('t', ''), _v['name'])
                _e['c2'] = classify_form(_e.get('t', ''), _v['name'])
            # 手動覆蓋優先：有指定就蓋掉上面的自動判斷
            _ov = _ev_ov.get(_norm_title(_e.get('t', '')))
            if _ov:
                if _ov.get('c'):  _e['c']  = _ov['c']
                if _ov.get('c2'): _e['c2'] = _ov['c2']
    log("兩軸分類完成")

    try:
        lmap = json.load(open(P("venue_logos.json"), encoding="utf-8")).get("map", [])
    except Exception:
        lmap = []
    # 逐站抓到的真實 logo（collect_logos.py 產生），優先使用；沒有則退用官方圖示服務
    logomap = {}
    lm_path = P("logo_map.json")
    if os.path.exists(lm_path):
        try:
            logomap = json.load(open(lm_path, encoding="utf-8"))
            if not logomap:
                log("⚠️ logo_map.json 讀取成功但內容為空，logo 將全部遺失！請檢查檔案是否損壞。")
        except Exception as _e:
            log(f"⚠️ logo_map.json 讀取失敗（{_e}），logo 將全部遺失！請確認檔案未被 APFS 壓縮或損壞。")
            logomap = {}
    artemperor_logos = {}
    ae_path = P("artemperor_logos.json")
    if os.path.exists(ae_path):
        try: artemperor_logos = json.load(open(ae_path, encoding="utf-8")).get("logos", {})
        except Exception: artemperor_logos = {}
    fb_logos = {}
    fb_path = P("fb_logos.json")
    if os.path.exists(fb_path):
        try: fb_logos = json.load(open(fb_path, encoding="utf-8")).get("logos", {})
        except Exception: fb_logos = {}
    def venue_logo(name):
        for kw, dom in lmap:
            if kw and kw in (name or ''):
                if dom in logomap:
                    return logomap[dom]                       # 本地真實 logo 檔
                if name in artemperor_logos:
                    return artemperor_logos[name]              # 非池中場館索引圖，僅作備援
                if name in fb_logos:
                    return fb_logos[name]                      # 官方 Facebook 大頭貼，僅作備援
                return ""                                      # 沒有真實 logo 就留空，不用 favicon 代理
        return artemperor_logos.get(name, fb_logos.get(name, ""))
    for v in venues:
        v['logo'] = venue_logo(v['name'])

    # 審核決策持久層：使用者於 PR 審核中拒絕（刪掉）的活動，依穩定鍵於輸出前過濾，
    # 確保下次自動更新不會再冒出來。名單為空或檔案不存在時完全不影響輸出。
    venues = filter_rejected_events(venues, load_rejected_keys())

    venues.sort(key=lambda v: -len(v['ex']))
    out = {'updated': TODAY, 'source': '文化部開放資料 藝文活動-展覽 + 編輯整理重點館/常設層', 'venues': venues}
    json.dump(out, open(P("venues.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(',', ':'))
    nimg = sum(1 for v in venues for e in v['ex'] if e.get('img'))
    nlink = sum(1 for v in venues for e in v['ex'] if e.get('l'))
    nex = sum(len(v['ex']) for v in venues)
    log("輸出 venues.json")
    print(json.dumps({'venues': len(venues), 'exhibitions': nex, 'with_image': nimg, 'with_link': nlink, 'updated': TODAY}, ensure_ascii=False))

if __name__ == "__main__":
    main()
