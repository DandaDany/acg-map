#!/usr/bin/env python3
import json
import os
import unittest

from event_lifecycle_test_helpers import assert_public_matches_lifecycle


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITO_TITLE = "伊藤潤二狂熱城市夜行路跑"
ITO_LINK = "https://www.bryte-fun.com/activity/1c3889b0-d90e-41d0-88ca-198c78fd2b5e/pages/102"
ITO_KV = "https://bryte-dev-cdn.bearathome.com.tw/dc149475-85d4-3677-8e7c-f6c9cd42d160.jpg"
INITIAL_D_TITLE = "頭文字D（Initial D）快閃店（第二站）"


def load(relative_path):
    with open(os.path.join(ROOT, relative_path), encoding="utf-8") as fh:
        return json.load(fh)


class EventDataSearchFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manual = load("data/manual/manual_extra.json")
        cls.events = load("data/manual/acg_events.json")
        cls.public = load("public/venues.json")

    def test_initial_d_uses_kaohsiung_station_coordinates(self):
        venue = self.manual["高雄駅一番街・北站 高雄捷運高雄車站B2"]
        self.assertEqual(venue["loc"], "exact")
        self.assertAlmostEqual(venue["lat"], 22.6377809)
        self.assertAlmostEqual(venue["lng"], 120.3034814)
        pins = assert_public_matches_lifecycle(
            self, self.public, self.events, INITIAL_D_TITLE
        )
        if pins:
            generated, _ = pins[0]
            self.assertAlmostEqual(generated["la"], 22.6377809)
            self.assertAlmostEqual(generated["lo"], 120.3034814)

    def test_junji_ito_uses_requested_page_and_kv(self):
        rows = [
            row
            for row in self.events
            if row.get("活動名稱 / Activity Name") == ITO_TITLE
        ]
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertEqual(row["活動連結 / Activity link"], ITO_LINK)
            self.assertEqual(row["KV"], ITO_KV)
        pins = assert_public_matches_lifecycle(
            self, self.public, self.events, ITO_TITLE, active_count=1
        )
        for _, event in pins:
            self.assertEqual(event["l"], ITO_LINK)
            # 地圖上的 KV：download_event_kv.py --all 會把這張遠端圖自存到
            # public/kv/ 並改引用 'kv/<hash>.<ext>'；尚未自存時才是原始遠端網址。
            img = event["img"]
            self.assertTrue(
                img == ITO_KV or img.startswith("kv/"),
                f"junji ito KV 應為原圖或已自存的站內路徑，實際: {img}",
            )


if __name__ == "__main__":
    unittest.main()
