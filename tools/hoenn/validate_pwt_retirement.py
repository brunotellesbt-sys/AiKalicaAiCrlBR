"""Decline a round through controller input and check the native restoration."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
prefix=(ROOT/'tools/hoenn/validate_pwt_world.py').read_text().split('for generation in range(cap+1):')[0]
exec(compile(prefix,str(ROOT/'tools/hoenn/validate_pwt_world.py'),'exec'))
begin(1);warp('JourneyPWTArena',9,6)
press(2)
for _ in range(300):
    if task('Task_HandleYesNoInput'):break
    press(1)
assert task('Task_HandleYesNoInput')
assert position()==(9,6),('Entrance camera/position mismatch',position())
picture('pwt-round-ready')
step(12);press(2)
for _ in range(300):
    if location()==map_id('JourneyPWTLobby') and not lib.read8(s['sLockFieldControls']):break
    press(1)
assert location()==map_id('JourneyPWTLobby')
assert bytes(lib.read8(party+i) for i in range(6*abi[2]))==original
assert lib.read16(bp_at)==bp_before
assert not lib.read8(state+offsets[4])
picture('pwt-retired-original-party')
lib.stop()
(args.output/'pwt-retirement.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),declined_round_with_controller=True,original_party_restored_byte_exact=True,no_bp_reward_for_retirement=True,player_ready_position=[9,6],travel_and_registration_are_fixtures=True),indent=2)+'\n')
