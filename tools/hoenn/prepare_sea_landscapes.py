"""Replace repeated sea patches with deterministic organic shores and complete cliffs."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import struct
from prepare_crossing import PIN
from prepare_early_story_tools import PRECEDING

LAYER='sea-landscapes'
SEA_NAMES=(['JourneyCinnabarSouthSea','JourneyWestRiver','JourneyRustboroCoast','JourneyRustboroGate','JourneyDewfordCoast','JourneyDewfordGate',
 'JourneyHoennNorthSea','JourneyHoennMiddleSea','JourneyHoennSouthSea','JourneyPacifidlogSea','JourneyFuchsiaSea']+
 ['JourneyWorldSea%02d'%i for i in range(10)]+['JourneyWorldLane'+i for i in ['10','11','20','21','30','31']])

def prepare(source):
 source=Path(source); marker=source/('.journey-'+LAYER)
 if marker.exists():
  report=json.loads(marker.read_text())
  for p,h in (report['prepared_sha256']|report['preserved_native_sha256']).items():
   if hashlib.sha256((source/p).read_bytes()).hexdigest()!=h:raise ValueError('Changed landscape output: '+p)
  return report
 acquired=json.loads((source/'.source-acquired.json').read_text());assert acquired['commit']==PIN
 expected=dict(acquired['sha256'])
 for layer in PRECEDING+['early-story-tools','mandatory-native-missions','sixteen-badge-leagues','rusturf-reunion']:
  expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 originals={};outputs={};preserved={}
 def checked(p):
  raw=(source/p).read_bytes();h=hashlib.sha256(raw).hexdigest()
  if h!=expected.get(p):raise ValueError('Unreviewed landscape input: '+p)
  preserved.setdefault(p,h)
  return raw
 def stage(p,raw):
  if p not in originals:originals[p]=hashlib.sha256(checked(p)).hexdigest()
  outputs[p]=raw;preserved.pop(p,None)
 for p in ['src/journey_campaign_gates.c','src/journey_gym_scaling.c','src/journey_wild.c','src/journey_family.c','include/constants/opponents.h','src/data/trainers.party','data/scripts/journey_team_stories.inc']:
  preserved[p]=hashlib.sha256(checked(p)).hexdigest()
 layouts={l['id']:l for l in json.loads(checked('data/layouts/layouts.json'))['layouts']}
 # Resolve only maps needed for the signed connection spans.
 maps={n:json.loads(checked(f'data/maps/{n}/map.json')) for n in SEA_NAMES}
 ids={m['id']:n for n,m in maps.items()}
 for p in (source/'data/maps').glob('*/map.json'):
  m=json.loads(p.read_text());ids[m['id']]=m['name']
 all_maps=dict(maps)
 def data(n):
  if n not in all_maps:all_maps[n]=json.loads(checked(f'data/maps/{n}/map.json'))
  return all_maps[n]
 # Copy the complete second Seafoam mountain, including every native contour tile.
 seafoam_map=data('Route20_Frlg');seafoam_layout=layouts[seafoam_map['layout']]
 seafoam_values=struct.unpack('<'+'H'*(seafoam_layout['width']*seafoam_layout['height']),checked(seafoam_layout['blockdata_filepath']))
 seafoam_mountain=[]
 for y in range(6,15):
  for x in range(67,78):
   value=seafoam_values[y*seafoam_layout['width']+x];tile=value&1023
   if 0x68<=tile<=0xAF or tile in [0xB2,0xB3,0xBA,0xBB]:seafoam_mountain.append([x-72,y-14,value])
 reports=[]
 for name,m in maps.items():
  l=layouts[m['layout']];w,h=l['width'],l['height'];frlg=l['layout_version']=='frlg'
  rng=random.Random(int(hashlib.sha256(name.encode()).hexdigest()[:16],16))
  water=0x112B if frlg else 0x1170
  old=list(struct.unpack('<'+'H'*(w*h),checked(l['blockdata_filepath'])));values=[water]*(w*h)
  # Connections describe intervals, not an open whole edge. Keep all actual overlaps.
  open_edges={d:set() for d in ['up','down','left','right']}
  for c in m.get('connections') or []:
   d=c['direction']
   if d not in open_edges:continue
   other=layouts[data(ids[c['map']])['layout']]
   length=other['width'] if d in ['up','down'] else other['height']
   limit=w if d in ['up','down'] else h
   open_edges[d].update(range(max(0,c['offset']),min(limit,c['offset']+length)))
  protected=set()
  # Wide navigable perimeter keeps the established regional seam coordinates safe.
  for y in range(h):
   for x in range(w):
    if x<3 or y<3 or x>=w-3 or y>=h-3:protected.add((x,y))
  for e in m['object_events']:
   if e['elevation']==1:
    protected.update((e['x']+dx,e['y']+dy) for dx in range(-1,2) for dy in range(-1,2))
  # Preserve the exact Dive patch and its surroundings (depth maps mirror coordinates).
  for y in range(h):
   for x in range(w):
    if old[y*w+x] in [0x114F]:protected.update((x+dx,y+dy) for dx in range(-3,4) for dy in range(-3,4))
  land=set()
  def blob(cx,cy,rx,ry):
   phase=rng.random()*6.28;phase2=rng.random()*6.28
   for y in range(max(3,int(cy-ry-2)),min(h-3,int(cy+ry+3))):
    for x in range(max(3,int(cx-rx-2)),min(w-3,int(cx+rx+3))):
     angle=math.atan2((y-cy)/ry,(x-cx)/rx)
     radius=1+.13*math.sin(3*angle+phase)+.10*math.sin(5*angle+phase2)
     if ((x-cx)/rx)**2+((y-cy)/ry)**2<radius**2 and (x,y) not in protected:land.add((x,y))
  # Small asymmetric beaches for existing land trainers; mission identity is unchanged.
  land_events=[e for e in m['object_events'] if e['elevation']==3]
  if land_events:
   cx=sum(e['x'] for e in land_events)/len(land_events);cy=sum(e['y'] for e in land_events)/len(land_events)
   blob(cx,cy,max(4,(max(e['x'] for e in land_events)-min(e['x'] for e in land_events))/2+3),max(4,(max(e['y'] for e in land_events)-min(e['y'] for e in land_events))/2+3))
   for e in land_events:
    land.update((e['x']+dx,e['y']+dy) for dx in range(-1,2) for dy in range(-1,2))
  entrances=[e for e in m['warp_events'] if e['dest_map'].startswith('MAP_JOURNEYSANCTUARY')]
  for e in entrances:
   # Keep doorway/warp coordinates but replace the square 17x17 slab with an island.
   blob(e['x'],e['y']-1,rng.uniform(9,11),rng.uniform(9,10))
   for dx,dy,_ in seafoam_mountain:
    land.update((e['x']+dx+a,e['y']+dy+b) for a in range(-1,2) for b in range(-1,2))
  for _ in range(1 if w*h<1000 else rng.randint(2,4)):
   cx=rng.randint(4,max(4,w-5));cy=rng.randint(5,max(5,h-6))
   blob(cx,cy,rng.uniform(2.4,4.8),rng.uniform(2,4))
  # Remove single-cell necks/tips. Keep a solid landing in front of each doorway/NPC.
  keep={(e['x']+dx,e['y']+dy) for e in land_events+entrances for dx in range(-1,2) for dy in range(-1,2)}
  for _ in range(2):
   land={p for p in land if p in keep or sum((p[0]+dx,p[1]+dy) in land for dx,dy in [(0,-1),(0,1),(-1,0),(1,0)])>=2}
  land-=protected
  shore=([0x10C,0x10D,0x10E,0x114,0x115,0x116,0x11C,0x11D,0x11E] if frlg else [0x11B,0x11C,0x11D,0x123,0x124,0x125,0x12B,0x12C,0x12D])
  for x,y in land:
   north=(x,y-1) not in land;south=(x,y+1) not in land;west=(x-1,y) not in land;east=(x+1,y) not in land
   row=0 if north else 2 if south else 1;col=0 if west else 2 if east else 1
   # Shoreline has native elevation/behavior; Emerald's water fringe uses elevation 1.
   tile=shore[row*3+col];elevation=3 if frlg or row==col==1 else 1
   values[y*w+x]=elevation*4096+tile
  # Broad inner patches add grassy islets without turning every beach into a copy.
  for x,y in land:
   if all((x+dx,y+dy) in land for dx in range(-2,3) for dy in range(-2,3)):values[y*w+x]=0x3001
  # One existing common trainer per broad route waits on sand; no new battle flags.
  moved=[]
  common=[e for e in m['object_events'] if e['graphics_id']=='OBJ_EVENT_GFX_SWIMMER_M_WATER']
  occupied={(e['x'],e['y']) for key in ['object_events','warp_events','coord_events','bg_events'] for e in m[key]}
  choices=[(x,y) for x,y in sorted(land) if (x,y) not in occupied and all((x+dx,y+dy) in land for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)]) and not any(abs(x-e['x'])+abs(y-e['y'])<7 for e in entrances)]
  if w>=32 and common and choices:
   e=common[-1];old_event=dict(e);x,y=min(choices,key=lambda p:abs(p[0]-e['x'])+abs(p[1]-e['y']))
   e.update(x=x,y=y,elevation=3,graphics_id='OBJ_EVENT_GFX_SWIMMER_M')
   values[y*w+x]=0x3115 if frlg else 0x3124
   moved.append(dict(before=old_event,after=dict(e)))
  for e in entrances:
   cx,ey=e['x'],e['y']
   for dx,dy,tile in seafoam_mountain:values[(ey+dy)*w+cx+dx]=tile
  for y in range(h):
   for x in range(w):
    if old[y*w+x]==0x114F:values[y*w+x]=old[y*w+x]
  # Natural water boulders, including every unconnected boundary segment.
  rocks=([0x510,0x511,0x518,0x519] if frlg else [0x550,0x551,0x558,0x559])
  def rock(x,y,dx,dy):values[y*w+x]=rocks[dy*2+dx]
  def is_open(x,y):
   return (x<2 and y in open_edges['left']) or (x>=w-2 and y in open_edges['right']) or (y<2 and x in open_edges['up']) or (y>=h-2 and x in open_edges['down'])
  for y in range(h):
   for x in range(w):
    if min(x,y,w-1-x,h-1-y)>=2 or is_open(x,y):continue
    # Complete two-tile boulders, rather than isolated quarters of a graphic.
    rock(x,y,x%2,y%2)
  # Scattered reefs away from all NPCs, doors, Dive patches and the connection lane.
  occupied={(e['x'],e['y']) for key in ['object_events','warp_events','coord_events','bg_events'] for e in m[key]}
  reefs=set()
  for _ in range(max(1,w*h//260)):
   x=rng.randint(4,max(4,w-6));y=rng.randint(4,max(4,h-6))
   cells={(x+dx,y+dy) for dx in range(2) for dy in range(2)}
   if any(p in protected or p in land or any(abs(p[0]-a)+abs(p[1]-b)<6 for a,b in reefs) or any(abs(p[0]-a)+abs(p[1]-b)<4 for a,b in occupied) for p in cells):continue
   for xx,yy in cells:rock(xx,yy,xx-x,yy-y)
   reefs.update(cells)
  # Every non-water NPC still stands on walkable sand, never on a shore wall.
  for e in land_events:values[e['y']*w+e['x']]=0x3115 if frlg else 0x3124
  stage(l['blockdata_filepath'],struct.pack('<'+'H'*len(values),*values))
  stage(l['border_filepath'],struct.pack('<4H',*rocks))
  map_path=f'data/maps/{name}/map.json'
  if moved:stage(map_path,(json.dumps(m,indent=2)+'\n').encode())
  else:preserved[map_path]=hashlib.sha256(checked(map_path)).hexdigest()
  reports.append(dict(map=name,width=w,height=h,land_tiles=len(land),water_fraction=round(sum(v in [water,0x114F] for v in values)/len(values),4),open_edges={d:sorted(v) for d,v in open_edges.items()},trainer_relocations=moved,trainers=m['object_events'],cave_entrances=entrances,blockdata_sha256=hashlib.sha256(outputs[l['blockdata_filepath']]).hexdigest()))
 # The western river enters Route114 BELOW its original waterfall, not above it.
 native_path='data/layouts/Route114/map.bin'
 native_bank=(Path(__file__).parent/'templates/route114-native.bin').read_bytes()
 if hashlib.sha256(native_bank).hexdigest()!=acquired['sha256'][native_path]:raise ValueError('Changed native Route114 reference')
 route=data('Route114');rl=layouts[route['layout']];rw=rl['width']
 rb=list(struct.unpack('<'+'H'*(rw*rl['height']),checked(native_path)))
 original_bank=struct.unpack('<'+'H'*(rw*rl['height']),native_bank)
 # Reinstate the cliff separating the upper river from the lower lake.
 for y in range(10,13):
  for x in range(12):rb[y*rw+x]=original_bank[y*rw+x]
 # Align the narrow river mouth on both sides of the signed-offset connection.
 rock_tiles=[0x550,0x551,0x558,0x559]
 for y in list(range(12,14))+list(range(20,24)):
  for x in range(2):rb[y*rw+x]=rock_tiles[(y%2)*2+x]
 stage(native_path,struct.pack('<'+'H'*len(rb),*rb))
 river=layouts[maps['JourneyWestRiver']['layout']];w,h=river['width'],river['height'];rp=river['blockdata_filepath']
 rv=list(struct.unpack('<'+'H'*(w*h),outputs[rp]))
 for y in range(h):
  for x in range(30,w):
   if 4<=y<=9:rv[y*w+x]=0x1170
   elif x>=34:
    # Fully assembled rock banks narrow the sea into a river; no invisible walls.
    rv[y*w+x]=rock_tiles[(y%2)*2+x%2]
 stage(rp,struct.pack('<'+'H'*len(rv),*rv))
 # Matching closed bank at the north edge of the lower coastal sea.
 coast=layouts[maps['JourneyRustboroCoast']['layout']];cp=coast['blockdata_filepath'];cv=list(struct.unpack('<'+'H'*(coast['width']*coast['height']),outputs[cp]))
 for y in range(2):
  for x in range(34,coast['width']):cv[y*coast['width']+x]=rock_tiles[y*2+x%2]
 stage(cp,struct.pack('<'+'H'*len(cv),*cv))
 for item in reports:
  l=layouts[maps[item['map']]['layout']];raw=outputs[l['blockdata_filepath']];vals=struct.unpack('<'+'H'*(len(raw)//2),raw)
  item['blockdata_sha256']=hashlib.sha256(raw).hexdigest()
  item['water_fraction']=round(sum(v in [0x1170,0x112B,0x114F] for v in vals)/len(vals),4)
 # Interior rooms, altars and returns stay exactly as in the preceding candidate.
 cave_reports=[]
 for site in json.loads((source/'.journey-sanctuaries').read_text())['sites']:
  name=site['map'];m=data(name);l=layouts[m['layout']]
  checked(l['blockdata_filepath']);checked(l['border_filepath'])
  cave_reports.append(dict(map=name,interior_unchanged=True,all_original_altars_and_return_warp_preserved=True))
 report=dict(status='varied_sea_landscapes_candidate',source_commit=PIN,maps=reports,caves=cave_reports,river_access=dict(map='JourneyWestRiver',route='Route114',connection_offset=-10,river_edge_rows=[4,9],route_edge_rows=[14,19],native_waterfall=[12,10,12],upper_bank_restored=True),seafoam_mountain=dict(source_map='Route20_Frlg',source_entrance=[72,14],cells=seafoam_mountain,tiles_copied_exactly=True),original_sha256=originals,prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()},preserved_native_sha256=preserved,all_connections_warps_scripts_trainer_identities_and_missions_preserved=True,full_campaign_validated=False)
 for p,raw in outputs.items():(source/p).write_bytes(raw)
 marker.write_text(json.dumps(report,indent=2)+'\n');return report

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True);print(json.dumps(prepare(p.parse_args().source),indent=2))
