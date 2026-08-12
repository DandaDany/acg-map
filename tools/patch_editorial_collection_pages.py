from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / 'public' / 'taiwan-exhibition-map.html'
DECISION = ROOT / 'decision.md'
EDITORIAL_TEST = ROOT / 'backend' / '_test_editorial_c_home.py'
COLLECTION_TEST = ROOT / 'backend' / '_test_editorial_collection_pages.py'
MAP_TEST = ROOT / 'backend' / '_test_map_ux.py'

text = HTML.read_text(encoding='utf-8')


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 match, found {count}')
    text = text.replace(old, new, 1)


def sub_once(pattern: str, repl: str, label: str, flags=0) -> None:
    global text
    new_text, count = re.subn(pattern, repl, text, count=1, flags=flags)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 regex match, found {count}')
    text = new_text


# ---------------------------------------------------------------------------
# Collection page visual system: same editorial language, more cards, persistent map.
# ---------------------------------------------------------------------------
COLLECTION_CSS = r'''
/* ===== Editorial collection pages ===== */
.desktop-shell.collection-mode{grid-template-columns:minmax(560px,55%) minmax(0,45%)}
.desktop-shell.collection-mode>.filter-pane{display:none}
.desktop-shell.collection-mode>.discover-pane{grid-column:1}
.desktop-shell.collection-mode>.map-pane{grid-column:2}
body.home-filter-open .desktop-shell.collection-mode>.filter-pane{display:flex;position:fixed;z-index:2050;top:0;bottom:0;left:0;width:var(--sidebar);box-shadow:22px 0 60px rgba(55,40,28,.16)}
.collection-panel{min-height:0;flex:1;overflow-y:auto;overscroll-behavior:contain;background:linear-gradient(180deg,#fffaf5 0%,#f8f3ed 100%);scrollbar-gutter:stable}
.collection-panel[hidden]{display:none!important}
.collection-head{display:flex;position:sticky;z-index:31;top:0;align-items:center;gap:12px;padding:18px 24px 16px;border-bottom:1px solid #eadfd5;background:rgba(255,250,245,.95);backdrop-filter:blur(14px)}
.collection-back{display:grid;width:42px;height:42px;flex:0 0 auto;place-items:center;border:1px solid var(--line);border-radius:50%;background:#fff;color:var(--text);font-size:22px;cursor:pointer}
.collection-head-copy{min-width:0;flex:1}.collection-head-copy h1{margin:0;color:var(--text);font-size:24px;font-weight:900;letter-spacing:-.35px}.collection-head-copy p{margin:4px 0 0;color:var(--muted);font-size:11.5px;line-height:1.45}
.collection-head-actions{display:flex;align-items:center;gap:8px}.collection-link,.collection-filter{min-height:38px;padding:0 12px;border:0;border-radius:999px;background:transparent;color:var(--accent2);font-size:12px;font-weight:850;cursor:pointer;white-space:nowrap}.collection-filter{border:1px solid var(--line);background:#fff;color:#51463e}.collection-link:hover{text-decoration:underline}.collection-filter:hover{border-color:#ebb5a6;color:var(--accent2)}
.collection-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;padding:20px 24px 8px}
.collection-card{display:block;min-width:0;padding:0;overflow:hidden;border:1px solid #eadfd5;border-radius:19px;background:#fff;color:var(--text);text-align:left;cursor:pointer;box-shadow:0 7px 24px rgba(70,52,38,.07);transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease}
.collection-card:hover{transform:translateY(-2px);border-color:#eab3a4;box-shadow:0 12px 30px rgba(70,52,38,.12)}
.collection-card-media{display:block;position:relative;overflow:hidden;width:100%;aspect-ratio:4/3;background:#eee5de}.collection-card-media img{display:block;width:100%;height:100%;object-fit:cover}.collection-card-media .home-placeholder{position:absolute}
.collection-card-copy{display:block;padding:14px 15px 16px}.collection-card-title{display:-webkit-box;overflow:hidden;color:var(--text);font-size:15px;font-weight:900;line-height:1.42;-webkit-box-orient:vertical;-webkit-line-clamp:2}.collection-card-meta,.collection-card-place{display:block;margin-top:6px;color:var(--muted);font-size:11.5px;line-height:1.45}.collection-card-distance{color:var(--accent2);font-weight:850}
.collection-empty{margin:20px 24px;padding:34px 20px;border:1px solid #eadfd5;border-radius:20px;background:#fff;color:var(--muted);text-align:center;font-size:13px}.collection-empty[hidden]{display:none!important}
.collection-more-wrap{display:flex;justify-content:center;padding:18px 24px 38px}.collection-load-more{min-height:42px;padding:0 18px;border:1px solid #e2d5ca;border-radius:999px;background:#fff;color:var(--accent2);font-size:12.5px;font-weight:850;cursor:pointer;box-shadow:0 5px 18px rgba(70,52,38,.05)}.collection-load-more:hover{border-color:#e6aa99;box-shadow:0 8px 22px rgba(70,52,38,.09)}.collection-load-more[hidden]{display:none!important}
.home-section-actions{display:flex;align-items:center;gap:12px}

html[data-theme="dark"] .desktop-shell.collection-mode>.discover-pane{background:#0f141d}
html[data-theme="dark"] .collection-panel{background:linear-gradient(180deg,#151a24 0%,#0f141d 100%)}
html[data-theme="dark"] .collection-head{border-color:#2a3344;background:rgba(21,26,36,.96)}
html[data-theme="dark"] .collection-back,html[data-theme="dark"] .collection-filter,html[data-theme="dark"] .collection-card,html[data-theme="dark"] .collection-empty,html[data-theme="dark"] .collection-load-more{border-color:#2a3344;background:#171d28;color:var(--text);box-shadow:0 8px 24px rgba(0,0,0,.18)}
html[data-theme="dark"] .collection-card:hover{border-color:#465674;box-shadow:0 12px 30px rgba(0,0,0,.3)}
html[data-theme="dark"] .collection-card-media{background:#111722}
html[data-theme="dark"] .collection-head-copy h1,html[data-theme="dark"] .collection-card-title{color:#eef2f8}
html[data-theme="dark"] .collection-filter{color:#eef2f8}

@media(max-width:1100px) and (min-width:761px){
  .desktop-shell.collection-mode{grid-template-columns:minmax(500px,58%) minmax(0,42%)}
  .collection-grid{gap:12px;padding-right:20px;padding-left:20px}.collection-head{padding-right:20px;padding-left:20px}
}
@media(max-width:760px){
  .desktop-shell.collection-mode{display:block;min-width:0}.desktop-shell.collection-mode>.filter-pane{display:none}
  .collection-panel{position:fixed;z-index:5;inset:var(--mobile-top) 0 calc(var(--mobile-nav) + env(safe-area-inset-bottom,0px));background:linear-gradient(180deg,#fffaf5 0%,#f8f3ed 100%)}
  .collection-head{top:0;gap:9px;padding:10px 12px}.collection-back{width:40px;height:40px}.collection-head-copy h1{font-size:20px}.collection-head-copy p{font-size:10.5px}.collection-head-actions{gap:2px}.collection-link,.collection-filter{min-height:38px;padding:0 9px;font-size:11.5px}
  .collection-grid{grid-template-columns:1fr;gap:14px;padding:14px 14px 6px}.collection-card{border-radius:18px}.collection-card-media{aspect-ratio:16/10}.collection-card-copy{padding:13px 14px 15px}.collection-card-title{font-size:15px}.collection-card-meta,.collection-card-place{font-size:11.5px}
  .collection-empty{margin:16px 14px}.collection-more-wrap{padding:16px 14px 28px}.collection-load-more{width:100%;max-width:280px}
  html[data-theme="dark"] .collection-panel{background:linear-gradient(180deg,#151a24 0%,#0f141d 100%)}
}
'''
replace_once('</style>', COLLECTION_CSS + '\n</style>', 'append collection CSS')

