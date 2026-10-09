"""Win Shelly/Matt by talking to native NPCs and check free-order gym gates.
Travel, arbitrary badges/prior missions and later Silph/Space Center completion
are fixtures. The two battles, Castform and submarine departure are native.
"""
from pathlib import Path
import hashlib
import json
ROOT = Path(__file__).resolve().parents[2]
exec(compile((ROOT / 'tools/hoenn/validate_team_missions.py').read_text().split('\nwins, completed =')[0],
             str(ROOT / 'tools/hoenn/validate_team_missions.py'), 'exec'))

# Decline gift nicknames through the actual yes/no menu.
def finish(limit=300):
    for _ in range(limit):
        if idle(): return
        if task('Task_HandleYesNoInput'):
            step(12); press(128); press(1)
        else: press(1)
    picture('aqua-episode-dialogue-failure')
    raise AssertionError(('Episode dialogue stuck', location(), position()))

fixed = (source / '.journey-aqua-episodes').exists()
for t in stories['trainers']:
    if t['mission'] == 'hoenn_rocket': rawflag(0x500 + t['id'], True)
native('VarSet', 0x40B3, 0)
for name in ['FLAG_HIDE_ROUTE_119_TEAM_AQUA', 'FLAG_HIDE_AQUA_HIDEOUT_GRUNTS',
             'FLAG_HIDE_AQUA_HIDEOUT_B2F_SUBMARINE_SHADOW',
             'FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE', 'FLAG_RECEIVED_CASTFORM']:
    rawflag(flag_id(name), False)
rawflag(0x500 + 32, False); rawflag(0x500 + 30, False)
if not fixed:
    assert pending(False) == 0
    doors = [door_probe('FortreeCity', False)]
    rawflag(hoenn_flags[0], True)
    rawflag(hoenn_flags[2], True)
    rawflag(flag_id('FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT'), True)
    assert pending(False) == 0
    doors.append(door_probe('FortreeCity', False))
    rawflag(hoenn_flags[5], True)
    native('VarSet', 0x409F, 3)
    rawflag(flag_id('FLAG_HIDE_SAFFRON_ROCKETS'), True)
    assert native('JourneyCanStartArchieAlliance') == 1
    assert not flag(0x500 + 32) and not flag(0x500 + 30)
    assert native('VarGet', 0x40B3) == 0
    assert not flag(flag_id('FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE'))
    lib.stop()
    result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
                  shelly_and_matt_can_be_skipped=True, native_gym_doors=doors,
                  archie_permission_without_either_episode=True,
                  flags_badges_prior_missions_travel_are_fixtures=True)
    (args.output / 'aqua-episodes-baseline.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Baseline permits skipping both native Aqua episodes', flush=True)
    raise SystemExit(0)
kanto_before = [flag(f) for f in kanto_flags]
assert pending(False) == 15 and pending(True) == 7
doors = [door_probe('FortreeCity', True)]

def talk(name, x, y, direction):
    native('HealPlayerParty')
    warp(name, x, y)
    assert native('MapGridGetCollisionAt', x + 7, y + 7) == 0
    step(4, direction); step(30); press(1)

talk('Route119_WeatherInstitute_2F', 5, 6, 32)
shelly = fight(dict(id=32, map='Route119_WeatherInstitute_2F', mission='weather_institute'))
assert native('VarGet', 0x40B3) == 1
assert flag(flag_id('FLAG_RECEIVED_CASTFORM'))
assert lib.read8(s['gPartiesCount']) == 4
assert native('GetMonData2', party + 3 * abi[2], abi[7]) == 351
assert pending(False) == 0 and pending(True) == 7
assert [flag(f) for f in kanto_flags + hoenn_flags] == badges_before
picture('shelly-defeated-castform-received')
doors.append(door_probe('FortreeCity', False))
assert native('TrySavingData', 0, max_frames=6000) == 1
assert native('LoadGameSave', 0, max_frames=6000) == 1
lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
step(1500); finish()
assert native('VarGet', 0x40B3) == 1 and flag(0x500 + 32)
assert flag(flag_id('FLAG_RECEIVED_CASTFORM'))

rawflag(hoenn_flags[0], True) # Fifth arbitrary badge; Magma Hideout remains required.
assert pending(False) == 4
rawflag(flag_id('FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT'), True) # Earlier episode fixture.
assert pending(False) == 0
rawflag(hoenn_flags[2], True) # Sixth badge, leaving Fortree/Mossdeep unwon.
badges_before_matt = [flag(f) for f in kanto_flags + hoenn_flags]
assert pending(False) == 16 and pending(True) == 7
doors.append(door_probe('FortreeCity', True))
talk('AquaHideout_B2F', 24, 19, 32)
matt = fight(dict(id=30, map='AquaHideout_B2F', mission='aqua_hideout'))
assert flag(flag_id('FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE'))
assert flag(flag_id('FLAG_HIDE_LILYCOVE_CITY_AQUA_GRUNTS'))
assert pending(False) == 0 and pending(True) == 7
assert [flag(f) for f in kanto_flags + hoenn_flags] == badges_before_matt
picture('matt-defeated-submarine-departed')
doors.append(door_probe('FortreeCity', False))

# Later story still requires seven Hoenn badges, Space Center victory and Silph.
assert native('VarGet', 0x409F) == 0
assert not native('JourneyCanStartArchieAlliance')
rawflag(hoenn_flags[5], True)
native('JourneyStartSpaceCenterInvasion')
assert native('VarGet', 0x409F) == 1 and pending(False) == 5
native('VarSet', 0x409F, 3) # Later Space Center fixture.
assert pending(False) == 13 and not native('JourneyCanStartArchieAlliance')
rawflag(flag_id('FLAG_HIDE_SAFFRON_ROCKETS'), True) # Later Silph fixture.
assert pending(False) == 6 and native('JourneyCanStartArchieAlliance')
assert [flag(f) for f in kanto_flags] == kanto_before
assert native('TrySavingData', 0, max_frames=6000) == 1
assert native('LoadGameSave', 0, max_frames=6000) == 1
lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
step(1500); finish()
assert flag(0x500 + 32) and flag(0x500 + 30)
assert native('VarGet', 0x40B3) == 1
assert flag(flag_id('FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE'))
assert native('JourneyCanStartArchieAlliance')
picture('aqua-episodes-retained-after-continue')
lib.stop()
result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              native_npc_interactions=True, native_interaction_tiles_walkable=True, wins=[shelly, matt], doors=doors,
              shelly_at_four_badges=True, matt_at_six_badges=True,
              original_castform_received=True, original_submarine_departed=True,
              wins_do_not_award_badges=True, kanto_missions_and_badges_unchanged=True,
              native_save_reload_continue=True, magma_space_center_and_silph_still_required=True,
              travel_badges_earlier_missions_later_scenes_and_battle_stats_are_fixtures=True,
              balance_validated=False, full_campaign_playthrough=False)
(args.output / 'aqua-episodes.json').write_text(json.dumps(result, indent=2) + '\n')
print('Native Shelly/Matt episodes and free-order gym progression passed', flush=True)
