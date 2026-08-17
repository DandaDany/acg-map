#!/usr/bin/env python3
"""Idempotently apply the dedicated multi-store map control to generated HTML."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MAP_HTML = ROOT / "public" / "taiwan-exhibition-map.html"

CONTROL_HTML = r'''
  <div class="multi-store-control" id="multiStoreControl" hidden>
    <button class="multi-store-trigger" id="multiStoreTrigger" type="button" aria-label="多店活動" aria-expanded="false" aria-controls="multiStoreMenu">
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M7.5 3.5a4 4 0 0 0-4 4c0 3 4 7 4 7s4-4 4-7a4 4 0 0 0-4-4Zm0 5.5A1.5 1.5 0 1 1 7.5 6a1.5 1.5 0 0 1 0 3Zm9-2.5a4 4 0 0 0-4 4c0 3 4 7 4 7s4-4 4-7a4 4 0 0 0-4-4Zm0 5.5a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3ZM9 18.5h6v2H9z"/>
      </svg>
    </button>
    <span class="multi-store-label">多店活動</span>
    <div class="multi-store-menu" id="multiStoreMenu" hidden>
      <div class="multi-store-list" id="multiStoreList"></div>
      <button class="multi-store-collapse" id="multiStoreCollapse" type="button" aria-label="收起多店活動並關閉門市圖釘" title="收起多店活動">↑</button>
    </div>
  </div>'''

CONTROL_CSS = r'''
/* Dedicated multi-store activity map control */
.multi-store-control{position:relative;display:flex;flex-direction:column;align-items:center;pointer-events:auto;min-width:52px}
.multi-store-control[hidden],.multi-store-menu[hidden]{display:none!important}
.multi-store-trigger{width:48px;height:48px;border:1px solid var(--border);border-radius:50%;display:grid;place-items:center;padding:0;background:var(--panel);color:var(--text);box-shadow:var(--shadow);cursor:pointer;transition:transform .16s ease,border-color .16s ease,box-shadow .16s ease}
.multi-store-trigger:hover{transform:translateY(-1px)}
.multi-store-trigger:focus-visible,.multi-store-activity:focus-visible,.multi-store-collapse:focus-visible{outline:3px solid color-mix(in srgb,var(--accent) 32%,transparent);outline-offset:2px}
.multi-store-trigger.active{border-color:var(--accent);box-shadow:0 0 0 2px color-mix(in srgb,var(--accent) 18%,transparent),var(--shadow)}
.multi-store-trigger svg{width:23px;height:23px;fill:currentColor}
.multi-store-label{margin-top:4px;font-size:10px;line-height:1.15;font-weight:700;letter-spacing:.02em;color:var(--muted);white-space:nowrap;text-shadow:0 1px 2px var(--panel)}
.multi-store-menu{position:absolute;right:0;top:calc(100% + 9px);z-index:20;width:58px;display:flex;flex-direction:column;align-items:center;gap:8px;overflow:hidden;padding:2px 3px 3px;background:transparent}
.multi-store-list{min-height:0;width:100%;display:flex;flex-direction:column;align-items:center;gap:9px;overflow-x:hidden;overflow-y:auto;overscroll-behavior:contain;padding:2px 3px 4px;scrollbar-width:none}
.multi-store-list::-webkit-scrollbar{display:none}
.multi-store-activity{position:relative;flex:none;width:46px;height:46px;padding:0;border:0;border-radius:50%;background:transparent;cursor:pointer;transition:transform .12s ease}
.multi-store-activity:hover{transform:scale(1.08)}
.multi-store-activity-face{position:absolute;inset:0;display:grid;place-items:center;overflow:hidden;border:2px solid #fff;border-radius:50%;background:var(--fc,#2b3650);color:#fff;box-shadow:0 7px 22px rgba(0,0,0,.22)}
.multi-store-activity.active .multi-store-activity-face{border-color:var(--accent);box-shadow:0 0 0 2px color-mix(in srgb,var(--accent) 24%,transparent),0 8px 24px rgba(0,0,0,.26)}
.multi-store-activity-face img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.multi-store-activity-glyph{font-size:18px;font-weight:800;line-height:1}
.multi-store-activity-badge{position:absolute;right:-4px;bottom:-4px;min-width:20px;height:20px;padding:0 4px;border:2px solid #fff;border-radius:10px;display:grid;place-items:center;background:var(--text);color:var(--panel);font-size:9px;font-weight:850;line-height:1;box-sizing:border-box}
.multi-store-collapse{flex:none;width:40px;height:40px;border:1px solid var(--border);border-radius:50%;display:grid;place-items:center;padding:0;background:var(--panel);color:var(--text);box-shadow:0 6px 18px rgba(0,0,0,.18);font-size:20px;font-weight:800;line-height:1;cursor:pointer}
.multi-store-collapse:hover{transform:translateY(-1px)}
@media(max-width:760px){.multi-store-control{min-width:48px}.multi-store-trigger{width:44px;height:44px}.multi-store-trigger svg{width:21px;height:21px}.multi-store-label{font-size:10px}.multi-store-menu{width:54px}.multi-store-activity{width:44px;height:44px}.multi-store-collapse{width:38px;height:38px}}
'''

CONTROL_JS = r'''
let multiStoreMenuOpen=false;
let activeMultiStoreEventId=null;

function isMappedMultiStoreGroup(group){
  return !!(group&&!group.floating&&group.multiFilter);
}
function isMultiStoreMapGroup(group){
  return !!(group&&(group.floating||group.multiFilter));
}
function multiStoreGroupVisible(group){
  if(!isMultiStoreMapGroup(group))return false;
  if(group.floating)return floatingVisible(group);
  return group.locations.some(location=>occurrenceVisible(location,uiState.filters)&&Number.isFinite(+location.lat)&&Number.isFinite(+location.lng));
}
function getVisibleMultiStoreGroups(){
  return getFilteredActivityGroups().filter(multiStoreGroupVisible);
}
function multiStorePreferredLocation(group){
  const nearest=nearestLocationForGroup(group);
  if(nearest&&nearest.location)return nearest.location;
  return group.locations.find(location=>occurrenceVisible(location,uiState.filters)&&Number.isFinite(+location.lat)&&Number.isFinite(+location.lng))||primaryLocationFor(group);
}
function fitMultiStoreMenuHeight(){
  if(!multiStoreMenuOpen)return;
  const host=document.getElementById('multiStoreControl');
  const menu=document.getElementById('multiStoreMenu');
  if(!host||!menu||menu.hidden)return;
  requestAnimationFrame(()=>{
    const bottomGap=MOBILE_QUERY.matches?104:80;
    const top=host.getBoundingClientRect().bottom+9;
    menu.style.maxHeight=Math.max(128,window.innerHeight-top-bottomGap)+'px';
  });
}
function normalizeMultiStoreState(){
  if(uiState.filters.multi!=='all')uiState.filters.multi='all';
  const groups=getVisibleMultiStoreGroups();
  if(activeMultiStoreEventId&&!groups.some(group=>group.id===activeMultiStoreEventId)){
    const previous=activeMultiStoreEventId;
    activeMultiStoreEventId=null;
    if(uiState.selectedEventId===previous)closeActiveMapPopup({clearSelection:true,updateHistory:false});
  }
  if(!groups.length)multiStoreMenuOpen=false;
  return groups;
}
function collapseMultiStoreMenu(updateHistory=true){
  const active=activeMultiStoreEventId;
  activeMultiStoreEventId=null;
  multiStoreMenuOpen=false;
  if(active&&uiState.selectedEventId===active)closeActiveMapPopup({clearSelection:true,updateHistory});
  renderMapMarkers();
  renderMultiStoreControl();
}
function toggleMultiStoreEvent(id){
  const group=activityGroups.get(id);
  if(!isMultiStoreMapGroup(group))return;
  const previous=activeMultiStoreEventId;
  if(previous&&previous!==id&&uiState.selectedEventId===previous)closeActiveMapPopup({clearSelection:true,updateHistory:false});
  activeMultiStoreEventId=id;
  multiStoreMenuOpen=true;
  renderMapMarkers();
  renderMultiStoreControl();
  if(group.floating){openFloatingEvent(id,true);return;}
  const location=multiStorePreferredLocation(group);
  if(location)selectLocation(location.id,{openPopup:true,revealMarker:true,recenter:true,updateHistory:true});
}
function renderMultiStoreControl(){
  const host=document.getElementById('multiStoreControl');
  const trigger=document.getElementById('multiStoreTrigger');
  const menu=document.getElementById('multiStoreMenu');
  const list=document.getElementById('multiStoreList');
  const collapse=document.getElementById('multiStoreCollapse');
  if(!host||!trigger||!menu||!list||!collapse)return;
  const groups=getVisibleMultiStoreGroups();
  host.hidden=!groups.length;
  if(!groups.length){menu.hidden=true;return;}
  trigger.classList.toggle('active',!!activeMultiStoreEventId);
  trigger.setAttribute('aria-expanded',multiStoreMenuOpen?'true':'false');
  trigger.onclick=event=>{
    event.stopPropagation();
    if(multiStoreMenuOpen)collapseMultiStoreMenu();
    else{multiStoreMenuOpen=true;renderMultiStoreControl();}
  };
  menu.hidden=!multiStoreMenuOpen;
  list.replaceChildren();
  groups.forEach(group=>{
    const option=document.createElement('button');
    option.type='button';
    option.className='multi-store-activity'+(group.id===activeMultiStoreEventId?' active':'');
    option.dataset.multiStoreId=group.id;
    const mappedCount=group.locations.filter(location=>occurrenceVisible(location,uiState.filters)&&Number.isFinite(+location.lat)&&Number.isFinite(+location.lng)).length;
    option.title=group.title+(group.floating?' · 官方門市查詢':' · '+mappedCount+' 間門市');
    option.setAttribute('aria-label',option.title);
    const face=document.createElement('span');
    face.className='multi-store-activity-face';
    face.style.setProperty('--fc',FLOATING_FORM_COLOR[group.form]||'#2b3650');
    const glyph=document.createElement('span');
    glyph.className='multi-store-activity-glyph';
    glyph.textContent=FLOATING_FORM_GLYPH[group.form]||'⌘';
    face.appendChild(glyph);
    const imageUrl=safeUrl(group.image,true);
    if(imageUrl){
      const image=document.createElement('img');
      image.src=imageUrl;image.alt='';image.loading='lazy';image.decoding='async';
      image.addEventListener('error',()=>image.remove(),{once:true});
      face.appendChild(image);
    }
    const badge=document.createElement('span');
    badge.className='multi-store-activity-badge';
    badge.textContent=group.floating?'官':String(mappedCount);
    option.append(face,badge);
    option.addEventListener('click',event=>{event.stopPropagation();toggleMultiStoreEvent(group.id);});
    list.appendChild(option);
  });
  collapse.onclick=event=>{event.stopPropagation();collapseMultiStoreMenu();};
  if(multiStoreMenuOpen)fitMultiStoreMenuHeight();
}
window.addEventListener('resize',()=>{if(multiStoreMenuOpen)fitMultiStoreMenuHeight()});

function renderFloatingEvents(){
  const host=document.getElementById('floatingEvents');
  if(host)host.replaceChildren();
}
'''

SELECT_SYNC_JS = r'''mapSelectionActive=true;
  const selectedGroup=activityGroups.get(location.event.id);
  const nextMultiStoreEventId=isMappedMultiStoreGroup(selectedGroup)?selectedGroup.id:null;
  if(activeMultiStoreEventId!==nextMultiStoreEventId){
    activeMultiStoreEventId=nextMultiStoreEventId;
    multiStoreMenuOpen=!!nextMultiStoreEventId;
    renderMapMarkers();
    renderMultiStoreControl();
  }
  ensureMapVisible'''


def must_sub(pattern: str, repl: str, text: str, label: str, *, flags=0) -> str:
    updated, count = re.subn(pattern, repl, text, count=1, flags=flags)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one patch target, got {count}")
    return updated


def replace_control_host(html: str) -> str:
    if 'id="multiStoreControl"' in html:
        pattern = r'<div class="multi-store-control" id="multiStoreControl" hidden>.*?<div class="multi-store-menu" id="multiStoreMenu" hidden>.*?</div>\s*</div>'
        return must_sub(pattern, CONTROL_HTML.strip(), html, "replace multi-store host", flags=re.S)
    return must_sub(
        r'(<div\s+class="floating-events"\s+id="floatingEvents"[^>]*></div>)',
        lambda m: m.group(1) + CONTROL_HTML,
        html,
        "insert multi-store host",
    )


def replace_control_css(html: str) -> str:
    if "/* Dedicated multi-store activity map control */" in html:
        return must_sub(
            r'/\* Dedicated multi-store activity map control \*/.*?(?=\n</style>)',
            CONTROL_CSS.strip(),
            html,
            "replace multi-store styles",
            flags=re.S,
        )
    return must_sub(r'</style>', CONTROL_CSS + '\n</style>', html, "insert multi-store styles")


def replace_control_js(html: str) -> str:
    if "let multiStoreMenuOpen=false;" in html:
        return must_sub(
            r'let multiStoreMenuOpen=false;.*?function openFloatingEvent',
            CONTROL_JS.strip() + '\nfunction openFloatingEvent',
            html,
            "replace multi-store logic",
            flags=re.S,
        )
    return must_sub(
        r'function renderFloatingEvents\(\)\{.*?\n\}\nfunction openFloatingEvent',
        CONTROL_JS.strip() + '\nfunction openFloatingEvent',
        html,
        "insert multi-store logic",
        flags=re.S,
    )


def remove_multi_filter_ui(html: str) -> str:
    html, count = re.subn(
        r'\s*<button class="filter-category" type="button" data-filter="multi".*?</button>',
        '',
        html,
        count=1,
        flags=re.S,
    )
    if count not in (0, 1):
        raise RuntimeError("multi filter button: unexpected match count")
    html = html.replace("\n  multi:{title:'多店活動',defaultLabel:'全部多店'}", '')
    return html


def apply_patch(html: str) -> str:
    html = remove_multi_filter_ui(html)
    html = replace_control_host(html)
    html = replace_control_css(html)
    html = replace_control_js(html)

    clean_marker = "const locations=getFilteredVenueOccurrences(venue._id);"
    gated_marker = "const locations=getFilteredVenueOccurrences(venue._id).filter(location=>{const group=activityGroups.get(location.event.id);return !isMultiStoreMapGroup(group)||group.id===activeMultiStoreEventId;});"
    if gated_marker not in html:
        if clean_marker not in html:
            raise RuntimeError("marker visibility gate: target not found")
        html = html.replace(clean_marker, gated_marker, 1)

    current_sync = re.compile(
        r'mapSelectionActive=true;\s*const selectedGroup=activityGroups\.get\(location\.event\.id\);\s*const nextMultiStoreEventId=.*?\s*ensureMapVisible',
        re.S,
    )
    if "const nextMultiStoreEventId=isMappedMultiStoreGroup(selectedGroup)?selectedGroup.id:null;" not in html:
        if current_sync.search(html):
            html = current_sync.sub(SELECT_SYNC_JS, html, count=1)
        else:
            html = must_sub(r'mapSelectionActive=true;\s*ensureMapVisible', SELECT_SYNC_JS, html, "selectLocation multi-store sync")

    clean_render = "renderMapMarkers();renderFloatingEvents();updateFilterUI();"
    integrated_render = "normalizeMultiStoreState();renderMapMarkers();renderFloatingEvents();renderMultiStoreControl();updateFilterUI();"
    if integrated_render not in html:
        if clean_render not in html:
            raise RuntimeError("renderAll integration: target not found")
        html = html.replace(clean_render, integrated_render, 1)

    return html


def validate(html: str) -> None:
    required = [
        'id="multiStoreControl"',
        '<span class="multi-store-label">多店活動</span>',
        'id="multiStoreCollapse"',
        "function isMappedMultiStoreGroup(group)",
        "group.floating||group.multiFilter",
        "function collapseMultiStoreMenu(updateHistory=true)",
        "multiStoreMenuOpen=true;",
        "const bottomGap=MOBILE_QUERY.matches?104:80;",
        "if(host)host.replaceChildren();",
        "const nextMultiStoreEventId=isMappedMultiStoreGroup(selectedGroup)?selectedGroup.id:null;",
    ]
    missing = [token for token in required if token not in html]
    if missing:
        raise RuntimeError(f"post-patch validation failed: {missing}")
    if 'data-filter="multi"' in html:
        raise RuntimeError("visible multi-store filter button must be removed")


def main() -> None:
    original = MAP_HTML.read_text(encoding="utf-8")
    updated = apply_patch(original)
    validate(updated)
    if updated != original:
        MAP_HTML.write_text(updated, encoding="utf-8")
        print("Updated public/taiwan-exhibition-map.html")
    else:
        print("Multi-store map control already applied")


if __name__ == "__main__":
    main()
