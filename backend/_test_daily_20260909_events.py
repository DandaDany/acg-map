#!/usr/bin/env python3
"""Regression coverage for the verified 2026-09-09 ACG addition."""
import json
import os
import unittest

from event_lifecycle_test_helpers import assert_public_matches_lifecycle


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TITLE = "台中超動漫研究社快閃店"
EVENT_ID = "manual-taichung-super-anime-research-popup-20260917"
VENUE = "LaLaport 台中北館1F 舞台區"
ACTIVITY_URL = "https://www.instagram.com/p/Dc-lB3cjbjj/"
KV_SOURCE = "https://www.facebook.com/emuse.com.tw/posts/1552279143601416/"


def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        return json.load(fh)


class Daily20260909EventTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public = load("public/venues.json")
        cls.manual = load("data/manual/acg_events.json")
        cls.metadata = load("data/manual/event_metadata_overrides.json")
        cls.admission = load("data/manual/event_admission_overrides.json")

    def test_taichung_super_anime_popup_is_complete_and_uses_official_sources(self):
        rows = assert_public_matches_lifecycle(
            self,
            self.public,
            self.manual,
            TITLE,
            active_count=1,
            active_venues={VENUE},
        )
        self.assertEqual(self.metadata[TITLE]["source_tier"], 1)
        self.assertEqual(self.metadata[TITLE]["source"], ACTIVITY_URL)
        self.assertEqual(self.metadata[TITLE]["kv_source"], KV_SOURCE)
        self.assertEqual(self.admission[TITLE]["fee"], "免費")
        if not rows:
            return
        venue, event = rows[0]
        self.assertEqual(venue["addr"], "台中市東區進德路600號北館1樓")
        self.assertEqual(venue["loc"], "building")
        self.assertEqual((event["s"], event["e"]), ("2026/09/17", "2026/10/20"))
        self.assertEqual(event["id"], EVENT_ID)
        self.assertEqual(event["c2"], "快閃店")
        self.assertEqual(event["fee"], "免費")
        self.assertEqual(event["org"], "木棉花國際股份有限公司")
        self.assertEqual(event["lic"], "木棉花國際股份有限公司（台灣代理）")
        self.assertEqual(event["l"], ACTIVITY_URL)
        self.assertTrue(event["img"].startswith("kv/"))
        self.assertTrue(os.path.isfile(os.path.join(ROOT, "public", event["img"])))


if __name__ == "__main__":
    unittest.main()
