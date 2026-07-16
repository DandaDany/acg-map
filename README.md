# 全台展覽地圖

專案已整理成後台導向結構：

- 前端公開檔：`public/`
- 後台資料管線：`backend/`
- 資料層：`data/`
- 文件與交接：`docs/`
- 排程與維運：`ops/`
- 執行期狀態：`runtime/`
- 歷史備份：`archive/`

請先看：

- `docs/README.md`
- `docs/後台資料夾結構.md`

常用指令：

```bash
python3 backend/update_all.py
cd public
python3 -m http.server 8000
```
