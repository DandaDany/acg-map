from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / 'public' / 'taiwan-exhibition-map.html'
DECISION = ROOT / 'decision.md'
FOLLOWUP = ROOT / 'backend' / '_test_map_followup_ux.py'
POLISH = ROOT / 'backend' / '_test_map_exploration_polish.py'
MAP_UX = ROOT / 'backend' / '_test_map_ux.py'


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 match, found {count}')
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Runtime cluster policy
# ---------------------------------------------------------------------------
text = HTML.read_text(encoding='utf-8')

# Remove the PR #95 destination-name whitelist. Cluster behavior now depends on
# whether spatial zoom can still resolve the markers, not on venue semantics.
pattern = re.compile(r"\nconst DESTINATION_VENUE_GROUPS=\[.*?\nfunction clusterPickerItems", re.S)
text, count = pattern.subn('\nfunction clusterPickerItems', text, count=1)
if count != 1:
    raise RuntimeError(f'remove destination whitelist: expected 1 match, found {count}')

old_picker = '''function clusterPickerItems(clusterLayer){
  const seen=new Set();
  return clusterLayer.getAllChildMarkers().map(marker=>{
    if(!marker.locationId||seen.has(marker.locationId))return null;
    seen.add(marker.locationId);
    const location=locationById(marker.locationId);
    const group=location&&activityGroups.get(location.event.id);
    return location&&group?{eventId:group.id,locationId:location.id,group,location}:null;
  }).filter(Boolean);
}
'''
new_picker = '''function clusterPickerItems(clusterLayer){
  const seenEvents=new Set();
  return clusterLayer.getAllChildMarkers().map(marker=>{
    if(!marker.locationId)return null;
    const location=locationById(marker.locationId);
    const group=location&&activityGroups.get(location.event.id);
    if(!location||!group||seenEvents.has(group.id))return null;
    seenEvents.add(group.id);
    return {eventId:group.id,locationId:location.id,group,location};
  }).filter(Boolean);
}
'''
text = replace_once(text, old_picker, new_picker, 'dedupe cluster picker by event')

old_handler = '''function handleClusterActivate(clusterLayer){
  if(!clusterLayer)return;
  const items=clusterPickerItems(clusterLayer);
  const destination=!MOBILE_QUERY.matches?destinationClusterInfo(items):null;
  if(destination){openActivityPicker({mode:'cluster',items,title:destination.group.label+'的活動'});return}
  if(map.getZoom()<map.getMaxZoom())clusterLayer.zoomToBounds();
  else clusterLayer.spiderfy();
}
'''
new_handler = '''function handleClusterActivate(clusterLayer){
  if(!clusterLayer)return;
  if(map.getZoom()<map.getMaxZoom()){clusterLayer.zoomToBounds();return}
  const items=clusterPickerItems(clusterLayer);
  if(items.length>4){openActivityPicker({mode:'cluster',items,title:'這個地點的活動'});return}
  clusterLayer.spiderfy();
}
'''
text = replace_once(text, old_handler, new_handler, 'max-zoom cluster threshold')
HTML.write_text(text, encoding='utf-8')

