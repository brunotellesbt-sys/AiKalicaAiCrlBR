"""Reproduce League-gated cave doors and walk their corrected entrances.
Badge/story state, party and initial placement before each cave are fixtures.
Door inputs, walking, landmark discovery and Save/Continue are native.
"""
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
exec(compile((ROOT / 'tools/hoenn/validate_team_missions.py').read_text().split('\nwins, completed =')[0],
             str(ROOT / 'tools/hoenn/validate_team_missions.py'), 'exec'))
for f in kanto_flags + hoenn_flags: rawflag(f, False)
compiled = subprocess.run([str(ROOT / '.local/arm-gcc/usr/bin/arm-none-eabi-gcc'), '-S',
    '-iquote', str(source / 'include'), '-x', 'c', '-', '-o', '-'], input='''
#include "constants/flags.h"
const unsigned cave_flags[] = {FLAG_SYS_GAME_CLEAR, FLAG_KANTO_GAME_CLEAR, FLAG_LANDMARK_DESERT_UNDERPASS};
''', text=True, capture_output=True, check=True).stdout
cave_flags = [int(n) for n in re.findall(r'\.word\s+(\d+)', compiled.split('cave_flags:', 1)[1].split('.size', 1)[0])]
assert len(cave_flags) == 3, cave_flags
hoenn_clear, kanto_clear, landmark = cave_flags
for f in cave_flags: rawflag(f, False)
names = ['Route103', 'AlteringCave', 'Route114_FossilManiacsTunnel', 'DesertUnderpass']
allowed = set()
walk_prefix = 'ordinary-caves'
exec(compile((ROOT / 'tools/hoenn/native_water_walk.py').read_text(),
             str(ROOT / 'tools/hoenn/native_water_walk.py'), 'exec'))
candidate = (source / '.journey-cave-access').exists()
rows, saves = [], []

def state():
    return dict(map=by_location[location()], position=list(position()),
                mode=lib.read8(s['gPlayerAvatar']) & 25,
                kanto_badges=native('JourneyGymBadgeCount', 1),
                hoenn_badges=native('JourneyGymBadgeCount', 0),
                kanto_champion=flag(kanto_clear), hoenn_champion=flag(hoenn_clear),
                underpass_discovered=flag(landmark), special_capture_unlocked=bool(native('JourneySpecialUnlocked')))

def checkpoint(label):
    before = state()
    assert before['kanto_badges'] == before['hoenn_badges'] == 0
    assert not before['kanto_champion'] and not before['hoenn_champion']
    assert not before['special_capture_unlocked']
    assert native('TrySavingData', 0, max_frames=6000) == 1
    assert native('LoadGameSave', 0, max_frames=6000) == 1
    lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
    step(1500); finish()
    after = state(); assert before == after, (label, before, after)
    saves.append(dict(label=label, before=before, after=after))
    picture(label + '-after-continue')

for exterior, start, approach, interior, goal in [
    ('Route103', (45, 7), (45, 7), 'AlteringCave', (18, 21)),
    ('Route114_FossilManiacsTunnel', (6, 6), (6, 3), 'DesertUnderpass', (10, 11))]:
    if exterior == 'Route114_FossilManiacsTunnel':
        vars_text = (source / 'include/constants/vars.h').read_text()
        fossil_state = int(re.search(r'^#define\s+VAR_FOSSIL_MANIAC_STATE\s+(0x\w+)', vars_text, re.M)[1], 16)
        native('VarSet', fossil_state, 1) # Exercise the original cave-in conversation.
    warp(exterior, *start)
    native('SetPlayerAvatarTransitionFlags', 1); step(30)
    refresh_loaded_warp_tiles()
    if candidate:
        walk((interior, *goal))
        picture(interior + '-native-entry')
        checkpoint(interior + '-inside')
        if interior == 'DesertUnderpass':
            assert flag(landmark), 'Native landmark flag missing'
            assert native('VarGet', fossil_state) == 2
        walk((exterior, *start))
        checkpoint(interior + '-returned')
        # Continue must not cause an OnLoad script to reseal the door.
        walk((interior, *goal))
        walk((exterior, *start))
        rows.append(dict(cave=interior, native_entry_exit_and_reentry=True))
    else:
        walk((exterior, *approach))
        step(100, 64); step(30); finish()
        assert location() == map_id(exterior) and position() == approach, (exterior, location(), position())
        assert native('MapGridGetCollisionAt', approach[0] + 7, approach[1] + 6) != 0
        picture(interior + '-baseline-closed')
        rows.append(dict(cave=interior, native_closed_door_reproduced=True))
    print('Native ordinary cave:', interior, candidate, flush=True)
assert not wins
lib.stop()
result = dict(passed=True, candidate=candidate,
              rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              rows=rows, save_continue=saves, position_changes=walked, transitions=transitions,
              initial_badges_story_party_and_two_approach_positions_are_fixtures=True,
              no_internal_warps_during_each_cave_route=True,
              native_underpass_landmark=candidate, no_trainer_battles=True,
              wild_encounters_disabled=True, full_campaign_playthrough=False, balance_validated=False)
(args.output / 'cave-access.json').write_text(json.dumps(result, indent=2) + '\n')
print('Native ordinary cave access checks passed', flush=True)
