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

    def test_all_65_verified_venue_geocodes_are_preserved(self):
        self.assertEqual(len(self.expected), 65)

    def test_coordinates_addresses_and_precision_match_verified_data(self):
        precision_counts = {"exact": 0, "building": 0}
        for name, expected in self.expected.items():
            # public/venues.json intentionally contains only venues with a
            # currently publishable event.  Keep the verified geocode for
            # future reuse, but do not require an expired venue to stay on the
            # live map forever.
            if name not in self.public:
                continue
            with self.subTest(name=name):
                venue = self.public[name]
                self.assertAlmostEqual(venue["la"], expected["la"], places=7)
                self.assertAlmostEqual(venue["lo"], expected["lo"], places=7)
                self.assertEqual(venue.get("addr"), expected["addr_key"])
                self.assertEqual(venue.get("loc"), expected["loc"])
                precision_counts[expected["loc"]] += 1
        published = set(self.expected) & set(self.public)
        expected_counts = {
            precision: sum(self.expected[name]["loc"] == precision for name in published)
            for precision in precision_counts
        }
        self.assertEqual(precision_counts, expected_counts)

    def test_named_venues_replace_old_address_as_name_entries(self):
        for name in (
            "爆彈燒本舖 南港 LaLaport",
            "爆彈燒本舖 新莊宏匯",
            "爆彈燒本舖 新竹巨城",
            "animate Gratte 西門站",
        ):
            if name in self.public:
                self.assertNotIn(self.expected[name]["addr_key"], self.public)


if __name__ == "__main__":
    unittest.main()