# ---------------------------------------------------------------------------
# Durable product decisions
# ---------------------------------------------------------------------------
decision = DECISION.read_text(encoding='utf-8')
replacements = {
    "- 每個活動各自一個 marker；同場館／同座標的多個活動會聚合。桌機只有 canonical 大型文化園區 destination cluster（華山、松菸、駁二，以及同類花蓮／嘉義文化創意產業園區）在目前篩選後仍含 2 個以上不同活動時，才直接開啟全螢幕 Activity Picker；一般 cluster 必須持續 zoom-to-bounds，最大層級再 spiderfy。若 broad cluster 同時混入園區外 marker，也先 zoom，不能因其中包含園區就提前滿版。手機維持 zoom／最大層級 spiderfy。個別 marker 不顯示數字徽章；聚合徽章顯示該處活動數。":
    "- 每個活動各自一個 marker；同場館／同座標的多個活動會聚合。Cluster 的處理只看空間是否還能拆解，不看場館名稱或類型：未到最大 zoom 一律 `zoomToBounds()`；到最大 zoom 後，以不同 event ID 計算活動數，2–4 個活動使用 spiderfy，5 個以上直接開啟 Fullscreen Activity Picker。此規則桌機與手機一致；同一 event 因多個 location marker 重疊時只計 1 個活動。個別 marker 不顯示數字徽章；聚合徽章顯示該處活動數。",
    "- Map popup 不提供跨活動上一個／下一個、`1 / N`、桌機方向鍵切換或手機左右 swipe。使用者要看另一活動時直接點另一 marker；同園區大量活動使用 Fullscreen Activity Picker，附近探索使用 Nearby Picker，大量瀏覽使用 Collection。底層距離清單只可作為 Nearby 計算，不得再暴露成 popup carousel。":
    "- Map popup 不提供跨活動上一個／下一個、`1 / N`、桌機方向鍵切換或手機左右 swipe。使用者要看另一活動時直接點另一 marker；最大 zoom 仍無法空間拆解且含 5 個以上不同活動的 cluster 使用 Fullscreen Activity Picker，附近探索使用 Nearby Picker，大量瀏覽使用 Collection。底層距離清單只可作為 Nearby 計算，不得再暴露成 popup carousel。",
    "- 桌機與手機活動 popup 共用橫式卡片資訊結構：左 KV、右資訊。手機高度約螢幕 1/3；桌機使用地圖內底部 docked card，不使用阻斷探索的全螢幕 event modal。桌機 card 應盡量使用地圖寬度、以內容撐高並一次顯示核心資訊，不提供 card 內垂直捲動。大型文化園區 destination 的多活動 cluster 才使用 Fullscreen Activity Picker。":
    "- 桌機與手機活動 popup 共用橫式卡片資訊結構：左 KV、右資訊。手機高度約螢幕 1/3；桌機使用地圖內底部 docked card，不使用阻斷探索的全螢幕 event modal。桌機 card 應盡量使用地圖寬度、以內容撐高並一次顯示核心資訊，不提供 card 內垂直捲動。Fullscreen Activity Picker 只在使用者已 zoom 到最大層級、cluster 仍含 5 個以上不同活動時作為選擇介面。",
    "- Nearby CTA 與大型文化園區 destination cluster／需要明確選活動的 venue selection 共用 Fullscreen Activity Picker。Picker 是 transient UI，不寫入核心 selection 或 history；一般多地點 Cluster 不得開 Picker。Nearby Picker 關閉後保留底層 popup，點卡片後一律關閉 Picker再呼叫 `selectLocation()`。":
    "- Nearby CTA、最大 zoom 且含 5 個以上不同活動的 cluster，以及需要明確選活動的 venue selection 共用 Fullscreen Activity Picker。Picker 是 transient UI，不寫入核心 selection 或 history；未到最大 zoom 的 Cluster 不得提前開 Picker。Nearby Picker 關閉後保留底層 popup，點卡片後一律關閉 Picker 再呼叫 `selectLocation()`。",
    "## 2026-08-12 — Desktop Map controls / Destination cluster / City viewport 微調":
    "## 2026-08-12 — Desktop Map controls / Cluster threshold / City viewport 微調",
    "- Map popup 不再提供跨活動 carousel：沒有 `1 / N`、左右箭頭、桌機方向鍵或手機左右 swipe。另一個活動由 marker、Destination Picker、Nearby Picker 或 Collection 進入。":
    "- Map popup 不再提供跨活動 carousel：沒有 `1 / N`、左右箭頭、桌機方向鍵或手機左右 swipe。另一個活動由 marker、Cluster Picker、Nearby Picker 或 Collection 進入。",
    "- 大型文化園區以 UI 靜態 canonical destination config 判定，不寫入每日活動資料。現階段包含華山1914、松山文創園區、駁二藝術特區（含官方／既有別名）、花蓮文化創意產業園區、嘉義文化創意產業園區。只有 cluster 的所有目前可見子活動都屬於同一 destination 且至少有 2 個不同活動時才直接 Fullscreen；混合一般地點的 cluster 先 zoom／spiderfy。":
    "- Fullscreen cluster 不再使用華山／松菸／駁二等場館白名單，也不依 venue name alias 判定。未到最大 zoom 一律先用地圖空間拆解；最大 zoom 時 2–4 個不同活動 spiderfy，5 個以上不同活動才 Fullscreen。活動數以 distinct event ID 計算，不以原始 marker 數計算；此規則桌機與手機一致。",
}
for old, new in replacements.items():
    decision = replace_once(decision, old, new, 'decision update')
DECISION.write_text(decision.rstrip() + '\n', encoding='utf-8')

