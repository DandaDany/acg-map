from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
text=(ROOT/'public'/'taiwan-exhibition-map.html').read_text(encoding='utf-8')
decision=(ROOT/'decision.md').read_text(encoding='utf-8')

# Desktop navigation controls: Home + / - share the upper-right utility stack.
assert 'class="map-nav-stack"' in text
assert 'id="mapHomeButton"' in text
assert 'id="mapZoomInButton"' in text
assert 'id="mapZoomOutButton"' in text
assert "document.getElementById('mapZoomInButton').addEventListener('click',()=>map.zoomIn())" in text
assert "document.getElementById('mapZoomOutButton').addEventListener('click',()=>map.zoomOut())" in text
assert '.leaflet-control-zoom{display:none}' in text
assert '.map-zoom-tool{display:none}.leaflet-control-zoom{display:block}' in text

# Desktop activity card is wider/taller and has no internal vertical scrolling.
assert 'width:min(960px,calc(100% - 32px))' in text
assert 'min-height:286px' in text
desktop_css=text[text.index('.desktop-map-card{'):text.index('html[data-theme="dark"] .home-filter-close')]
assert 'overflow-y:auto' not in desktop_css
assert 'overflow:visible' in desktop_css

# Cross-activity carousel is removed from both desktop and mobile UI.
for forbidden in ('function popupNavigationHtml()','data-popup-move=','function movePopupCard(delta)',"event.key==='ArrowLeft'","movePopupCard(dx<0?1:-1)"):
    assert forbidden not in text
mobile=text[text.index("document.getElementById('mobileVenueBody').addEventListener"):text.index("document.getElementById('mobileVenueGrip')")]
assert 'touchstart' not in mobile and 'touchend' not in mobile
assert 'function buildNearbyActivities' in text  # Nearby distance logic remains.

# Destination cluster policy: canonical cultural parks fullscreen, mixed ordinary clusters still zoom/spiderfy.
for name in ('華山1914文化創意產業園區','松山文創園區','高雄市駁二藝術特區','駁二藝術特區','花蓮文化創意產業園區','嘉義文化創意產業園區'):
    assert name in text
assert 'function destinationVenueGroup(location)' in text
assert 'function destinationClusterInfo(items)' in text
cluster=text[text.index('function handleClusterActivate'):text.index("cluster.on('clusterclick'")]
assert 'destinationClusterInfo(items)' in cluster
assert "openActivityPicker({mode:'cluster'" in cluster
assert 'clusterLayer.zoomToBounds()' in cluster and 'clusterLayer.spiderfy()' in cluster
assert 'venueIds.size===1' not in cluster

# City filter changes viewport only; they do not select an activity or force mobile Explore into Map.
desktop_start=text.index("document.getElementById('filterOptions').addEventListener")
desktop_end=text.index("document.getElementById('clearFilters').addEventListener",desktop_start)
desktop=text[desktop_start:desktop_end]
assert "if(key==='city'&&!MOBILE_QUERY.matches){uiState.pendingCityView=null;fitCityView(value)}" in desktop
assert 'selectLocation' not in desktop
mobile_apply=text[text.index('function applyMobileFilters()'):text.index('function setTab(')]
assert 'const previousCity=uiState.filters.city' in mobile_apply
assert "else uiState.pendingCityView=uiState.filters.city" in mobile_apply
assert "setTab('map'" not in mobile_apply
set_tab=text[text.index('function setTab('):text.index('let searchTimer=')]
assert 'uiState.pendingCityView!==null' in set_tab
assert 'fitCityView(city)' in set_tab

for phrase in ('Desktop Map controls / Destination cluster / City viewport 微調','Map popup 不再提供跨活動 carousel','Desktop 選定縣市 Filter 後立即 `fitCityView(city)`'):
    assert phrase in decision
print('map follow-up UX: PASS')
