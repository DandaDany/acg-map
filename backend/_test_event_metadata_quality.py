#!/usr/bin/env python3
"""Hard quality gates for public ACG metadata and source provenance."""
import json
import os
import unittest
from urllib.parse import urlparse


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED_FORMS = {"展覽", "快閃店", "主題餐廳", "體驗活動"}
DISALLOWED_PRIMARY_HOSTS = {
    "gnn.gamer.com.tw",
    "forum.gamer.com.tw",
    "sounova.com",
    "tw.news.yahoo.com",
    "woman.udn.com",
}


def load(relative_path):
    with open(os.path.join(ROOT, relative_path), encoding="utf-8") as fh:
        return json.load(fh)


class EventMetadataQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public = load("public/venues.json")
        cls.metadata = load("data/manual/event_metadata_overrides.json")
        cls.events = [
            event
            for venue in cls.public["venues"]
            for event in venue.get("ex", [])
            if event.get("c") == "ACG"
        ]

    def test_public_acg_metadata_is_complete_and_has_no_review_placeholders(self):
        self.assertTrue(self.events)
        for event in self.events:
            with self.subTest(title=event.get("t")):
                self.assertIn(event.get("c2"), ALLOWED_FORMS)
                self.assertTrue(str(event.get("org") or "").strip())
                self.assertTrue(str(event.get("lic") or "").strip())
                self.assertNotEqual(str(event.get("org") or "").strip(), "官方")
                self.assertNotEqual(str(event.get("lic") or "").strip(), "官方")
                combined = " ".join(
                    str(event.get(field) or "") for field in ("org", "lic", "c2")
                )
                self.assertNotIn("需人工", combined)
                self.assertNotIn("人工處理", combined)
                self.assertNotIn("其他", str(event.get("c2") or ""))
                serialized = json.dumps(event, ensure_ascii=False)
                self.assertNotIn("需人工", serialized)
                self.assertNotIn("人工處理", serialized)

    def test_every_public_acg_link_is_https_and_not_a_known_media_fallback(self):
        for event in self.events:
            with self.subTest(title=event.get("t")):
                link = str(event.get("l") or "").strip()
                self.assertTrue(link.startswith("https://"), link)
                host = urlparse(link).netloc.lower().removeprefix("www.")
                self.assertNotIn(host, DISALLOWED_PRIMARY_HOSTS)

        for venue in self.public["venues"]:
            if not any(event.get("c") == "ACG" for event in venue.get("ex", [])):
                continue
            venue_link = str(venue.get("url") or "").strip()
            if not venue_link:
                continue
            with self.subTest(venue=venue.get("name")):
                self.assertTrue(venue_link.startswith("https://"), venue_link)
                host = urlparse(venue_link).netloc.lower().removeprefix("www.")
                self.assertNotIn(host, DISALLOWED_PRIMARY_HOSTS)

    def test_metadata_override_provenance_schema(self):
        records = {k: v for k, v in self.metadata.items() if not k.startswith("_")}
        self.assertGreaterEqual(len(records), 49)
        for title, record in records.items():
            with self.subTest(title=title):
                self.assertIn(record.get("source_tier"), (1, 2, 3))
                self.assertTrue(str(record.get("source") or "").startswith("https://"))
                self.assertTrue(str(record.get("checked") or "").startswith("2026-"))
                if record.get("link"):
                    self.assertEqual(record["link"], record["source"])
                if record.get("kv_source"):
                    self.assertTrue(record["kv_source"].startswith("https://"))
                if record.get("source_tier") == 3:
                    self.assertTrue(str(record.get("fallback_reason") or "").strip())
                for field in ("org", "lic"):
                    value = str(record.get(field) or "").strip()
                    self.assertNotIn("需人工", value)
                    self.assertNotEqual(value, "官方")
                if record.get("c2"):
                    self.assertIn(record["c2"], ALLOWED_FORMS)

    def test_every_metadata_override_matches_a_public_event(self):
        public_titles = {event.get("t") for event in self.events}
        metadata_titles = {title for title in self.metadata if not title.startswith("_")}
        self.assertSetEqual(public_titles, metadata_titles)
        for title in self.metadata:
            if title.startswith("_"):
                continue
            with self.subTest(title=title):
                self.assertIn(title, public_titles)


if __name__ == "__main__":
    unittest.main()
