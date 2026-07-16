# 技術決策紀錄（DECISIONS.md）

最後確認：2026/07/01
確認方式：實際讀取專案內 `README.md`、`專案交接文件.md`、`geocode_venues.py`、`_audit_arcgis_candidates.py` 與檔案清單比對，非憑記憶推測。

本檔案回答兩個問題：
1. 這個專案「現在」實際用什麼技術（有憑有據，可回頭查來源）。
2. 哪些決策已經投入到程式邏輯或資料結構裡，**改變的代價很高、等於重來**（不能反悔的決策）。

---

## 一、目前確認使用的技術

### 前端
- 純靜態單頁 HTML（`taiwan-exhibition-map.html`），無框架、無 build 工具。
- 地圖函式庫：Leaflet.js + Leaflet.markercluster（圖釘群集）。
- 街道底圖：MapLibre GL JS，透過 `leaflet-maplibre-gl` 外掛接入 Leaflet；樣式為 OpenFreeMap Positron，圖磚來源 `tiles.openfreemap.org`；函式庫由 unpkg CDN 載入。
- 鄉鎮界：g0v `twTown1982` GeoJSON，簡化後內嵌於 HTML，作淡色輔助框線。
- 資料載入：執行時 `fetch('venues.json')`；`file://` 離線模式改用 HTML 內嵌備援資料（`let DATA=...`），由 `update_all.py` 末段自動同步。

### 後端／資料管線
- Python 3 腳本，無資料庫，資料一律以 JSON 檔案落地（`venues.json`、`venue_extra.json`…）。
- 爬蟲：Playwright（headless Chromium）。
- Excel 處理：openpyxl。
- HTTP：Python 內建 `urllib`，並自訂放寬版 SSL context（因應部分政府憑證缺 Subject Key Identifier 導致新版 OpenSSL 驗證失敗）。
- 定位（geocoding）：**OpenStreetMap Nominatim**（保守 POI 比對，見 `geocode_venues.py`）為主要方案，輔以 ArcGIS 候選比對（`arcgis_geocode_cache.json`、`_audit_arcgis_candidates.py`）。**尚未**採用 TGOS 或 Google Geocoding API——`專案交接文件.md` §11／§14 明確列為待辦，需金鑰。

### 資料來源（四層，來源自 `專案交接文件.md` §3）
1. 文化部開放資料「藝文活動」API（`cloud.culture.tw`，`category=6` 展覽）。
2. 各館官網爬蟲：`collect_venues.py`（通用）＋ `collect_public.py`（客製，如新竹市美術館／關渡／C-LAB）。
3. `refresh_venues.py` 內建 `ANCHORS` 編輯整理層。
4. `manual_extra.json`：使用者手動整理的 ACG 活動持久層。

### 排程／自動化
- macOS **launchd**（非 cron），每週一 11:00 執行 `update_all.py`；設定檔 `~/Library/LaunchAgents/com.danielcheng.twexhibmap.plist`。
- `report_status.py` 由 Claude 排程每週一／四 11:13 執行。
- 排程只在使用者本機 Mac 上有效——沙箱環境連不到多數 `.gov.tw`。

### 部署
- 純靜態網站，`README.md`／`專案交接文件.md` 建議可上 GitHub Pages，但**目前未確認已實際部署**，僅為建議，需人工確認。

---

## 二、不能反悔的決策

以下區分兩類，依你的規則分開列：

### （A）文件中已明確載明、屬既定決策（有直接來源）