# ---------------------------------------------------------------------------
# Regression updates
# ---------------------------------------------------------------------------
followup = FOLLOWUP.read_text(encoding='utf-8')
old = '''# Destination cluster policy: canonical cultural parks fullscreen, mixed ordinary clusters still zoom/spiderfy.
for name in ('華山1914文化創意產業園區','松山文創園區','高雄市駁二藝術特區','駁二藝術特區','花蓮文化創意產業園區','嘉義文化創意產業園區'):
    assert name in text
assert 'function destinationVenueGroup(location)' in text
assert 'function destinationClusterInfo(items)' in text
cluster=text[text.index('function handleClusterActivate'):text.index("cluster.on('clusterclick'")]
assert 'destinationClusterInfo(items)' in cluster
assert "openActivityPicker({mode:'cluster'" in cluster
assert 'clusterLayer.zoomToBounds()' in cluster and 'clusterLayer.spiderfy()' in cluster
assert 'venueIds.size===1' not in cluster
'''
new = '''# Cluster policy: spatial zoom first; at max zoom 2-4 spiderfy and 5+ distinct events fullscreen.
assert 'DESTINATION_VENUE_GROUPS' not in text
assert 'function destinationVenueGroup(location)' not in text
assert 'function destinationClusterInfo(items)' not in text
picker=text[text.index('function clusterPickerItems'):text.index('function handleClusterActivate')]
assert 'const seenEvents=new Set()' in picker and 'seenEvents.has(group.id)' in picker
cluster=text[text.index('function handleClusterActivate'):text.index("cluster.on('clusterclick'")]
assert "if(map.getZoom()<map.getMaxZoom()){clusterLayer.zoomToBounds();return}" in cluster
assert "if(items.length>4){openActivityPicker({mode:'cluster',items,title:'這個地點的活動'});return}" in cluster
assert 'clusterLayer.spiderfy();' in cluster
assert 'MOBILE_QUERY' not in cluster
'''
followup = replace_once(followup, old, new, 'followup cluster regression')
followup = replace_once(
    followup,
    "for phrase in ('Desktop Map controls / Destination cluster / City viewport 微調','Map popup 不再提供跨活動 carousel','Desktop 選定縣市 Filter 後立即 `fitCityView(city)`'):",
    "for phrase in ('Desktop Map controls / Cluster threshold / City viewport 微調','Map popup 不再提供跨活動 carousel','Desktop 選定縣市 Filter 後立即 `fitCityView(city)`'):",
    'followup decision heading',
)
FOLLOWUP.write_text(followup, encoding='utf-8')

polish = POLISH.read_text(encoding='utf-8')
old = '''# 1. Desktop cluster picker is destination-aware; ordinary clusters still zoom/spiderfy.
cluster=text[text.index('function handleClusterActivate'):text.index("cluster.on('clusterclick'")]
assert "destinationClusterInfo(items)" in cluster
assert "openActivityPicker({mode:'cluster'" in cluster
assert 'clusterLayer.zoomToBounds()' in cluster
assert 'clusterLayer.spiderfy()' in cluster
assert "venueIds.size===1" not in cluster
'''
new = '''# 1. Cluster picker is max-zoom threshold based; ordinary clusters keep zoom/spiderfy.
cluster=text[text.index('function handleClusterActivate'):text.index("cluster.on('clusterclick'")]
assert "if(map.getZoom()<map.getMaxZoom()){clusterLayer.zoomToBounds();return}" in cluster
assert "if(items.length>4)" in cluster
assert "openActivityPicker({mode:'cluster'" in cluster
assert 'clusterLayer.spiderfy()' in cluster
assert 'destinationClusterInfo' not in cluster
'''
polish = replace_once(polish, old, new, 'polish cluster regression')
POLISH.write_text(polish, encoding='utf-8')

map_ux = MAP_UX.read_text(encoding='utf-8')
old = '''        cluster_handler = self.html[self.html.index("function handleClusterActivate"):self.html.index("cluster.on('clusterclick'")]
        self.assertIn("destinationClusterInfo(items)", cluster_handler)
        self.assertNotIn("venueIds.size===1", cluster_handler)
        self.assertIn("if(destination)", cluster_handler)
        self.assertIn("clusterLayer.zoomToBounds()", cluster_handler)
        self.assertIn("clusterLayer.spiderfy()", cluster_handler)
'''
new = '''        cluster_handler = self.html[self.html.index("function handleClusterActivate"):self.html.index("cluster.on('clusterclick'")]
        self.assertIn("if(map.getZoom()<map.getMaxZoom()){clusterLayer.zoomToBounds();return}", cluster_handler)
        self.assertIn("if(items.length>4)", cluster_handler)
        self.assertIn("openActivityPicker({mode:'cluster'", cluster_handler)
        self.assertIn("clusterLayer.spiderfy()", cluster_handler)
        self.assertNotIn("destinationClusterInfo", cluster_handler)
'''
map_ux = replace_once(map_ux, old, new, 'map ux cluster regression')
MAP_UX.write_text(map_ux, encoding='utf-8')

print('cluster threshold patch applied')
