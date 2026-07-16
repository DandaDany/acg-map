# 🔴 BUG 工單：文化部場館大量消失（資料遺失，最高優先）

開單：2026/06/27　技術主管：Claude（網頁維護員）　執行：Claude Code
優先級：P0（資料遺失，先於 logo 修復與分類重構）

---

## 1. 問題（一句話）
06/27 跑完 update_all.py 後，venues.json 的場館從 224 掉到 81，活動從 449 掉到 215，且**幾乎全集中在文化部（moc）層**。這不是自然到期，是流程出包。

## 2. 證據（我已量測，請以此為基準）
| 指標 | 06/25 快照(_report_prev.json, 229KB) | 06/27 現在(venues.json, 109KB) |
|---|---|---|
| 場館數 | 224 | **81** |
| 活動數 | 449 | **215** |

- 06/27 現在各來源(src)分布：`official=23, moc=12, curated=5, manual=36, caco=3, cayenne=2`。
- **moc（文化部）層從約 140 崩到只剩 12**；其餘層（manual/official/caco/cayenne）大致完好。
- 到期分析：現有資料中「結束日 < 今天」的活動只有 **12 個**。→ 根本無法解釋少掉的 234 個活動 / 143 個場館。**排除「自然到期」。**

## 3. 最可能原因（依可能性排序，請逐一驗證，不要只重跑碰運氣）
- **H1：文化部 API 抓取步驟回傳變少/失敗**（collect_public.py 或文化部 open-data 抓取）。可能是網路逾時、API 分頁、或 API 改版導致只拿到一小部分，且回傳碼仍為 0 → update_all 不會 sys.exit、照樣輸出殘缺 venues.json。
- **H2：近期程式改動過度過濾掉 moc 層**。檢查 refresh_venues.py 的策展/砍場館篩選（KEEP_NAME / CUT_A / CUT_B / HIST_KEEP / 圖書館郵政排除 等）以及任何分類相關改動，是否誤砍文化部場館。（注意：本專案近期有「分類重構」與你 Claude Code 介入，務必看 git diff。）
- **H3：update_all.py 某步驟 soft-fail**（回傳 0 但資料不全），中繼檔（venue_extra.json / 文化部 raw cache）在 06/27 變空或變小。

## 4. 診斷步驟（請依序做，附判斷準則）
1. **直接打文化部 API 數筆數**（我的沙盒被擋，Mac 端可做）：
   ```
   curl -s 'https://cloud.culture.tw/frontsite/trans/SearchShowAction.do?method=doFindTypeJ&category=6' | python3 -c "import sys,json;d=json.load(sys.stdin);print('API 回傳筆數:',len(d))"
   ```
   - 回幾百筆 → 問題在我們的處理（往 H2/H3 查）。
   - 回很少 → 往 API 用法/分頁/改版查（H1），確認是不是要分頁或換參數。
2. **看執行 log**：`_scheduled_update.log` 06/27 那次，找 collect_public.py / collect_venues.py 步驟有無錯誤、警告、抓到 0 筆。
3. **比對消失清單**：讀 `_report_prev.json`(06/25) 與現在 `venues.json`，列出消失的 moc 場館及其「最後檔期」；若多數仍有未來檔期(≥今天)=不該掉，坐實是流程吃掉的。
   （註：_report_prev.json 在我這端常被 mount 鎖住讀不到，Mac 端應正常。）
4. **看程式改動**：`git diff`（或備份比對）refresh_venues.py、collect_public.py 自 06/25 以來的變更；確認分類重構/篩選是否誤砍。
5. **看中繼檔**：venue_extra.json 與文化部 raw 快取檔在 06/27 的大小/筆數是否異常變小。

## 5. 修復標準（驗收條件）
- 找出 **root cause**（API 用法 / 篩選 bug / soft-fail 其一），不是只重跑一次。
- moc 層場館數回到與 06/25 相當（扣掉真正到期者）。
- **不得破壞** manual(36)/official(23)/caco/cayenne 層。
- 若是 soft-fail：在 update_all.py 對該步驟加「抓到筆數過低就中止、保留上一版 venues.json」的保護，避免再次默默輸出殘缺資料。

## 6. 驗證方式（修完必跑，符合「已完成≠完成」）
- 重跑 update_all.py 後，輸出：場館數、各 src 分布、活動數，與 06/25(224/449) 對照，差異需能用「真正到期」解釋。
- 列「相比 06/25 仍消失、但仍有未來檔期」的場館 → 應為 0 或逐一可解釋。
- 把結論與 root cause 寫進 Agent交流工作日誌.txt。

## 7. 注意
- 先備份現有 venues.json 再動。
- 這張單(P0)優先於：①logo DDG favicon 根本修復、②分類重構規格——但三者可一起在同一輪處理。
- 我(技術主管)這端已先把當前地圖的 59 個 DDG favicon 錯圖退回預設；那是另一件事，與本工單無關。
