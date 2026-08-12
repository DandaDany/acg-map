from pathlib import Path

HTML = Path('public/taiwan-exhibition-map.html')
DECISION = Path('decision.md')
TEST = Path('backend/_test_discover_intent_home.py')

text = HTML.read_text(encoding='utf-8')


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected exactly 1 match, found {count}')
    text = text.replace(old, new, 1)


# --- CSS: Discover intent chips, desktop map search, marker controls ---
replace_once(
    '.discover-mode{margin-top:10px;width:190px}.discover-mode button{min-height:32px}\n.discover-count{color:var(--muted);font-size:12px}',
    '.discover-mode{margin-top:10px;width:190px}.discover-mode button{min-height:32px}\n'
    '.discover-count{color:var(--muted);font-size:12px}\n'
    '.discover-intents{display:flex;flex:none;gap:8px;overflow-x:auto;padding:10px 14px 0;scrollbar-width:none}\n'
    '.discover-intents::-webkit-scrollbar{display:none}\n'
    '.discover-intent{display:inline-flex;min-height:38px;flex:none;align-items:center;gap:6px;padding:0 12px;border:1px solid #364157;border-radius:999px;background:#121925;color:#c7d0dd;font-size:12px;font-weight:750;white-space:nowrap;cursor:pointer}\n'
    '.discover-intent:hover{border-color:#56647d;background:#172131}.discover-intent.active{border-color:#b53b67;background:#321725;color:#ffd7e5}\n'
    '.discover-intent.sort.active{border-color:#3b6fa8;background:#152b45;color:#d6e9ff}.discover-intent:disabled{opacity:.55;cursor:progress}\n'
    '.intent-count{display:inline-grid;min-width:20px;height:20px;place-items:center;padding:0 5px;border-radius:999px;background:rgba(255,255,255,.08);font-size:10px}',
    'intent chip CSS'
)
replace_once(
    '.map-tools{position:absolute;z-index:1000;top:14px;right:14px;display:flex;flex-direction:column;align-items:flex-end;gap:8px}',
    '.desktop-map-search{position:absolute;z-index:1100;top:14px;left:14px;width:min(430px,calc(100% - 220px))}.desktop-map-search .searchbox{box-shadow:0 7px 22px rgba(0,0,0,.18)}\n'
    '.map-tools{position:absolute;z-index:1000;top:66px;right:14px;display:flex;flex-direction:column;align-items:flex-end;gap:8px}',
    'desktop map search CSS'
)
replace_once(
    '.map-marker-toggle{position:absolute;z-index:1000;top:14px;left:50%;width:160px;transform:translateX(-50%);background:rgba(16,22,32,.94);box-shadow:0 7px 22px rgba(0,0,0,.22)}',
    '.map-marker-toggle{position:absolute;z-index:1000;top:14px;right:14px;width:160px;background:rgba(16,22,32,.94);box-shadow:0 7px 22px rgba(0,0,0,.22)}',
    'desktop marker toggle placement'
)
replace_once(
    '  .map-tools{top:66px;right:10px}\n  .map-marker-toggle{top:10px;width:148px}',
    '  .desktop-map-search{display:none}\n  .discover-intents{padding:9px 12px 0}\n  .map-tools{top:66px;right:10px}\n  .map-marker-toggle{top:10px;right:auto;left:50%;width:148px;transform:translateX(-50%)}',
    'mobile control placement'
)

