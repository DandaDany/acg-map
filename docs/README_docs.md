# 全台展覽地圖

最後更新：2026/09/04

⚠️ **與 Claude / Codex 溝通一律使用中文，不得用日文或英文。**

---

## 📌 目前交接狀態（最新覆蓋；給人類/Agent 一眼看完省 token）

> **硬性規定**：不論是誰（Claude / Claude Code / Codex / 人類），**每次做完事情，結束前都要做兩件事**：
> （1）在 `Agent交流工作日誌.txt` **追加**一筆歷史紀錄（只加不改）；
> （2）把下面這六欄**覆蓋更新**成最新狀態。兩者都做完才算工作結束。

```
目標：     修正 2026/09/04 Daily Update #60 的駁二部分清單退化，並收錄 Slack 兩項北中南快閃活動。
目前檔案： 人工活動來源為 data/manual/acg_events.json；主辦／授權／來源與費用覆寫在 data/manual/；
           穩定 KV 在 data/manual/_kv_cache/；公開輸出在 public/；後端管線與測試在 backend/。
已完成：   確認 run #60 的六館抓取與管線成功、驗證因駁二僅回傳9筆且漏掉仍在展期的《獵人實境解謎》而失敗。
           新增非空部分清單防護：保留本次新資料、補回昨日仍有效缺項、已到期活動不補回；測試與決策文件同步。
           收錄咒術迴戰與魔法少女小圓兩項快閃店，共6圖釘；官方KV、主辦、權利方、免費判定、地址與座標已驗證。
目前錯誤： GitHub Daily Update #60 失敗且未建立自動PR；本地修正與127項backend測試均通過。GitHub Actions額度已滿，PR CI可能無法啟動。
下一步：   建立單一維護 PR；待 Actions 額度恢復後確認 CI，並由下一次 Daily Update 驗證部分清單防護。
不要改動： 未經 Daniel 對本PR明確同意不得合併；不得放寬日期防退化測試，不得覆蓋人工 SSOT、座標、KV、費用與 UI 決策。
```

---

這是一個純靜態的台灣展覽與 ACG 活動地圖。前端公開檔在 `public/`，後台資料管線在 `backend/`，資料層在 `data/`；資料夾與後台結構請看 `docs/後台資料夾結構.md`，詳細交接請看 `docs/專案交接文件.md`。每個主要資料夾也都有自己的 `README.md`，用來說明該資料夾的檔案角色。

## 快速上手

```bash
# 首次安裝
pip install playwright openpyxl --break-system-packages
python3 -m playwright install chromium

# 更新資料
python3 backend/update_all.py

# 本機預覽
cd public
python3 -m http.server 8000
# 開 http://localhost:8000/taiwan-exhibition-map.html
```

也可以直接雙擊 `public/taiwan-exhibition-map.html`。file:// 模式會使用 HTML 內嵌的備援資料；街道底圖與路名需要連網才會載入。

## 專案內容

- `public/taiwan-exhibition-map.html`：單頁地圖，內嵌 Leaflet、MarkerCluster、鄉鎮界、備援資料，並透過 CDN 載入 MapLibre / OpenFreeMap 街道底圖。
- `public/venues.json`：網頁讀取的最終資料。
- `backend/update_all.py`：一鍵更新流程，依序跑收集、匯入、補圖、地理編碼、主資料刷新與 HTML 內嵌備援同步。
- `backend/refresh_venues.py`：主資料管線，合併官網爬蟲（六大園區）、園區座標錨與手動/CACO/Cayenne ACG 資料。⚠️ 2026/07/12 起 `USE_MOC=False`：政府（文化部）API 已停用，不再收錄 moc 層。
- `backend/paths.py`：新後台結構的路徑中心。
- `data/manual/manual_extra.json`：手動整理的 ACG 活動持久層。
- `data/generated/venue_extra.json`：官網爬蟲中繼資料。
- `data/logos/venue_logos.json`、`data/logos/logo_map.json`、`public/logos/`：場館 logo 對照與前端本地檔案。
- `data/reference/town_centroids.json`：鄉鎮區中心點，用於約略定位與前端地名標籤。
- `backend/report_status.py`：維護回報腳本（讀 `public/venues.json` 比對 `data/reports/_report_prev.json`，輸出新增/缺漏/建議）。
- `Agent交流工作日誌.txt`：**Claude 與 Codex 兩個 agent 的協作日誌**。⚠️ **每次對專案做任何更動，結束前都必須在此追加一筆**（日期＋agent 名＋做了什麼/改了哪些檔/注意事項）。這是硬性規定，不論改動大小，不寫就算工作未完成。最新寫在最上面，只追加不刪改歷史。
- `DECISIONS.md`：**技術決策紀錄**（2026/07/01 建立）。記錄目前確認使用的技術（前端/管線/資料來源/排程），以及已投入程式邏輯、改動代價很高的「不能反悔的決策」（如：純靜態架構、放棄 build2.py、兩軸分類、0.003° 合併門檻、manual_extra.json 持久層等）。文件中也把「明確載明的決策」與「AI 依現況推論的判斷」分開標示，並附可信度（✅/⚠️）。**任何人要做架構級改動（換分類軸、換合併門檻、改 venues.json 欄位結構等）前，請先讀這份檔案**，避免不小心推翻已經確認過的決策。

