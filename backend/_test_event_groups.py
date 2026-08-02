#!/usr/bin/env python3
import os
import sys
import unittest


BACKEND = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND)

from refresh_venues import assign_event_group_ids, canonical_activity_url, event_group_id


class EventGroupTests(unittest.TestCase):
    def test_canonical_url_drops_tracking_and_fragment(self):
        self.assertEqual(
            canonical_activity_url("https://example.com/event/?utm_source=x&id=3#top"),
            "https://example.com/event?id=3",
        )

    def test_explicit_id_wins(self):
        self.assertEqual(event_group_id({"id": "tour-2026", "t": "活動"}), "tour-2026")

    def test_same_activity_different_dates_groups_together(self):
        first = {"t": "巡迴展", "s": "2026/07/01", "l": "https://example.com/tour", "c": "ACG", "fee": "免費"}
        second = {"t": "巡迴展", "s": "2026/08/01", "l": "https://example.com/tour?utm_source=ig", "c": "ACG", "fee": "免費"}
        venues = [{"name": "A", "ex": [first]}, {"name": "B", "ex": [second]}]
        groups = assign_event_group_ids(venues)
        self.assertEqual(len(groups), 1)
        self.assertEqual(first["id"], second["id"])

    def test_fee_conflict_fails(self):
        venues = [
            {"name": "A", "ex": [{"id": "same", "t": "活動", "c": "ACG", "fee": "免費"}]},
            {"name": "B", "ex": [{"id": "same", "t": "活動", "c": "ACG", "fee": "付費"}]},
        ]
        with self.assertRaises(RuntimeError):
            assign_event_group_ids(venues)

    def test_metadata_fills_missing_occurrences(self):
        venues = [
            {"name": "A", "ex": [{"id": "same", "t": "活動", "c": "ACG", "ip": "作品", "org": "主辦"}]},
            {"name": "B", "ex": [{"id": "same", "t": "活動", "c": "ACG"}]},
        ]
        assign_event_group_ids(venues)
        self.assertEqual(venues[1]["ex"][0]["ip"], "作品")
        self.assertEqual(venues[1]["ex"][0]["org"], "主辦")


if __name__ == "__main__":
    unittest.main()