# --- Markup: move desktop search to map; add quick intents ---
desktop_search = '''    <div class="search-shell">
      <div class="searchbox">
        <svg viewBox="0 0 24 24" fill="none" stroke="#98a6ba" stroke-width="2" width="17" height="17" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>
        <input id="q" placeholder="搜尋活動、作品、主辦或場館…" aria-label="搜尋活動、作品、主辦或場館" role="combobox" aria-autocomplete="list" aria-controls="searchSuggestions" aria-expanded="false">
      </div>
      <div class="search-suggestions" id="searchSuggestions" role="listbox"></div>
    </div>
'''
replace_once(desktop_search, '', 'remove desktop search from filter pane')
replace_once(
    '    <header class="discover-head"><div><h1>Discover</h1><p>正在進行與即將開始的 ACG 活動</p><div class="segmented discover-mode" id="discoverMode" aria-label="Discover 清單模式"><button type="button" data-discover-mode="discover" class="active">Discover</button><button type="button" data-discover-mode="latest">Latest</button></div></div><span class="discover-count" id="discoverCount"></span></header>\n    <div class="discover-list" id="discoverList"></div>',
    '    <header class="discover-head"><div><h1>Discover</h1><p>正在進行與即將開始的 ACG 活動</p><div class="segmented discover-mode" id="discoverMode" aria-label="Discover 清單模式"><button type="button" data-discover-mode="discover" class="active">Discover</button><button type="button" data-discover-mode="latest">Latest</button></div></div><span class="discover-count" id="discoverCount"></span></header>\n'
    '    <div class="discover-intents" id="discoverIntents" aria-label="快速探索">\n'
    '      <button class="discover-intent" type="button" data-discover-time="today" aria-pressed="false"><span>今天</span><span class="intent-count" id="todayIntentCount">0</span></button>\n'
    '      <button class="discover-intent" type="button" data-discover-time="weekend" aria-pressed="false"><span id="weekendIntentLabel">週末</span><span class="intent-count" id="weekendIntentCount">0</span></button>\n'
    '      <button class="discover-intent sort" type="button" data-discover-sort="distance" aria-pressed="false">⌖ 離我最近</button>\n'
    '    </div>\n'
    '    <div class="discover-list" id="discoverList"></div>',
    'insert Discover intent chips'
)
map_search = desktop_search.replace('class="search-shell"', 'class="search-shell desktop-map-search"', 1)
replace_once(
    '  <section class="map-pane" id="mapPane" aria-label="活動地圖">\n    <div id="map"></div>\n    <div class="segmented map-marker-toggle marker-toggle" aria-label="地圖 Marker 顯示模式">',
    '  <section class="map-pane" id="mapPane" aria-label="活動地圖">\n    <div id="map"></div>\n' + map_search + '    <div class="segmented map-marker-toggle marker-toggle" aria-label="地圖 Marker 顯示模式">',
    'move desktop search above map'
)

