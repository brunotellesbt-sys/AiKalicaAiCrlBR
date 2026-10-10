"""Controller Surf roundtrip Cinnabar–western Hoenn–Dewford; setup is a fixture."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
prefix=(ROOT/'tools/hoenn/validate_eastern_union.py').read_text().split('exec(compile((ROOT/')[0]
prefix=prefix.replace("names=[r['map'] for r in report['rectangles']]", "names=['Route19_Frlg','Route20_Frlg','CinnabarIsland_Frlg','JourneyCinnabarSouthSea','JourneyWestRiver','JourneyRustboroCoast','JourneyRustboroGate','JourneyDewfordCoast','JourneyDewfordGate','Route115','Route105','Route106','DewfordTown']")
exec(compile(prefix,str(ROOT/'tools/hoenn/validate_eastern_union.py'),'exec'))
exec(compile((ROOT/'tools/hoenn/native_water_walk.py').read_text(),str(ROOT/'tools/hoenn/native_water_walk.py'),'exec'))
passable={n:{i for i in p if not blocks[n][2][i]&0xC00 and blocks[n][2][i]>>12==1 and water_behaviors[behaviors[n][i]]} for n,p in passable.items()}
def target(name):
 w,h,_=blocks[name];i=min(passable[name],key=lambda i:abs(i%w-w//2)+abs(i//w-h//2));return(name,i%w,i//w)
start=('Route19_Frlg',15,50);g,n=map_id(start[0]);script(b'\x39'+bytes([g,n,255])+struct.pack('<HH',*start[1:])+b'\x27\x6b\x02',frames=240);step(120)
native('SetPlayerAvatarTransitionFlags',8);step(30)
legs=[]
for name in ['Route20East','Route20West','CinnabarIsland_Frlg','JourneyCinnabarSouthSea','JourneyWestRiver','JourneyRustboroCoast','JourneyRustboroGate','Route115','JourneyRustboroCoast','JourneyDewfordCoast','JourneyDewfordGate','Route105','Route106','DewfordTown','JourneyDewfordCoast','JourneyRustboroCoast','JourneyWestRiver','JourneyCinnabarSouthSea','CinnabarIsland_Frlg','Route20East','Route19_Frlg']:
 if name in ['Route20East','Route20West']:
  goal=('Route20_Frlg',110 if name=='Route20East' else 10,10)
 else:goal=target(name) if name!=start[0] else start
 walk(goal);assert lib.read8(s['gPlayerAvatar'])&8;legs.append(dict(map=name,position=list(position())));picture('western-'+name);print('Western Surf arrival:',name,position(),flush=True)
assert location()==map_id(start[0]) and position()==start[1:]
lib.stop()
(args.output/'western-coast.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),continuous_surf_roundtrip=True,no_midtrip_fixture_warps=True,legs=legs,transitions=transitions,initial_party_and_location_are_fixtures=True,full_campaign_playthrough=False),indent=2)+'\n')
