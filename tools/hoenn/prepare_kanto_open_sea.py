"""Join the actual southern Kanto shoreline to Lavender's dock and eastern ocean."""
import argparse,copy,hashlib,json,struct,math,random
from pathlib import Path
from prepare_world_map import CHAIN as PREVIOUS
LAYER='kanto-open-sea';CHAIN=PREVIOUS+['world-map']
POSITIONS={
 'Route19_Frlg':(118,-60),'FuchsiaCity_Frlg':(106,-100),'Route15_Frlg':(154,-90),
 'Route14_Frlg':(226,-130),'Route13_Frlg':(250,-130),'Route12_Frlg':(298,-250),
 'LavenderTown_Frlg':(298,-270),'Route11_Frlg':(226,-190),'VermilionCity_Frlg':(178,-200),
 'JourneyFuchsiaSea':(142,-20),'JourneyRoute12Shipyard':(322,-190),'JourneyRoute12OuterSea':(322,-250),
 'JourneyWorldSea00':(190,0),'JourneyWorldSea01':(254,0),'JourneyWorldSea02':(318,0),'JourneyWorldSea03':(382,0),
 'JourneyKantoSouthWestSea':(142,-60),'JourneyKantoSouthSea':(190,-70),
 'JourneyRoute13Coast':(250,-110),'JourneyKantoCoastalBand':(190,-20),'JourneyLavenderApproach':(322,-130),
 'JourneyKantoEasternChannel':(295,-20),'JourneyOneIslandChannel':(278,-20),'OneIsland_Harbor_Frlg':(278,-13),'TwoIsland_Harbor_Frlg':(346,-263),'JourneyFuchsiaInlet':(154,-70),'JourneyLavenderApproachSouth':(322,-65)}
SIZES={'JourneyKantoSouthWestSea':(48,40),'JourneyKantoSouthSea':(132,50),'JourneyRoute13Coast':(72,40),'JourneyKantoCoastalBand':(88,20),'JourneyLavenderApproach':(64,65),'JourneyKantoEasternChannel':(27,20),'JourneyOneIslandChannel':(17,7),'JourneyFuchsiaInlet':(36,10),'JourneyLavenderApproachSouth':(64,65)}
LINKS=[('JourneyFuchsiaInlet','JourneyKantoSouthWestSea','down'),('JourneyFuchsiaInlet','JourneyKantoSouthSea','right'),('JourneyFuchsiaInlet','Route15_Frlg','up'),('JourneyFuchsiaInlet','FuchsiaCity_Frlg','left'),('JourneyKantoSouthWestSea','JourneyFuchsiaSea','down'),('JourneyKantoSouthWestSea','Route19_Frlg','left'),
 ('JourneyKantoSouthWestSea','JourneyKantoSouthSea','right'),('JourneyFuchsiaSea','JourneyKantoCoastalBand','right'),
 ('JourneyKantoSouthSea','JourneyKantoCoastalBand','down'),('JourneyKantoSouthSea','JourneyOneIslandChannel','down'),('JourneyKantoSouthSea','JourneyKantoEasternChannel','down'),('JourneyRoute13Coast','JourneyKantoSouthSea','down'),
 ('JourneyRoute13Coast','Route13_Frlg','up'),('JourneyRoute13Coast','Route14_Frlg','left'),
 ('JourneyKantoSouthSea','Route15_Frlg','up'),('JourneyKantoSouthSea','Route14_Frlg','up'),
 ('JourneyKantoCoastalBand','JourneyWorldSea00','down'),('JourneyKantoCoastalBand','JourneyWorldSea01','down'),('JourneyKantoEasternChannel','JourneyWorldSea01','down'),('JourneyKantoEasternChannel','JourneyWorldSea02','down'),
 ('JourneyKantoCoastalBand','JourneyOneIslandChannel','right'),('JourneyOneIslandChannel','JourneyKantoEasternChannel','right'),
 ('JourneyKantoCoastalBand','OneIsland_Harbor_Frlg','right'),('OneIsland_Harbor_Frlg','JourneyKantoEasternChannel','right'),('JourneyOneIslandChannel','OneIsland_Harbor_Frlg','down'),
 ('JourneyRoute12Shipyard','JourneyLavenderApproach','down'),('JourneyLavenderApproach','JourneyLavenderApproachSouth','down'),('JourneyLavenderApproachSouth','JourneyWorldSea02','down'),('JourneyLavenderApproachSouth','JourneyWorldSea03','down'),
 ('JourneyLavenderApproach','Route13_Frlg','left'),('JourneyLavenderApproach','JourneyRoute13Coast','left'),
 ('JourneyLavenderApproach','JourneyKantoSouthSea','left'),('JourneyLavenderApproachSouth','JourneyKantoSouthSea','left'),('JourneyLavenderApproachSouth','JourneyKantoEasternChannel','left')]
