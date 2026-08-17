#!/usr/bin/env python3
"""Idempotently add the dedicated multi-store map control to the generated map HTML."""
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
    <div class="multi-store-menu" id="multiStoreMenu" hidden></div>
  </div>'''

CONTROL_CSS = r'''
/* Dedicated multi-store activity map control */
.multi-store-control{position:relative;display:flex;flex-direction:column;align-items:center;pointer-events:auto;min-width:48px}
.multi-store-control[hidden],.multi-store-menu[hidden]{display:none!important}
.multi-store-trigger{width:48px;height:48px;border:1px solid var(--border);border-radius:50%;display:grid;place-items:center;padding:0;background:var(--panel);color:var(--text);box-shadow:var(--shadow);cursor:pointer;transition:transform .16s ease,border-color .16s ease,box-shadow .16s ease}
.multi-store-trigger:hover{transform:translateY(-1px)}
.multi-store-trigger:focus-visible{outline:3px solid color-mix(in srgb,var(--accent) 32%,transparent);outline-offset:2px}
.multi-store-trigger.active{border-color:var(--accent);box-shadow:0 0 0 2px color-mix(in srgb,var(--accent) 18%,transparent),var(--shadow)}
.multi-store-trigger svg{width:23px;height:23px;fill:currentColor}
.multi-store-label{margin-top:4px;font-size:10px;line-height:1.15;font-weight:700;letter-spacing:.02em;color:var(--muted);white-space:nowrap;text-shadow:0 1px 2px var(--panel)}
.multi-store-menu{position:absolute;right:0;top:calc(100% + 10px);width:min(310px,calc(100vw - 32px));max-height:min(360px,55vh);overflow:auto;padding:8px;border:1px solid var(--border);border-radius:16px;background:var(--panel);box-shadow:var(--shadow);z-index:20}
.multi-store-option{width:100%;display:flex;align-items:center;justify-content:space-between;gap:12px;border:0;border-radius:12px;padding:10px 11px;background:transparent;color:var(--text);text-align:left;cursor:pointer}
.multi-store-option:hover,.multi-store-option:focus-visible{background:var(--panel-2);outline:none}
.multi-store-option.active{background:color-mix(in srgb,var(--accent) 10%,var(--panel));}
.multi-store-option-copy{min-width:0;display:flex;flex-direction:column;gap:3px}
.multi-store-option-title{font-size:13px;line-height:1.35;font-weight:750;overflow:hidden;text-overflow:ellipsis;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.multi-store-option-meta{font-size:11px;line-height:1.3;color:var(--muted)}
.multi-store-option-action{flex:none;font-size:11px;font-weight:800;color:var(--accent)}
@media(max-width:760px){.multi-store-control{min-width:44px}.multi-store-trigger{width:44px;height:44px}.multi-store-trigger svg{width:21px;height:21px}.multi-store-label{font-size:10px}.multi-store-menu{right:0;width:min(292px,calc(100vw - 20px));max-height:46vh}}
'''

CONTROL_JS = r'''
let multiStoreMenuOpen=false;
let activeMultiStoreEventId=null;

function isMultiStoreMapGroup(group){
  return !!(group&&!group.floating&&group.multiFilter);
}
function getVisibleMultiStoreGroups(){
  return getFilteredActivityGroups().filter(group=>isMultiStoreMapGroup(group)&&group.locations.some(location=>occurrenceVisible(location,uiState.filters)&&Number.isFinite(+location.lat)&&Number.isFinite(+location.lng)));
}
function multiStorePreferredLocation(group){
  const nearest=nearestLocationForGroup(group);
  if(nearest&&nearest.location)return nearest.location;
  return group.locations.find(location=>occurrenceVisible(location,uiState.filters)&&Number.isFinite(+location.lat)&&Number.isFinite(+location.lng))||primaryLocationFor(group);
}
function normalizeMultiStoreState(){
  const groups=getVisibleMultiStoreGroups();
  if(activeMultiStoreEventId&&!groups.some(group=>group.id===activeMultiStoreEventId)){
    const previous=activeMultiStoreEventId;
    activeMultiStoreEventId=null;
    multiStoreMenuOpen=false;
    if(uiState.selectedEventId===previous)closeActiveMapPopup({clearSelection:true,updateHistory:false});
  }
  if(!groups.length)multiStoreMenuOpen=false;
  return groups;
}
function collapseMultiStoreEvent(){
  const active=activeMultiStoreEventId;
  if(!active)return;
  activeMultiStoreEventId=null;
  multiStoreMenuOpen=false;
  if(uiState.selectedEventId===active)closeActiveMapPopup({clearSelection:true,updateHistory:true});
  else clearSelection();
  renderMapMarkers();
  renderMultiStoreControl();
}
function toggleMultiStoreEvent(id){
  const group=activityGroups.get(id);
  if(!isMultiStoreMapGroup(group))return;
  if(activeMultiStoreEventId===id){collapseMultiStoreEvent();return;}
  activeMultiStoreEventId=id;
  multiStoreMenuOpen=false;
  renderMapMarkers();
  renderMultiStoreControl();
  const location=multiStorePreferredLocation(group);
  if(location)selectLocation(location.id,{openPopup:true,revealMarker:true,recenter:true,updateHistory:true});
}
function renderMultiStoreControl(){
  const host=document.getElementById('multiStoreControl');
  const trigger=document.getElementById('multiStoreTrigger');
  const menu=document.getElementById('multiStoreMenu');
  if(!host||!trigger||!menu)return;
  const groups=getVisibleMultiStoreGroups();
  host.hidden=!groups.length;
  if(!groups.length){menu.hidden=true;return;}
  trigger.classList.toggle('active',!!activeMultiStoreEventId);
  trigger.setAttribute('aria-expanded',multiStoreMenuOpen?'true':'false');
  trigger.onclick=event=>{event.stopPropagation();multiStoreMenuOpen=!multiStoreMenuOpen;renderMultiStoreControl();};
  menu.hidden=!multiStoreMenuOpen;
  menu.replaceChildren();
  groups.forEach(group=>{
    const option=document.createElement('button');
    option.type='button';
    option.className='multi-store-option'+(group.id===activeMultiStoreEventId?' active':'');
    option.dataset.multiStoreId=group.id;
    const copy=document.createElement('span');
    copy.className='multi-store-option-copy';
    const title=document.createElement('span');
    title.className='multi-store-option-title';
    title.textContent=group.title;
    const meta=document.createElement('span');
    meta.className='multi-store-option-meta';
    const visibleCount=group.locations.filter(location=>occurrenceVisible(location,uiState.filters)&&Number.isFinite(+location.lat)&&Number.isFinite(+location.lng)).length;
    meta.textContent=visibleCount+' 間門市';
    const action=document.createElement('span');
    action.className='multi-store-option-action';
    action.textContent=group.id===activeMultiStoreEventId?'收合':'展開';
    copy.append(title,meta);
    option.append(copy,action);
    option.addEventListener('click',event=>{event.stopPropagation();toggleMultiStoreEvent(group.id);});
    menu.appendChild(option);
  });
}
'''

SELECT_SYNC_JS = r'''mapSelectionActive=true;
  const selectedGroup=activityGroups.get(location.event.id);
  const nextMultiStoreEventId=isMultiStoreMapGroup(selectedGroup)?selectedGroup.id:null;
  if(activeMultiStoreEventId!==nextMultiStoreEventId){
    activeMultiStoreEventId=nextMultiStoreEventId;
    multiStoreMenuOpen=false;
    renderMapMarkers();
    renderMultiStoreControl();
  }
  ensureMapVisible'''


def must_sub(pattern: str, repl: str, text: str, label: str, *, flags=0) -> str:
    updated, count = re.subn(pattern, repl, text, count=1, flags=flags)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one patch target, got {count}")
    return updated


def apply_patch(html: str) -> str:
    if 'id="multiStoreControl"' not in html:
        html = must_sub(
            r'(<div\s+class="floating-events"\s+id="floatingEvents"[^>]*></div>)',
            lambda m: m.group(1) + CONTROL_HTML,
            html,
            "multi-store control host",
        )

    if "/* Dedicated multi-store activity map control */" not in html:
        html = must_sub(r'</style>', CONTROL_CSS + '\n</style>', html, "multi-store control styles")

    if "function isMultiStoreMapGroup(group)" not in html:
        html = must_sub(
            r'function\s+renderFloatingEvents\s*\(\)\s*\{',
            CONTROL_JS + '\nfunction renderFloatingEvents(){',
            html,
            "multi-store control logic",
        )

    marker_old = "const locations=getFilteredVenueOccurrences(venue._id);"
    marker_new = "const locations=getFilteredVenueOccurrences(venue._id).filter(location=>{const group=activityGroups.get(location.event.id);return !isMultiStoreMapGroup(group)||group.id===activeMultiStoreEventId;});"
    if marker_new not in html:
        if marker_old not in html:
            raise RuntimeError("marker visibility gate: target not found")
        html = html.replace(marker_old, marker_new, 1)

    if "const nextMultiStoreEventId=isMultiStoreMapGroup(selectedGroup)?selectedGroup.id:null;" not in html:
        html = must_sub(
            r'mapSelectionActive=true;\s*ensureMapVisible',
            SELECT_SYNC_JS,
            html,
            "selectLocation multi-store sync",
        )

    render_old = "renderMapMarkers();renderFloatingEvents();updateFilterUI();"
    render_new = "normalizeMultiStoreState();renderMapMarkers();renderFloatingEvents();renderMultiStoreControl();updateFilterUI();"
    if render_new not in html:
        if render_old not in html:
            raise RuntimeError("renderAll integration: target not found")
        html = html.replace(render_old, render_new, 1)

    return html


def validate(html: str) -> None:
    required = [
        'id="multiStoreControl"',
        '<span class="multi-store-label">多店活動</span>',
        "function isMultiStoreMapGroup(group)",
        "group.id===activeMultiStoreEventId",
        "function toggleMultiStoreEvent(id)",
        "function collapseMultiStoreEvent()",
        "renderMultiStoreControl();updateFilterUI();",
        "const nextMultiStoreEventId=isMultiStoreMapGroup(selectedGroup)?selectedGroup.id:null;",
    ]
    missing = [token for token in required if token not in html]
    if missing:
        raise RuntimeError(f"post-patch validation failed: {missing}")


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
