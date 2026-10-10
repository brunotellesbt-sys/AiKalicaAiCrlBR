"""Controller Surf roundtrip and northern wooden bridge; initial setup is a fixture."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
prefix=(ROOT/'tools/hoenn/validate_eastern_union.py').read_text().split('exec(compile((ROOT/')[0]
prefix=prefix.replace("names=[r['map'] for r in report['rectangles']]", "names=list(dict.fromkeys([r['map'] for r in report['rectangles']]+[r['map'] for r in json.loads((source/'.journey-kanto-open-sea').read_text())['rectangles']]))")
exec(compile(prefix,str(ROOT/'tools/hoenn/validate_eastern_union.py'),'exec'))
exec(compile((ROOT/'tools/hoenn/native_water_walk.py').read_text(),str(ROOT/'tools/hoenn/native_water_walk.py'),'exec'))
def warp(name,x,y):
 g,n=map_id(name);script(b'\x39'+bytes([g,n,255])+struct.pack('<HH',x,y)+b'\x27\x6b\x02',frames=240);step(120)
 assert location()==(g,n) and position()==(x,y)
water_passable={n:{i for i in p if not blocks[n][2][i]&0xC00 and blocks[n][2][i]>>12==1 and water_behaviors[behaviors[n][i]]} for n,p in passable.items()}
land_passable={n:{i for i in p if not water_behaviors[behaviors[n][i]]} for n,p in passable.items()}
passable=water_passable
start=('Route19_Frlg',15,50);warp(*start);native('SetPlayerAvatarTransitionFlags',8);step(30)
legs=[]
for n,x,y in [('JourneyFuchsiaSea',20,10),('JourneyKantoSouthWestSea',25,25),('JourneyKantoSouthSea',60,25),('JourneyRoute13Coast',40,25),('JourneyLavenderApproach',25,35),('JourneyRoute12Shipyard',45,45),('JourneyRoute12OuterSea',30,35),('JourneyRoute12Shipyard',45,45),('JourneyLavenderApproachSouth',25,30),('JourneyWorldSea02',35,20),('JourneyWorldSea01',35,20),('JourneyWorldSea00',35,20),('JourneyKantoCoastalBand',40,10),start]:
 walk((n,x,y));assert lib.read8(s['gPlayerAvatar'])&8;legs.append(dict(map=n,position=list(position())));picture('coast-'+n);print('Surf coast arrival:',n,position(),flush=True)
assert location()==map_id(start[0]) and position()==start[1:]
# Independent land placement, followed only by D-pad movement along the bridge.
passable=land_passable;warp('Route12_Frlg',17,53);native('SetPlayerAvatarTransitionFlags',1);step(30)
bridge=[]
for n,x,y in [('JourneyRoute12OuterSea',5,54),('JourneyRoute12OuterSea',5,59),('JourneyRoute12Shipyard',5,3),('JourneyRoute12Shipyard',5,29),('JourneyRoute12OuterSea',5,54),('Route12_Frlg',17,53)]:
 walk((n,x,y));assert not lib.read8(s['gPlayerAvatar'])&8;bridge.append(dict(map=n,position=list(position())));picture('bridge-'+n)
lib.stop()
(args.output/'kanto-open-sea.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),surf_legs=legs,pedestrian_bridge_legs=bridge,continuous_surf_roundtrip=True,no_midtrip_fixture_warps=True,bridge_walk_without_surf=True,initial_party_positions_and_defeated_trainer_flags_are_fixtures=True,full_campaign_playthrough=False),indent=2)+'\n')
