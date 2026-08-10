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

from collect_venues import parse_dates


class CollectVenueDateTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
