"""Audit all integrated surface sea routes against native compiled terrain."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
prefix=(ROOT/'tools/hoenn/validate_eastern_union.py').read_text().split('exec(compile((ROOT/')[0]
replacement="names=[p.parent.name for p in (source/'data/maps').glob('*/map.json') if json.loads(p.read_text()).get('map_type') in ['MAP_TYPE_ROUTE','MAP_TYPE_CITY','MAP_TYPE_TOWN','MAP_TYPE_OCEAN_ROUTE'] or ('Harbor' in p.parent.name and json.loads(p.read_text()).get('connections'))]"
prefix=prefix.replace("names=[r['map'] for r in report['rectangles']]",replacement)
exec(compile(prefix,str(ROOT/'tools/hoenn/validate_eastern_union.py'),'exec'))
exec(compile((ROOT/'tools/hoenn/native_water_walk.py').read_text(),str(ROOT/'tools/hoenn/native_water_walk.py'),'exec'))
passable={n:{i for i in p if not blocks[n][2][i]&0xC00 and blocks[n][2][i]>>12==1 and water_behaviors[behaviors[n][i]]} for n,p in passable.items()}
from collections import deque
start=('Route19_Frlg',15,50);queue=deque([start]);reachable={start}
while queue:
 n,x,y=queue.popleft();w,h,_=blocks[n]
 for dx,dy,key in keys:
  xx,yy=x+dx,y+dy
  nxt=(n,xx,yy) if 0<=xx<w and 0<=yy<h and yy*w+xx in passable[n] else connection_step(n,x,y,key) if not(0<=xx<w and 0<=yy<h) else None
  if nxt is not None and nxt not in reachable:reachable.add(nxt);queue.append(nxt)
reachable_maps=sorted({n for n,_,_ in reachable})
required={r['map'] for r in json.loads((source/'.journey-sea-landscapes').read_text())['maps']}
required.update(r['map'] for r in json.loads((source/'.journey-kanto-open-sea').read_text())['landscape'])
required.update(r['map'] for r in report['rectangles'] if r['map'].startswith('Journey'))
assert required<=set(reachable_maps),('Disconnected integrated sea map',sorted(required-set(reachable_maps)))
# The engine uses these collision-marked border blocks beyond unconnected sides.
terrain=[]
for n in sorted(required):
 layout=layouts[maps[n]['layout']];raw=(source/layout['border_filepath']).read_bytes()
 assert all(t&0xC00 for t in struct.unpack('<'+'H'*(len(raw)//2),raw)),('Unblocked outer border',n)
 shore=[0x10C,0x10D,0x10E,0x114,0x115,0x116,0x11C,0x11D,0x11E] if layout['layout_version']=='frlg' else [0x11B,0x11C,0x11D,0x123,0x124,0x125,0x12B,0x12C,0x12D]
 sand=sum(t&1023 in shore for t in blocks[n][2]);assert sand>0,('Empty water-only route',n)
 terrain.append(dict(map=n,sand_tiles=sand,outer_border_collision=True))
lib.stop()
(args.output/'coast-connectivity.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),all_nine_new_channels_reachable=True,all_integrated_surface_seas_reachable=True,unconnected_outer_borders_blocked=True,no_water_only_surface_maps=True,terrain=terrain,required_sea_maps=sorted(required),reachable_maps=reachable_maps,visited_water_tiles=len(reachable),compiled_collision_and_water_behaviors=True,signed_map_connection_offsets=True,graph_audit_not_controller_playthrough=True),indent=2)+'\n')
print('All integrated sea maps connected:',len(required),'maps;',len(reachable),'compiled water tiles',flush=True)
