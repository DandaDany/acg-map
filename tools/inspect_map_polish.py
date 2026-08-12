from pathlib import Path

p=Path('public/taiwan-exhibition-map.html')
text=p.read_text(encoding='utf-8')
patterns=[
  'function openDesktopEventModal',
  'function openDesktopVenuePicker',
  "cluster.on('clusterclick'",
  'function markerClick',
  'function selectLocation(locationId,options={})',
  'function occurrenceVisible',
  'function getFacetCount',
  'data-filter="time"',
  "if(value==='today')",
  "if(value==='next7')",
  'id="filterClose"',
  'home-filter-close',
  'function renderUserLocationMarker',
  'user-location-dot',
  'function buildPopupCards',
  'function popupCardHtml',
  'mobile-card-kv',
  'IP：',
  '主辦',
  '官方資訊',
  '分享活動',
  'collectionContext',
  'function getCollectionEntries',
  'function getFacetCount',
]
lines=text.splitlines()
out=[]
for pat in patterns:
    out.append('\n'+'='*96+'\nPATTERN: '+pat+'\n'+'='*96)
    hits=[i for i,line in enumerate(lines) if pat in line]
    if not hits:
        out.append('NOT FOUND')
        continue
    for idx in hits[:6]:
        a=max(0,idx-22);b=min(len(lines),idx+55)
        out.append(f'--- lines {a+1}-{b} ---')
        out.extend(f'{j+1:05d}: {lines[j]}' for j in range(a,b))
Path('tools/_inspect_map_polish.txt').write_text('\n'.join(out),encoding='utf-8')
