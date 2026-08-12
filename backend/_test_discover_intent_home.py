from pathlib import Path

HTML = Path(__file__).resolve().parents[1] / "public" / "taiwan-exhibition-map.html"
text = HTML.read_text(encoding="utf-8")

assert 'id="discoverIntents"' in text
assert 'data-discover-time="today"' in text
assert 'data-discover-time="weekend"' in text
assert 'data-discover-sort="distance"' in text
assert "{value:'today',label:'今天'}" in text
assert "{value:'weekend',label:'本週末'}" in text
assert "locationMatchesTimeFilter(location,filters.time)" in text
assert "time:value" in text  # quick counts replace their own time dimension
assert "navigator.geolocation.getCurrentPosition" in text
assert "uiState.discoverSort='distance'" in text
assert "nearestLocationForGroup" in text
assert "data-location-id=\"'+esc(first.id)+'\"" in text
assert "fitTaiwanView();return" not in text[text.index('function requestDistanceSort'):text.index("let activityPickerMode=''")]
assert '.desktop-map-search{position:absolute' in text
assert '.map-marker-toggle{position:absolute;z-index:1000;top:14px;right:14px' in text
assert '<aside class="filter-pane"' in text and text.index('id="q"') > text.index('<section class="map-pane"')
assert 'id="mq"' in text  # mobile keeps its own top search
assert '現在可去' not in text
print('discover intent home UX: PASS')
