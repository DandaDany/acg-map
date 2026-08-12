from pathlib import Path
import re

ROOT=Path('.')
HTML=ROOT/'public'/'taiwan-exhibition-map.html'
DECISION=ROOT/'decision.md'
MAP_TEST=ROOT/'backend'/'_test_map_ux.py'
HOME_TEST=ROOT/'backend'/'_test_editorial_c_home.py'
NEW_TEST=ROOT/'backend'/'_test_map_exploration_polish.py'
text=HTML.read_text(encoding='utf-8')

def replace_once(old,new,label):
    global text
    c=text.count(old)
    if c!=1:
        raise RuntimeError(f'{label}: expected 1 match, found {c}')
    text=text.replace(old,new,1)

def sub_once(pattern,repl,label,flags=0):
    global text
    text2,c=re.subn(pattern,repl,text,count=1,flags=flags)
    if c!=1:
        raise RuntimeError(f'{label}: expected 1 regex match, found {c}')
    text=text2

# ---------------------------------------------------------------------------
# Decision document updates.
# ---------------------------------------------------------------------------
decision=DECISION.read_text(encoding='utf-8')
old="- 每個活動各自一個 marker；同場館／同座標的多個活動會聚合。桌機點擊聚合開啟共用的全螢幕 Activity Picker，不同步縮放；手機維持 zoom／最大層級 spiderfy。個別 marker 不顯示數字徽章；聚合徽章顯示該處活動數。"
new="- 每個活動各自一個 marker；同場館／同座標的多個活動會聚合。桌機 cluster 只有在所有子 marker 都屬於同一 venue/location 且確實有多活動時，才開啟全螢幕 Activity Picker；一般由不同地點組成的 cluster 必須持續 zoom-to-bounds，最大層級再 spiderfy。手機維持 zoom／最大層級 spiderfy。個別 marker 不顯示數字徽章；聚合徽章顯示該處活動數。"
if decision.count(old)!=1:raise RuntimeError('decision cluster bullet mismatch')
decision=decision.replace(old,new,1)
old="- 手機版活動 popup 為橫式卡片（左 KV、右資訊）、高度約螢幕 1/3。單一場館多場活動不再另出選擇格。"
new="- 桌機與手機活動 popup 共用橫式卡片資訊結構：左 KV、右資訊。手機高度約螢幕 1/3；桌機使用地圖內底部 docked card，不使用阻斷探索的全螢幕 event modal。單一活動直接顯示卡片；只有同一 location 的多活動才使用 Fullscreen Activity Picker。"
if decision.count(old)!=1:raise RuntimeError('decision popup layout bullet mismatch')
decision=decision.replace(old,new,1)
old="- 桌機與手機 popup 顯示 IP、主辦、日期、目前活動地點；空 IP、空主辦與空地址整列不顯示，不以 placeholder 代替。浮動活動仍顯示「請至官方網站查詢地點」。本次 popup 不新增授權商。"
new="- Popup 的閱讀順序固定為活動名稱 → 目前地點／導航 → 目前 location 日期 → `#縣市`／`#付費狀態` → 官方資訊／分享；IP、主辦與授權商都不進 compact popup。浮動活動仍顯示「請至官方網站查詢地點」。Nearby CTA 與活動序列導覽屬 secondary interaction，可保留在主要資訊之後。"
if decision.count(old)!=1:raise RuntimeError('decision popup metadata bullet mismatch')
decision=decision.replace(old,new,1)
old="- Nearby CTA 與桌機 Cluster 共用同一個 Fullscreen Activity Picker。Picker 是 transient UI，不寫入核心 selection 或 history；Nearby Picker 關閉後保留底層 popup，點卡片後一律關閉 Picker 再呼叫 `selectLocation()`。"
new="- Nearby CTA 與「同地點多活動」的桌機 Cluster／venue selection 共用 Fullscreen Activity Picker。Picker 是 transient UI，不寫入核心 selection 或 history；一般多地點 Cluster 不得開 Picker。Nearby Picker 關閉後保留底層 popup，點卡片後一律關閉 Picker 再呼叫 `selectLocation()`。"
if decision.count(old)!=1:raise RuntimeError('decision nearby picker bullet mismatch')
decision=decision.replace(old,new,1)
old="- 桌機與手機的活動 popup 皆顯示目前地點所在縣市的 hashtag（例：`#台北市`）。"
new="- 桌機與手機活動 popup 皆保留純文字 tertiary context：`#縣市` 與 `#付費狀態`（例：`#台北市 #免費`）；不擴張成活動形式／IP 等大量 chips。"
if decision.count(old)!=1:raise RuntimeError('decision hashtags bullet mismatch')
decision=decision.replace(old,new,1)
insert="""

## 2026-08-12 — Map exploration / Filter 微調

- 篩選的「活動時段」只保留 `不限／進行中／即將開始／即將結束`，不再提供「今天／週末／未來 7 天」preset；`進行中` 與 `即將結束` 為互斥狀態。
- 「活動時段」下方提供月曆。點單一日期代表 `event.start <= selected_date <= event.end`；日期選擇與狀態選擇互斥，選其中一種會取代另一種。月曆只以小點提示當天有符合其他 active filters 的活動，不在日期格顯示活動數。
- 「最近發現」Collection 的母集合固定為 `first_seen` 最近 7 個 Asia/Taipei 日曆日；進入這頁後仍可篩選，但所有 facet count、disabled 狀態與摘要統計都必須先限制在這個 7 日母集合，再套 city／time／form／fee／multi／query。
- 暖白模式的 Filter 關閉 X 使用 warm semantic surface／text token，不得維持黑底高對比；dark mode 使用對應深色 surface。
- 使用者自己的位置 marker 使用鮮紅實心圓＋白色 halo＋淡紅外圈；活動 selected marker 仍用原 marker shape 的紅色 outline，兩者不得混為同一語意。
"""
decision=decision.rstrip()+insert+'\n'
DECISION.write_text(decision,encoding='utf-8')