## 資料來源

目前資料來源（2026/07/12 收斂後）：

1. ~~文化部開放資料「藝文活動-展覽」API~~ → **已停用**（`USE_MOC=False`）。政府層對公開端 ACG 幾乎無貢獻，全停以去雜訊。
2. 各場館官網爬蟲（`collect_venues.py`），**只留六大文創園區/特區**：華山1914、松山文創、圓山花博、駁二、嘉義文創、花蓮文創。
3. `manual_extra.json` / `manual_permanent_extra.json`：手動整理的 ACG 活動（核心）。
4. `caco_extra.json`（CACO 官方快閃）、`cayenne_extra.json`（Cayenne 官方主題餐廳）。
5. 補件層（不是活動來源）：`geocode_venues.py` 座標、`collect_logos.py`/`collect_fb_logos.py` logo、`collect_event_kv.py` 主視覺。

去重規則：官網（official）為主，手動 Excel 若活動標題與官網重複則不寫入（`refresh_venues.py` 的 `skip_titles`／跨場館名比對）。

資料連結維護規則：
- `url` 只能填場館或主辦單位真正的官方網站、官方展覽頁、官方活動頁。
- 禁止把 Wikipedia、Google Maps、新聞報導、部落格、資料庫頁面、地址查詢頁、非官方介紹頁，或任何「看起來合理」但不是官方的連結填入 `url`。
- 如果使用者只提供地址、場館名稱或非官方參考資料，`url` 必須留空；只能補地址、座標、活動名稱等可明確確認的欄位。
- 不要自行猜官方網站。除非能確認它是真的官方網站，否則不要補。

分類為兩個正交軸：
- **軸 A 主題**（`c`）：`ACG` / `藝術設計` / `其他文化`
- **軸 B 形式**（`c2`）：`展覽` / `快閃店` / `主題餐廳` / `體驗活動` / `其他`

## 維護重點

- 修改前端：直接改 `public/taiwan-exhibition-map.html`。目前沒有 `build2.py` 產生流程。
- 新增通用官網爬蟲場館：編輯 `backend/collect_venues.py` 的 `VENUES`。
- 新增特殊格式場館：編輯 `backend/collect_public.py`。
- 新增手動 ACG 活動：整理進 `data/manual/manual_extra.json` 後跑 `python3 backend/update_all.py`。
- 調整分類關鍵字：修改 `backend/refresh_venues.py` 的 `THEME_ACG_KW` / `THEME_ART_KW`（軸 A）或 `FORM_KW`（軸 B）。
- 新增 logo：修改 `data/logos/venue_logos.json` 後跑 `python3 backend/collect_logos.py`。

## 已知限制

- 多數文化部資料沒有精確座標；目前不少點位是區級或市級約略定位。
- KV 圖片來源不穩，管線會嚴格驗證圖片，寧可留空也不放錯圖。
- 官網爬蟲受網站結構與網路狀況影響，更新後需要抽查重點場館。
- 街道底圖依賴外部 CDN 與 OpenFreeMap；離線時仍可顯示資料與鄉鎮界輔助框線。

## 驗證

```bash
python3 -m py_compile backend/update_all.py backend/collect_venues.py backend/collect_public.py backend/collect_logos.py backend/refresh_venues.py
python3 -c 'import json; json.load(open("public/venues.json", encoding="utf-8")); print("venues json ok")'
```

前端請用本機 server 或 file:// 開啟，確認圖釘、群集、抽屜、搜尋、篩選、分類與資料更新標示都正常。
