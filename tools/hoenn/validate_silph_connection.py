"""Win Giovanni at Silph and verify the mandatory cross-region alliance.
Earlier mission wins, badges/Space Center and initial travel are fixtures.
Silph's battle, completion and alliance unlock are native events.
"""
from pathlib import Path
import hashlib
import json
import struct
ROOT = Path(__file__).resolve().parents[2]
exec(compile((ROOT / 'tools/hoenn/validate_team_missions.py').read_text().split('\nwins, completed =')[0], str(ROOT / 'tools/hoenn/validate_team_missions.py'), 'exec'))
for t in stories['trainers']: rawflag(0x500 + t['id'], True)
for i, f in enumerate(kanto_flags): rawflag(f, i in {0, 1, 2, 3, 7})
for i, f in enumerate(hoenn_flags): rawflag(f, i != 0)
rawflag(flag_id('FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT'), True)
rawflag(flag_id('FLAG_HIDE_SAFFRON_ROCKETS'), False)
rawflag(flag_id('FLAG_HIDE_SILPH_ROCKETS'), False)
rawflag(0x500 + 1103, False)
native('VarSet', 0x409F, 3)
native('VarSet', 0x4160, 0)
assert native('JourneyCanChallengeSilph') == 0
assert native('JourneyCanStartArchieAlliance') == 0
assert pending(False) == 13
# Obtain the original Card Key by talking to its item ball on 5F, then
# open the native 11F door. These are real item/door events, not receipt flags.
warp('SilphCo_5F_Frlg', 22, 22)
step(4, 64); step(20); press(1); finish()
assert native('CheckBagHasItem', 750, 1) == 1
assert flag(flag_id('FLAG_HIDE_SILPH_CO_5F_CARD_KEY'))
picture('silph-card-key-received')
warp('SilphCo_11F_Frlg', 5, 18)
step(4, 64); step(20); press(1); finish()
assert flag(flag_id('FLAG_SILPH_11F_DOOR'))
picture('silph-native-card-door-opened')
for _ in range(160):
    step(1, 64)
    if lib.read8(s['sLockFieldControls']): break
assert position() == (5, 15), position()
step(30)
picture('silph-five-badges-denial-message')
for _ in range(150):
    assert (lib.read32(s['gMain'] + 4) & ~1) != s['BattleMainCB2']
    if idle(): break
    press(1)
else: raise AssertionError('Silph early denial did not finish')
assert not flag(flag_id('FLAG_HIDE_SAFFRON_ROCKETS'))
assert not flag(0x500 + 1103)
picture('silph-five-badges-denied')
rawflag(kanto_flags[4], True) # Six arbitrary Kanto badges, with 5 and 6 unwon.
badges_before = [flag(f) for f in kanto_flags + hoenn_flags]
assert native('JourneyCanChallengeSilph') == 1
assert native('JourneyCanStartArchieAlliance') == 0
assert pending(True) == 2 and pending(False) == 13
# Walk onto the actual coordinate trigger, preserving Giovanni's approach.
assert native('VarGet', 0x4160) == 0
warp('SilphCo_11F_Frlg', 5, 18)
for _ in range(160):
    step(1, 64)
    if lib.read8(s['sLockFieldControls']): break
assert position() == (5, 15), position()
step(30)
win = fight(dict(id=1103, map='SilphCo_11F_Frlg', mission='silph_giovanni'))
assert flag(flag_id('FLAG_HIDE_SAFFRON_ROCKETS'))
assert native('VarGet', 0x4160) == 1
assert [flag(f) for f in kanto_flags + hoenn_flags] == badges_before
assert pending(True) == 0
assert native('JourneyCanStartArchieAlliance') == 1
assert pending(False) == 6
picture('silph-giovanni-defeated')
doors.append(door_probe('CinnabarIsland_Frlg', False))
warp('Route128', 20, 10)
assert native('JourneyCanStartArchieAlliance') == 1
assert pending(False) == 6
assert native('TrySavingData', 0, max_frames=6000) == 1
assert native('LoadGameSave', 0, max_frames=6000) == 1
lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
step(1500); finish()
assert native('JourneyCanStartArchieAlliance') == 1
assert flag(flag_id('FLAG_HIDE_SAFFRON_ROCKETS'))
assert native('VarGet', 0x4160) == 1
assert native('FlagGet', 0x500 + 1103) == 1
assert [flag(f) for f in kanto_flags + hoenn_flags] == badges_before
picture('hoenn-silph-alliance-retained-after-continue')
lib.stop()
result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              five_kanto_badges_denied_without_battle=True, physical_silph_coordinate_trigger=True,
              native_card_key_pickup=True, native_card_key_door_opened=True,
              native_giovanni_win=win, silph_completion_from_native_scene=True,
              hoenn_event_before=13, hoenn_event_after=6, alliance_before=False, alliance_after=True,
              checked_in_kanto_and_hoenn=True, native_save_reload_continue=True,
              badges_unchanged=True, unwon_kanto_gym_opened=True,
              earlier_missions_badges_space_center_travel_and_battle_stats_are_fixtures=True,
              balance_validated=False, full_campaign_playthrough=False)
(args.output / 'silph-connection.json').write_text(json.dumps(result, indent=2) + '\n')
print('Native Silph victory unlocked the mandatory Giovanni alliance in Hoenn', flush=True)
