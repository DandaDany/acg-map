#!/usr/bin/env python3
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geocode_venues import arcgis_address_result, same_address_identity


def candidate(address, score=100):
    return {
        "address": address,
        "location": {"x": 121.46, "y": 25.01},
        "score": score,
        "attributes": {"Addr_type": "PointAddress", "Match_addr": address, "Score": score},
    }


class GeocodeAddressIdentityTests(unittest.TestCase):
    def test_accepts_same_admin_street_and_main_house_number(self):
        requested = "新北市板橋區中山路一段6號3樓"
        matched = "新北市板橋區深丘里中山路一段6號, 220"
        self.assertTrue(same_address_identity(requested, matched))

    def test_rejects_high_score_6_to_63_mismatch(self):
        requested = "新北市板橋區中山路一段6號3樓"
        wrong = candidate("新北市板橋區中山路一段63號, 220", 97.88)
        self.assertIsNone(arcgis_address_result(requested, {"candidates": [wrong]}))

    def test_rejects_high_score_8_to_81_mismatch(self):
        requested = "台中市豐原區大社街8號1樓"
        wrong = {
            "address": "台中市神岡區大社街81號, 429",
            "location": {"x": 120.70, "y": 24.25},
            "score": 99,
            "attributes": {"Addr_type": "PointAddress", "Score": 99},
        }
        self.assertIsNone(arcgis_address_result(requested, {"candidates": [wrong]}))

    def test_rejects_different_district_even_when_house_number_matches(self):
        self.assertFalse(same_address_identity(
            "新北市板橋區中正路435號",
            "新北市新莊區中正路435號",
        ))


if __name__ == "__main__":
    unittest.main()
