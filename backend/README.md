# backend

後台資料管線與維護工具。

主要入口：
- `update_all.py`：完整更新流程。
- `refresh_venues.py`：合併各來源並輸出 `public/venues.json`。
- `paths.py`：集中管理所有資料夾與檔案路徑。

常見工具：
- `collect_*.py`：來源收集、logo/KV 補件、品牌資料匯入。
- `import_acg_excel.py`：把 `data/manual/全台ACG活動.xlsx` 轉成 `manual_extra.json`。
- `geocode_venues.py`：補精準座標。
- `build_logo_thumbs.py`：產生 `public/logos/_thumbs/`。

新增或移動資料檔時，優先更新 `paths.py`，不要在腳本中寫死根目錄路徑。
