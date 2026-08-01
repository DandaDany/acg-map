#!/usr/bin/env python3
import json
import os
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class MultiStoreEventTests(unittest.TestCase):
    def test_generated_map_has_expected_multistore_markers(self):
        with open(os.path.join(ROOT, "public", "venues.json"), encoding="utf-8") as fh:
            data = json.load(fh)
        found = {}
        totals = {}
        for venue in data["venues"]:
            for event in venue.get("ex", []):
                label = event.get("mf")
                if not label:
                    continue
                found[label] = found.get(label, 0) + 1
                totals.setdefault(label, set()).add(event.get("ms"))

        self.assertEqual(found, {"點點心": 20, "凍心": 11, "bb.q CHICKEN": 14})
        self.assertEqual(totals["點點心"], {20})
        self.assertEqual(totals["凍心"], {28})
        self.assertEqual(totals["bb.q CHICKEN"], {14})
        self.assertTrue(all(total > 10 for values in totals.values() for total in values))

    def test_frontend_contains_dynamic_multistore_filter(self):
        with open(
            os.path.join(ROOT, "public", "taiwan-exhibition-map.html"),
            encoding="utf-8",
        ) as fh:
            html = fh.read()
        self.assertIn('id="fmultiSec"', html)
        self.assertIn("function renderMultiStoreFilters()", html)
        self.assertIn("if(state.multi!=='all' && e.mf!==state.multi)", html)


if __name__ == "__main__":
    unittest.main()
