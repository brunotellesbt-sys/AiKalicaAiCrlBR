"""Walk the beach, embark, cross both regional seams, and reach Fallarbor.

Only the starting party/story/placement is a fixture. All travel, obstacles,
Surf prompts, disembarking and Save/Continue run in the native game.
"""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/record_fallarbor_river.py').read_text().split('\nvideo=ROOT')[0]
exec(compile(bootstrap,__file__,'exec'))
observed=[]
last_observed_map=start[0]
def walk_observer(before,after):
    global last_observed_map
    name,x,y=after
    w,h,tiles=blocks[name]
    if not (0<=x<w and 0<=y<h):return
    surfing=bool(lib.read8(s['gPlayerAvatar'])&8)
    if surfing:
        assert water_behaviors[behaviors[name][y*w+x]],('Surf on dry land',after)
    # A map ID can change before the object coordinates settle. Observe the
    # first valid position in the new map, retaining the previous valid map.
    if last_observed_map!=name:
        observed.append(dict(source=last_observed_map,destination=name,surf=surfing))
        last_observed_map=name

def assert_ground():
    step(60)
    assert idle() and lib.read8(s['gPlayerAvatar'])&25==1
    n=by_location[location()];x,y=position();w=blocks[n][0]
    assert blocks[n][2][y*w+x]>>12==3
    assert native('MapGridGetMetatileIdAt',x+7,y+7)==blocks[n][2][y*w+x]&1023

beach_checks=[]
for target in [(12,9),(9,6),(12,3),(16,6),(12,8)]:
    walk(('JourneyWestRiver',*target));assert_ground()
    beach_checks.append(list(target))
picture('walkable-beach')
walk(('JourneyWestRiver',25,7));step(60)
assert surf_prompts and lib.read8(s['gPlayerAvatar'])&8
walk(('JourneyCinnabarSouthSea',12,46));step(60)
assert lib.read8(s['gPlayerAvatar'])&8;picture('north-regional-seam')
walk(('JourneyWestRiver',25,7))
walk(('JourneyRustboroCoast',24,2));step(60)
assert lib.read8(s['gPlayerAvatar'])&8;picture('south-regional-seam')
walk(('JourneyWestRiver',25,7))
walk(('JourneyWestRiver',2,6));step(60)
before=position();step(90,32);step(60)
assert position()==before,'The outside rock limit was crossed'
picture('whole-rocks-block-outside')
walk(('Route114',4,17));step(60)
before=position();step(90,128);step(60)
assert position()==before,'Surf passed under the bank trees'
picture('complete-trees-block-surf')
walk(('Route114',20,13));assert_ground();picture('landing-on-dry-ground')
saved={n:passable[n] for n in ['Route114','FallarborTown']}
for n in saved:passable[n]={i for i in passable[n] if not water_behaviors[behaviors[n][i]]}
walk(('FallarborTown',14,8));assert_ground();picture('fallarbor-on-foot')
for n,valid in saved.items():passable[n]=valid
walk(('JourneyWestRiver',12,8));assert_ground();picture('beach-native-return')
assert native('TrySavingData',0,max_frames=6000)==1
assert native('LoadGameSave',0,max_frames=6000)==1
lib.write32(s['gMain']+4,s['CB2_ContinueSavedGame']|1);step(1500);finish()
assert by_location[location()]=='JourneyWestRiver' and position()==(12,8)
assert_ground();picture('beach-saved-and-continued')
expected={('JourneyWestRiver',n) for n in ['JourneyCinnabarSouthSea','JourneyRustboroCoast','Route114']}
expected|={(b,a) for a,b in list(expected)}
if (source/'.journey-extra-gyms').exists():
    coasts=json.loads((source/'.journey-extra-gyms').read_text())['coastal_fixes']['geography']['repaired_links']
    for link in coasts:
        pair=link['source'],link['destination']
        if pair not in expected:continue
        expected.discard(pair);expected.discard(pair[::-1])
        chain=[pair[0],*link['segments'],pair[1]]
        for a,b in zip(chain,chain[1:]):expected.add((a,b));expected.add((b,a))
assert expected<={(r['source'],r['destination']) for r in observed if r['surf']},observed
result=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
    beach_walk_targets=beach_checks,beach_walkable_on_foot=True,native_surf_prompt=True,
    native_disembark_before_city=True,city_reachable_on_foot=True,return_to_beach_on_foot=True,
    rock_limit_blocks_controller=True,complete_tree_overhang_blocks_surf=True,
    northern_southern_and_river_connections_bidirectional=True,seams=observed,
    surfing_observed_only_on_water=True,native_save_continue_preserves_land_and_foot_state=True,
    no_midroute_warps_or_coordinate_writes=True,initial_party_story_and_departure_are_fixtures=True)
lib.stop();(args.output/'fallarbor-physics.json').write_text(json.dumps(result,indent=2)+'\n')
print('Native Fallarbor river and beach physics passed',flush=True)
