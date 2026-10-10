"""Physically trigger Wanda's reunion from the west and east approach tiles.
Initial location, Peeko rescue and party are fixtures. No Rock Smash, synthetic
reunion completion, trainer victories or full campaign playthrough are claimed.
"""
from pathlib import Path
import hashlib
import json
import re
import subprocess
ROOT = Path(__file__).resolve().parents[2]
exec(compile((ROOT / 'tools/hoenn/validate_abilities.py').read_text().split('\nability_field,')[0],
             str(ROOT / 'tools/hoenn/validate_abilities.py'), 'exec'))
fields = ['FLAG_RECOVERED_DEVON_GOODS', 'FLAG_RUSTURF_TUNNEL_OPENED', 'FLAG_RECEIVED_HM_STRENGTH',
    'FLAG_HIDE_RUSTURF_TUNNEL_WANDA', 'FLAG_HIDE_RUSTURF_TUNNEL_WANDAS_BOYFRIEND',
    'VAR_RUSTURF_TUNNEL_STATE', 'ITEM_TM_STRENGTH']
assembly = subprocess.run([str(ROOT / '.local/arm-gcc/usr/bin/arm-none-eabi-gcc'), '-S',
    '-mabi=apcs-gnu', '-iquote', str(source / 'include'), '-x', 'c', '-', '-o', '-'],
    input='#include "global.h"\n#include "constants/vars.h"\n#include "constants/flags.h"\n#include "constants/items.h"\nconst u32 reunion_ids[] = {' + ','.join(fields) + '};',
    text=True, capture_output=True, check=True).stdout
ids = dict(zip(fields, [int(n) for n in re.findall(r'\.word\s+(\d+)', assembly.split('reunion_ids:', 1)[1].split('.size', 1)[0])]))
def flag(name):
    f = ids[name]
    return bool(lib.read8(save() + 4720 + f // 8) & (1 << (f & 7)))
def rawflag(name, enabled):
    f = ids[name]; a = save() + 4720 + f // 8; value = lib.read8(a); mask = 1 << (f & 7)
    lib.write8(a, value | mask if enabled else value & ~mask)
def idle():
    return (lib.read32(s['gMain'] + 4) & ~1) == s['CB2_Overworld'] and not lib.read8(s['sLockFieldControls'])
def finish():
    for tick in range(1200):
        assert (lib.read32(s['gMain'] + 4) & ~1) != s['BattleMainCB2']
        if tick >= 20 and idle(): return
        press(1)
    picture('reunion-stuck')
    raise AssertionError(('Reunion stuck', location(), position()))
def count(): return native('CountTotalItemQuantityInBag', ids['ITEM_TM_STRENGTH'])
def reset(rescued):
    warp('RustboroCity', 20, 30)
    for name in fields[:5]: rawflag(name, False)
    rawflag('FLAG_RECOVERED_DEVON_GOODS', rescued)
    native('VarSet', ids['VAR_RUSTURF_TUNNEL_STATE'], 3 if rescued else 0)
    quantity = count()
    if quantity: assert native('RemoveBagItem', ids['ITEM_TM_STRENGTH'], quantity)

def approach(x, y, key):
    warp('RusturfTunnel', x, y)
    step(120)
    step(40, key); step(60)
    finish()

assert native('ScriptGiveMon', 7, 5, 0) == 0
for slot in range(4): native('ScriptSetMonMoveSlot', 0, 0, slot)
assert native('JourneyGymBadgeCount', 1) == native('JourneyGymBadgeCount', 0) == 0
fixed = (source / '.journey-rusturf-reunion').exists()
cases = []
for x, y, key, pos in [(22, 4, 16, 1), (26, 5, 32, 3)]:
    reset(False); approach(x, y, key)
    assert not flag('FLAG_RUSTURF_TUNNEL_OPENED') and count() == 0
    reset(True)
    rawflag('FLAG_HIDE_RUSTURF_TUNNEL_WANDA', True)
    rawflag('FLAG_HIDE_RUSTURF_TUNNEL_WANDAS_BOYFRIEND', True)
    approach(x, y, key)
    assert not flag('FLAG_RUSTURF_TUNNEL_OPENED') and count() == 0
    reset(True); approach(x, y, key)
    if not fixed:
        assert not flag('FLAG_RUSTURF_TUNNEL_OPENED') and count() == 0
        cases.append(dict(approach=pos, rescued=True, original_rock_smash_scene_unreachable=True))
        continue
    assert flag('FLAG_RUSTURF_TUNNEL_OPENED') and flag('FLAG_RECEIVED_HM_STRENGTH'), (pos, position())
    assert flag('FLAG_HIDE_RUSTURF_TUNNEL_WANDA') and flag('FLAG_HIDE_RUSTURF_TUNNEL_WANDAS_BOYFRIEND')
    assert count() == 1
    picture('rusturf-reunion-' + str(pos))
    before = dict(opened=True, reward=count(), state=native('VarGet', ids['VAR_RUSTURF_TUNNEL_STATE']))
    assert native('TrySavingData', 0, max_frames=6000) == 1
    assert native('LoadGameSave', 0, max_frames=6000) == 1
    lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
    step(1500); finish()
    assert flag('FLAG_RUSTURF_TUNNEL_OPENED') and count() == before['reward']
    warp('RustboroCity', 20, 30); approach(x, y, key)
    assert count() == 1 and flag('FLAG_RUSTURF_TUNNEL_OPENED')
    assert native('JourneyGymBadgeCount', 1) == native('JourneyGymBadgeCount', 0) == 0
    cases.append(dict(approach=pos, pre_rescue_does_not_complete=True, hidden_couple_does_not_start_scene=True, scene_triggered_by_walking=True,
        original_couple_exit=True, tm_strength_quantity=1, native_continue=True, revisit_no_duplicate=True,
        no_moves_or_badges=True))
lib.stop()
report = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
    baseline_unreachable_reproduced=not fixed, cases=cases,
    initial_location_rescue_and_party_are_fixtures=True, full_campaign_playthrough=False)
(args.output / ('rusturf-reunion.json' if fixed else 'baseline.json')).write_text(json.dumps(report, indent=2) + '\n')
print('Native Rusturf reunion validation passed.', flush=True)
