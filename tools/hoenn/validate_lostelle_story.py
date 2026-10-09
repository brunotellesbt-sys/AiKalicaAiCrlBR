"""Native Bill-meteorite-bikers-Lostelle story through controller interactions.
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
names = ['JourneyWorldSea00', 'JourneyWorldSea01', 'JourneyWorldSea02', 'JourneyWorldSea03',
    'OneIsland_Harbor_Frlg', 'OneIsland_Frlg', 'OneIsland_PokemonCenter_1F_Frlg',
    'TwoIsland_Harbor_Frlg', 'TwoIsland_Frlg', 'TwoIsland_JoyfulGameCorner_Frlg',
    'ThreeIsland_Harbor_Frlg', 'ThreeIsland_Port_Frlg', 'ThreeIsland_Frlg',
    'ThreeIsland_BondBridge_Frlg', 'ThreeIsland_BerryForest_Frlg']
trainer_text = (source / 'data/scripts/trainers_frlg.inc').read_text()
shared_trainers = '\n'.join(re.findall(r'^ThreeIsland_[^\n]+::\n(.*?)(?=^[A-Za-z0-9_]+::|\Z)', trainer_text, re.M | re.S))
constants = sorted(set(re.findall(r'\bTRAINER_[A-Z0-9_]+', shared_trainers + '\n'.join(
    (source / 'data/maps' / n / 'scripts.inc').read_text() for n in ['ThreeIsland_Frlg', 'ThreeIsland_BondBridge_Frlg']))))
compiled = subprocess.run([str(ROOT / '.local/arm-gcc/usr/bin/arm-none-eabi-gcc'), '-S',
    '-iquote', str(source / 'include'), '-x', 'c', '-', '-o', '-'],
    input='#include "constants/opponents.h"\nconst unsigned sea_trainers[] = {' + ','.join(constants) + '};',
    text=True, capture_output=True, check=True).stdout
allowed = set(int(n) for n in re.findall(r'\.word\s+(\d+)', compiled.split('sea_trainers:', 1)[1].split('.size', 1)[0]))
allowed.update(t['id'] for t in stories['trainers'])
walk_prefix = 'lostelle-story'
exec(compile((ROOT / 'tools/hoenn/native_water_walk.py').read_text(),
             str(ROOT / 'tools/hoenn/native_water_walk.py'), 'exec'))
fields = ['VAR_MAP_SCENE_ONE_ISLAND_POKEMON_CENTER_1F', 'VAR_MAP_SCENE_TWO_ISLAND_JOYFUL_GAME_CORNER',
    'VAR_MAP_SCENE_THREE_ISLAND', 'FLAG_RESCUED_LOSTELLE', 'FLAG_HIDE_LOSTELLE_IN_BERRY_FOREST',
    'FLAG_GOT_MOON_STONE_FROM_JOYFUL_GAME_CORNER', 'ITEM_METEORITE', 'ITEM_MOON_STONE',
    'ITEM_IAPAPA_BERRY', 'SPECIES_HYPNO', 'offsetof(struct BattlePokemon, level)',
    'sizeof(struct BattlePokemon)', 'offsetof(struct BattlePokemon, pp)']
compiled = subprocess.run([str(ROOT / '.local/arm-gcc/usr/bin/arm-none-eabi-gcc'), '-S',
    '-mabi=apcs-gnu', '-iquote', str(source / 'include'), '-x', 'c', '-', '-o', '-'],
    input='#include "global.h"\n#include "pokemon.h"\n#include "constants/vars.h"\n#include "constants/flags.h"\n#include "constants/items.h"\nconst unsigned story_fields[] = {' + ','.join(fields) + '};',
    text=True, capture_output=True, check=True).stdout
ids = dict(zip(fields, [int(n) for n in re.findall(r'\.word\s+(\d+)', compiled.split('story_fields:', 1)[1].split('.size', 1)[0])]))
assert ids['sizeof(struct BattlePokemon)'] == abi[74]
battles, checks, saves = [], [], []
targets = {int(a, 16) for a, _, n in re.findall(r'^(\w+) (\w) (\S+)$', raw, re.M)
           if n in ['HandleInputChooseTarget', 'HandleInputShowTargets', 'HandleInputShowEntireFieldTargets']}

# Keep native field-script continuation intact between consecutive battles.
# Trampoline calls are reserved for idle checkpoints, never made inside scenes.
def finish(limit=6000):
    active = None
    for tick in range(limit):
        cb = lib.read32(s['gMain'] + 4) & ~1
        if cb == s['BattleMainCB2']:
            trainer = bool(lib.read32(s['gBattleTypeFlags']) & abi[10])
            if active is None:
                active = dict(kind='trainer' if trainer else 'scripted_wild',
                    trainer=lib.read16(s['gTrainerBattleParameter'] + abi[13]) if trainer else None,
                    map=by_location[location()], attacks=0)
                if trainer: assert active['trainer'] in allowed, (active, sorted(allowed))
            species = lib.read16(s['gBattleMons'] + abi[74] + abi[75])
            if species:
                active['opponent_species'] = species
                active['opponent_level'] = lib.read8(s['gBattleMons'] + abi[74] + ids['offsetof(struct BattlePokemon, level)'])
            active['double_battle'] = lib.read8(s['gBattlersCount']) == 4
            for battler in ([0, 2] if active['double_battle'] else [0]):
                lib.write32(s['gBattleMons'] + battler * abi[74] + abi[95], 0)
            lib.write8(s['gBattleMons'] + ids['offsetof(struct BattlePokemon, pp)'], 20)
            lib.write16(s['gBattleMons'] + pabi[15], 16000)
            lib.write16(s['gBattleMons'] + pabi[16], 10000)
            lib.write16(s['gBattleMons'] + pabi[20], 30000)
            if lib.read16(s['gBattleMons'] + abi[102]): lib.write16(s['gBattleMons'] + abi[102], 30000)
            controllers = {lib.read32(s['gBattlerControllerFuncs'] + 4 * i) & ~1 for i in range(4)}
            if controllers & targets:
                press(1)
            elif controllers & (actions | moves):
                step(1, 64); step(8); step(1, 32); step(8); press(1)
                active['attacks'] += bool(controllers & moves)
            else: press(2)
        else:
            if active is not None and cb == s['CB2_Overworld']:
                active['outcome'] = lib.read8(s['gBattleOutcome'])
                assert active['outcome'] == 1 and active['attacks'] > 0, active
                battles.append(active)
                print('Native story battle:', active, flush=True)
                active = None
            if idle(): return
            press(1)
    picture('lostelle-scene-failure')
    raise AssertionError(('Native scene incomplete', by_location[location()], position(), active))

def field():
    if not idle(): finish(); return True
    return False

def state():
    return dict(map=by_location[location()], position=list(position()), mode=lib.read8(s['gPlayerAvatar']) & 25,
        kanto_badges=native('JourneyGymBadgeCount', 1), hoenn_badges=native('JourneyGymBadgeCount', 0),
        one_scene=native('VarGet', ids[fields[0]]), two_scene=native('VarGet', ids[fields[1]]),
        three_scene=native('VarGet', ids[fields[2]]), rescued=flag(ids['FLAG_RESCUED_LOSTELLE']),
        forest_lostelle_hidden=flag(ids['FLAG_HIDE_LOSTELLE_IN_BERRY_FOREST']),
        moon_reward_received=flag(ids['FLAG_GOT_MOON_STONE_FROM_JOYFUL_GAME_CORNER']),
        meteorite=native('CountTotalItemQuantityInBag', ids['ITEM_METEORITE']),
        moon_stone=native('CountTotalItemQuantityInBag', ids['ITEM_MOON_STONE']),
        iapapa=native('CountTotalItemQuantityInBag', ids['ITEM_IAPAPA_BERRY']))

def checkpoint(label):
    before = state()
    assert before['kanto_badges'] == before['hoenn_badges'] == 0
    assert native('TrySavingData', 0, max_frames=6000) == 1
    assert native('LoadGameSave', 0, max_frames=6000) == 1
    lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
    step(1500); finish()
    after = state(); assert before == after, (label, before, after)
    saves.append(dict(label=label, before=before, after=after))
    picture(label + '-after-continue')

def leg(label, goal):
    first = walked; walk(goal)
    checks.append(dict(label=label, goal=list(goal), position_changes=walked - first))
    picture(label + '-arrival'); print('Native Lostelle leg:', label, position(), flush=True)

start = ('JourneyWorldSea00', 34, 6)
warp(*start); native('SetPlayerAvatarTransitionFlags', 8); step(30)
initial = state()
assert (initial['one_scene'], initial['two_scene'], initial['three_scene']) == (0, 0, 0)
assert not initial['rescued'] and not initial['meteorite']
leg('celio-meteorite', ('OneIsland_PokemonCenter_1F_Frlg', 9, 7))
assert state()['one_scene'] == 1 and state()['meteorite'] == 1
checkpoint('celio-introduction')
leg('lostelle-request', ('TwoIsland_JoyfulGameCorner_Frlg', 5, 6))
assert state()['two_scene'] == 1 and state()['three_scene'] == 2
checkpoint('lostelle-request')
leg('biker-boss-introduction', ('ThreeIsland_Frlg', 9, 27))
assert state()['three_scene'] == 3
leg('four-biker-battles', ('ThreeIsland_Frlg', 9, 25))
assert state()['three_scene'] == 4 and len(battles) == 4, battles
checkpoint('bikers-defeated')
leg('berry-forest-lostelle', ('ThreeIsland_BerryForest_Frlg', 4, 9))
checkpoint('forest-before-rescue')
mean = native('JourneyWildMean')
press(64); press(1); finish()
assert by_location[location()] == 'TwoIsland_JoyfulGameCorner_Frlg'
rescue = state()
assert rescue['rescued'] and rescue['forest_lostelle_hidden'] and rescue['two_scene'] == 3
hypno = [b for b in battles if b['kind'] == 'scripted_wild']
assert len(hypno) == 1 and hypno[0]['opponent_species'] == ids['SPECIES_HYPNO']
assert max(1, mean - 5) <= hypno[0]['opponent_level'] <= min(100, mean + 2)
checkpoint('lostelle-reunited')
leg('father-meteorite-delivery', ('TwoIsland_JoyfulGameCorner_Frlg', 5, 6))
press(64); press(1); finish()
delivered = state()
assert delivered['meteorite'] == 0 and delivered['moon_reward_received']
assert delivered['moon_stone'] == initial['moon_stone'] + 1
leg('reward-game-corner-exit', ('TwoIsland_Frlg', 39, 10))
leg('reward-game-corner-reentry', ('TwoIsland_JoyfulGameCorner_Frlg', 5, 6))
games_opened = state()
assert games_opened['two_scene'] == 4 and games_opened['moon_stone'] == delivered['moon_stone']
checkpoint('moon-stone-reward')
# Re-enter the forest and check the child cannot trigger a second encounter.
leg('forest-rescue-revisit', ('ThreeIsland_BerryForest_Frlg', 4, 9))
count = len(battles); press(64); press(1); finish()
assert len(battles) == count and state()['rescued']
checkpoint('forest-revisit')
leg('original-sea-return', start)
checkpoint('sea-return')
assert state()['mode'] == 8
for b in battles:
    if b['trainer'] is not None:
        b['native_defeated_flag'] = flag(0x500 + b['trainer'])
        assert b['native_defeated_flag']
lib.stop()
(args.output / 'lostelle-story.json').write_text(json.dumps(dict(passed=True,
    rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
    initial=initial, rescue=rescue, delivered=delivered, games_opened=games_opened, start=list(start), end=list(start),
    battles=battles, wild_party_mean=mean, position_changes=walked, transitions=transitions,
    legs=checks, save_continue=saves, surf_prompts=surf_prompts,
    visited_maps=sorted({n for t in transitions for n in [t['source'][0], t['destination'][0]]}),
    original_lostelle_escort_warp=True, no_midroute_fixture_warps_or_direct_npc_scripts=True,
    rescued_child_revisit_has_no_second_battle=True, initial_party_position_and_prior_story_states_are_fixtures=True,
    boosted_battle_stats_and_pp_are_fixtures=True, random_wild_encounters_disabled=True,
    balance_validated=False, full_campaign_playthrough=False), indent=2) + '\n')
print('Native Lostelle rescue, meteorite delivery and eight Continues passed', flush=True)