# ---------------------------------------------------------------------------
# Home CTAs and collection markup.
# ---------------------------------------------------------------------------
replace_once('data-home-action="week-results">查看更多 ›', 'data-home-action="week-collection">查看全部 ›', 'week CTA')
replace_once('data-home-action="latest-results">探索更多 ›', 'data-home-action="latest-collection">探索更多 ›', 'latest CTA')
replace_once(
    '<div class="home-section-head"><h2>附近</h2><button class="home-section-link" id="homeNearbyMap" type="button" data-home-action="nearby-map">看地圖 ›</button></div>',
    '<div class="home-section-head"><h2>附近</h2><div class="home-section-actions"><button class="home-section-link" id="homeNearbyMore" type="button" data-home-action="nearby-collection">查看更多 ›</button><button class="home-section-link" id="homeNearbyMap" type="button" data-home-action="nearby-map">地圖查看 ›</button></div></div>',
    'nearby CTAs',
)

OLD_RESULTS_MARKUP = '''    <header class="discover-head results-head" id="resultsHead" hidden>\n      <button class="results-back" id="resultsBack" type="button" aria-label="返回探索首頁">‹</button>\n      <div class="results-head-copy"><h1 id="resultsTitle">所有活動</h1><p id="resultsSubtitle">依目前條件瀏覽活動</p></div>\n      <span class="discover-count" id="discoverCount"></span>\n    </header>\n    <div class="discover-list" id="discoverList" hidden></div>'''
NEW_COLLECTION_MARKUP = '''    <section class="collection-panel" id="collectionPanel" hidden aria-label="活動集合">\n      <header class="collection-head">\n        <button class="collection-back" id="collectionBack" type="button" aria-label="返回探索首頁">‹</button>\n        <div class="collection-head-copy"><h1 id="collectionTitle">活動</h1><p id="collectionSubtitle"></p></div>\n        <div class="collection-head-actions"><button class="collection-link" id="collectionNearbyMap" type="button" hidden>地圖查看 ›</button><button class="collection-filter" id="collectionFilterButton" type="button">篩選</button></div>\n      </header>\n      <div class="collection-grid" id="collectionGrid"></div>\n      <div class="collection-empty" id="collectionEmpty" hidden></div>\n      <div class="collection-more-wrap"><button class="collection-load-more" id="collectionLoadMore" type="button">載入更多 ↓</button></div>\n    </section>\n    <div class="discover-list" id="discoverList" hidden aria-hidden="true"></div>'''
replace_once(OLD_RESULTS_MARKUP, NEW_COLLECTION_MARKUP, 'collection markup')

