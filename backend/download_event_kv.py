#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自存活動主視覺（KV）到 public/kv/，改引用站內路徑，並清理過期活動的圖檔。

背景：
- 每張活動 KV 原本都是「遠端網址直接引用」。這有兩種失效風險：
  a) 會過期的臨時簽章網址（Instagram / Facebook CDN：scontent*.cdninstagram.com、
     *.fbcdn.net，或網址帶 oe= 到期參數），數天～數週後必失效導致破圖。
  b) 一般官網圖雖較穩定，仍可能被站方改版、搬移、擋外連（hotlink）而破圖。
- 因此支援兩種模式（見 --all）：
  * 預設：只自存 (a) 會過期的那類（最小必要，省儲存）。
  * --all：把所有遠端 KV 全部自存到 public/kv/，一律改引用站內路徑
           （「先存起來，再從存檔資料夾引用」的完整自存模式，不再依賴外站）。
    update_all.py 走的就是 --all。

機制：
1) 讀 public/venues.json，對「符合本次模式」的 e.img 下載到
   public/kv/<穩定鍵hash>.<ext>，並把 e.img 改寫成 'kv/<檔名>'（站內相對路徑，
   前端 safeUrl 會正確解析）。
   下載失敗則保留原網址（不讓管線中斷、寧可暫時破圖也不寫壞資料）。
   已存在同名本地檔則跳過下載、只改寫路徑（可重複執行、冪等）。
2) 清理（使用者需求「活動過了就刪掉」）：venues.json 已由 refresh_venues.py 自動移除
   endDate < 今天的過期活動，因此它們的 KV 不再被引用。本步驟把 public/kv/ 內
   「未被目前 venues.json 任一活動引用」的孤兒圖檔刪除，避免資料夾無限膨脹。

在 update_all.py 中的位置：最後一輪 refresh 之後、sync_embed 之前執行，
讓 HTML 內嵌備援也拿到站內路徑。

用法：
  python3 backend/download_event_kv.py         # 只自存會過期的 KV
  python3 backend/download_event_kv.py --all    # 自存所有遠端 KV（完整自存模式）
