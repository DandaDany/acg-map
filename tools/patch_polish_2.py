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
# 1. Cluster = expand unless all children are multiple activities at one venue.
# ---------------------------------------------------------------------------
replace_once(
"""function handleClusterActivate(clusterLayer){
  if(!clusterLayer)return;
  if(MOBILE_QUERY.matches){
    if(map.getZoom()<map.getMaxZoom())clusterLayer.zoomToBounds();
    else clusterLayer.spiderfy();
    return;
  }
  openActivityPicker({mode:'cluster',items:clusterPickerItems(clusterLayer),title:'這個區域的活動'});
}""",
"""function handleClusterActivate(clusterLayer){
  if(!clusterLayer)return;
  const items=clusterPickerItems(clusterLayer);
  const venueIds=new Set(items.map(item=>item.location.venueId));
  const eventIds=new Set(items.map(item=>item.eventId));
  const sameVenueMultiActivity=!MOBILE_QUERY.matches&&venueIds.size===1&&eventIds.size>1;
  if(sameVenueMultiActivity){openActivityPicker({mode:'cluster',items,title:'這個地點的活動'});return}
  if(map.getZoom()<map.getMaxZoom())clusterLayer.zoomToBounds();
  else clusterLayer.spiderfy();
}""",
'cluster progressive expansion')

# Desktop venue search uses the same full-screen picker only when a venue has multiple activities.
sub_once(
 r"function openDesktopVenuePicker\(venueIdValue,updateHistory=true\)\{.*?\n\}",
 """function openDesktopVenuePicker(venueIdValue,updateHistory=true){
  const locations=getFilteredVenueOccurrences(venueIdValue);
  const items=sortDiscoverActivities([...new Set(locations.map(location=>location.event.id))].map(id=>activityGroups.get(id)).filter(Boolean)).map(group=>{
    const location=locations.find(item=>item.event.id===group.id);return location?{eventId:group.id,locationId:location.id,group,location}:null;
  }).filter(Boolean);
  if(!items.length)return;
  if(items.length===1){selectLocation(items[0].locationId,{recenter:false,updateHistory});return}
  openActivityPicker({mode:'cluster',items,title:'這個地點的活動'});
  if(updateHistory)updateEventParam('','replace');
}""",
'desktop venue picker shared full-screen picker',re.S)