# --- State and time filter SSOT ---
replace_once(
    "  filters:{city:'all',time:'all',form:'all',fee:'all',multi:'all'},\n  markerMode:'pin',",
    "  filters:{city:'all',time:'all',form:'all',fee:'all',multi:'all'},\n  discoverSort:'default',\n  userLocation:null,\n  markerMode:'pin',",
    'discover sort state'
)
replace_once(
    "  time:{title:'時間',defaultLabel:'全部時間',options:[\n    {value:'all',label:'全部時間'},{value:'ongoing',label:'進行中'},\n    {value:'upcoming',label:'即將開始'},{value:'ending',label:'即將結束'}]},",
    "  time:{title:'時間',defaultLabel:'全部時間',options:[\n    {value:'all',label:'全部時間'},{value:'today',label:'今天'},{value:'weekend',label:'本週末'},\n    {value:'ongoing',label:'進行中'},{value:'upcoming',label:'即將開始'},{value:'ending',label:'即將結束'}]},",
    'time filter presets'
)
replace_once(
    "function groupMatchesFilters(group,filters,ignoreKey){\n  if(ignoreKey!=='city'&&filters.city!=='all'&&!group.locations.some(location=>location.city===filters.city)) return false;\n  if(ignoreKey!=='time'&&filters.time!=='all'&&!group.locations.some(location=>location.status.kind===filters.time||(filters.time==='ongoing'&&location.status.kind==='ending'))) return false;\n  if(ignoreKey!=='form'&&filters.form!=='all'&&group.form!==filters.form) return false;\n  if(ignoreKey!=='fee'&&filters.fee!=='all'&&group.fee!==filters.fee) return false;\n  if(ignoreKey!=='multi'&&filters.multi!=='all'&&group.multiFilter!==filters.multi) return false;\n  return true;\n}",
    "function groupMatchesFilters(group,filters,ignoreKey){\n  if(ignoreKey!=='city'&&filters.city!=='all'&&!group.locations.some(location=>location.city===filters.city)) return false;\n  if(ignoreKey!=='time'&&filters.time!=='all'&&!group.locations.some(location=>locationMatchesTimeFilter(location,filters.time))) return false;\n  if(ignoreKey!=='form'&&filters.form!=='all'&&group.form!==filters.form) return false;\n  if(ignoreKey!=='fee'&&filters.fee!=='all'&&group.fee!==filters.fee) return false;\n  if(ignoreKey!=='multi'&&filters.multi!=='all'&&group.multiFilter!==filters.multi) return false;\n  return true;\n}",
    'group time filtering'
)
replace_once(
    "function occurrenceVisible(location,filters){\n  if(location.status.kind==='ended') return false;\n  if(filters.city!=='all'&&location.city!==filters.city) return false;\n  if(filters.time!=='all'){\n    const match=location.status.kind===filters.time||(filters.time==='ongoing'&&location.status.kind==='ending');\n    if(!match) return false;\n  }\n  return true;\n}",
    "function occurrenceVisible(location,filters){\n  if(location.status.kind==='ended') return false;\n  if(filters.city!=='all'&&location.city!==filters.city) return false;\n  if(filters.time!=='all'&&!locationMatchesTimeFilter(location,filters.time)) return false;\n  return true;\n}",
    'occurrence time filtering'
)
calendar_anchor = "function calendarDayNumber(value){\n  const match=String(value||'').match(/^(\\d{4})-(\\d{2})-(\\d{2})$/);\n  return match?Date.UTC(+match[1],+match[2]-1,+match[3])/86400000:NaN;\n}\n"
calendar_helpers = calendar_anchor + "function eventCalendarDayNumber(value){return calendarDayNumber(String(value||'').replace(/\\//g,'-'))}\nfunction currentWeekendRange(today=taipeiCalendarToday()){\n  const todayDay=calendarDayNumber(today);\n  const weekday=new Date(todayDay*86400000).getUTCDay();\n  const saturday=todayDay+(weekday===0?-1:6-weekday);\n  return {start:saturday,end:saturday+1};\n}\nfunction locationOverlapsCalendarRange(location,startDay,endDay){\n  const rawStart=eventCalendarDayNumber(location.start),rawEnd=eventCalendarDayNumber(location.end);\n  const start=Number.isFinite(rawStart)?rawStart:rawEnd,end=Number.isFinite(rawEnd)?rawEnd:rawStart;\n  return Number.isFinite(start)&&Number.isFinite(end)&&start<=endDay&&end>=startDay;\n}\nfunction locationMatchesTimeFilter(location,value){\n  if(value==='today'){const day=calendarDayNumber(taipeiCalendarToday());return locationOverlapsCalendarRange(location,day,day)}\n  if(value==='weekend'){const range=currentWeekendRange();return locationOverlapsCalendarRange(location,range.start,range.end)}\n  return location.status.kind===value||(value==='ongoing'&&location.status.kind==='ending');\n}\nfunction formatMonthDay(dayNumber){const date=new Date(dayNumber*86400000);return (date.getUTCMonth()+1)+'/'+date.getUTCDate()}\n"
replace_once(calendar_anchor, calendar_helpers, 'Taipei calendar intent helpers')

