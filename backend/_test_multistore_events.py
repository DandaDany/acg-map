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
        # 不再硬編碼「哪些連鎖、各幾間」的快照——多店活動會隨檔期自然增減，
        # 快照式斷言只要有新的合法多店活動加入就會誤判失敗、拖垮每日更新。
        # 改為驗證多店標記的「結構不變量」，這才是真正該守住的正確性：
        #   1) 同一 mf 連鎖標籤的所有 occurrence 必屬同一個活動群組 id；
        #   2) 同一標籤的門市總數 ms 前後一致（單一值）；
        #   3) 上圖的門市 occurrence 數落在 [1, ms] 之間（不多於宣稱總數）；
        #   4) 地圖上至少存在一組多店活動（feature 未被整條移除）。
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

    def test_dedicated_multistore_map_control_is_wired(self):
        with open(os.path.join(ROOT, "public", "taiwan-exhibition-map.html"), encoding="utf-8") as fh:
            html = fh.read()

        self.assertIn('id="multiStoreControl"', html)
        self.assertIn('<span class="multi-store-label">多店活動</span>', html)
        self.assertIn("function isMultiStoreMapGroup(group)", html)
        self.assertIn("function toggleMultiStoreEvent(id)", html)
        self.assertIn("function collapseMultiStoreEvent()", html)
        self.assertIn("group.id===activeMultiStoreEventId", html)
        self.assertIn("renderMultiStoreControl();updateFilterUI();", html)
        self.assertIn(
            "const nextMultiStoreEventId=isMultiStoreMapGroup(selectedGroup)?selectedGroup.id:null;",
            html,
        )


if __name__ == "__main__":
    unittest.main()
