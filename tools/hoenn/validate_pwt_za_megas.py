"""Verify Z-A form eligibility, the Mega shop stock and a native PWT match."""
import hashlib
import json
from pathlib import Path
import re

from audit_megas import audit_megas
from battle_interaction_fixture import compile_probe
from pwt_cup_controller import CupController

ROOT = Path(__file__).resolve().parents[2]
bootstrap = ROOT / 'tools/hoenn/validate_pwt_world.py'
exec(compile(bootstrap.read_text().split('for generation in range(cap+1):')[0], str(bootstrap), 'exec'))

constants = {'ITEM_CLEFABLITE', 'ITEM_GLIMMORANITE', 'ITEM_RAICHUNITE_X', 'ITEM_RAICHUNITE_Y',
             'ITEM_MEGA_RING', 'MOVE_PROTECT', 'SPECIES_RAICHU', 'SPECIES_RAICHU_MEGA_X',
             'SPECIES_RAICHU_MEGA_Y', 'BATTLE_TYPE_PWT', 'MON_DATA_HELD_ITEM'}
_, c, _ = compile_probe(source, constants)
audit = audit_megas(source)
assert audit['passed']
stones = set(range(c['ITEM_CLEFABLITE'], c['ITEM_GLIMMORANITE'] + 1))
links = [form for form in audit['links'] if form['requirement_id'] in stones and form['method'] == 'item']
assert len({form['target_id'] for form in links}) == 49
assert {form['requirement_id'] for form in links} == stones and len(stones) == 45
stock = []
for i in range(128):
    item = lib.read16(s['JourneyEverGrande_MegaStock'] + i * 2)
    if item == 0:
        break
    stock.append(item)
else:
    raise AssertionError('Ever Grande has no stock terminator')
assert len(stock) == len(set(stock)) and stones <= set(stock)

eligible_forms = []
for form in links:
    base_allowed = bool(native('JourneySpeciesAllowed', form['species_id']))
    assert bool(native('JourneySpeciesAllowed', form['target_id'])) == base_allowed, form['target']
    if base_allowed:
        eligible_forms.append(form['target'])
assert len(set(eligible_forms)) == (17 if cap == 4 else 49)

# Travel and registration fixture. The live match uses controller input.
assert native('AddBagItem', c['ITEM_MEGA_RING'], 1)
native('ZeroPlayerPartyMons')
assert native('ScriptGiveMon', c['SPECIES_RAICHU'], 50, c['ITEM_RAICHUNITE_Y']) == 0
# Protect keeps both Raichu on the field to observe the forms between turns.
assert native('JourneyBossMoveLegal', c['SPECIES_RAICHU'], c['MOVE_PROTECT'], 50)
native('ScriptSetMonMoveSlot', 0, c['MOVE_PROTECT'], 0)
for species in (9, 149, 376, 94, 6):
    assert native('ScriptGiveMon', species, 50, 0) == 0
surge = next(row['id'] for row in rows if row['key'] == 'LT_SURGE')
original = bytes(lib.read8(party + i) for i in range(6 * abi[2]))


def register_surge_match():
    ids = begin(1)
    lib.write16(cup + offsets[9], ids.index(surge))
    lib.write8(cup + offsets[10], 1)


register_surge_match()
native('JourneyPWTPrepareBattle')
assert native('GetMonData2', enemy, abi[7]) == c['SPECIES_RAICHU']
assert native('GetMonData2', enemy, c['MON_DATA_HELD_ITEM']) == c['ITEM_RAICHUNITE_X']
assert native('GetMonData2', party, c['MON_DATA_HELD_ITEM']) == c['ITEM_RAICHUNITE_Y']
mega_effect = native('GetItemHoldEffect', c['ITEM_RAICHUNITE_X'])
assert sum(native('GetItemHoldEffect', native('GetMonData2', enemy + i * abi[2], c['MON_DATA_HELD_ITEM']))
           == mega_effect for i in range(6)) == 1
finish()

register_surge_match()
warp('JourneyPWTArena', 9, 6)
for _ in range(400):
    if task('Task_HandleYesNoInput'):
        step(12)
        break
    press(1)
else:
    raise AssertionError('Missing PWT ready prompt')
press(1)
for _ in range(300):
    if lib.read32(s['gMain'] + 4) & ~1 == s['BattleMainCB2']:
        break
    press(1)
else:
    raise AssertionError('PWT battle did not start')
assert lib.read32(s['gBattleTypeFlags']) & c['BATTLE_TYPE_PWT']

controller = CupController(source, lib, s)


def handlers(label):
    return {int(address, 16) for address, _, name in re.findall(r'^(\w+) (\w) (\S+)$', raw, re.M)
            if name == label}


actions = handlers('HandleInputChooseAction')
moves = handlers('HandleInputChooseMove')
species_offset, stride = controller.abi[5:7]
player_state = s['gBattleMons'] + species_offset
expected = (c['SPECIES_RAICHU_MEGA_Y'], c['SPECIES_RAICHU_MEGA_X'])
selected = False
for _ in range(800):
    visible = (lib.read16(player_state), lib.read16(player_state + stride))
    handler = lib.read32(s['gBattlerControllerFuncs']) & ~1
    if visible == expected and handler in actions:
        assert selected
        picture('pwt-mega-raichu-x-and-y')
        break
    if handler in actions:
        step(1, 64)
        step(8)
        step(1, 32)
        step(8)
        press(1)
    elif handler in moves:
        if not selected:
            step(1, 8)
            step(15)
            selected = True
        assert lib.read8(s['gMoveSelectionCursor']) == 0
        press(1)
    else:
        press(2)
else:
    picture('pwt-megas-not-observed')
    raise AssertionError(('Both native Mega forms were not visible between turns', visible))

lib.stop()
result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              generation_cap=cap, hard=bool(hard), compiled_za_forms=49, stones_in_ever_grande=len(stones),
              eligible_forms=sorted(set(eligible_forms)), opponent='Lt. Surge',
              player_start_button_mega='SPECIES_RAICHU_MEGA_Y', native_ai_mega='SPECIES_RAICHU_MEGA_X',
              one_opponent_mega_stone=True, registration_and_travel_fixtures=True)
(args.output / 'pwt-za-megas.json').write_text(json.dumps(result, indent=2) + '\n')
print('PWT Mega Raichu X and Y observed with', len(set(eligible_forms)), 'eligible Z-A forms', flush=True)
