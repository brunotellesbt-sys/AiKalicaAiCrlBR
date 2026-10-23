"""Audit layer-163 Six cliff closures and exercise their actual compiled ROM.

Without --library (or with --preflight), write a source-only, non-passing
preflight. Native runs use an initial loaded-map fixture and one town trip;
doors, collisions, new coastal Surf routes and reboarding use controller input.
The layer-162 validator and its historical reports are left unchanged.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import struct
import sys

from coastal_six_cliffs import render_review
from render_sea_maps import MapRenderer


ROOT = Path(__file__).resolve().parents[2]
TOWN = 'SixIsland_Frlg'
WATER_PATH = 'SixIsland_WaterPath_Frlg'
KIND = 'six-coastal-closures'
PARENT_ROM_SHA256 = '08fc8a08b95e8e3a923e3342b4f1a31bbaccd1582cbc67ea010021191c43fd6e'
PARENT_TOWN_SHA256 = '8d9329126be5e9dd2437a6898a4b41583173505809f1a7cd754c2c70e46a5b44'

# The independently reviewed allowlist is deliberately local to these two
# blockdata files. The unchanged southwest water cell (1,23) is checked below,
# not counted as a source change. Exactly 65 + 12 cells must differ from 162.
TOWN_CHANGES = {
    (0, 2): 0x1273, (1, 2): 0x067A, (2, 2): 0x3132,
    (8, 2): 0x3134, (9, 2): 0x067C, (10, 2): 0x1273,
    **{(0, y): 0x1270 if y == 3 else 0x1274 for y in range(3, 22)},
    **{(1, y): 0x0473 for y in range(3, 22)},
    (0, 22): 0x1274, (1, 22): 0x047B, (0, 23): 0x1278,
    (16, 28): 0x047B, **{(x, 28): 0x047C for x in range(17, 24)},
    (14, 29): 0x1276, (15, 29): 0x1278,
    **{(x, 29): 0x126B for x in range(16, 23)}, (23, 29): 0x1269,
}
WATER_PATH_CHANGES = {(0, 68): 0x04B3, **{(0, y): 0x0473 for y in range(69, 80)}}
assert len(TOWN_CHANGES) == 65 and len(WATER_PATH_CHANGES) == 12
SOLID_TOWN_CELLS = ([(1, y) for y in range(3, 23)] + [(1, 2), (9, 2), (2, 22)]
                    + [(9, y) for y in (3, 4, 5)] + [(x, 28) for x in range(16, 24)])
WET_TOWN_CELLS = ([(0, y) for y in range(2, 24)] + [(10, y) for y in range(2, 6)]
                  + [(x, 29) for x in range(15, 24)])


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inspect_source(source, baseline):
    source, baseline = Path(source), Path(baseline)
    assert source.resolve() != baseline.resolve(), 'Use a distinct layer-163 candidate'
    assert sha(baseline / 'pokeemerald.gba') == PARENT_ROM_SHA256, 'Not the immutable layer-162 baseline'
    renderer, original = MapRenderer(source), MapRenderer(baseline)
    records, data = [], {}
    for name, allow, expected_dimensions in [(TOWN, TOWN_CHANGES, (24, 30)),
                                              (WATER_PATH, WATER_PATH_CHANGES, (24, 100))]:
        mapping_path = f'data/maps/{name}/map.json'
        assert (source / mapping_path).read_bytes() == (baseline / mapping_path).read_bytes(), name
        mapping = json.loads((source / mapping_path).read_text())
        layout = renderer.layouts[mapping['layout']]
        assert layout == original.layouts[mapping['layout']], ('Changed dimensions, connection bank or layout', name)
        assert (layout['width'], layout['height']) == expected_dimensions
        assert (source / layout['border_filepath']).read_bytes() == (baseline / layout['border_filepath']).read_bytes()
        path = layout['blockdata_filepath']
        raw, before = (source / path).read_bytes(), (baseline / path).read_bytes()
        if name == TOWN:
            assert hashlib.sha256(before).hexdigest() == PARENT_TOWN_SHA256
        width, height = expected_dimensions
        values, old = struct.unpack('<' + 'H' * (width * height), raw), struct.unpack('<' + 'H' * (width * height), before)
        changes = {(i % width, i // width): value for i, (prior, value) in enumerate(zip(old, values)) if prior != value}
        assert changes == allow, ('Outside literal 65+12-cell scope or incomplete native coast', name, changes, allow)
        data[name] = (mapping, layout, values, old)
        records.append(dict(map=name, path=path, dimensions=[width, height],
                            before_sha256=hashlib.sha256(before).hexdigest(),
                            after_sha256=hashlib.sha256(raw).hexdigest(),
                            changed_cells=[dict(position=list(point), before=old[point[1] * width + point[0]], after=value)
                                           for point, value in sorted(changes.items())]))
    mapping, layout, values, old = data[TOWN]

    def at(x, y):
        assert 0 <= x < 24 and 0 <= y < 30
        return values[y * 24 + x]

    objects, owned = [], set()
    for y in range(30):
        for x in range(24):
            if at(x, y) & 1023 != 0xE:
                continue
            cells = [[at(x + dx, y + dy) for dx in range(2)] for dy in range(3)]
            assert cells[0] == [0x300E, 0x300F] and cells[1] == [0x041E, 0x041F]
            assert cells[2][0] in (0x0424, 0x0426) and cells[2][1] in (0x0425, 0x0427)
            footprint = {(x + dx, y + dy) for dx in range(2) for dy in range(3)}
            assert not owned & footprint
            owned |= footprint
            objects.append(dict(bounds=[x, y, 2, 3], native_rows=cells, crown_middle_and_base_complete=True))
    parts = {0xE, 0xF, 0x1E, 0x1F, 0x24, 0x25, 0x26, 0x27}
    assert owned == {(x, y) for y in range(30) for x in range(24) if at(x, y) & 1023 in parts}
    assert len(objects) == 12 and all(obj['bounds'][0] != 0 for obj in objects)
    assert at(1, 23) == 0x126B and at(2, 22) == 0x047A
    assert all(at(8, y) == 0x3001 and at(9, y) == 0x0475 and at(10, y) == 0x1271 for y in (3, 4, 5))
    assert all(at(*point) & 0xC00 == 0x400 for point in SOLID_TOWN_CELLS)
    assert all(at(*point) >> 12 == 1 and not at(*point) & 0xC00 for point in WET_TOWN_CELLS)
    preserved = []
    for name, x, y, w, h in [('PokemonCenter', 9, 7, 5, 5), ('Gym', 2, 13, 6, 5),
                             ('Mart', 18, 8, 4, 4), ('House', 15, 14, 5, 4),
                             ('IntegratedTerminal', 3, 23, 7, 6)]:
        assert all(at(xx, yy) == old[yy * 24 + xx] for yy in range(y, y + h) for xx in range(x, x + w))
        preserved.append(dict(building=name, bounds=[x, y, w, h], complete_native_footprint_unchanged=True))
    # Each remaining tree is the same entire object as in 162, with no shifted
    # collision fragments. The six removed footprints are replaced in full.
    assert all(at(x, y) == old[y * 24 + x] for x, y in owned)
    return dict(kind=KIND, source_tree_objects_complete=True, complete_tree_count=12, objects=objects,
                exact_source_cell_counts=[65, 12], maps=records, preserved_buildings=preserved,
                west_shore_and_port_mountain_bodies_complete=True,
                north_dry_corridor_preserved=[[8, y] for y in (3, 4, 5)],
                source_solid_cliff_cells=[list(point) for point in SOLID_TOWN_CELLS],
                source_adjacent_surf_height_one_cells=[list(point) for point in WET_TOWN_CELLS],
                baseline_rom_sha256=PARENT_ROM_SHA256,
                buildings_events_paths_connections_dimensions_and_borders_preserved=True,
                source_map_renders_not_emulator_captures=True)


def run_native(options, report):
    global source, args, s, lib, layouts, names, allowed, walk_prefix
    global walk_transition_pictures, walk_cache_paths, walk_max_ticks, walk_surf_under_bridges
    global picture, passable, _planned_goal, _planned_keys, native_picture
    sys.argv = [sys.argv[0], '--source', str(options.source), '--library', str(options.library),
                '--output', str(options.output)]
    bootstrap = (ROOT / 'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
    exec(compile(bootstrap, __file__, 'exec'), globals())
    initial_sha = sha(source / 'pokeemerald.gba')
    native('RtcInitLocalTimeOffset', 12, 0)
    native('VarSet', 0x40FE, 7)
    native('VarSet', 0x40FF, 4095)
    native('VarSet', 0x4021, 65535)
    native('VarSet', 0x4120, 65535)
    team([40, 40, 40])
    native('ScriptSetMonMoveSlot', 0, 57, 1)
    for value in hoenn_flags + kanto_flags:
        rawflag(value, True)
    for trainer_id in range(1, 1589):
        rawflag(0x500 + trainer_id, True)
    all_maps = {p.parent.name: json.loads(p.read_text()) for p in (source / 'data/maps').glob('*/map.json')}
    all_by_id = {row['id']: name for name, row in all_maps.items()}
    names = list(dict.fromkeys([TOWN, WATER_PATH] + [all_by_id[warp['dest_map']] for warp in all_maps[TOWN]['warp_events']]))
    allowed, walk_prefix = set(), 'six-coastal'
    walk_transition_pictures, walk_cache_paths, walk_max_ticks = False, True, 2500
    walk_surf_under_bridges = True
    captures = []
    native_picture = picture

    def record_picture(label):
        native_picture(label)
        filename = label + '.png'
        captures.append(dict(file=filename, sha256=sha(args.output / filename)))

    picture = record_picture
    # Reuse the hardware OBJ/scanout comparator, not previous RAM or captures.
    # It reads this emulator's current player frame, OAM, VRAM and palettes.
    visibility = (ROOT / 'tools/hoenn/validate_integrated_piers.py').read_text()
    visibility = visibility[visibility.index('def player_state():'):visibility.index('def set_passability(')]
    exec(compile(visibility, 'current-native-avatar-pixels', 'exec'), globals())

    # One initial loaded-map observation fixture, followed by one complete
    # town trip. No coordinate or elevation writes occur during either trip.
    warp(WATER_PATH, 9, 65)
    native('SetPlayerAvatarTransitionFlags', 1)
    step(120)
    bw = lib.read32(s['gBackupMapLayout'])
    buffer = lib.read32(s['gBackupMapLayout'] + 8)
    water_path_loaded = []
    for (x, y), value in WATER_PATH_CHANGES.items():
        loaded = lib.read16(buffer + 2 * ((y + 7) * bw + x + 7))
        assert loaded == value and native('MapGridGetCollisionAt', x + 7, y + 7) != 0
        water_path_loaded.append(dict(position=[x, y], value=loaded, native_solid=True))
    picture('six-coastal-waterpath-connected-face')
    warp(TOWN, 11, 22)
    native('SetPlayerAvatarTransitionFlags', 1)
    step(120)
    # Cache MB_FAST_WATER while a native whitelisted Sevii coast is loaded.
    exec(compile((ROOT / 'tools/hoenn/native_water_walk.py').read_text(), 'six-coastal-native-walker', 'exec'), globals())
    full_passable = {name: valid.copy() for name, valid in passable.items()}

    def mode(dry):
        global passable, _planned_goal, _planned_keys
        passable = {name: {i for i in valid if not water_behaviors[behaviors[name][i]]} if dry else valid.copy()
                    for name, valid in full_passable.items()}
        _planned_goal, _planned_keys = None, {}

    bw = lib.read32(s['gBackupMapLayout'])
    buffer = lib.read32(s['gBackupMapLayout'] + 8)
    loaded_town = [lib.read16(buffer + 2 * ((y + 7) * bw + x + 7)) for y in range(30) for x in range(24)]
    assert loaded_town == list(blocks[TOWN][2]), 'Loaded town differs from source'
    solid, wet, corridor = [], [], []
    for x, y in SOLID_TOWN_CELLS:
        assert native('MapGridGetCollisionAt', x + 7, y + 7) != 0
        solid.append(dict(position=[x, y], loaded=loaded_town[y * 24 + x], native_solid=True))
    for x, y in WET_TOWN_CELLS:
        behavior = native('MapGridGetMetatileBehaviorAt', x + 7, y + 7)
        assert native('MapGridGetElevationAt', x + 7, y + 7) == 1
        assert native('MapGridGetCollisionAt', x + 7, y + 7) == 0
        assert native('MetatileBehavior_IsSurfableWaterOrUnderwater', behavior)
        wet.append(dict(position=[x, y], loaded=loaded_town[y * 24 + x], elevation=1, behavior=behavior, native_surf_water=True))
    for y in (3, 4, 5):
        assert native('MapGridGetCollisionAt', 15, y + 7) == 0
        assert native('MapGridGetElevationAt', 15, y + 7) == 3
        corridor.append([8, y])
    mode(True)
    routes, doors, collisions = [], [], []

    def foot_at(goal):
        assert (by_location[location()], *position()) == goal
        assert not lib.read8(s['gPlayerAvatar']) & 8 and native('PlayerGetElevation') == 3

    for x, y, label in [(8, 19, 'gym-south-cliff'), (8, 12, 'center-gym-gap'),
                         (8, 3, 'north-corridor-and-retreated-corner'), (8, 8, 'western-tree-row'),
                         (8, 16, 'western-lower-tree-row'), (3, 21, 'southwest-finished-corner'),
                         (11, 22, 'harbor-ramp-return')]:
        start = list(position())
        walk((TOWN, x, y))
        step(60)
        foot_at((TOWN, x, y))
        picture('six-coastal-' + label)
        routes.append(dict(start=start, destination=[x, y], dry=True, controller_input=True))
    for index in [1, 4, 2, 3, 0]:
        exterior = all_maps[TOWN]['warp_events'][index]
        x, y = exterior['x'], exterior['y']
        dest = all_by_id[exterior['dest_map']]
        inside = all_maps[dest]['warp_events'][int(exterior['dest_warp_id'])]
        walk((TOWN, x, y + 1))
        walk((dest, inside['x'], inside['y'] - 1))
        step(80)
        assert location() == map_id(dest)
        picture('six-coastal-door-' + dest)
        walk((TOWN, x, y + 1))
        step(80)
        foot_at((TOWN, x, y + 1))
        picture('six-coastal-returned-' + dest)
        doors.append(dict(destination=dest, warp_id=index, entered=True, exited=True,
                          dry_return=True, controller_input=True))
    assert len(transitions) == 10, ('Expected five physical door roundtrips', transitions)
    probes = [((8, 4), 32, (7, 4)), ((8, 7), 32, (7, 7)), ((6, 10), 32, (5, 10)),
              ((2, 12), 32, (1, 12)), ((2, 19), 32, (1, 19)),
              ((8, 4), 16, (9, 4)), ((8, 2), 16, (9, 2)),
              ((3, 21), 32, (2, 21)), ((4, 21), 64, (4, 20))]
    for start, key, target in probes:
        walk((TOWN, *start))
        step(60)
        assert native('MapGridGetCollisionAt', target[0] + 7, target[1] + 7) != 0
        step(90, key)
        step(60)
        foot_at((TOWN, *start))
        collisions.append(dict(start=list(start), target=list(target), key=key, blocked=True,
                               native_collision=True, controller_input=True))
    picture('six-coastal-trees-and-shore-block-walking')

    # The original layer-162 port door/wooden apron remains at the same place.
    # Walk both boardwalk edges, answer real Surf prompts, navigate the new
    # west shore and south face, then reboard without a height/state repair.
    integration = json.loads((source / '.journey-sevii-integrated-piers').read_text())
    port = next(row for row in integration['harbors']['ports'] if row['island'] == 'Six')
    assert port['door'] == [TOWN, 6, 28] and port['outside_arrival'] == [TOWN, 6, 29]
    surf_checks = []
    for label, dry, water, key, coast_goal in [
            ('west', (TOWN, 3, 29), (TOWN, 2, 29), 32, (TOWN, 0, 18)),
            ('east', (TOWN, 12, 29), (TOWN, 13, 29), 16, (TOWN, 18, 29))]:
        mode(True)
        walk(dry)
        step(60)
        departure = assert_foot('six-coastal-' + label + '-pier-departure-avatar')
        before = (location(), position())
        step(90, key)
        step(45)
        assert (location(), position()) == before, ('Foot walked onto ocean', label)
        assert_foot()
        assert native('IsPlayerFacingSurfableFishableWater')
        prompt_count = len(surf_prompts)
        mode(False)
        walk(water)
        assert_surf()
        assert len(surf_prompts) > prompt_count, ('No native Surf prompt', label)
        walk(coast_goal)
        step(60)
        coast = assert_surf()
        picture('six-coastal-' + label + '-whole-cliff-from-surf')
        if label == 'east':
            before = (location(), position())
            assert native('MapGridGetCollisionAt', 18 + 7, 28 + 7) != 0
            step(90, 64)
            step(60)
            assert (location(), position()) == before, 'Surf crossed the solid south mountain face'
            assert_surf()
        walk(water)
        walk(dry)
        step(60)
        returned = assert_foot('six-coastal-' + label + '-same-pier-reboarded-avatar')
        surf_checks.append(dict(side=label, dry=list(dry), water=list(water), coast_goal=list(coast_goal),
                                departure=departure, coast=coast, reboarded=returned,
                                foot_blocked_from_ocean=True, native_surf_prompt=True,
                                controller_coastal_route=True, returned_to_same_pier=True,
                                head_body_feet_native_pixels_verified=True,
                                no_coordinate_avatar_or_elevation_writes=True))
    mode(True)
    walk((TOWN, 11, 22))
    foot_at((TOWN, 11, 22))
    picture('six-coastal-final-dry-town-return')
    assert len(transitions) == 10
    review_mode = bool(lib.read8(s['gJourneyReviewMode']))
    lib.stop()
    assert sha(source / 'pokeemerald.gba') == initial_sha, 'ROM changed during validation'
    result = dict(report, passed=True, preflight=False, native_validation_performed=True,
                  rom_sha256=initial_sha, review_mode=review_mode,
                  loaded_town_cell_count=720, loaded_town_blocks_match_source=True,
                  loaded_water_path_changed_cells=water_path_loaded,
                  loaded_solid_cliff_cells=solid, loaded_adjacent_surf_height_one_cells=wet,
                  loaded_dry_corridor=corridor, dry_controller_routes=routes, doors_tested=doors,
                  collision_checks=collisions, surf_roundtrips=surf_checks, captures=captures,
                  native_map_transitions=transitions, controller_tiles_walked=walked,
                  water_path_loaded_observation_and_initial_town_position_are_fixtures=True,
                  party_progress_and_trainer_flags_are_fixtures=True,
                  player_movement_uses_controller_input=True,
                  no_position_or_elevation_writes_after_initial_town_placement=True,
                  full_campaign_playthrough=False)
    (options.output / (KIND + '.json')).write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--library', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--preflight', action='store_true')
    options = parser.parse_args()
    options.output.mkdir(parents=True, exist_ok=True)
    report = inspect_source(options.source, options.baseline)
    report['source_review_images'] = render_review(options.source, options.output / 'source-review', report)
    for record in report['source_review_images']:
        record['file'] = 'source-review/' + record['file']
    if options.library and not options.preflight:
        result = run_native(options, report)
    else:
        result = dict(report, passed=False, preflight=True, native_validation_performed=False)
        (options.output / (KIND + '-preflight.json')).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ['kind', 'passed', 'preflight', 'complete_tree_count', 'exact_source_cell_counts']}))


if __name__ == '__main__':
    main()
