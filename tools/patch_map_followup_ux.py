from pathlib import Path

ROOT = Path('.')
HTML = ROOT / 'public' / 'taiwan-exhibition-map.html'
DECISION = ROOT / 'decision.md'
MAP_TEST = ROOT / 'backend' / '_test_map_ux.py'
POLISH_TEST = ROOT / 'backend' / '_test_map_exploration_polish.py'
NEW_TEST = ROOT / 'backend' / '_test_map_followup_ux.py'

text = HTML.read_text(encoding='utf-8')


def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 match, found {count}')
    text = text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# 1) Desktop navigation controls + larger non-scrolling map card.
# ---------------------------------------------------------------------------
replace_once(
    ".map-tools{position:absolute;z-index:1000;top:66px;right:14px;display:flex;flex-direction:column;align-items:flex-end;gap:8px}\n.map-tool{display:grid;min-width:44px;height:44px;place-items:center;border:1px solid rgba(25,31,42,.18);border-radius:13px;background:rgba(255,255,255,.94);color:#1b2430;box-shadow:0 7px 22px rgba(0,0,0,.16);cursor:pointer}\n",
    ".map-tools{position:absolute;z-index:1000;top:66px;right:14px;display:flex;flex-direction:column;align-items:flex-end;gap:8px}\n.map-nav-stack{display:flex;flex-direction:column;align-items:center;gap:7px}\n.map-tool{display:grid;min-width:44px;height:44px;place-items:center;border:1px solid rgba(25,31,42,.18);border-radius:13px;background:rgba(255,255,255,.94);color:#1b2430;box-shadow:0 7px 22px rgba(0,0,0,.16);cursor:pointer}\n.map-zoom-tool{font-size:21px;font-weight:700;line-height:1}.leaflet-control-zoom{display:none}\n",
    'desktop map navigation css',
)
replace_once(
    '<div class="map-tools"><button class="map-tool" id="mapHomeButton" type="button" aria-label="回到台灣全圖" title="回到台灣全圖">⌂</button><div class="floating-events" id="floatingEvents" aria-label="多店活動（無單一地址）"></div></div>',
    '<div class="map-tools"><div class="map-nav-stack" aria-label="地圖控制"><button class="map-tool" id="mapHomeButton" type="button" aria-label="回到台灣全圖" title="回到台灣全圖">⌂</button><button class="map-tool map-zoom-tool" id="mapZoomInButton" type="button" aria-label="放大地圖" title="放大地圖">＋</button><button class="map-tool map-zoom-tool" id="mapZoomOutButton" type="button" aria-label="縮小地圖" title="縮小地圖">−</button></div><div class="floating-events" id="floatingEvents" aria-label="多店活動（無單一地址）"></div></div>',
    'desktop map navigation html',
)
replace_once(
    ".desktop-map-card{position:absolute;z-index:1450;left:16px;bottom:18px;width:min(760px,calc(100% - 96px));height:clamp(214px,27dvh,260px);padding:12px;overflow:hidden;border:1px solid var(--line);border-radius:22px;background:rgba(255,250,245,.98);box-shadow:0 20px 58px rgba(54,39,28,.24);opacity:0;pointer-events:none;transform:translateY(calc(100% + 34px));transition:transform .24s cubic-bezier(.2,.82,.2,1),opacity .18s ease;backdrop-filter:blur(14px)}\n.desktop-map-card.show{opacity:1;pointer-events:auto;transform:translateY(0)}\n.desktop-map-card-close{position:absolute;z-index:3;top:7px;right:7px;display:grid;width:38px;height:38px;place-items:center;border:0;border-radius:50%;background:rgba(255,255,255,.88);color:#5b4c43;font-size:20px;cursor:pointer;box-shadow:0 3px 12px rgba(64,47,36,.08)}\n.desktop-map-card-body{height:100%;padding-right:34px}\n.desktop-map-card .mobile-card{display:flex;height:100%;gap:15px;overflow:hidden}.desktop-map-card .mobile-card-kv{width:42%;height:100%;flex:none}.desktop-map-card .mobile-card-kv .media-frame{height:100%;border-radius:15px}.desktop-map-card .mobile-card-info{display:flex;min-width:0;flex:1;flex-direction:column;gap:7px;overflow-y:auto;padding:2px 2px 2px 0}.desktop-map-card .mobile-card-info h2{margin:0;font-size:18px;line-height:1.32;padding-right:8px}.desktop-map-card .mobile-card-date{font-size:12.5px;font-weight:700;color:var(--text)}\n",
    ".desktop-map-card{position:absolute;z-index:1450;left:50%;bottom:18px;width:min(960px,calc(100% - 32px));min-height:286px;height:auto;padding:12px;overflow:hidden;border:1px solid var(--line);border-radius:22px;background:rgba(255,250,245,.98);box-shadow:0 20px 58px rgba(54,39,28,.24);opacity:0;pointer-events:none;transform:translate(-50%,calc(100% + 34px));transition:transform .24s cubic-bezier(.2,.82,.2,1),opacity .18s ease;backdrop-filter:blur(14px)}\n.desktop-map-card.show{opacity:1;pointer-events:auto;transform:translate(-50%,0)}\n.desktop-map-card-close{position:absolute;z-index:3;top:7px;right:7px;display:grid;width:38px;height:38px;place-items:center;border:0;border-radius:50%;background:rgba(255,255,255,.88);color:#5b4c43;font-size:20px;cursor:pointer;box-shadow:0 3px 12px rgba(64,47,36,.08)}\n.desktop-map-card-body{min-height:262px;padding-right:34px}\n.desktop-map-card .mobile-card{display:flex;min-height:262px;gap:15px;overflow:hidden}.desktop-map-card .mobile-card-kv{width:40%;min-height:262px;flex:none}.desktop-map-card .mobile-card-kv .media-frame{height:100%;min-height:262px;border-radius:15px}.desktop-map-card .mobile-card-info{display:flex;min-width:0;min-height:262px;flex:1;flex-direction:column;gap:7px;overflow:visible;padding:2px 2px 2px 0}.desktop-map-card .mobile-card-info h2{margin:0;font-size:18px;line-height:1.32;padding-right:8px}.desktop-map-card .mobile-card-date{font-size:12.5px;font-weight:700;color:var(--text)}\n",
    'desktop map card geometry',
)
replace_once(
    '@media(max-width:760px){.desktop-map-card{display:none!important}.filter-calendar{margin-right:3px;margin-left:3px}.filter-calendar-day{height:42px}.filter-calendar-spacer{height:42px}.mobile-card-info .map-card-context{margin-top:1px}.mobile-card-info .map-card-location{font-size:12px}}',
    '@media(max-width:760px){.desktop-map-card{display:none!important}.map-zoom-tool{display:none}.leaflet-control-zoom{display:block}.filter-calendar{margin-right:3px;margin-left:3px}.filter-calendar-day{height:42px}.filter-calendar-spacer{height:42px}.mobile-card-info .map-card-context{margin-top:1px}.mobile-card-info .map-card-location{font-size:12px}}',
    'mobile keeps native zoom control',
)

