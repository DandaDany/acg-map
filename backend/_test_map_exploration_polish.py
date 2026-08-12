from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
text=(ROOT/'public'/'taiwan-exhibition-map.html').read_text(encoding='utf-8')
decision=(ROOT/'decision.md').read_text(encoding='utf-8')

# 1. Desktop cluster picker is destination-aware; ordinary clusters still zoom/spiderfy.
cluster=text[text.index('function handleClusterActivate'):text.index("cluster.on('clusterclick'")]
assert "destinationClusterInfo(items)" in cluster
assert "openActivityPicker({mode:'cluster'" in cluster
assert 'clusterLayer.zoomToBounds()' in cluster
assert 'clusterLayer.spiderfy()' in cluster
assert "venueIds.size===1" not in cluster

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
