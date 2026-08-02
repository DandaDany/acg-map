#!/usr/bin/env python3
"""Regression checks for ACG admission/payment status metadata."""
import datetime
import json
import os
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VALID_FEES = {"免費", "付費"}
TODAY = datetime.date(2026, 8, 2)


def load(relative_path):
    with open(os.path.join(ROOT, relative_path), encoding="utf-8") as fh:
        return json.load(fh)


def parse_date(value):
    try:
        return datetime.datetime.strptime(value, "%Y/%m/%d").date()
    except (TypeError, ValueError):
        return None


class AdmissionStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = load("data/manual/acg_events.json")
        cls.overrides = load("data/manual/event_admission_overrides.json")
        cls.public = load("public/venues.json")

    def test_source_json_has_admission_column_on_every_row(self):
        self.assertTrue(self.source)
        for row in self.source:
            self.assertIn("付費狀態 / Admission", row)
            self.assertIn(row["付費狀態 / Admission"], VALID_FEES | {None})

    def test_override_records_are_auditable(self):
        records = {k: v for k, v in self.overrides.items() if not k.startswith("_")}
        self.assertGreaterEqual(len(records), 83)
        for title, record in records.items():
            with self.subTest(title=title):
                self.assertIn(record.get("fee"), VALID_FEES)
                self.assertTrue(str(record.get("source") or "").startswith("https://"))
                checked = datetime.date.fromisoformat(record.get("checked"))
                self.assertLessEqual(checked, TODAY)
                self.assertTrue(record.get("basis"))

    def test_every_current_acg_map_event_has_a_fee_badge_value(self):
        current = []
        for venue in self.public["venues"]:
            for event in venue.get("ex", []):
                end = parse_date(event.get("e"))
                if event.get("c") == "ACG" and (end is None or end >= TODAY):
                    current.append(event)
        self.assertTrue(current)
        for event in current:
            self.assertIn(event.get("fee"), VALID_FEES, event.get("t"))

    def test_known_free_and_paid_examples(self):
        events = {
            event["t"]: event
            for venue in self.public["venues"]
            for event in venue.get("ex", [])
        }
        expected = {
            "漫畫便當店 COMIC BENTO": "免費",
            "藥師少女的獨語展": "付費",
            "PokéXciting! in 台北（寶可夢30週年慶典）": "免費",
            "2026 新世紀福音戰士路跑（2KM）": "付費",
        }
        for title, fee in expected.items():
            with self.subTest(title=title):
                self.assertEqual(events[title].get("fee"), fee)


if __name__ == "__main__":
    unittest.main()
