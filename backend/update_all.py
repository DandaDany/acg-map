#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全台展覽地圖 — 一鍵更新流程（可重複、可定期執行）

步驟：
  1) collect_venues.py  用瀏覽器渲染各館官網、抓「完整當期展覽」→ venue_extra.json
  2) collect_soka_art.py 從索卡藝術詳情頁判斷台北/台南分館 → soka_extra.json
  3) clean_acg_excel.py 清洗使用者 Excel，把上下列地點/地址合併成「地點（地址）」
  4) collect_caco_stores.py 從 CACO 官方 CAFE/POPUP 頁快取分店與動漫快閃
  5) collect_cayenne_cafe.py 從 Cayenne 官方消息/餐廳頁快取動漫主題餐廳活動
  6) import_acg_excel.py 從使用者 Excel 重建 manual_extra.json，解析「地點（地址）」
  7) collect_logos.py  依已確認官方網域補本機 logo 快取
  8) refresh_venues.py  先產生最新 venues.json，讓後續補件看見新場館/新活動
  9) collect_fb_logos.py  依最新版 venues.json 的 Facebook 連結補 fallback logo
 10) geocode_venues.py  對最新版場館中約略定位但有地址/高可信 POI 者更新精準座標快取
 11) collect_event_kv.py 對最新版活動中缺 KV 但有活動連結者抓主視覺快取；靜態抓不到時用瀏覽器 fallback
 12) refresh_venues.py  套用 Facebook logo/geocode/KV 快取，輸出最終 venues.json
 13) build_logo_thumbs.py  依最終 venues.json 產生前端 marker 用小圖

網頁 taiwan-exhibition-map.html 會載入 venues.json，更新後重新整理即生效。

用法：python3 backend/update_all.py
定期更新：用系統排程（cron / 工作排程器）每日或每週執行本檔即可。
"""
import subprocess, sys, datetime
from paths import path as P

def run(script, *args):
    label = " ".join((script, *args))
    print(f"\n=== 執行 {label} ===")
    r = subprocess.run([sys.executable, P(script), *args])
    if r.returncode != 0:
        sys.exit(f"{label} 失敗（離開碼 {r.returncode}），venues.json 維持上一版")

print(f"開始更新 {datetime.datetime.now():%Y-%m-%d %H:%M}")
run("collect_venues.py")   # 六大園區官網爬蟲；任一步失敗即停，避免產生半套資料
# 2026/07/12 停止收錄：collect_public.py（新竹/關渡/C-LAB）、collect_soka_art.py（索卡）——
# 官網來源收斂為六大文創園區/特區，不再抓純美術館。如需恢復再取消下列註解。
# run("collect_public.py")
# run("collect_soka_art.py")
run("clean_acg_excel.py")  # 標準化 Excel：地點/地址上下列 → 地點（地址）
run("collect_caco_stores.py") # CACO 官方 CAFE/POPUP → caco_stores.json / caco_extra.json
run("collect_cayenne_cafe.py") # Cayenne 官方 news/restaurant → cayenne_stores.json / cayenne_extra.json
run("import_acg_excel.py") # 使用者 Excel → manual_extra.json；保留括號內地址，可用 CACO CAFE 快取補分店地址
run("collect_logos.py")    # 已確認官方網域 → logos/ + logo_map.json
run("refresh_venues.py")   # 第一輪：建立最新場館/活動清單，供補件腳本讀取
run("collect_fb_logos.py") # 讀最新版 venues.json 的 FB 連結 → logos/facebook/ + fb_logos.json
run("geocode_venues.py")   # 讀最新版 venues.json；完整地址/高可信 POI → geocode 快取
run("collect_event_kv.py", "--browser-fallback")  # 讀最新版 venues.json；缺 KV 且有活動連結者 → event_kv_cache.json
run("refresh_venues.py")   # 第二輪：套用 FB logo、geocode、KV 快取後輸出最終版
run("build_logo_thumbs.py") # 依最終 logo 清單產生小圖 → logos/_thumbs/，前端 marker 載入更快

def sync_embed():
    """把最新 venues.json 同步進 taiwan-exhibition-map.html 的內嵌備援，
    讓本機 file:// 雙擊開啟也是最新資料（http/線上版讀即時 venues.json，不受影響）。"""
    import json, io
    try:
        vj = json.load(open(P("venues.json"), encoding="utf-8"))
        hp = P("taiwan-exhibition-map.html")
        lines = io.open(hp, encoding="utf-8").readlines()
        # 只認「開頭是 let DATA = 」這一行；liveMode 是獨立宣告在別的行（現況如此，不假設同行），
        # 這裡不動它，只換 DATA 的 JSON 內容本身。
        nl = 'let DATA = ' + json.dumps(vj, ensure_ascii=False, separators=(',', ':')) + ';\n'
        hit = 0
        for i, l in enumerate(lines):
            if l.lstrip().startswith('let DATA = '):
                lines[i] = nl; hit += 1
        if hit == 1:
            io.open(hp, "w", encoding="utf-8").writelines(lines); print("已同步 HTML 內嵌備援")
        else:
            print(f"（內嵌備援未同步：找到 {hit} 處 DATA 行）")
    except Exception as e:
        print("內嵌備援同步略過：", e)

sync_embed()
print("\n更新完成：venues.json 已更新（請重新整理網頁）")
