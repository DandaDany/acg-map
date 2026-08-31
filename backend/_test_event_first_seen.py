#!/usr/bin/env python3
import json
import os
import sys
import tempfile
import unittest
import datetime as dt
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from event_first_seen import apply_first_seen, taipei_today  # noqa: E402


class EventFirstSeenTests(unittest.TestCase):
    def event(self, event_id="auto-stable"):
        return {"id": event_id, "c": "ACG", "t": "測試活動"}

    def test_existing_event_retains_original_first_seen(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "event_first_seen.json"
            registry.write_text('{"auto-stable":"2026-08-01"}\n', encoding="utf-8")
            venues = [{"ex": [self.event()]}]
            apply_first_seen(venues, registry, today="2026-08-09")
            self.assertEqual(venues[0]["ex"][0]["first_seen"], "2026-08-01")
            self.assertEqual(json.loads(registry.read_text())["auto-stable"], "2026-08-01")

    def test_taipei_today_crosses_utc_date_boundary(self):
        utc = dt.datetime(2026, 8, 30, 16, 30, tzinfo=dt.timezone.utc)
        self.assertEqual(taipei_today(utc), "2026-08-31")

    def test_new_event_receives_today_first_seen(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "event_first_seen.json"
            venues = [{"ex": [self.event("auto-new")]}]
            apply_first_seen(venues, registry, today="2026-08-09")
            self.assertEqual(json.loads(registry.read_text())["auto-new"], "2026-08-09")

    def test_daily_rebuild_does_not_refresh_old_first_seen(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "event_first_seen.json"
            venues = [{"ex": [self.event()]}]
            apply_first_seen(venues, registry, today="2026-08-01")
            apply_first_seen(venues, registry, today="2026-08-09")
            self.assertEqual(json.loads(registry.read_text())["auto-stable"], "2026-08-01")

    def test_registry_uses_stable_event_ids(self):
        registry = json.loads((ROOT / "data" / "event_first_seen.json").read_text(encoding="utf-8"))
        self.assertTrue(registry)
        self.assertTrue(all(key.startswith("auto-") or key.startswith("manual-") for key in registry))

    def test_public_first_seen_matches_registry(self):
        registry = json.loads((ROOT / "data" / "event_first_seen.json").read_text(encoding="utf-8"))
        public = json.loads((ROOT / "public" / "venues.json").read_text(encoding="utf-8"))
        events = [event for venue in public["venues"] for event in venue.get("ex", []) if event.get("c") == "ACG"]
        self.assertTrue(events)
        self.assertTrue(all(event.get("id") in registry for event in events))
        self.assertTrue(all(event.get("first_seen") == registry[event["id"]] for event in events))


if __name__ == "__main__":
    unittest.main()