# --- Distance sorting helpers and list ordering ---
replace_once(
    "function getLatestActivityGroups(state=uiState){return getFilteredActivityGroups(state).filter(group=>isLatestGroup(group))}\nfunction getDiscoverModeGroups(){return uiState.discoverMode==='latest'?getLatestActivityGroups():getFilteredActivityGroups()}",
    "function getLatestActivityGroups(state=uiState){return getFilteredActivityGroups(state).filter(group=>isLatestGroup(group))}\nfunction sortDiscoverModeGroups(groups){\n  if(uiState.discoverSort!=='distance'||!uiState.userLocation)return groups;\n  return [...groups].sort((a,b)=>(nearestLocationForGroup(a)?.distanceMeters??Infinity)-(nearestLocationForGroup(b)?.distanceMeters??Infinity)||a.title.localeCompare(b.title,'zh-Hant')||a.id.localeCompare(b.id));\n}\nfunction getDiscoverModeGroups(){const groups=uiState.discoverMode==='latest'?getLatestActivityGroups():getFilteredActivityGroups();return sortDiscoverModeGroups(groups)}",
    'Discover distance ordering'
)
replace_once(
    "function formatDistance(distanceMeters){\n  if(distanceMeters<1)return '同地點';\n  if(distanceMeters<1000)return Math.round(distanceMeters)+' 公尺';\n  return (distanceMeters/1000).toFixed(1)+' 公里';\n}\nlet activityPickerMode='';",
    "function formatDistance(distanceMeters){\n  if(distanceMeters<1)return '同地點';\n  if(distanceMeters<1000)return Math.round(distanceMeters)+' 公尺';\n  return (distanceMeters/1000).toFixed(1)+' 公里';\n}\nfunction locationDistanceInfo(location){\n  if(!uiState.userLocation||!location||!Number.isFinite(+location.lat)||!Number.isFinite(+location.lng))return null;\n  const distanceMeters=L.latLng(uiState.userLocation.lat,uiState.userLocation.lng).distanceTo(L.latLng(+location.lat,+location.lng));\n  return {location,distanceMeters};\n}\nfunction nearestLocationForGroup(group){\n  let best=null;\n  group.locations.filter(location=>occurrenceVisible(location,uiState.filters)).forEach(location=>{\n    const info=locationDistanceInfo(location);if(info&&(!best||info.distanceMeters<best.distanceMeters))best=info;\n  });\n  return best;\n}\nfunction requestDistanceSort(button){\n  if(uiState.discoverSort==='distance'){uiState.discoverSort='default';renderAll();return}\n  if(!navigator.geolocation){showToast('此瀏覽器不支援定位功能');return}\n  button.disabled=true;button.setAttribute('aria-busy','true');\n  navigator.geolocation.getCurrentPosition(position=>{\n    button.disabled=false;button.removeAttribute('aria-busy');\n    const lat=Number(position.coords.latitude),lng=Number(position.coords.longitude);\n    if(!Number.isFinite(lat)||!Number.isFinite(lng)){showToast('無法取得目前位置');return}\n    uiState.userLocation={lat,lng};uiState.discoverSort='distance';renderAll();\n  },error=>{\n    button.disabled=false;button.removeAttribute('aria-busy');\n    showToast(error&&error.code===1?'未取得定位權限，請允許瀏覽器使用位置':'定位失敗，請稍後再試');\n  },{enableHighAccuracy:false,timeout:10000,maximumAge:300000});\n}\nlet activityPickerMode='';",
    'distance helpers'
)

