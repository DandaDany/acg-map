#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""產生「資料缺口」報表：機器讀的 KV JSON ＋ 人看的合併缺口清單。

背景：舊版 _missing_event_kv.json 是專案初始 commit 的文化部（moc）美術館快照，來源已於
2026/07/12 停用，且沒有任何步驟會重產它，長期停在舊資料、看它會被誤導。本腳本改為每次
update_all 之後、依「最終版 venues.json」重新產生準確報表，並把三種缺口併成一份好找的清單。

只讀 venues.json，不連網、不改資料本體。涵蓋三種缺口：
  1) KV（主視覺）——每筆活動的 img 分成：
     - ok       ：img 已自存到 public/kv/（站內相對路徑，穩定不破圖）
     - empty    ：完全沒有主視覺
     - expiring ：img 仍指向會過期的 FB/IG 簽章網址（cdninstagram/fbcdn 或帶 oe=），多數數天內
                  就破圖；能從 oe= 解出到期日者一併標出（過去式＝現已破圖）→ 須人工補
     - remote   ：img 仍指向其他外站、尚未自存（例如官網圖，下輪 download_event_kv 可自存）
  2) 缺官方連結——活動沒有 e.l。
  3) 約略定位——場館 loc 非 exact（座標不精準）。

輸出：
  - data/reports/_missing_event_kv.json：機器讀的 KV 風險清單（empty/expiring/remote 三類）。
  - docs/資料缺口清單.md：人看的合併清單。只要看這份就知道目前所有活動缺什麼
    （KV 破圖/待補、缺官方連結、約略定位）。
  - stdout 另印一行 summary JSON 供管線觀察。

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


def _status_label(r):
    if r["reason_code"] == "empty":
        return "無圖"
    if r["reason_code"] == "expiring":
        exp = r.get("expiry") or "未知"
        return f"已過期破圖（到期 {exp}）" if r.get("expired_now") else f"會過期（到期 {exp}）"
    return "尚未自存（外站官網圖，下次 update_all 可自動修）"


def missing_links(venues):
    """回傳沒有官方連結（e.l 為空）的活動 [(場館, 活動)]。"""
    out = []
    for v in venues:
        for e in v.get("ex", []):
            if not (e.get("l") or "").strip():
                out.append((v.get("name", ""), e.get("t", "")))
    return out


def approx_locations(venues):
    """回傳座標為約略定位（loc 非 exact）的場館名。"""
    return [v.get("name", "") for v in venues if v.get("loc") and v.get("loc") != "exact"]


RAW_BASE = "https://raw.githubusercontent.com/DandaDany/acg-map/main/data/manual/_kv_cache/"


def build_markdown(venues, today=None):
    """把 KV／缺連結／約略定位三種缺口組成一份人看的合併清單 Markdown。"""
    rows, summary = build_report(venues, today=today)
    manual = [r for r in rows if r["reason_code"] == "expiring"]  # FB/IG 會過期，須人工
    auto = [r for r in rows if r["reason_code"] != "expiring"]    # 官網外站圖，多可自動自存
    miss_link = missing_links(venues)
    approx = approx_locations(venues)
    n_e = summary["total_events"]
    n_v = len(venues)

    L = []
    L.append("# 資料缺口清單")
    L.append("")
    L.append(f"產生日期：{summary['generated']}　"
             "本檔由 `backend/report_event_kv.py` 隨 `update_all.py` 自動重產，請勿手改。")
    L.append("")
    L.append("看這份即知目前所有活動缺什麼：① KV 主視覺（破圖/待補）② 缺官方連結 ③ 約略定位。")
    L.append("")
    L.append("## 總覽")
    L.append("")
    L.append("| 缺口 | 數量 |")
    L.append("|---|---|")
    L.append(f"| 活動總數 | {n_e} |")
    L.append(f"| KV 已自存（穩定） | {summary['ok_selfhosted']} |")
    L.append(f"| KV 有風險（破圖/待補） | {summary['at_risk']}（含已破圖 {summary['expired_now']}） |")
    L.append(f"| 缺官方連結 | {len(miss_link)} |")
    L.append(f"| 約略定位（場館） | {len(approx)} / {n_v} |")
    L.append("")

    # ── ① KV ──
    L.append("## ① KV 主視覺")
    L.append("")
    L.append("補圖 SOP（A 區每筆照做，比照『藍色監獄×指南針武昌店』那筆）：")
    L.append("")
    L.append("1. 開該筆「來源連結」的 FB/IG 貼文，找官方主視覺（hi-res）。")
    L.append("2. 下載存到 `data/manual/_kv_cache/`，檔名建議 `作品_場地_YYYYMMDD.jpg`。")
    L.append(f"3. 在 `data/manual/acg_events.json` 對應活動的 `KV` 欄改成 repo 內永久 raw URL：`{RAW_BASE}<檔名>`")
    L.append("4. commit（含圖檔）。下次 `update_all.py` 的 `download_event_kv` 會再自存到 `public/kv/`，雙保險。")
    L.append("")
    L.append(f"### A. KV 需人工補（FB/IG 會過期，無法自動抓回）— {len(manual)} 筆")
    L.append("")
    if manual:
        L.append("| # | 完成 | 場館 | 活動 | 狀況 | 來源連結 |")
        L.append("|---|---|---|---|---|---|")
        for i, r in enumerate(manual, 1):
            L.append(f"| {i} | ☐ | {r['venue']} | {r['title']} | {_status_label(r)} | {r['link'] or '—'} |")
    else:
        L.append("（目前無此類）")
    L.append("")
    L.append(f"### B. KV 官網外站圖（下次 update_all 自動自存，通常免手動）— {len(auto)} 筆")
    L.append("")
    if auto:
        L.append("| # | 場館 | 活動 | 狀況 | 來源連結 |")
        L.append("|---|---|---|---|---|")
        for i, r in enumerate(auto, 1):
            L.append(f"| {i} | {r['venue']} | {r['title']} | {_status_label(r)} | {r['link'] or '—'} |")
    else:
        L.append("（目前無此類）")
    L.append("")

    # ── ② 缺官方連結 ──
    L.append(f"## ② 缺官方連結 — {len(miss_link)} 筆")
    L.append("")
    L.append("補法：把官方活動頁/貼文網址加進 `data/manual/event_link_overrides.json`。")
    L.append("")
    if miss_link:
        L.append("| # | 場館 | 活動 |")
        L.append("|---|---|---|")
        for i, (vn, t) in enumerate(miss_link, 1):
            L.append(f"| {i} | {vn} | {t} |")
    else:
        L.append("（目前無此類）")
    L.append("")

    # ── ③ 約略定位 ──
    L.append(f"## ③ 約略定位（非精確座標）— {len(approx)} 館")
    L.append("")
    L.append("補法：補完整地址後跑 `geocode_venues.py`（或在 `venue_geocodes.json` 補精準座標）。")
    L.append("")
    if approx:
        L.append("| # | 場館 |")
        L.append("|---|---|")
        for i, vn in enumerate(approx, 1):
            L.append(f"| {i} | {vn} |")
    else:
        L.append("（目前無此類）")
    L.append("")
    return "\n".join(L)


def main():
    data = json.load(open(P("venues.json"), encoding="utf-8"))
    venues = data.get("venues", [])
    rows, summary = build_report(venues)
    json.dump(rows, open(P("_missing_event_kv.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    open(P("資料缺口清單.md"), "w", encoding="utf-8").write(build_markdown(venues))
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