1. **純靜態架構，不引入後端伺服器或資料庫。** 來源：`專案交接文件.md` §1／§13。改為動態後端需重寫前端讀取邏輯與整個部署方式。
2. **HTML 已放棄 `build2.py` 產生流程，改為直接手動編輯 `taiwan-exhibition-map.html`。** 來源：`專案交接文件.md` §7「注意」、`README.md`「維護重點」。這條路已經走回頭——代表往後也要接受手動編輯 HTML 的維護方式。
3. **分類採兩正交軸**（主題 `c`：ACG／藝術設計／其他文化；形式 `c2`：展覽／快閃店／主題餐廳／體驗活動／其他），非單一分類欄位。來源：`README.md`「資料來源」段、`分類重構規格_for_ClaudeCode.md`。已寫入 `refresh_venues.py` 分類邏輯與前端篩選按鈕的 `data-c` 字串契約，兩邊字串必須完全一致，改分類要同步動前後端。
4. **座標聚合合併門檻定為 0.003°（≈330m）**，由原本 0.01° 收緊而來。來源：`專案交接文件.md` §0／§6。這是為了不把相距約 1km 的不同館誤併，是已修正過的教訓，不宜再放寬。
5. **`manual_extra.json`（使用者手動 ACG 資料）為持久層，每次自動更新一律併入、不被自動下架清除**（只有 `endDate < 今天` 才會過期略過）。來源：`專案交接文件.md` §3 第四層、§10。`README.md` 也明列「不要改動 `manual_extra.json` 既有列」。
6. **圖片／KV 嚴格驗證，寧可留空也不放錯圖。** 來源：`README.md`「已知限制」、`專案交接文件.md` §6 步驟10。
7. **排除圖書館、郵政類場館，不收錄。** 來源：`專案交接文件.md` §6 步驟9、§11。
8. **協作流程硬性規定**：任何人（Claude／Claude Code／Codex／人類）每次改動結束前，必須（1）在 `Agent交流工作日誌.txt` 追加一筆紀錄、（2）覆蓋更新 `README.md` 的六欄交接狀態。來源：`README.md` 開頭「硬性規定」。這不是技術決策，但屬於已經確立、不能私自跳過的流程承諾。

### （B）AI 依現況判斷、非文件明文寫「不可逆」——標示為推論，供你覆核

> 以下是我根據現有程式與資料結構「反推」出來的判斷，不是專案文件裡白紙黑字寫「這條不能改」。列在這裡是因為改動代價明顯很高，但分類邊界本身有主觀成分，請你確認是否同意。

9. **venues.json 的欄位結構**（`name/city/la/lo/loc/src/addr/url/logo/ex[]` 等）已被前端 HTML 直接讀取、也被多個腳本（`collect_logos.py`、`report_status.py`、內嵌備援同步）依賴。改欄位名稱或巢狀結構屬於「schema 變更」等級，會牽動前端與至少 3 支腳本，建議視為不可逆操作，變更前应先跟你確認（依你的核心規則第 3 條）。
10. **`src` 來源標籤（moc/official/curated/manual）作為資料可信度與去重優先序依據**——`refresh_venues.py` 的合併/取代邏輯（第8步「取代為 official」）依賴這個欄位語意，改變其定義等同重寫合併規則。

---

## 三、可信度標示

- ✅ 已驗證：第一節「目前確認使用的技術」與第二節（A）類 8 項，均逐條核對 `README.md`／`專案交接文件.md`／實際程式碼（`geocode_venues.py`、`_audit_arcgis_candidates.py`）內容後才寫入，非憑推測。
- ⚠️ 部分驗證：「建議上 GitHub Pages」一項——文件只寫「建議」，未確認是否已實際部署，需你確認目前正式站台位置。
- ⚠️ 部分驗證：第二節（B）類 2 項為 AI 推論的「不可逆」判斷，不是文件明文結論，請你覆核是否同意分類。
- 驗證方式：`grep`／`Read` 直接讀取上述檔案原文比對，未執行程式碼、未改動任何原始資料。

---

## 需人工確認

- 是否已有實際部署位置（GitHub Pages 或其他），目前文件只到「建議」層級。
- 第二節（B）類兩項「不可逆」判斷是否同意；若不同意，請告知修改依據。
- 若之後要導入 TGOS／Google Geocoding API（`專案交接文件.md` §14 待辦），屬於新增付費/金鑰依賴，建議正式決策前再次確認。
