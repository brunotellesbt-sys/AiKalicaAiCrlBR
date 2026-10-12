"""Exercise No and B before committing a home, using controller input only."""
import argparse, hashlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--source', type=Path, required=True)
p.add_argument('--library', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
options = p.parse_args()
sys.argv = [sys.argv[0], '--source', str(options.source), '--library', str(options.library), '--output', str(options.output), '--region', 'hoenn']
exec(compile((ROOT / 'tools/hoenn/validate_campaign_playthrough.py').read_text().split('step(600)')[0], str(ROOT / 'tools/hoenn/validate_campaign_playthrough.py'), 'exec'))
def active(name):
    return any(lib.read8(s['gTasks'] + j*40 + 4) and lib.read32(s['gTasks'] + j*40) & ~1 == s[name] for j in range(16))
def wait_for(name, frames=16000):
    for _ in range(frames//30):
        if active(name):
            step(30)
            return
        action(1, 1, 29)
    raise AssertionError((name, map_name()))
sha = hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest()
step(600)
wait_for('Task_HandleMultichoiceInput')
action()  # Hoenn in the early professor selection.
wait_for('Task_HandleMultichoiceGridInput')
assert map_name() == 'InsideOfTruck'
action()  # Littleroot.
wait_for('Task_HandleYesNoInput')
picture('named-city-confirmation')
action(128); action()  # No must return to the city grid.
wait_for('Task_HandleMultichoiceGridInput')
picture('no-returns-to-cities')
action(2)  # B must reopen regions.
wait_for('Task_HandleMultichoiceInput')
picture('back-returns-to-regions')
action(128); action()  # Kanto.
wait_for('Task_HandleMultichoiceGridInput')
action()  # Pallet.
wait_for('Task_HandleYesNoInput')
picture('pallet-confirmation')
action()  # Yes commits Pallet only now.
for _ in range(100):
    if callback() == s['CB2_Overworld'] and not locked():
        break
    action()
assert map_name() == 'InsideOfTruck' and not locked()
for _ in range(35):
    action(16, 8, 20)
    if map_name() != 'InsideOfTruck':
        break
for _ in range(140):
    action()
    if callback() == s['CB2_Overworld'] and not locked():
        break
assert map_name() == 'PalletTown_PlayersHouse_2F_Frlg', map_name()
checkpoint('confirmed-pallet-arrival')
lib.stop()
assert hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest() == sha
(args.output / 'birth-confirmation.json').write_text(json.dumps(dict(passed=True, rom_sha256=sha, controller_only=True, ram_writes=False, script_injection=False, no_returns_to_city_menu=True, b_returns_to_region_menu=True, changed_region_arrival='PalletTown_PlayersHouse_2F_Frlg', checkpoints=checkpoints, input_log=inputs), indent=2)+'\n')
print('Birth confirmation, No, B and changed-region arrival passed', flush=True)
