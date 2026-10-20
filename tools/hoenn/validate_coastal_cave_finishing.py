"""Load all nine complete coastal mountains and enter each cave twice.

Each route starts with one explicit Surf-position fixture. Landing, walking,
both cave entries and returns, and reembarking use controller inputs only.
Artwork is checked against the independently copied native Seafoam object;
the full-map source renders remain separate from these emulator captures.
"""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
bootstrap = (ROOT / 'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap, __file__, 'exec'))
initial_rom_sha256 = hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest()
marker = json.loads((source / '.journey-dewford-coast-safety').read_text())
finishing = marker['caves']
assert finishing['shared_defect_repaired_on_all_nine_surfaces']
assert finishing['atlas_events_warps_and_map_dimensions_unchanged']
sites = [site for site in json.loads((source / '.journey-sanctuaries').read_text())['sites']
         if site['access'] == 'surf']
assert {site['surface'] for site in sites} == {f'JourneyWorldSea{i:02d}' for i in range(9)}
records = {row['map']: row for row in finishing['maps']}
native_mountain = finishing['native_mountain_cells']
assert len(native_mountain) == 81
names = [name for site in sites for name in (site['surface'], site['map'])]
allowed = set()
walk_prefix = 'completed-coastal-cave'
walk_transition_pictures = False
walk_max_ticks = 1200
native('RtcInitLocalTimeOffset', 12, 0)
team([40, 40, 40])
native('ScriptSetMonMoveSlot', 0, 57, 1)
for badge in hoenn_flags + kanto_flags:
    rawflag(badge, True)
exec(compile((ROOT / 'tools/hoenn/native_water_walk.py').read_text(),
             'completed-cave-native-walker', 'exec'))


checks = []
for site in sites:
    surface, chamber = site['surface'], site['map']
    cx, cy = records[surface]['entrance']
    width, height, values = blocks[surface]
    _, yy, xx = min((abs(x - cx) + abs(y - cy), y, x)
                    for y in range(cy + 2, height - 2) for x in range(2, width - 2)
                    if y * width + x in passable[surface]
                    and values[y * width + x] == 0x112B)
    start = (xx, yy)
    assert hashlib.sha256((source / f'data/maps/{surface}/map.json').read_bytes()).hexdigest() == records[surface]['map_events_sha256']
    entry = next(warp for warp in maps[surface]['warp_events']
                 if (warp['x'], warp['y']) == (cx, cy))
    assert entry['dest_map'] == maps[chamber]['id']
    warp(surface, *start)
    native('SetPlayerAvatarTransitionFlags', 8)
    step(90)
    assert lib.read8(s['gPlayerAvatar']) & 8
    for dx, dy, expected in native_mountain:
        x, y = cx + dx, cy + dy
        assert values[y * width + x] == expected
        assert native('MapGridGetMetatileIdAt', x + 7, y + 7) == expected & 1023
        assert native('MapGridGetElevationAt', x + 7, y + 7) == expected >> 12
        assert native('MapGridGetCollisionAt', x + 7, y + 7) == (expected >> 10) & 3
    before_walked, before_transitions, before_prompts = walked, len(transitions), len(surf_prompts)
    cycles = []
    for cycle in range(2):
        walk((chamber, 14, 17))
        step(60)
        assert location() == map_id(chamber)
        assert lib.read8(s['gPlayerAvatar']) & 25 == 1
        if cycle == 0:
            picture(site['theme'] + '-complete-mountain-inside')
        walk((surface, cx, cy + 1))
        step(60)
        assert location() == map_id(surface)
        assert lib.read8(s['gPlayerAvatar']) & 25 == 1
        if cycle == 0:
            picture(site['theme'] + '-complete-mountain-front')
        walk((surface, *start))
        step(60)
        assert position() == start
        assert lib.read8(s['gPlayerAvatar']) & 8
        cycles.append(dict(controller_entry_and_return=True, foot_inside=True,
                           native_landing_and_reembarkation=True))
    observed = transitions[before_transitions:]
    assert len(observed) == 4
    assert [(row['source'][0], row['destination'][0]) for row in observed] == [
        (surface, chamber), (chamber, surface), (surface, chamber), (chamber, surface)]
    assert len(surf_prompts) - before_prompts == 2
    checks.append(dict(
        surface=surface, chamber=chamber, sanctuary=site['theme'],
        entrance=[cx, cy], surface_start=list(start), complete_native_mountain_loaded=True,
        native_mountain_cells_checked=81, controller_door_roundtrip=True,
        native_surf_landing_and_reembarkation=True, foot_state_inside=True,
        cycles=cycles, native_controller_transitions=observed,
        native_surf_prompts=surf_prompts[before_prompts:],
        walked_tiles=walked - before_walked))
    print('Complete native mountain and two cave roundtrips passed:', surface, flush=True)

assert len(checks) == 9
lib.stop()
assert hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest() == initial_rom_sha256
result = dict(
    passed=True, rom_sha256=initial_rom_sha256, caves=checks,
    all_nine_native_mountains_complete=True,
    all_nine_controller_entries_and_returns=True,
    all_nine_native_surf_landings_and_reembarkations=True,
    two_roundtrips_per_cave=True,
    atlas_events_and_warps_unchanged=True,
    no_internal_warps_or_coordinate_writes=True,
    initial_positions_and_party_are_fixtures=True,
    initial_badges_are_fixtures=True,
    full_campaign_playthrough=False)
(args.output / 'coastal-cave-finishing.json').write_text(json.dumps(result, indent=2) + '\n')
