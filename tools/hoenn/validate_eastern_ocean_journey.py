"""Continuous native Vermilion-Sevii-Pacifidlog-eastern Hoenn round trip.
Initial party/location and earlier story state are fixtures; no mid-route
warps or direct trainer entries. Wild encounters and battle balance excluded.
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
names = ['VermilionCity_Frlg', 'Route127', 'Route131', 'PacifidlogTown',
         'JourneyHoennMiddleSea', 'JourneyPacifidlogSea']
names += ['JourneyWorldSea%02d' % i for i in range(8)]
names += ['JourneyWorldLane' + i for i in ['10', '11', '20', '21']]
names += [n + 'Island_Harbor_Frlg' for n in ['One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven']]
constants = sorted(set(re.findall(r'\bTRAINER_[A-Z0-9_]+', '\n'.join(
    (source / 'data/maps' / n / 'scripts.inc').read_text() for n in ['Route127', 'Route131']))))
compiled = subprocess.run([str(ROOT / '.local/arm-gcc/usr/bin/arm-none-eabi-gcc'), '-S',
    '-iquote', str(source / 'include'), '-x', 'c', '-', '-o', '-'],
    input='#include "constants/opponents.h"\nconst unsigned sea_trainers[] = {' + ','.join(constants) + '};',
    text=True, capture_output=True, check=True).stdout
allowed = set(int(n) for n in re.findall(r'\.word\s+(\d+)', compiled.split('sea_trainers:', 1)[1].split('.size', 1)[0]))
allowed.update(t['id'] for t in stories['trainers'])
walk_layout_overrides = {'Route131': 'LAYOUT_ROUTE131_SKY_PILLAR'}
walk_prefix = 'eastern-ocean-journey'
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
    walk(goal)
    checks.append(dict(label=label, goal=list(goal), position_changes=walked - first))
    picture(label + '-arrival')
    print('Continuous ocean leg:', label, position(), flush=True)

start = ('VermilionCity_Frlg', 20, 20)
warp(*start); native('SetPlayerAvatarTransitionFlags', 1); step(30)
leg('vermilion-east-shore', ('VermilionCity_Frlg', 34, 30))
leg('vermilion-surf-channel', ('VermilionCity_Frlg', 34, 38))
leg('vermilion-sea', ('JourneyWorldSea00', 10, 20))
checkpoint('vermilion-sea-surf')
for number, name in enumerate(['One', 'Two', 'Three'], 1):
    leg(name.lower() + '-island-harbor', (name + 'Island_Harbor_Frlg', 8, 4))
checkpoint('three-island-land')
leg('two-island-sea-return', ('JourneyWorldSea02', 8, 30))
leg('five-island-harbor', ('FiveIsland_Harbor_Frlg', 8, 4))
leg('four-island-harbor', ('FourIsland_Harbor_Frlg', 8, 4))
checkpoint('four-island-land')
leg('six-island-harbor', ('SixIsland_Harbor_Frlg', 8, 4))
leg('seven-island-harbor', ('SevenIsland_Harbor_Frlg', 8, 4))
leg('pacifidlog-sea', ('JourneyPacifidlogSea', 6, 20))
checkpoint('pacifidlog-sea-surf')
leg('route131', ('Route131', 50, 25))
checkpoint('route131-alternate-layout-surf')
leg('pacifidlog-town', ('PacifidlogTown', 8, 18))
checkpoint('pacifidlog-town-land')
leg('pacifidlog-sea-return', ('JourneyPacifidlogSea', 6, 20))
leg('six-island-sea-return', ('JourneyWorldSea06', 10, 20))
leg('four-island-sea-return', ('JourneyWorldSea04', 10, 20))
leg('hoenn-middle-sea', ('JourneyHoennMiddleSea', 20, 12))
leg('route127', ('Route127', 75, 42))
checkpoint('route127-surf')
leg('hoenn-middle-sea-return', ('JourneyHoennMiddleSea', 20, 12))
leg('four-island-sea-final', ('JourneyWorldSea04', 10, 20))
leg('one-island-sea-return', ('JourneyWorldSea01', 10, 20))
leg('vermilion-sea-return', ('JourneyWorldSea00', 10, 20))
leg('vermilion-surf-channel-return', ('VermilionCity_Frlg', 34, 38))
leg('vermilion-east-shore-return', ('VermilionCity_Frlg', 34, 30))
leg('vermilion-town-return', start)
checkpoint('vermilion-return-land')
assert state()['mode'] == 1
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
print('Continuous eastern ocean round trip and eight Continues passed', flush=True)
