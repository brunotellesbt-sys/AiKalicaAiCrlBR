"""Lay Hoenn's eastern ocean and Sevii on one non-overlapping tile plane."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import struct
from prepare_crossing import PIN
from prepare_early_story_tools import PRECEDING

LAYER = 'eastern-sea-union'
# Tile coordinates, measured from Route125's northwest corner.
POSITIONS = {
 'Route124': [-80, 0], 'Route125': [0, 0], 'MossdeepCity': [0, 40],
 'Route126': [-80, 80], 'Route127': [0, 80], 'Route128': [0, 160],
 'Route129': [0, 200], 'Route130': [-80, 200], 'Route131': [-140, 200],
 'EverGrandeCity': [120, 120],
 'JourneyHoennNorthSea': [80, 0], 'JourneyMossdeepOuterSea': [80, 48], 'JourneyMossdeepOuterEastSea': [190,48],
 'JourneyHoennMiddleSea': [80, 80], 'JourneyHoennMiddleEastSea':[190,80], 'JourneyPacifidlogSea': [80, 120],
 'JourneyEverGrandeBackSea': [160, 120], 'JourneyEverGrandeBackSouthSea': [160, 160], 'JourneyHoennSouthSea': [80, 200], 'JourneyHoennSouthEastSea':[190,200],
}
SIZES = {'JourneyHoennNorthSea': [110, 48], 'JourneyMossdeepOuterSea': [110, 32], 'JourneyMossdeepOuterEastSea':[64,32],
 'JourneyHoennMiddleSea': [110, 40], 'JourneyHoennMiddleEastSea':[64,40], 'JourneyPacifidlogSea': [40, 40],
 'JourneyEverGrandeBackSea': [94, 40], 'JourneyEverGrandeBackSouthSea': [94, 40], 'JourneyHoennSouthSea': [110, 40], 'JourneyHoennSouthEastSea':[64,40]}
CELLS = [(0,0),(1,0),(2,0),(3,0),(1,1),(2,1),(1,2),(2,2),(3,1),(3,2)]
for i,(col,row) in enumerate(CELLS):POSITIONS[f'JourneyWorldSea{i:02d}']=[190+64*col,96*row]
for col in [1,2,3]:
 for row in [0,1]:POSITIONS[f'JourneyWorldLane{col}{row}']=[190+64*col,48+96*row]
for col in [1,2,3]:
 for row in [0,1]:SIZES[f'JourneyWorldLane{col}{row}']=[24,48]
NEW = ['JourneyMossdeepOuterSea', 'JourneyMossdeepOuterEastSea','JourneyHoennMiddleEastSea','JourneyHoennSouthEastSea','JourneyEverGrandeBackSea', 'JourneyEverGrandeBackSouthSea']
PORT_NAMES={1:['FourIsland_Harbor_Frlg','SixIsland_Harbor_Frlg'],2:['FiveIsland_Harbor_Frlg','SevenIsland_Harbor_Frlg'],3:['BirthIsland_Harbor_Frlg','NavelRock_Harbor_Frlg']}
for col in [1,2,3]:
 for row in [0,1]:
  x,y=POSITIONS[f'JourneyWorldLane{col}{row}']
  for suffix,dx,w,h in [('Cap',24,17,35),('Right',41,23,48)]:
   n=f'JourneyWorldFill{col}{row}{suffix}';NEW.append(n);POSITIONS[n]=[x+dx,y];SIZES[n]=[w,h]
  POSITIONS[PORT_NAMES[col][row]]=[x+24,y+35]
POSITIONS['JourneyFuchsiaSea']=[142,-14]


def prepare(source):
 source=Path(source);marker=source/('.journey-'+LAYER)
 if marker.exists():
  report=json.loads(marker.read_text())
  for p,h in (report['prepared_sha256']|report['preserved_native_sha256']).items():
   if hashlib.sha256((source/p).read_bytes()).hexdigest()!=h:raise ValueError('Changed eastern ocean output: '+p)
  return report
 acquired=json.loads((source/'.source-acquired.json').read_text());assert acquired['commit']==PIN
 expected=dict(acquired['sha256'])
 for layer in PRECEDING+['early-story-tools','mandatory-native-missions','sixteen-badge-leagues','rusturf-reunion','sea-landscapes']:
  expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 originals={};outputs={};preserved={}
 def checked(p):
  raw=(source/p).read_bytes();h=hashlib.sha256(raw).hexdigest()
  if h!=expected.get(p):raise ValueError('Unreviewed eastern ocean input: '+p)
  preserved[p]=h;return raw
 def stage(p,raw):
  if p in expected and p not in originals:originals[p]=hashlib.sha256(checked(p)).hexdigest()
  outputs[p]=raw;preserved.pop(p,None)
 def encode(data):return (json.dumps(data,indent=2)+'\n').encode()
 layout_data=json.loads(checked('data/layouts/layouts.json'));layouts={l['id']:l for l in layout_data['layouts']}
 maps={n:json.loads(checked(f'data/maps/{n}/map.json')) for n in POSITIONS if n not in NEW}
 template=maps['JourneyHoennNorthSea'];tl=layouts[template['layout']]
 for n in NEW:
  base=maps['JourneyWorldLane'+n[16:18]] if n.startswith('JourneyWorldFill') else template
  tl=layouts[base['layout']]
  m=copy.deepcopy(base);m.update(id='MAP_'+n.upper(),name=n,layout='LAYOUT_'+n.upper(),connections=[],object_events=[],warp_events=[],coord_events=[],bg_events=[])
  maps[n]=m;l=copy.deepcopy(tl);l.update(id=m['layout'],name=n+'_Layout',width=SIZES[n][0],height=SIZES[n][1],border_filepath=f'data/layouts/{n}/border.bin',blockdata_filepath=f'data/layouts/{n}/map.bin')
  layouts[l['id']]=l;layout_data['layouts'].append(l)
  stage(f'data/maps/{n}/scripts.inc',(n+'_MapScripts::\n\t.byte 0\n').encode())
 groups=json.loads(checked('data/maps/map_groups.json'))
 # Append IDs to an existing group: no pre-existing map numbers change.
 group=next(g for g in groups['group_order'] if 'JourneyHoennNorthSea' in groups[g])
 groups[group].extend(NEW);stage('data/maps/map_groups.json',encode(groups))
 events=checked('data/event_scripts.s')
 for n in NEW:events+=f'\n\t.include "data/maps/{n}/scripts.inc"\n'.encode()
 stage('data/event_scripts.s',events)
 # Protect story and League implementation, native Ever Grande mountain and all events.
 for p in ['src/journey_campaign_gates.c','src/journey_gym_scaling.c','src/journey_wild.c','src/journey_family.c','include/constants/opponents.h','src/data/trainers.party','data/scripts/journey_team_stories.inc',layouts[maps['EverGrandeCity']['layout']]['blockdata_filepath'],layouts[maps['Route128']['layout']]['blockdata_filepath']]:checked(p)
 for n in ['EverGrandeCity']+[p for ports in PORT_NAMES.values() for p in ports]:
  checked(layouts[maps[n]['layout']]['blockdata_filepath'])
  checked(f'data/maps/{n}/scripts.inc')
 raw=checked('src/fieldmap.c');old=b'offset2 <= coord && coord <= srcMax';new=b'offset2 <= coord && coord < srcMax'
 assert raw.count(old)==1,'Unexpected incoming-connection bounds'
 stage('src/fieldmap.c',raw.replace(old,new))
 sanctuaries=json.loads((source/'.journey-sanctuaries').read_text())
 for site in sanctuaries['sites']:
  for n in [site['map']]+(['JourneyDepth'+site['theme']] if site['access']=='dive' else []):
   m=json.loads(checked(f'data/maps/{n}/map.json'));l=layouts[m['layout']]
   checked(l['blockdata_filepath']);checked(l['border_filepath'])
 # Delete every old connector edge, including reciprocal endpoints and Route131 shortcut.
 for n,m in maps.items():
  m['connections']=[c for c in m.get('connections') or [] if c['direction'] in ['dive','emerge'] or (n not in SIZES and c['map'] not in {'MAP_'+s.upper() for s in SIZES})]
 maps['JourneyPacifidlogSea']['region_map_section']='MAPSEC_ROUTE_128'
 for name in ['JourneyFuchsiaSea','JourneyWorldSea00']:
  maps[name]['connections']=[c for c in maps[name]['connections'] if c['map'] not in ['MAP_JOURNEYFUCHSIASEA','MAP_JOURNEYWORLDSEA00']]
 links=[]
 def connect(a,d,b):
  ax,ay=POSITIONS[a];bx,by=POSITIONS[b];offset=bx-ax if d in ['up','down'] else by-ay
  opposite={'up':'down','down':'up','left':'right','right':'left'}[d]
  maps[a]['connections'].append(dict(map=maps[b]['id'],direction=d,offset=offset))
  maps[b]['connections'].append(dict(map=maps[a]['id'],direction=opposite,offset=-offset))
  links.append(dict(source=a,direction=d,destination=b,offset=offset))
 for a,d,b in [
 ('JourneyFuchsiaSea','down','JourneyHoennNorthSea'),
 ('Route125','right','JourneyHoennNorthSea'),('MossdeepCity','right','JourneyHoennNorthSea'),
 ('MossdeepCity','right','JourneyMossdeepOuterSea'),('Route127','right','JourneyHoennMiddleSea'),
 ('Route127','right','JourneyPacifidlogSea'),('Route129','right','JourneyHoennSouthSea'),
 ('JourneyHoennNorthSea','right','JourneyWorldSea00'),('JourneyHoennNorthSea','down','JourneyMossdeepOuterSea'),
 ('JourneyWorldSea00','down','JourneyMossdeepOuterEastSea'),('JourneyMossdeepOuterSea','down','JourneyHoennMiddleSea'),
 ('JourneyMossdeepOuterSea','right','JourneyMossdeepOuterEastSea'),('JourneyMossdeepOuterEastSea','right','JourneyWorldLane10'),('JourneyMossdeepOuterEastSea','down','JourneyHoennMiddleEastSea'),('JourneyHoennMiddleSea','right','JourneyHoennMiddleEastSea'),('JourneyHoennMiddleEastSea','right','JourneyWorldLane10'),
 ('JourneyHoennMiddleEastSea','right','JourneyWorldSea04'),('JourneyHoennMiddleSea','down','JourneyPacifidlogSea'),
 ('JourneyHoennMiddleSea','down','EverGrandeCity'),('JourneyHoennMiddleSea','down','JourneyEverGrandeBackSea'),('JourneyHoennMiddleEastSea','down','JourneyEverGrandeBackSea'),
 ('JourneyPacifidlogSea','right','EverGrandeCity'),('JourneyPacifidlogSea','down','Route128'),
 ('EverGrandeCity','right','JourneyEverGrandeBackSea'),('EverGrandeCity','right','JourneyEverGrandeBackSouthSea'),('JourneyEverGrandeBackSea','down','JourneyEverGrandeBackSouthSea'),('EverGrandeCity','down','JourneyHoennSouthSea'),
 ('JourneyEverGrandeBackSea','right','JourneyWorldSea04'),('JourneyEverGrandeBackSea','right','JourneyWorldLane11'),
 ('JourneyEverGrandeBackSouthSea','right','JourneyWorldLane11'),('JourneyEverGrandeBackSouthSea','right','JourneyWorldSea06'),('JourneyEverGrandeBackSouthSea','down','JourneyHoennSouthSea'),('JourneyEverGrandeBackSouthSea','down','JourneyHoennSouthEastSea'),
 ('Route128','down','JourneyHoennSouthSea'),('JourneyHoennSouthSea','right','JourneyHoennSouthEastSea'),('JourneyHoennSouthEastSea','right','JourneyWorldSea06')]:connect(a,d,b)
 for col in [1,2,3]:
  sea_rows={1:[1,4,6],2:[2,5,7],3:[3,8,9]}[col]
  for row in [0,1]:
   lane=f'JourneyWorldLane{col}{row}'
   connect(f'JourneyWorldSea{sea_rows[row]:02d}','down',lane)
   connect(lane,'down',f'JourneyWorldSea{sea_rows[row+1]:02d}')
   cap=f'JourneyWorldFill{col}{row}Cap';right=f'JourneyWorldFill{col}{row}Right';port=PORT_NAMES[col][row]
   connect(lane,'right',cap);connect(lane,'right',port);connect(cap,'right',right);connect(port,'right',right);connect(cap,'down',port)
   connect(f'JourneyWorldSea{sea_rows[row]:02d}','down',cap);connect(f'JourneyWorldSea{sea_rows[row]:02d}','down',right)
   connect(right,'down',f'JourneyWorldSea{sea_rows[row+1]:02d}')
   if col<3:connect(right,'right',f'JourneyWorldLane{col+1}{row}')
 rocks=[0x550,0x551,0x558,0x559];terrain=[]
 for n,(w,h) in SIZES.items():
  m=maps[n];l=layouts[m['layout']];ow,oh=l['width'],l['height'];frlg=l['layout_version']=='frlg';water=0x112B if frlg else 0x1170;rs=[0x510,0x511,0x518,0x519] if frlg else rocks
  old=[] if n in NEW else list(struct.unpack('<'+'H'*(ow*oh),checked(l['blockdata_filepath'])))
  values=[water]*(w*h)
  for y in range(min(oh,h)):
   for x in range(min(ow,w)):
    v=old[y*ow+x] if old else water
    # Old exterior rocks must disappear inside the enlarged navigable ocean.
    if x<2 or y<2 or x>=ow-2 or y>=oh-2:v=water
    values[y*w+x]=v
  # Organic, low sandbars confined to newly added space; preserve all old anchors.
  rng=random.Random(n);land=set()
  for cx,cy,rx,ry in [(ow+18,h//2,6,4),(w-30,h//2+5,5,3)] if n not in NEW else [(w//3,h//3,7,4),(2*w//3,2*h//3,5,3)]:
   cx+=rng.randint(-3,3);cy+=rng.randint(-5,5);rx*=rng.uniform(.75,1.2);ry*=rng.uniform(.8,1.3)
   if cx>=w-5:continue
   rx,ry=int(rx),int(ry)
   for y in range(max(5,cy-ry-1),min(h-5,cy+ry+2)):
    for x in range(max(ow+5 if n not in NEW else 5,cx-rx-1),min(w-5,cx+rx+2)):
     if ((x-cx)/rx)**2+((y-cy)/ry)**2 < 1+.10*rng.random():land.add((x,y))
  shore=[0x10C,0x10D,0x10E,0x114,0x115,0x116,0x11C,0x11D,0x11E] if frlg else [0x11B,0x11C,0x11D,0x123,0x124,0x125,0x12B,0x12C,0x12D]
  for x,y in land:
   row=0 if (x,y-1) not in land else 2 if (x,y+1) not in land else 1
   col=0 if (x-1,y) not in land else 2 if (x+1,y) not in land else 1
   values[y*w+x]=(0x3000 if frlg or row==col==1 else 0x1000)+shore[row*3+col]
  # Sparse complete reefs in the extension, separated from each other and events.
  reefs=[];occupied=[(e['x'],e['y']) for key in ['object_events','warp_events','coord_events','bg_events'] for e in m[key]]
  for _ in range(max(1,w*h//350)):
   lo=5 if n in NEW else ow+5
   if lo>w-7:continue
   x=rng.randint(lo,w-7);y=rng.randint(5,h-7)
   if any(abs(x-a)+abs(y-b)<9 for a,b in reefs+occupied):continue
   if any(values[(y+dy)*w+x+dx]!=water for dy in range(2) for dx in range(2)):continue
   for dy in range(2):
    for dx in range(2):values[(y+dy)*w+x+dx]=rs[dy*2+dx]
   reefs.append((x,y))
  open_edges={d:set() for d in ['up','down','left','right']}
  for c in m['connections']:
   if c['direction'] not in open_edges:continue
   other=next(mm for mm in maps.values() if mm['id']==c['map']);ol=layouts[other['layout']]
   size=SIZES.get(other['name'],[ol['width'],ol['height']]);d=c['direction'];length=size[0 if d in ['up','down'] else 1];limit=w if d in ['up','down'] else h
   open_edges[d].update(range(max(0,c['offset']),min(limit,c['offset']+length)))
  for y in range(h):
   for x in range(w):
    closed=(x<2 and y not in open_edges['left']) or (x>=w-2 and y not in open_edges['right']) or (y<2 and x not in open_edges['up']) or (y>=h-2 and x not in open_edges['down'])
    if closed:values[y*w+x]=rs[y%2*2+x%2]
  assert all(e['x']<w and e['y']<h for key in ['object_events','warp_events','coord_events','bg_events'] for e in m[key]),n
  assert w<=127 and h<=127, (n,'signed native warp coordinates')
  assert (w+15)*(h+14)<=10240, (n,'native map buffer capacity')
  l.update(width=w,height=h);stage(l['blockdata_filepath'],struct.pack('<'+'H'*len(values),*values))
  if n in NEW:stage(l['border_filepath'],struct.pack('<4H',*rs))
  terrain.append(dict(map=n,width=w,height=h,water_fraction=sum(v in [water,0x114F] for v in values)/len(values),events_unchanged=n not in NEW,deep_water_coordinates_preserved=True))
 # Update the Sevii side of every changed seam, including formerly closed rock banks.
 for n in ['JourneyWorldSea00','JourneyWorldSea01','JourneyWorldSea02','JourneyWorldSea03','JourneyWorldSea04','JourneyWorldSea05','JourneyWorldSea06','JourneyWorldSea07','JourneyWorldSea08','JourneyWorldSea09','JourneyFuchsiaSea']:
  m=maps[n];l=layouts[m['layout']];w,h=l['width'],l['height'];vals=list(struct.unpack('<'+'H'*(w*h),checked(l['blockdata_filepath'])))
  frlg=l['layout_version']=='frlg';water=0x112B if frlg else 0x1170;rs=[0x510,0x511,0x518,0x519] if frlg else rocks
  for y in range(h):
   for x in range(w):
    if min(x,y,w-1-x,h-1-y)>=2:continue
    sides=[]
    if x<2:sides.append(('left',y))
    if x>=w-2:sides.append(('right',y))
    if y<2:sides.append(('up',x))
    if y>=h-2:sides.append(('down',x))
    changed_sides={name:['down'] if name in ['JourneyWorldSea01','JourneyWorldSea02','JourneyWorldSea03'] else ['up','down'] for name in maps if name.startswith('JourneyWorldSea')}
    changed_sides.update(JourneyWorldSea00=['left','down'],JourneyWorldSea04=['left','up','down'],JourneyWorldSea06=['left','up'],JourneyFuchsiaSea=['right','down'])
    sides=[(d,c) for d,c in sides if d in changed_sides[n]]
    if not sides:continue
    opened=False
    for d,coord in sides:
     for c in m['connections']:
      if c['direction']!=d:continue
      other=next((mm for mm in maps.values() if mm['id']==c['map']),None)
      if other is None:
       # Top-row native island harbors retain their original coastal opening.
       if c['map'].endswith('ISLAND_HARBOR') or c['map']=='MAP_VERMILION_CITY':
        if c['offset']<=coord<c['offset']+(80 if c['map']=='MAP_VERMILION_CITY' else 17):opened=True
       continue
      ol=layouts[other['layout']];length=ol['width'] if d in ['up','down'] else ol['height']
      if c['offset']<=coord<c['offset']+length:opened=True
    if opened and vals[y*w+x] in rs:vals[y*w+x]=water
    elif not opened:vals[y*w+x]=rs[y%2*2+x%2]
  stage(l['blockdata_filepath'],struct.pack('<'+'H'*len(vals),*vals))
 # Ever Grande's outer rim has elevated water (3), not sea-level water (1).
 # Preserve its terrain and expose a visible rock bank instead of an invisible wall.
 l=layouts[maps['JourneyEverGrandeBackSouthSea']['layout']];w=l['width'];path=l['blockdata_filepath'];v=list(struct.unpack('<'+'H'*(len(outputs[path])//2),outputs[path]))
 for y in range(16,32):
  for x in range(2):v[y*w+x]=rocks[y%2*2+x]
 stage(path,struct.pack('<'+'H'*len(v),*v))
 # Close obsolete Route131's south spur, including its alternate Sky Pillar layout.
 for lid in ['LAYOUT_ROUTE131','LAYOUT_ROUTE131_SKY_PILLAR']:
  l=layouts[lid];w,h=l['width'],l['height'];vals=list(struct.unpack('<'+'H'*(w*h),checked(l['blockdata_filepath'])))
  for y in range(h-2,h):
   for x in range(48,w):vals[y*w+x]=rocks[y%2*2+x%2]
  stage(l['blockdata_filepath'],struct.pack('<'+'H'*len(vals),*vals))
 for n,m in maps.items():
  p=f'data/maps/{n}/map.json';raw=encode(m)
  if n in NEW or raw!=checked(p):stage(p,raw)
 stage('data/layouts/layouts.json',encode(layout_data))
 rectangles=[]
 for n,(x,y) in POSITIONS.items():
  l=layouts[maps[n]['layout']];rectangles.append(dict(map=n,x=x,y=y,width=l['width'],height=l['height']))
 for i,a in enumerate(rectangles):
  for b in rectangles[i+1:]:
   assert min(a['x']+a['width'],b['x']+b['width'])<=max(a['x'],b['x']) or min(a['y']+a['height'],b['y']+b['height'])<=max(a['y'],b['y']),(a,b,'overlapping maps')
 for link in links:
  a=next(r for r in rectangles if r['map']==link['source']);b=next(r for r in rectangles if r['map']==link['destination']);d=link['direction']
  assert (a['x']+a['width']==b['x']) if d=='right' else (a['y']+a['height']==b['y']),link
 for row in terrain:
  l=layouts[maps[row['map']]['layout']];v=struct.unpack('<'+'H'*(len(outputs[l['blockdata_filepath']])//2),outputs[l['blockdata_filepath']])
  row['water_fraction']=sum(t in [0x1170,0x112B,0x114F] for t in v)/len(v)
 report=dict(status='continuous_eastern_ocean_candidate',source_commit=PIN,rectangles=rectangles,connections=links,terrain=terrain,route131_south_spur_removed=True,ever_grande_terrain_and_events_preserved=True,no_added_transition_warps=True,full_campaign_validated=False,incoming_connection_upper_bound_exclusive=True,elevated_ever_grande_bank=dict(map='JourneyEverGrandeBackSouthSea',x=[0,1],y=[16,31],native_terrain_unchanged=True),original_sha256=originals,prepared_sha256={p:hashlib.sha256(v).hexdigest() for p,v in outputs.items()},preserved_native_sha256=preserved)
 for p,raw in outputs.items():(source/p).parent.mkdir(parents=True,exist_ok=True);(source/p).write_bytes(raw)
 marker.write_bytes(encode(report));return report

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True);print(json.dumps(prepare(p.parse_args().source),indent=2))
