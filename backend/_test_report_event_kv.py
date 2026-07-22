#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""report_event_kv 的離線單元測試（不連網）。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import report_event_kv as m


def test_kv_status():
    assert m.kv_status("kv/abc.jpg") == ("ok", "")
    assert m.kv_status("") == ("empty", "")
    assert m.kv_status(None) == ("empty", "")
    # 一般外站官網圖：尚未自存
    assert m.kv_status("https://www.g9cip.com/b.png") == ("remote", "")
    # FB/IG 簽章網址（host 標記）→ expiring
    code, exp = m.kv_status("https://scontent.cdninstagram.com/a.jpg")
    assert code == "expiring"
    code, exp = m.kv_status("https://instagram.frmq3-3.fna.fbcdn.net/a.jpg")
    assert code == "expiring"
    # 帶 oe= 者能解出到期日
    # oe=6A4BC1D8 → 2026-07-06（UTC）
    code, exp = m.kv_status("https://x/a.jpg?oe=6A4BC1D8")
    assert code == "expiring" and exp == "2026-07-06", (code, exp)
    print("test_kv_status: PASS")


def test_build_report():
    venues = [
        {"name": "館A", "ex": [
            {"t": "已自存", "img": "kv/deadbeef.jpg"},
            {"t": "無圖", "img": ""},
            {"t": "會過期且已破圖", "l": "L1", "img": "https://scontent.cdninstagram.com/a.jpg?oe=6A4BC1D8"},  # 2026-07-06
            {"t": "官網未自存", "img": "https://www.g9cip.com/b.png"},
        ]},
    ]
    rows, summary = m.build_report(venues, today="2026-07-22")
    assert summary["total_events"] == 4
    assert summary["ok_selfhosted"] == 1
    assert summary["empty"] == 1
    assert summary["expiring_remote"] == 1
    assert summary["expired_now"] == 1        # 07-06 < 07-22
    assert summary["other_remote"] == 1
    assert summary["at_risk"] == 3            # ok 不列入
    # 排序：現正破圖者排最前
    assert rows[0]["title"] == "會過期且已破圖" and rows[0]["expired_now"] is True
    titles = {r["title"] for r in rows}
    assert "已自存" not in titles
    print("test_build_report: PASS")


def test_missing_links_and_approx():
    venues = [
        {"name": "館A", "loc": "exact", "ex": [
            {"t": "有連結", "l": "https://x", "img": "kv/a.jpg"},
            {"t": "沒連結", "l": "", "img": "kv/b.jpg"},
        ]},
        {"name": "館B", "loc": "approx", "ex": [{"t": "無 l 鍵", "img": "kv/c.jpg"}]},
    ]
    assert m.missing_links(venues) == [("館A", "沒連結"), ("館B", "無 l 鍵")]
    assert m.approx_locations(venues) == ["館B"]
    print("test_missing_links_and_approx: PASS")


def test_build_markdown():
    venues = [
        {"name": "館A", "loc": "approx", "ex": [
            {"t": "已自存", "l": "https://x", "img": "kv/deadbeef.jpg"},
            {"t": "FB破圖", "l": "https://instagram.com/p/x", "img": "https://scontent.cdninstagram.com/a.jpg?oe=6A4BC1D8"},
            {"t": "官網未自存", "l": "https://g9cip.com/e", "img": "https://www.g9cip.com/b.png"},
            {"t": "缺連結活動", "l": "", "img": "kv/d.jpg"},
        ]},
    ]
    md = m.build_markdown(venues, today="2026-07-22")
    assert "# 資料缺口清單" in md
    # 三種缺口段落都在
    assert "## ① KV 主視覺" in md and "## ② 缺官方連結" in md and "## ③ 約略定位" in md
    assert "### A. KV 需人工補" in md and "### B. KV 官網外站圖" in md
    assert "FB破圖" in md and "官網未自存" in md and "缺連結活動" in md
    assert "☐" in md                             # A 區有勾選欄
    assert "已自存" not in md.split("## ①")[1]   # ok 的不出現在任何表格
    print("test_build_markdown: PASS")


if __name__ == "__main__":
    test_kv_status()
    test_build_report()
    test_missing_links_and_approx()
    test_build_markdown()
    print("ALL TESTS PASS")