# Remove user-facing cross-activity carousel/navigation while retaining Nearby's internal distance list.
old_popup_nav = """function popupNavigationHtml(){
  if(popupCards.length<=1)return '';
  return '<div class=\"popup-nav\"><button class=\"popup-arrow\" type=\"button\" data-popup-move=\"-1\" aria-label=\"上一個活動\" '+(popupCardIndex===0?'disabled':'')+'>‹</button>'
    +'<span class=\"popup-position\">'+(popupCardIndex+1)+' / '+popupCards.length+'</span>'
    +'<button class=\"popup-arrow\" type=\"button\" data-popup-move=\"1\" aria-label=\"下一個活動\" '+(popupCardIndex===popupCards.length-1?'disabled':'')+'>›</button></div>';
}
"""
replace_once(old_popup_nav, '', 'remove popup navigation renderer')
replace_once(
    "+nearbyCtaHtml(location)+actionHtml(group)+popupNavigationHtml()+'</div></div>';",
    "+nearbyCtaHtml(location)+actionHtml(group)+'</div></div>';",
    'remove legacy dialog popup navigation',
)
replace_once(
    "+actionHtml(group)+nearbyCtaHtml(location)+popupNavigationHtml()\n    +'</div></article>';",
    "+actionHtml(group)+nearbyCtaHtml(location)\n    +'</div></article>';",
    'remove compact popup navigation',
)
old_move = """function movePopupCard(delta){
  const next=popupCardIndex+delta;
  if(next<0||next>=popupCards.length)return;
  const prev=popupCards[popupCardIndex].location;
  popupCardIndex=next;
  const cur=popupCards[popupCardIndex].location;
  if(MOBILE_QUERY.matches)renderMobileCard(false);
  selectLocation(cur.id,{openPopup:!MOBILE_QUERY.matches,revealMarker:true,recenter:prev.lat!==cur.lat||prev.lng!==cur.lng,updateHistory:true,preservePopupCards:true});
}
"""
replace_once(old_move, '', 'remove cross-activity move function')
replace_once("  const move=event.target.closest('[data-popup-move]');if(move)movePopupCard(+move.dataset.popupMove);\n", '', 'remove dialog move handler')
replace_once("  const move=event.target.closest('[data-popup-move]');if(move)movePopupCard(+move.dataset.popupMove);\n", '', 'remove desktop dock move handler')
old_mobile_body = """(function(){
  const body=document.getElementById('mobileVenueBody');
  body.addEventListener('click',event=>{
    const share=event.target.closest('[data-share]');if(share){shareEvent(share.dataset.share)}
    const nearby=event.target.closest('[data-nearby-location]');if(nearby)openNearbyPicker(nearby.dataset.nearbyLocation);
    const move=event.target.closest('[data-popup-move]');if(move)movePopupCard(+move.dataset.popupMove);
  });
  let startX=0,startY=0,swiping=false;
  body.addEventListener('touchstart',event=>{const t=event.changedTouches[0];startX=t.clientX;startY=t.clientY;swiping=true},{passive:true});
  body.addEventListener('touchend',event=>{
    if(!swiping) return; swiping=false;
    const t=event.changedTouches[0],dx=t.clientX-startX,dy=t.clientY-startY;
    if(Math.abs(dx)>45&&Math.abs(dx)>Math.abs(dy)*1.4) movePopupCard(dx<0?1:-1);
  },{passive:true});
})();
"""
new_mobile_body = """document.getElementById('mobileVenueBody').addEventListener('click',event=>{
  const share=event.target.closest('[data-share]');if(share){shareEvent(share.dataset.share)}
  const nearby=event.target.closest('[data-nearby-location]');if(nearby)openNearbyPicker(nearby.dataset.nearbyLocation);
});
"""
replace_once(old_mobile_body, new_mobile_body, 'remove mobile cross-activity swipe')
old_keyboard = """document.addEventListener('keydown',event=>{
  if((event.key==='ArrowLeft'||event.key==='ArrowRight')&&activeDialogMode==='event'&&!document.getElementById('activityPickerOverlay').classList.contains('show')&&!event.target.matches('input,textarea,select,[contenteditable=\"true\"]')){
    event.preventDefault();movePopupCard(event.key==='ArrowLeft'?-1:1);return;
  }
  if(event.key!=='Escape')return;
"""
new_keyboard = """document.addEventListener('keydown',event=>{
  if(event.key!=='Escape')return;
"""
replace_once(old_keyboard, new_keyboard, 'remove desktop keyboard carousel')

