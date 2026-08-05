#!/usr/bin/env python3
"""Regression checks for the 2026-08-01 verified event KV repair."""
import json
import os
import unittest
from urllib.parse import urlparse


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PREFIX = "https://raw.githubusercontent.com/DandaDany/acg-map/main/"

# These event records were verified against the organizer, venue, licensor, or
# official event account.  The values are repository-owned files so that the
# map does not regress to expiring Facebook/Instagram CDN URLs.
VERIFIED = {
    "ANI-FEST期間限定店": "anifest_dreammall_20260520.jpg",
    "《凡爾賽玫瑰》快閃空間": "rose_of_versailles_pier2_20260612.jpg",
    "《Marshville Quokscout》": "marshville_quokscout_20260619.jpg",
    "San-X 90週年紀念展in台灣": "sanx90_breeze_20260627.jpg",
    "Hello Kitty展 高雄站": "hello_kitty_kaohsiung_20260703.jpg",
    "吉伊卡哇-2026 臺灣國際熱氣球嘉年華": "chiikawa_balloon_festival_20260704.jpg",
    "九井諒子展 及 《迷宮飯》迷宮探索展 台灣站": "dungeon_meshi_taipei_20260715.jpg",
    "藥師少女的獨語展": "apothecary_diaries_exhibition_20260717.jpg",
    "孤獨搖滾！動畫展（台中場）": "bocchi_animation_exhibition_taichung_20260720.jpg",
    "2026花蓮FUN暑假": "hualien_fun_onepiece_20260711.webp",
    "「夏日動漫時光機」展": "anime_time_machine_eslite_20260710.jpg",
    "mofusand快閃店": "mofusand_r79_20260703.jpg",
    "三麗鷗甜心復古快閃店": "sanrio_retro_chungyo_20260702.jpg",
    "麵包超人夏日萌萌主題店": "anpanman_lihpao_20260716.jpg",
    "《東京喰種》期間限定快閃店": "tokyo_ghoul_incubase_20260731.jpg",
    "HUNTER×HUNTER POP UP SHOP": "hunter_incubase_taipei_20260904.jpg",
    "《相反的你和我》雪人睡衣派對 FAIR in animate 活動紀念 Gratte": "you_and_i_gratte_20260718.jpg",
    "GODZILLA STORE 台南期間限定快閃店": "godzilla_tainan_20260703.jpg",
    "Tamagotchi電子雞30週年紀念快閃店": "tamagotchi_taichung_20260727.jpg",
    "primaniacs 夢時代POPUP 2026": "primaniacs_dreammall_20260717.jpg",
    "點點心×三麗鷗「萌友來點心」": "dimdimsum_sanrio_20260713.jpg",
    "藏壽司 × 三麗鷗家族「泳池派對」": "kurasushi_sanrio_20260807.jpg",
    "Bandai Namco Asia JOURNEY TAIWAN": "bandai_namco_journey_taiwan_20260731.jpg",
    "PEANUTS夏日海灘祭": "peanuts_summer_20260618.jpg",
    "Maniani World 限定快閃店": "maniani_world_popup_20260808.jpg",
    "第五人格 × 義式屋古拉爵 8週年聯名": "identityv_grazie_20260722.jpg",
}


def load(relative_path):
    with open(os.path.join(ROOT, relative_path), encoding="utf-8") as fh:
        return json.load(fh)


class VerifiedEventKvTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = load("data/manual/acg_events.json")
        cls.kv_cache = load("data/cache/event_kv_cache.json")
        cls.public = load("public/venues.json")

    def test_verified_manual_events_use_repository_owned_images(self):
        for title, filename in VERIFIED.items():
            with self.subTest(title=title):
                rows = [
                    row for row in self.events
                    if row.get("活動名稱 / Activity Name") == title
                ]
                self.assertTrue(rows, f"missing activity row: {title}")
                expected = RAW_PREFIX + "data/manual/_kv_cache/" + filename
                for row in rows:
                    self.assertEqual(row.get("KV"), expected)
                local_path = os.path.join(ROOT, urlparse(expected).path.split("/main/", 1)[1])
                self.assertTrue(os.path.isfile(local_path), local_path)
                self.assertGreater(os.path.getsize(local_path), 512)

    def test_verified_cayenne_events_use_repository_owned_images(self):
        links = self.kv_cache["links"]
        expected = {
            "https://www.cayenne-cafe.com.tw/NewsCount.aspx?id=22": "seer_cayenne_20260612.jpg",
            "https://www.cayenne-cafe.com.tw/NewsCount.aspx?id=23": "maplestory_cayenne_20260716.jpg",
            "https://www.cayenne-cafe.com.tw/NewsCount.aspx?id=24": "egg_party_cayenne_20260807.jpg",
        }
        for source, filename in expected.items():
            with self.subTest(source=source):
                record = links[source]
                self.assertEqual(record["code"], "manual_verified")
                self.assertEqual(
                    record["img"],
                    RAW_PREFIX + "data/manual/_kv_cache/" + filename,
                )

    def test_official_dates_corrected(self):
        expected = {
            "九井諒子展 及 《迷宮飯》迷宮探索展 台灣站": (
                "2026-07-15 00:00:00", "2026-08-30 00:00:00"
            ),
            "藥師少女的獨語展": (
                "2026-07-17 00:00:00", "2026-09-13 00:00:00"
            ),
        }
        for title, (start, end) in expected.items():
            row = next(
                row for row in self.events
                if row.get("活動名稱 / Activity Name") == title
            )
            self.assertEqual(row["開始日期 / Start Date"], start)
            self.assertEqual(row["結束日期 / End Date"], end)

    def test_unverified_scene_photo_remains_excluded(self):
        row = next(
            row for row in self.events
            if row.get("活動名稱 / Activity Name") == "角落小夥伴水族館第2彈"
        )
        self.assertIsNone(row.get("KV"))

    def test_verified_events_on_map_use_repository_owned_images(self):
        # 不變式：凡是仍在地圖上的已驗證活動，KV 必須指向 repo 內永久 raw URL，
        # 不得退回會過期的 Facebook/Instagram CDN 連結。
        # 不再硬編死釘數或要求已結束活動仍在圖上——活動隨結束日自然下架時，
        # 這裡不應讓每日更新失敗。
        expected_titles = set(VERIFIED) | {
            "楓之谷 x 凱岩主題餐廳",
            "賽爾號 x 凱岩主題餐廳",
            "蛋仔派對 x 凱岩主題餐廳",
        }
        pins = [
            event
            for venue in self.public["venues"]
            for event in venue.get("ex", [])
            if event.get("t") in expected_titles
        ]
        self.assertTrue(pins, "no verified events currently on the map")
        for event in pins:
            self.assertTrue(
                str(event.get("img") or "").startswith(RAW_PREFIX),
                f"unstable map KV: {event.get('t')} -> {event.get('img')}",
            )


if __name__ == "__main__":
    unittest.main()
