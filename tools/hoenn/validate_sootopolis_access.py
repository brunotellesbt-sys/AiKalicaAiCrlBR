"""Enter Sootopolis by native Dive, visit both shores, and return to Route126.
Initial origin, badges, story, party and ocean position are fixtures.
All travel after that placement uses native inputs, including Save/Continue.
"""
from pathlib import Path
import hashlib
import json
import struct

ROOT = Path(__file__).resolve().parents[2]
exec(compile((ROOT / 'tools/hoenn/validate_team_missions.py').read_text().split('\nwins, completed =')[0],
             str(ROOT / 'tools/hoenn/validate_team_missions.py'), 'exec'))
assert (source / '.journey-water-continue').exists()
for f in kanto_flags + hoenn_flags: rawflag(f, False)
native('ScriptSetMonMoveSlot', 0, 291, 2)
lib.write8(lib.read32(s['gSaveBlock2Ptr']) + abi[45], abi[46])
for name in ['FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN', 'FLAG_SYS_WEATHER_CTRL']:
    rawflag(abi[111] if name == 'FLAG_SYS_WEATHER_CTRL' else flag_id(name), False)
native('VarSet', 0x409F, 0)
names = ['Route126', 'Underwater_Route126', 'Underwater_SootopolisCity', 'SootopolisCity',
         'SootopolisCity_PokemonCenter_1F', 'SootopolisCity_House1']
allowed = set() # This access route must not need a trainer battle.
walk_prefix = 'sootopolis'
exec(compile((ROOT / 'tools/hoenn/native_water_walk.py').read_text(),
             str(ROOT / 'tools/hoenn/native_water_walk.py'), 'exec'))
checks = []

def state():
    return dict(map=by_location[location()], position=list(position()),
                avatar_mode=lib.read8(s['gPlayerAvatar']) & 25,
                kanto_badges=native('JourneyGymBadgeCount', 1),
                hoenn_badges=native('JourneyGymBadgeCount', 0),
                kyogre_escaped=flag(flag_id('FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN')))

def checkpoint(label, mode):
    before = state()
    assert before['avatar_mode'] == mode, before
    assert before['kanto_badges'] == before['hoenn_badges'] == 0
    assert not before['kyogre_escaped']
    assert native('TrySavingData', 0, max_frames=6000) == 1
    assert native('LoadGameSave', 0, max_frames=6000) == 1
    lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
    step(1500); finish()
    after = state()
    assert before == after, (label, before, after)
    checks.append(dict(label=label, before=before, after=after))
    picture(label + '-after-continue')
    print('Native Sootopolis checkpoint:', label, after, flush=True)

def change_water(target, emerge=False):
    assert native('TrySetDiveWarp') == (1 if emerge else 2)
    if emerge: press(2)
    for _ in range(160):
        press(1)
        if location() == map_id(target): break
    step(120); finish()
    assert location() == map_id(target), (target, location(), position())
    picture('native-water-' + target)

# Single travel fixture, on the deep-water ring outside Sootopolis.
warp('Route126', 45, 66)
native('SetPlayerAvatarTransitionFlags', 8); step(30)
change_water('Underwater_Route126')
walk(('Underwater_SootopolisCity', 9, 7))
checkpoint('underwater-sootopolis-entry', 16)
change_water('SootopolisCity', emerge=True)
checkpoint('sootopolis-lake-arrival', 8)
walk(('SootopolisCity_House1', 4, 5))
checkpoint('sootopolis-west-house', 1)
walk(('SootopolisCity_PokemonCenter_1F', 7, 7))
checkpoint('sootopolis-east-pokemon-center', 1)
walk(('SootopolisCity', 29, 53))
change_water('Underwater_SootopolisCity')
walk(('Underwater_Route126', 45, 66))
checkpoint('underwater-route126-return', 16)
change_water('Route126', emerge=True)
checkpoint('route126-surface-return', 8)
assert not wins
lib.stop()
result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              native_dive_and_resurface=True, native_walking_and_surf=True,
              position_changes=walked, transitions=transitions, surf_prompts=surf_prompts,
              save_continue=checks, no_trainer_battle_required=True,
              no_internal_warps_after_initial_ocean_fixture=True,
              initial_story_badges_origin_party_ocean_are_fixtures=True,
              wild_encounters_disabled=True, full_campaign_playthrough=False, balance_validated=False)
(args.output / 'sootopolis-access.json').write_text(json.dumps(result, indent=2) + '\n')
print('Native Sootopolis access and return passed', flush=True)