# ---------------------------------------------------------------------------
# State: Collection is a content view, not a filter/list/map mode.
# ---------------------------------------------------------------------------
replace_once(
    "  exploreView:'home',\n  resultsContext:'all',\n  resultsPreviousTime:null,\n  homeScrollTop:0,",
    "  exploreView:'home',\n  collectionContext:'all',\n  collectionVisibleCount:0,\n  homeScrollTop:0,",
    'collection state',
)
replace_once('const HOME_NEARBY_MAX_M=20000;', 'const HOME_NEARBY_MAX_M=20000;\nconst COLLECTION_BATCH_DESKTOP=8,COLLECTION_BATCH_MOBILE=6;', 'collection batch constants')

# Nearby teaser keeps exactly three items; Collection uses the full distance-sorted set.
replace_once(
    "  const nearbySection=document.getElementById('homeNearbySection'),nearbyContent=document.getElementById('homeNearbyContent'),nearbyMap=document.getElementById('homeNearbyMap');\n  nearbySection.hidden=false;nearbyMap.hidden=!uiState.userLocation;",
    "  const nearbySection=document.getElementById('homeNearbySection'),nearbyContent=document.getElementById('homeNearbyContent'),nearbyMap=document.getElementById('homeNearbyMap'),nearbyMore=document.getElementById('homeNearbyMore');\n  nearbySection.hidden=false;nearbyMap.hidden=!uiState.userLocation;nearbyMore.hidden=!uiState.userLocation;",
    'nearby CTA visibility',
)

