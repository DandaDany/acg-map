# data

後台資料層，依資料性質分區。

- `manual/`：人工維護資料，最需要小心。
- `generated/`：管線可重建的中繼資料。
- `cache/`：可重抓的外部查詢快取。
- `logos/`：logo 對照與 fallback metadata。
- `reference/`：穩定參考資料。
- `reports/`：稽核報告與缺漏清單。

前端實際公開資料在 `public/`，不是這裡。