# Wire the custom desktop zoom buttons without changing Leaflet's mobile zoom control.
replace_once(
    "document.getElementById('mapHomeButton').addEventListener('click',fitTaiwanView);\n",
    "document.getElementById('mapHomeButton').addEventListener('click',fitTaiwanView);\ndocument.getElementById('mapZoomInButton').addEventListener('click',()=>map.zoomIn());\ndocument.getElementById('mapZoomOutButton').addEventListener('click',()=>map.zoomOut());\n",
    'wire custom desktop zoom controls',
)

# ---------------------------------------------------------------------------
# 2) Cultural-park destination clusters: fullscreen only for canonical destinations.
# ---------------------------------------------------------------------------
destination_code = """const DESTINATION_VENUE_GROUPS=[
  {id:'huashan1914',label:'華山1914文化創意產業園區',aliases:['華山1914文化創意產業園區']},
  {id:'songshan-cultural-park',label:'松山文創園區',aliases:['松山文創園區']},
  {id:'pier2',label:'駁二藝術特區',aliases:['高雄市駁二藝術特區','駁二藝術特區']},
  {id:'hualien-cultural-park',label:'花蓮文化創意產業園區',aliases:['花蓮文化創意產業園區']},
  {id:'chiayi-cultural-park',label:'嘉義文化創意產業園區',aliases:['嘉義文化創意產業園區']}
];
function destinationVenueGroup(location){
  const name=normalizeText(location&&location.venueName);
  return DESTINATION_VENUE_GROUPS.find(group=>group.aliases.some(alias=>normalizeText(alias)===name))||null;
}
function destinationClusterInfo(items){
  if(!items.length)return null;
  const groups=items.map(item=>destinationVenueGroup(item.location));
  if(groups.some(group=>!group))return null;
  const ids=new Set(groups.map(group=>group.id));
  if(ids.size!==1)return null;
  const eventIds=new Set(items.map(item=>item.eventId));
  return eventIds.size>1?{group:groups[0],eventIds}:null;
}
"""
replace_once('function clusterPickerItems(clusterLayer){\n', destination_code + 'function clusterPickerItems(clusterLayer){\n', 'insert destination venue config')
old_cluster = """function handleClusterActivate(clusterLayer){
  if(!clusterLayer)return;
  const items=clusterPickerItems(clusterLayer);
  const venueIds=new Set(items.map(item=>item.location.venueId));
  const eventIds=new Set(items.map(item=>item.eventId));
  const sameVenueMultiActivity=!MOBILE_QUERY.matches&&venueIds.size===1&&eventIds.size>1;
  if(sameVenueMultiActivity){openActivityPicker({mode:'cluster',items,title:'這個地點的活動'});return}
  if(map.getZoom()<map.getMaxZoom())clusterLayer.zoomToBounds();
  else clusterLayer.spiderfy();
}
"""
new_cluster = """function handleClusterActivate(clusterLayer){
  if(!clusterLayer)return;
  const items=clusterPickerItems(clusterLayer);
  const destination=!MOBILE_QUERY.matches?destinationClusterInfo(items):null;
  if(destination){openActivityPicker({mode:'cluster',items,title:destination.group.label+'的活動'});return}
  if(map.getZoom()<map.getMaxZoom())clusterLayer.zoomToBounds();
  else clusterLayer.spiderfy();
}
"""
replace_once(old_cluster, new_cluster, 'destination-aware cluster activation')

