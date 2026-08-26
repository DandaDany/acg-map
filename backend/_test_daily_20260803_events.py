#!/usr/bin/env python3
"""Regression checks for official events accepted in the 2026-08-03 scan."""
import json
import os
import unittest

from event_lifecycle_test_helpers import (
    assert_persistent_venue_decisions,
    assert_public_matches_lifecycle,
)


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(relative_path):
    with open(os.path.join(ROOT, relative_path), encoding="utf-8") as fh:
        return json.load(fh)


class Daily20260803EventTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public = load("public/venues.json")
        cls.events = load("data/manual/acg_events.json")
        cls.address_overrides = load("data/manual/venue_address_overrides.json")
        cls.venue_geocodes = load("data/manual/venue_geocodes.json")
        cls.metadata = load("data/manual/event_metadata_overrides.json")
        cls.admission = load("data/manual/event_admission_overrides.json")

    def assert_persistent_records(self, title, expected_count):
        return assert_persistent_venue_decisions(
            self,
            self.events,
            title,
            self.address_overrides,
            self.venue_geocodes,
            expected_count,
            expected_loc="exact",
        )

    def test_maniani_popup_has_two_exact_official_pins(self):
        title = "Maniani World 限定快閃店"
        rows = self.assert_persistent_records(title, 2)
        pins = assert_public_matches_lifecycle(self, self.public, self.events, title)
        if pins:
            self.assertEqual({venue["loc"] for venue, _ in pins}, {"exact"})
            self.assertEqual({event["c2"] for _, event in pins}, {"快閃店"})
            self.assertEqual({event["fee"] for _, event in pins}, {"免費"})
            self.assertEqual({event["org"] for _, event in pins}, {"unicreative 有點共創"})
            self.assertEqual(
                {event["lic"] for _, event in pins},
                {"Maniani／Frontier Works Inc."},
            )
            self.assertEqual(
                {event["l"] for _, event in pins},
                {"https://www.instagram.com/p/Dbfd7tWDB0f/"},
            )
        self.assertEqual({row["付費狀態 / Admission"] for row in rows}, {"免費"})
        self.assertEqual(self.metadata[title]["source_tier"], 1)
        self.assertEqual(self.metadata[title]["source"], self.metadata[title]["kv_source"])

    def test_identity_v_grazie_has_two_exact_theme_store_pins(self):
        title = "第五人格 × 義式屋古拉爵 8週年聯名"
        rows = self.assert_persistent_records(title, 2)
        pins = assert_public_matches_lifecycle(self, self.public, self.events, title)
        if pins:
            self.assertEqual({venue["loc"] for venue, _ in pins}, {"exact"})
            self.assertEqual({event["c2"] for _, event in pins}, {"主題餐廳"})
            self.assertEqual({event["fee"] for _, event in pins}, {"付費"})
            self.assertEqual({event["org"] for _, event in pins}, {"義式屋古拉爵"})
            self.assertEqual(
                {event["lic"] for _, event in pins},
                {"Joker Studio／NetEase Inc."},
            )
            self.assertEqual(
                {event["l"] for _, event in pins},
                {"https://www.grazie.com.tw/data-414071"},
            )
        self.assertEqual({row["付費狀態 / Admission"] for row in rows}, {"付費"})
        self.assertEqual(self.metadata[title]["source_tier"], 1)
        self.assertTrue(self.metadata[title]["kv_source"].startswith("https://www.instagram.com/"))
        self.assertEqual(self.admission[title]["fee"], "付費")

    def test_expired_identity_v_keeps_ssot_without_materialized_or_public_pins(self):
        title = "第五人格 × 義式屋古拉爵 8週年聯名"
        rows = self.assert_persistent_records(title, 2)
        expired_snapshot = {"updated": "2026/08/24", "venues": []}
        pins = assert_public_matches_lifecycle(
            self,
            expired_snapshot,
            self.events,
            title,
        )
        self.assertEqual(pins, [])
        self.assertEqual(
            {row["結束日期 / End Date"] for row in rows},
            {"2026-08-23 00:00:00"},
        )


if __name__ == "__main__":
    unittest.main()
