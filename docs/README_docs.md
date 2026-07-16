# 全台展覽地圖

最後更新：2026/07/13

⚠️ **與 Claude / Codex 溝通一律使用中文，不得用日文或英文。**

---

## 📌 目前交接狀態（最新覆蓋；給人類/Agent 一眼看完省 token）

> **硬性規定**：不論是誰（Claude / Claude Code / Codex / 人類），**每次做完事情，結束前都要做兩件事**：
> （1）在 `Agent交流工作日誌.txt` **追加**一筆歷史紀錄（只加不改）；
> （2）把下面這六欄**覆蓋更新**成最新狀態。兩者都做完才算工作結束。

```
目標：     依「ACG 活動地圖 UI 更改建議書」把站台從「全台展覽地圖」收斂定位為「全台 ACG 活動地圖」，
           公開端預設只顯示 ACG、以活動為主角，UI 精簡並改為活動優先的圖釘 popup。
目前檔案： 前端公開檔在 public/（唯一前端檔 public/taiwan-exhibition-map.html，約 730KB 單一大檔，
           內嵌 DATA 與 Leaflet／MarkerCluster 函式庫）；後台程式在 backend/；資料層在 data/；
           文件在 docs/；維運在 ops/；執行期 log/profile/debug 在 runtime/；歷史備份在 archive/。
已完成：   【第一階段 UI 收斂 ＋ 版型改側欄 ＋ 第二階段使用者功能，2026/07/11，皆已驗證通過】
           ▍第一階段：①站名／文案改「全台 ACG 活動地圖」②移除 #fcat 主題篩選（state.cat='ACG'）
             ③時段文案「進行中／即將開始」、「即將結束」統一 ENDING_SOON_DAYS=7 ④地區加縣市次級（#regionCities）
             ⑤活動數「目前共有 N 場活動」、搜尋擴充 v.name/v.city/v.addr/e.t ⑥點圖釘改活動優先 popup card
           ▍版型改側欄（建議書 §三 桌機版）：移除「自選日期」與「常設活動」兩項篩選；原頂部懸浮篩選列（.hud/.bar）
             改為固定左側、寬 340px、滿版可捲動深色玻璃側欄（站名→#stat→搜尋→時間／活動形式／地區三分區）；
             手機版（≤600px）退化為頂部面板＋「篩選」(#fbtn)展開；縮放鈕移右下、.foot 右移避欄；popup autoPan 動態量測閃避
           ▍第二階段使用者功能：⑦「想去」收藏（localStorage key='acg_favs'，favKey=[v.name,e.t,e.s,e.l].join('¦')，
             免登入不跨裝置）＋側欄「♥ 想去 N」入口與收藏浮層 ⑧popup「導航」外部 Google Maps 連結（優先座標否則地址）
             ⑨popup「附近 2km 內還有 N 個活動」（haversine、通過篩選、依距離排序、點擊跳轉切換 popup）
             ⑩圖釘狀態：已收藏愛心 .favdot（頭部右側）、即將結束左上紅點 .soondot、活動數 .bd 右上，三者共存
           ▍圖釘外觀（2026/07/12，建議書 §5.2）：圓形＋場館 logo 圖釘改為「水滴造型＋依活動形式圖示」，
             不再用 logo；FORM_ICON（展覽=畫框／快閃店=購物袋／主題餐廳=杯子／體驗=星號／其他=定位點）＋
             venueForm(exs)＋pinSvg(form)；顏色僅作輔助。iconAnchor 移到水滴尖端 [20,50]、popup offset 改 (0,-46)。
目前錯誤： ①#sheet/#scrim/openSheet/cardHtml 及場館 logo 相關（loadPinLogo/observePinLogos/logoThumbUrl/ART）
           保留為休眠碼（未觸發，僅備用，未刪以縮小改動面）。②現資料（TODAY 基準）暫無「即將結束」活動，
           .soondot 紅點在現資料不會出現（邏輯已 runtime 模擬驗證）；已收藏愛心在群集併入時不顯示（叢集正常行為）。
           ③同一場館多形式時 pin 顯示「其他」定位圖示（代表形式無法唯一判定）。
           ▍來源收斂（2026/07/12）：政府（文化部）API 全停（refresh_venues.py USE_MOC=False，
             並關掉 moc 快照補填）；官網爬蟲只留六大園區（華山/松山/圓山花博/駁二/嘉義文創/花蓮文創，
             collect_venues.py VENUES 精簡＋update_all.py 停用 collect_public/collect_soka_art）；
             ANCHORS 精簡為四園區座標錨；新增官網優先「全域標題去重」（手動標題與官網重複則不寫入）。
             保留：手動 Excel（含早點出發）、CACO、Cayenne、補件層。已用過濾腳本清理現有 venues.json：
             場館 199→44、活動 406→128、ACG 49→46，並同步 HTML 內嵌備援。
目前錯誤： ①#sheet/#scrim/openSheet/cardHtml 及場館 logo 相關（loadPinLogo/observePinLogos/logoThumbUrl/ART）
           保留為休眠碼（未觸發，僅備用，未刪以縮小改動面）。②現資料（TODAY 基準）暫無「即將結束」活動，
           .soondot 紅點在現資料不會出現（邏輯已 runtime 模擬驗證）；已收藏愛心在群集併入時不顯示（叢集正常行為）。
           ③同一場館多形式時 pin 顯示「其他」定位圖示。④venue_extra.json 目前可能仍含舊的非六園區官網場館
           （上次爬蟲留下），下次 collect_venues 重跑才會覆蓋；如要提前乾淨可手動清該檔非六園區鍵。
           ⑤後台管線仍沿用舊 schema，schema 擴充/待審核流程尚未做。
下一步：   【第三階段：資料穩定（剩餘）】候選/待審核流程、資料異常偵測（突然消失/日期異常/重複）、schema 擴充。
           ⚠️ 任何 schema 擴充 / venues.json 欄位結構變更前，須先確認 DECISIONS.md（架構級決策不可貿然推翻）。
不要改動： ①data/manual/manual_extra.json / data/manual/全台ACG活動.xlsx 既有列 ②archive/backups/ 內歷史備份
           ③venues.json 欄位結構 ④前端請只改 public/taiwan-exhibition-map.html 這一個檔，
           不要新增檔案、不要動內嵌 DATA 與 Leaflet 函式庫區塊、不要重新引入已放棄的 build 流程
           ⑤政府 API 已「刻意」停用：重跑 update_all.py 後筆數大幅下降是預期結果，不要視為異常而回退或觸發警報
           （恢復政府來源才改 refresh_venues.py 的 USE_MOC=True）
目前錯誤： （續）▍維護回報排呈（2026/07/12）：backend/report_status.py 已調整，配合地圖收斂為
           「ACG＋六大園區」後不再有logo問題：移除「缺場館logo」統計/建議（⚠️AI判斷，非逐字指示，
           需你覆核是否同意）；保留缺KV／約略定位／缺連結；新增「分類複核」章節，逐筆列出
           src=='official' 且 c!='ACG' 的官網活動，供人工複核後補 data/manual/event_overrides.json
           （不用改程式碼）。✅已驗證：py_compile 通過、實際跑過一次對照真實 public/venues.json
           輸出正確；⚠️未驗證：尚未跑到下次 Claude 排程 exhibition-map-maintenance-report 的正式觸發。
           ▍分類複核＋補Excel（2026/07/12 續）：逐筆過官網六大園區70筆非ACG候選（另3筆已由前一輪
           流程補進Excel改判成功：好想兔/nagano market/MONSTER STRIKE），查證後與你確認，3筆高信心
           候選（Baby Shark守護海洋大冒險、星際大戰Mission Cantina、NishimuraYuji's shop!）已補進
           data/manual/全台ACG活動.xlsx（先備份於archive/backups/excel/，111→114列原始資料不動、
           末新增3列）；B-SIDE LABEL／開心馬場×2／果子們特展／鮮乳偵探事務所查無角色IP授權來源，
           經你確認暫不列入。✅已驗證：openpyxl讀回檔案dims=A1:Q115，原有列內容比對備份未變、
           新增3列17欄逐欄核對正確。⚠️未驗證：尚未跑import_acg_excel.py/update_all.py（需Mac端瀏覽器）
           讓這3筆真正合併回venues.json；Baby Shark的主辦/授權資訊取自同巡迴台北科教館場次，
           非駁二官網頁面直接證實，待你覆核。詳見 Agent交流工作日誌.txt 同日條目。
已完成：   【2026/07/13 排程回報延伸手動修資料缺口，Cowork】KV補3場（GANADI/蠟筆小新/狗狗派對）；
           event_overrides.json補2場分類為ACG（B-SIDE LABEL POP UP STORE in Taiwan、愛麗絲夢遊仙境）
           ⚠️B-SIDE LABEL與07/12日誌記載的「已確認排除ACG」矛盾，需你覆核是否刻意改變心意；
           GANADI POP-UP依規則9從1列展開為4列（台北微風南山/新竹巨城/台中綠園道/高雄夢時代，地址
           皆已查證且你已確認無誤）；花蓮鯉魚潭/香堤大道廣場補座標（香堤大道用你提供的座標，查無
           正式門牌）。跑完import→refresh→geocode→refresh後51館全數loc=exact（原8館約略定位→0）。
           同步修好HTML內嵌DATA備援（之前手動分段跑腳本漏了這步，導致你回報「地圖沒更新」）。
           排程任務 exhibition-map-maintenance-report 已改版：機械性地址/座標缺口可自動修正+跑
           pipeline+同步HTML內嵌，ACG分類複核維持只列清單人工確認（你已用AskUserQuestion確認此邊界）。
           ✅已驗證：重讀venues.json/xlsx/event_overrides.json/HTML內嵌逐項核對，見Agent交流工作
           日誌.txt同日條目。
目前錯誤：（續）▍2026/07/13 踩到 openpyxl `insert_rows()` 不會搬移既有儲存格 Hyperlink 物件的坑，
           曾一度讓不相關資料的舊超連結覆蓋新資料KV欄，已修好並改用「附加表尾」方式，詳見日誌；
           之後任何人編輯 全台ACG活動.xlsx 展開多列，禁止用 insert_rows。
           ▍`data/manual/_excel_backups/全台ACG活動_CORRUPTED_had_stray_hyperlink_20260713.xlsx`
           是修復過程中留下的損毀中間版本備份，Cowork沙盒環境對這個掛載資料夾裡的既有檔案沒有
           刪除權限，刪不掉，需 Daniel 自己在 Finder 刪除。
下一步：   ⚠️請 Daniel 覆核「B-SIDE LABEL POP UP STORE in Taiwan」分類矛盾（07/12排除ACG vs
           07/13指示是ACG），確認後續以哪個為準。
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