# ---------------------------------------------------------------------------
# 3) City filter immediately drives map viewport, without touching selection.
# ---------------------------------------------------------------------------
replace_once(
    "  mapView:null,\n  mapHasVisibleView:false\n};",
    "  mapView:null,\n  mapHasVisibleView:false,\n  pendingCityView:null\n};",
    'add pending mobile city viewport',
)
replace_once(
    "  const key=openFilterKey,value=button.dataset.value;uiState.filters[key]=value;closeFilterDetail();renderAll();if(key==='city'&&uiState.exploreView==='results')fitCityView(value);",
    "  const key=openFilterKey,value=button.dataset.value;uiState.filters[key]=value;closeFilterDetail();renderAll();if(key==='city'&&!MOBILE_QUERY.matches){uiState.pendingCityView=null;fitCityView(value)}",
    'desktop city filter viewport',
)
old_mobile_apply = """function applyMobileFilters(){
  uiState.filters={...draftFilters};if(draftClearSort)uiState.discoverSort='default';draftFilters=null;draftClearSort=false;closeMobileFilters(false);renderAll();
  if(uiState.tab==='map') fitCityView(uiState.filters.city);
}
"""
new_mobile_apply = """function applyMobileFilters(){
  const previousCity=uiState.filters.city;
  uiState.filters={...draftFilters};if(draftClearSort)uiState.discoverSort='default';draftFilters=null;draftClearSort=false;closeMobileFilters(false);renderAll();
  if(previousCity!==uiState.filters.city){
    if(uiState.tab==='map'){uiState.pendingCityView=null;fitCityView(uiState.filters.city)}
    else uiState.pendingCityView=uiState.filters.city;
  }
}
"""
replace_once(old_mobile_apply, new_mobile_apply, 'mobile city filter viewport')
replace_once(
    "    if(options.explicitTarget)return;\n    if(uiState.mapHasVisibleView&&uiState.mapView)map.setView(uiState.mapView.center,uiState.mapView.zoom,{animate:false});\n    else{fitTaiwanView();uiState.mapHasVisibleView=true}\n",
    "    if(options.explicitTarget)return;\n    if(uiState.pendingCityView!==null){const city=uiState.pendingCityView;uiState.pendingCityView=null;uiState.mapHasVisibleView=true;fitCityView(city)}\n    else if(uiState.mapHasVisibleView&&uiState.mapView)map.setView(uiState.mapView.center,uiState.mapView.zoom,{animate:false});\n    else{fitTaiwanView();uiState.mapHasVisibleView=true}\n",
    'mobile map pending city priority',
)
replace_once(
    "  if(!MOBILE_QUERY.matches||uiState.tab==='map')fitTaiwanView();\n  else{uiState.mapView=null;uiState.mapHasVisibleView=false}\n",
    "  uiState.pendingCityView=null;\n  if(!MOBILE_QUERY.matches||uiState.tab==='map')fitTaiwanView();\n  else{uiState.mapView=null;uiState.mapHasVisibleView=false}\n",
    'clear pending city on clear all',
)