# ---------------------------------------------------------------------------
# 5. User location = unmistakable bright red dot with white halo.
# 4. Warm filter close is semantic, not hard-coded black.
# 3. Calendar styles.
# 6/7. Desktop map dock + shared horizontal event card.
# ---------------------------------------------------------------------------
POLISH_CSS=r'''

/* ===== Map exploration polish ===== */
.home-filter-close{display:none;margin-left:auto;border-color:var(--line);background:#fff;color:#51463e;box-shadow:0 4px 14px rgba(70,52,38,.06)}
.home-filter-close:hover,.home-filter-close:focus-visible{border-color:#e7ad9d;background:#fff0eb;color:var(--accent2)}
.filter-calendar{margin:12px 5px 4px;padding-top:14px;border-top:1px solid var(--line)}
.filter-calendar-label{margin:0 4px 9px;color:var(--muted);font-size:11px;font-weight:800;letter-spacing:.4px}
.filter-calendar-head{display:grid;grid-template-columns:38px 1fr 38px;align-items:center;gap:6px;margin-bottom:8px}
.filter-calendar-head strong{text-align:center;font-size:13px}
.filter-calendar-head button{display:grid;width:38px;height:38px;place-items:center;border:0;border-radius:10px;background:transparent;color:var(--text);font-size:20px;cursor:pointer}
.filter-calendar-head button:hover:not(:disabled){background:#f6eee8}.filter-calendar-head button:disabled{opacity:.25;cursor:default}
.filter-calendar-weekdays,.filter-calendar-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:3px}
.filter-calendar-weekdays{margin-bottom:4px}.filter-calendar-weekdays span{padding:4px 0;color:var(--muted);font-size:10px;text-align:center}
.filter-calendar-spacer{height:38px}
.filter-calendar-day{position:relative;display:grid;height:38px;place-items:center;padding:0;border:0;border-radius:10px;background:transparent;color:var(--text);font-size:11.5px;cursor:pointer}
.filter-calendar-day:hover:not(:disabled){background:#f6eee8}.filter-calendar-day:disabled{color:#b9aea5;cursor:default;opacity:.45}
.filter-calendar-day.today{box-shadow:inset 0 0 0 1px #e4c1b5}.filter-calendar-day.selected{background:var(--accent);color:#fff;font-weight:850;box-shadow:none}
.filter-calendar-day i{position:absolute;bottom:4px;width:4px;height:4px;border-radius:50%;background:transparent}.filter-calendar-day.has-events i{background:var(--accent2)}.filter-calendar-day.selected i{background:#fff}
.user-location-dot{background:#ff2d2d;box-shadow:0 0 0 7px rgba(255,45,45,.18),0 3px 13px rgba(111,23,23,.32)}
html[data-theme="dark"] .user-location-dot{border-color:#fff;background:#ff2d2d;box-shadow:0 0 0 7px rgba(255,45,45,.22),0 3px 13px rgba(0,0,0,.42)}
.desktop-map-card{position:absolute;z-index:1450;left:16px;bottom:18px;width:min(760px,calc(100% - 96px));height:clamp(214px,27dvh,260px);padding:12px;overflow:hidden;border:1px solid var(--line);border-radius:22px;background:rgba(255,250,245,.98);box-shadow:0 20px 58px rgba(54,39,28,.24);opacity:0;pointer-events:none;transform:translateY(calc(100% + 34px));transition:transform .24s cubic-bezier(.2,.82,.2,1),opacity .18s ease;backdrop-filter:blur(14px)}
.desktop-map-card.show{opacity:1;pointer-events:auto;transform:translateY(0)}
.desktop-map-card-close{position:absolute;z-index:3;top:7px;right:7px;display:grid;width:38px;height:38px;place-items:center;border:0;border-radius:50%;background:rgba(255,255,255,.88);color:#5b4c43;font-size:20px;cursor:pointer;box-shadow:0 3px 12px rgba(64,47,36,.08)}
.desktop-map-card-body{height:100%;padding-right:34px}
.desktop-map-card .mobile-card{display:flex;height:100%;gap:15px;overflow:hidden}.desktop-map-card .mobile-card-kv{width:42%;height:100%;flex:none}.desktop-map-card .mobile-card-kv .media-frame{height:100%;border-radius:15px}.desktop-map-card .mobile-card-info{display:flex;min-width:0;flex:1;flex-direction:column;gap:7px;overflow-y:auto;padding:2px 2px 2px 0}.desktop-map-card .mobile-card-info h2{margin:0;font-size:18px;line-height:1.32;padding-right:8px}.desktop-map-card .mobile-card-date{font-size:12.5px;font-weight:700;color:var(--text)}
.map-card-location{display:flex;align-items:center;justify-content:space-between;gap:10px;color:var(--muted);font-size:12.5px;line-height:1.45}.map-card-location>span{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.map-card-nav{flex:none;color:var(--accent2);font-size:11.5px;font-weight:800;text-decoration:none}.map-card-nav:hover{text-decoration:underline}
.map-card-context{display:flex;flex-wrap:wrap;gap:8px;color:var(--accent2);font-size:11px;font-weight:800}.map-card-context span{white-space:nowrap}
.desktop-map-card .action-row{margin-top:2px}.desktop-map-card .action-btn{min-height:36px;padding:0 11px;font-size:11.5px}.desktop-map-card .nearby-cta{min-height:34px;margin-top:0;font-size:11.5px}.desktop-map-card .popup-nav{margin-top:auto}
html[data-theme="dark"] .home-filter-close{border-color:#2a3344;background:#171d28;color:#eef2f8;box-shadow:none}html[data-theme="dark"] .home-filter-close:hover{border-color:#465674;background:#232c3d;color:#ff8a74}
html[data-theme="dark"] .filter-calendar{border-color:#2a3344}html[data-theme="dark"] .filter-calendar-head button:hover:not(:disabled),html[data-theme="dark"] .filter-calendar-day:hover:not(:disabled){background:#232c3d}html[data-theme="dark"] .filter-calendar-day:disabled{color:#596579}html[data-theme="dark"] .filter-calendar-day.today{box-shadow:inset 0 0 0 1px #58657a}
html[data-theme="dark"] .desktop-map-card{border-color:#2a3344;background:rgba(21,26,36,.98);box-shadow:0 20px 58px rgba(0,0,0,.5)}html[data-theme="dark"] .desktop-map-card-close{background:rgba(28,35,48,.94);color:#eef2f8}
@media(max-width:760px){.desktop-map-card{display:none!important}.filter-calendar{margin-right:3px;margin-left:3px}.filter-calendar-day{height:42px}.filter-calendar-spacer{height:42px}.mobile-card-info .map-card-context{margin-top:1px}.mobile-card-info .map-card-location{font-size:12px}}
'''
replace_once('\n</style></head>\n',POLISH_CSS+'\n</style></head>\n','append polish CSS')

