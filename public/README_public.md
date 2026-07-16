# public

靜態網站公開目錄。

檔案：
- `taiwan-exhibition-map.html`：前端地圖頁。
- `venues.json`：前端即時讀取的資料。
- `logos/`：前端可直接載入的 logo 圖片。

本機預覽：

```bash
cd public
python3 -m http.server 8000
```

網站部署時，這個資料夾就是最接近可發布內容的區塊。
