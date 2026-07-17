#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自存會過期的活動主視覺（KV）並清理過期活動的圖檔。

背景：
- 多數活動 KV 來自場館官網（穩定公開網址），維持遠端引用即可，不處理。
- 少數 KV 來自 Instagram / Facebook CDN（scontent*.cdninstagram.com、*.fbcdn.net，
  或網址帶 oe= 到期參數）。這種網址是臨時簽章網址，數天～數週後會失效導致破圖，
  不論網站部署在哪都一樣。→ 這類必須「自存一份」到 public/kv/，改引用站內路徑。

機制：
1) 讀 public/venues.json，對「會過期主機」的 e.img 下載到 public/kv/<穩定鍵hash>.<ext>，
   並把 e.img 改寫成 'kv/<檔名>'（站內相對路徑，前端 safeUrl 會正確解析）。
   下載失敗則保留原網址（不讓管線中斷、寧可暫時破圖也不寫壞資料）。
   已存在同名本地檔則跳過下載、只改寫路徑（可重複執行、冪等）。
2) 清理（使用者需求「活動過了就刪掉」）：venues.json 已由 refresh_venues.py 自動移除
   endDate < 今天的過期活動，因此它們的 KV 不再被引用。本步驟把 public/kv/ 內
   「未被目前 venues.json 任一活動引用」的孤兒圖檔刪除，避免資料夾無限膨脹。

在 update_all.py 中的位置：最後一輪 refresh 之後、sync_embed 之前執行，
讓 HTML 內嵌備援也拿到站內路徑。

用法：python3 backend/download_event_kv.py
"""
import json, os, sys, ssl, hashlib, urllib.request
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


def is_expiring(url):
    """判斷此圖網址是否為會過期的臨時簽章網址（IG/FB CDN 或帶 oe= 到期參數）。"""
    u = str(url or "")
    if not u.startswith("http"):
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


def _default_downloader(url, dest):
    """實際下載器：抓 url 存到 dest。失敗丟例外，由呼叫端決定是否略過。"""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30, context=_CTX) as r:
        data = r.read()
    if not data or len(data) < 512:
        raise ValueError(f"下載內容過小（{len(data)} bytes）")
    tmp = dest + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, dest)


def localize(venues, dirpath, downloader=_default_downloader, log=print):
    """把會過期的 e.img 下載到 dirpath 並改寫為站內路徑。回傳 (改寫數, 下載數, 失敗數)。"""
    os.makedirs(dirpath, exist_ok=True)
    rewritten = downloaded = failed = 0
    for v in venues:
        for e in v.get("ex", []):
            url = e.get("img")
            if not is_expiring(url):
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
    vpath = P("venues.json")
    data = json.load(open(vpath, encoding="utf-8"))
    venues = data.get("venues", [])
    dirpath = kv_dir()
    rewritten, downloaded, failed = localize(venues, dirpath)
    removed = gc_orphans(venues, dirpath)
    json.dump(data, open(vpath, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"KV 自存：改寫 {rewritten} 張（新下載 {downloaded}、失敗 {failed}）｜清理過期孤兒圖 {removed} 張")


if __name__ == "__main__":
    main()
