#!/usr/bin/env python3
import json
import os
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = {"user_verified_2026-08-09", "user_verified_building_2026-08-09"}


class VenueCorrections20260809Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ROOT, "data", "manual", "venue_geocodes.json"), encoding="utf-8") as fh:
            geocodes = json.load(fh)
        cls.expected = {name: value for name, value in geocodes.items() if value.get("source") in SOURCES}
        with open(os.path.join(ROOT, "public", "venues.json"), encoding="utf-8") as fh:
            cls.public = {venue["name"]: venue for venue in json.load(fh)["venues"]}

    def test_all_65_verified_venues_are_published(self):
        self.assertEqual(len(self.expected), 65)
        self.assertEqual(set(self.expected) - set(self.public), set())

    def test_coordinates_addresses_and_precision_match_verified_data(self):
        precision_counts = {"exact": 0, "building": 0}
        for name, expected in self.expected.items():
            with self.subTest(name=name):
                venue = self.public[name]
                self.assertAlmostEqual(venue["la"], expected["la"], places=7)
                self.assertAlmostEqual(venue["lo"], expected["lo"], places=7)
                self.assertEqual(venue.get("addr"), expected["addr_key"])
                self.assertEqual(venue.get("loc"), expected["loc"])
                precision_counts[expected["loc"]] += 1
        self.assertEqual(precision_counts, {"exact": 54, "building": 11})

    def test_named_venues_replace_old_address_as_name_entries(self):
        for name in (
            "爆彈燒本舖 南港 LaLaport",
            "爆彈燒本舖 新莊宏匯",
            "爆彈燒本舖 新竹巨城",
            "animate Gratte 西門站",
        ):
            self.assertIn(name, self.public)


if __name__ == "__main__":
    unittest.main()
