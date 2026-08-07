#!/usr/bin/env python3
import json
import os
import re
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP_HTML = os.path.join(ROOT, "public", "taiwan-exhibition-map.html")
VENUES_JSON = os.path.join(ROOT, "public", "venues.json")


class MapUxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(MAP_HTML, encoding="utf-8") as fh:
            cls.html = fh.read()
        with open(VENUES_JSON, encoding="utf-8") as fh:
            cls.data = json.load(fh)

    def test_desktop_three_column_shell_exists(self):
        self.assertIn('class="desktop-shell"', self.html)
        self.assertIn('class="filter-pane"', self.html)
        self.assertIn('class="discover-pane"', self.html)
        self.assertIn('class="map-pane"', self.html)
        self.assertIn("grid-template-columns:var(--sidebar) var(--discover) minmax(0,1fr)", self.html)

    def test_mobile_has_only_discover_and_map_tabs(self):
        ui_html = re.sub(r"^let DATA = .+;$", "", self.html, flags=re.MULTILINE)
        self.assertIn('id="discoverTab"', self.html)
        self.assertIn('id="mapTab"', self.html)
        self.assertNotIn('>Save<', ui_html)
        self.assertNotIn("想去", ui_html)
        self.assertNotIn("收藏", ui_html)
        self.assertNotIn("localStorage", ui_html)
        self.assertNotIn("sessionStorage", ui_html)

    def test_shared_state_and_activity_groups_exist(self):
        self.assertIn("const uiState={", self.html)
        self.assertIn("function buildActivityGroups(data)", self.html)
        self.assertIn("function getFilteredActivityGroups(", self.html)
        self.assertIn("function getFilteredVenueOccurrences(", self.html)
        self.assertIn("function getFacetCount(", self.html)
        self.assertIn("group.status.kind!=='ended'", self.html)

    def test_marker_modes_keep_a_single_venue_marker(self):
        self.assertIn('data-marker-mode="pin"', self.html)
        self.assertIn('data-marker-mode="image"', self.html)
        self.assertIn("function markerIcon(venueIdValue,locations)", self.html)
        self.assertIn("function renderMapMarkers()", self.html)
        self.assertIn("new Set(locations.map(location=>location.event.id))", self.html)

    def test_markers_and_discover_focus_the_map(self):
        self.assertIn("function focusMapLocation(location,zoom=13", self.html)
        self.assertIn("focusMapLocation(card.location)", self.html)
        self.assertIn("data-location-id=", self.html)
        self.assertIn("setTab('map')", self.html)

    def test_image_markers_preserve_kv_orientation(self):
        self.assertIn('class="kv-marker-shell"', self.html)
        self.assertIn("function classifyKvMarker(marker)", self.html)
        self.assertIn("image.naturalWidth>=image.naturalHeight", self.html)
        self.assertIn(".kv-marker.landscape", self.html)

    def test_marker_toggle_is_centered_over_map(self):
        self.assertIn('class="segmented map-marker-toggle marker-toggle"', self.html)
        self.assertIn(".map-marker-toggle{position:absolute", self.html)
        self.assertIn("left:50%", self.html)
        self.assertNotIn('class="marker-setting"', self.html)

    def test_map_restores_original_positron_visuals(self):
        self.assertIn("baseGL=L.maplibreGL({style:'https://tiles.openfreemap.org/styles/positron'", self.html)
        self.assertIn("function boldRoads()", self.html)
        self.assertIn("W('highway_major_inner','#ffffff'", self.html)
        self.assertIn("style:{color:'#8fa0b5',weight:.7,fill:false,opacity:.5}", self.html)
        self.assertIn("const TOWN_C=", self.html)
        self.assertIn("function syncLabels()", self.html)
        self.assertIn("function canUseWebGL()", self.html)
        self.assertIn("function useRasterFallback()", self.html)
        self.assertIn("if(L.maplibreGL&&canUseWebGL())", self.html)
        self.assertIn("L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png'", self.html)

    def test_pin_mode_restores_activity_form_visuals(self):
        # ACG 只有四種活動形式，沒有「其他」分類（decision.md）。
        for color in ("#3f8ad0", "#e05aa0", "#e08a3c", "#8560d8"):
            self.assertIn(color, self.html)
        self.assertIn("const FORM_ICON={", self.html)
        self.assertIn("function venueForm(locations)", self.html)
        # 無法辨識活動形式時退回「展覽」，不得再落入已移除的「其他」分類。
        self.assertIn("return '展覽';", self.html)
        self.assertNotIn("return '其他';", self.html)
        self.assertIn("venue.loc!=='exact'", self.html)
        self.assertIn("location.status.kind==='ending'", self.html)
        self.assertIn('class="soondot"', self.html)

    def test_desktop_dialog_and_mobile_sheet_exist(self):
        self.assertIn('id="dialogOverlay"', self.html)
        self.assertIn('role="dialog" aria-modal="true"', self.html)
        self.assertIn("function openDesktopEventModal(", self.html)
        self.assertIn("function openDesktopVenuePicker(", self.html)
        self.assertIn('id="mobileVenueSheet"', self.html)
        self.assertIn("function openMobileVenueSheet(", self.html)
        self.assertIn("function closeMobileVenueSheet(", self.html)

    def test_mobile_popup_is_horizontal_swipeable_card(self):
        # 桌機活動詳情對話框：固定高度、內部捲動。
        self.assertIn("height:min(760px,calc(100dvh - 72px))", self.html)
        self.assertIn("overflow-y:auto", self.html)
        # 手機活動 popup 為橫式卡片（左 KV、右資訊）、高度約螢幕 1/3（decision.md）。
        self.assertIn("height:clamp(210px,34dvh,360px)", self.html)
        self.assertIn("mobile-card-kv", self.html)
        self.assertIn("function buildMobileCards(origin)", self.html)
        # 可左右滑切換，順序以目前地點為原點、依距離由近到遠；
        # 不再另列「其他活動地點」清單。
        self.assertIn("function moveMobileCard(delta)", self.html)
        self.assertIn("occurrenceDistance(origin", self.html)
        self.assertNotIn("其他活動地點（", self.html)

    def test_navigation_copy_link_and_private_review_text(self):
        self.assertNotIn("https://www.threads.net/intent/post?text=", self.html)
        self.assertNotIn('class="threads-share"', self.html)
        self.assertIn("navigator.clipboard", self.html)
        self.assertIn("showToast('成功複製連結')", self.html)
        self.assertNotIn("navigator.share", self.html)
        self.assertIn("text.includes('需人工確認')?'':text", self.html)
        self.assertIn(".location-nav{", self.html)

    def test_pin_legend_and_image_badge_rules(self):
        self.assertIn('id="pinLegend"', self.html)
        # 圖例只列出四種活動形式，不含已移除的「其他」分類（decision.md）。
        for label in ("展覽", "快閃店", "主題餐廳", "體驗活動"):
            self.assertIn(label, self.html)
        self.assertNotIn("其他／混合", self.html)
        self.assertIn("document.getElementById('pinLegend').hidden=uiState.markerMode!=='pin'", self.html)
        # 徽章貼齊圖片右上角邊界外緣（手機 App 通知徽章樣式，decision.md）。
        self.assertIn(".kv-marker>.marker-badge{top:-7px;right:-7px", self.html)
        self.assertIn("background:#e53935", self.html)
        self.assertIn("object-position:center", self.html)

    def test_cluster_expansion_tracked_via_spiderfied_events(self):
        self.assertIn("let expandedClusterLatLng=null", self.html)
        self.assertIn("cluster.on('spiderfied'", self.html)
        self.assertIn("cluster.on('unspiderfied'", self.html)
        self.assertIn("function restoreExpandedCluster()", self.html)
        self.assertIn("cluster.getVisibleParent(marker)", self.html)
        self.assertNotIn("rememberExpandedCluster", self.html)
        self.assertNotIn("expandedClusterVenueIds", self.html)

    def test_selection_decoupled_from_popup_lifecycle(self):
        self.assertIn("function closeDesktopDialog(updateHistory=true)", self.html)
        self.assertIn("function closeMobileVenueSheet()", self.html)
        close_desktop = self.html[self.html.index("function closeDesktopDialog"):]
        close_desktop = close_desktop[: close_desktop.index("\n}") + 2]
        self.assertNotIn("selectedLocationId=null", close_desktop)
        self.assertNotIn("selectedVenueId=null", close_desktop)
        close_mobile = self.html[self.html.index("function closeMobileVenueSheet"):]
        close_mobile = close_mobile[: close_mobile.index("\n}") + 2]
        self.assertNotIn("selectedLocationId=null", close_mobile)
        self.assertNotIn("selectedVenueId=null", close_mobile)

    def test_map_click_clears_selection(self):
        self.assertIn(
            "map.on('click',()=>{if(Date.now()-mobileSheetOpenedAt<350)return;"
            "closeMobileVenueSheet();uiState.selectedVenueId=null;"
            "uiState.selectedLocationId=null;highlightSelectedMarker()})",
            self.html,
        )

    def test_unspiderfied_clears_selection(self):
        unspi = self.html[self.html.index("cluster.on('unspiderfied'"):]
        unspi = unspi[: unspi.index("});") + 3]
        self.assertIn("selectedLocationId=null", unspi)
        self.assertIn("highlightSelectedMarker()", unspi)

    def test_no_settimeout_hacks_for_map_cluster(self):
        app_js = self.html[self.html.index("const uiState="):]
        self.assertNotIn("setTimeout(()=>{map.invalidateSize()", app_js)
        self.assertNotIn("setTimeout(()=>{map.invalidateSize", app_js)

    def test_initial_and_home_view_use_main_bounds(self):
        self.assertIn("const TW_MAIN_BOUNDS=L.latLngBounds", self.html)
        self.assertIn("map.fitBounds(TW_MAIN_BOUNDS,{padding:[16,16]})", self.html)
        self.assertIn("function fitTaiwanView(){map.fitBounds(TW_MAIN_BOUNDS", self.html)

    def test_mobile_filters_use_draft_until_done(self):
        self.assertIn("let draftFilters=null", self.html)
        self.assertIn("draftFilters={...uiState.filters}", self.html)
        self.assertIn("function applyMobileFilters()", self.html)
        self.assertIn("uiState.filters={...draftFilters}", self.html)
        self.assertIn("closeMobileFilters(true)", self.html)

    def test_share_lightbox_and_deep_links_exist(self):
        self.assertIn("function createShareUrl(eventId)", self.html)
        self.assertIn("async function shareEvent(eventId)", self.html)
        self.assertIn("navigator.clipboard.writeText(url)", self.html)
        self.assertIn("function openImageLightbox(", self.html)
        self.assertIn("url.searchParams.set('event',eventId)", self.html)
        self.assertIn("function handleDeepLink()", self.html)

    def test_public_acg_events_have_ids_and_metadata(self):
        events = [
            event
            for venue in self.data["venues"]
            for event in venue.get("ex", [])
            if event.get("c") == "ACG"
        ]
        self.assertTrue(events)
        self.assertTrue(all(event.get("id") for event in events))
        self.assertTrue(any(event.get("ip") for event in events))
        self.assertTrue(any(event.get("org") for event in events))
        self.assertTrue(any(event.get("lic") for event in events))

    def test_embedded_data_matches_public_json(self):
        match = re.search(r"^let DATA = (.+);$", self.html, re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(json.loads(match.group(1)), self.data)


if __name__ == "__main__":
    unittest.main()
