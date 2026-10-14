"""Observe original cave player points; unresolved locations remain findings."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_world_map.py').read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap,__file__,'exec'))
native('VarSet',0x40FE,7)
rows=[]
for name in ['GraniteCave_1F','DiglettsCave_B1F_Frlg','RockTunnel_1F_Frlg','ShoalCave_LowTideEntranceRoom','SeafoamIslands_1F_Frlg']:
 warp(name,10,10);i=native('JourneyWorldMapPlayerPoint');p=native('JourneyWorldMapPosition');at=s['sWorldPoints']+i*12
 actual=lib.read16(at);matches=actual==((map_id(name)[0]<<8)|map_id(name)[1])
 rows.append(dict(map=name,selected_point=i,selected_map_id=actual,marker=[p&255,p>>8],has_own_point=matches))
 ptr=open_map();picture(name+'-map-point');press(2);wait_for(lambda:callback()==s['CB2_Overworld']);step(120);press(2)
 print(rows[-1],flush=True)
lib.stop()
(args.output/'native-cave-findings.json').write_text(json.dumps(dict(completed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),checks=rows,unresolved=[r['map'] for r in rows if not r['has_own_point']],travel_party_and_progress_are_fixtures=True,not_a_passing_release_proof=True),indent=2)+'\n')
