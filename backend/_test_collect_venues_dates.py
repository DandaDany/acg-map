#!/usr/bin/env python3
import os
import sys
import types
import unittest


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 日期解析是純文字邏輯；離線測試不應要求安裝或啟動 Playwright。
if "playwright.sync_api" not in sys.modules:
    playwright = types.ModuleType("playwright")
    sync_api = types.ModuleType("playwright.sync_api")
    sync_api.sync_playwright = None
    playwright.sync_api = sync_api
    sys.modules["playwright"] = playwright
    sys.modules["playwright.sync_api"] = sync_api

from collect_venues import (
    CARD_CONTAINER_SELECTOR,
    CARD_DESCENDANT_SELECTOR,
    VENUES,
    parse_dates,
)
from refresh_venues import (
    STRICT_OFFICIAL_DATE_VENUES,
    filter_public_acg_only,
    keep_official_event_dates,
)


class CollectVenueDateTests(unittest.TestCase):
    def test_songshan_rows_are_a_card_boundary(self):
        self.assertIn(".rows", CARD_CONTAINER_SELECTOR.split(","))

    def test_anchor_wrapped_cards_are_a_descendant_boundary(self):
        self.assertIn(":scope > li", CARD_DESCENDANT_SELECTOR.split(","))

    def test_pier2_only_scans_current_event_list(self):
        pier2 = next(v for v in VENUES if v["key"] == "高雄市駁二藝術特區")
        self.assertEqual(pier2.get("root"), "#event_list")

    def test_valid_range_is_preserved(self):
        self.assertEqual(
            parse_dates("2026-08-11～2026-09-07"),
            ("2026/08/11", "2026/09/07"),
        )

    def test_adjacent_card_date_cannot_create_reversed_range(self):
        self.assertEqual(
            parse_dates("2026-08-26 2026-08-21"),
            ("2026/08/26", "2026/08/26"),
        )

    def test_short_range_with_reversed_dates_becomes_single_day(self):
        self.assertEqual(
            parse_dates("2026/08/28 - 08/21"),
            ("2026/08/28", "2026/08/28"),
        )

    def test_month_day_range_is_not_misread_as_a_year(self):
        self.assertEqual(
            parse_dates("▸11/8-9 一展將團精神引領陣頭風姿"),
            ("", ""),
        )

    def test_roc_year_is_still_supported(self):
        self.assertEqual(
            parse_dates("115/08/19-115/09/20"),
            ("2026/08/19", "2026/09/20"),
        )

    def test_public_guard_rejects_stale_open_ended_and_bad_year(self):
        self.assertFalse(keep_official_event_dates("2025/09/05", "", "2026/08/19"))
        self.assertFalse(keep_official_event_dates("11/08/09", "11/08/09", "2026/08/19"))
        self.assertTrue(keep_official_event_dates("2026/12/19", "", "2026/08/19"))

    def test_strict_official_date_venues_include_chiayi_yuanshan_and_songshan(self):
        self.assertTrue(
            {"嘉義文化創意產業園區", "圓山花博", "松山文創園區"}
            <= STRICT_OFFICIAL_DATE_VENUES
        )

    def test_public_output_keeps_only_acg_and_drops_empty_venues(self):
        venues = [
            {"name": "混合場館", "ex": [{"t": "ACG", "c": "ACG"}, {"t": "藝術", "c": "其他文化"}]},
            {"name": "非 ACG 場館", "ex": [{"t": "科技展", "c": "其他文化"}]},
        ]
        self.assertEqual(
            filter_public_acg_only(venues),
            [{"name": "混合場館", "ex": [{"t": "ACG", "c": "ACG"}]}],
        )


if __name__ == "__main__":
    unittest.main()
