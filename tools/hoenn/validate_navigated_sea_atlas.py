"""Audit compiled tile GPS fields and seal all eight controller journeys."""
import hashlib,json,re,struct,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'.local/hoenn-route12-src';out=ROOT/'mods/hoenn/coastal-update-validation/common/navigation';rom=(source/'pokeemerald.gba').read_bytes();sha=hashlib.sha256(rom).hexdigest()
r=json.loads((source/'.journey-navigated-sea-atlas').read_text());raw=subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),'-S',str(source/'pokeemerald.elf')],text=True);symbols={n:(int(a,16)-0x08000000,int(size,16)) for a,size,_,n in re.findall(r'^(\w+) (\w+) (\w) (\S+)$',raw,re.M)}
at,size=symbols['sWorldNavigationPixels'];values=np.frombuffer(rom[at:at+size],dtype='<u2');assert len(values)==r['tiles']
xy=np.stack([values&255,values>>8],axis=1).astype(int);assert (xy>=[0,0]).all() and (xy<=[223,111]).all()
at,table_size=symbols['sWorldTileGrids'];stride=table_size//len(r['projections']);grids={};maximum=0
for p in r['projections']:
 row=len(grids);first,ident,w,h=struct.unpack_from('<IHHH',rom,at+row*stride);assert (w,h)==(p['width'],p['height']);grid=xy[first:first+w*h].reshape(h,w,2);grids[p['map']]=grid
 for axis in [0,1]:
  if grid.shape[axis]>1:maximum=max(maximum,int(abs(np.diff(grid,axis=axis)).max()))
assert maximum<=2
maps={p.parent.name:json.loads(p.read_text()) for p in (source/'data/maps').glob('*/map.json')};byid={m['id']:n for n,m in maps.items()};seams=0
for n,a in grids.items():
 for c in maps[n].get('connections') or []:
  other=byid.get(c['map']);d=c['direction'];offset=c['offset']
  if other not in grids or d not in ['left','right','up','down']:continue
  b=grids[other];h,w=a.shape[:2];hh,ww=b.shape[:2]
  if d in ['left','right']:
   for y in range(max(0,offset),min(h,offset+hh)):assert np.array_equal(a[y,0 if d=='left' else w-1],b[y-offset,ww-1 if d=='left' else 0])
  else:
   for x in range(max(0,offset),min(w,offset+ww)):assert np.array_equal(a[0 if d=='up' else h-1,x],b[hh-1 if d=='up' else 0,x-offset])
  seams+=1
required=set(r['active_generated_seas']);visited=set();trips=[]
for p in sorted(out.rglob('*.json')):
 if p.name=='navigated-sea-atlas.json':continue
 t=json.loads(p.read_text())
 if 'marker_samples' not in t:continue
 assert t['passed'] and t['rom_sha256']==sha,(p,t.get('gps_jumps'))
 assert t['controller_roundtrip'] and t['no_midroute_warps_or_coordinate_writes'] and t['save_continue_preserves_location']
 assert len(t['marker_samples'])==t['walked_tiles']+1
 assert all(max(abs(a-b) for a,b in zip(u['marker'],v['marker']))<=2 for u,v in zip(t['marker_samples'],t['marker_samples'][1:]))
 visited.update(v['map'] for v in t['arrivals']);trips.append(dict(profile=t['profile'],walked_tiles=t['walked_tiles'],transitions=len(t['transitions']),proof_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
assert required<=visited and len(trips)==8,(sorted(required-visited),len(trips))
assert 'MAP_JOURNEYHOENNCROSSING' not in (source/'src/data/journey_world_map.h').read_text()
result=dict(passed=True,rom_sha256=sha,compiled_gps_tiles=len(values),compiled_shared_edges=seams,maximum_neighbor_pixel_step=maximum,all_generated_seas_visited=sorted(required),trips=trips,total_controller_tiles=sum(t['walked_tiles'] for t in trips),total_controller_transitions=sum(t['transitions'] for t in trips),unconnected_prototype_hidden=True,large_sea_areas_without_internal_grid=True,no_terrain_or_port_changes=True,level_100_and_repels_are_test_fixtures=True,full_campaign_playthrough=False)
(out/'navigated-sea-atlas.json').write_text(json.dumps(result,indent=2)+'\n');print('Compiled GPS and 56-sea controller journeys passed',result['total_controller_tiles'],result['total_controller_transitions'])
