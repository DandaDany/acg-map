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

        self.assertTrue(found, "地圖上應至少有一組多店活動 (mf) 標記")
        for label, occurrences in found.items():
            with self.subTest(label=label):
                self.assertEqual(len(ids[label]), 1,
                                 f"{label} 的多店 occurrence 應同屬一個活動群組 id: {ids[label]}")
                self.assertEqual(len(totals[label]), 1,
                                 f"{label} 的門市總數 ms 應一致: {totals[label]}")
                total = next(iter(totals[label]))
                self.assertIsInstance(total, int, f"{label} 的門市總數 ms 應為整數")
                self.assertGreaterEqual(occurrences, 1)
                self.assertLessEqual(occurrences, total,
                                     f"{label} 上圖門市數 {occurrences} 不應超過宣稱總數 {total}")

    def test_multistore_filter_is_internal_only(self):
        with open(os.path.join(ROOT, "public", "taiwan-exhibition-map.html"), encoding="utf-8") as fh:
            html = fh.read()
        self.assertNotIn('data-filter="multi"', html)
        self.assertIn("group.multiFilter!==filters.multi", html)
        self.assertIn("if(uiState.filters.multi!=='all')uiState.filters.multi='all';", html)

    def test_dedicated_multistore_control_matches_expected_ux(self):
        with open(os.path.join(ROOT, "public", "taiwan-exhibition-map.html"), encoding="utf-8") as fh:
            html = fh.read()

        self.assertIn('id="multiStoreControl"', html)
        self.assertIn('<span class="multi-store-label">多店活動</span>', html)
        self.assertIn('id="multiStoreList"', html)
        self.assertIn('id="multiStoreCollapse"', html)
        self.assertIn("function isMappedMultiStoreGroup(group)", html)
        self.assertIn("group.floating||group.multiFilter", html)
        self.assertIn("function collapseMultiStoreMenu(updateHistory=true)", html)
        self.assertIn("multiStoreMenuOpen=true;", html)
        self.assertIn("const bottomGap=MOBILE_QUERY.matches?104:80;", html)
        self.assertIn("if(host)host.replaceChildren();", html)
        self.assertIn("badge.textContent=group.floating?'官':String(mappedCount);", html)
        self.assertIn(
            "const nextMultiStoreEventId=isMappedMultiStoreGroup(selectedGroup)?selectedGroup.id:null;",
            html,
        )

    def test_kfc_legacy_floating_event_is_absorbed_by_multistore_control(self):
        with open(os.path.join(ROOT, "public", "taiwan-exhibition-map.html"), encoding="utf-8") as fh:
            html = fh.read()
        self.assertIn("肯德基 × 新世紀福音戰士（EVANGELION）期間限定聯名", html)
        self.assertIn("if(group.floating)return floatingVisible(group);", html)
        self.assertIn("if(group.floating){openFloatingEvent(id,true);return;}", html)


if __name__ == "__main__":
    unittest.main()
