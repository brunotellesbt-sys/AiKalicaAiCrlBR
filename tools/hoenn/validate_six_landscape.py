"""Audit whole Six trees/cliffs, then exercise its dry paths and doors in mGBA.

Without --library this writes a source-only preflight, never a passed native
report. Native tests use one initial travel/progress fixture; subsequent town
routes, building entrances/returns and collision attempts use controller input.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from PIL import Image, ImageDraw
from render_sea_maps import MapRenderer


ROOT = Path(__file__).resolve().parents[2]
TOWN = 'SixIsland_Frlg'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inspect_source(source, baseline=None):
    source = Path(source)
    renderer = MapRenderer(source)
    mapping = json.loads((source / f'data/maps/{TOWN}/map.json').read_text())
    layout = renderer.layouts[mapping['layout']]
    assert (layout['width'], layout['height'], layout['layout_version']) == (24, 30, 'frlg')
    raw = (source / layout['blockdata_filepath']).read_bytes()
    values = struct.unpack('<720H', raw)

    def at(x, y):
        assert 0 <= x < 24 and 0 <= y < 30, (x, y)
        return values[y * 24 + x]

    objects, owned = [], set()
    for y in range(30):
        for x in range(24):
            if at(x, y) & 1023 != 0xE:
                continue
            cells = [[at(x + dx, y + dy) for dx in range(2)] for dy in range(3)]
            assert cells[0] == [0x300E, 0x300F], (x, y, cells)
            assert cells[1] == [0x041E, 0x041F], (x, y, cells)
            assert cells[2][0] in (0x0424, 0x0426) and cells[2][1] in (0x0425, 0x0427), (x, y, cells)
            footprint = {(x + dx, y + dy) for dy in range(3) for dx in range(2)}
            assert not owned & footprint
            owned.update(footprint)
            objects.append(dict(bounds=[x, y, 2, 3], native_rows=cells,
                                crown_middle_and_base_complete=True))
    tree_ids = {0xE, 0xF, 0x1E, 0x1F, 0x24, 0x25, 0x26, 0x27}
    unused_forest_parts = {0xA, 0xB, 0xC, 0xD, 0x12, 0x13, 0x14, 0x15, 0x16,
                           0x17, 0x1A, 0x1B, 0x1C, 0x1D, 0x20, 0x21, 0x22, 0x23}
    assert not any(value & 1023 in unused_forest_parts for value in values), 'Unexpected old dense-forest fragments'
    all_tree_cells = {(x, y) for y in range(30) for x in range(24) if at(x, y) & 1023 in tree_ids}
    assert owned == all_tree_cells, ('Orphan or missing native tree part', sorted(all_tree_cells ^ owned))
    assert len(objects) == 18, len(objects)
    assert all([4, 21, 2, 3] != obj['bounds'] and [6, 21, 2, 3] != obj['bounds'] for obj in objects)
    assert at(9, 12) == 0x3001
    northwest = {**{(x, 2): 0x3133 for x in range(9)}, (9, 2): 0x3134, (10, 2): 0x067C,
                 **{(9, y): 0x0475 for y in (3, 4, 5)}, **{(10, y): 0x1271 for y in (3, 4, 5)}}
    southwest = {(2, 20): 0x04B2, (2, 21): 0x0472, (2, 22): 0x047A,
                 **{(x, 20): 0x0479 for x in range(3, 8)}}
    for point, value in (northwest | southwest).items():
        assert at(*point) == value, ('Incomplete native cliff', point, hex(at(*point)), hex(value))
    assert all(at(x, y) == 0x3001 for y in (21, 22) for x in range(3, 8))
    preserved = []
    if baseline:
        baseline = Path(baseline)
        original = json.loads((baseline / f'data/maps/{TOWN}/map.json').read_text())
        assert mapping == (original | {'warp_events': mapping['warp_events']}), 'Town events or connections changed'
        assert mapping['warp_events'][1:] == original['warp_events'][1:]
        old_layouts = json.loads((baseline / 'data/layouts/layouts.json').read_text())['layouts']
        old_layout = next(row for row in old_layouts if row['id'] == mapping['layout'])
        assert layout['primary_tileset'] in (old_layout['primary_tileset'], 'gTileset_JourneySeviiSea')
        assert layout == (old_layout | {'primary_tileset': layout['primary_tileset'],
                                       'secondary_tileset': layout['secondary_tileset']})
        assert (source / layout['border_filepath']).read_bytes() == (baseline / old_layout['border_filepath']).read_bytes()
        old = struct.unpack('<720H', (baseline / old_layout['blockdata_filepath']).read_bytes())
        for name, x, y, w, h in [('PokemonCenter', 9, 7, 5, 5), ('Gym', 2, 13, 6, 5),
                                 ('Mart', 18, 8, 4, 4), ('House', 15, 14, 5, 4)]:
            assert all(at(xx, yy) == old[yy * 24 + xx] for yy in range(y, y + h) for xx in range(x, x + w)), name
            preserved.append(dict(building=name, bounds=[x, y, w, h], complete_native_footprint_unchanged=True))
    return dict(source_tree_objects_complete=True, complete_tree_count=len(objects), objects=objects,
                cliff_outline_complete=True,
                cliff_cells=[dict(position=list(p), value=v) for p, v in (northwest | southwest).items()],
                blockdata_sha256=hashlib.sha256(raw).hexdigest(),
                dimensions=[24, 30], preserved_buildings=preserved,
                source_map_renders_not_emulator_captures=True)


def render_review(source, output, metadata=None):
    """Whole town plus actual west/east connected-map edges in native palettes."""
    source, output = Path(source), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    renderer = MapRenderer(source)
    mapping = json.loads((source / f'data/maps/{TOWN}/map.json').read_text())
    layout = renderer.layouts[mapping['layout']]
    raw = (source / layout['blockdata_filepath']).read_bytes()
    after = list(struct.unpack('<720H', raw))
    before = after.copy()
    if metadata:
        assert hashlib.sha256(raw).hexdigest() == metadata['after_sha256']
        for change in metadata['changed_cells']:
            x, y = change['position']
            assert before[y * 24 + x] == change['after']
            before[y * 24 + x] = change['before']
    border_raw = (source / layout['border_filepath']).read_bytes()
    border = struct.unpack('<' + 'H' * (len(border_raw) // 2), border_raw)
    neighbors = [('SixIsland_WaterPath_Frlg', 24, -40), ('JourneySurfLink05200', -16, 17)]
    panels, records = [], []
    for state, values in [('before', before), ('after', after)]:
        town, _ = renderer.render(TOWN, values=values)
        town.save(output / f'Six-{state}.png')
        # Seven tiles around the complete town match the native map backup;
        # neighboring maps are rendered with their OWN graphics and palettes.
        width, height = 39, 44
        outside = [border[((x - 7) % layout['border_width']) + layout['border_width'] * ((y - 7) % layout['border_height'])]
                   for y in range(height) for x in range(width)]
        canvas, _ = renderer.render(TOWN, values=outside, dimensions=(width, height), npcs=False)
        for name, ox, oy in neighbors:
            neighbor, _ = renderer.render(name)
            canvas.paste(neighbor, ((ox + 7) * 16, (oy + 7) * 16))
        canvas.paste(town, (7 * 16, 7 * 16))
        label = Image.new('RGB', (canvas.width, canvas.height + 24), '#17232b')
        label.paste(canvas, (0, 24))
        ImageDraw.Draw(label).text((4, 5), f'Six {state}: native source render, whole map and connected edges', fill='white')
        path = output / f'Six-{state}-whole-with-neighbors.png'
        label.save(path)
        records.append(dict(state=state, file=path.name, sha256=sha(path)))
        panels.append(label)
    comparison = Image.new('RGB', (panels[0].width * 2 + 16, panels[0].height), '#17232b')
    comparison.paste(panels[0], (0, 0))
    comparison.paste(panels[1], (panels[0].width + 16, 0))
    comparison.save(output / 'Six-comparison-whole-with-neighbors.png')
    return records


def run_native(options, source_report):
    # The shared harness creates an isolated emulator flash file. It does not
    # write source, ELF, ROM or the distributed save.
    global source, args, s, lib, layouts, names, allowed, walk_prefix
    global walk_transition_pictures, walk_cache_paths, walk_max_ticks
    sys.argv = [sys.argv[0], '--source', str(options.source), '--library', str(options.library),
                '--output', str(options.output)]
    bootstrap = (ROOT / 'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
    exec(compile(bootstrap, __file__, 'exec'), globals())
    initial_sha = sha(source / 'pokeemerald.gba')
    native('RtcInitLocalTimeOffset', 12, 0)
    native('VarSet', 0x40FE, 7)
    native('VarSet', 0x40FF, 4095)
    for flag_value in hoenn_flags + kanto_flags:
        rawflag(flag_value, True)
    # Suppress optional trainer approaches while entering the gym's foyer.
    gym_metadata = json.loads((source / '.journey-extra-gyms').read_text())['gyms']
    gym_students = next(row['students'] for row in gym_metadata if row['name'] == 'JourneySixIslandGym')
    for trainer_id in gym_students:
        rawflag(0x500 + trainer_id, True)
    all_maps = {p.parent.name: json.loads(p.read_text()) for p in (source / 'data/maps').glob('*/map.json')}
    all_by_id = {row['id']: name for name, row in all_maps.items()}
    names = [TOWN] + [all_by_id[warp['dest_map']] for warp in all_maps[TOWN]['warp_events']]
    names = list(dict.fromkeys(names))
    allowed, walk_prefix = set(), 'six-landscape'
    walk_transition_pictures, walk_cache_paths, walk_max_ticks = False, True, 2000
    exec(compile((ROOT / 'tools/hoenn/native_water_walk.py').read_text(), 'six-native-walker', 'exec'), globals())
    for name, valid in passable.items():
        passable[name] = {i for i in valid if not water_behaviors[behaviors[name][i]]}
    warp(TOWN, 11, 22)
    native('SetPlayerAvatarTransitionFlags', 1)
    step(120)
    # Observe every loaded cell, including collisions/heights, directly in
    # the native backup buffer after map scripts and connection loading.
    buffer_width = lib.read32(s['gBackupMapLayout'])
    buffer = lib.read32(s['gBackupMapLayout'] + 8)
    loaded = [lib.read16(buffer + 2 * ((y + 7) * buffer_width + x + 7))
              for y in range(30) for x in range(24)]
    assert loaded == list(blocks[TOWN][2]), 'Loaded Six blockdata differs from source'
    captures, routes, door_checks, collisions = [], [], [], []

    def capture(label):
        filename = 'six-' + label
        picture(filename)
        captures.append(dict(file=filename + '.png', sha256=sha(args.output / (filename + '.png'))))

    def dry_route(x, y, label):
        start = [*position()]
        walk((TOWN, x, y))
        step(60)
        assert location() == map_id(TOWN) and position() == (x, y)
        assert not lib.read8(s['gPlayerAvatar']) & 8
        assert native('PlayerGetElevation') == 3
        capture(label)
        routes.append(dict(start=start, destination=[x, y], complete=True, dry=True,
                           controller_input=True))

    dry_route(8, 19, 'gym-south-and-whole-cliff')
    dry_route(8, 12, 'center-gym-gap')
    dry_route(8, 3, 'northwest-whole-tree-crowns')
    dry_route(8, 8, 'western-middle-tree-row')
    dry_route(8, 16, 'western-lower-tree-row')
    dry_route(3, 21, 'southwest-finished-corner')
    dry_route(11, 22, 'harbor-ramp-return')
    # These are physical, round-trip door transitions from the same trip.
    for index in [1, 4, 2, 3, 0]:
        exterior_warp = all_maps[TOWN]['warp_events'][index]
        x, y = exterior_warp['x'], exterior_warp['y']
        dest = all_by_id[exterior_warp['dest_map']]
        inside_warp = all_maps[dest]['warp_events'][int(exterior_warp['dest_warp_id'])]
        walk((TOWN, x, y + 1))
        walk((dest, inside_warp['x'], inside_warp['y'] - 1))
        step(80)
        assert location() == map_id(dest)
        capture('door-' + dest)
        walk((TOWN, x, y + 1))
        step(80)
        assert location() == map_id(TOWN) and position() == (x, y + 1)
        assert not lib.read8(s['gPlayerAvatar']) & 8
        assert native('PlayerGetElevation') == 3
        capture('returned-' + dest)
        door_checks.append(dict(destination=dest, warp_id=index, entered=True, exited=True,
                                controller_input=True, dry_return=True))
    for start, key, target in [((8, 4), 32, (7, 4)), ((8, 7), 32, (7, 7)),
                               ((6, 10), 32, (5, 10)), ((2, 18), 32, (1, 18)),
                               ((8, 4), 16, (9, 4)), ((3, 21), 32, (2, 21)),
                               ((4, 21), 64, (4, 20))]:
        walk((TOWN, *start))
        step(60)
        assert native('MapGridGetCollisionAt', target[0] + 7, target[1] + 7) != 0
        step(90, key)
        step(60)
        assert location() == map_id(TOWN) and position() == start, (start, target, position())
        collisions.append(dict(start=list(start), target=list(target), key=key,
                               blocked=True, native_collision=True, controller_input=True))
    capture('trees-and-cliff-block-walking')
    assert len(transitions) == 10, ('Expected five native door roundtrips', transitions)
    review_mode = bool(lib.read8(s['gJourneyReviewMode']))
    lib.stop()
    assert sha(source / 'pokeemerald.gba') == initial_sha
    result = dict(source_report, passed=True, preflight=False, rom_sha256=initial_sha,
                  review_mode=review_mode, loaded_cell_count=len(loaded),
                  loaded_blocks_match_source=True, dry_controller_routes=routes,
                  doors_tested=door_checks, collision_checks=collisions, captures=captures,
                  native_map_transitions=transitions, controller_tiles_walked=walked,
                  initial_travel_and_progress_are_fixtures=True,
                  foyer_trainer_flags_are_fixtures=gym_students,
                  player_movement_uses_controller_input=True,
                  no_position_or_elevation_writes_after_initial_placement=True,
                  surf_roundtrip_validated_here=False,
                  surf_roundtrip_validator='validate_integrated_piers.py')
    (options.output / 'six-landscape.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--library', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    options.output.mkdir(parents=True, exist_ok=True)
    report = inspect_source(options.source, options.baseline)
    marker = options.source / '.journey-sevii-integrated-piers'
    metadata = json.loads(marker.read_text()).get('six_landscape') if marker.exists() else None
    report['source_review_images'] = render_review(options.source, options.output / 'source-review', metadata)
    for record in report['source_review_images']:
        record['file'] = 'source-review/' + record['file']
    if options.library:
        result = run_native(options, report)
    else:
        result = dict(report, passed=False, preflight=True, native_validation_performed=False)
        (options.output / 'six-landscape-preflight.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ['passed', 'preflight', 'complete_tree_count', 'cliff_outline_complete']}))


if __name__ == '__main__':
    main()
