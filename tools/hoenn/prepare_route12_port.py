"""Extend Route12's wooden piers into a shipyard and replace Vermilion's Surf exit."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
from prepare_early_story_tools import PRECEDING
LAYER='route12-port'
NAME='JourneyRoute12Shipyard'

def prepare(source):
 source=Path(source);marker=source/('.journey-'+LAYER)
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in (r['prepared_sha256']|r['preserved_native_sha256']).items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  return r
 expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
 for layer in PRECEDING+['early-story-tools','mandatory-native-missions','sixteen-badge-leagues','rusturf-reunion','sea-landscapes','eastern-sea-union','ever-grande-entrance']:
  expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 originals={};outputs={};preserved={}
 def checked(p):
  raw=(source/p).read_bytes();h=hashlib.sha256(raw).hexdigest();assert h==expected[p],p
  preserved[p]=h;return raw
 def stage(p,raw):
  if p in expected:originals[p]=hashlib.sha256(checked(p)).hexdigest()
  outputs[p]=raw;preserved.pop(p,None)
 def encode(d):return (json.dumps(d,indent=2)+'\n').encode()
 ld=json.loads(checked('data/layouts/layouts.json'));layouts={l['id']:l for l in ld['layouts']}
 maps={n:json.loads(checked(f'data/maps/{n}/map.json')) for n in ['Route12_Frlg','VermilionCity_Frlg','JourneyWorldSea00','JourneyWorldSea02','TwoIsland_Harbor_Frlg']}
 route=maps['Route12_Frlg'];city=maps['VermilionCity_Frlg'];oldsea=maps['JourneyWorldSea00'];sea=maps['JourneyWorldSea02']
 city['connections']=[c for c in city['connections'] if c['map']!=oldsea['id']]
 oldsea['connections']=[c for c in oldsea['connections'] if c['map']!=city['id']]
 city['object_events']=[e for e in city['object_events'] if e['script']!='Journey_FerryPort0']
 port=copy.deepcopy(sea);port.update(id='MAP_JOURNEYROUTE12SHIPYARD',name=NAME,layout='LAYOUT_JOURNEYROUTE12SHIPYARD',region_map_section=route['region_map_section'],connections=[dict(map=route['id'],direction='left',offset=-60),dict(map=sea['id'],direction='down',offset=-1)],object_events=[],warp_events=[],coord_events=[],bg_events=[])
 route['connections'].append(dict(map=port['id'],direction='right',offset=60))
 upper=copy.deepcopy(port);upper.update(id='MAP_JOURNEYROUTE12OUTERSEA',name='JourneyRoute12OuterSea',layout='LAYOUT_JOURNEYROUTE12OUTERSEA',object_events=[],connections=[dict(map=route['id'],direction='left',offset=0),dict(map=port['id'],direction='down',offset=0)])
 route['connections'].append(dict(map=upper['id'],direction='right',offset=0))
 port['connections'].append(dict(map=upper['id'],direction='up',offset=0))
 sea['connections']=[c for c in sea['connections'] if c['map']!=maps['TwoIsland_Harbor_Frlg']['id']]
 sea['connections'].append(dict(map=port['id'],direction='up',offset=1))
 island=maps['TwoIsland_Harbor_Frlg']
 for c in island['connections']:
  if c['map']==sea['id']:c['map']=upper['id']
 upper['connections'].append(dict(map=island['id'],direction='up',offset=24))
 rl=layouts[route['layout']];layout=copy.deepcopy(rl);layout.update(id=port['layout'],name=NAME+'_Layout',width=64,height=60,blockdata_filepath=f'data/layouts/{NAME}/map.bin',border_filepath=f'data/layouts/{NAME}/border.bin');ld['layouts'].append(layout)
 rocks=[0x510,0x511,0x518,0x519];water=0x112B;wood=0x32F3
 values=[water]*(64*60)
 # A compact central square, a complete wood/ sand/grass border and branching berths.
 for x0,x1,y0,y1 in [(7,20,33,46),(0,31,43,46),(3,6,32,53),(6,7,38,41),(19,31,38,41),(19,22,46,52),(6,14,50,53),(22,30,49,52),(3,9,32,35),(3,6,28,35),(0,9,28,31),(6,7,32,46),(17,20,27,33),(17,26,27,30)]:
  for y in range(y0,y1):
   for x in range(x0,x1):values[y*64+x]=wood
 native_route=list(struct.unpack('<2880H',checked(rl['blockdata_filepath'])))
 # A small grassy island surrounds the entire facade by one tile.
 grass=native_route[87*24+13]
 for y in range(34,41):
  for x in range(8,17):values[y*64+x]=0x3115
 for y in range(35,40):
  for x in range(9,16):values[y*64+x]=grass
 # Irregular soil extensions: at most two tiles west and south, within the deck.
 for x,y in [(7,35),(7,36),(6,36),(6,37),(7,37),(7,38),(7,39),(7,40),(8,41),(9,41),(9,42),(10,41),(10,42),(11,41),(12,41),(13,41),(14,41),(14,42),(15,41),(16,41)]:
  values[y*64+x]=0x3115
 for x,y in [(8,36),(8,37),(8,38),(9,40),(10,40),(11,40),(12,40),(14,40)]:values[y*64+x]=grass
 # Copy the complete native fishing-house exterior, including its actual door.
 for dy in range(3):
  for dx in range(5):values[(36+dy)*64+10+dx]=native_route[(84+dy)*24+11+dx]
 port['warp_events']=[dict(x=11,y=38,elevation=3,dest_map='MAP_JOURNEYROUTE12SAILORSLODGE',dest_warp_id='1')]
 for y in range(60):
  for x in range(64):
   if x>=62:values[y*64+x]=rocks[y%2*2+x%2]
 stage(layout['blockdata_filepath'],struct.pack('<3840H',*values));stage(layout['border_filepath'],struct.pack('<4H',*rocks))
 ul=copy.deepcopy(layout);ul.update(id=upper['layout'],name='JourneyRoute12OuterSea_Layout',blockdata_filepath='data/layouts/JourneyRoute12OuterSea/map.bin',border_filepath='data/layouts/JourneyRoute12OuterSea/border.bin');ld['layouts'].append(ul)
 uv=[water]*(64*60)
 for y in range(60):
  for x in range(64):
   if (y<2 and not 24<=x<40) or x>=62:uv[y*64+x]=rocks[y%2*2+x%2]
 stage(ul['blockdata_filepath'],struct.pack('<3840H',*uv));stage(ul['border_filepath'],struct.pack('<4H',*rocks))
 stage('data/maps/JourneyRoute12OuterSea/scripts.inc',b'JourneyRoute12OuterSea_MapScripts::\n\t.byte 0\n')
 rv=list(struct.unpack('<2880H',checked(rl['blockdata_filepath'])));cleared=[]
 aquatic={0x510,0x511,0x518,0x519,0x5CB,0x5CC,0x5D3,0x5D4}
 for y in range(120):
  for x in range(24):
   i=y*24+x
   if rv[i] in aquatic or (y>=5 and x>=20):
    if rv[i]!=water:cleared.append([x,y,rv[i]])
    rv[i]=water
 # Extend an existing walkway horizontally into the shipyard's central slip.
 for y in range(103,106):
  for x in range(16,24):rv[y*24+x]=wood
 stage(rl['blockdata_filepath'],struct.pack('<2880H',*rv))
 sl=layouts[sea['layout']];sw,sh=sl['width'],sl['height'];sv=list(struct.unpack('<'+'H'*(sw*sh),checked(sl['blockdata_filepath'])))
 for y in range(2):
  for x in range(sw):sv[y*sw+x]=water if 2<=x<62 else rocks[y%2*2+x%2]
 stage(sl['blockdata_filepath'],struct.pack('<'+'H'*len(sv),*sv))
 # Close the former endpoints; Surf now joins through Route12's east coast.
 for n,m in [('VermilionCity_Frlg',city),('JourneyWorldSea00',oldsea)]:
  l=layouts[m['layout']];w,h=l['width'],l['height'];v=list(struct.unpack('<'+'H'*(w*h),checked(l['blockdata_filepath'])))
  for y in range(h-2,h) if n=='VermilionCity_Frlg' else range(2):
   for x in range(w):v[y*w+x]=rocks[y%2*2+x%2]
  stage(l['blockdata_filepath'],struct.pack('<'+'H'*len(v),*v))
 def npc(gfx,x,y,script,elevation=3):return dict(type='object',graphics_id=gfx,x=x,y=y,elevation=elevation,movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',script=script,flag='0')
 port['object_events']=[npc('OBJ_EVENT_GFX_SAILOR_FRLG',23,39,'Journey_FerryPort0'),npc('OBJ_EVENT_GFX_OLD_MAN_1',20,39,'JourneyShipyard_Worker'),npc('OBJ_EVENT_GFX_MACHOP',20,47,'JourneyShipyard_Worker'),npc('OBJ_EVENT_GFX_MR_BRINEYS_BOAT',9,54,'JourneyShipyard_Boat',1),npc('OBJ_EVENT_GFX_MR_BRINEYS_BOAT',25,53,'JourneyShipyard_Boat',1),npc('OBJ_EVENT_GFX_MR_BRINEYS_BOAT',1,27,'JourneyShipyard_Boat',1),npc('OBJ_EVENT_GFX_MR_BRINEYS_BOAT',2,40,'JourneyShipyard_Boat',1),npc('OBJ_EVENT_GFX_SEAGALLOP',24,26,'JourneyShipyard_Boat',1),npc('OBJ_EVENT_GFX_SEAGALLOP',28,37,'JourneyShipyard_Boat',1),npc('OBJ_EVENT_GFX_SEAGALLOP',30,55,'JourneyShipyard_Boat',1)]
 lodge=copy.deepcopy(json.loads(checked('data/maps/VermilionCity_PokemonFanClub_Frlg/map.json')))
 lodge.update(id='MAP_JOURNEYROUTE12SAILORSLODGE',name='JourneyRoute12SailorsLodge',region_map_section=route['region_map_section'],object_events=[npc('OBJ_EVENT_GFX_SAILOR_FRLG',5,4,'JourneyShipyard_LodgeKeeper',4),npc('OBJ_EVENT_GFX_SAILOR_FRLG',7,6,'JourneyShipyard_Worker'),npc('OBJ_EVENT_GFX_FISHERMAN',4,6,'JourneyShipyard_LodgeKeeper')],bg_events=[])
 for w in lodge['warp_events']:w.update(dest_map=port['id'],dest_warp_id='0')
 checked(layouts[lodge['layout']]['blockdata_filepath']);checked(layouts[lodge['layout']]['border_filepath'])
 stage('data/maps/JourneyRoute12SailorsLodge/map.json',encode(lodge))
 stage('data/maps/JourneyRoute12SailorsLodge/scripts.inc',b'JourneyRoute12SailorsLodge_MapScripts::\n\t.byte 0\nJourneyShipyard_LodgeKeeper::\n\tmsgbox JourneyShipyard_LodgeText, MSGBOX_NPC\n\tend\nJourneyShipyard_LodgeText::\n\t.string "Welcome to the sailors lodge!\\n"\n\t.string "Crews rest here between voyages.\\p"\n\t.string "The captain outside sails to SEVII\\n"\n\t.string "and HOENN. Surfers are welcome!$"\n')

 scripts=NAME+'_MapScripts::\n\t.byte 0\nJourneyShipyard_Worker::\n\tmsgbox JourneyShipyard_WorkerText, MSGBOX_NPC\n\tend\nJourneyShipyard_Boat::\n\tmsgbox JourneyShipyard_BoatText, MSGBOX_NPC\n\tend\nJourneyShipyard_WorkerText::\n\t.string "We repair ships at this yard.\\n"\n\t.string "The open sea leads to the islands\\n"\n\t.string "and the HOENN coast!$"\nJourneyShipyard_BoatText::\n\t.string "This ship is being repaired.$"\n'
 stage(f'data/maps/{NAME}/scripts.inc',scripts.encode())
 for n,m in [('Route12_Frlg',route),('VermilionCity_Frlg',city),('JourneyWorldSea00',oldsea),('JourneyWorldSea02',sea),(NAME,port),('JourneyRoute12OuterSea',upper),('TwoIsland_Harbor_Frlg',island)]:stage(f'data/maps/{n}/map.json',encode(m))
 stage('data/layouts/layouts.json',encode(ld))
 groups=json.loads(checked('data/maps/map_groups.json'));g=next(g for g in groups['group_order'] if 'JourneyWorldSea00' in groups[g]);groups[g].extend([NAME,'JourneyRoute12OuterSea','JourneyRoute12SailorsLodge']);stage('data/maps/map_groups.json',encode(groups))
 stage('data/event_scripts.s',checked('data/event_scripts.s')+f'\n\t.include "data/maps/{NAME}/scripts.inc"\n\t.include "data/maps/JourneyRoute12OuterSea/scripts.inc"\n\t.include "data/maps/JourneyRoute12SailorsLodge/scripts.inc"\n'.encode())
 scripts=checked('data/scripts/journey_campaign_gates.inc');old=b'warp MAP_VERMILION_CITY, 23, 31';assert scripts.count(old)==1
 stage('data/scripts/journey_campaign_gates.inc',scripts.replace(old,b'warp MAP_JOURNEYROUTE12SHIPYARD, 24, 39'))
 menu=checked('src/data/script_menu.h');old_menu=b'{COMPOUND_STRING("VERMILION")}'
 assert menu.count(old_menu)==1
 stage('src/data/script_menu.h',menu.replace(old_menu,b'{COMPOUND_STRING("ROUTE 12 YARD")}'))
 for p in ['src/journey_campaign_gates.c','src/journey_gym_scaling.c','data/maps/Route12_Frlg/scripts.inc','data/layouts/JourneyFuchsiaSea/map.bin','data/maps/JourneyFuchsiaSea/map.json']:
  checked(p)
 rects=[dict(map='TwoIsland_Harbor_Frlg',x=343,y=-133,width=17,height=13),dict(map='OneIsland_Harbor_Frlg',x=278,y=-13,width=17,height=13),dict(map='ThreeIsland_Harbor_Frlg',x=406,y=-13,width=17,height=13),dict(map='JourneyRoute12OuterSea',x=319,y=-120,width=64,height=60),dict(map=NAME,x=319,y=-60,width=64,height=60),dict(map='Route12_Frlg',x=295,y=-120,width=24,height=120),dict(map='Route11_Frlg',x=223,y=-60,width=72,height=20),dict(map='VermilionCity_Frlg',x=175,y=-70,width=48,height=40)]
 r=dict(layer=LAYER,rectangle_overrides=rects,cleared_rocks=cleared,old_vermilion_surf_exit_removed=True,fuchsia_unchanged=True,snorlax_and_route12_events_preserved=True,wooden_shipyard=True,compact_platform=True,grassy_house_border_tiles=1,sandy_grass_border_tiles=1,central_wooden_square_tiles=13,boats_docked_against_piers=True,northwest_berth=True,central_water_holes_filled=True,irregular_house_island=True,soil_extension_max_tiles=2,sailors_lodge=True,boat_count=7,larger_boats=3,ferry_arrival=[24,39],original_sha256=originals,prepared_sha256={p:hashlib.sha256(v).hexdigest() for p,v in outputs.items()},preserved_native_sha256=preserved)
 for p,v in outputs.items():(source/p).parent.mkdir(parents=True,exist_ok=True);(source/p).write_bytes(v)
 marker.write_bytes(encode(r));return r

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);print(json.dumps(prepare(p.parse_args().source),indent=2))
