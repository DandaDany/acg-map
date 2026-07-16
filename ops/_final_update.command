#!/bin/bash
# 最後一次完整更新：在真機跑 update_all.py（collect_venues → collect_public(含C-LAB) → refresh）。
# 由 Claude 建立。先備份產物 → 完整跑 → 全程寫 log。可安全重複執行。
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
TS=$(date +%Y%m%d_%H%M%S)
mkdir -p runtime/logs archive/backups/manual-run
LOG="runtime/logs/final_update_${TS}.log"
PY=/Users/daniel0522/miniforge3/bin/python3
{
  echo "=== 完整更新開始 $(date '+%Y-%m-%d %H:%M:%S') ==="
  echo "python: $PY"; "$PY" --version
  echo "--- 備份產物 ---"
  cp -v public/venues.json "archive/backups/manual-run/venues.json.bak_${TS}"
  cp -v data/generated/venue_extra.json "archive/backups/manual-run/venue_extra.json.bak_${TS}"
  echo "--- 跑 backend/update_all.py（collect_venues → collect_public → refresh）---"
  "$PY" backend/update_all.py 2>&1
  echo "--- C-LAB 結果檢查 ---"
  "$PY" - << 'PYEOF'
import json
d=json.load(open("public/venues.json"))
for t in ["C-LAB","關渡","新竹市美術館","蕭壠","台北當代藝術館","鳳甲"]:
    v=next((v for v in d["venues"] if t in v["name"]), None)
    if v: print(f'  {v["name"]}: src={v.get("src")} 展覽{len(v["ex"])}筆 -> {[e["t"][:22] for e in v["ex"][:4]]}')
    else: print(f'  {t}: 不在')
print("總場館:", len(d["venues"]))
PYEOF
  echo "=== 完整更新結束 $(date '+%Y-%m-%d %H:%M:%S') ==="
} 2>&1 | tee "$LOG"
echo ""; echo "完成。輸出在 $LOG（此視窗可關閉）"
