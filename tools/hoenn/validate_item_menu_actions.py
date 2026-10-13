"""Use a stone and teach one reusable TM to two Pokémon via real menus.

The initial party, items and location are fixtures. Every item activation,
evolution animation and move-learning confirmation uses controller input.
"""
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--library', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--case', choices=['stone', 'alola-stone', 'kadabra', 'onix', 'pawmo', 'gimmighoul'], default='stone')
options = parser.parse_args()
case = options.case
sys.argv = [sys.argv[0], '--source', str(options.source), '--library', str(options.library), '--output', str(options.output)]
prefix = (ROOT / 'tools/hoenn/validate_world_map.py').read_text().split('\nchecks=[]')[0]
exec(compile(prefix, str(ROOT / 'tools/hoenn/validate_world_map.py'), 'exec'))
sha = hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest()
names = ['ITEM_THUNDER_STONE', 'ITEM_TM_THUNDERBOLT', 'MOVE_THUNDERBOLT',
         'MON_DATA_MOVE1', 'sizeof(struct Pokemon)', 'POCKET_TM_HM', 'offsetof(struct BagPosition,pocket)',
         'ITEM_RARE_CANDY', 'ITEM_METAL_COAT', 'MON_DATA_HELD_ITEM', 'MON_DATA_LEVEL',
         'VAR_UNUSED_0x404E', 'SPECIES_RAICHU_ALOLA', 'SPECIES_PAWMO', 'SPECIES_PAWMOT',
         'SPECIES_GIMMIGHOUL', 'SPECIES_GHOLDENGO']
with tempfile.TemporaryDirectory(dir='/tmp') as directory:
    probe = Path(directory) / 'constants.s'
    code = '#include "global.h"\n#include "pokemon.h"\n#include "constants/items.h"\n#include "constants/moves.h"\n#include "constants/species.h"\n#include "constants/vars.h"\n#include "item_menu.h"\n#include <stddef.h>\nconst u32 probe[]={' + ','.join(names) + '};'
    subprocess.run([str(ROOT / '.local/arm-gcc/usr/bin/arm-none-eabi-gcc'), '-S',
                    '-mabi=apcs-gnu', '-iquote', str(source / 'include'), '-x', 'c',
                    '-', '-o', str(probe)], input=code, text=True, check=True)
    constants = dict(zip(names, map(int, re.findall(r'\.word\s+(\d+)', probe.read_text()))))

def active(name):
    return task(name) if name in s else False

def wait_task(name, limit=500):
    for _ in range(limit):
        if active(name):
            step(30)
            return
        step(8)
    picture('failure-' + name)
    raise AssertionError(('Missing menu task', name, hex(callback())))

def bag():
    press(8)
    wait_for(lambda: lib.read8(s['sNumStartMenuActions']) > 0)
    step(80)
    actions = [lib.read8(s['sCurrentStartMenuActions'] + i)
               for i in range(lib.read8(s['sNumStartMenuActions']))]
    index = next(i for i, value in enumerate(actions)
                 if lib.read32(s['sStartMenuItems'] + value * 8 + 4) & ~1 == s['StartMenuBagCallback'])
    for _ in range(12):
        pos = lib.read8(s['sStartMenuCursorPos'])
        if pos == index:
            break
        press(128 if pos < index else 64)
    assert lib.read8(s['sStartMenuCursorPos']) == index
    press(1)
    wait_task('Task_BagMenu_HandleInput')

def activate_item(slot=0):
    press(1)
    for _ in range(100):
        if active('Task_ItemContext_SingleRow') or active('Task_ItemContext_MultipleRows'):
            break
        step(8)
    assert active('Task_ItemContext_SingleRow') or active('Task_ItemContext_MultipleRows')
    press(1)  # USE
    # TMs first display their move and ask whether to teach it.
    for _ in range(100):
        if active('Task_HandleChooseMonInput'):
            break
        press(1)
    assert active('Task_HandleChooseMonInput'), 'Item did not open party selection'
    step(30)
    for _ in range(slot):
        press(128)
    press(1)

def back_to_field(limit=500):
    for _ in range(limit):
        if callback() == s['CB2_Overworld'] and not lib.read8(s['sLockFieldControls']):
            step(60)
            return
        press(2)
    picture('failure-return-to-field')
    raise AssertionError('Item menus did not return to field')

# Clear fixture party so both teaching targets have a free move slot.
for index in range(6 * constants['sizeof(struct Pokemon)']):
    lib.write8(s['gParties'] + index, 0)
lib.write8(s['gPartiesCount'], 0)
species, level, held, expected = {
    'stone': (25, 5, 0, 26),
    'alola-stone': (25, 5, 0, constants['SPECIES_RAICHU_ALOLA']),
    'kadabra': (64, 35, 0, 65),
    'onix': (95, 29, constants['ITEM_METAL_COAT'], 208),
    'pawmo': (constants['SPECIES_PAWMO'], 35, 0, constants['SPECIES_PAWMOT']),
    'gimmighoul': (constants['SPECIES_GIMMIGHOUL'], 35, 0, constants['SPECIES_GHOLDENGO']),
}[case]
assert native('ScriptGiveMon', species, level, held) == 0
if case == 'stone':
    assert native('ScriptGiveMon', 25, 5, 0) == 0
