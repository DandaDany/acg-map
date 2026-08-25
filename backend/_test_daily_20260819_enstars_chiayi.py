#!/usr/bin/env python3
import json
import os
import re
import unittest

from event_lifecycle_test_helpers import assert_public_matches_lifecycle, snapshot_date


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TITLE = "偶像夢幻祭 2 聚光舞台主題快閃店 台北場"
OFFICIAL = "https://www.songshanculturalpark.org/exhibition/activity/44ec2ffc-72ff-4f98-8593-02937252a54b"
DATE_RE = re.compile(r"^20\d{2}/(?:0[1-9]|1[0-2])/(?:0[1-9]|[12]\d|3[01])$")


def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        return json.load(fh)


class Daily20260819EnstarsChiayiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public = load("public/venues.json")
        cls.manual = load("data/manual/acg_events.json")
        cls.metadata = load("data/manual/event_metadata_overrides.json")
        cls.admission = load("data/manual/event_admission_overrides.json")
        cls.generated = load("data/generated/venue_extra.json")

    def test_enstars_is_a_complete_public_acg_event(self):
        rows = assert_public_matches_lifecycle(
            self,
            self.public,
            self.manual,
            TITLE,
            active_count=1,
            active_venues={"松山文創園區"},
        )
        if not rows:
            return
        venue, event = rows[0]
        self.assertEqual(venue["name"], "松山文創園區")
        self.assertEqual((event["s"], event["e"]), ("2026/08/28", "2026/09/13"))
        self.assertEqual(event["c"], "ACG")
        self.assertEqual(event["c2"], "快閃店")
        self.assertEqual(event["fee"], "免費")
        self.assertEqual(event["org"], "活動官方未公開")
        self.assertEqual(event["lic"], "Happy Elements K.K.")
        self.assertEqual(event["l"], OFFICIAL)
        self.assertEqual(event["id"], "auto-87bfe0fcaa86319e")
        self.assertTrue(event["img"].startswith("kv/"))
        self.assertTrue(os.path.isfile(os.path.join(ROOT, "public", event["img"])))

    def test_enstars_manual_decision_and_provenance_are_persistent(self):
        rows = [r for r in self.manual if r.get("活動名稱 / Activity Name") == TITLE]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["活動連結 / Activity link"], OFFICIAL)
        self.assertEqual(rows[0]["付費狀態 / Admission"], "免費")
        self.assertEqual(rows[0]["主辦方 / Organizer"], "活動官方未公開")
        self.assertEqual(rows[0]["授權單位 / Authorized unit (Licensor)"], "Happy Elements K.K.")

        meta = self.metadata[TITLE]
        self.assertEqual(meta["source_tier"], 1)
        self.assertEqual(meta["source"], OFFICIAL)
        self.assertEqual(meta["kv_source"], OFFICIAL)
        self.assertEqual(self.admission[TITLE]["fee"], "免費")

        manual_kv = os.path.join(ROOT, "data", "manual", "_kv_cache", "enstars_spotlight_taipei_20260828.jpg")
        public_kv = os.path.join(ROOT, "public", "kv", "a99974cee949f199.jpg")
        with open(manual_kv, "rb") as fh:
            manual_bytes = fh.read()
        with open(public_kv, "rb") as fh:
            public_bytes = fh.read()
        self.assertEqual(manual_bytes, public_bytes)
        self.assertGreater(len(manual_bytes), 100_000)

    def test_chiayi_generated_data_has_no_invalid_or_stale_open_end_date(self):
        today = snapshot_date(self.public).strftime("%Y/%m/%d")
        events = self.generated["嘉義文化創意產業園區"]["ex"]
        self.assertTrue(events)
        for event in events:
            with self.subTest(title=event.get("t")):
                start = str(event.get("s") or "")
                end = str(event.get("e") or "")
                self.assertTrue(start or end)
                if start:
                    self.assertRegex(start, DATE_RE)
                if end:
                    self.assertRegex(end, DATE_RE)
                    self.assertGreaterEqual(end, today)
                elif start:
                    self.assertGreaterEqual(start, today)

    def test_generated_keeps_auditable_non_acg_but_public_is_acg_only(self):
        generated_titles = {
            event.get("t")
            for event in self.generated["嘉義文化創意產業園區"]["ex"]
        }
        self.assertIn("▸OpenLab 沉浸式投影展 ➫ 科技與藝術的交會點", generated_titles)

        public_events = [
            event
            for venue in self.public["venues"]
            for event in venue.get("ex", [])
        ]
        self.assertTrue(public_events)
        self.assertTrue(all(event.get("c") == "ACG" for event in public_events))
        self.assertNotIn(
            "嘉義文化創意產業園區",
            {venue.get("name") for venue in self.public["venues"]},
        )


if __name__ == "__main__":
    unittest.main()
