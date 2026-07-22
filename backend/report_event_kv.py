#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""產生「活動主視覺（KV）健康度」報表 → data/reports/_missing_event_kv.json。

背景：舊版這份報表是專案初始 commit 的文化部（moc）美術館快照，來源已於
2026/07/12 停用，且沒有任何步驟會重產它，長期停在舊資料、看它會被誤導。
本腳本改為每次 update_all 之後、依「最終版 venues.json」重新產生準確報表。

判斷方式（只讀 venues.json，不連網、不改資料本體）：
  - ok            ：img 已自存到 public/kv/（站內相對路徑，穩定不破圖）
  - empty         ：完全沒有主視覺
  - expiring      ：img 仍指向會過期的 FB/IG 簽章網址（cdninstagram/fbcdn 或帶 oe=），
                    多數數天內就破圖；能從 oe= 解出到期日者一併標出（過去式＝現已破圖）
  - remote        ：img 仍指向其他外站、尚未自存（例如官網圖，下輪 download_event_kv 可自存）

輸出：把 empty / expiring / remote 三類「有風險」的活動逐筆寫進報表，
ok 的不列入。stdout 另印一行 summary JSON 供管線觀察。

用法：python3 backend/report_event_kv.py
"""
import datetime
import json
from urllib.parse import urlparse, parse_qs

from paths import path as P

KV_PREFIX = "kv/"
EXPIRING_MARKERS = ("cdninstagram.com", "fbcdn.net")


def _oe_expiry(url):
    """從 FB/IG 簽章網址的 oe= 參數解出到期日（UTC）；解不出回傳空字串。"""
    try:
        q = parse_qs(urlparse(url).query)
        if "oe" in q:
            ts = int(q["oe"][0], 16)
            return datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
    except Exception:
        pass
    return ""


def kv_status(img):
    """回傳 (reason_code, expiry)。reason_code ∈ {ok, empty, expiring, remote}。"""
    u = str(img or "").strip()
    if not u:
        return "empty", ""
    if u.startswith(KV_PREFIX):
        return "ok", ""
    if u.startswith("http"):
        if "oe=" in u or any(m in u for m in EXPIRING_MARKERS):
            return "expiring", _oe_expiry(u)
        return "remote", ""
    return "ok", ""  # 其他站內相對路徑也視為 ok


REASON_TEXT = {
    "empty": "沒有主視覺",
    "expiring": "遠端會過期(FB/IG簽章網址)",
    "remote": "遠端未自存",
}


def build_report(venues, today=None):
    """回傳 (rows, summary)。rows 只含有風險的活動。"""
    today = today or datetime.date.today().isoformat()
    rows = []
    counts = {"ok": 0, "empty": 0, "expiring": 0, "remote": 0}
    expired_now = 0
    for v in venues:
        for e in v.get("ex", []):
            code, expiry = kv_status(e.get("img"))
            counts[code] += 1
            if code == "ok":
                continue
            already = bool(expiry and expiry < today)
            if already:
                expired_now += 1
            rows.append({
                "venue": v.get("name", ""),
                "title": e.get("t", ""),
                "reason": REASON_TEXT.get(code, code),
                "reason_code": code,
                "expiry": expiry,           # 僅 expiring 類可能有值
                "expired_now": already,     # True＝到期日已過、現正破圖
                "link": e.get("l", ""),
                "img": str(e.get("img", "")),
            })
    # 破圖風險（現已過期）排最前，其次會過期、無圖、一般遠端
    order = {"expiring": 0, "empty": 1, "remote": 2}
    rows.sort(key=lambda r: (not r["expired_now"], order.get(r["reason_code"], 9)))
    total = sum(counts.values())
    summary = {
        "generated": today,
        "total_events": total,
        "ok_selfhosted": counts["ok"],
        "empty": counts["empty"],
        "expiring_remote": counts["expiring"],
        "expired_now": expired_now,   # 其中到期日已過、地圖現正破圖的筆數
        "other_remote": counts["remote"],
        "at_risk": len(rows),
    }
    return rows, summary


def main():
    data = json.load(open(P("venues.json"), encoding="utf-8"))
    venues = data.get("venues", [])
    rows, summary = build_report(venues)
    json.dump(rows, open(P("_missing_event_kv.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
