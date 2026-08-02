#!/usr/bin/env python3
import json
import os
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class MultiStoreEventTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ROOT, "public", "venues.json"), encoding="utf-8") as fh:
            cls.data = json.load(fh)

    def test_generated_map_has_expected_multistore_markers(self):
        found = {}
        totals = {}
        ids = {}
        for venue in self.data["venues"]:
            for event in venue.get("ex", []):
                label = event.get("mf")
                if not label:
                    continue
                found[label] = found.get(label, 0) + 1
                totals.setdefault(label, set()).add(event.get("ms"))
                ids.setdefault(label, set()).add(event.get("id"))

        self.assertEqual(found, {
            "點點心": 20,
            "凍心": 11,
            "bb.q CHICKEN": 14,
            "藏壽司": 63,
        })
        self.assertEqual(totals["點點心"], {20})
        self.assertEqual(totals["凍心"], {28})
        self.assertEqual(totals["bb.q CHICKEN"], {14})
        self.assertEqual(totals["藏壽司"], {63})
        self.assertTrue(all(len(group_ids) == 1 for group_ids in ids.values()))

    def test_frontend_filters_multistore_by_activity_group(self):
        with open(os.path.join(ROOT, "public", "taiwan-exhibition-map.html"), encoding="utf-8") as fh:
            html = fh.read()
        self.assertIn('data-filter="multi"', html)
        self.assertIn("group.multiFilter!==filters.multi", html)
        self.assertIn("new Set(locations.map(location=>location.event.id))", html)
        self.assertIn("if(key==='multi')", html)
        self.assertIn("group.locations.filter(location=>occurrenceVisible(location,filters)).length", html)
        self.assertIn("const multiStoreMode=uiState.filters.multi!=='all'", html)
        self.assertIn("entries.length+' 間門市'", html)


if __name__ == "__main__":
    unittest.main()