COLLECTION_JS = r'''
function collectionBatchSize(){return MOBILE_QUERY.matches?COLLECTION_BATCH_MOBILE:COLLECTION_BATCH_DESKTOP}
function collectionWeekGroups(){
  const todayDay=calendarDayNumber(taipeiCalendarToday());
  const groups=getFilteredActivityGroups().filter(group=>homeWeekLocations(group,todayDay,todayDay+6).length);
  groups.sort((a,b)=>{const ra=homeEditorialRank(a,todayDay),rb=homeEditorialRank(b,todayDay);return ra[0]-rb[0]||ra[1]-rb[1]||a.title.localeCompare(b.title,'zh-Hant')||a.id.localeCompare(b.id)});
  return groups;
}
function collectionNearbyEntries(){
  if(!uiState.userLocation)return [];
  const entries=[];
  getFilteredActivityGroups().forEach(group=>{const info=nearestLocationForGroup(group);if(info&&info.distanceMeters<=HOME_NEARBY_MAX_M)entries.push({group,location:info.location,distanceMeters:info.distanceMeters})});
  return entries.sort((a,b)=>a.distanceMeters-b.distanceMeters||a.group.title.localeCompare(b.group.title,'zh-Hant')||a.group.id.localeCompare(b.group.id));
}
function collectionGroupEntries(groups,context){
  const multiStoreMode=uiState.filters.multi!=='all';
  const todayDay=calendarDayNumber(taipeiCalendarToday());
  if(multiStoreMode){
    return groups.flatMap(group=>group.locations.filter(location=>occurrenceVisible(location,uiState.filters)&&(context!=='week'||locationOverlapsCalendarRange(location,todayDay,todayDay+6))).map(location=>({group,location,distanceMeters:null})));
  }
  return groups.map(group=>({group,location:homeRepresentativeLocation(group)||primaryLocationFor(group),distanceMeters:null})).filter(entry=>entry.location);
}
function getCollectionEntries(){
  const context=uiState.collectionContext;
  if(context==='nearby')return collectionNearbyEntries();
  if(context==='week')return collectionGroupEntries(collectionWeekGroups(),'week');
  if(context==='latest')return collectionGroupEntries(getLatestActivityGroups(),'latest');
  return collectionGroupEntries(getFilteredActivityGroups(),context);
}
function collectionCardHtml(entry){
  const group=entry.group,location=entry.location;
  const meta=[groupDateText(group),group.form,group.fee].filter(Boolean).join(' · ');
  let place=[location.city,location.venueName].filter(Boolean).join(' · ');
  if(Number.isFinite(entry.distanceMeters))place+=(place?' · ':'')+formatDistance(entry.distanceMeters);
  return '<button class="collection-card collection-event-target" type="button" data-collection-location-id="'+esc(location.id)+'">'
    +homeImageHtml(group,'collection-card-media')
    +'<span class="collection-card-copy"><span class="collection-card-title">'+esc(group.title)+'</span>'
    +(meta?'<span class="collection-card-meta">'+esc(meta)+'</span>':'')
    +(place?'<span class="collection-card-place'+(Number.isFinite(entry.distanceMeters)?' collection-card-distance':'')+'">'+esc(place)+'</span>':'')
    +'</span></button>';
}
function updateCollectionHeader(){
  const title=document.getElementById('collectionTitle'),subtitle=document.getElementById('collectionSubtitle'),mapLink=document.getElementById('collectionNearbyMap');
  const context=uiState.collectionContext;
  if(context==='week'){title.textContent='這週想去哪？';subtitle.textContent='接下來 7 天可以參加的活動'}
  else if(context==='nearby'){title.textContent='附近';subtitle.textContent='依你目前的位置，由近到遠瀏覽活動'}
  else if(context==='latest'){title.textContent='最近發現';subtitle.textContent='最近加入 ACG Map 的活動'}
  else if(context==='search'){title.textContent='搜尋結果';subtitle.textContent=uiState.query?'「'+uiState.query+'」':'輸入作品、活動或地點'}
  else{title.textContent='探索活動';subtitle.textContent='依目前條件瀏覽活動'}
  mapLink.hidden=!(context==='nearby'&&uiState.userLocation);
}
function renderCollection(){
  updateCollectionHeader();
  const entries=getCollectionEntries();
  if(!uiState.collectionVisibleCount)uiState.collectionVisibleCount=collectionBatchSize();
  const shown=entries.slice(0,uiState.collectionVisibleCount);
  const grid=document.getElementById('collectionGrid'),empty=document.getElementById('collectionEmpty'),more=document.getElementById('collectionLoadMore');
  grid.innerHTML=shown.map(collectionCardHtml).join('');
  empty.hidden=!!entries.length;
  if(!entries.length){
    if(uiState.collectionContext==='nearby')empty.textContent='20 公里內目前沒有符合條件的活動。';
    else if(uiState.collectionContext==='latest')empty.textContent='目前篩選條件下沒有最近發現的活動。';
    else if(uiState.collectionContext==='search')empty.textContent='找不到符合搜尋條件的活動。';
    else empty.textContent='目前篩選條件下沒有符合的活動。';
  }
  more.hidden=!entries.length||shown.length>=entries.length;
}
'''
replace_once('function requestHomeLocation(button,onReady=null){', COLLECTION_JS + '\nfunction requestHomeLocation(button,onReady=null){', 'collection rendering functions')

# Replace old Results navigation with Collection navigation.
sub_once(
    r"function updateResultsHeader\(\)\{.*?\nfunction setHomeMarkerHover",
    r'''function updateExploreViewUI(){
  const home=uiState.exploreView==='home',collection=uiState.exploreView==='collection';
  const shell=document.querySelector('.desktop-shell');shell.classList.toggle('home-mode',home);shell.classList.toggle('collection-mode',collection);shell.classList.remove('results-mode');
  document.body.classList.toggle('editorial-home-active',home);
  document.getElementById('editorialHome').hidden=!home;document.getElementById('collectionPanel').hidden=!collection;document.getElementById('discoverList').hidden=true;
  if(collection)updateCollectionHeader();
  requestAnimationFrame(()=>{map.invalidateSize();if(home)document.getElementById('editorialHome').scrollTop=uiState.homeScrollTop||0});
}
function enterCollection(context='all'){
  if(context==='nearby'&&!uiState.userLocation){requestHomeLocation(null,()=>enterCollection('nearby'));return}
  if(uiState.exploreView==='home')uiState.homeScrollTop=document.getElementById('editorialHome').scrollTop;
  uiState.collectionContext=context;uiState.collectionVisibleCount=collectionBatchSize();uiState.exploreView='collection';closeHomeFilterDrawer();
  if(MOBILE_QUERY.matches&&uiState.tab!=='discover')setTab('discover');
  renderAll();
}
function returnEditorialHome(){
  if(uiState.collectionContext==='search'){
    uiState.query='';document.getElementById('q').value='';document.getElementById('mq').value='';hideSearchSuggestions();
  }
  uiState.collectionContext='all';uiState.collectionVisibleCount=0;uiState.exploreView='home';renderAll();
}
function setHomeMarkerHover''',
    'replace Results navigation',
    re.S,
)

