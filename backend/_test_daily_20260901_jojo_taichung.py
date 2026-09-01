#!/usr/bin/env python3
"""Lifecycle-aware regression for JOJO CARAVAN Taichung."""
import datetime
import json
import os
import unittest

from event_first_seen import taipei_today


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TITLE = "JOJO CARAVAN《飆馬野郎》複製原畫展（台中站）"
OFFICIAL = "https://www.facebook.com/emuse.com.tw/posts/1530886889073975/"
END = datetime.date(2026, 9, 28)


def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        return json.load(fh)


class JojoCaravanTaichungTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public = load("public/venues.json")
        cls.metadata = load("data/manual/event_metadata_overrides.json")
        cls.admission = load("data/manual/event_admission_overrides.json")
        cls.geocodes = load("data/manual/venue_geocodes.json")
        cls.today = datetime.date.fromisoformat(taipei_today())
        cls.rows = [
            (venue, event)
            for venue in cls.public["venues"]
            for event in venue.get("ex", [])
            if event.get("t") == TITLE
        ]

    def test_verified_decisions_remain_persistent(self):
        self.assertEqual(self.metadata[TITLE]["org"], "木棉花國際股份有限公司")
        self.assertEqual(
            self.metadata[TITLE]["lic"],
            "荒木飛呂彥／LUCKY LAND COMMUNICATIONS／集英社",
        )
        self.assertEqual(self.metadata[TITLE]["c2"], "展覽")
        self.assertEqual(self.metadata[TITLE]["source_tier"], 1)
        self.assertEqual(self.metadata[TITLE]["source"], OFFICIAL)
        self.assertEqual(self.admission[TITLE]["fee"], "免費")
        self.assertEqual(self.admission[TITLE]["source"], OFFICIAL)
        self.assertEqual(
            (self.geocodes["中友百貨 C棟13F 國際大廳"]["la"],
             self.geocodes["中友百貨 C棟13F 國際大廳"]["lo"]),
            (24.1522668, 120.6847123),
        )

    def test_public_record_matches_lifecycle_and_verified_fields(self):
        if self.today > END:
            self.assertEqual(self.rows, [])
            return
        self.assertEqual(len(self.rows), 1)
        venue, event = self.rows[0]
        self.assertEqual(venue["name"], "中友百貨 C棟13F 國際大廳")
        self.assertEqual(venue["addr"], "台中市北區三民路三段161號")
        self.assertEqual((event["s"], event["e"]), ("2026/08/29", "2026/09/28"))
        self.assertEqual(event["l"], OFFICIAL)
        self.assertEqual(event["c"], "ACG")
        self.assertEqual(event["c2"], "展覽")
        self.assertEqual(event["fee"], "免費")
        self.assertEqual(event["org"], "木棉花國際股份有限公司")
        self.assertEqual(
            event["lic"], "荒木飛呂彥／LUCKY LAND COMMUNICATIONS／集英社"
        )
        self.assertTrue(event["img"].startswith("kv/"))
        self.assertTrue(os.path.isfile(os.path.join(ROOT, "public", event["img"])))


if __name__ == "__main__":
    unittest.main()
