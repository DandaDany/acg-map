# data/manual

人工維護資料與未來後台表單最可能直接管理的資料。

重要檔案：
- `全台ACG活動.xlsx`：使用者維護的 ACG 活動來源。
- `manual_extra.json`：Excel 匯入後、依 Asia/Taipei 當日日期過濾的 ACG 活動中介層；活動到期後會從此檔移除，不是歷史活動或 geocode 的 SSOT。
- `manual_permanent_extra.json`：長期保留的手動活動。
- `venue_corrections.json`：場館修正規則。
- `venue_address_overrides.json`：場館地址覆寫。
- `event_link_overrides.json`：活動連結覆寫。
- `event_metadata_overrides.json`：主辦方、授權／權利方、形式與來源層級的人工查證覆寫。
- `venue_event_sources.json`：官方展覽來源補強。
- `venue_geocodes.json`、`address_geocodes.json`：已確認精準座標。
- `點點心門市地址_dimdimsum.json`、`凍心門市地址_frozenheart.json`：多門市聯名活動的人工門市參考清單。

原則：這裡的資料不要被爬蟲任意覆蓋。

六館官網的列表卡日期只可在明確卡片邊界內解析；駁二清單若未完整載入不得覆蓋昨日成果，
且其列表缺日期時應讀取官方詳情頁的結構化展期欄位。這些修正只影響 generated／public 衍生層，
不得回寫或改寫本目錄的人工 SSOT。
駁二即使回傳非空清單，只要相較昨日缺少官方結束日尚未到期的活動，就視為 AJAX 部分載入；保留本次新抓資料並補回仍有效的昨日活動，
已到期活動不受此保護，仍會依 Asia/Taipei 日期正常下架。

持久資料模型：歷史人工活動來源以 `acg_events.json` 為準；活動欄位決策以 metadata／admission 等 overrides 為準；場館地址與座標以 `venue_address_overrides.json`、`venue_geocodes.json` 為準。測試不得要求到期活動繼續留在 `manual_extra.json` 或 `public/venues.json`。`public/kv/` 同樣是依當期公開活動重建的衍生層；活動全部到期後，未再被引用的公開 KV 會由管線清理，測試只應保護人工來源列所引用的持久 KV，不得要求孤兒公開副本永久存在。所有「今天」、到期判斷、輸出日期與 Daily Update PR 日期一律以 Asia/Taipei 為準，不得依 runner 的 UTC 或本機時區漂移。

## ACG 活動品質門檻

- 主辦方是實際策劃／執行單位；授權欄是授權商，若官方只公開版權列則記錄權利方。不得填「官方」、「需人工確認」或空白。
- 活動連結優先使用 IP、品牌、主辦、場館的官方活動頁或官方貼文；其次才是正式售票／報名頁。只有前兩級都找不到時才可使用可信媒體，並在 `event_metadata_overrides.json` 填寫 `fallback_reason`。
- KV 必須保留原始來源。連結與 KV 可以來自不同頁，但兩者都必須是官方來源；若沒有更完整的官方活動頁，活動連結應與 KV 來源一致。社群 CDN 圖片需下載到 repository 保存。
- 形式只接受「展覽、快閃店、主題餐廳、體驗活動」。分類不明時停止輸出並交由編輯判定，不得回落到「其他」。
- `backend/_test_event_metadata_quality.py` 是硬性檢查；每日排程必須在開 PR 前通過，PR 不會自動合併。

## acg_events.json（Excel 的 diff 友善文字鏡像）

- 由 `backend/export_excel_to_json.py` 從 `全台ACG活動.xlsx` 匯出：頂層陣列，一元素 = 一列
  `{欄名: 值}`（保留欄位順序與所有欄；空格 → null；日期 → "YYYY-MM-DD HH:MM:SS"；
  儲存格超連結目標存於該列 `"_links": {欄名: 網址}`）。
- `backend/import_acg_excel.py` 若見到本檔會優先讀它（解析邏輯不變、輸出經驗證與 xlsx 路徑
  完全等值）；刪掉本檔即回退為讀 xlsx。
- 注意：xlsx 更新後需重跑 `python3 backend/export_excel_to_json.py`，否則 import 會讀到舊鏡像。

## review_decisions.json（審核決策持久層）

- 每日自動更新開 PR 供審核時，使用者「刪掉／拒絕」的活動記在 `rejected`；
  `backend/refresh_venues.py` 輸出 venues.json 前會依穩定鍵過濾，確保下次不再冒出來。
- 穩定鍵：`場館名|正規化標題|開始日(YYYY-MM-DD)`，由 `refresh_venues.stable_event_key()` 產生
  （標題正規化：strip、全形空白→半形並壓縮、去除前後標點、臺→台）。
- 範例（勿直接照抄進正式陣列，key 請用 stable_event_key 產生）：

  ```json
  {
   "rejected": [
    {"key": "松山文創園區|航海王特展|2026-08-01",
     "title": "航海王特展", "venue": "松山文創園區",
     "reason": "非 ACG／使用者於 PR 審核刪除", "date": "2026-07-17"}
   ],
   "approved": []
  }
  ```

- 復原：把該筆從 `rejected` 移除（或清空陣列）再重跑 refresh，活動即恢復輸出。
