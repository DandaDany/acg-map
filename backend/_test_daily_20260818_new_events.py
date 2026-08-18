#!/usr/bin/env python3
import json
import os
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TITLES = {
    "Ani-One 玩轉動漫遊・高雄場": "ani_one_kaohsiung_20260829.jpg",
    "《我獨自升級 SOLO LEVELING》期間限定快閃店（高雄場）": "solo_leveling_kaohsiung_20260819.jpg",
    "「我在意的對象 並不是男人」POP UP STORE in A-BASE": "guy_not_guy_abase_20260828.jpg",
    "『光逝去的夏天』聯名咖啡廳": "hikaru_summer_cafe_20260819.jpg",
}
EXPECTED_PINS = {
    "夢時代購物中心 8F 時代會館": (22.5948961, 120.3079497, "exact"),
    "高雄夢時代購物中心 1F 時代光廊": (22.5948656, 120.3057541, "building"),
    "A-BASE": (25.042666, 121.506814, "exact"),
    "花漾蒔光": (25.058842, 121.546792, "exact"),
    "初覓手作餐坊": (22.6345934, 120.3094, "exact"),
}


class Daily20260818NewEventsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ROOT, "public", "venues.json"), encoding="utf-8") as fh:
            cls.venues = json.load(fh)["venues"]
        cls.rows = [
            (venue, event)
            for venue in cls.venues
            for event in venue.get("ex", [])
            if event.get("t") in TITLES
        ]

    def test_four_event_groups_create_five_location_pins(self):
        self.assertEqual(len(self.rows), 5)
        self.assertEqual({event["t"] for _, event in self.rows}, set(TITLES))
        self.assertEqual(len({event["id"] for _, event in self.rows}), 4)
        hikari = [event for _, event in self.rows if event["t"] == "『光逝去的夏天』聯名咖啡廳"]
        self.assertEqual(len(hikari), 2)
        self.assertEqual(len({event["id"] for event in hikari}), 1)

    def test_verified_google_map_coordinates_and_precision(self):
        self.assertEqual({venue["name"] for venue, _ in self.rows}, set(EXPECTED_PINS))
        for venue, _ in self.rows:
            with self.subTest(venue=venue["name"]):
                lat, lng, precision = EXPECTED_PINS[venue["name"]]
                self.assertAlmostEqual(venue["la"], lat, places=7)
                self.assertAlmostEqual(venue["lo"], lng, places=7)
                self.assertEqual(venue["loc"], precision)

    def test_public_fields_meet_editorial_gate(self):
        for _, event in self.rows:
            with self.subTest(title=event["t"]):
                self.assertIn(event["c2"], {"快閃店", "主題餐廳"})
                self.assertIn(event["fee"], {"免費", "付費"})
                self.assertTrue(event["org"])
                self.assertTrue(event["lic"])
                self.assertTrue(event["l"].startswith("https://"))
                self.assertNotIn("需人工確認", json.dumps(event, ensure_ascii=False))
                self.assertNotEqual(event["c2"], "其他")

    def test_official_kv_is_self_hosted_and_matches_verified_source(self):
        for _, event in self.rows:
            with self.subTest(title=event["t"]):
                source = os.path.join(ROOT, "data", "manual", "_kv_cache", TITLES[event["t"]])
                public = os.path.join(ROOT, "public", event["img"].lstrip("/"))
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
