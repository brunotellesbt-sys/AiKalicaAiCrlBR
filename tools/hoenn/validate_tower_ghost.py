"""Native Marowak reconstruction, Silph Scope outcome, stairs and Continue.
Initial party, position, inventory and defeated ordinary trainers are fixtures.
Battle attack/speed/HP are boosted; no synthetic boss win or scene completion.
"""
from pathlib import Path
import hashlib
import json
import re
import struct
import subprocess
ROOT = Path(__file__).resolve().parents[2]
exec(compile((ROOT / 'tools/hoenn/validate_team_missions.py').read_text().split('\nwins, completed =')[0],
             str(ROOT / 'tools/hoenn/validate_team_missions.py'), 'exec'))
fields = ['ITEM_SILPH_SCOPE', 'VAR_MAP_SCENE_POKEMON_TOWER_6F', 'offsetof(struct BattlePokemon, level)',
          'offsetof(struct BattlePokemon, pp)', 'MON_DATA_LEVEL', 'MON_DATA_SPECIES', 'MON_DATA_HP_IV',
          'MON_DATA_ATK_IV', 'MON_DATA_DEF_IV', 'MON_DATA_SPEED_IV', 'MON_DATA_SPATK_IV', 'MON_DATA_SPDEF_IV',
          'MON_FEMALE', 'NATURE_SERIOUS', 'TRAINER_CHANNELER_ANGELICA', 'TRAINER_CHANNELER_EMILIA',
          'TRAINER_CHANNELER_JENNIFER', 'BATTLE_TYPE_GHOST', 'offsetof(struct BattlePokemon, volatiles)']
compiled = subprocess.run([str(ROOT / '.local/arm-gcc/usr/bin/arm-none-eabi-gcc'), '-S', '-mabi=apcs-gnu',
    '-iquote', str(source / 'include'), '-x', 'c', '-', '-o', '-'],
    input='#include "global.h"\n#include "pokemon.h"\n#include "constants/items.h"\n#include "constants/vars.h"\n#include "constants/opponents.h"\n#include "constants/battle.h"\nconst unsigned ghost_fields[] = {' + ','.join(fields) + '};',
    text=True, capture_output=True, check=True).stdout
ids = dict(zip(fields, [int(n) for n in re.findall(r'\.word\s+(\d+)', compiled.split('ghost_fields:', 1)[1].split('.size', 1)[0])]))
for f in kanto_flags + hoenn_flags: rawflag(f, False)
for name in fields[14:17]: rawflag(0x500 + ids[name], True)
item = ids['ITEM_SILPH_SCOPE']; scene = ids['VAR_MAP_SCENE_POKEMON_TOWER_6F']
enemy = party + 6 * abi[2]

def set_scope(enabled):
    n = native('CountTotalItemQuantityInBag', item)
    if n: assert native('RemoveBagItem', item, n)
    if enabled: assert native('AddBagItem', item, 1)

def team(levels):
    for i in range(6 * abi[2]): lib.write8(party + i, 0)
    lib.write8(s['gPartiesCount'], 0)
    for i, level in enumerate(levels):
        assert native('ScriptGiveMon', 658, level, 0) == 0
        native('ScriptSetMonMoveSlot', i, abi[142], 0)

def mon(pointer=enemy):
    return dict(species=native('GetMonData3', pointer, ids['MON_DATA_SPECIES'], 0),
        level=native('GetMonData3', pointer, ids['MON_DATA_LEVEL'], 0),
        gender=native('GetMonGender', pointer), nature=native('GetNature', pointer),
        ivs=[native('GetMonData3', pointer, ids[n], 0) for n in fields[6:12]])

