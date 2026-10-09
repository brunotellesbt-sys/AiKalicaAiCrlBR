"""Walk the early Sky Pillar without awakening Rayquaza or clearing missions.
Initial travel, party, badges and story are fixtures; tower travel is native.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
exec(compile((ROOT / 'tools/hoenn/validate_team_missions.py').read_text().split('\nwins, completed =')[0],
             str(ROOT / 'tools/hoenn/validate_team_missions.py'), 'exec'))
for f in kanto_flags + hoenn_flags: rawflag(f, False)
for var in [0x405E, 0x40CA, 0x40D7]: native('VarSet', var, 0)
for name in ['FLAG_WALLACE_GOES_TO_SKY_PILLAR', 'FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN']:
    rawflag(flag_id(name), False)
rawflag(abi[111], False)
names = ['SkyPillar_Outside'] + [f'SkyPillar_{i}F' for i in range(1, 6)] + ['SkyPillar_Top']
walk_layout_overrides = {f'SkyPillar_{i}F': f'LAYOUT_SKY_PILLAR_{i}F_CLEAN' for i in range(1, 6)}
walk_layout_overrides['SkyPillar_Top'] = 'LAYOUT_SKY_PILLAR_TOP_CLEAN'
allowed = set()
walk_prefix = 'sky-pillar'
exec(compile((ROOT / 'tools/hoenn/native_water_walk.py').read_text(),
             str(ROOT / 'tools/hoenn/native_water_walk.py'), 'exec'))
hole_behaviors = {b for b in set(behaviors['SkyPillar_4F']) if native('MetatileBehavior_IsCrackedFloorHole', b)
                  or native('MetatileBehavior_IsCrackedFloor', b)}
walk_hole_destinations = {('SkyPillar_4F', i % blocks['SkyPillar_4F'][0], i // blocks['SkyPillar_4F'][0]):
                          ('SkyPillar_3F', i % blocks['SkyPillar_4F'][0], i // blocks['SkyPillar_4F'][0])
                          for i, b in enumerate(behaviors['SkyPillar_4F']) if b in hole_behaviors}
candidate = (source / '.journey-sky-pillar-access').exists()
saves = []

def state():
    return dict(map=by_location[location()], position=list(position()),
                mode=lib.read8(s['gPlayerAvatar']) & 25,
                sky_state=native('VarGet', 0x40CA), sootopolis_state=native('VarGet', 0x405E),
                cry_done=native('VarGet', 0x40D7), weather_crisis=flag(abi[111]),
                archie_completed=flag(flag_id('FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN')),
                kanto_badges=native('JourneyGymBadgeCount', 1), hoenn_badges=native('JourneyGymBadgeCount', 0),
                special_capture_unlocked=bool(native('JourneySpecialUnlocked')))

def checkpoint(label):
    before = state()
    for key in ['sky_state', 'sootopolis_state', 'cry_done', 'kanto_badges', 'hoenn_badges']:
        assert before[key] == 0, (key, before)
    for key in ['weather_crisis', 'archie_completed', 'special_capture_unlocked']: assert not before[key]
    assert native('TrySavingData', 0, max_frames=6000) == 1
    assert native('LoadGameSave', 0, max_frames=6000) == 1
    lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
    step(1500); finish()
    after = state(); assert before == after, (label, before, after)
    saves.append(dict(label=label, before=before, after=after))
    picture(label + '-after-continue')

warp('SkyPillar_Outside', 14, 6) # The only initial travel fixture.
native('SetPlayerAvatarTransitionFlags', 1); step(30)
refresh_loaded_warp_tiles()
if candidate:
    assert not native('JourneyCanAwakenRayquaza')
    walk(('SkyPillar_Top', 14, 10))
    clean = layouts['LAYOUT_SKY_PILLAR_TOP_CLEAN']['name']
    assert lib.read32(s['gMapHeader']) == s[clean], 'Native summit did not select its clean layout'
    # Trigger the original coordinate event through the controller.
    for _ in range(80):
        step(1, 64)
        if not idle(): break
    step(190); picture('rayquaza-early-awakening-refused'); finish()
    assert position() == (14, 9), position()
    assert lib.read16(s['gSpecialVar_Result']) == 0
    checkpoint('sky-pillar-summit')
    walk(('SkyPillar_1F', 6, 12))
    checkpoint('sky-pillar-first-floor')
    walk(('SkyPillar_Outside', 14, 6))
    checkpoint('sky-pillar-return')
    walk(('SkyPillar_1F', 6, 12))
    walk(('SkyPillar_Outside', 14, 6))
else:
    step(100, 64); step(30)
    assert location() == map_id('SkyPillar_Outside') and position() == (14, 6)
    assert native('MapGridGetCollisionAt', 21, 12) != 0
    picture('sky-pillar-baseline-door-closed')
assert not wins
lib.stop()
result = dict(passed=True, candidate=candidate,
              rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              native_closed_door_reproduced=not candidate,
              native_full_tower_walk_return_and_reentry=candidate,
              native_early_awakening_trigger_refused=candidate,
              native_clean_summit_layout=candidate, position_changes=walked, transitions=transitions,
              save_continue=saves, initial_story_badges_party_outside_position_are_fixtures=True,
              no_internal_warps_after_initial_placement=True, wild_encounters_disabled=True,
              full_campaign_playthrough=False, balance_validated=False)
(args.output / 'sky-pillar-access.json').write_text(json.dumps(result, indent=2) + '\n')
print('Native Sky Pillar access passed:', candidate, flush=True)
