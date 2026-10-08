"""Native Hoenn ferry guards, first Scott invitation, cabin voyage and Frontier.
Champion/visibility flags and initial port warps are fixtures, not campaigns.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--library', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--baseline', action='store_true')
options = parser.parse_args()
baseline_mode = options.baseline
sys.argv = [sys.argv[0], '--source', str(options.source), '--library', str(options.library), '--output', str(options.output)]
exec(compile((ROOT / 'tools/hoenn/validate_abilities.py').read_text().split('\nability_field,')[0], str(ROOT / 'tools/hoenn/validate_abilities.py'), 'exec'))
# Resolve menu.c's RAM cursor from its native getter: several translation
# units have unrelated static symbols also named sMenu. No menu mutation.
getter = s['Menu_GetCursorPos']
ldr = lib.read16(getter)
assert ldr & 0xF800 == 0x4800
menu_cursor = lib.read32(((getter + 4) & ~3) + (ldr & 255) * 4) + 2
TICKET, HOENN_CLEAR, SCOTT = 727, abi[111] - 0x2A + 4, 0x1D0

def flag(f, v): native('FlagSet' if v else 'FlagClear', f)
def idle():
    return (lib.read32(s['gMain'] + 4) & ~1) == s['CB2_Overworld'] and not lib.read8(s['sLockFieldControls'])
def until(predicate, limit=400):
    for _ in range(limit):
        if predicate(): return
        press(1)
    picture('frontier-travel-failure')
    pc = lib.read32(s['sGlobalScriptContext'] + 8)
    names = sorted([(a, n) for n, a in s.items() if a <= pc], reverse=True)[:4]
    print('Failure state', hex(pc), names, 'lock', lib.read8(s['sLockFieldControls']), 'yesno', task('Task_HandleYesNoInput'), 'menu', task('Task_HandleMultichoiceInput'), 'result', lib.read16(s['gSpecialVar_Result']), flush=True)
    raise AssertionError(('Ferry did not reach target', location(), position()))
def menu(): return task('Task_HandleMultichoiceInput')
def choose(index):
    assert menu()
    step(16)
    for _ in range(8):
        if lib.read8(menu_cursor) == index: break
        press(64 if lib.read8(menu_cursor) > index else 128)
    assert lib.read8(menu_cursor) == index
    press(1)
def talk_up(): step(4, 64); step(20); press(1)
def walk(key, axis, target):
    for _ in range(700):
        if position()[axis] == target:
            step(30); return
        step(1, key)
    picture('frontier-walk-failure')
    raise AssertionError(('Native ferry walk blocked', location(), position(), target))
def move_map(key, name):
    for _ in range(300):
        if location() == map_id(name): step(90); return
        step(1, key)
    raise AssertionError(('Native door did not change map', name, location(), position()))

def port(city):
    # Story scenes and NPC visibility are deliberately prepared by the fixture.
    for f in [0x389, 0x38C, 0x35C, 0x35D]: flag(f, False)
    # Slateport's Aqua sequence must be in its completed state to use the clerk.
    flags_text = (source / 'include/constants/vars.h').read_text()
    import re
    state = int(re.search(r'#define VAR_SLATEPORT_HARBOR_STATE\s+(0x\w+)', flags_text)[1], 16)
    native('VarSet', state, 2)
    warp(city + 'City_Harbor', 8, 11)
    talk_up()

for mon in [658, 149, 376, 121, 445, 637]: assert native('ScriptGiveMon', mon, 50, 0) == 0
flag(0x1AB8, True) # Kanto victory alone must not unlock the Hoenn ferry.
flag(SCOTT, True); native('VarSet', 0x40D4, 1)
guards = []
for city in ['Slateport', 'Lilycove']:
    for champ, ticket in [(False, False), (False, True), (True, False), (True, True)]:
        flag(HOENN_CLEAR, champ)
        native('RemoveBagItem', TICKET, 1)
        if ticket: assert native('AddBagItem', TICKET, 1) == 1
        port(city)
        until(lambda: menu() or idle())
        offered = menu()
        expected = champ and (ticket or baseline_mode)
        assert offered == expected, (city, champ, ticket, offered)
        picture(f'{city.lower()}-{int(champ)}-{int(ticket)}-guard')
        if offered: press(2); until(idle)
        assert location() == map_id(city + 'City_Harbor')
        guards.append(dict(port=city, hoenn_champion=champ, ticket=ticket, destination_menu=offered))
print('Native ferry guard cases passed:', len(guards), flush=True)
if baseline_mode:
    lib.stop()
    (args.output / 'frontier-travel-baseline.json').write_text(json.dumps(dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(), guards=guards, allows_boarding_without_ticket=True), indent=2) + '\n')
    sys.exit(0)

# Take the first cruise with Scott's flag actually unset. Arrival is via the
# attendant's scripts, then real cabin/bed/exit interactions without more warps.
flag(SCOTT, False); flag(0x32A, False); native('VarSet', 0x40D4, 0)
port('Slateport')
until(menu); choose(0)
until(lambda: task('Task_HandleYesNoInput')); step(12); press(1)
until(lambda: location() == map_id('SSTidalCorridor') and idle())
assert native('FlagGet', SCOTT) == 1
assert native('VarGet', 0x40D4) == 1
picture('first-cruise-scott-invitation-complete')
# Native helper calls only happen while idle, and do not synthesize progression.
assert position() == (1, 10), position()
walk(16, 0, 7)
move_map(64, 'SSTidalRooms')
picture('native-cabin-two-arrival')
walk(16, 0, 14); walk(64, 1, 12)
step(4, 16); step(20); press(1); until(idle)
picture('native-cabin-bed-voyage-complete')
walk(128, 1, 15); walk(32, 0, 13)
move_map(128, 'SSTidalCorridor')
walk(32, 0, 1)
step(4, 128); step(20); press(1)
until(lambda: location() == map_id('LilycoveCity_Harbor') and idle())
assert position() == (8, 11)
picture('native-first-cruise-arrives-lilycove')

# Actual port menu to Frontier; the arrival puts the player before the clerk.
trips = []
for city in ['Lilycove', 'Slateport']:
    # First loop continues directly from the cruise. Second continues from the
    # prior return to Slateport. No injected warp between these ferry trips.
    if city == 'Slateport':
        # The previous return went to Slateport, as selected below.
        assert location() == map_id('SlateportCity_Harbor')
    talk_up(); until(menu); choose(1)
    until(lambda: task('Task_HandleYesNoInput')); step(12)
    picture(f'{city.lower()}-frontier-confirmation')
    press(64); press(1)
    until(lambda: location() == map_id('BattleFrontier_OutsideWest') and idle())
    assert position() == (19, 67), position()
    picture(f'{city.lower()}-arrives-frontier')
    # Below the player is the actual Frontier clerk.
    step(4, 128); step(20); press(1); until(menu)
    choose(0 if city == 'Lilycove' else 1) # Return to the other port.
    until(lambda: task('Task_HandleYesNoInput')); step(12); press(1)
    dest = 'Slateport' if city == 'Lilycove' else 'Lilycove'
    until(lambda: location() == map_id(dest + 'City_Harbor') and idle())
    assert native('CountTotalItemQuantityInBag', TICKET) == 1
    picture(f'frontier-returns-{dest.lower()}')
    trips.append(dict(origin=city, via='BattleFrontier', destination=dest, ticket_quantity=1))
    if city == 'Lilycove':
        assert native('TrySavingData', 0, max_frames=6000) == 1
        assert native('LoadGameSave', 0, max_frames=6000) == 1
        # LoadGameSave alone is not Continue: it leaves live NPC objects from
        # the previous field session. Rebuild the field through the real entry.
        lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
        step(1500); until(idle)
        assert location() == map_id('SlateportCity_Harbor')
        assert position() == (8, 11)
        picture('continue-in-slateport-before-reboarding')
assert native('TrySavingData', 0, max_frames=6000) == 1
assert native('LoadGameSave', 0, max_frames=6000) == 1
lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
step(1500); until(idle)
assert location() == map_id('LilycoveCity_Harbor')
assert native('FlagGet', SCOTT) == 1
assert native('CountTotalItemQuantityInBag', TICKET) == 1
lib.stop()
result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              guards=guards, first_native_cruise_scott_invitation=True,
              physical_cabin_bed_and_arrival=True, native_ferry_trips=trips,
              ticket_not_consumed=True, native_flash_save_reload=True, native_continue_rebuilds_map=True,
              initial_port_warps_and_champion_visibility_are_fixtures=True,
              full_campaign_playthrough=False)
(args.output / 'frontier-travel.json').write_text(json.dumps(result, indent=2) + '\n')
print('Native first cruise and Frontier round trips passed', flush=True)
