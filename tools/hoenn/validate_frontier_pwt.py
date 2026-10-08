"""Run one real six-on-six PWT round on the candidate with native ferry fixes."""
from pathlib import Path
import hashlib
import json
ROOT = Path(__file__).resolve().parents[2]
exec(compile((ROOT / 'tools/hoenn/validate_pwt.py').read_text().split('\nfor pool in range(3):')[0], str(ROOT / 'tools/hoenn/validate_pwt.py'), 'exec'))
leaves = enter(2)
win = fight(0, test_bag=True)
wait_yesno()
press(128); press(1); until(idle)
assert snapshot() == original
assert points() == bp_before and flags() == flags_before and money() == money_before
assert native('TrySavingData', 0, max_frames=6000) == 1
assert native('LoadGameSave', 0, max_frames=6000) == 1
step(30)
assert snapshot() == original
lib.stop()
result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              team_size=6, native_win=win, leaves=leaves, after_win_retirement=True,
              original_party_byte_identical=True, flags_money_and_bp_unchanged=True,
              native_flash_save_reload=True, battle_stats_and_travel_are_fixtures=True,
              balance_validated=False, full_campaign_playthrough=False)
(args.output / 'frontier-pwt.json').write_text(json.dumps(result, indent=2) + '\n')
print('Native six-on-six PWT smoke on ferry candidate passed', flush=True)
