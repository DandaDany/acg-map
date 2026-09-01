#!/usr/bin/env python3
"""Lifecycle-aware regression for TAMASHII EXHIBITION 2026."""
import datetime
import json
import os
import unittest

from event_first_seen import taipei_today


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TITLE = "TAMASHII EXHIBITION 2026"
OFFICIAL = "https://pier2.org/exhibition/info/1976/"
END = datetime.date(2026, 9, 28)


def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        return json.load(fh)


class TamashiiExhibitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public = load("public/venues.json")
        cls.metadata = load("data/manual/event_metadata_overrides.json")
        cls.admission = load("data/manual/event_admission_overrides.json")
        cls.today = datetime.date.fromisoformat(taipei_today())
        cls.rows = [
            (venue, event)
            for venue in cls.public["venues"]
            for event in venue.get("ex", [])
            if event.get("t") == TITLE
        ]

    def test_verified_decisions_remain_persistent(self):
        self.assertEqual(
            self.metadata[TITLE],
            {
                "org": "活動官方未公開",
                "lic": "BANDAI SPIRITS／BANDAI NAMCO及各參展作品權利方",
                "c2": "展覽",
                "link": OFFICIAL,
                "source_tier": 1,
                "source": OFFICIAL,
                "kv_source": "https://pier2.org/upload/event/YIFZFCQZ982552.jpeg",
                "checked": "2026-09-01",
            },
        )
        self.assertEqual(self.admission[TITLE]["fee"], "免費")
        self.assertEqual(self.admission[TITLE]["source"], OFFICIAL)

    def test_public_record_matches_lifecycle_and_verified_fields(self):
        if self.today > END:
            self.assertEqual(self.rows, [])
            return
        self.assertEqual(len(self.rows), 1)
        venue, event = self.rows[0]
        self.assertEqual(venue["name"], "高雄市駁二藝術特區")
        self.assertEqual(venue["addr"], "高雄市鹽埕區大勇路1號")
        self.assertEqual((event["s"], event["e"]), ("2026/09/19", "2026/09/28"))
        self.assertEqual(event["l"], OFFICIAL)
        self.assertEqual(event["c"], "ACG")
        self.assertEqual(event["c2"], "展覽")
        self.assertEqual(event["fee"], "免費")
        self.assertEqual(event["org"], "活動官方未公開")
        self.assertEqual(
            event["lic"], "BANDAI SPIRITS／BANDAI NAMCO及各參展作品權利方"
        )
        self.assertEqual(event["img"], "kv/fb2b565da49b1c11.jpeg")
        self.assertTrue(os.path.isfile(os.path.join(ROOT, "public", event["img"])))


if __name__ == "__main__":
    unittest.main()
