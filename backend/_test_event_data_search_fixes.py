#!/usr/bin/env python3
import json
import os
import unittest


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
        venue = self.manual["高雄車站一番街 北站 B2"]
        self.assertEqual(venue["loc"], "exact")
        self.assertAlmostEqual(venue["lat"], 22.6377809)
        self.assertAlmostEqual(venue["lng"], 120.3034814)
        generated = next(
            venue
            for venue in self.public["venues"]
            if any(event.get("t") == INITIAL_D_TITLE for event in venue.get("ex", []))
        )
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
        generated = [
            event
            for venue in self.public["venues"]
            for event in venue.get("ex", [])
            if event.get("t") == ITO_TITLE
        ]
        self.assertTrue(generated)
        for event in generated:
            self.assertEqual(event["l"], ITO_LINK)
            self.assertEqual(event["img"], ITO_KV)


if __name__ == "__main__":
    unittest.main()
