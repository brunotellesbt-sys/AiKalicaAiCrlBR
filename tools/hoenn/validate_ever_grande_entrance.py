"""Controller-driven Vermilion-Ever Grande roundtrip with the eastern reef open."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
prefix = (ROOT / 'tools/hoenn/validate_eastern_union.py').read_text().split('seams=[];cliffs=[]')[0]
prefix = prefix.replace("names=[r['map'] for r in report['rectangles']]", "names=[r['map'] for r in report['rectangles']]+['VermilionCity_Frlg']")
exec(compile(prefix, str(ROOT / 'tools/hoenn/validate_eastern_union.py'), 'exec'))
walk_prefix = 'ever-entrance'
start = ('VermilionCity_Frlg', 20, 20)
warp(*start); native('SetPlayerAvatarTransitionFlags', 1); step(30)
legs = []
for goal in [
 ('VermilionCity_Frlg',34,38), ('JourneyWorldSea00',10,20),
 ('JourneyHoennNorthSea',40,22), ('JourneyEverGrandeBackSouthSea',8,34),
 ('EverGrandeCity',34,74), ('EverGrandeCity',20,72), ('EverGrandeCity',20,68),
 ('EverGrandeCity',34,74), ('JourneyEverGrandeBackSouthSea',8,34),
 ('JourneyWorldSea00',10,20), start]:
    walk(goal)
    assert location() == map_id(goal[0]) and position() == goal[1:]
    legs.append(dict(map=goal[0], position=list(position())))
    picture('ever-entrance-leg-' + str(len(legs)))
    print('Vermilion / Ever Grande arrival:',goal,flush=True)
    if goal == ('EverGrandeCity',20,68):
        before = (location(), position(), lib.read8(s['gPlayerAvatar']) & 25)
        assert native('TrySavingData',0,max_frames=6000) == 1
        step(60)
        assert native('LoadGameSave',0,max_frames=6000) == 1
        lib.write32(s['gMain']+4,s['CB2_ContinueSavedGame']|1);step(1500);finish()
        assert before == (location(), position(), lib.read8(s['gPlayerAvatar']) & 25)
        picture('ever-entrance-continue')
assert location() == map_id(start[0]) and position() == start[1:]
lib.stop()
(args.output/'ever-grande-entrance.json').write_text(json.dumps(dict(
 passed=True, rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
 continuous_roundtrip=True, legs=legs, transitions=transitions,
 save_continue_at_waterfall_base=True, no_midroute_warps=True,
 defeated_trainer_and_party_fixtures=True, wild_encounters_disabled=True,
 full_campaign_playthrough=False),indent=2)+'\n')
print('Vermilion to eastern Ever Grande entrance and back passed',flush=True)
