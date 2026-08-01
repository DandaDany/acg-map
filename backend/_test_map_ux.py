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

    def test_mobile_sheet_and_layered_filters_exist(self):
        self.assertIn('id="mobileVenueSheet"', self.html)
        self.assertIn('id="mobileVenueBody"', self.html)
        self.assertIn('id="filterDetail"', self.html)
        self.assertIn('id="filterOptions"', self.html)
        self.assertIn("function openFilterDetail(key)", self.html)
        self.assertIn("function closeFilterDetail()", self.html)
        order = [
            self.html.index(f'data-filter="{key}"')
            for key in ("city", "time", "form", "fee", "multi")
        ]
        self.assertEqual(order, sorted(order))
        self.assertIn("@media(max-width:760px)", self.html)

    def test_faceted_counts_use_unique_activity_keys(self):
        self.assertIn("function eventKey(e)", self.html)
        self.assertIn("function uniqueActivityCount(overrides)", self.html)
        self.assertIn("const eventKeys=new Set()", self.html)
        self.assertIn("目前共有 <b>'+eventKeys.size+'</b> 場活動", self.html)
        self.assertIn("const disabled=count===0&&!selected", self.html)

    def test_clear_all_stays_visible_and_can_be_disabled(self):
        self.assertIn('id="clearFilters" type="button" disabled', self.html)
        self.assertIn("clearFiltersEl.disabled=!hasActiveFilters()", self.html)
        self.assertIn("state.city=state.time=state.form=state.fee=state.multi='all'", self.html)

    def test_mobile_and_desktop_search_are_synchronized(self):
        self.assertIn('id="mq"', self.html)
        self.assertIn("function queueSearch(value,source)", self.html)

    def test_kv_images_use_fixed_bounded_frames(self):
        self.assertIn(".evcard .evmedia{", self.html)
        self.assertIn("aspect-ratio:16/9", self.html)
        self.assertIn("aspect-ratio:340/440", self.html)
        self.assertIn("overflow:hidden", self.html)
        self.assertIn("object-fit:cover", self.html)
        self.assertIn(".evcard.kv-contain .evimg{object-fit:contain}", self.html)
        self.assertIn('class="evback"', self.html)
        self.assertIn("object-position:center", self.html)
        self.assertIn('<div class="evmedia"><img class="evback"', self.html)
        self.assertIn("function applyKvLayouts(root,pop)", self.html)
        self.assertIn("img.naturalHeight>img.naturalWidth", self.html)
        self.assertNotIn("pop.options.minWidth=width", self.html)
        self.assertNotIn("pop.options.maxWidth=width", self.html)
        self.assertNotIn("pop.update();", self.html)

    def test_fee_badges_exist_in_list_and_popup_cards(self):
        self.assertIn(".tag.fee-free{", self.html)
        self.assertIn(".tag.fee-paid{", self.html)
        self.assertIn("e.fee==='免費'?'fee-free':'fee-paid'", self.html)

    def test_map_search_has_suggestions(self):
        self.assertIn('class="mapsearch"', self.html)
        self.assertIn('id="searchSuggestions"', self.html)
        self.assertIn('id="mobileSearchSuggestions"', self.html)
        self.assertIn("function searchSuggestions(value)", self.html)
        self.assertIn("function chooseSearchSuggestion(item)", self.html)


if __name__ == "__main__":
    unittest.main()
