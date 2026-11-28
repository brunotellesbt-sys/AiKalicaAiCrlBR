"""Decline a round through controller input and check the native restoration."""
from pathlib import Path
import argparse, hashlib, json, sys
ROOT=Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--expect-offset-regression', action='store_true')
diagnostic, rest = parser.parse_known_args()
sys.argv = [sys.argv[0], *rest]
prefix=(ROOT/'tools/hoenn/validate_pwt_world.py').read_text().split('for generation in range(cap+1):')[0]
exec(compile(prefix,str(ROOT/'tools/hoenn/validate_pwt_world.py'),'exec'))
# Draw the same opponent on both sides of the visual regression test.
draw_seed = 101
native('SeedRng', draw_seed)
begin(1);warp('JourneyPWTArena',9,6)
press(2)
step(100)
assert not task('Task_HandleYesNoInput')
assert lib.read32(s['gMain'] + 4) & ~1 == s['CB2_Overworld']
presentation = observe_ready_positions()
picture('pwt-opponent-presentation')
for _ in range(300):
    if task('Task_HandleYesNoInput'):break
    press(1)
assert task('Task_HandleYesNoInput')
entrance = observe_ready_positions()
assert entrance == presentation
if diagnostic.expect_offset_regression:
    assert entrance['player'] == [9, 6] and entrance['opponent_start'] == [10, -1], entrance
    assert entrance['opponent'] == [6, -1], entrance
else:
    check_ready_positions(entrance)
step(12)
picture('pwt-round-ready')
press(2)
for _ in range(300):
    if location()==map_id('JourneyPWTLobby') and not lib.read8(s['sLockFieldControls']):break
    press(1)
assert location()==map_id('JourneyPWTLobby')
assert bytes(lib.read8(party+i) for i in range(6*abi[2]))==original
assert lib.read16(bp_at)==bp_before
assert not lib.read8(state+offsets[4])
picture('pwt-retired-original-party')
lib.stop()
capture_sha = hashlib.sha256((args.output/'pwt-round-ready.png').read_bytes()).hexdigest()
(args.output/'pwt-retirement.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),elf_sha256=hashlib.sha256((source/'pokeemerald.elf').read_bytes()).hexdigest(),
    draw_seed=draw_seed,offset_regression_observed=diagnostic.expect_offset_regression,capture_sha256=capture_sha,
    presentation_sha256=hashlib.sha256((args.output/'pwt-opponent-presentation.png').read_bytes()).hexdigest(),
    declined_round_with_controller=True,original_party_restored_byte_exact=True,no_bp_reward_for_retirement=True,player_ready_position=entrance['player'],entrance=entrance,travel_and_registration_are_fixtures=True),indent=2)+'\n')