# ---------------------------------------------------------------------------
# Update legacy regressions so they protect the new product decisions.
# ---------------------------------------------------------------------------
home_test=HOME_TEST.read_text(encoding='utf-8')
home_test=home_test.replace("assert \"if(value==='next7')\" in text\n","assert \"locationOverlapsCalendarRange(location,todayDay,todayDay+6)\" in text\n")
HOME_TEST.write_text(home_test,encoding='utf-8')

map_test=MAP_TEST.read_text(encoding='utf-8')
old="""    def test_desktop_dialog_and_mobile_sheet_exist(self):
        self.assertIn('id=\"dialogOverlay\"', self.html)
        self.assertIn('role=\"dialog\" aria-modal=\"true\"', self.html)
        self.assertIn(\"function openDesktopEventModal(\", self.html)
        self.assertIn(\"function openDesktopVenuePicker(\", self.html)
        self.assertIn('id=\"mobileVenueSheet\"', self.html)
        self.assertIn(\"function openMobileVenueSheet(\", self.html)
        self.assertIn(\"function closeMobileVenueSheet(\", self.html)

    def test_mobile_popup_is_horizontal_swipeable_card(self):
        # 桌機活動詳情對話框：固定高度、內部捲動。
        self.assertIn(\"height:min(760px,calc(100dvh - 72px))\", self.html)
        self.assertIn(\"overflow-y:auto\", self.html)
        # 手機活動 popup 為橫式卡片（左 KV、右資訊）、高度約螢幕 1/3（decision.md）。
        self.assertIn(\"height:clamp(210px,34dvh,360px)\", self.html)
        self.assertIn(\"mobile-card-kv\", self.html)
        self.assertIn(\"function buildPopupCards(origin)\", self.html)
"""
new="""    def test_desktop_map_dock_and_mobile_sheet_exist(self):
        self.assertIn('id=\"desktopMapCard\"', self.html)
        self.assertIn('id=\"desktopMapCardBody\"', self.html)
        self.assertIn(\"function openDesktopMapCard(\", self.html)
        self.assertIn(\"function openDesktopVenuePicker(\", self.html)
        self.assertIn('id=\"mobileVenueSheet\"', self.html)
        self.assertIn(\"function openMobileVenueSheet(\", self.html)
        self.assertIn(\"function closeMobileVenueSheet(\", self.html)

    def test_mobile_and_desktop_popup_share_horizontal_card(self):
        # 手機約螢幕 1/3；桌機則是地圖內 bottom dock，不阻斷地圖探索。
        self.assertIn(\"height:clamp(210px,34dvh,360px)\", self.html)
        self.assertIn(\"height:clamp(214px,27dvh,260px)\", self.html)
        self.assertIn(\"mobile-card-kv\", self.html)
        self.assertIn(\"function mapCardHtml(group,location)\", self.html)
        self.assertIn(\"function buildPopupCards(origin)\", self.html)
"""
if old not in map_test: raise RuntimeError('map ux popup tests mismatch')
map_test=map_test.replace(old,new,1)
MAP_TEST.write_text(map_test,encoding='utf-8')