replace_once(
    "function renderAll(){\n  const groups=getFilteredActivityGroups();\n  if(uiState.exploreView==='home')renderEditorialHome();else renderDiscover(getDiscoverModeGroups());\n  renderMapMarkers();renderFloatingEvents();updateFilterUI();updateMarkerToggles();updateStat(groups);updateExploreViewUI();\n}",
    "function renderAll(){\n  const groups=getFilteredActivityGroups();\n  if(uiState.exploreView==='home')renderEditorialHome();else if(uiState.exploreView==='collection')renderCollection();\n  renderMapMarkers();renderFloatingEvents();updateFilterUI();updateMarkerToggles();updateStat(groups);updateExploreViewUI();\n}",
    'renderAll collection branch',
)

# Search uses the same image-first Collection template, never the legacy list.
replace_once(
    "      uiState.query=input.value.trim();\n      if(uiState.query&&uiState.exploreView==='home'){uiState.homeScrollTop=document.getElementById('editorialHome').scrollTop;uiState.exploreView='results';uiState.resultsContext='search';uiState.discoverMode='discover';updateExploreViewUI()}\n      renderAll();",
    "      uiState.query=input.value.trim();\n      if(uiState.query){\n        if(uiState.exploreView==='home')enterCollection('search');\n        else{uiState.collectionContext='search';uiState.collectionVisibleCount=collectionBatchSize();renderAll()}\n      }else if(uiState.exploreView==='collection'&&uiState.collectionContext==='search')returnEditorialHome();\n      else renderAll();",
    'search collection route',
)

# Event wiring.
replace_once("document.getElementById('resultsBack').addEventListener('click',returnEditorialHome);", "document.getElementById('collectionBack').addEventListener('click',returnEditorialHome);\ndocument.getElementById('collectionFilterButton').addEventListener('click',openHomeFilterDrawer);\ndocument.getElementById('collectionNearbyMap').addEventListener('click',openHomeNearbyMap);\ndocument.getElementById('collectionLoadMore').addEventListener('click',()=>{uiState.collectionVisibleCount+=collectionBatchSize();renderCollection()});", 'collection controls')
replace_once(
    "    if(action.dataset.homeAction==='week-results')enterResults('week');\n    else if(action.dataset.homeAction==='latest-results')enterResults('latest');\n    else if(action.dataset.homeAction==='nearby-map')openHomeNearbyMap();",
    "    if(action.dataset.homeAction==='week-collection')enterCollection('week');\n    else if(action.dataset.homeAction==='latest-collection')enterCollection('latest');\n    else if(action.dataset.homeAction==='nearby-collection')enterCollection('nearby');\n    else if(action.dataset.homeAction==='nearby-map')openHomeNearbyMap();",
    'home collection actions',
)
replace_once(
    "document.getElementById('editorialHome').addEventListener('pointerout',event=>{const target=event.target.closest('[data-home-location-id]');if(target&&!target.contains(event.relatedTarget))setHomeMarkerHover(target.dataset.homeLocationId,false)});",
    "document.getElementById('editorialHome').addEventListener('pointerout',event=>{const target=event.target.closest('[data-home-location-id]');if(target&&!target.contains(event.relatedTarget))setHomeMarkerHover(target.dataset.homeLocationId,false)});\ndocument.getElementById('collectionPanel').addEventListener('click',event=>{const target=event.target.closest('[data-collection-location-id]');if(target)selectLocation(target.dataset.collectionLocationId,{updateHistory:true})});\ndocument.getElementById('collectionPanel').addEventListener('pointerover',event=>{const target=event.target.closest('[data-collection-location-id]');if(target)setHomeMarkerHover(target.dataset.collectionLocationId,true)});\ndocument.getElementById('collectionPanel').addEventListener('pointerout',event=>{const target=event.target.closest('[data-collection-location-id]');if(target&&!target.contains(event.relatedTarget))setHomeMarkerHover(target.dataset.collectionLocationId,false)});",
    'collection card events',
)