HTML.write_text(text, encoding='utf-8')

# ---------------------------------------------------------------------------
# Product decision updates.
# ---------------------------------------------------------------------------
decision = DECISION.read_text(encoding='utf-8')
replacements = {
    "- 縮放控制位於右下角。": "- 桌機地圖導航控制固定在右上：Home 鍵下方依序為 `+ / -`；手機保留既有右下 Leaflet 縮放控制。",
    "- 每個活動各自一個 marker；同場館／同座標的多個活動會聚合。桌機 cluster 只有在所有子 marker 都屬於同一 venue/location 且確實有多活動時，才開啟全螢幕 Activity Picker；一般由不同地點組成的 cluster 必須持續 zoom-to-bounds，最大層級再 spiderfy。手機維持 zoom／最大層級 spiderfy。個別 marker 不顯示數字徽章；聚合徽章顯示該處活動數。": "- 每個活動各自一個 marker；同場館／同座標的多個活動會聚合。桌機只有 canonical 大型文化園區 destination cluster（華山、松菸、駁二，以及同類花蓮／嘉義文化創意產業園區）在目前篩選後仍含 2 個以上不同活動時，才直接開啟全螢幕 Activity Picker；一般 cluster 必須持續 zoom-to-bounds，最大層級再 spiderfy。若 broad cluster 同時混入園區外 marker，也先 zoom，不能因其中包含園區就提前滿版。手機維持 zoom／最大層級 spiderfy。個別 marker 不顯示數字徽章；聚合徽章顯示該處活動數。",
    "- 紅框優先代表 Map popup 目前正在觀看的 activity marker；沒有 active selection 時代表最後看過的 marker。同時間只顯示一個主要紅框。Discover、Latest、Search、deep link、marker click、popup swipe／arrow、Cluster Picker、Nearby Picker 與 popstate 必須共用同一 selection pipeline。": "- 紅框優先代表 Map popup 目前正在觀看的 activity marker；沒有 active selection 時代表最後看過的 marker。同時間只顯示一個主要紅框。Discover、Latest、Search、deep link、marker click、Cluster Picker、Nearby Picker 與 popstate 必須共用同一 selection pipeline。Map popup 不提供跨活動 swipe／上一個／下一個 carousel。",
    "- 桌機與手機 popup 共用同一個活動序列：以目前地點為原點，將目前篩選後的有效 map locations 依距離由近到遠排列；灰色左右箭頭不循環，手機 swipe 與箭頭走同一個移動函式，桌機另支援方向鍵。": "- Map popup 不提供跨活動上一個／下一個、`1 / N`、桌機方向鍵切換或手機左右 swipe。使用者要看另一活動時直接點另一 marker；同園區大量活動使用 Fullscreen Activity Picker，附近探索使用 Nearby Picker，大量瀏覽使用 Collection。底層距離清單只可作為 Nearby 計算，不得再暴露成 popup carousel。",
    "- 桌機與手機活動 popup 共用橫式卡片資訊結構：左 KV、右資訊。手機高度約螢幕 1/3；桌機使用地圖內底部 docked card，不使用阻斷探索的全螢幕 event modal。單一活動直接顯示卡片；只有同一 location 的多活動才使用 Fullscreen Activity Picker。": "- 桌機與手機活動 popup 共用橫式卡片資訊結構：左 KV、右資訊。手機高度約螢幕 1/3；桌機使用地圖內底部 docked card，不使用阻斷探索的全螢幕 event modal。桌機 card 應盡量使用地圖寬度、以內容撐高並一次顯示核心資訊，不提供 card 內垂直捲動。大型文化園區 destination 的多活動 cluster 才使用 Fullscreen Activity Picker。",
    "- Popup 的閱讀順序固定為活動名稱 → 目前地點／導航 → 目前 location 日期 → `#縣市`／`#付費狀態` → 官方資訊／分享；IP、主辦與授權商都不進 compact popup。浮動活動仍顯示「請至官方網站查詢地點」。Nearby CTA 與活動序列導覽屬 secondary interaction，可保留在主要資訊之後。": "- Popup 的閱讀順序固定為活動名稱 → 目前地點／導航 → 目前 location 日期 → `#縣市`／`#付費狀態` → 官方資訊／分享；IP、主辦與授權商都不進 compact popup。浮動活動仍顯示「請至官方網站查詢地點」。Nearby CTA 屬 secondary interaction，可保留在主要資訊之後。",
    "- Nearby CTA 與「同地點多活動」的桌機 Cluster／venue selection 共用 Fullscreen Activity Picker。Picker 是 transient UI，不寫入核心 selection 或 history；一般多地點 Cluster 不得開 Picker。Nearby Picker 關閉後保留底層 popup，點卡片後一律關閉 Picker 再呼叫 `selectLocation()`。": "- Nearby CTA 與大型文化園區 destination cluster／需要明確選活動的 venue selection 共用 Fullscreen Activity Picker。Picker 是 transient UI，不寫入核心 selection 或 history；一般多地點 Cluster 不得開 Picker。Nearby Picker 關閉後保留底層 popup，點卡片後一律關閉 Picker再呼叫 `selectLocation()`。",
}
for old, new in replacements.items():
    if decision.count(old) != 1:
        raise RuntimeError('decision mismatch: ' + old[:36])
    decision = decision.replace(old, new, 1)
