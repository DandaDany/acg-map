from pathlib import Path

HTML = Path(__file__).resolve().parents[1] / "public" / "taiwan-exhibition-map.html"
DECISION = Path(__file__).resolve().parents[1] / "decision.md"
text = HTML.read_text(encoding="utf-8")
decision = DECISION.read_text(encoding="utf-8")

# True C information architecture, not #91 pills.
assert 'id="editorialHome"' in text
assert '>這週想去哪？<' in text
assert '>附近<' in text
assert '>最近發現<' in text
assert 'id="discoverIntents"' not in text
assert 'todayIntentCount' not in text
assert 'weekendIntentCount' not in text
assert 'intent-count' not in text
assert 'id="discoverMode"' not in text
assert 'data-discover-mode=' not in text

# Week = rolling seven days; home has editorial ranking/diversity and real Results route.
assert "if(value==='next7')" in text
assert "day,day+6" in text
assert 'function homeEditorialRank' in text
assert 'function pickEditorialDiverse' in text
assert "safeUrl(group.image,true)&&homeWeekLocations" in text
assert "enterResults('week')" in text
assert "uiState.filters.time='next7'" in text

# Nearby is a location section, opt-in only, max 20 km / 3 events, no automatic fit.
assert 'const HOME_NEARBY_MAX_M=20000' in text
assert '使用目前位置' in text
assert 'navigator.geolocation.getCurrentPosition' in text
assert '.slice(0,3)' in text
request_block = text[text.index('function requestHomeLocation'):text.index('function openHomeNearbyMap')]
assert 'fitBounds' not in request_block and 'flyTo' not in request_block and 'setView' not in request_block
assert 'function openHomeNearbyMap' in text and 'map.fitBounds' in text[text.index('function openHomeNearbyMap'):text.index('function closeHomeFilterDrawer')]
assert 'user-location-dot' in text

# Desktop: editorial content + persistent map; tool sidebar only in Results.
assert '.desktop-shell.home-mode{grid-template-columns:minmax(560px,55%) minmax(0,45%)}' in text
assert '.desktop-shell.home-mode>.filter-pane{display:none}' in text
assert 'id="homeFilterButton"' in text
assert 'id="homeFilterScrim"' in text
assert '.desktop-map-search{position:absolute' in text
assert '.map-marker-toggle{position:absolute;z-index:1000;top:14px;right:14px' in text
assert 'function setHomeMarkerHover' in text
assert 'marker.isHovered=hovered' in text

# Mobile: brand + icons, no permanent search bar, only Explore/Map navigation.
assert '<div class="mobile-brand">ACG MAP</div>' in text
assert 'id="mobileSearchButton"' in text
assert 'id="mobileSearchPanel"' in text
assert '>探索</button>' in text
assert '>地圖</button>' in text

# Light editorial system and existing map selection architecture coexist.
assert '--bg:#f7f3ed' in text
assert 'function selectLocation(locationId,options={})' in text
assert 'function buildNearbyActivities(originLocation)' in text
assert 'cluster.zoomToShowLayer(marker' in text
assert "firstSeen:chooseValue(items,'first_seen')||null" in text
assert 'Editorial C 探索首頁' in decision
print('editorial C home UX: PASS')
