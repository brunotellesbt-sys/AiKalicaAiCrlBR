"""Walk the Seafloor Cavern from a real Dive prompt with zero badges.
Initial story/badge state, ocean position, party/stats and healing are fixtures.
No internal warps or trainer/script entry; victories and boss checks are native.
"""
from pathlib import Path
import hashlib
import json
import struct

ROOT = Path(__file__).resolve().parents[2]
exec(compile((ROOT / 'tools/hoenn/validate_team_missions.py').read_text().split('\nwins, completed =')[0],
             str(ROOT / 'tools/hoenn/validate_team_missions.py'), 'exec'))
assert (source / '.journey-aqua-episodes').exists()
for f in kanto_flags + hoenn_flags: rawflag(f, False)
native('ScriptSetMonMoveSlot', 0, 291, 2) # Dive; the party also knows Surf.
for name in ['FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN', 'FLAG_SYS_WEATHER_CTRL']:
    rawflag(abi[111] if name == 'FLAG_SYS_WEATHER_CTRL' else flag_id(name), False)
native('VarSet', 0x409F, 0)
opponents = (source / 'include/constants/opponents.h').read_text()
allowed = {int(value) for name, value in re.findall(r'^#define\s+(TRAINER_\w+)\s+(\d+)\s*$', opponents, re.M)
           if 'SEAFLOOR_CAVERN' in name}
assert {6, 7, 8, 14, 33, 567} <= allowed
for trainer in allowed: rawflag(0x500 + trainer, False)
assert flag(flag_id('FLAG_HIDE_JOURNEY_LAND_OBSTACLES'))
assert native('JourneyCanStartArchieAlliance') == 0
assert native('JourneyGymBadgeCount', 0) == native('JourneyGymBadgeCount', 1) == 0

ocean = json.loads((source / 'data/maps/Route128/map.json').read_text())
layout = layouts[ocean['layout']]
tiles = struct.unpack('<' + 'H' * (layout['width'] * layout['height']), (source / layout['blockdata_filepath']).read_bytes())
warp('Route128', 38, 28) # Only the initial ocean travel is a fixture.
candidates = sorted(((x, y) for y in range(layout['height']) for x in range(layout['width'])
                     if not tiles[y * layout['width'] + x] & 0xC00 and tiles[y * layout['width'] + x] >> 12 == 1),
                    key=lambda p: abs(p[0] - 38) + abs(p[1] - 26))
dive_point = next(p for p in candidates if native('MetatileBehavior_IsDiveable', native('MapGridGetMetatileBehaviorAt', p[0] + 7, p[1] + 7)))
warp('Route128', *dive_point)
native('SetPlayerAvatarTransitionFlags', 8); step(30)
assert native('TrySetDiveWarp') == 2
for _ in range(160):
    press(1)
    if location() == map_id('Underwater_Route128'): break
step(120); finish()
assert location() == map_id('Underwater_Route128'), ('Dive failed', location())
picture('zero-badge-dive-route128')
print('Native zero-badge Dive entered Underwater Route128', flush=True)

names = ['Underwater_Route128', 'Underwater_SeafloorCavern', 'SeafloorCavern_Entrance'] + [f'SeafloorCavern_Room{i}' for i in range(1, 10)]
exec(compile((ROOT / 'tools/hoenn/native_water_walk.py').read_text(),
             str(ROOT / 'tools/hoenn/native_water_walk.py'), 'exec'))

walk(('Underwater_SeafloorCavern', 6, 6))
assert native('TrySetDiveWarp') == 1
press(2)
for _ in range(160):
    press(1)
    if location() == map_id('SeafloorCavern_Entrance'): break
step(120); finish()
assert location() == map_id('SeafloorCavern_Entrance')
picture('native-emerge-seafloor-entrance')
print('Native resurface entered Seafloor Cavern', flush=True)
if not (source / '.journey-seafloor-access').exists():
    walk(('SeafloorCavern_Entrance', 10, 3))
    step(100, 64); step(30)
    assert location() == map_id('SeafloorCavern_Entrance') and position() == (10, 3)
    press(1); picture('native-entrance-guard-blocks-passage'); finish()
    step(100, 64); step(30)
    assert location() == map_id('SeafloorCavern_Entrance') and position() == (10, 3)
    assert not flag(flag_id('FLAG_HIDE_SEAFLOOR_CAVERN_ENTRANCE_AQUA_GRUNT'))
    lib.stop()
    (args.output / 'seafloor-baseline.json').write_text(json.dumps(dict(
        passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
        native_zero_badge_dive=True, native_resurface_into_cavern=True,
        native_entrance_guard_blocks_passage=True, position=[10, 3],
        guard_visibility_not_faked=True, full_campaign_playthrough=False), indent=2) + '\n')
    print('Native baseline guard blocks the only entrance', flush=True)
    raise SystemExit(0)