# New non-modal desktop dock inside the map pane.
replace_once(
'    <div class="map-tools"><button class="map-tool" id="mapHomeButton" type="button" aria-label="回到台灣全圖" title="回到台灣全圖">⌂</button><div class="floating-events" id="floatingEvents" aria-label="多店活動（無單一地址）"></div></div>\n  </section>',
'    <div class="map-tools"><button class="map-tool" id="mapHomeButton" type="button" aria-label="回到台灣全圖" title="回到台灣全圖">⌂</button><div class="floating-events" id="floatingEvents" aria-label="多店活動（無單一地址）"></div></div>\n    <aside class="desktop-map-card" id="desktopMapCard" aria-hidden="true" aria-label="活動資訊"><button class="desktop-map-card-close" id="desktopMapCardClose" type="button" aria-label="關閉活動資訊">×</button><div class="desktop-map-card-body" id="desktopMapCardBody"></div></aside>\n  </section>',
'desktop map dock markup')

# ---------------------------------------------------------------------------
# 7. Shared popup hierarchy: title -> location/nav -> date -> #city/#fee -> actions.
# Remove IP / organizer from compact popup; keep official info + share + Nearby/nav.
# ---------------------------------------------------------------------------
replace_once("官方活動頁 ↗","官方資訊 ↗",'official info label')
sub_once(
 r"function mobileCardHtml\(group,location\)\{.*?\n\}",
 """function popupContextHtml(group,location){
  const tags=[location.city,group.fee].filter(Boolean);return tags.length?'<div class=\"map-card-context\">'+tags.map(value=>'<span>#'+esc(value)+'</span>').join('')+'</div>':'';
}
function mapCardLocationHtml(group,location){
  if(location.noAddress)return '<div class=\"map-card-location\"><span>'+esc(FLOATING_ADDRESS_TEXT)+'</span></div>';
  const label=location.venueName||cleanAddress(location.address)||location.city||'';
  return label?'<div class=\"map-card-location\"><span>'+esc(label)+'</span><a class=\"map-card-nav\" href=\"'+esc(navUrl(location))+'\" target=\"_blank\" rel=\"noopener\">導航 ↗</a></div>':'';
}
function mapCardHtml(group,location){
  return '<article class=\"mobile-card map-event-card\">'
    +'<div class=\"mobile-card-kv\">'+mediaFrameHtml(group.image,group.title,false)+'</div>'
    +'<div class=\"mobile-card-info\"><h2>'+esc(group.title)+'</h2>'
    +mapCardLocationHtml(group,location)
    +'<div class=\"mobile-card-date\">'+esc(locationDateText(location))+'</div>'
    +popupContextHtml(group,location)
    +actionHtml(group)+nearbyCtaHtml(location)+popupNavigationHtml()
    +'</div></article>';
}
function mobileCardHtml(group,location){return mapCardHtml(group,location)}""",
'shared compact popup hierarchy',re.S)

# ---------------------------------------------------------------------------
# 6. Desktop marker/deep-link popup becomes a map-bottom dock; no focus trap/backdrop.
# ---------------------------------------------------------------------------
insert_after="let mapSelectionActive=false;"
if text.count(insert_after)!=1: raise RuntimeError('mapSelectionActive anchor mismatch')
text=text.replace(insert_after,insert_after+"""
function openDesktopMapCard(eventId,historyMode='push',preferredLocationId='',preservePopupCards=false){
  const group=activityGroups.get(eventId);if(!group)return;
  const popupOrigin=primaryLocationFor(group,preferredLocationId);
  if(group.floating){popupCards=[{group,location:popupOrigin}];popupCardIndex=0}else preparePopupCards(popupOrigin,preservePopupCards);
  activeDialogMode='event';dialogReturn=null;uiState.selectedEventId=eventId;
  const body=document.getElementById('desktopMapCardBody');body.innerHTML=mapCardHtml(group,popupOrigin);wireImages(body);
  const card=document.getElementById('desktopMapCard');card.classList.add('show');card.setAttribute('aria-hidden','false');
  if(historyMode)updateEventParam(eventId,historyMode);
}
function closeDesktopMapCard(updateHistory=true){closeActiveMapPopup({clearSelection:true,updateHistory})}
""",1)
sub_once(
 r"function openDesktopEventModal\(eventId,returnTarget=null,historyMode='push',preferredLocationId='',preservePopupCards=false\)\{.*?\n\}",
 """function openDesktopEventModal(eventId,returnTarget=null,historyMode='push',preferredLocationId='',preservePopupCards=false){
  openDesktopMapCard(eventId,historyMode,preferredLocationId,preservePopupCards);
}""",
'desktop event modal delegates to dock',re.S)