# Exercise the native coordinate event with and without Silph Scope.
# Snapshot its encrypted Pokemon while battle is active; the engine clears
# the enemy party on return. Decode the copy only after the field is idle.
reconstruction = []
for scope, levels in [(False, [40]), (True, [5]), (True, [40]), (True, [100]), (True, [7, 21, 44])]:
    warp('PokemonTower_6F_Frlg', 11, 14)
    team(levels); set_scope(scope)
    # Start the actual existing event via its coordinate trigger. Wait until
    # BattleMainCB2 appears and inspect its native BattlePokemon level.
    native('VarSet', scene, 0)
    step(1, 128); step(16)
    for _ in range(500):
        if lib.read32(s['gMain'] + 4) & ~1 == s['BattleMainCB2']: break
        press(1)
    assert lib.read32(s['gMain'] + 4) & ~1 == s['BattleMainCB2']
    for _ in range(160):
        if lib.read16(s['gBattleMons'] + abi[74] + abi[75]) == 105: break
        press(2)
    enemy_snapshot = bytes(lib.read8(enemy + i) for i in range(abi[2]))
    level = lib.read8(s['gBattleMons'] + abi[74] + ids['offsetof(struct BattlePokemon, level)'])
    mean = sum(levels) // len(levels)
    assert max(1, mean - 5) <= level <= min(100, mean + 2), (scope, levels, level)
    assert lib.read32(s['gBattleTypeFlags']) & ids['BATTLE_TYPE_GHOST']
    picture('ghost-' + str(mean) + ('-scope' if scope else '-no-scope'))
    # Complete the real battle. Without Scope select Run; with Scope use a
    # legal move and boosted fixture stats. No ARM calls while a scene runs.
    observed = dict(scope=scope, party_levels=levels, mean=mean, opponent_level=level, ghost_battle=True)
    attacks = 0
    for _ in range(2600):
        cb = lib.read32(s['gMain'] + 4) & ~1
        if cb == s['BattleMainCB2']:
            lib.write16(s['gBattleMons'] + pabi[15], 3000)
            lib.write16(s['gBattleMons'] + pabi[16], 10000)
            lib.write16(s['gBattleMons'] + pabi[20], 1000)
            lib.write16(s['gBattleMons'] + abi[102], 1000)
            lib.write8(s['gBattleMons'] + ids['offsetof(struct BattlePokemon, pp)'], 20)
            lib.write32(s['gBattleMons'] + abi[95], 0)
            volatile = s['gBattleMons'] + ids['offsetof(struct BattlePokemon, volatiles)']
            lib.write32(volatile, lib.read32(volatile) & ~7)  # First compiled volatile is confusionTurns:3.
            controllers = {lib.read32(s['gBattlerControllerFuncs'] + 4 * i) & ~1 for i in range(4)}
            if controllers & (actions | moves):
                step(1, 64); step(8); step(1, 32); step(8)
                if not scope: step(1, 128); step(8); step(1, 16); step(8)
                press(1); attacks += bool(controllers & moves)
            else: press(2)
        else:
            if idle(): break
            press(1)
    if not idle():
        picture('ghost-incomplete-' + str(mean))
        print('Ghost incomplete state:', hex(lib.read32(s['gMain'] + 4)), [hex(lib.read32(s['gBattlerControllerFuncs'] + i * 4)) for i in range(4)], lib.read8(s['gActionSelectionCursor']), attacks, flush=True)
    assert idle(), ('Ghost battle did not finish', scope, levels)
    outcome = lib.read8(s['gBattleOutcome'])
    assert outcome == (1 if scope else 4), outcome
    assert native('VarGet', scene) == int(scope)
    snapshot_pointer = s['gStringVar4'] + 256
    for i, value in enumerate(enemy_snapshot): lib.write8(snapshot_pointer + i, value)
    after = mon(snapshot_pointer)
    assert after['species'] == 105 and after['level'] == level
    if scope:
        assert after['gender'] == ids['MON_FEMALE'] and after['nature'] == ids['NATURE_SERIOUS']
        assert after['ivs'] == [31, 0, 0, 0, 0, 0], after
        # Upstream passes packed IVs=31, rather than six perfect IVs.
    observed.update(outcome=outcome, scene=native('VarGet', scene), reconstructed=after, attacks=attacks)
    reconstruction.append(observed)
    print('Marowak event passed:', observed, flush=True)
    native('HealPlayerParty')

# Continue after the victory must keep the stairs unlocked and scope held.
assert native('TrySavingData', 0, max_frames=6000) == 1
assert native('LoadGameSave', 0, max_frames=6000) == 1
lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1); step(1500); finish()
assert native('VarGet', scene) == 1 and native('CountTotalItemQuantityInBag', item) == 1
picture('tower-ghost-victory-after-continue')
# The stair tile has MB_UP_LEFT_STAIR_WARP: enter westward from (12,16).
assert position() == (11, 15), position()
def approach(goal, key):
    for _ in range(80):
        step(4, key); step(4)
        if position() == goal:
            step(24); return
    raise AssertionError(('Stair approach failed', goal, position()))
approach((12, 15), 16)
approach((12, 16), 128)
for _ in range(180):
    if location() == map_id('PokemonTower_7F_Frlg'): break
    step(1, 32); step(4)
assert location() == map_id('PokemonTower_7F_Frlg'), (location(), position())
picture('tower-seventh-floor-after-ghost')
lib.stop()
(args.output / 'tower-ghost.json').write_text(json.dumps(dict(passed=True,
    rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
    cases=reconstruction, victory_save_continue=True, native_coordinate_trigger=True,
    seventh_floor_reached_by_walking=True, identified_gender_nature_and_original_packed_ivs_preserved=True,
    ghost_capture_block_source_preserved=True, initial_states_and_boosted_stats_are_fixtures=True,
    ordinary_tower_trainers_bypassed_by_initial_flags=True, full_campaign_playthrough=False,
    capture_attempt_exercised=False, fixture_clears_player_confusion=True, balance_validated=False), indent=2) + '\n')
print('Native Marowak event, level rule and stairs passed', flush=True)
