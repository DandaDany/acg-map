#!/usr/bin/env python3
"""Regression coverage for the verified 2026-09-08 ACG additions."""
import json
import os
import unittest

from event_lifecycle_test_helpers import assert_public_matches_lifecycle, snapshot_date


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REZERO = "Re:從零開始的異世界生活 主題Café"
CCF = "兩棲爬蟲盛典x CCF動漫盛典"


def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        return json.load(fh)


class Daily20260908EventTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public = load("public/venues.json")
        cls.manual = load("data/manual/acg_events.json")
        cls.metadata = load("data/manual/event_metadata_overrides.json")
        cls.admission = load("data/manual/event_admission_overrides.json")

    def test_rezero_cafe_is_complete_and_uses_verified_r79_address(self):
        rows = assert_public_matches_lifecycle(
            self,
            self.public,
            self.manual,
            REZERO,
            active_count=1,
            active_venues={"誠品R79 中山地下書街B1"},
        )
        source = "https://www.instagram.com/p/DcdNjlvGJ78/"
        self.assertEqual(self.metadata[REZERO]["source_tier"], 1)
        self.assertEqual(self.metadata[REZERO]["source"], source)
        self.assertEqual(self.admission[REZERO]["fee"], "付費")
        if not rows:
            return
        venue, event = rows[0]
        self.assertEqual(
            venue["addr"],
            "台北市大同區南京西路16號B1之中山地下街B1-B48號店鋪",
        )
        self.assertEqual((event["s"], event["e"]), ("2026/08/28", "2026/10/31"))
        self.assertEqual(event["c2"], "主題餐廳")
        self.assertEqual(event["fee"], "付費")
        self.assertEqual(event["org"], "IP POPUP STORE（宅一番）")
        self.assertEqual(event["l"], source)
        self.assertTrue(event["img"].startswith("kv/"))
        self.assertTrue(os.path.isfile(os.path.join(ROOT, "public", event["img"])))

    def test_ccf_exhibition_has_official_ticket_and_metadata_decisions(self):
        official = "https://www.expopark.taipei/News_Photo_Content.aspx?n=247&s=4560"
        self.assertEqual(self.metadata[CCF]["source_tier"], 1)
        self.assertEqual(self.metadata[CCF]["source"], official)
        self.assertEqual(self.metadata[CCF]["c2"], "展覽")
        self.assertEqual(self.metadata[CCF]["lic"], "活動官方未公開")
        self.assertEqual(self.admission[CCF]["fee"], "付費")

        pins = [
            (venue, event)
            for venue in self.public["venues"]
            for event in venue.get("ex", [])
            if event.get("t") == CCF
        ]
        if snapshot_date(self.public).isoformat() > "2026-10-11":
            self.assertEqual(pins, [])
            return
        self.assertEqual(len(pins), 1)
        venue, event = pins[0]
        self.assertEqual(venue["name"], "圓山花博")
        self.assertEqual((event["s"], event["e"]), ("2026/10/09", "2026/10/11"))
        self.assertEqual(event["c2"], "展覽")
        self.assertEqual(event["fee"], "付費")
        self.assertEqual(event["org"], "囍閣閣國際有限公司／CCF動漫盛典")
        self.assertEqual(event["l"], official)
        self.assertTrue(event["img"].startswith("kv/"))
        self.assertTrue(os.path.isfile(os.path.join(ROOT, "public", event["img"])))


if __name__ == "__main__":
    unittest.main()
