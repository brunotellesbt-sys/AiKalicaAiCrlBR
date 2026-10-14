"""Check each added native cave floor and open the five reported cave maps."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
exec(compile((ROOT/'tools/hoenn/validate_world_map.py').read_text().split('\nchecks=[]')[0],__file__,'exec'))
native('VarSet',0x40FE,7)
r=json.loads((source/'.journey-navigated-sea-atlas').read_text());rows=[]
for c in r['native_cave_points']:
 name=c['map'];g,num=map_id(name);lib.write8(save()+4,g);lib.write8(save()+5,num)
 i=native('JourneyWorldMapPlayerPoint');p=native('JourneyWorldMapPosition');at=s['sWorldPoints']+i*12
 assert lib.read16(at)==(g<<8)|num,(name,i)
 assert [p&255,p>>8]==c['position'],(name,p,c)
 rows.append(dict(map=name,point_index=i,position=c['position']))
for name in ['GraniteCave_1F','DiglettsCave_B1F_Frlg','RockTunnel_1F_Frlg','ShoalCave_LowTideEntranceRoom','SeafoamIslands_1F_Frlg']:
 warp(name,10,10);ptr=open_map();picture(name+'-correct-map-point');press(2);wait_for(lambda:callback()==s['CB2_Overworld']);step(120);press(2)
lib.stop()
(args.output/'native-cave-points.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),checks=rows,all_registered_cave_floors_have_own_point=True,actual_map_ui=True,initial_location_party_and_flags_are_fixtures=True),indent=2)+'\n')
print('Native cave floors passed',len(rows),flush=True)
