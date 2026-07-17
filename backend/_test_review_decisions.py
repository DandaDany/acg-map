#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""離線單元測試：review_decisions.json 的穩定鍵與輸出前過濾（不連網、不動任何資料檔）。

用法：python3 backend/_test_review_decisions.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from refresh_venues import (  # noqa: E402
    stable_event_key, filter_rejected_events, load_rejected_keys, _norm_key_text,
)


def test_stable_key_normalization():
    # 基準鍵
    base = stable_event_key("松山文創園區", "航海王特展", "2026/08/01")
    assert base == "松山文創園區|航海王特展|2026-08-01", base
    # 前後空白、全形空白、前後標點都不影響鍵；日期 / 與 - 等價
    assert stable_event_key("松山文創園區", "  航海王特展  ", "2026-08-01") == base
    assert stable_event_key("松山文創園區", "【航海王特展】", "2026/08/01") == base
    assert stable_event_key("松山文創園區", "航海王　特展", "2026/08/01") == \
        stable_event_key("松山文創園區", "航海王 特展", "2026/08/01")
    # 臺/台 正規化（norm）
    assert stable_event_key("臺北市松山文創園區", "A", "2026/08/01") == \
        stable_event_key("台北市松山文創園區", "A", "2026/08/01")
    # 內部標點保留（只去前後）
    assert _norm_key_text("航海王：黃金城") == "航海王：黃金城"
    print("test_stable_key_normalization: PASS")


def test_filter_rejected_events():
    venues = [
        {"name": "松山文創園區", "city": "台北市", "la": 25.04, "lo": 121.56,
         "loc": "exact", "src": "manual", "url": "", "ex": [
             {"t": "航海王特展", "s": "2026/08/01", "e": "2026/10/01", "l": "", "img": ""},
             {"t": "咒術迴戰展", "s": "2026/09/01", "e": "2026/11/01", "l": "", "img": ""},
         ]},
        {"name": "駁二藝術特區", "city": "高雄市", "la": 22.62, "lo": 120.28,
         "loc": "exact", "src": "manual", "url": "", "ex": [
             {"t": "鬼滅之刃展", "s": "2026/07/20", "e": "2026/09/20", "l": "", "img": ""},
         ]},
    ]
    # rejected：拒掉「航海王特展」與駁二唯一的一場（後者場館應整個消失）
    rejected = {
        stable_event_key("松山文創園區", "【航海王特展】 ", "2026-08-01"),  # 帶標點/空白也要命中
        stable_event_key("駁二藝術特區", "鬼滅之刃展", "2026/07/20"),
    }
    out = filter_rejected_events([dict(v, ex=list(v["ex"])) for v in venues], rejected)
    assert len(out) == 1 and out[0]["name"] == "松山文創園區", out
    assert [e["t"] for e in out[0]["ex"]] == ["咒術迴戰展"], out[0]["ex"]
    # 未被拒的欄位結構原封不動
    assert set(out[0].keys()) == set(venues[0].keys())
    assert out[0]["ex"][0] == venues[0]["ex"][1]
    # 空名單 = 完全不動
    out2 = filter_rejected_events([dict(v, ex=list(v["ex"])) for v in venues], set())
    assert out2 == venues, "空 rejected 名單不得改變輸出"
    print("test_filter_rejected_events: PASS")


def test_load_rejected_keys_real_file():
    # 正式檔目前 rejected 為空 → 空集合（不影響輸出）
    keys = load_rejected_keys()
    assert keys == set(), keys
    print("test_load_rejected_keys_real_file: PASS (目前 rejected 為空)")


def test_load_rejected_keys_schema(tmp_path=None):
    # 用暫存檔驗證 loader 解析 schema
    import tempfile
    import refresh_venues
    sample = {"rejected": [
        {"key": "松山文創園區|航海王特展|2026-08-01", "title": "航海王特展",
         "venue": "松山文創園區", "reason": "重複活動", "date": "2026-07-17"},
        {"note": "沒有 key 的項目應被忽略"},
    ], "approved": []}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(sample, f, ensure_ascii=False)
        tmp = f.name
    orig_P = refresh_venues.P
    try:
        refresh_venues.P = lambda name, *a: tmp if name == "review_decisions.json" else orig_P(name, *a)
        keys = refresh_venues.load_rejected_keys()
    finally:
        refresh_venues.P = orig_P
        os.unlink(tmp)
    assert keys == {"松山文創園區|航海王特展|2026-08-01"}, keys
    print("test_load_rejected_keys_schema: PASS")


if __name__ == "__main__":
    test_stable_key_normalization()
    test_filter_rejected_events()
    test_load_rejected_keys_real_file()
    test_load_rejected_keys_schema()
    print("ALL TESTS PASS")