def prepare(source):
 source=Path(source);marker=source/('.journey-'+LAYER)
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in (r['prepared_sha256']|r['preserved_native_sha256']).items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  return r
 expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
 for layer in CHAIN:expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 originals={};preserved={};outputs={}
 def read(p):
  v=(source/p).read_bytes();h=hashlib.sha256(v).hexdigest();assert expected[p]==h,p;preserved[p]=h;return v
 def stage(p,v):
  if p in expected:originals[p]=hashlib.sha256(read(p)).hexdigest();preserved.pop(p,None)
  else:assert not (source/p).exists(),p
  outputs[p]=v if isinstance(v,bytes) else (json.dumps(v,indent=2)+'\n').encode()
 ld=json.loads(read('data/layouts/layouts.json'));ls={l['id']:l for l in ld['layouts']}
 maps={n:json.loads(read(f'data/maps/{n}/map.json')) for n in POSITIONS if n not in SIZES}
 maps['Route20_Frlg']=json.loads(read('data/maps/Route20_Frlg/map.json'))
 extra=[r['map'] for r in json.loads((source/'.journey-eastern-sea-union').read_text())['rectangles'] if 'WorldLane' in r['map'] or 'WorldFill' in r['map']]
 for n in extra:maps[n]=json.loads(read(f'data/maps/{n}/map.json'))
 template=maps['JourneyRoute12OuterSea'];tl=ls[template['layout']]
 for n,(w,h) in SIZES.items():
  assert (w+15)*(h+14)<=10240,(n,'Native map buffer exceeded')
  d=copy.deepcopy(template);d.update(id='MAP_'+n.upper(),name=n,layout='LAYOUT_'+n.upper(),connections=[],object_events=[],warp_events=[],coord_events=[],bg_events=[],region_map_section='MAPSEC_ROUTE_19' if 'West' in n else 'MAPSEC_LAVENDER_PORT')
  maps[n]=d;l=copy.deepcopy(tl);l.update(id=d['layout'],name=n+'_Layout',width=w,height=h,blockdata_filepath=f'data/layouts/{n}/map.bin',border_filepath=f'data/layouts/{n}/border.bin');ld['layouts'].append(l);ls[l['id']]=l
  stage(f'data/maps/{n}/scripts.inc',(n+'_MapScripts::\n\t.byte 0\n').encode())
 def size(n):l=ls[maps[n]['layout']];return l['width'],l['height']
 reverse={'up':'down','down':'up','left':'right','right':'left'};seams=[]
 for n in ['JourneyRoute12Shipyard','JourneyWorldSea02']:
  other='JourneyWorldSea02' if n=='JourneyRoute12Shipyard' else 'JourneyRoute12Shipyard'
  maps[n]['connections']=[c for c in maps[n]['connections'] if c['map']!=maps[other]['id']]
 for a,b,d in LINKS:
  ax,ay=POSITIONS[a];bx,by=POSITIONS[b];aw,ah=size(a);bw,bh=size(b)
  assert {'right':ax+aw==bx,'left':bx+bw==ax,'up':by+bh==ay,'down':ay+ah==by}[d],(a,b,d)
  off=by-ay if d in ['left','right'] else bx-ax
  for first,second,direction,offset in [(a,b,d,off),(b,a,reverse[d],-off)]:
   maps[first]['connections'].append(dict(map=maps[second]['id'],direction=direction,offset=offset))
  seams.append(dict(source=a,destination=b,direction=d,offset=off))
 # Coast borders are open only where a real map connection exists. Unconnected
 # edges use complete two-by-two aquatic rocks; the middle remains open sea.
 terrain={};rock_blocks={};landscape=[];rocks=[0x510,0x511,0x518,0x519];water=0x112B
 shore=[0x10C,0x10D,0x10E,0x114,0x115,0x116,0x11C,0x11D,0x11E]
 def decorate(n,v,w,h,actors=()):
  rng=random.Random(n+'-compact-islands');land=set();patches=[];grass=0
  occupied={(o['x']+dx,o['y']+dy) for o in actors if o['elevation']==1 for dx in range(-2,3) for dy in range(-2,3)}
  protected=lambda x,y:min(x,y,w-1-x,h-1-y)<2 or abs(x-w//2)<2 or (h>=12 and abs(y-h//2)<2)
  count=1 if h<12 else 2 if min(w,h)<25 else min(5,2+w*h//1900)
  for _ in range(400):
   if len(patches)>=count:break
   cx=rng.randrange(3,w-3);cy=rng.randrange(2,h-2)
   limit=min(5.2,(min(w,h)/2-3)/2) if h>=12 else 1.7
   radius=rng.uniform(max(1.6,limit*.75),max(1.7,limit));rx=radius*rng.uniform(.9,1.12);ry=radius*rng.uniform(.9,1.12);phase=rng.random()*6.28
   patch=set()
   for y in range(int(cy-ry-2),int(cy+ry+3)):
    for x in range(int(cx-rx-2),int(cx+rx+3)):
     angle=math.atan2(y-cy,x-cx);edge=1+.13*math.sin(3*angle+phase)+.07*math.sin(5*angle+phase)
     if ((x-cx)/rx)**2+((y-cy)/ry)**2<edge**2:patch.add((x,y))
   # Reject clipped islands wholesale: clipping created the repeated thin strips.
   if len(patch)<8 or any(protected(x,y) or (x,y) in occupied or v[y*w+x]!=water for x,y in patch):continue
   if any((x+dx,y+dy) in land for x,y in patch for dx in range(-2,3) for dy in range(-2,3)):continue
   patches.append(patch);land.update(patch)
   green=len(patches)%3!=0 or count==1
   for x,y in patch:
    row=0 if (x,y-1) not in patch else 2 if (x,y+1) not in patch else 1
    col=0 if (x-1,y) not in patch else 2 if (x+1,y) not in patch else 1
    v[y*w+x]=0x3000+shore[row*3+col]
    if green and all((x+dx,y+dy) in patch for dx,dy in [(0,-1),(0,1),(-1,0),(1,0)]):v[y*w+x]=0x3001;grass+=1
  assert land,('No compact island fits',n,w,h)
  for o in actors:
   if o['elevation']==3:v[o['y']*w+o['x']]=0x3115
  return land,grass,len(patches),protected,rng
 for n,(w,h) in SIZES.items():
  v=[water]*(w*h);stamps=[]
  def rock(x,y):
   cells=[(x+dx,y+dy) for dy in range(2) for dx in range(2)]
   if any(v[yy*w+xx]!=water for xx,yy in cells):return
   for i,(xx,yy) in enumerate(cells):v[yy*w+xx]=rocks[i]
   stamps.append(cells)
  for x in range(0,w-1,2):rock(x,0);rock(x,h-2)
  for y in range(2,h-3,2):rock(0,y);rock(w-2,y)
  land,grass,count,protected,rng=decorate(n,v,w,h)
  if w>=32 and h>=24:
   for _ in range(max(1,w*h//420)):
    x=rng.randrange(4,w-5);y=rng.randrange(4,h-5)
    if any(protected(x+dx,y+dy) or (x+dx,y+dy) in land for dx in range(-2,4) for dy in range(-2,4)):continue
    if any(abs(x-a)+abs(y-b)<7 for cells in stamps for a,b in cells):continue
    rock(x,y)
  rock_blocks[n]=stamps;landscape.append(dict(map=n,land_tiles=len(land),grass_tiles=grass,islands=count))
  terrain[n]=v;stage(ls[maps[n]['layout']]['border_filepath'],struct.pack('<4H',*rocks))
 def values(n):
  if n not in terrain:
   w,h=size(n);terrain[n]=list(struct.unpack('<'+'H'*(w*h),read(ls[maps[n]['layout']]['blockdata_filepath'])))
  return terrain[n]
 # Preserve existing beaches, trainers and scripts in the older narrow lanes,
 # and add small off-center sandbanks instead of leaving long empty corridors.
 all_headers={d['id']:d for row in json.loads((source/'.journey-eastern-sea-union').read_text())['rectangles'] if (d:=json.loads(read('data/maps/'+row['map']+'/map.json')))}
 all_headers.update({d['id']:d for d in maps.values()})
 for n in extra:
  w,h=size(n);v=values(n);d=maps[n];stamps=[]
  # These synthetic channels have no buildings: reshape their old repeated
  # sand rectangles while keeping every trainer, event and connection.
  for i,t in enumerate(v):
   if t>>12==3 and (t&1023 in shore or t==0x3001):v[i]=water
  added,grass,count,_,_=decorate(n,v,w,h,d['object_events'])
  open_edges={direction:set() for direction in ['up','down','left','right']}
  for c in d.get('connections') or []:
   direction=c['direction']
   if direction not in open_edges:continue
   dest=all_headers[c['map']];other=ls[dest['layout']];limit=h if direction in ['left','right'] else w;length=other['height'] if direction in ['left','right'] else other['width']
   open_edges[direction].update(range(max(0,c['offset']),min(limit,c['offset']+length)))
  def edge_rock(x,y,direction,span):
   cells=[(x+dx,y+dy) for dy in range(2) for dx in range(2)]
   if any(z in open_edges[direction] for z in span) or any(v[yy*w+xx]!=water for xx,yy in cells):return
   for i,(xx,yy) in enumerate(cells):v[yy*w+xx]=rocks[i]
   stamps.append(cells)
  for x in range(0,w-1,2):edge_rock(x,0,'up',[x,x+1]);edge_rock(x,h-2,'down',[x,x+1])
  for y in range(2,h-3,2):edge_rock(0,y,'left',[y,y+1]);edge_rock(w-2,y,'right',[y,y+1])
  rock_blocks[n]=stamps
  stage(ls[d['layout']]['border_filepath'],struct.pack('<4H',*rocks))
  landscape.append(dict(map=n,land_tiles=sum(t>>12==3 for t in v),added_sand_tiles=len(added),grass_tiles=grass,islands=count,water_fraction=round(v.count(water)/len(v),4),complete_rock_blocks=len(stamps),existing_trainers_and_missions_preserved=True))
 # Two complete native aquatic boulders separate the Route 20 sea basins.
 # Open a Surf passage without editing either Seafoam mountain or its beach.
 route20=values('Route20_Frlg');route20_width,_=size('Route20_Frlg')
 for x,y,pattern in [(78,10,[0x512,0x511,0x51A,0x519]),(79,12,rocks)]:
  for i,(dx,dy) in enumerate([(0,0),(1,0),(0,1),(1,1)]):
   assert route20[(y+dy)*route20_width+x+dx]==pattern[i],('Seafoam boulder mismatch',x,y,i)
   route20[(y+dy)*route20_width+x+dx]=water
 # Clear every connected sea border, while retaining terrestrial shoreline tiles.
 for a,b,d in LINKS:
  for n,other,direction in [(a,b,d),(b,a,reverse[d])]:
   if n not in SIZES and n not in ['JourneyFuchsiaSea','JourneyWorldSea00','JourneyWorldSea01','JourneyWorldSea02','JourneyWorldSea03']:continue
   w,h=size(n);ow,oh=size(other);x,y=POSITIONS[n];ox,oy=POSITIONS[other];v=values(n)
   begin,end=(max(0,oy-y),min(h,oy-y+oh)) if direction in ['left','right'] else (max(0,ox-x),min(w,ox-x+ow))
   for z in range(begin,end):
    for depth in [0,1]:
     xx,yy={'left':(depth,z),'right':(w-1-depth,z),'up':(z,depth),'down':(z,h-1-depth)}[direction]
     v[yy*w+xx]=water if ls[maps[n]['layout']].get('layout_version')=='frlg' else 0x1170
 # Opening a seam must remove entire boulders, never leave half a graphic.
 for n,stamps in rock_blocks.items():
  if n in extra:continue
  w,h=size(n);v=terrain[n]
  for cells in stamps:
   if any(v[y*w+x] not in rocks for x,y in cells):
    for x,y in cells:
     if v[y*w+x] in rocks:v[y*w+x]=water
  row=next(r for r in landscape if r['map']==n)
  row.update(water_fraction=round(v.count(water)/len(v),4),complete_rock_blocks=sum(all(v[y*w+x]==rocks[i] for i,(x,y) in enumerate(cells)) for cells in stamps))
 # A northern wooden approach joins the original Route12 bridge to the dock's
 # existing northwest pier. The approved central island, house and boats remain.
 wood=0x32F3
 for n,x0,x1,y0,y1 in [('Route12_Frlg',16,24,53,56),('JourneyRoute12OuterSea',0,7,53,56),('JourneyRoute12OuterSea',4,7,56,60),('JourneyRoute12Shipyard',4,7,0,28)]:
  v=values(n);w,h=size(n)
  for y in range(y0,y1):
   for x in range(x0,x1):v[y*w+x]=wood
 # Keep the old bottom gate open into the new approach. Existing dock terrain
 # already has water across this span; boats and the facade are untouched.
 for n,v in terrain.items():stage(ls[maps[n]['layout']]['blockdata_filepath'],struct.pack('<'+'H'*len(v),*v))
 for n,d in maps.items():stage(f'data/maps/{n}/map.json',d)
 groups=json.loads(read('data/maps/map_groups.json'));g=next(g for g in groups['group_order'] if 'JourneyRoute12Shipyard' in groups[g]);groups[g].extend(SIZES);stage('data/maps/map_groups.json',groups)
 stage('data/layouts/layouts.json',ld)
 stage('data/event_scripts.s',read('data/event_scripts.s')+''.join(f'\n\t.include "data/maps/{n}/scripts.inc"\n' for n in SIZES).encode())
 for p in ['src/journey_campaign_gates.c','src/journey_gym_scaling.c','data/maps/Route12_Frlg/scripts.inc']:read(p)
 # Exact edge positions must not overlap any native coastline or harbor.
 for i,a in enumerate(POSITIONS):
  ax,ay=POSITIONS[a];aw,ah=size(a)
  for b in list(POSITIONS)[i+1:]:
   bx,by=POSITIONS[b];bw,bh=size(b)
   assert not (max(ax,bx)<min(ax+aw,bx+bw) and max(ay,by)<min(ay+ah,by+bh)),('Overlapping maps',a,b)
 old_port=struct.unpack('<3840H',read(ls[maps['JourneyRoute12Shipyard']['layout']]['blockdata_filepath']))
 assert terrain['JourneyRoute12Shipyard'][28*64:]==list(old_port[28*64:])
 preserved.pop(ls[maps['JourneyRoute12Shipyard']['layout']]['blockdata_filepath'],None)
 r=dict(layer=LAYER,seafoam_surf_passage=dict(map="Route20_Frlg",removed_complete_boulders=[[78,10],[79,12]],mountains_beaches_and_entrances_preserved=True),landscape=landscape,complete_water_boulders=True,map_buffer_limit=10240,map_buffers_fit=True,no_rectangle_overlaps=True,approved_shipyard_core_preserved=True,rectangles=[dict(map=n,x=x,y=y,width=size(n)[0],height=size(n)[1]) for n,(x,y) in POSITIONS.items()],connections=seams,northern_pedestrian_bridge=True,vermilion_exit_not_restored=True,original_sha256=originals,preserved_native_sha256=preserved,prepared_sha256={p:hashlib.sha256(v).hexdigest() for p,v in outputs.items()})
 for p,v in outputs.items():(source/p).parent.mkdir(parents=True,exist_ok=True);(source/p).write_bytes(v)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);print(json.dumps(prepare(p.parse_args().source),indent=2))
