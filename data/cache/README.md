# data/cache

外部查詢與圖片驗證快取。

常見檔案：
- `enrich_cache_v3.json`：活動連結驗證與 og:image 快取。
- `imgcache_v3.json`：圖片可用性快取。
- `event_kv_cache.json`：活動主視覺補抓快取。
- `geocode_cache.json`、`arcgis_geocode_cache.json`：地理編碼查詢快取。
- `_short_url_resolved.json`：短網址解析快取。

原則：可刪除重建，但刪除後下一次更新會變慢或重新打外部服務。