walk(('SeafloorCavern_Entrance', 10, 3))
step(4, 16); step(30); press(1)
picture('native-relocated-grunt-dialogue'); finish()
assert native('VarGet', 0x40D9) == 1
assert not flag(flag_id('FLAG_HIDE_SEAFLOOR_CAVERN_ENTRANCE_AQUA_GRUNT'))
walk(('SeafloorCavern_Room9', 16, 42))
picture('native-seafloor-route-before-archie')
assert not native('JourneyCanStartArchieAlliance')
# Step onto the real boss trigger. Permission must reject at zero badges.
for _ in range(80):
    step(1, 16)
    if not idle(): break
step(30); picture('native-archie-trigger-refuses-zero-badges'); finish()
assert position() == (17, 42), position()
assert lib.read16(s['gSpecialVar_Result']) == 0
assert not flag(flag_id('FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN'))
assert not native('JourneyCanStartArchieAlliance')
assert native('JourneyGymBadgeCount', 0) == native('JourneyGymBadgeCount', 1) == 0
assert native('TrySavingData', 0, max_frames=6000) == 1
assert native('LoadGameSave', 0, max_frames=6000) == 1
lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
step(1500); finish()
assert location() == map_id('SeafloorCavern_Room9')
assert not flag(flag_id('FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN'))
assert native('JourneyGymBadgeCount', 0) == native('JourneyGymBadgeCount', 1) == 0
if not (source / '.journey-water-continue').exists():
    # Retain the previous layer's outbound-only reproduction. Its underwater
    # Continue regression is reproduced separately by validate_water_continue.
    lib.stop()
    result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
                  dive_point=list(dive_point), native_zero_badge_dive=True, native_resurface_into_cavern=True,
                  walked_steps=walked, original_map_transitions=transitions, wins=wins, surf_prompts=surf_prompts,
                  reaches_archie_without_strength_rock_smash_flash_or_acro=True,
                  relocated_grunt_visible_and_native_dialogue_retained=True,
                  native_boss_trigger_refuses_missing_missions=True, native_save_continue_preserves_zero_badges=True,
                  no_internal_position_warps_or_event_entries=True, starting_ocean_party_stats_healing_are_fixtures=True,
                  in_battle_status_recovery_is_fixture=True,
                  wild_encounters_disabled=True, full_campaign_playthrough=False, balance_validated=False)
    (args.output / 'seafloor-route.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Native outbound Seafloor Cavern route passed', flush=True)
    raise SystemExit(0)
outbound_walked = walked
outbound_transitions = list(transitions)
outbound_surf_prompts = list(surf_prompts)

def water_state():
    return dict(map=next(n for n in ['Route128'] + names if location() == map_id(n)),
                position=list(position()), avatar_mode=lib.read8(s['gPlayerAvatar']) & 25,
                kanto_badges=native('JourneyGymBadgeCount', 1),
                hoenn_badges=native('JourneyGymBadgeCount', 0),
                kyogre_escaped=flag(flag_id('FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN')),
                archie_permission=bool(native('JourneyCanStartArchieAlliance')))

continues = []
def continue_water():
    before = water_state()
    assert native('TrySavingData', 0, max_frames=6000) == 1
    assert native('LoadGameSave', 0, max_frames=6000) == 1
    lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
    step(1500); finish()
    after = water_state()
    assert before == after, (before, after)
    continues.append(dict(before=before, after=after))

# Retrace native passages and currents, without internal map/position writes.
walk(('SeafloorCavern_Entrance', 10, 17))
assert native('TrySetDiveWarp') == 2
for _ in range(160):
    press(1)
    if location() == map_id('Underwater_SeafloorCavern'): break
step(120); finish()
assert location() == map_id('Underwater_SeafloorCavern')
picture('native-return-dive-underwater-cavern')
continue_water()
picture('native-underwater-return-after-continue')
walk(('Underwater_Route128', *dive_point))
assert native('TrySetDiveWarp') == 1
continue_water()
press(2)
for _ in range(160):
    press(1)
    if location() == map_id('Route128'): break
step(120); finish()
assert location() == map_id('Route128') and lib.read8(s['gPlayerAvatar']) & 8
picture('native-return-surface-route128')
continue_water()
picture('native-route128-return-after-continue')
lib.stop()
result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              dive_point=list(dive_point), native_zero_badge_dive=True, native_resurface_into_cavern=True,
              walked_steps=outbound_walked, original_map_transitions=outbound_transitions, wins=wins, surf_prompts=outbound_surf_prompts,
              return_walked_steps=walked - outbound_walked, return_map_transitions=transitions[len(outbound_transitions):],
              return_surf_prompts=surf_prompts[len(outbound_surf_prompts):],
              native_dive_out_and_return_to_route128=True, water_save_continues=continues,
              in_battle_status_recovery_is_fixture=True,
              reaches_archie_without_strength_rock_smash_flash_or_acro=True,
              relocated_grunt_visible_and_native_dialogue_retained=True,
              native_boss_trigger_refuses_missing_missions=True, native_save_continue_preserves_zero_badges=True,
              no_internal_position_warps_or_event_entries=True, starting_ocean_party_stats_healing_are_fixtures=True,
              wild_encounters_disabled=True, full_campaign_playthrough=False, balance_validated=False)
(args.output / 'seafloor-route.json').write_text(json.dumps(result, indent=2) + '\n')
print('Native Seafloor Cavern route passed', flush=True)
