"""Exercise Battle Bond and a partner Mega in a real Tate/Liza double battle."""
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
parser.add_argument('--case', choices=['hidden', 'torrent', 'protean', 'event'], required=True)
options = parser.parse_args()
double_case = options.case
sys.argv = [sys.argv[0], '--source', str(options.source), '--library', str(options.library),
            '--output', str(options.output)]
bootstrap = (ROOT / 'tools/hoenn/validate_abilities.py').read_text().split('\nability_field,')[0]
exec(compile(bootstrap, str(ROOT / 'tools/hoenn/validate_abilities.py'), 'exec'))
party, scratch = s['gParties'], s['gStringVar4'] + 800
first_species = abi[70] if double_case == 'event' else abi[68]
ability_slot = {'hidden': 2, 'torrent': 0, 'protean': 1, 'event': 0}[double_case]
for i in range(6 * abi[2]):
    lib.write8(party + i, 0)
lib.write8(s['gPartiesCount'], 0)
for index, species, held, move in [(0, first_species, 0, abi[77]),
                                   (1, abi[84], abi[81], abi[103])]:
    assert native('ScriptGiveMon', species, 100, held) == 0
    lib.write8(scratch, 5)
    native('SetMonData', party + index * abi[2], abi[96], scratch)
    for slot in range(4):
        native('ScriptSetMonMoveSlot', index, move if slot == 0 else 0, slot)
lib.write8(scratch, ability_slot)
native('SetMonData', party, abi[65], scratch)
assert native('AddBagItem', abi[80], 1)
warp('MossdeepCity_Gym', 23, 8)
script(b'\x05' + struct.pack('<I', s['MossdeepCity_Gym_EventScript_TateAndLiza']), 30)
def handlers(name):
    return {int(a, 16) for a, kind, n in re.findall(r'^(\w+) (\w) (\S+)$', raw, re.M) if n == name}
actions, moves, targets = [handlers(name) for name in ['HandleInputChooseAction', 'HandleInputChooseMove', 'HandleInputChooseTarget']]
targets |= handlers('HandleInputShowTargets') | handlers('HandleInputShowEntireFieldTargets')
started = False
mega_triggered = False
ash_seen = False
mega_seen = False
both_seen = False
rendered = False
selections = [0, 0]
for tick in range(2400):
    callback = lib.read32(s['gMain'] + 4) & ~1
    if callback == s['BattleMainCB2']:
        started = True
        assert lib.read8(s['gBattlersCount']) == 4
        assert lib.read32(s['gBattleTypeFlags']) & 1
        first = lib.read16(s['gBattleMons'] + abi[75])
        partner = lib.read16(s['gBattleMons'] + 2 * abi[74] + abi[75])
        ash_seen |= first == abi[69]
        mega_seen |= partner == abi[85]
        both_seen |= first == abi[69] and partner == abi[85]
        acted = False
        for battler in [0, 2]:
            controller = lib.read32(s['gBattlerControllerFuncs'] + 4 * battler) & ~1
            if controller in actions:
                if first == abi[69] and partner == abi[85] and not rendered:
                    picture('double-' + double_case + '-forms-ready')
                    rendered = True
                step(3, 64); step(12); step(3, 32); step(12); press(1)
                acted = True
                break
            if controller in moves:
                if battler == 2 and not mega_triggered:
                    step(3, 8); step(15)
                    mega_triggered = True
                # Both fixtures have exactly one move, in slot zero.
                assert lib.read8(s['gMoveSelectionCursor'] + battler) == 0
                press(1)
                selections[battler // 2] += 1
                acted = True
                break
            if controller in targets:
                # The default target is an opponent; never pick the ally.
                press(1)
                acted = True
                break
        if not acted:
            press(2)
    elif started and callback == s['CB2_Overworld']:
        break
    else:
        press(1)
expected_ash = double_case in {'hidden', 'event'}
if not started or callback != s['CB2_Overworld']:
    picture('double-' + double_case + '-incomplete')
    print('Incomplete:', tick, hex(callback), selections, ash_seen, mega_seen, flush=True)
assert started and callback == s['CB2_Overworld']
assert all(selections) and mega_triggered and mega_seen
assert ash_seen == expected_ash
assert both_seen == expected_ash and rendered == expected_ash
# Finish the actual post-victory badge/item script before making native field calls.
for _ in range(180):
    press(1)
assert native('JourneyGymBadgeCount', 0) == 1
assert native('JourneyGymBadgeCount', 1) == 0
assert native('GetMonData2', party, abi[7]) == first_species
assert native('GetMonData2', party, abi[65]) == ability_slot
assert native('GetMonData2', party + abi[2], abi[7]) == abi[84]
assert native('TrySavingData', 0, max_frames=6000) == 1
lib.write8(scratch, (ability_slot + 1) % 3)
native('SetMonData', party, abi[65], scratch)
assert native('LoadGameSave', 0) == 1
step(30)
assert native('GetMonData2', s['gParties'], abi[65]) == ability_slot
assert native('JourneyGymBadgeCount', 0) == 1 and native('JourneyGymBadgeCount', 1) == 0
lib.stop()
result = dict(passed=True, case=double_case, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              real_tate_liza_double_battle=True, player_move_selections=selections,
              ability_slot=ability_slot, ash_after_ko=ash_seen, partner_mega=mega_seen,
              simultaneous_forms=both_seen, rendered_at_action_menu=rendered,
              both_original_species_restored=True, original_ability_slot_restored=True,
              real_hoenn_badge_awarded=True, kanto_badges_unchanged=True,
              native_save_preserves_slot_and_badge=True, fixture_met_level=5,
              mega_items_added_only_in_fixture=True)
(args.output / ('double-' + double_case + '.json')).write_text(json.dumps(result, indent=2) + '\n')
print(result, flush=True)
