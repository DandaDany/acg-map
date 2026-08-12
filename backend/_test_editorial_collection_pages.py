from pathlib import Path

HTML = Path(__file__).resolve().parents[1] / "public" / "taiwan-exhibition-map.html"
text = HTML.read_text(encoding="utf-8")

# CTA semantics: more content -> a Collection, not legacy Results mode.
for action in ('week-collection', 'nearby-collection', 'latest-collection'):
    assert f'data-home-action="{action}"' in text
assert 'data-home-action="week-results"' not in text
assert 'data-home-action="latest-results"' not in text
assert 'function enterResults' not in text
assert "exploreView='results'" not in text
assert 'resultsContext' not in text

# One Collection template, persistent map, image-first cards.
assert 'id="collectionPanel"' in text
assert 'id="collectionGrid"' in text
assert 'id="collectionLoadMore"' in text
assert 'class="collection-card collection-event-target"' in text
assert 'collection-card-media' in text
assert 'grid-template-columns:repeat(2,minmax(0,1fr))' in text
assert 'grid-template-columns:1fr' in text
assert 'COLLECTION_BATCH_DESKTOP=8,COLLECTION_BATCH_MOBILE=6' in text
assert "uiState.collectionVisibleCount+=collectionBatchSize()" in text

# Collection context has week/latest/nearby/search without changing marker dataset.
assert "if(context==='nearby')return collectionNearbyEntries()" in text
assert "if(context==='week')return collectionGroupEntries(collectionWeekGroups(),'week')" in text
assert "if(context==='latest')return collectionGroupEntries(getLatestActivityGroups(),'latest')" in text
collection = text[text.index('function renderCollection'):text.index('function requestHomeLocation')]
assert 'renderMapMarkers' not in collection
assert 'fitTaiwanView' not in collection
assert 'fitBounds' not in collection

# Filter is progressive disclosure only; Nearby map is a distinct action.
assert "document.getElementById('collectionFilterButton').addEventListener('click',openHomeFilterDrawer)" in text
assert "document.getElementById('collectionNearbyMap').addEventListener('click',openHomeNearbyMap)" in text
assert 'home-section-actions' in text

# Card interactions preserve the unified map selection pipeline.
assert "data-collection-location-id" in text
assert "selectLocation(target.dataset.collectionLocationId,{updateHistory:true})" in text
assert "setHomeMarkerHover(target.dataset.collectionLocationId,true)" in text

# Search results use Collection cards, not the old Discover list.
search = text[text.index("uiState.query=input.value.trim();"):text.index("input.addEventListener('focus'")]
assert "enterCollection('search')" in search
assert "collectionContext='search'" in search
assert 'renderDiscover' not in search
print('editorial collection pages: PASS')
