#!/usr/bin/env python3
"""Regression checks for exact coordinates retained from PR #37."""
import json
import os
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXPECTED = {
    "bb.q CHICKEN 三重三和店": (25.079326, 121.481494),
    "bb.q CHICKEN 中和中漢店": (25.006584, 121.47232),
    "bb.q CHICKEN 公館店": (25.0156631, 121.5315247),
    "bb.q CHICKEN 南紡購物店": (22.990582, 120.233455),
    "bb.q CHICKEN 台中崇德店": (24.1707868, 120.6851669),
    "bb.q CHICKEN 松山店": (25.0403043, 121.5780041),
    "bb.q CHICKEN 板橋板農店": (25.008633, 121.45876),
    "bb.q CHICKEN 桃園統領廣場店": (24.991113, 121.312523),
    "bb.q CHICKEN 洲子店": (25.0792389, 121.5691082),
    "bb.q CHICKEN 芝山店": (25.1024587, 121.5229631),
    "bb.q CHICKEN 鳳山青年店": (22.63988, 120.3509),
    "大安森林公園": (25.030152, 121.5353507),
    "肉的長谷川 SOGO忠孝店": (25.0417384, 121.5449554),
    "肉的長谷川 南港LaLaPort店": (25.0586227, 121.6169879),
    "肉的長谷川 台中新光三越中港店": (24.1650058, 120.6433984),
    "肉的長谷川 誠品南西店": (25.0523804, 121.5212653),
    "肉的長谷川 高雄漢神巨蛋店": (22.669549, 120.303159),
    "馬場町紀念公園": (25.0199329, 121.5035063),
}


class VerifiedGeocodeTests(unittest.TestCase):
    def test_verified_coordinates_are_preserved(self):
        path = os.path.join(ROOT, "data", "manual", "venue_geocodes.json")
        with open(path, encoding="utf-8") as fh:
            geocodes = json.load(fh)

        for name, (lat, lng) in EXPECTED.items():
            with self.subTest(name=name):
                self.assertIn(name, geocodes)
                self.assertAlmostEqual(geocodes[name]["la"], lat, places=6)
                self.assertAlmostEqual(geocodes[name]["lo"], lng, places=6)
                self.assertEqual(geocodes[name]["source"], "address_geocode")


if __name__ == "__main__":
    unittest.main()