NEW_TEST.write_text(r'''from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
text=(ROOT/'public'/'taiwan-exhibition-map.html').read_text(encoding='utf-8')
decision=(ROOT/'decision.md').read_text(encoding='utf-8')

# 1. Desktop cluster picker is only for one venue/location with multiple activities.
cluster=text[text.index('function handleClusterActivate'):text.index("cluster.on('clusterclick'")]
assert "venueIds.size===1&&eventIds.size>1" in cluster
assert "openActivityPicker({mode:'cluster'" in cluster
assert 'clusterLayer.zoomToBounds()' in cluster
assert 'clusterLayer.spiderfy()' in cluster

# 2. Recent Collection keeps Filter, but facet universe and stat summary are Latest/first_seen seven-day scoped.
assert 'function facetBaseGroups(state=uiState)' in text
assert "state.exploreView==='collection'&&state.collectionContext==='latest'" in text
assert 'groups=groups.filter(group=>isLatestGroup(group))' in text
assert "最近 7 天新加入 ACG Map 的活動" in text
assert 'function filterSummaryGroups()' in text

# 3. Time filter = status OR explicit calendar date; no Today / Weekend / Next7 presets.
meta=text[text.index('const FILTER_META='):text.index('/* ===== 多店')]
assert "time:{title:'活動時段'" in meta
for obsolete in ("value:'today'","value:'weekend'","value:'next7'"):
    assert obsolete not in meta
for status in ("value:'ongoing'","value:'upcoming'","value:'ending'"):
    assert status in meta
assert 'function timeFilterDate(value)' in text
assert "locationActiveOnCalendarDay(location,day)" in text
assert 'class="filter-calendar"' in text
assert 'data-calendar-date=' in text
assert 'data-calendar-shift=' in text
assert 'filter-calendar-day.has-events i' in text

# 4. Warm Filter close is not the old black icon surface.
assert '.home-filter-close{display:none;margin-left:auto;border-color:var(--line);background:#fff;color:#51463e' in text
assert 'html[data-theme="dark"] .home-filter-close' in text

# 5. User position is bright red + white halo; selected event remains outline-based.
assert '.user-location-dot{background:#ff2d2d;box-shadow:0 0 0 7px rgba(255,45,45,.18)' in text
assert '.pinwrap.is-selected .pinsvg>path:first-child{stroke:#ff2d2d}' in text

# 6. Desktop event details are a map dock, while same-location multi-event selection stays fullscreen Picker.
assert 'id="desktopMapCard"' in text
assert 'function openDesktopMapCard(' in text
modal=text[text.index("function openDesktopEventModal"):text.index("function openDesktopVenuePicker")]
assert 'openDesktopMapCard(' in modal
assert "document.getElementById('dialogOverlay').classList.add('show')" not in modal
assert "document.getElementById('desktopMapCard').classList.contains('show')" in text

# 7. Shared popup hierarchy: What -> Where/Nav -> When -> #city/#fee -> actions. No IP/organizer in compact card.
card=text[text.index('function mapCardHtml(group,location)'):text.index('function mobileCardHtml')]
assert card.index("<h2>") < card.index('mapCardLocationHtml') < card.index('mobile-card-date') < card.index('popupContextHtml') < card.index('actionHtml')
assert 'popupMetadataHtml' not in card
assert 'IP：' not in card and '主辦：' not in card
assert "const tags=[location.city,group.fee].filter(Boolean)" in text
assert "官方資訊 ↗" in text

for phrase in ('Map exploration / Filter 微調','最近發現','鮮紅實心圓','`#縣市` 與 `#付費狀態`'):
    assert phrase in decision
print('map exploration polish: PASS')
''',encoding='utf-8')
