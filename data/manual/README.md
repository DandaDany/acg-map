# data/manual

人工維護資料與未來後台表單最可能直接管理的資料。

重要檔案：
- `全台ACG活動.xlsx`：使用者維護的 ACG 活動來源。
- `manual_extra.json`：Excel 匯入後的 ACG 活動持久層。
- `manual_permanent_extra.json`：長期保留的手動活動。
- `venue_corrections.json`：場館修正規則。
- `venue_address_overrides.json`：場館地址覆寫。
- `event_link_overrides.json`：活動連結覆寫。
- `venue_event_sources.json`：官方展覽來源補強。
- `venue_geocodes.json`、`address_geocodes.json`：已確認精準座標。

原則：這裡的資料不要被爬蟲任意覆蓋。
