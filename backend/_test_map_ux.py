#!/usr/bin/env python3
import os
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP_HTML = os.path.join(ROOT, "public", "taiwan-exhibition-map.html")


class MapUxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(MAP_HTML, encoding="utf-8") as fh:
            cls.html = fh.read()

    def test_home_controls_exist(self):
        self.assertIn('id="homeButton"', self.html)
        self.assertIn('id="mobileHomeButton"', self.html)
        self.assertIn("function resetMapView()", self.html)

    def test_marker_click_uses_toggle_state(self):
        self.assertIn("function toggleVenueFocus(v,m,latlng)", self.html)
        self.assertIn("if(activeVenue===v){ closeVenueFocus(true); return; }", self.html)
        self.assertIn("closePopupOnClick:false", self.html)

    def test_mobile_sheet_and_filter_tabs_exist(self):
        self.assertIn('id="mobileVenueSheet"', self.html)
        self.assertIn('id="mobileVenueBody"', self.html)
        self.assertIn('id="mobileTabs"', self.html)
        for panel in ("ftimeSec", "fformSec", "fmultiSec", "fregionSec"):
            self.assertIn(f'data-panel="{panel}"', self.html)
        self.assertIn("@media(max-width:760px)", self.html)

    def test_mobile_and_desktop_search_are_synchronized(self):
        self.assertIn('id="mq"', self.html)
        self.assertIn("function queueSearch(value,source)", self.html)

    def test_kv_images_use_adaptive_bounded_frames(self):
        self.assertIn(".evcard .evmedia{", self.html)
        self.assertIn("aspect-ratio:16/9", self.html)
        self.assertIn("aspect-ratio:9/16", self.html)
        self.assertIn("aspect-ratio:340/440", self.html)
        self.assertIn("aspect-ratio:440/340", self.html)
        self.assertIn("overflow:hidden", self.html)
        self.assertIn("object-fit:cover", self.html)
        self.assertIn(".evcard.kv-contain .evimg{object-fit:contain}", self.html)
        self.assertIn('class="evback"', self.html)
        self.assertIn("object-position:center", self.html)
        self.assertIn('<div class="evmedia"><img class="evback"', self.html)
        self.assertIn("function applyKvLayouts(root,pop)", self.html)
        self.assertIn("img.naturalHeight>img.naturalWidth", self.html)

    def test_map_search_has_suggestions(self):
        self.assertIn('class="mapsearch"', self.html)
        self.assertIn('id="searchSuggestions"', self.html)
        self.assertIn('id="mobileSearchSuggestions"', self.html)
        self.assertIn("function searchSuggestions(value)", self.html)
        self.assertIn("function chooseSearchSuggestion(item)", self.html)


if __name__ == "__main__":
    unittest.main()