# --- Card hierarchy: show distance; nearest multi-store branch becomes the card target ---
old_card = """function eventCardHtml(group,preferredLocation=null){
  const first=preferredLocation||primaryLocationFor(group);
  return '<article class="event-card desktop-clickable" data-event-id="'+esc(group.id)+'" data-location-id="'+esc(first.id)+'">'
    +mediaFrameHtml(group.image,group.title,true)
    +'<div class="card-body">'+tagHtml(group,first.city)+'<h2>'+esc(group.title)+'</h2>'
    +'<div class="desktop-only-summary"><div class="card-summary">'+esc(groupDateText(group))+'</div>'
    +'<div class="card-summary">'+(preferredLocation?esc(first.venueName):(group.locations.length>1?'共 '+group.locations.length+' 個地點':esc(first.venueName)))+'</div>'
    +metadataHtml(group)+'</div>'
    +'<div class="mobile-detail"><div class="card-summary">'+esc(groupDateText(group))+'</div>'
    +'<div class="card-summary">'+esc(preferredLocation?first.venueName:(group.locations.length>1?'共 '+group.locations.length+' 個地點':first.venueName))+'</div></div></div></article>';
}"""
new_card = """function eventCardHtml(group,preferredLocation=null){
  const distanceInfo=uiState.discoverSort==='distance'?(preferredLocation?locationDistanceInfo(preferredLocation):nearestLocationForGroup(group)):null;
  const first=preferredLocation||(distanceInfo&&distanceInfo.location)||primaryLocationFor(group);
  const placeText=preferredLocation?first.venueName:(group.locations.length>1?'共 '+group.locations.length+' 個地點':first.venueName);
  const distanceHtml=distanceInfo?'<div class="card-summary card-distance">⌖ '+esc(formatDistance(distanceInfo.distanceMeters))+(group.locations.length>1&&!preferredLocation?' · 最近分店':'')+'</div>':'';
  return '<article class="event-card desktop-clickable" data-event-id="'+esc(group.id)+'" data-location-id="'+esc(first.id)+'">'
    +mediaFrameHtml(group.image,group.title,true)
    +'<div class="card-body">'+tagHtml(group,first.city)+'<h2>'+esc(group.title)+'</h2>'
    +'<div class="desktop-only-summary"><div class="card-summary">'+esc(groupDateText(group))+'</div>'
    +'<div class="card-summary">'+esc(placeText)+'</div>'+distanceHtml
    +metadataHtml(group)+'</div>'
    +'<div class="mobile-detail"><div class="card-summary">'+esc(groupDateText(group))+'</div>'
    +'<div class="card-summary">'+esc(placeText)+'</div>'+distanceHtml+'</div></div></article>';
}"""
replace_once(old_card, new_card, 'distance-aware event cards')
replace_once(
    "  const entries=multiStoreMode?groups.flatMap(group=>group.locations.filter(location=>occurrenceVisible(location,uiState.filters)).map(location=>({group,location}))):groups.map(group=>({group,location:null}));",
    "  let entries=multiStoreMode?groups.flatMap(group=>group.locations.filter(location=>occurrenceVisible(location,uiState.filters)).map(location=>({group,location}))):groups.map(group=>({group,location:null}));\n  if(multiStoreMode&&uiState.discoverSort==='distance'&&uiState.userLocation)entries.sort((a,b)=>(locationDistanceInfo(a.location)?.distanceMeters??Infinity)-(locationDistanceInfo(b.location)?.distanceMeters??Infinity)||a.group.title.localeCompare(b.group.title,'zh-Hant'));",
    'multi-store distance ordering'
)

# --- Intent UI rendering ---
intent_renderer = """function getIntentCount(value){
  const state={...uiState,filters:{...uiState.filters,time:value}};
  let groups=getFilteredActivityGroups(state);
  if(uiState.discoverMode==='latest')groups=groups.filter(group=>isLatestGroup(group));
  return groups.length;
}
function renderDiscoverIntents(){
  const today=document.querySelector('[data-discover-time="today"]');
  const weekend=document.querySelector('[data-discover-time="weekend"]');
  const nearest=document.querySelector('[data-discover-sort="distance"]');
  document.getElementById('todayIntentCount').textContent=getIntentCount('today');
  document.getElementById('weekendIntentCount').textContent=getIntentCount('weekend');
  const range=currentWeekendRange();document.getElementById('weekendIntentLabel').textContent='週末 '+formatMonthDay(range.start)+'–'+formatMonthDay(range.end);
  [[today,'today'],[weekend,'weekend']].forEach(([button,value])=>{const active=uiState.filters.time===value;button.classList.toggle('active',active);button.setAttribute('aria-pressed',active?'true':'false')});
  const distanceActive=uiState.discoverSort==='distance';nearest.classList.toggle('active',distanceActive);nearest.setAttribute('aria-pressed',distanceActive?'true':'false');
}
"""
replace_once('function popupNavigationHtml(){', intent_renderer + 'function popupNavigationHtml(){', 'intent renderer')