append = """

## 2026-08-12 — Desktop Map controls / Destination cluster / City viewport 微調

- Desktop `Home / + / -` 為同一組 map navigation utility，固定在右上垂直排列；移開右下縮放控制是為了釋放 bottom card 空間，手機仍保留原生右下縮放。
- Desktop activity card 使用更寬、內容撐高的 bottom dock，一次顯示活動名稱、地點／導航、日期、`#縣市 #付費狀態`、官方資訊／分享與 Nearby；card 本身不得上下捲動。
- Map popup 不再提供跨活動 carousel：沒有 `1 / N`、左右箭頭、桌機方向鍵或手機左右 swipe。另一個活動由 marker、Destination Picker、Nearby Picker 或 Collection 進入。
- 大型文化園區以 UI 靜態 canonical destination config 判定，不寫入每日活動資料。現階段包含華山1914、松山文創園區、駁二藝術特區（含官方／既有別名）、花蓮文化創意產業園區、嘉義文化創意產業園區。只有 cluster 的所有目前可見子活動都屬於同一 destination 且至少有 2 個不同活動時才直接 Fullscreen；混合一般地點的 cluster 先 zoom／spiderfy。
- Desktop 選定縣市 Filter 後立即 `fitCityView(city)`；選全台灣回 `fitTaiwanView()`。此 viewport side effect 不得選活動、開 popup 或改寫 selection。Mobile 若正在 Map 則立即 fit；若仍在 Explore，只記錄 pending city target，下一次使用者自行進 Map 時優先顯示該縣市，不可自動切 tab。
"""
decision = decision.rstrip() + append + '\n'
DECISION.write_text(decision, encoding='utf-8')

