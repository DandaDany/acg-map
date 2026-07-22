# 缺 KV 活動：原因分析與改善方法

盤點日期：2026/07/22　資料來源：`public/venues.json`（146 場活動）

## 一、現況（先修正一個誤解）

`data/reports/_missing_event_kv.json` 這份報表**已經過期、不可直接採信**：

- 它是專案初始 commit（`05e7180`）留下的舊快照，內容全是**文化部（`src:"moc"`）美術館／工藝館**活動。
- 文化部 API 來源已於 **2026/07/12 停用**（見 `report_status.py` 說明），這些活動早就不在現行資料裡。
- `update_all.py` 管線中**沒有任何步驟會重新產生這份報表**，所以它只會一直停在舊資料，看它會被誤導。

依現行 `venues.json` 實際盤點：

| 狀態 | 數量 |
|---|---|
| 活動總數 | 146 |
| 已自存到 `public/kv/`（穩定、不會破圖） | 115 |
| **完全沒有圖（img 為空）** | **0** |
| **仍引用外站遠端網址、未自存** | **31** ⚠️ |

也就是說「完全沒有 KV」的活動其實是 0，真正的問題是**另外 31 筆的圖是脆弱的外站連結**，其中大多數**現在就已經破圖**。

## 二、真正的問題與根本原因

### 問題 A：29／31 筆的 FB／IG 主視覺「已經過期、正在破圖」（最嚴重）

這 31 筆裡有 30 筆的 `img` 直接指向 `scontent*.cdninstagram.com` / `*.fbcdn.net` 的**臨時簽章網址**。這種網址帶 `oe=` 到期參數，數天～數週後必失效。把 `oe=` 解出來看：

- **29 筆的到期日已經是過去式**（2026-06-25 ~ 2026-07-16，今天已 07-22）→ **這些活動在地圖上此刻就是破圖**。
- 受影響的都是主打的 ACG 快閃／原畫展，例如：名偵探柯南快閃（多分店）、迷宮飯探索展、孤獨搖滾動畫展、Hello Kitty 展、藥師少女的獨語展、凡爾賽玫瑰、San-X 90 週年、誠品「夏日動漫時光機」展（4 分店）等。

**根本原因（鏈）：**

1. 這些活動多為 `src:"manual"`，在人工整理時**把 IG／FB 貼文當下的 CDN 簽章網址原封貼進 `img`**。
2. `download_event_kv.py --all` 本該把所有遠端圖自存到 `public/kv/`，但**跑到下載步驟時該簽章網址往往已過期／被 FB 擋外連 → 下載失敗**。
3. 依 `download_event_kv.py` 設計「下載失敗則保留原網址」，於是就**留下一個已經死掉的網址**，且每次 `update_all` 重跑都一樣救不回來。

> 專案其實**已經有正解範本**：`data/manual/acg_events.json` 裡「藍色監獄 × 指南針武昌店」那筆的做法——把 FB 官方主視覺**先下載、commit 進 `data/manual/_kv_cache/`，KV 欄改引用 repo 內永久 raw URL**，不再依賴會過期的 FB CDN。這正是應該推廣到其他 30 筆的做法。

### 問題 B：含空白／中文字的官網圖網址，自存時直接崩潰（`《天官賜福》`）

第 31 筆是華山官網的 `《天官賜福》`，網址是：

```
https://media.huashan1914.com/WebUPD/huashan1914/exhibition/華山官網活動 1920(W) x 1080(H)_1.jpg
```

網址路徑含**空白與中文字**。`download_event_kv.py` 的下載器**沒有先做 percent-encode**，`urllib.request.Request` 會直接丟 `InvalidURL: URL can't contain control characters`，於是這張圖**永遠自存失敗、只能留原始遠端網址**。（對照組：`collect_event_kv.py` 早就有 `quote_url()` 處理，`download_event_kv.py` 卻漏了。）

### 問題 C：缺 KV 報表沒有自動化、也沒有分類依據

`report_status.py` 只會列「缺 KV = img 為空」的活動（現在是 0），**不會**把「img 指向會過期外站網址」這種**假有圖、實破圖**的情況揪出來，也不會重產 `_missing_event_kv.json`。所以這類問題目前沒有任何自動預警。

## 三、已做的修正（本次 commit）

**修掉問題 B**：`backend/download_event_kv.py` 新增 `quote_url()`，下載前先 percent-encode 路徑／查詢字串（與 `collect_event_kv.py` 同手法）。含空白／中文的官網 KV 從此能正常自存到 `public/kv/`，不再破圖。已補離線單元測試 `test_quote_url`，全數通過。

## 四、建議的改善方法（依優先序）

1. **【最高】把 30 筆 FB／IG 主視覺改成「自存 raw」範本做法。**
   對每筆 ACG 快閃／原畫展，在**簽章網址還沒過期時**下載官方主視覺、commit 進 `data/manual/_kv_cache/`，`img`／KV 欄改引用 repo 內永久 raw URL（比照藍色監獄那筆）。之後 `download_event_kv` 會再自存到 `public/kv/`，雙保險。
   —— 這是唯一能根治「FB CDN 過期破圖」的做法，因為簽章網址本質上救不回。

2. **【流程】人工整理 manual 活動時，禁止直接貼 `cdninstagram.com` / `fbcdn.net` 簽章網址當 `img`。**
   一律走「下載→存 `_kv_cache/`→引用 raw URL」流程，並在 `docs` 的整理規範裡明文寫死。

3. **【自動預警】把 `report_status.py` 的「缺 KV」判斷從「img 為空」擴大為「img 為空 **或** img 仍指向會過期外站網址（含 `oe=`／`cdninstagram`／`fbcdn`）」**，並讓 `update_all.py` 每輪重新產生一份**準確的** `_missing_event_kv.json`（取代目前那份舊文化部快照）。這樣破圖能在報表就被抓到，而不是等使用者發現。

4. **【強韌化，選配】給 `download_event_kv.py` 的 FB／IG 下載補 `Referer` 標頭與瀏覽器 fallback**，提高「簽章還沒過期時」自存成功率；但這只是提高成功率，**不能取代第 1、2 點**（已過期者仍救不回）。

## 附錄：目前 31 筆脆弱 KV 清單

見盤點腳本輸出；29 筆 `oe=` 到期日已早於今天（2026-07-22），即現在就破圖。集中在：名偵探柯南快閃（信義 A8／林口 outlet／台中中友／高雄夢時代等多分店）、誠品「夏日動漫時光機」展（新店／松菸／武昌／西門）、凱岩主題餐廳（楓之谷／賽爾號）、迷宮飯、孤獨搖滾、Hello Kitty 展、藥師少女的獨語、凡爾賽玫瑰、San-X 90 週年、JOJO、GODZILLA STORE 等。
