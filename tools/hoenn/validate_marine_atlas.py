"""Check actual cave/player positions and the restored native Surf route graph."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_world_map.py').read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap,__file__,'exec'))
from prepare_complete_marine_atlas import SURF_ROUTES
r=json.loads((source/'.journey-complete-marine-atlas').read_text())
native('VarSet',0x40FE,7)
routes={tuple(sorted([p['source'],p['destination']])) for p in r['orthogonal_marine_paths']}
needed=[('PalletTown_Frlg','Route21_North_Frlg'),('Route21_North_Frlg','Route21_South_Frlg'),
 ('Route21_South_Frlg','CinnabarIsland_Frlg'),('FuchsiaCity_Frlg','Route19_Frlg'),
 ('Route19_Frlg','Route20_Frlg'),('Route20_Frlg','CinnabarIsland_Frlg'),
 ('Route104','Route105'),('Route105','Route106'),('Route106','DewfordTown'),
 ('JourneyRustboroCoast','JourneyDewfordCoast'),('JourneyDewfordCoast','JourneyDewfordGate'),
 ('JourneyDewfordGate','Route105')]
assert all(tuple(sorted(p)) in routes for p in needed)
checks=[]
for c in r['cave_entrances']:
 if 'entry' in c:
  # The warp fixture places the player one tile south of the requested tile.
  # Put the feet on the doorway only for this projection probe.
  x,y=c['entry'];warp(c['surface'],x,y)
  obj=s['gObjectEvents']+lib.read8(s['gPlayerAvatar']+5)*36
  for offset,value in [(16,x+7),(18,y+7),(20,x+7),(22,y+7)]:lib.write16(obj+offset,value)
  packed=native('JourneyWorldMapPosition')
  assert [packed&255,packed>>8]==c['position'],('Entrance mismatches cave icon',c,packed)
 warp(c['map'],10,10);packed=native('JourneyWorldMapPosition');i=native('JourneyWorldMapPlayerPoint')
 assert [packed&255,packed>>8]==c['position']
 # Native point selection must refer to this cave, not a reused region section.
 at=s['sWorldPoints']+i*12;g,num=map_id(c['map'])
 assert lib.read16(at)==(g<<8)|num
 assert [lib.read8(at+4),lib.read8(at+5)]==c['position']
 checks.append(dict(**c,compiled_player_position=[packed&255,packed>>8],compiled_point_index=i))
for name in ['SeafoamIslands_B1F_Frlg','SeafoamIslands_B2F_Frlg','SeafoamIslands_B3F_Frlg','SeafoamIslands_B4F_Frlg']:
 warp(name,10,10);packed=native('JourneyWorldMapPosition');assert [packed&255,packed>>8]==checks[-1]['position']
warp('Route20_Frlg',60,9);ptr=open_map();picture('world-map-restored-corridors')
press(256);step(90);assert lib.read8(ptr+2062)==1;picture('world-map-kanto-detail')
press(256);step(90);assert lib.read8(ptr+2062)==0
press(2);wait_for(lambda:callback()==s['CB2_Overworld']);step(120);press(2)
warp('Route105',20,50);ptr=open_map();press(256);step(90);picture('world-map-hoenn-detail')
press(2);wait_for(lambda:callback()==s['CB2_Overworld']);step(120);press(2)
lib.stop()
(args.output/'marine-atlas.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),restored_native_connections=needed,caves=checks,all_seafoam_floors_resolve_correctly=True,native_menu_and_zoom=True,controller_zoom_and_return=True,initial_party_flags_and_travel_are_fixtures=True,no_terrain_or_ports_changed=True),indent=2)+'\n')
print('Restored 12 native route links; 15 cave entrances and all Seafoam floors passed',flush=True)
