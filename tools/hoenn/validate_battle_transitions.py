"""Exercise real switching, the one-Mega rule and faint-form reversion."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--library', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--case', choices=['mega-switch', 'mega-faint', 'ash-switch', 'ash-faint'], required=True)
options = parser.parse_args()
transition_case = options.case
sys.argv = [sys.argv[0], '--source', str(options.source), '--library', str(options.library),
            '--output', str(options.output), '--case', 'charizard-x']
bootstrap = (ROOT / 'tools/hoenn/validate_megas.py').read_text().split("\nwarp('PewterCity_Gym_Frlg'")[0]
exec(compile(bootstrap, str(ROOT / 'tools/hoenn/validate_megas.py'), 'exec'))
first_species, transformed_species = abi[84], abi[85]
if transition_case.startswith('ash-'):
    for i in range(6 * abi[2]):
        lib.write8(party + i, 0)
    lib.write8(s['gPartiesCount'], 0)
    first_species, transformed_species = abi[68], abi[69]
    assert native('ScriptGiveMon', first_species, 100, 0) == 0
    lib.write8(scratch, 2)
    native('SetMonData', party, abi[65], scratch)
    lib.write8(scratch, 5)
    native('SetMonData', party, abi[96], scratch)
    native('ScriptSetMonMoveSlot', 0, abi[76], 0)
if transition_case == 'ash-faint':
    native('ScriptSetMonMoveSlot', 0, abi[103], 1)
    lib.write16(scratch, 10)
    native('SetMonData', party, abi[47], scratch)
assert native('ScriptGiveMon', abi[84], 100, abi[82]) == 0
second = party + abi[2]
lib.write8(scratch, 5)
native('SetMonData', second, abi[96], scratch)
native('ScriptSetMonMoveSlot', 1, abi[76], 0)
if transition_case == 'mega-faint':
    native('ScriptSetMonMoveSlot', 0, abi[103], 0)
    lib.write16(scratch, 1)
    native('SetMonData', party, abi[47], scratch)
warp('PewterCity_Gym_Frlg', 4, 3)
script(b'\x05' + struct.pack('<I', s['PewterCity_Gym_EventScript_Brock']), 30)
def handlers(name):
    return {int(a, 16) for a, kind, n in re.findall(r'^(\w+) (\w) (\S+)$', raw, re.M) if n == name}
actions, moves = handlers('HandleInputChooseAction'), handlers('HandleInputChooseMove')
started = False
first_triggered = False
seen_form = False
switched = False
asked_switch = False
second_trigger_attempted = False
second_mega = False
fainted = False
returned_first = False
party_menu_seen = False
for tick in range(1800):
    callback = lib.read32(s['gMain'] + 4) & ~1
    if callback == s['BattleMainCB2']:
        started = True
        index = lib.read8(s['gBattlerPartyIndexes'])
        species = lib.read16(s['gBattleMons'] + abi[75])
        controller = lib.read32(s['gBattlerControllerFuncs']) & ~1
        if index == 0 and species == transformed_species:
            seen_form = True
        fainted |= seen_form and lib.read16(party + abi[101]) == 0
        if index == 1:
            switched = True
            second_mega |= species == abi[86]
        if switched and index == 0 and species == transformed_species:
            returned_first = True
        if controller in actions:
            if seen_form and not switched and transition_case not in {'mega-faint', 'ash-faint'}:
                # Choose Pokemon through the action menu, then the second party slot.
                step(3, 128); step(12); step(3, 32); step(12)
                assert lib.read8(s['gActionSelectionCursor']) == 2
                press(1)
                asked_switch = True
            elif switched and transition_case == 'ash-switch' and not returned_first:
                step(3, 128); step(12); step(3, 32); step(12); press(1)
                asked_switch = True
            else:
                step(3, 64); step(12); step(3, 32); step(12); press(1)
        elif controller in moves:
            if transition_case.startswith('mega-') and not first_triggered:
                step(3, 8); step(15)
                first_triggered = True
            elif index == 1 and transition_case.startswith('mega-') and not second_trigger_attempted:
                step(3, 8); step(15)
                second_trigger_attempted = True
            for _ in range(5):
                cursor = lib.read8(s['gMoveSelectionCursor'])
                if cursor == 0:
                    break
                step(3, 64 if cursor & 2 else 32); step(12)
            assert lib.read8(s['gMoveSelectionCursor']) == 0
            if transition_case == 'ash-faint' and index == 0 and seen_form:
                step(3, 16); step(12)
                assert lib.read8(s['gMoveSelectionCursor']) == 1
            press(1)
        else:
            press(1 if transition_case in {'mega-faint', 'ash-faint'} and fainted else 2)
    elif callback in {s['CB2_InitPartyMenu'], s['CB2_UpdatePartyMenu']}:
        if task('Task_HandleChooseMonInput'):
            party_menu_seen = True
            # Battle party order puts the active Pokemon in the left slot.
            # The other of our two Pokemon stays in menu slot one on both swaps.
            desired = 1
            current = lib.read8(s['gPartyMenu'] + abi[100])
            if current != desired:
                step(3, 32 if desired == 0 else 128); step(20)
            else:
                press(1)
        else:
            press(1)
    elif started and callback == s['CB2_Overworld']:
        break
    else:
        press(2)
assert started and seen_form and switched and party_menu_seen
assert not second_mega, transition_case
assert callback == s['CB2_Overworld'], (transition_case, hex(callback))
if transition_case == 'ash-switch':
    assert returned_first
elif transition_case in {'mega-faint', 'ash-faint'}:
    assert fainted
    if transition_case == 'mega-faint':
        assert second_trigger_attempted
else:
    assert asked_switch and second_trigger_attempted
step(200)
assert native('GetMonData2', party, abi[7]) == first_species
assert native('GetMonData2', second, abi[7]) == abi[84]
if transition_case.startswith('ash-'):
    assert native('GetMonData2', party, abi[65]) == 2
lib.stop()
result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              case=transition_case, native_party_menu=True, real_switch=True,
              fainted_after_transformation=fainted, second_mega_blocked=second_trigger_attempted and not second_mega,
              ash_persists_after_return=returned_first, original_species_restored=True)
(args.output / (transition_case + '.json')).write_text(json.dumps(result, indent=2) + '\n')
print(result, flush=True)
