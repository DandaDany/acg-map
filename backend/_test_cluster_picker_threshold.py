from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / 'public' / 'taiwan-exhibition-map.html'
text = HTML.read_text(encoding='utf-8')

# Product rule: spatially resolvable clusters keep zooming; at max zoom,
# 2-4 distinct activities spiderfy, 5+ distinct activities use Fullscreen Picker.
cluster = text[text.index('function clusterPickerItems'):text.index("cluster.on('clusterclick'")]
assert 'DESTINATION_VENUE_GROUPS' not in text
assert 'function destinationVenueGroup' not in text
assert 'function destinationClusterInfo' not in text
assert "if(map.getZoom()<map.getMaxZoom()){clusterLayer.zoomToBounds();return}" in cluster
assert "if(items.length>4){openActivityPicker({mode:'cluster',items,title:'這個地點的活動'});return}" in cluster
assert 'clusterLayer.spiderfy();' in cluster
assert 'MOBILE_QUERY' not in cluster  # same threshold on desktop and mobile cluster click.

# Count distinct activities, not raw marker/location count.
picker = text[text.index('function clusterPickerItems'):text.index('function handleClusterActivate')]
assert 'const seenEvents=new Set()' in picker
assert 'seenEvents.has(group.id)' in picker
assert 'seenEvents.add(group.id)' in picker

node = shutil.which('node')
if node:
    script = r'''
let pickerCalls=0, zoomCalls=0, spiderCalls=0;
let currentZoom=16;
const map={getZoom:()=>currentZoom,getMaxZoom:()=>16};
const activityGroups=new Map();
const locations=new Map();
function locationById(id){return locations.get(id)||null}
function openActivityPicker(payload){pickerCalls++;globalThis.lastPayload=payload}
function reset(){pickerCalls=0;zoomCalls=0;spiderCalls=0;globalThis.lastPayload=null}
function add(id,eventId){
  const event={id:eventId};
  const location={id,event};
  locations.set(id,location);
  activityGroups.set(eventId,{id:eventId,title:eventId});
  return {locationId:id};
}
function layer(markers){return {getAllChildMarkers:()=>markers,zoomToBounds:()=>zoomCalls++,spiderfy:()=>spiderCalls++}}
'''
    start = text.index('function clusterPickerItems')
    end = text.index("cluster.on('clusterclick'", start)
    script += '\n' + text[start:end] + '\n'
    script += r'''
function assert(ok,msg){if(!ok)throw new Error(msg)}

reset();currentZoom=15;
let markers=[add('a1','A'),add('b1','B'),add('c1','C'),add('d1','D'),add('e1','E')];
handleClusterActivate(layer(markers));
assert(zoomCalls===1&&pickerCalls===0&&spiderCalls===0,'below max zoom must only zoom');

reset();currentZoom=16;
markers=[add('f1','F'),add('g1','G'),add('h1','H'),add('i1','I')];
handleClusterActivate(layer(markers));
assert(spiderCalls===1&&pickerCalls===0,'four distinct activities must spiderfy');

reset();currentZoom=16;
markers=[add('j1','J'),add('k1','K'),add('l1','L'),add('m1','M'),add('n1','N')];
handleClusterActivate(layer(markers));
assert(pickerCalls===1&&spiderCalls===0,'five distinct activities must open picker');
assert(lastPayload.items.length===5,'picker must receive five distinct activities');

reset();currentZoom=16;
markers=[add('o1','O'),add('o2','O'),add('p1','P'),add('q1','Q'),add('r1','R')];
handleClusterActivate(layer(markers));
assert(spiderCalls===1&&pickerCalls===0,'duplicate markers for one event must not inflate threshold');
'''
    completed = subprocess.run([node, '-e', script], cwd=ROOT, capture_output=True, text=True, check=False)
    assert completed.returncode == 0, completed.stderr

print('cluster picker threshold: PASS')