if case == 'alola-stone':
    native('VarSet', constants['VAR_UNUSED_0x404E'], 1)
stone = constants['ITEM_THUNDER_STONE'] if case.endswith('stone') else constants['ITEM_RARE_CANDY']
assert native('AddBagItem', stone, 2 if case.endswith('stone') else 1)
before = native('CountTotalItemQuantityInBag', stone)
bag()
activate_item()
for _ in range(200):
    if callback() == s['CB2_EvolutionSceneUpdate']:
        break
    press(1)  # Rare Candy level/stat and optional move-learning messages.
assert callback() == s['CB2_EvolutionSceneUpdate'], 'Item did not start evolution'
step(60)
picture('stone-evolution-start')
seen_animation = active('Task_EvolutionScene')
for _ in range(500):
    press(1)
    if active('Task_BagMenu_HandleInput'):
        break
assert active('Task_BagMenu_HandleInput'), 'Evolution did not finish and return to Bag'
step(90)
picture('stone-evolution-return-to-bag')
back_to_field()
assert seen_animation
assert native('GetMonData2', s['gParties'], abi[7]) == expected
assert native('CountTotalItemQuantityInBag', stone) == before - 1
expected_level = level if case.endswith('stone') else level + 1
assert native('GetMonData2', s['gParties'], constants['MON_DATA_LEVEL']) == expected_level
after_held = native('GetMonData2', s['gParties'], constants['MON_DATA_HELD_ITEM'])
if held:
    assert after_held == 0, 'Evolution must consume its held item'

if case != 'stone':
    assert native('TrySavingData', 0, max_frames=6000) == 1
    assert native('LoadGameSave', 0, max_frames=6000) == 1
    assert native('GetMonData2', s['gParties'], abi[7]) == expected
    assert native('CountTotalItemQuantityInBag', stone) == before - 1
    assert native('GetMonData2', s['gParties'], constants['MON_DATA_HELD_ITEM']) == after_held
    assert hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest() == sha
    lib.stop()
    (args.output / ('item-menu-' + case + '.json')).write_text(json.dumps(dict(
        passed=True, rom_sha256=sha, case=case, initial_party_items_and_travel_are_fixtures=True,
        item_activation_and_confirmation_are_controller_input=True,
        animation_completed=True, used_item_consumed_once=True,
        evolved_species=expected, level=expected_level, held_item_after=after_held,
        flash_reload_preserves_evolved_species_and_item_quantities=True), indent=2) + '\n')
    print('Native evolution, item consumption and reload passed:', case, flush=True)
    sys.exit(0)

tm = constants['ITEM_TM_THUNDERBOLT']
assert native('AddBagItem', tm, 1)
tm_before = native('CountTotalItemQuantityInBag', tm)
learned = []
for slot in range(2):
    bag()
    # Pocket changes use the actual left/right Bag controls.
    for _ in range(7):
        if lib.read8(s['gBagPosition'] + constants['offsetof(struct BagPosition,pocket)']) == constants['POCKET_TM_HM']:
            break
        press(16)
        step(90)
    assert lib.read8(s['gBagPosition'] + constants['offsetof(struct BagPosition,pocket)']) == constants['POCKET_TM_HM']
    activate_item(slot)
    for _ in range(160):
        press(1)
        if active('Task_HandleChooseMonInput'):
            break
    assert active('Task_HandleChooseMonInput'), 'TM teaching did not finish'
    step(90)
    picture('reusable-tm-target-' + str(slot))
    back_to_field()
    mon = s['gParties'] + slot * constants['sizeof(struct Pokemon)']
    moves = [native('GetMonData2', mon, constants['MON_DATA_MOVE1'] + i) for i in range(4)]
    assert constants['MOVE_THUNDERBOLT'] in moves, (slot, moves)
    assert native('CountTotalItemQuantityInBag', tm) == tm_before
    learned.append(dict(slot=slot, moves=moves, tm_quantity=tm_before))

assert native('TrySavingData', 0, max_frames=6000) == 1
assert native('LoadGameSave', 0, max_frames=6000) == 1
assert native('GetMonData2', s['gParties'], abi[7]) == 26
assert native('CountTotalItemQuantityInBag', stone) == before - 1
assert native('CountTotalItemQuantityInBag', tm) == tm_before
for row in learned:
    mon = s['gParties'] + row['slot'] * constants['sizeof(struct Pokemon)']
    moves = [native('GetMonData2', mon, constants['MON_DATA_MOVE1'] + i) for i in range(4)]
    assert moves == row['moves'], 'Move changed after flash reload'
assert hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest() == sha
lib.stop()
(args.output / 'item-menu-actions.json').write_text(json.dumps(dict(
    passed=True, rom_sha256=sha, initial_party_items_and_travel_are_fixtures=True,
    item_activation_and_confirmation_are_controller_input=True,
    stone_animation_completed=True, stone_consumed_once=True, evolved_species=26,
    reusable_tm_taught_to_two_pokemon=True, learned=learned,
    flash_reload_preserves_evolved_species_and_item_quantities=True), indent=2) + '\n')
print('Native stone animation, consumption, reusable TM teaching and reload passed', flush=True)
