"""Land on each new islet, defeat its actual trainer and retain its private flag."""
import hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
text = (ROOT / 'tools/hoenn/validate_team_missions.py').read_text()
exec(compile(text.split('\nassert pending(True) == 7')[0], __file__, 'exec'))
fight_code = 'def fight(t):' + text.split('\ndef fight(t):', 1)[1].split('\nwins, completed =', 1)[0]
fight_code = fight_code.replace("native('FlagGet', 0x500 + t['id'])", "native('HasTrainerBeenFought', t['id'])")
exec(compile(fight_code, __file__, 'exec'))
islands = json.loads((source / '.journey-surf-cave-coasts').read_text())['islands']
names = [i['map'] for i in islands]; allowed = set(); walk_prefix = 'beach'; walk_cache_paths = True
native('ScriptSetMonMoveSlot', 0, 57, 1)
exec(compile((ROOT / 'tools/hoenn/native_water_walk.py').read_text(), __file__, 'exec'))
checks = []
for island in islands:
    n = island['map']; t = island['trainer']; native('ClearTrainerFlag', t['id']); native('HealPlayerParty')
    # Approach from the side, outside the trainer's downward sight line, so
    # landing and the A interaction are both visible native actions.
    w, h, v = blocks[n]
    _, y, x = min((abs(x - (t['x'] + 4)) + abs(y - t['y']), y, x) for y in range(h) for x in range(w)
                  if y * w + x in passable[n] and v[y * w + x] in [0x112B, 0x1170])
    start = (n, x, y); warp(*start); native('SetPlayerAvatarTransitionFlags', 8); step(30)
    walk((n, t['x'] + 1, t['y'])); assert lib.read8(s['gPlayerAvatar']) & 25 == 1
    unrelated_flag_before = native('FlagGet', 0x500 + t['id'])
    step(1, 32); step(16); press(1)
    win = fight(dict(t, map=n, mission=None)); assert native('FlagGet', t['flag'])
    assert native('FlagGet', 0x500 + t['id']) == unrelated_flag_before, 'New trainer overwrote an unrelated system flag'
    picture(n + '-trainer-defeated'); walk(start); assert lib.read8(s['gPlayerAvatar']) & 8
    checks.append(dict(map=n, trainer=t['id'], flag=t['flag'], native_landing_and_surf_return=True,
                       interacted_with_A=True, won_native_battle=True, private_defeated_flag=True, attacks=win['attacks']))
assert native('TrySavingData', 0, max_frames=6000) == 1 and native('LoadGameSave', 0, max_frames=6000) == 1
lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1); step(1500); finish()
assert all(native('HasTrainerBeenFought', t['trainer']) for t in checks)
lib.stop(); (args.output / 'beach-trainers.json').write_text(json.dumps(dict(passed=True,
    rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(), islands=checks,
    save_continue_retains_all_private_flags=True, native_controller_battles=True,
    initial_placements_party_and_boosted_battle_stats_are_fixtures=True, balance_playthrough=False), indent=2) + '\n')
