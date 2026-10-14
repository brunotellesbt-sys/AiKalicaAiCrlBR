"""Check native access, whole boat collisions and visible rival approach objects.

Travel, encounter flags and party are fixtures. Walking and door transitions
use controller input; this is not a complete campaign playthrough.
"""
import hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_trainer_levels.py'),'exec'))
from render_sea_maps import MapRenderer
renderer=MapRenderer(source)
native('VarSet',0x40FE,7)
ports=[];info=(source/'src/data/object_events/object_event_graphics_info.h').read_text();pointers=(source/'src/data/object_events/object_event_graphics_info_pointers.h').read_text()
for name in ['MossdeepCity','CinnabarIsland_Frlg','PalletTown_Frlg','Route19_Frlg','Route25_Frlg','PacifidlogTown','SootopolisCity','JourneyRoute12Shipyard','DewfordTown','Route104','BattleFrontier_OutsideWest','SlateportCity_Harbor','LilycoveCity_Harbor','VermilionCity_Frlg']+[i+'Island_Harbor_Frlg' for i in ['One','Two','Three','Four','Five','Six','Seven']]:
 m=json.loads((source/f'data/maps/{name}/map.json').read_text());l=layouts[m['layout']];boats=[o for o in m['object_events'] if o['graphics_id'] in ['OBJ_EVENT_GFX_MR_BRINEYS_BOAT','OBJ_EVENT_GFX_SEAGALLOP','OBJ_EVENT_GFX_JOURNEY_SUBMARINE','OBJ_EVENT_GFX_SS_TIDAL','OBJ_EVENT_GFX_JOURNEYSEVIIBOAT','OBJ_EVENT_GFX_JOURNEYPETALBURGBOAT'] and str(o['flag'])=='0'];captains=[o for o in m['object_events'] if o['script'].startswith(('Journey_FerryPort','LavenderNetwork_Service'))]
 assert len(captains)==1 if name!='JourneyRoute12Shipyard' else True
 captain=captains[0] if captains else None;wx,wy=(captain['x'],captain['y']-1) if captain else (30,17);warp(name,wx,wy);step(90);footprints=[]
 for o in boats:
  symbol=re.search(r'\['+o['graphics_id']+r'\]\s*=\s*&([A-Za-z0-9_]+)',pointers)[1];body=re.search(r'const struct ObjectEventGraphicsInfo '+symbol+r'\s*=\s*\{(.*?)\};',info,re.S)[1];w=int(re.search(r'\.width\s*=\s*(\d+)',body)[1]);h=int(re.search(r'\.height\s*=\s*(\d+)',body)[1]);cells=[]
  dx,dy=renderer.sprite_offset(o['graphics_id'])
  if dx:
   sp=renderer.sprite(o['graphics_id'],0);ox=o['x']*16+8-w//2+dx;oy=o['y']*16+16-h+dy
   occupied=sorted({((ox+x)//16,(oy+y)//16) for y in range(h) for x in range(w) if sp.getpixel((x,y))[3]})
   table=re.search(r'\.subspriteTables\s*=\s*sOamTables_(\w+)',body)[1]
   assert lib.read8(s['sOamTable_'+table+'_0'])==((-w//2+dx)&255),('Native sprite offset differs',name)
  else:occupied=[(xx,yy) for yy in range((o['y']*16+16-h)//16,o['y']+1) for xx in range((o['x']*16+8-w//2)//16,(o['x']*16+8+w//2-1)//16+1)]
  for xx,yy in occupied:
   assert native('MapGridGetCollisionAt',xx+7,yy+7)!=0,(name,'Surf through boat',xx,yy)
   behavior=native('MapGridGetMetatileBehaviorAt',xx+7,yy+7);assert native('MetatileBehavior_IsSurfableWaterOrUnderwater',behavior),(name,'Boat on land',xx,yy,behavior)
   cells.append([xx,yy])
  footprints.append(cells)
 if name=='CinnabarIsland_Frlg':
  # Assert complete source/native metatiles at the repaired marine border.
  for yy in [18,19]:
   for xx in range(8,14):assert native('MapGridGetMetatileIdAt',xx+7,yy+7)==0x12B
  for dy in range(2):
   for dx in range(2):assert native('MapGridGetMetatileIdAt',29+dx,25+dy)==[0x110,0x111,0x118,0x119][dy*2+dx]
  resident=next(o for o in m['object_events'] if o['x']==12 and o['y']==14);assert not resident['script'].startswith('Journey_FerryPort')
  assert native('MapGridGetCollisionAt',19,21)==0
 if name in ['MossdeepCity','CinnabarIsland_Frlg','OneIsland_Harbor_Frlg','Route25_Frlg','SootopolisCity']:picture(name+'-port')
 ports.append(dict(map=name,boat_footprints=footprints,world_ferry_captains=len(captains)))
# Real exits from the new houses and shared Sevii harbor.
doors=[]
for name,x,y,target,key in [('MossdeepCity',4,31,'JourneyMossdeepSailorsLodge',64),('CinnabarIsland_Frlg',9,15,'JourneyCinnabarSailorsLodge',64),('OneIsland_Harbor_Frlg',8,3,'OneIsland_Frlg',64)]:
 warp(name,x,y);step(30)
 for _ in range(80):
  step(4,key)
  if location()==map_id(target):break
 assert location()==map_id(target),(name,'Door/harbor warp failed',location(),position())
 step(160);doors.append(dict(source=name,destination=target,controller_transition=True))
# Every added native cottage supports real entry and its matching exit.
for cottage in json.loads((source/'.journey-port-orientation-finish').read_text())['cottages']:
 name=cottage['map'];x,y=cottage['door'];target=cottage['interior'];warp(name,x,y+1);step(30)
 for _ in range(100):
  step(4,64)
  if location()==map_id(target):break
 assert location()==map_id(target),(name,'Cottage entry failed',position())
 step(160);im=json.loads((source/f'data/maps/{target}/map.json').read_text());exit=im['warp_events'][0];warp(target,exit['x'],exit['y']-1);step(30)
 for _ in range(100):
  step(4,128)
  if location()==map_id(name):break
 assert location()==map_id(name),(name,'Cottage exit failed',position())
 step(160);assert abs(position()[0]-x)<=1 and abs(position()[1]-y)<=1,(name,'Wrong cottage return warp',position(),[x,y])
 doors.append(dict(source=name,destination=target,controller_transition=True,controller_return=True))
# Each origin's captain remains usable, with actual player access to the pier.
for name,start,end,key in [('MossdeepCity',(4,31),(4,32),128),('CinnabarIsland_Frlg',(10,15),(10,16),128),('Route25_Frlg',(62,10),(63,10),16),('OneIsland_Harbor_Frlg',(7,4),(7,5),128),('BattleFrontier_OutsideWest',(20,68),(20,71),128),('PalletTown_Frlg',(12,18),(12,19),128)]:
 warp(name,*start);step(30)
 for _ in range(60):
  if position()==end:break
  step(1,key)
 assert position()==end,(name,'Pier not walkable',position(),end)
 step(15)
# Capture the accepted Spiritomb site, without changing its landscape.
workshop=json.loads((source/'.journey-special-encounter-workshop').read_text());well=next(o for o in workshop['placed_objects'] if o['script']=='JourneySpecial_SpiritombWell')
warp(well['map'],well['x'],well['y']+1);step(90);picture('spiritomb-well')
# Observe actors created by the regular route hook, then their one-tile approach.
heroes=[];rawflag(lib.read16(s['gBadgeFlags'])-7,True);native('VarSet',0x40FE,0);native('VarSet',0x40FF,0)
for route,x,y in [('Route4_Frlg',30,8),('Route6_Frlg',12,20)]:
 warp(route,x,y);step(100)
 group,num=map_id(route);oid=native('GetObjectEventIdByLocalIdAndMap',240,num,group);assert oid<16,(route,'Rival not spawned',position())
 obj=s['gObjectEvents']+oid*36;initial=[lib.read16(obj+12)-7,lib.read16(obj+14)-7];current=[lib.read16(obj+16)-7,lib.read16(obj+18)-7];player=list(position())
 assert 2<=sum(abs(a-b) for a,b in zip(initial,player))<=4,(route,initial,current,player)
 assert sum(abs(a-b) for a,b in zip(current,player))==1,(route,initial,current,player)
 assert not(lib.read8(obj+1)&0x60),(route,'Hidden/offscreen actor')
 picture(route+'-visible-rival');heroes.append(dict(map=route,initial=initial,after_approach=current,player=player,object_id=oid,visible=True))
 native('JourneyCrossoverFinish');native('VarSet',0x40FE,7)
 # End the unfinished dialogue fixture before the next independent route.
 for _ in range(10):press(2)
 native('VarSet',0x40FE,0)
lib.stop();(args.output/'ports-and-actors.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),ports=ports,doors=doors,crossover_visible_approaches=heroes,all_boat_footprints_blocked=True,cinnabar_complete_rocks_and_resident_off_roof=True,native_controller_access=True,initial_state_and_travel_are_fixtures=True,full_campaign_playthrough=False),indent=2)+'\n')
