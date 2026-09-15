#!/usr/bin/env python3
"""Regression coverage for verified 2026-09-10 ACG additions."""
import json
import os
import unittest

from event_lifecycle_test_helpers import (
    assert_persistent_venue_decisions,
    assert_public_matches_lifecycle,
)


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIND = "WIND BREAKER—防風少年—5th Anniversary Exhibition Taipei"
JOJO = "《JOJO的奇妙冒險 星塵遠征軍》快閃店（高雄站）"
CONAN = "名偵探柯南 大型實境解謎遊戲《逃脫！疾風的高速追逐》新竹場"


def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        return json.load(fh)


class Daily20260910EventTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public = load("public/venues.json")
        cls.manual = load("data/manual/acg_events.json")
        cls.metadata = load("data/manual/event_metadata_overrides.json")
        cls.admission = load("data/manual/event_admission_overrides.json")
        cls.addresses = load("data/manual/venue_address_overrides.json")
        cls.geocodes = load("data/manual/venue_geocodes.json")

    def assert_event(self, title, venue_name, dates, event_id, category, fee, source):
        pins = assert_public_matches_lifecycle(
            self,
            self.public,
            self.manual,
            title,
            active_count=1,
            active_venues={venue_name},
        )
        self.assertEqual(self.metadata[title]["source_tier"], 1)
        self.assertEqual(self.metadata[title]["source"], source)
        self.assertEqual(self.admission[title]["fee"], fee)
        assert_persistent_venue_decisions(
            self,
            self.manual,
            title,
            self.addresses,
            self.geocodes,
            1,
        )
        if not pins:
            return
        venue, event = pins[0]
        self.assertEqual((event["s"], event["e"]), dates)
        self.assertEqual(event["id"], event_id)
        self.assertEqual(event["c2"], category)
        self.assertEqual(event["fee"], fee)
        self.assertEqual(event["l"], source)
        self.assertTrue(event["org"])
        self.assertTrue(event["lic"])
        self.assertTrue(event["img"].startswith("kv/"))
        self.assertTrue(os.path.isfile(os.path.join(ROOT, "public", event["img"])))
        self.assertIn(venue["loc"], {"exact", "building"})

    def test_wind_breaker_exhibition(self):
        self.assert_event(
            WIND,
            "新光三越台北南西店 一館 9F 活動會館",
            ("2026/10/24", "2026/12/06"),
            "manual-wind-breaker-5th-taipei-20261024",
            "展覽",
            "付費",
            "https://www.instagram.com/p/DdDWojPgfRZ/",
        )
        self.assertEqual(
            self.metadata[WIND]["org"],
            "台灣東販股份有限公司／movic Co., Ltd.",
        )
        self.assertEqual(self.metadata[WIND]["lic"], "Satoru Nii／KODANSHA")

    def test_jojo_kaohsiung_popup(self):
        self.assert_event(
            JOJO,
            "高雄夢時代購物中心 1F",
            ("2026/09/16", "2026/11/02"),
            "manual-jojo-stardust-popup-kaohsiung-20260916",
            "快閃店",
            "免費",
            "https://www.instagram.com/p/DdDbFsPnT69/",
        )
        self.assertEqual(self.metadata[JOJO]["org"], "IP POPUP STORE（宅一番）")

    def test_conan_hsinchu_realescape(self):
        self.assert_event(
            CONAN,
            "風livehouse",
            ("2027/01/21", "2027/01/24"),
            "manual-conan-realescape-hsinchu-20270121",
            "體驗活動",
            "付費",
            "https://www.instagram.com/p/DdBiBMqCf67/",
        )
        self.assertEqual(self.metadata[CONAN]["org"], "SCRAP／頂級豬排遊戲工作室")
        self.assertEqual(
            self.metadata[CONAN]["kv_source"],
            "https://realdgame.jp/s/conan2026/taiwan/",
        )


if __name__ == "__main__":
    unittest.main()
