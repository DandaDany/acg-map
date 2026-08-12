#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
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

    def test_desktop_home_and_results_shells_exist(self):
        self.assertIn('class="desktop-shell home-mode"', self.html)
        self.assertIn('class="filter-pane"', self.html)
        self.assertIn('class="discover-pane"', self.html)
        self.assertIn('class="map-pane"', self.html)
        self.assertIn("grid-template-columns:var(--sidebar) var(--discover) minmax(0,1fr)", self.html)
        self.assertIn(".desktop-shell.home-mode{grid-template-columns:minmax(560px,55%) minmax(0,45%)}", self.html)
        self.assertIn(".desktop-shell.home-mode>.filter-pane{display:none}", self.html)

    def test_mobile_has_only_discover_and_map_tabs(self):
        ui_html = re.sub(r"^let DATA = .+;$", "", self.html, flags=re.MULTILINE)
        self.assertIn('id="discoverTab"', self.html)
        self.assertIn('id="mapTab"', self.html)
        self.assertNotIn('>Save<', ui_html)
        self.assertNotIn('data-tab="save"', ui_html)
        self.assertNotIn('id="saveTab"', ui_html)
        self.assertNotIn("收藏", ui_html)

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
        self.assertIn("function navigateToEvent(eventId,options={})", self.html)
        self.assertIn("function selectLocation(locationId,options={})", self.html)
        self.assertIn("function focusMapLocation(location,zoom=13,onComplete=null)", self.html)
        self.assertIn("data-location-id=", self.html)
        self.assertIn("ensureMapVisible(version", self.html)

    def test_image_markers_preserve_kv_orientation(self):
        self.assertIn('class="kv-marker-shell"', self.html)
        self.assertIn("function classifyKvMarker(marker)", self.html)
        self.assertIn("image.naturalWidth>=image.naturalHeight", self.html)
        self.assertIn(".kv-marker.landscape", self.html)

    def test_marker_toggle_is_right_on_desktop_and_centered_on_mobile(self):
        self.assertIn('class="segmented map-marker-toggle marker-toggle"', self.html)
        self.assertIn(".map-marker-toggle{position:absolute;z-index:1000;top:14px;right:14px", self.html)
        self.assertIn(".map-marker-toggle{top:10px;right:auto;left:50%;width:148px;transform:translateX(-50%);background:rgba(255,255,255,.96)}", self.html)
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
        self.assertIn("function buildPopupCards(origin)", self.html)
        # 可左右滑切換，順序以目前地點為原點、依距離由近到遠；
        # 不再另列「其他活動地點」清單。
        self.assertIn("function movePopupCard(delta)", self.html)
        self.assertIn("occurrenceDistance(origin", self.html)
        self.assertIn("a.location.id===origin.id?-1", self.html)
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

    def test_popup_close_is_unified_with_selection_lifecycle(self):
        self.assertIn("function closeActiveMapPopup(options={})", self.html)
        self.assertIn("function clearSelection()", self.html)
        self.assertIn("if(settings.clearSelection)clearSelection()", self.html)
        self.assertIn("closeActiveMapPopup({clearSelection:true,updateHistory});", self.html)
        self.assertIn("if(clear)clearSelection();", self.html)

    def test_map_click_clears_selection(self):
        self.assertIn("map.on('click',()=>{if(Date.now()-mobileSheetOpenedAt<350)return;closeActiveMapPopup({clearSelection:true})})", self.html)

    def test_unspiderfied_preserves_selection(self):
        unspi = self.html[self.html.index("cluster.on('unspiderfied'"):]
        unspi = unspi[: unspi.index("});") + 3]
        self.assertIn("expandedClusterLatLng=null", unspi)
        self.assertNotIn("selectedLocationId", unspi)
        self.assertNotIn("clearSelection", unspi)

    def test_latest_is_editorial_recent_discovery_and_keeps_first_seen(self):
        self.assertIn('id="homeRecentSection"', self.html)
        self.assertIn('data-home-action="latest-results"', self.html)
        self.assertNotIn('id="discoverMode"', self.html)
        self.assertNotIn('data-discover-mode="discover"', self.html)
        self.assertNotIn('data-discover-mode="latest"', self.html)
        self.assertIn("discoverMode:'discover'", self.html)
        self.assertIn("firstSeen:chooseValue(items,'first_seen')||null", self.html)
        self.assertIn("days>=0&&days<=6", self.html)
        self.assertIn("function getHomeRecentGroups(excludedIds)", self.html)
        self.assertIn("getLatestActivityGroups().filter(group=>!excludedIds.has(group.id)", self.html)
        self.assertIn("discoverScrollTop:{discover:0,latest:0}", self.html)

    def test_latest_results_do_not_change_marker_dataset(self):
        enter = self.html[self.html.index("function enterResults(context='all')"):self.html.index("function returnEditorialHome")]
        self.assertIn("if(context==='latest')", enter)
        latest_branch = enter[enter.index("if(context==='latest')"):]
        self.assertIn("renderDiscover(getDiscoverModeGroups())", latest_branch)
        self.assertNotIn("renderMapMarkers", latest_branch.split("else renderAll()",1)[0])
        self.assertNotIn("fitTaiwanView", latest_branch.split("else renderAll()",1)[0])

    def test_mobile_viewport_only_saves_visible_initialized_map(self):
        self.assertIn("mapHasVisibleView:false", self.html)
        self.assertIn("if(!MOBILE_QUERY.matches){map.fitBounds(TW_MAIN_BOUNDS", self.html)
        self.assertIn("(!MOBILE_QUERY.matches||uiState.tab==='map')&&uiState.mapHasVisibleView", self.html)
        self.assertIn("if(uiState.mapHasVisibleView&&uiState.mapView)map.setView", self.html)
        self.assertIn("else{fitTaiwanView();uiState.mapHasVisibleView=true}", self.html)

    def test_tab_to_discover_closes_popup_and_selection(self):
        self.assertIn("const leavingMap=uiState.tab==='map'&&tab==='discover'", self.html)
        self.assertIn("if(leavingMap)closeActiveMapPopup({clearSelection:true})", self.html)
        self.assertIn("sheet.classList.remove('show');sheet.setAttribute('aria-hidden','true')", self.html)

    def test_cluster_reveal_is_part_of_selection_pipeline(self):
        self.assertIn("function revealMarkerForLocation(locationId,version=selectionVersion", self.html)
        self.assertIn("cluster.zoomToShowLayer(marker", self.html)
        self.assertIn("cluster.getVisibleParent(marker)", self.html)
        self.assertIn("cluster.once('spiderfied',finish);parent.spiderfy()", self.html)
        self.assertIn("selectLocation(cur.id,{openPopup:!MOBILE_QUERY.matches,revealMarker:true", self.html)

    def test_selection_version_guards_async_callbacks(self):
        self.assertIn("let selectionVersion=0", self.html)
        self.assertIn("const version=++selectionVersion", self.html)
        self.assertGreaterEqual(self.html.count("version!==selectionVersion"), 3)
        self.assertIn("uiState.selectedLocationId!==locationId", self.html)

    def test_search_deeplink_and_popstate_share_navigation(self):
        self.assertIn("navigateToEvent(item.eventId,{updateHistory:true})", self.html)
        self.assertIn("navigateToEvent(id,{updateHistory:false})", self.html)
        popstate = self.html[self.html.index("window.addEventListener('popstate'"):]
        self.assertIn("navigateToEvent(id,{updateHistory:false})", popstate)
        self.assertIn("closeActiveMapPopup({clearSelection:true,updateHistory:false})", popstate)

    def test_rerender_preserves_selection_if_marker_still_exists(self):
        render = self.html[self.html.index("function renderMapMarkers()"):]
        render = render[: render.index("function highlightSelectedMarker")]
        self.assertNotIn("uiState.selectedLocationId=null", render)
        self.assertIn("if(selected&&!visibleLocationIds.has(selected))", render)
        self.assertIn("else requestAnimationFrame", render)

    def test_last_viewed_is_visual_only_and_survives_popup_close(self):
        self.assertIn("lastViewedLocationId:null", self.html)
        select = self.html[self.html.index("function selectLocation("):self.html.index("function navigateToEvent(")]
        self.assertIn("uiState.lastViewedLocationId=location.id", select)
        clear = self.html[self.html.index("function clearSelection()"):self.html.index("function revealMarkerForLocation")]
        self.assertNotIn("lastViewedLocationId", clear)
        highlight = self.html[self.html.index("function applyMarkerVisualState"):self.html.index("function locationById")]
        self.assertIn("uiState.selectedLocationId||uiState.lastViewedLocationId", highlight)
        self.assertIn("closeActiveMapPopup({clearSelection:true", self.html)

    def test_last_viewed_is_cleared_only_when_marker_is_invalid_or_floating(self):
        render = self.html[self.html.index("function renderMapMarkers()"):self.html.index("function applyMarkerVisualState")]
        self.assertIn("if(uiState.lastViewedLocationId&&!visibleLocationIds.has(uiState.lastViewedLocationId))uiState.lastViewedLocationId=null", render)
        floating = self.html[self.html.index("function openFloatingEvent"):self.html.index("function fitTaiwanView")]
        self.assertIn("uiState.lastViewedLocationId=null", floating)
        self.assertIn("if(group.floating){popupCards=[{group,location:popupOrigin}];popupCardIndex=0}", self.html)

    def test_popup_arrows_share_one_sequence_and_selection_pipeline(self):
        self.assertIn("function popupNavigationHtml()", self.html)
        self.assertIn('data-popup-move="-1"', self.html)
        self.assertIn('data-popup-move="1"', self.html)
        self.assertIn("popupCardIndex===0?'disabled'", self.html)
        self.assertIn("popupCardIndex===popupCards.length-1?'disabled'", self.html)
        self.assertIn("movePopupCard(dx<0?1:-1)", self.html)
        move = self.html[self.html.index("function movePopupCard"):self.html.index("function openMobileVenueSheet")]
        self.assertIn("selectLocation(cur.id", move)
        self.assertIn("preservePopupCards:true", move)
        self.assertIn("activeDialogMode==='event'", self.html)
        self.assertIn("event.key==='ArrowLeft'", self.html)

    def test_desktop_marker_hover_uses_inner_marker_state(self):
        self.assertIn("marker.on('mouseover'", self.html)
        self.assertIn("marker.on('mouseout'", self.html)
        self.assertIn("root.classList.toggle('is-hovered'", self.html)
        self.assertIn("marker.isHovered?2000:(highlighted?1000:0)", self.html)
        self.assertIn(".pinwrap.is-selected,.pinwrap.is-hovered,.kv-marker-shell.is-selected,.kv-marker-shell.is-hovered{transform:scale(1.3)}", self.html)
        self.assertNotIn(".leaflet-marker-icon{transform:scale(1.3)", self.html)

    def test_nearby_uses_filtered_unique_events_and_nearest_occurrence(self):
        self.assertIn("const NEARBY_RADIUS_M=2000", self.html)
        nearby = self.html[self.html.index("function buildNearbyActivities"):self.html.index("function formatDistance")]
        self.assertIn("buildPopupCards(originLocation)", nearby)
        self.assertIn("if(item.group.id===originLocation.event.id)return", nearby)
        self.assertIn("if(distanceMeters>NEARBY_RADIUS_M)return", nearby)
        self.assertIn("const nearestByEvent=new Map()", nearby)
        self.assertIn("!current||distanceMeters<current.distanceMeters", nearby)
        self.assertNotIn("venueId===originLocation.venueId", nearby)
        self.assertIn("return [...nearestByEvent.values()].sort", nearby)

    def test_nearby_runtime_algorithm_cases(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is unavailable")

        start = self.html.index("function buildNearbyActivities")
        end = self.html.index("function formatDistance", start)
        build_nearby = self.html[start:end]
        filter_start = self.html.index("function groupMatchesQuery")
        filter_end = self.html.index("function statusClass", filter_start)
        filter_pipeline = self.html[filter_start:filter_end]
        popup_start = self.html.index("function occurrenceDistance")
        popup_end = self.html.index("function preparePopupCards", popup_start)
        popup_pipeline = self.html[popup_start:popup_end]
        script = f"""
const NEARBY_RADIUS_M=2000;
const normalizeText=value=>String(value||'').toLowerCase();
const sortDiscoverActivities=items=>items;
const L={{latLng:(lat,lng)=>({{lat,lng,distanceTo:other=>Math.abs(other.lat-lat)}})}};
let DATA={{venues:[]}},activityGroups=new Map(),venueEventIndex=new Map();
let uiState={{filters:{{city:'all',time:'all',form:'all',fee:'all',multi:'all'}},query:''}};
{filter_pipeline}
{popup_pipeline}
{build_nearby}
const origin={{id:'A1',event:{{id:'A'}},venueId:'shared',lat:0,lng:0,status:{{kind:'ongoing'}},city:'台北市'}};
function item(eventId,id,distanceMeters,options={{}}){{
  const location={{id,event:{{id:eventId}},venueId:options.venueId||id,lat:distanceMeters,lng:0,status:{{kind:options.time||'ongoing'}},city:options.city||'台北市'}};
  const group={{id:eventId,title:options.title||eventId,ip:'',organizer:'',licensor:'',status:{{kind:'ongoing'}},form:options.form||'展覽',fee:options.fee||'免費',multiFilter:options.multi||'single',locations:[location]}};
  return {{group,location}};
}}
function setWorld(items,filters={{}},query=''){{
  activityGroups=new Map();venueEventIndex=new Map();
  for(const entry of items){{
    const existing=activityGroups.get(entry.group.id);
    if(existing)existing.locations.push(entry.location);else activityGroups.set(entry.group.id,entry.group);
    const rows=venueEventIndex.get(entry.location.venueId)||[];rows.push(entry.location);venueEventIndex.set(entry.location.venueId,rows);
  }}
  DATA={{venues:[...venueEventIndex.keys()].map(_id=>({{_id}}))}};
  uiState={{filters:{{city:'all',time:'all',form:'all',fee:'all',multi:'all',...filters}},query}};
}}
function ids(result){{return result.map(x=>x.eventId);}}
function assert(condition,message){{if(!condition)throw new Error(message);}}

setWorld([item('A','A2',300),item('B','B1',500)]);
assert(buildPopupCards(origin).length===2,'popup filter pipeline returned unexpected cards');
let result=buildNearbyActivities(origin);
assert(result.length===1&&result[0].eventId==='B','current event occurrences must be excluded');

setWorld([item('A','A1',0,{{venueId:'shared'}}),item('B','B1',0,{{venueId:'shared'}})]);
result=buildNearbyActivities(origin);
assert(result.length===1&&result[0].eventId==='B'&&result[0].distanceMeters===0,'same venue event must be included at zero distance');

setWorld([item('B','B1',400),item('B','B2',1200)]);
result=buildNearbyActivities(origin);
assert(result.length===1&&result[0].locationId==='B1'&&result[0].distanceMeters===400,'multi-location event must use nearest occurrence once');

setWorld([item('C','C1',2000),item('D','D1',2001)]);
result=buildNearbyActivities(origin);
assert(ids(result).join(',')==='C','2000m must be included and 2001m excluded');

const filterCases=[
  ['city',{{city:'台北市'}},'',{{city:'台北市'}},{{city:'高雄市'}}],
  ['time',{{time:'ongoing'}},'',{{time:'ongoing'}},{{time:'upcoming'}}],
  ['form',{{form:'展覽'}},'',{{form:'展覽'}},{{form:'快閃店'}}],
  ['fee',{{fee:'免費'}},'',{{fee:'免費'}},{{fee:'付費'}}],
  ['multi',{{multi:'multi'}},'',{{multi:'multi'}},{{multi:'single'}}],
  ['search',{{}},'needle',{{title:'needle event'}},{{title:'other event'}}],
];
for(const [filter,filters,query,visibleOptions,excludedOptions] of filterCases){{
  setWorld([item('VISIBLE','V-'+filter,500,visibleOptions),item('EXCLUDED','X-'+filter,400,excludedOptions)],filters,query);
  result=buildNearbyActivities(origin);
  assert(ids(result).join(',')==='VISIBLE',filter+'-excluded activity leaked into Nearby');
}}
"""
        completed = subprocess.run(
            [node, "-e", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_desktop_cluster_keyboard_contract(self):
        cluster = self.html[self.html.index("const cluster=L.markerClusterGroup") : self.html.index("const FORM_ICON=")]
        self.assertIn("className:'marker-cluster'", cluster)
        self.assertIn("icon.tabIndex=0", cluster)
        self.assertIn("icon.setAttribute('role','button')", cluster)
        self.assertIn("icon.setAttribute('aria-label','查看這個區域的活動')", cluster)
        self.assertIn("event.key!=='Enter'||MOBILE_QUERY.matches", cluster)
        self.assertIn("event.preventDefault();handleClusterActivate(layer)", cluster)
        desktop = cluster[cluster.index("function handleClusterActivate") : cluster.index("cluster.on('clusterclick'")]
        self.assertIn("openActivityPicker({mode:'cluster'", desktop)
        self.assertNotIn("selectLocation", desktop)
        self.assertNotIn("updateEventParam", desktop)
        self.assertNotIn("setTimeout", desktop)

    def test_activity_picker_focus_and_hover_geometry_contract(self):
        self.assertIn(".activity-picker-slot{display:grid;min-height:426px", self.html)
        self.assertIn(".activity-picker-copy{display:block;min-height:105px", self.html)
        self.assertIn("-webkit-line-clamp:3", self.html)
        self.assertIn(".activity-picker-card.is-hovered{z-index:1;border-color:#ff9a4d;transform:scale(1.3)}", self.html)
        self.assertIn("document.getElementById('activityPickerClose').focus({preventScroll:true})", self.html)
        self.assertIn("addEventListener('keydown',event=>trapFocus(event,document.getElementById('activityPickerOverlay')))", self.html)
        self.assertIn("if(document.getElementById('activityPickerOverlay').classList.contains('show'))closeActivityPicker()", self.html)
        close = self.html[self.html.index("function closeActivityPicker()") : self.html.index("function openNearbyPicker")]
        self.assertIn("activityPickerReturnFocus.focus({preventScroll:true})", close)
        for forbidden in ("clearSelection", "updateEventParam", "history."):
            self.assertNotIn(forbidden, close)

    def test_nearby_cta_hides_zero_and_formats_distance(self):
        cta = self.html[self.html.index("function nearbyCtaHtml"):self.html.index("function detailHtml")]
        self.assertIn("nearby.length?", cta)
        self.assertIn("附近 2 公里還有 '+nearby.length+' 個活動", cta)
        self.assertIn("if(distanceMeters<1)return '同地點'", self.html)
        self.assertIn("if(distanceMeters<1000)return Math.round(distanceMeters)+' 公尺'", self.html)

    def test_cluster_and_nearby_share_activity_picker(self):
        self.assertEqual(self.html.count('id="activityPickerOverlay"'), 1)
        self.assertIn("function openActivityPicker({mode,items,title,sourceLocationId=null})", self.html)
        self.assertIn("openActivityPicker({mode:'cluster'", self.html)
        self.assertIn("openActivityPicker({mode:'nearby'", self.html)
        self.assertIn("zoomToBoundsOnClick:false,spiderfyOnMaxZoom:false", self.html)
        cluster_handler = self.html[self.html.index("function handleClusterActivate"):self.html.index("cluster.on('clusterclick'")]
        self.assertIn("if(MOBILE_QUERY.matches)", cluster_handler)
        self.assertIn("clusterLayer.zoomToBounds()", cluster_handler)
        self.assertIn("clusterLayer.spiderfy()", cluster_handler)

    def test_picker_close_is_transient_and_selection_is_unified(self):
        close = self.html[self.html.index("function closeActivityPicker()"):self.html.index("function openNearbyPicker")]
        for forbidden in ("clearSelection", "selectedLocationId", "lastViewedLocationId", "updateEventParam", "flyTo", "spiderfy"):
            self.assertNotIn(forbidden, close)
        select = self.html[self.html.index("function selectActivityPickerItem"):self.html.index("function mobileCardHtml")]
        self.assertLess(select.index("closeActivityPicker()"), select.index("selectLocation(locationId"))
        self.assertIn("if(document.getElementById('activityPickerOverlay').classList.contains('show'))closeActivityPicker()", self.html)

    def test_popup_metadata_and_empty_address_rules(self):
        popup_meta = self.html[self.html.index("function popupMetadataHtml"):self.html.index("function actionHtml")]
        self.assertIn("group.ip?", popup_meta)
        self.assertIn("group.organizer?", popup_meta)
        self.assertNotIn("licensor", popup_meta)
        app_js = self.html[self.html.index("const uiState="):]
        self.assertNotIn("地址未提供", app_js)
        self.assertNotIn("地點未提供", app_js)
        self.assertIn("FLOATING_ADDRESS_TEXT", app_js)

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
