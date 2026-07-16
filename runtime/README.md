# runtime

本機執行期狀態，不屬於資料模型。

- `logs/`：排程與手動更新 log。
- `state/`：lock、last success 等狀態檔。
- `debug/`：除錯輸出。
- `profiles/`：Playwright/Chrome profile。
- `cache/`：Python pycache 等本機快取。

原則：這裡可以協助診斷，但不應作為正式資料來源。
