"""Use the native Start-button Mega trigger in real Brock battles."""
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
parser.add_argument('--case', choices=['charizard-x', 'charizard-y', 'no-ring', 'wrong-stone', 'rayquaza', 'greninja', 'garchomp-z'], required=True)
options = parser.parse_args()
mega_case = options.case
sys.argv = [sys.argv[0], '--source', str(options.source), '--library', str(options.library),
            '--output', str(options.output), '--ability-slot', '0']
bootstrap = (ROOT / 'tools/hoenn/validate_abilities.py').read_text().split('\nability_field,')[0]
exec(compile(bootstrap, str(ROOT / 'tools/hoenn/validate_abilities.py'), 'exec'))
ring, stone_x, stone_y, leftovers, charizard, mega_x, mega_y, rayquaza, mega_ray, ascent, greninjite, mega_greninja = abi[80:92]
base, target, item = charizard, mega_x, stone_x
if mega_case == 'charizard-y':
    target, item = mega_y, stone_y
elif mega_case == 'wrong-stone':
    item = leftovers
elif mega_case == 'rayquaza':
    base, target, item = rayquaza, mega_ray, 0
elif mega_case == 'greninja':
    base, target, item = abi[68], mega_greninja, greninjite
elif mega_case == 'garchomp-z':
    base, target, item = abi[97:100]
should_transform = mega_case not in ['no-ring', 'wrong-stone']
party = s['gParties']
for i in range(6 * abi[2]):
    lib.write8(party + i, 0)
lib.write8(s['gPartiesCount'], 0)
# Model an owned Pokemon trained from level 5. Gen9 obedience uses met level;
# a gift received at level 100 disobeys before badges, obscuring Mega tests.
assert native('ScriptGiveMon', base, 100, item) == 0
scratch = s['gStringVar4'] + 800
lib.write8(scratch, 5)
native('SetMonData', party, abi[96], scratch)
assert native('GetMonData2', party, abi[96]) == 5
assert native('GetMonData2', party, abi[6]) == 100
for slot in range(4):
    native('ScriptSetMonMoveSlot', 0, 0, slot)
native('ScriptSetMonMoveSlot', 0, abi[76], 0)
assert native('GetMonData2', party, abi[92]) == abi[76]
assert native('GetMonData2', party, abi[94]) == 0
if mega_case == 'rayquaza':
    native('ScriptSetMonMoveSlot', 0, ascent, 1)
assert not native('CheckBagHasItem', ring, 1)
if mega_case != 'no-ring':
    assert native('AddBagItem', ring, 1)
warp('PewterCity_Gym_Frlg', 4, 3)
script(b'\x05' + struct.pack('<I', s['PewterCity_Gym_EventScript_Brock']), 30)
def handlers(name):
    return {int(address, 16) for address, kind, label in re.findall(r'^(\w+) (\w) (\S+)$', raw, re.M) if label == name}
actions, moves = handlers('HandleInputChooseAction'), handlers('HandleInputChooseMove')
started = False
triggered = False
seen = False
rendered = False
attacks = 0
last_status = None
for _ in range(1200):
    if lib.read32(s['gMain'] + 4) & ~1 == s['BattleMainCB2']:
        started = True
        species = lib.read16(s['gBattleMons'] + abi[75])
        status = lib.read32(s['gBattleMons'] + abi[95])
        if status != last_status:
            print('Status change:', hex(status), 'attacks', attacks,
                  'move', lib.read16(s['gCurrentMove']), flush=True)
            last_status = status
        seen |= species == target
        controller = lib.read32(s['gBattlerControllerFuncs']) & ~1
        if controller in actions:
            if species == target and not rendered:
                picture('mega-' + mega_case + '-ready')
                rendered = True
            step(1, 64); step(8); step(1, 32); step(8); press(1)
        elif controller in moves:
            if not triggered:
                step(1, 8); step(15)
                triggered = True
            # Confirm the selected slot instead of assuming short key pulses were read.
            for _ in range(5):
                cursor = lib.read8(s['gMoveSelectionCursor'])
                if cursor == 0:
                    break
                step(3, 64 if cursor & 2 else 32); step(12)
            assert lib.read8(s['gMoveSelectionCursor']) == 0
            assert lib.read16(s['gBattleMons'] + abi[93]) == abi[76]
            press(1)
            attacks += 1
        else:
            press(2)
    elif started and lib.read32(s['gMain'] + 4) & ~1 == s['CB2_Overworld']:
        break
    else:
        press(2)
assert started and triggered and attacks > 0
assert seen == should_transform, (mega_case, seen)
assert rendered == should_transform, (mega_case, rendered)
if lib.read32(s['gMain'] + 4) & ~1 != s['CB2_Overworld']:
    picture('mega-' + mega_case + '-incomplete')
    print('Incomplete battle:', attacks, hex(lib.read32(s['gMain'] + 4) & ~1),
          hex(lib.read32(s['gBattlescriptCurrInstr'])),
          hex(lib.read32(s['gBattlerControllerFuncs']) & ~1),
          lib.read8(s['gActionSelectionCursor']), lib.read8(s['gMoveSelectionCursor']), flush=True)
assert lib.read32(s['gMain'] + 4) & ~1 == s['CB2_Overworld']
step(200)
assert native('GetMonData2', party, abi[7]) == base
lib.stop()
result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              case=mega_case, real_brock_battle=True, native_start_button=True,
              transformed=seen, rendered_at_action_menu=rendered, restored_base_species=True,
              items_added_only_in_test_fixture=True)
result['fixture_met_level'] = 5
(args.output / (mega_case + '.json')).write_text(json.dumps(result, indent=2) + '\n')
print(result, flush=True)
