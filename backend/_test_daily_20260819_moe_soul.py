#!/usr/bin/env python3
import json
import os
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TITLE = "2026 台中萌魂動漫祭．餘暑篇"
OFFICIAL = "https://www.instagram.com/p/DcNp0ahkksP/"


def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        return json.load(fh)


class Daily20260819MoeSoulTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public = load("public/venues.json")
        cls.manual = load("data/manual/acg_events.json")
        cls.metadata = load("data/manual/event_metadata_overrides.json")
        cls.admission = load("data/manual/event_admission_overrides.json")
        cls.rows = [
            (venue, event)
            for venue in cls.public["venues"]
            for event in venue.get("ex", [])
            if event.get("t") == TITLE
        ]

    def test_event_is_complete_and_has_one_map_pin(self):
        self.assertEqual(len(self.rows), 1)
        venue, event = self.rows[0]
        self.assertEqual(venue["name"], "台中驛鐵道文化園區 鐵鹿大街 A2")
        self.assertEqual(venue["addr"], "台中市中區台灣大道一段1號")
        self.assertAlmostEqual(venue["la"], 24.1373875, places=7)
        self.assertAlmostEqual(venue["lo"], 120.6874749, places=7)
        self.assertEqual(venue["loc"], "building")
        self.assertEqual((event["s"], event["e"]), ("2026/08/27", "2026/09/20"))
        self.assertEqual(event["c"], "ACG")
        self.assertEqual(event["c2"], "快閃店")
        self.assertEqual(event["fee"], "免費")
        self.assertEqual(event["org"], "辰星計畫／重星戰略有限公司")
        self.assertTrue(event["lic"])
        self.assertEqual(event["l"], OFFICIAL)
        self.assertEqual(event["id"], "manual-taichung-moe-soul-20260827")

    def test_manual_decisions_and_provenance_are_persistent(self):
        rows = [r for r in self.manual if r.get("活動名稱 / Activity Name") == TITLE]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["付費狀態 / Admission"], "免費")
        self.assertEqual(rows[0]["活動類別 / Activity Category"], "快閃店/Pop Up Store")
        self.assertEqual(rows[0]["活動連結 / Activity link"], OFFICIAL)

        meta = self.metadata[TITLE]
        self.assertEqual(meta["source_tier"], 1)
        self.assertEqual(meta["source"], OFFICIAL)
        self.assertEqual(meta["kv_source"], OFFICIAL)
        self.assertEqual(self.admission[TITLE]["fee"], "免費")

    def test_official_kv_is_self_hosted_and_matches_verified_source(self):
        _, event = self.rows[0]
        source = os.path.join(
            ROOT, "data", "manual", "_kv_cache", "taichung_moe_soul_20260827.png"
        )
        public = os.path.join(ROOT, "public", event["img"])
        self.assertTrue(os.path.isfile(source))
        self.assertTrue(os.path.isfile(public))
        with open(source, "rb") as fh:
            source_bytes = fh.read()
        with open(public, "rb") as fh:
            public_bytes = fh.read()
        self.assertEqual(source_bytes, public_bytes)
        self.assertGreater(len(source_bytes), 100_000)


if __name__ == "__main__":
    unittest.main()
