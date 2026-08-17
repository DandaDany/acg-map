#!/usr/bin/env python3
"""Hard quality gates for public ACG metadata and source provenance."""
import json
import os
import subprocess
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

    def test_every_public_acg_kv_is_a_committed_local_file(self):
        """公開 ACG KV 不可依賴外站，也不可引用未提交的站內檔案。

        Facebook／Instagram CDN 及部分官方站台會讓圖片網址過期、禁止外連，
        即使資料列仍有 ``img``，網站也會顯示破圖。Daily Update 已負責把遠端
        KV 自存至 ``public/kv``；這個門檻確保下載失敗或漏交檔案時 CI 直接阻擋。
        """
        public_dir = os.path.join(ROOT, "public")
        for event in self.events:
            with self.subTest(title=event.get("t")):
                image = str(event.get("img") or "").strip()
                self.assertTrue(image, "缺少 KV img")
                normalized = image.lstrip("/")
                self.assertTrue(
                    normalized.startswith("kv/"),
                    f"KV 必須自存至 public/kv，不可直接引用外站: {image}",
                )
                resolved = os.path.realpath(os.path.join(public_dir, normalized))
                self.assertTrue(
                    resolved.startswith(os.path.realpath(public_dir) + os.sep),
                    f"KV 路徑越出 public: {image}",
                )
                exists = os.path.isfile(resolved)
                if not exists:
                    # Cowork 使用 sparse checkout 時，public/kv blob 可能只存在於
                    # Git tree、未展開至工作樹；CI 的一般 checkout 則會走上面的
                    # filesystem 檢查。兩者都必須確認同一個 repository 路徑存在。
                    tracked = subprocess.run(
                        ["git", "cat-file", "-e", f"HEAD:public/{normalized}"],
                        cwd=ROOT,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )
                    exists = tracked.returncode == 0
                self.assertTrue(exists, f"KV 引用的檔案未提交: {image}")

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

    def test_every_current_public_event_has_metadata(self):
        # 完整性檢查：目前地圖上的每個 ACG 活動都要有主辦／授權／來源覆寫。
        # 不再做雙向 set 相等——覆寫檔可保留已結束活動的稽核紀錄，
        # 活動每日隨結束日自然下架時，這裡不應誤判為「孤兒」而讓每日更新失敗。
        public_titles = {event.get("t") for event in self.events}
        metadata_titles = {title for title in self.metadata if not title.startswith("_")}
        missing = public_titles - metadata_titles
        self.assertFalse(missing, f"目前地圖活動缺少 metadata 覆寫: {sorted(missing)}")


if __name__ == "__main__":
    unittest.main()