# --- Floating event time semantics ---
replace_once(
    "  if(filters.time!=='all'&&!(group.status.kind===filters.time||(filters.time==='ongoing'&&group.status.kind==='ending'))) return false;",
    "  if(filters.time!=='all'&&!group.locations.some(location=>locationMatchesTimeFilter(location,filters.time))) return false;",
    'floating time semantics'
)

# --- Clear-all and rendering ---
replace_once(
    "function hasActiveFilters(){return Object.values(uiState.filters).some(value=>value!=='all')||!!uiState.query}",
    "function hasActiveFilters(){return Object.values(uiState.filters).some(value=>value!=='all')||!!uiState.query||uiState.discoverSort==='distance'}",
    'active filter state includes sort'
)
replace_once(
    "  uiState.query='';\n  document.getElementById('q').value='';document.getElementById('mq').value='';",
    "  uiState.query='';uiState.discoverSort='default';\n  document.getElementById('q').value='';document.getElementById('mq').value='';",
    'clear distance sort'
)
replace_once(
    "function renderAll(){\n  const groups=getFilteredActivityGroups();\n  renderDiscover(getDiscoverModeGroups());renderMapMarkers();renderFloatingEvents();updateFilterUI();updateMarkerToggles();updateStat(groups);\n}",
    "function renderAll(){\n  const groups=getFilteredActivityGroups();\n  renderDiscover(getDiscoverModeGroups());renderDiscoverIntents();renderMapMarkers();renderFloatingEvents();updateFilterUI();updateMarkerToggles();updateStat(groups);\n}",
    'render intent UI'
)
replace_once(
    "  document.querySelectorAll('[data-discover-mode]').forEach(item=>item.classList.toggle('active',item.dataset.discoverMode===mode));\n  renderDiscover(getDiscoverModeGroups());\n});\ndocument.querySelectorAll('[data-marker-mode]').forEach(button=>button.addEventListener('click',()=>setMarkerMode(button.dataset.markerMode)));",
    "  document.querySelectorAll('[data-discover-mode]').forEach(item=>item.classList.toggle('active',item.dataset.discoverMode===mode));\n  renderDiscover(getDiscoverModeGroups());renderDiscoverIntents();\n});\ndocument.getElementById('discoverIntents').addEventListener('click',event=>{\n  const timeButton=event.target.closest('[data-discover-time]');\n  if(timeButton){const value=timeButton.dataset.discoverTime;uiState.filters.time=uiState.filters.time===value?'all':value;closeFilterDetail();renderAll();return}\n  const sortButton=event.target.closest('[data-discover-sort="distance"]');if(sortButton)requestDistanceSort(sortButton);\n});\ndocument.querySelectorAll('[data-marker-mode]').forEach(button=>button.addEventListener('click',()=>setMarkerMode(button.dataset.markerMode)));",
    'wire Discover intent controls'
)

HTML.write_text(text, encoding='utf-8')

# --- Permanent regression test ---
TEST.write_text(r'''from pathlib import Path

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
''', encoding='utf-8')

# --- Decision record ---
decision = DECISION.read_text(encoding='utf-8')
marker = '## 2026-08-12 — Discover 情境入口與桌機地圖搜尋'
if marker not in decision:
    decision += f'''\n\n{marker}\n\n- Discover / Latest 仍是內容模式，不新增第三種 mode。\n- 「今天」與「本週末」是既有時間 Filter 的正式 preset；兩者共用 `uiState.filters.time`，互斥且同步桌機／手機 Filter。日期以 Asia/Taipei 日曆日判斷。\n- 「離我最近」是 Discover 清單排序，不是半徑 Filter；只在使用者點擊後要求 geolocation，不得自動定位，也不得改 Map viewport。\n- 多店活動在距離排序時以目前條件下最近的可用分店作為卡片目標，仍走既有 `selectLocation()` flow。\n- 桌機搜尋移到地圖上方，圖釘／圖片切換靠右；手機保留頂部搜尋與原本 Map 切換位置。\n- Quick intent 只保留高頻情境（今天／週末／離我最近），完整條件仍由 Filter 負責。\n'''
    DECISION.write_text(decision, encoding='utf-8')

print('patch complete')
