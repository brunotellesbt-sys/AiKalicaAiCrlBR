"""Continuous native Cinnabar-western Hoenn-Dewford round trip.
Initial party/location and earlier story state are fixtures; no mid-route
warps or direct trainer entries. Wild encounters and battle balance excluded.
"""
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_team_missions.py').read_text().split('\nwins, completed =')[0]
# The old mission-fixture preflight predates mandatory native episodes. This
# walker checks travel; the current gate matrix validates those episodes separately.
for line in ['assert pending(True) == 7 and pending(False) == 12',
             'assert not done(True) and not done(False)',
             "doors = [door_probe('CinnabarIsland_Frlg', True), door_probe('FortreeCity', True)]"]:
    assert bootstrap.count(line)==1
    bootstrap=bootstrap.replace(line,'')
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_team_missions.py'),'exec'))
for f in kanto_flags + hoenn_flags: rawflag(f, False)
names = ['CinnabarIsland_Frlg', 'JourneyCinnabarSouthSea', 'JourneyWestRiver',
         'JourneyRustboroCoast', 'JourneyDewfordCoast', 'JourneyDewfordGate',
         'Route105', 'Route106', 'DewfordTown', 'Route114', 'JourneyRustboroGate', 'Route115', 'RustboroCity']
constants = sorted(set(re.findall(r'\bTRAINER_[A-Z0-9_]+', '\n'.join(
    (source / 'data/maps' / n / 'scripts.inc').read_text() for n in ['Route105', 'Route106', 'Route114', 'Route115']))))
compiled = subprocess.run([str(ROOT / '.local/arm-gcc/usr/bin/arm-none-eabi-gcc'), '-S',
    '-iquote', str(source / 'include'), '-x', 'c', '-', '-o', '-'],
    input='#include "constants/opponents.h"\nconst unsigned sea_trainers[] = {' + ','.join(constants) + '};',
    text=True, capture_output=True, check=True).stdout
allowed = set(int(n) for n in re.findall(r'\.word\s+(\d+)', compiled.split('sea_trainers:', 1)[1].split('.size', 1)[0]))
allowed.update(t['id'] for t in stories['trainers'])
walk_prefix = 'ocean-journey'
exec(compile((ROOT / 'tools/hoenn/native_water_walk.py').read_text(),
             str(ROOT / 'tools/hoenn/native_water_walk.py'), 'exec'))
checks, saves = [], []

def state():
    return dict(map=by_location[location()], position=list(position()), mode=lib.read8(s['gPlayerAvatar']) & 25,
                kanto_badges=native('JourneyGymBadgeCount', 1), hoenn_badges=native('JourneyGymBadgeCount', 0),
                special_capture_unlocked=bool(native('JourneySpecialUnlocked')),
                frlg_format=bool(lib.read8(s['isFrlg'])))

def checkpoint(label):
    before = state()
    assert before['kanto_badges'] == before['hoenn_badges'] == 0
    assert not before['special_capture_unlocked']
    assert native('TrySavingData', 0, max_frames=6000) == 1
    assert native('LoadGameSave', 0, max_frames=6000) == 1
    lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
    step(1500); finish()
    after = state(); assert before == after, (label, before, after)
    saves.append(dict(label=label, before=before, after=after))
    picture(label + '-after-continue')

def leg(label, goal):
    first = walked
    name,x,y=goal
    if name.startswith('Journey'):
        w,h,values=blocks[name]
        if values[y*w+x] not in [0x112B,0x1170]:
            candidates=[(abs(xx-x)+abs(yy-y),yy,xx) for yy in range(3,h-3) for xx in range(3,w-3) if values[yy*w+xx] in [0x112B,0x1170]]
            _,y,x=min(candidates);goal=(name,x,y)
    walk(goal)
    checks.append(dict(label=label, goal=list(goal), position_changes=walked - first))
    picture(label + '-arrival')
    print('Continuous ocean leg:', label, position(), flush=True)

start = ('CinnabarIsland_Frlg', 11, 12)
warp(*start); native('SetPlayerAvatarTransitionFlags', 1); step(30)
leg('cinnabar-departure', ('JourneyCinnabarSouthSea', 10, 12))
checkpoint('cinnabar-south-surf')
leg('western-river', ('JourneyWestRiver', 6, 7))
leg('route114-lake', ('Route114', 4, 14))
checkpoint('route114-lake-surf')
leg('return-from-lake', ('JourneyWestRiver', 6, 7))
leg('rustboro-coast', ('JourneyRustboroCoast', 6, 60))
checkpoint('rustboro-coast-surf')
leg('rustboro-gate', ('Route115', 4, 36))
leg('rustboro-town', ('RustboroCity', 21, 38))
checkpoint('rustboro-town-land')
leg('return-rustboro-gate', ('Route115', 4, 36))
leg('return-from-rustboro', ('JourneyRustboroCoast', 6, 60))
leg('dewford-coast', ('JourneyDewfordCoast', 46, 42))
leg('dewford-gate', ('Route105', 4, 42))
leg('dewford-town', ('DewfordTown', 7, 13))
checkpoint('dewford-town-land')
leg('return-route105', ('Route105', 4, 42))
leg('return-dewford-coast', ('JourneyDewfordCoast', 46, 42))
leg('return-rustboro-coast', ('JourneyRustboroCoast', 6, 60))
leg('return-western-river', ('JourneyWestRiver', 6, 7))
leg('return-cinnabar-sea', ('JourneyCinnabarSouthSea', 10, 12))
leg('return-cinnabar-town', start)
checkpoint('cinnabar-return-land')
assert state()['mode'] == 1
assert len(transitions) == 24, transitions
lib.stop()
(args.output / 'ocean-journey.json').write_text(json.dumps(dict(
    passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
    continuous_roundtrip=True, start=list(start), end=list(start), maps=names, legs=checks,
    position_changes=walked, transitions=transitions, surf_prompts=surf_prompts,
    save_continue=saves, native_trainer_battles=wins,
    no_midroute_warps_or_direct_trainer_scripts=True,
    initial_party_position_and_prior_story_states_are_fixtures=True,
    trainer_stats_and_healing_are_fixtures=True, wild_encounters_disabled=True,
    full_campaign_playthrough=False, balance_validated=False), indent=2) + '\n')
print('Continuous ocean round trip and six Continues passed', flush=True)