"""
import argparse, json, os, sys, ssl, hashlib, urllib.request
from urllib.parse import quote, unquote, urlparse, urlunparse
from paths import path as P
from refresh_venues import stable_event_key  # 用同一把穩定鍵，檔名跨執行穩定

KV_DIRNAME = "kv"
EXPIRING_HOST_MARKERS = ("cdninstagram.com", "fbcdn.net")
# 放寬版 SSL context（與專案其他抓取一致，因應部分憑證缺 SKI）
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE


def public_dir():
    return os.path.dirname(P("venues.json"))


def kv_dir():
    return os.path.join(public_dir(), KV_DIRNAME)


def is_remote(url):
    """是否為仍指向外站的遠端網址（尚未本地化）。站內相對路徑/空值回傳 False。"""
    return str(url or "").startswith("http")


def is_expiring(url):
    """判斷此圖網址是否為會過期的臨時簽章網址（IG/FB CDN 或帶 oe= 到期參數）。"""
    u = str(url or "")
    if not is_remote(u):
        return False  # 已是站內相對路徑或空值
    if "oe=" in u:
        return True
    return any(m in u for m in EXPIRING_HOST_MARKERS)


def _ext_from_url(url, default=".jpg"):
    tail = str(url).split("?", 1)[0].split("#", 1)[0]
    dot = tail.rfind(".")
    slash = tail.rfind("/")
    if dot > slash and dot >= 0:
        ext = tail[dot:].lower()
        if 2 <= len(ext) <= 5 and ext.lstrip(".").isalnum():
            return ext
    return default


def local_name(venue_name, event, url):
    """以穩定鍵 hash 命名，跨執行穩定；同一活動永遠對到同一檔。"""
    key = stable_event_key(venue_name, event.get("t", ""), event.get("s", ""))
    h = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
    return h + _ext_from_url(url)


def quote_url(url):
    """把網址路徑/查詢字串中的空白與非 ASCII 字元做 percent-encode。

    urllib.request.Request 遇到含空白或中文的原始網址會直接丟 InvalidURL
    （"URL can't contain control characters"），使該圖無法自存、只能留原始遠端網址
    （見 collect_event_kv.py 也用同樣手法）。例：華山官網 KV 檔名含空白與中文。
    """
    try:
        p = urlparse(url)
        path = quote(unquote(p.path), safe="/%:@")
        query = quote(unquote(p.query), safe="=&?/%:@,+")
        return urlunparse((p.scheme, p.netloc, path, p.params, query, p.fragment))
    except Exception:
        return url


def _default_downloader(url, dest):
    """實際下載器：抓 url 存到 dest。失敗丟例外，由呼叫端決定是否略過。"""
    req = urllib.request.Request(quote_url(url), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30, context=_CTX) as r:
        data = r.read()
    if not data or len(data) < 512:
        raise ValueError(f"下載內容過小（{len(data)} bytes）")
    tmp = dest + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, dest)


def localize(venues, dirpath, downloader=_default_downloader, log=print, predicate=is_expiring):
    """把符合 predicate 的 e.img 下載到 dirpath 並改寫為站內路徑。

    predicate(url) 決定哪些圖要自存：預設 is_expiring（只會過期的），
    傳 is_remote 則自存所有遠端圖（完整自存模式）。
    回傳 (改寫數, 下載數, 失敗數)。
    """
    os.makedirs(dirpath, exist_ok=True)
    rewritten = downloaded = failed = 0
    for v in venues:
        for e in v.get("ex", []):
            url = e.get("img")
            if not predicate(url):
                continue
            fname = local_name(v.get("name", ""), e, url)
            dest = os.path.join(dirpath, fname)
            rel = f"{KV_DIRNAME}/{fname}"
            if os.path.exists(dest):
                e["img"] = rel
                rewritten += 1
                continue
            try:
                downloader(url, dest)
                e["img"] = rel
                rewritten += 1
                downloaded += 1
            except Exception as err:
                failed += 1
                log(f"  KV 下載失敗（保留原網址）: {v.get('name','')} / {e.get('t','')[:20]} :: {err}", file=sys.stderr)
    return rewritten, downloaded, failed


def gc_orphans(venues, dirpath, log=print):
    """刪除 public/kv/ 內未被目前 venues.json 任一活動引用的孤兒圖檔（過期活動的圖）。"""
    if not os.path.isdir(dirpath):
        return 0
    referenced = set()
    for v in venues:
        for e in v.get("ex", []):
            img = str(e.get("img") or "")
            if img.startswith(KV_DIRNAME + "/"):
                referenced.add(os.path.basename(img))
    removed = 0
    for fn in os.listdir(dirpath):
        full = os.path.join(dirpath, fn)
        if os.path.isfile(full) and fn not in referenced:
            try:
                os.remove(full)
                removed += 1
            except OSError as err:
                log(f"  清理孤兒圖失敗: {fn} :: {err}", file=sys.stderr)
    return removed


def main():
    parser = argparse.ArgumentParser(description="自存活動主視覺（KV）到 public/kv/ 並清理過期孤兒圖。")
    parser.add_argument(
        "--all",
        action="store_true",
        help="自存所有遠端 KV（不只會過期的），一律改引用 public/kv/（完整自存模式）",
    )
    args = parser.parse_args()

    predicate = is_remote if args.all else is_expiring
    mode = "全部遠端" if args.all else "僅會過期"
    vpath = P("venues.json")
    data = json.load(open(vpath, encoding="utf-8"))
    venues = data.get("venues", [])
    dirpath = kv_dir()
    rewritten, downloaded, failed = localize(venues, dirpath, predicate=predicate)
    removed = gc_orphans(venues, dirpath)
    json.dump(data, open(vpath, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"KV 自存（{mode}）：改寫 {rewritten} 張（新下載 {downloaded}、失敗 {failed}）｜清理過期孤兒圖 {removed} 張")


if __name__ == "__main__":
    main()