# ---------------------------------------------------------------------------
# Update existing regressions to reflect the approved product change.
# ---------------------------------------------------------------------------
map_test = MAP_TEST.read_text(encoding='utf-8')
old = '''    def test_mobile_and_desktop_popup_share_horizontal_card(self):
        # 手機約螢幕 1/3；桌機則是地圖內 bottom dock，不阻斷地圖探索。
        self.assertIn("height:clamp(210px,34dvh,360px)", self.html)
        self.assertIn("height:clamp(214px,27dvh,260px)", self.html)
        self.assertIn("mobile-card-kv", self.html)
        self.assertIn("function mapCardHtml(group,location)", self.html)
        self.assertIn("function buildPopupCards(origin)", self.html)
        # 可左右滑切換，順序以目前地點為原點、依距離由近到遠；
        # 不再另列「其他活動地點」清單。
        self.assertIn("function movePopupCard(delta)", self.html)
        self.assertIn("occurrenceDistance(origin", self.html)
        self.assertIn("a.location.id===origin.id?-1", self.html)
        self.assertNotIn("其他活動地點（", self.html)
'''
new = '''    def test_mobile_and_desktop_popup_share_horizontal_card(self):
        # 手機維持橫式 bottom sheet；桌機 bottom dock 更寬、內容撐高且不內捲。
        self.assertIn("height:clamp(210px,34dvh,360px)", self.html)
        self.assertIn("width:min(960px,calc(100% - 32px))", self.html)
        self.assertIn("min-height:286px", self.html)
        desktop_css = self.html[self.html.index(".desktop-map-card{"):self.html.index("html[data-theme=\"dark\"] .home-filter-close")]
        self.assertNotIn("overflow-y:auto", desktop_css)
        self.assertIn("mobile-card-kv", self.html)
        self.assertIn("function mapCardHtml(group,location)", self.html)
        self.assertIn("function buildPopupCards(origin)", self.html)
        self.assertNotIn("function movePopupCard(delta)", self.html)
        self.assertNotIn('data-popup-move=', self.html)
        self.assertNotIn("其他活動地點（", self.html)
'''
if old not in map_test: raise RuntimeError('map test popup block mismatch')
map_test = map_test.replace(old, new, 1)
map_test = map_test.replace(
    '        self.assertIn("selectLocation(cur.id,{openPopup:!MOBILE_QUERY.matches,revealMarker:true", self.html)\n',
    '        self.assertIn("selectLocation(location.id,{openPopup:true,revealMarker:true,recenter:false,updateHistory:true})", self.html)\n',
    1,
)
old = '''    def test_popup_arrows_share_one_sequence_and_selection_pipeline(self):
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
'''
new = '''    def test_popup_does_not_expose_cross_activity_carousel(self):
        self.assertNotIn("function popupNavigationHtml()", self.html)
        self.assertNotIn('data-popup-move=', self.html)
        self.assertNotIn("function movePopupCard(delta)", self.html)
        self.assertNotIn("movePopupCard(dx<0?1:-1)", self.html)
        self.assertNotIn("event.key==='ArrowLeft'", self.html)
        mobile_wiring = self.html[self.html.index("document.getElementById('mobileVenueBody').addEventListener"):self.html.index("document.getElementById('mobileVenueGrip')")]
        self.assertNotIn("touchstart", mobile_wiring)
        self.assertNotIn("touchend", mobile_wiring)
        # Nearby may still build a distance-sorted list internally, but it is not a popup carousel.
        self.assertIn("function buildNearbyActivities", self.html)
'''
if old not in map_test: raise RuntimeError('map test popup arrows block mismatch')
map_test = map_test.replace(old, new, 1)
old = '''        cluster_handler = self.html[self.html.index("function handleClusterActivate"):self.html.index("cluster.on('clusterclick'")]
        self.assertIn("venueIds.size===1&&eventIds.size>1", cluster_handler)
        self.assertIn("if(sameVenueMultiActivity)", cluster_handler)
        self.assertIn("clusterLayer.zoomToBounds()", cluster_handler)
        self.assertIn("clusterLayer.spiderfy()", cluster_handler)
'''
new = '''        cluster_handler = self.html[self.html.index("function handleClusterActivate"):self.html.index("cluster.on('clusterclick'")]
        self.assertIn("destinationClusterInfo(items)", cluster_handler)
        self.assertNotIn("venueIds.size===1", cluster_handler)
        self.assertIn("if(destination)", cluster_handler)
        self.assertIn("clusterLayer.zoomToBounds()", cluster_handler)
        self.assertIn("clusterLayer.spiderfy()", cluster_handler)
'''
if old not in map_test: raise RuntimeError('map test cluster block mismatch')
map_test = map_test.replace(old, new, 1)
MAP_TEST.write_text(map_test, encoding='utf-8')

