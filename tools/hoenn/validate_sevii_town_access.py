"""Continuous native Sevii town access, nurse healing and return to Surf.
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
islands = ['One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven']
names = ['JourneyWorldSea%02d' % i for i in range(8)]
names += ['JourneyWorldLane' + i for i in ['10', '11', '20', '21']]
names += [i + 'Island' + suffix for i in islands
          for suffix in ['_Harbor_Frlg', '_Frlg', '_PokemonCenter_1F_Frlg']]
names += ['ThreeIsland_Port_Frlg']
constants = sorted(set(re.findall(r'\bTRAINER_[A-Z0-9_]+', '\n'.join(
    (source / 'data/maps' / n / 'scripts.inc').read_text() for n in ['ThreeIsland_Frlg']))))
compiled = subprocess.run([str(ROOT / '.local/arm-gcc/usr/bin/arm-none-eabi-gcc'), '-S',
    '-iquote', str(source / 'include'), '-x', 'c', '-', '-o', '-'],
    input='#include "constants/opponents.h"\nconst unsigned sea_trainers[] = {' + ','.join(constants) + '};',
    text=True, capture_output=True, check=True).stdout
allowed = set(int(n) for n in re.findall(r'\.word\s+(\d+)', compiled.split('sea_trainers:', 1)[1].split('.size', 1)[0]))
allowed.update(t['id'] for t in stories['trainers'])
walk_prefix = 'sevii-town-access'
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

compiled = subprocess.run([str(ROOT / '.local/arm-gcc/usr/bin/arm-none-eabi-gcc'), '-S',
    '-fno-short-enums', '-iquote', str(source / 'include'), '-x', 'c', '-', '-o', '-'],
    input='#include "global.h"\n#include "pokemon.h"\nconst unsigned health_fields[] = {MON_DATA_HP, MON_DATA_MAX_HP};',
    text=True, capture_output=True, check=True).stdout
hp_field, max_hp_field = [int(n) for n in re.findall(r'\.word\s+(\d+)', compiled.split('health_fields:', 1)[1].split('.size', 1)[0])]
healing = []

def nurse(island):
    center = island + 'Island_PokemonCenter_1F_Frlg'
    x = 5 if island == 'One' else 7
    leg(island.lower() + '-nurse-counter', (center, x, 4))
    # Initial damage is a fixture; recovery comes from native nurse dialogue.
    scratch = s['gStringVar4'] + 800
    lib.write16(scratch, 1)
    native('SetMonData', party, hp_field, scratch)
    maximum = native('GetMonData2', party, max_hp_field)
    assert native('GetMonData2', party, hp_field) == 1
    press(64); press(1); finish(limit=700)
    actual = native('GetMonData2', party, hp_field)
    assert actual == maximum, (island, actual, maximum)
    healing.append(dict(island=island, hp_before=1, hp_after=actual, max_hp=maximum,
                        native_nurse_interaction=True, initial_damage_is_fixture=True))
    picture(island.lower() + '-native-healing')

start = ('JourneyWorldSea00', 34, 6)
warp(*start); native('SetPlayerAvatarTransitionFlags', 8); step(30)
for island in islands:
    center = island + 'Island_PokemonCenter_1F_Frlg'
    x, y = (9, 7) if island == 'One' else (7, 7)
    leg(island.lower() + '-center', (center, x, y))
    nurse(island)
    checkpoint(island.lower() + '-center-land')
    town = island + 'Island_Frlg'
    entrance = next(w for w in maps[town]['warp_events'] if w['dest_map'] == maps[center]['id'])
    leg(island.lower() + '-town-return', (town, entrance['x'], entrance['y'] + 1))
    sea = 'JourneyWorldSea%02d' % (islands.index(island) + 1)
    leg(island.lower() + '-sea-return', (sea, 32, 15))
    checkpoint(island.lower() + '-sea-surf')
leg('original-sea-return', start)
assert state()['mode'] == 8
assert not wins
lib.stop()
(args.output / 'sevii-town-access.json').write_text(json.dumps(dict(
    passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
    continuous_roundtrip=True, start=list(start), end=list(start), planned_maps=names,
    visited_maps=sorted({n for t in transitions for n in [t['source'][0], t['destination'][0]]}),
    islands=islands, legs=checks, healing=healing,
    position_changes=walked, transitions=transitions, surf_prompts=surf_prompts,
    save_continue=saves, native_trainer_battles=wins,
    no_midroute_warps_or_direct_npc_scripts=True,
    initial_party_position_and_prior_story_states_are_fixtures=True,
    wild_encounters_disabled=True, full_campaign_playthrough=False, balance_validated=False), indent=2) + '\n')
print('Seven native island towns, nurses and fourteen Continues passed', flush=True)