HTML.write_text(text, encoding='utf-8')

# ---------------------------------------------------------------------------
# Decision log: Collection pages preserve the browsing language and reveal tools progressively.
# ---------------------------------------------------------------------------
decision = DECISION.read_text(encoding='utf-8')
decision = decision.replace(
    'Latest 的資料定義保留，並由「最近發現」與其完整 Results view 使用。',
    'Latest 的資料定義保留，並由「最近發現」與其完整 Collection view 使用。',
)
decision = decision.replace(
    '- 「查看更多」進入完整 Results mode，使用既有 Filter/List/Map 架構，並將 `未來 7 天` 作為正式 time filter preset；返回首頁時只撤回這個 route 注入的 time preset，不清除使用者在 Results 中主動修改的其他 Filter。',
    '- 「這週想去哪？」的「查看全部」進入 Weekly Collection：桌機以 2 欄等權 KV cards＋右側 persistent Map 呈現，手機以單欄 image-first cards 呈現；首批直接增加可瀏覽的 KV 數量，之後可用「載入更多」續載。不得因查看全部而切回舊 Filter/List/Map 三欄工具版。',
)
decision = decision.replace(
    '- 「附近」是首頁內容 section，不是 quick-sort pill。未授權時只顯示「使用目前位置」CTA；必須由使用者點擊後才呼叫 geolocation。授權後顯示 20 公里內最近 3 個不同 event，多店活動只取最近 eligible location；點卡片仍走 `selectLocation()`。使用者位置以獨立 marker 顯示；只有點「看地圖」才可主動調整 map viewport。',
    '- 「附近」是首頁內容 section，不是 quick-sort pill。未授權時只顯示「使用目前位置」CTA；必須由使用者點擊後才呼叫 geolocation。授權後首頁顯示 20 公里內最近 3 個不同 event，多店活動只取最近 eligible location；「查看更多」進入距離排序的 Nearby Collection，「地圖查看」才主動調整 map viewport。兩者都沿用同一 location target 與 `selectLocation()`。',
)
decision = decision.replace(
    '- Desktop Home 為 `Editorial content × persistent map` 兩欄；Filter sidebar 在 Home 隱藏，Filter 由 trigger 開啟 drawer。搜尋固定放在右側地圖上方，Marker 圖釘／圖片切換放右上。只有 Results mode 才恢復 Filter / List / Map 三欄工具架構。',
    '- Desktop Home 與 Collection 都維持 `Editorial content × persistent map` 兩欄；Filter sidebar 不常駐，只有使用者主動點「篩選」才以 drawer overlay 開啟。搜尋固定放在右側地圖上方，Marker 圖釘／圖片切換放右上。Collection 不得切回舊三欄工具架構。',
)
decision = decision.replace(
    '- Mobile Home 頂部是 `ACG MAP` brand + search icon + filter icon；底部只有「探索／地圖」。首頁不把 search input 常駐成工具列；搜尋 icon 展開搜尋面板，輸入後進 Results mode。',
    '- Mobile Home 頂部是 `ACG MAP` brand + search icon + filter icon；底部只有「探索／地圖」。首頁不把 search input 常駐成工具列；搜尋 icon 展開搜尋面板，輸入後進 image-first Search Collection。',
)
decision = decision.replace(
    '- Home 與 Results 共用 light editorial consumer-product visual system；Positron 地圖與既有 pin 類型配色不變。Filter facet counts、日期、距離、Map cluster counts 屬功能性資訊，可保留；禁止的是把首頁做成統計儀表板。',
    '- Home 與所有 Collection 共用同一套 light/dark editorial consumer-product visual system；首頁 teaser 可用不對稱 hierarchy，Collection 為方便比較改用規律 grid，但 KV 尺寸不得因「查看更多」反而縮成工具型小縮圖。Positron 地圖與既有 pin 類型配色不變。Filter facet counts、日期、距離、Map cluster counts 屬功能性資訊，可保留；禁止的是把首頁做成統計儀表板。',
)
if 'Collection Page UX' not in decision:
    decision += '''\n\n## 2026-08-12 — Collection Page UX\n\n- 首頁 section CTA 的語意固定：`查看全部／查看更多／探索更多` 代表進入同主題的完整 Collection，必須增加同類內容供瀏覽；不得讓 Filter sidebar 自動出現、不得把 KV 卡縮成舊工具 List，也不得改成不同視覺系統。\n- Weekly／Nearby／Recent Collection 共用同一套 image-first Collection template；桌機 2 欄 cards＋persistent Map，手機單欄 cards。Search results 也使用相同 Collection card system。\n- Collection 首批桌機顯示 8 張、手機顯示 6 張；若仍有內容，底部「載入更多」以同樣卡片規格追加下一批。\n- Filter 與「查看更多」是不同 intent：Filter 只有使用者主動點擊才開 drawer，套用後只改 Collection 內容，不改版型。\n- Nearby 同時提供「查看更多」與「地圖查看」：前者維持內容瀏覽，後者才切換／調整空間視角。\n'''
