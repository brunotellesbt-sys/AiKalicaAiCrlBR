"""Controller-driven shipyard approach and Surf journey; initial state is a fixture."""
from pathlib import Path
import hashlib
import json
ROOT=Path(__file__).resolve().parents[2]
prefix=(ROOT/'tools/hoenn/validate_eastern_union.py').read_text().split('seams=[];cliffs=[]')[0]
prefix=prefix.replace("names=[r['map'] for r in report['rectangles']]", "names=[r['map'] for r in report['rectangles']]+['JourneyRoute12Shipyard','JourneyRoute12OuterSea','Route12_Frlg','Route11_Frlg','VermilionCity_Frlg','TwoIsland_Harbor_Frlg','JourneyRoute12SailorsLodge']")
exec(compile(prefix,str(ROOT/'tools/hoenn/validate_eastern_union.py'),'exec'))
walk_prefix='route12-shipyard'
# The removed Vermilion crossing must be physically closed.
warp('VermilionCity_Frlg',34,37);native('SetPlayerAvatarTransitionFlags',8);step(30);step(180,128)
assert location()==map_id('VermilionCity_Frlg')
picture('vermilion-old-exit-closed')
start=('Route12_Frlg',17,104)
warp(*start);native('SetPlayerAvatarTransitionFlags',1);step(30)
legs=[]
for goal in [
 ('JourneyRoute12Shipyard',2,44),('JourneyRoute12Shipyard',5,38),
 ('JourneyRoute12Shipyard',20,44),('JourneyRoute12OuterSea',10,20),
 ('TwoIsland_Harbor_Frlg',6,10),('JourneyRoute12OuterSea',10,20),
 ('JourneyRoute12Shipyard',55,52),('JourneyWorldSea02',40,12),
 ('JourneyWorldSea01',12,20),('JourneyWorldSea00',12,20),
 ('JourneyHoennNorthSea',100,20),('JourneyEverGrandeBackSouthSea',10,34),
 ('JourneyHoennNorthSea',100,20),('JourneyWorldSea00',12,20),
 ('JourneyWorldSea01',12,20),('JourneyWorldSea02',40,12),
 ('JourneyRoute12Shipyard',55,52),('JourneyRoute12Shipyard',8,44),start]:
 walk(goal);legs.append(dict(map=goal[0],position=list(position())));picture('route12-leg-'+str(len(legs)))
 print('Shipyard arrival:',goal,flush=True)
 if goal==('JourneyRoute12Shipyard',20,44):
  before=(location(),position(),lib.read8(s['gPlayerAvatar'])&25)
  assert native('TrySavingData',0,max_frames=6000)==1;step(60)
  assert native('LoadGameSave',0,max_frames=6000)==1
  lib.write32(s['gMain']+4,s['CB2_ContinueSavedGame']|1);step(1500);finish()
  assert before==(location(),position(),lib.read8(s['gPlayerAvatar'])&25)
  picture('shipyard-continue')
walk(('JourneyRoute12Shipyard',11,39));step(24,64);step(180);finish()
assert location()==map_id('JourneyRoute12SailorsLodge'),('Lodge entrance',location(),position())
picture('sailors-lodge-interior')
# Native indoor exit: room arrival lies immediately above the welcome mat.
step(48,128);step(180);finish()
assert location()==map_id('JourneyRoute12Shipyard'),('Lodge exit',location(),position())
picture('sailors-lodge-return');walk(start)
assert location()==map_id(start[0]) and position()==start[1:]
lib.stop()
(args.output/'route12-shipyard.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),continuous_roundtrip=True,legs=legs,transitions=transitions,vermilion_old_exit_physically_closed=True,foot_access_from_existing_route12_walkway=True,save_continue_on_pier=True,sailors_lodge_native_entry_and_exit=True,no_midroute_warps=True,initial_party_and_trainer_flags_are_fixtures=True,wild_encounters_disabled=True,full_campaign_playthrough=False),indent=2)+'\n')
print('Shipyard foot approach, Surf roundtrip and Continue passed',flush=True)
