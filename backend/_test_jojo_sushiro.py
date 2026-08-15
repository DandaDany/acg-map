#!/usr/bin/env python3
import json
import os
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TITLE = "《JOJO的奇妙冒險 星塵遠征軍》× 台灣壽司郎 聯名活動"


class JojoSushiroTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ROOT, "data", "manual", "台灣壽司郎門市地址_20260815.json"), encoding="utf-8") as fh:
            cls.stores = json.load(fh)
        with open(os.path.join(ROOT, "public", "venues.json"), encoding="utf-8") as fh:
            cls.venues = json.load(fh)["venues"]
        cls.pins = [
            (venue, event)
            for venue in cls.venues
            for event in venue.get("ex", [])
            if event.get("t") == TITLE
        ]

    def test_official_scope_excludes_togo(self):
        self.assertEqual(self.stores["官網全部店舖數"], 59)
        self.assertEqual(self.stores["JOJO活動參與門市數"], 58)
        self.assertEqual(len(self.stores["門市清單"]), 58)
        self.assertEqual([store["門市名稱"] for store in self.stores["排除門市"]], ["To Go 站前店"])

    def test_all_participating_stores_have_exact_google_pins(self):
        self.assertEqual(len(self.pins), 58)
        expected = {
            f'台灣壽司郎 {store["門市名稱"]}': (store["緯度"], store["經度"])
            for store in self.stores["門市清單"]
        }
        self.assertEqual({venue["name"] for venue, _ in self.pins}, set(expected))
        for venue, _ in self.pins:
            with self.subTest(venue=venue["name"]):
                self.assertEqual(venue["loc"], "exact")
                self.assertAlmostEqual(venue["la"], expected[venue["name"]][0], places=6)
                self.assertAlmostEqual(venue["lo"], expected[venue["name"]][1], places=6)

    def test_event_fields_and_multistore_group(self):
        ids = {event["id"] for _, event in self.pins}
        self.assertEqual(len(ids), 1)
        for _, event in self.pins:
            self.assertEqual(event["s"], "2026/08/17")
            self.assertEqual(event["e"], "2026/09/20")
            self.assertEqual(event["c2"], "主題餐廳")
            self.assertEqual(event["fee"], "付費")
            self.assertEqual(event["org"], "台灣壽司郎股份有限公司")
            self.assertIn("荒木飛呂彥", event["lic"])
            self.assertEqual(event["mf"], "台灣壽司郎")
            self.assertEqual(event["ms"], 58)
            self.assertTrue(event["l"].startswith("https://www.facebook.com/Sushiro.TW/posts/"))
            self.assertEqual(event["img"], "/kv/jojo-sushiro-20260817.jpg")

    def test_uploaded_kv_is_stable_and_identical(self):
        source = os.path.join(ROOT, "data", "manual", "_kv_cache", "jojo_sushiro_20260817.jpg")
        public = os.path.join(ROOT, "public", "kv", "jojo-sushiro-20260817.jpg")
        self.assertTrue(os.path.isfile(source))
        self.assertTrue(os.path.isfile(public))
        with open(source, "rb") as fh:
            source_bytes = fh.read()
        with open(public, "rb") as fh:
            public_bytes = fh.read()
        self.assertEqual(source_bytes, public_bytes)
        self.assertGreater(len(source_bytes), 200_000)


if __name__ == "__main__":
    unittest.main()