DECISION.write_text(decision, encoding='utf-8')

# ---------------------------------------------------------------------------
# Tests.
# ---------------------------------------------------------------------------
EDITORIAL_TEST.write_text('''from pathlib import Path\n\nHTML = Path(__file__).resolve().parents[1] / "public" / "taiwan-exhibition-map.html"\nDECISION = Path(__file__).resolve().parents[1] / "decision.md"\ntext = HTML.read_text(encoding="utf-8")\ndecision = DECISION.read_text(encoding="utf-8")\n\n# True C information architecture, not #91 pills.\nassert 'id="editorialHome"' in text\nassert '>這週想去哪？<' in text\nassert '>附近<' in text\nassert '>最近發現<' in text\nassert 'id="discoverIntents"' not in text\nassert 'todayIntentCount' not in text\nassert 'weekendIntentCount' not in text\nassert 'intent-count' not in text\nassert 'id="discoverMode"' not in text\nassert 'data-discover-mode=' not in text\n\n# Week = rolling seven days; Home stays editorial and opens a Collection.\nassert "if(value==='next7')" in text\nassert "day,day+6" in text\nassert 'function homeEditorialRank' in text\nassert 'function pickEditorialDiverse' in text\nassert "safeUrl(group.image,true)&&homeWeekLocations" in text\nassert 'data-home-action="week-collection"' in text\nassert "enterCollection('week')" in text\nassert "uiState.filters.time='next7'" not in text[text.index('function enterCollection'):text.index('function returnEditorialHome')]\n\n# Nearby is opt-in, max 20 km / 3 teaser events, with separate Collection and map actions.\nassert 'const HOME_NEARBY_MAX_M=20000' in text\nassert '使用目前位置' in text\nassert 'navigator.geolocation.getCurrentPosition' in text\nassert '.slice(0,3)' in text\nassert 'data-home-action="nearby-collection"' in text\nassert 'data-home-action="nearby-map"' in text\nrequest_block = text[text.index('function requestHomeLocation'):text.index('function openHomeNearbyMap')]\nassert 'fitBounds' not in request_block and 'flyTo' not in request_block and 'setView' not in request_block\nassert 'function openHomeNearbyMap' in text and 'map.fitBounds' in text[text.index('function openHomeNearbyMap'):text.index('function closeHomeFilterDrawer')]\nassert 'user-location-dot' in text\n\n# Desktop: Home and Collection both preserve editorial content + persistent map.\nassert '.desktop-shell.home-mode{grid-template-columns:minmax(560px,55%) minmax(0,45%)}' in text\nassert '.desktop-shell.collection-mode{grid-template-columns:minmax(560px,55%) minmax(0,45%)}' in text\nassert '.desktop-shell.home-mode>.filter-pane{display:none}' in text\nassert '.desktop-shell.collection-mode>.filter-pane{display:none}' in text\nassert 'id="homeFilterButton"' in text\nassert 'id="collectionFilterButton"' in text\nassert '.desktop-map-search{position:absolute' in text\nassert '.map-marker-toggle{position:absolute;z-index:1000;top:14px;right:14px' in text\nassert 'function setHomeMarkerHover' in text\nassert 'marker.isHovered=hovered' in text\n\n# Mobile keeps image-first browsing and Explore/Map navigation.\nassert '<div class="mobile-brand">ACG MAP</div>' in text\nassert 'id="mobileSearchButton"' in text\nassert 'id="mobileSearchPanel"' in text\nassert '>探索</button>' in text\nassert '>地圖</button>' in text\nassert '.collection-card-media{aspect-ratio:16/10}' in text\n\n# Light/dark editorial system and existing map selection architecture coexist.\nassert '--bg:#f7f3ed' in text\nassert 'html[data-theme="dark"] .collection-panel' in text\nassert 'function selectLocation(locationId,options={})' in text\nassert 'function buildNearbyActivities(originLocation)' in text\nassert 'cluster.zoomToShowLayer(marker' in text\nassert "firstSeen:chooseValue(items,'first_seen')||null" in text\nassert 'Collection Page UX' in decision\nprint('editorial C home UX: PASS')\n''', encoding='utf-8')