replace_once(
"""function closeActiveMapPopup(options={}){
  const settings={clearSelection:true,updateHistory:true,...options};
  const sheet=document.getElementById('mobileVenueSheet');
  sheet.classList.remove('show');sheet.setAttribute('aria-hidden','true');popupCards=[];popupCardIndex=0;
  const overlay=document.getElementById('dialogOverlay');
  overlay.classList.remove('show');overlay.setAttribute('aria-hidden','true');activeDialogMode='';dialogReturn=null;
  if(settings.clearSelection)clearSelection();
  if(settings.updateHistory)updateEventParam('','replace');
}""",
"""function closeActiveMapPopup(options={}){
  const settings={clearSelection:true,updateHistory:true,...options};
  const sheet=document.getElementById('mobileVenueSheet');
  sheet.classList.remove('show');sheet.setAttribute('aria-hidden','true');popupCards=[];popupCardIndex=0;
  const dock=document.getElementById('desktopMapCard');dock.classList.remove('show');dock.setAttribute('aria-hidden','true');document.getElementById('desktopMapCardBody').innerHTML='';
  const overlay=document.getElementById('dialogOverlay');
  overlay.classList.remove('show');overlay.setAttribute('aria-hidden','true');activeDialogMode='';dialogReturn=null;
  if(settings.clearSelection)clearSelection();
  if(settings.updateHistory)updateEventParam('','replace');
}""",
'unified close includes desktop dock')

# Shared popup controls for the desktop dock.
replace_once(
"document.getElementById('dialogClose').addEventListener('click',()=>closeDesktopDialog());",
"""document.getElementById('desktopMapCardClose').addEventListener('click',()=>closeDesktopMapCard());
document.getElementById('desktopMapCardBody').addEventListener('click',event=>{
  const share=event.target.closest('[data-share]');if(share)shareEvent(share.dataset.share);
  const nearby=event.target.closest('[data-nearby-location]');if(nearby)openNearbyPicker(nearby.dataset.nearbyLocation);
  const move=event.target.closest('[data-popup-move]');if(move)movePopupCard(+move.dataset.popupMove);
});
document.getElementById('dialogClose').addEventListener('click',()=>closeDesktopDialog());""",
'desktop dock event wiring')
replace_once(
"""  else if(document.getElementById('dialogOverlay').classList.contains('show'))closeDesktopDialog();
  else if(document.getElementById('mobileFilterOverlay').classList.contains('show'))closeMobileFilters(true);""",
"""  else if(document.getElementById('desktopMapCard').classList.contains('show'))closeDesktopMapCard();
  else if(document.getElementById('dialogOverlay').classList.contains('show'))closeDesktopDialog();
  else if(document.getElementById('mobileFilterOverlay').classList.contains('show'))closeMobileFilters(true);""",
'escape closes desktop dock')

# ---------------------------------------------------------------------------
# Recent collection header + filter stats stay within its seven-day base set.
# ---------------------------------------------------------------------------
replace_once("else if(context==='latest'){title.textContent='最近發現';subtitle.textContent='最近加入 ACG Map 的活動'}",
             "else if(context==='latest'){title.textContent='最近發現';subtitle.textContent='最近 7 天新加入 ACG Map 的活動'}",
             'latest collection subtitle')
replace_once(
"""function updateStat(groups){
  const occurrences=[...venueEventIndex.values()].flat().filter(location=>getFilteredVenueOccurrences(location.venueId).some(item=>item.id===location.id));
  document.getElementById('stat').innerHTML='目前共有 <b>'+groups.length+'</b> 場活動<br>'+new Set(occurrences.map(location=>location.venueId)).size+' 個地點符合條件';
}
function renderAll(){
  const groups=getFilteredActivityGroups();
  if(uiState.exploreView==='home')renderEditorialHome();else if(uiState.exploreView==='collection')renderCollection();
  renderMapMarkers();renderFloatingEvents();updateFilterUI();updateMarkerToggles();updateStat(groups);updateExploreViewUI();
}""",
"""function filterSummaryGroups(){
  if(uiState.exploreView==='collection'&&uiState.collectionContext==='latest')return getLatestActivityGroups();
  return getFilteredActivityGroups();
}
function updateStat(groups){
  const allowed=new Set(groups.map(group=>group.id));
  const occurrences=[...venueEventIndex.values()].flat().filter(location=>allowed.has(location.event.id)&&occurrenceVisible(location,uiState.filters));
  document.getElementById('stat').innerHTML='目前共有 <b>'+groups.length+'</b> 場活動<br>'+new Set(occurrences.map(location=>location.venueId)).size+' 個地點符合條件';
}
function renderAll(){
  const groups=getFilteredActivityGroups();
  if(uiState.exploreView==='home')renderEditorialHome();else if(uiState.exploreView==='collection')renderCollection();
  renderMapMarkers();renderFloatingEvents();updateFilterUI();updateMarkerToggles();updateStat(filterSummaryGroups());updateExploreViewUI();
}""",
'latest scoped filter summary')

HTML.write_text(text,encoding='utf-8')
