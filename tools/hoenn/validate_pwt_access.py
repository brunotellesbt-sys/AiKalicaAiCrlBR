"""Use the actual Dome guide, PWT receptionist and exit door in mGBA."""
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
options = parser.parse_args()
sys.argv = [sys.argv[0], '--source', str(options.source), '--library', str(options.library), '--output', str(options.output)]
exec(compile((ROOT / 'tools/hoenn/validate_abilities.py').read_text().split('\nability_field,')[0], str(ROOT / 'tools/hoenn/validate_abilities.py'), 'exec'))

def until(predicate, limit=200):
    for _ in range(limit):
        if predicate(): return
        press(1)
    picture('pwt-access-failure')
    raise AssertionError(('PWT access incomplete', location(), position()))

def idle():
    return (lib.read32(s['gMain'] + 4) & ~1) == s['CB2_Overworld'] and not lib.read8(s['sLockFieldControls'])

def walk(key, axis, target):
    for _ in range(300):
        if position()[axis] == target:
            step(30)
            return
        step(1, key)
    raise AssertionError(('PWT lobby walk blocked', position(), axis, target))

for species in [658, 149, 376]: assert native('ScriptGiveMon', species, 20, 0) == 0
warp('BattleFrontier_BattleDomeLobby', 8, 15)
step(4, 64); step(20); press(1)
until(lambda: task('Task_HandleYesNoInput')); step(12)
picture('pwt-guide-in-dome')
press(1); until(idle)
assert location() == map_id('JourneyPWTLobby')
assert position() == (11, 14)
picture('pwt-independent-reception')
# Walk through the actual lobby floor to the counter, with no injected warp.
walk(32, 0, 5)
assert position() == (5, 14), position()
walk(64, 1, 11)
assert position() == (5, 11), position()
press(1)
until(lambda: task('Task_HandleYesNoInput')); step(12)
picture('pwt-physical-counter')
press(1)
until(lambda: task('Task_HandleChooseMonInput')); step(120)
press(2)
until(lambda: task('Task_HandleCancelChooseMonYesNoInput'))
press(64); press(1); until(idle)
assert location() == map_id('JourneyPWTLobby')
walk(128, 1, 14)
walk(16, 0, 11)
for _ in range(100):
    step(4, 128)
    if location() == map_id('BattleFrontier_BattleDomeLobby'): break
else: raise AssertionError(('PWT exit not connected to Dome', location(), position()))
step(900)
picture('pwt-exit-to-dome')
lib.stop()
result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              native_guide_interaction=True, physical_counter_walk=True, native_selection_cancel=True,
              physical_exit_door_returns_to_dome=True, initial_dome_warp_is_fixture=True,
              full_frontier_journey_validated=False)
(args.output / 'pwt-access.json').write_text(json.dumps(result, indent=2) + '\n')
print('Native PWT guide, counter and exit passed', flush=True)