COLLECTION_TEST.write_text('''from pathlib import Path\n\nHTML = Path(__file__).resolve().parents[1] / "public" / "taiwan-exhibition-map.html"\ntext = HTML.read_text(encoding="utf-8")\n\n# CTA semantics: more content -> a Collection, not legacy Results mode.\nfor action in ('week-collection', 'nearby-collection', 'latest-collection'):\n    assert f'data-home-action="{action}"' in text\nassert 'data-home-action="week-results"' not in text\nassert 'data-home-action="latest-results"' not in text\nassert 'function enterResults' not in text\nassert "exploreView='results'" not in text\nassert 'resultsContext' not in text\n\n# One Collection template, persistent map, image-first cards.\nassert 'id="collectionPanel"' in text\nassert 'id="collectionGrid"' in text\nassert 'id="collectionLoadMore"' in text\nassert 'class="collection-card collection-event-target"' in text\nassert 'collection-card-media' in text\nassert 'grid-template-columns:repeat(2,minmax(0,1fr))' in text\nassert 'grid-template-columns:1fr' in text\nassert 'COLLECTION_BATCH_DESKTOP=8,COLLECTION_BATCH_MOBILE=6' in text\nassert "uiState.collectionVisibleCount+=collectionBatchSize()" in text\n\n# Collection context has week/latest/nearby/search without changing marker dataset.\nassert "if(context==='nearby')return collectionNearbyEntries()" in text\nassert "if(context==='week')return collectionGroupEntries(collectionWeekGroups(),'week')" in text\nassert "if(context==='latest')return collectionGroupEntries(getLatestActivityGroups(),'latest')" in text\ncollection = text[text.index('function renderCollection'):text.index('function requestHomeLocation')]
assert 'renderMapMarkers' not in collection\nassert 'fitTaiwanView' not in collection\nassert 'fitBounds' not in collection\n\n# Filter is progressive disclosure only; Nearby map is a distinct action.\nassert "document.getElementById('collectionFilterButton').addEventListener('click',openHomeFilterDrawer)" in text\nassert "document.getElementById('collectionNearbyMap').addEventListener('click',openHomeNearbyMap)" in text\nassert 'home-section-actions' in text\n\n# Card interactions preserve the unified map selection pipeline.\nassert "data-collection-location-id" in text\nassert "selectLocation(target.dataset.collectionLocationId,{updateHistory:true})" in text\nassert "setHomeMarkerHover(target.dataset.collectionLocationId,true)" in text\n\n# Search results use Collection cards, not the old Discover list.\nsearch = text[text.index("uiState.query=input.value.trim();"):text.index("input.addEventListener('focus'")]
assert "enterCollection('search')" in search\nassert "collectionContext='search'" in search\nassert 'renderDiscover' not in search\nprint('editorial collection pages: PASS')\n''', encoding='utf-8')

map_test = MAP_TEST.read_text(encoding='utf-8')
map_test = map_test.replace('def test_desktop_home_and_results_shells_exist(self):', 'def test_desktop_home_and_collection_shells_exist(self):')
map_test = map_test.replace('self.assertIn(".desktop-shell.home-mode>.filter-pane{display:none}", self.html)', 'self.assertIn(".desktop-shell.home-mode>.filter-pane{display:none}", self.html)\n        self.assertIn(".desktop-shell.collection-mode{grid-template-columns:minmax(560px,55%) minmax(0,45%)}", self.html)\n        self.assertIn(".desktop-shell.collection-mode>.filter-pane{display:none}", self.html)')
map_test = map_test.replace('data-home-action="latest-results"', 'data-home-action="latest-collection"')
sub_pattern = r'''    def test_latest_results_do_not_change_marker_dataset\(self\):.*?\n    def test_mobile_viewport_only_saves_visible_initialized_map'''
sub_repl = '''    def test_latest_collection_does_not_change_marker_dataset(self):\n        collection = self.html[self.html.index("function getCollectionEntries()"):self.html.index("function collectionCardHtml")]\n        self.assertIn("if(context==='latest')return collectionGroupEntries(getLatestActivityGroups(),'latest')", collection)\n        self.assertNotIn("renderMapMarkers", collection)\n        self.assertNotIn("fitTaiwanView", collection)\n\n    def test_mobile_viewport_only_saves_visible_initialized_map'''
map_test, count = re.subn(sub_pattern, sub_repl, map_test, count=1, flags=re.S)
if count != 1:
    raise RuntimeError(f'map UX latest collection test: expected 1 match, found {count}')
MAP_TEST.write_text(map_test, encoding='utf-8')

print('patched editorial collection pages')