polish = POLISH_TEST.read_text(encoding='utf-8')
old = '''# 1. Desktop cluster picker is only for one venue/location with multiple activities.
cluster=text[text.index('function handleClusterActivate'):text.index("cluster.on('clusterclick'")]
assert "venueIds.size===1&&eventIds.size>1" in cluster
assert "openActivityPicker({mode:'cluster'" in cluster
assert 'clusterLayer.zoomToBounds()' in cluster
assert 'clusterLayer.spiderfy()' in cluster
'''
new = '''# 1. Desktop cluster picker is destination-aware; ordinary clusters still zoom/spiderfy.
cluster=text[text.index('function handleClusterActivate'):text.index("cluster.on('clusterclick'")]
assert "destinationClusterInfo(items)" in cluster
assert "openActivityPicker({mode:'cluster'" in cluster
assert 'clusterLayer.zoomToBounds()' in cluster
assert 'clusterLayer.spiderfy()' in cluster
assert "venueIds.size===1" not in cluster
'''
if old not in polish: raise RuntimeError('polish test cluster block mismatch')
polish = polish.replace(old, new, 1)
POLISH_TEST.write_text(polish, encoding='utf-8')

NEW_TEST.write_text(r'''from pathlib import Path

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
desktop=text[text.index("document.getElementById('filterOptions').addEventListener"):text.index("document.getElementById('clearFilters')")]
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
''', encoding='utf-8')

print('map follow-up patch applied')
