"""Independently replay layer 161 and audit its exact coastal repair scope."""
import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

from prepare_dewford_coast_safety import LAYER, PRIOR, prepare


ROOT = Path(__file__).resolve().parents[2]
PARENT_ROM_SHA256 = 'ae5da9ae24d315cd2a987afc48d42673a4d11b4fa9b411afcf5214d936759a2b'
DEWFORD_CHANGED_FILES = [
    'data/layouts/Route107/map.bin',
    'include/journey_dewford_bridge.h',
    'include/journey_dewford_coast.h',
    'include/journey_dewford_coast_view.h',
    'src/event_object_movement.c',
    'src/fieldmap.c',
]
UPSTREAM_ROUTE107_SHA256 = 'af88a3d526aa59d8f263514364c2ae76f333d3e0dc9222c3b1786f10f025e097'
UPSTREAM_COMMIT = 'e05c82865d38a6638173fd30b2c830d1250aa50d'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit_completed_caves(source, baseline, layouts, metadata):
    """Read the native donor independently of the repairing helper."""
    donor_name = 'Route20_Frlg'
    donor_map = json.loads((baseline/f'data/maps/{donor_name}/map.json').read_text())
    donor_layout = layouts[donor_map['layout']]
    donor_values = struct.unpack('<'+'H'*(donor_layout['width']*donor_layout['height']),
                                 (baseline/donor_layout['blockdata_filepath']).read_bytes())
    donor = []
    for y in range(6, 15):
        for x in range(67, 78):
            value = donor_values[y*donor_layout['width']+x]
            mid = value & 1023
            if 0x68 <= mid <= 0xAF or mid in [0xB2, 0xB3, 0xBA, 0xBB]:
                donor.append([x-72, y-14, value])
    assert len(donor) == 81
    assert metadata['donor_map'] == donor_name
    assert metadata['donor_entrance'] == [72, 14]
    assert metadata['donor_bounds'] == [67, 6, 78, 15]
    assert metadata['native_mountain_cells'] == donor
    assert metadata['shared_defect_repaired_on_all_nine_surfaces']
    assert metadata['atlas_events_warps_and_map_dimensions_unchanged']
    sites = [site for site in json.loads((baseline/'.journey-sanctuaries').read_text())['sites']
             if site['access'] == 'surf']
    names = {f'JourneyWorldSea{i:02d}' for i in range(9)}
    assert {site['surface'] for site in sites} == names
    records = {row['map']: row for row in metadata['maps']}
    assert set(records) == names and len(metadata['maps']) == 9
    paths, checks = set(), []
    for site in sites:
        name = site['surface']
        row = records[name]
        path = f'data/maps/{name}/map.json'
        assert (source/path).read_bytes() == (baseline/path).read_bytes()
        data = json.loads((baseline/path).read_text())
        layout = layouts[data['layout']]
        assert layout['layout_version'] == 'frlg'
        assert layout['primary_tileset'] == 'gTileset_General_Frlg'
        width, height = layout['width'], layout['height']
        cx, cy = site['entry'][0], site['entry'][1]-4
        assert row['entrance'] == [cx, cy]
        assert row['sanctuary'] == site['theme']
        assert row['map_events_sha256'] == digest(baseline/path)
        assert row['native_mountain_restored_exactly']
        assert row['doorway_and_warp_unchanged']
        assert row['coastline_and_all_tiles_outside_object_unchanged']
        path = layout['blockdata_filepath']
        paths.add(path)
        old = struct.unpack('<'+'H'*(width*height), (baseline/path).read_bytes())
        new = struct.unpack('<'+'H'*(width*height), (source/path).read_bytes())
        expected = list(old)
        footprint = set()
        for dx, dy, native in donor:
            x, y = cx+dx, cy+dy
            footprint.add((x, y))
            expected[y*width+x] = native
        assert list(new) == expected, (name, 'Outside-object edit or incomplete mountain')
        actual = [[i % width, i // width, a, b]
                  for i, (a, b) in enumerate(zip(old, new)) if a != b]
        assert actual == row['changed_cells'] and len(actual) == 19
        assert new[cy*width+cx] == old[cy*width+cx] == 0x30A9
        assert row['complete_native_mountain_cells'] == 81
        def connected(values):
            dry = {(i % width, i // width) for i, value in enumerate(values)
                   if value >> 12 == 3 and not value & 0xC00}
            reached = {(cx, cy)}
            pending = [(cx, cy)]
            for x, y in pending:
                for point in ((x-1, y), (x+1, y), (x, y-1), (x, y+1)):
                    if point in dry and point not in reached:
                        reached.add(point)
                        pending.append(point)
            return reached
        useful = connected(old)-footprint
        assert useful <= connected(new), name
        assert len(useful) == row['useful_dry_tiles_still_connected_to_door']
        checks.append(dict(map=name, native_mountain_cells=81, changed_tiles=19,
                           native_donor_exact=True, useful_dry_paths_to_door_preserved=True,
                           events_warps_and_surrounding_terrain_unchanged=True))
    return paths, checks


def audit_wooden_endcaps(source, baseline, layouts, metadata):
    """Only three unused primary definitions gain native wood and warp behavior."""
    meta_path = 'data/tilesets/primary/general_frlg/metatiles.bin'
    attrs_path = 'data/tilesets/primary/general_frlg/metatile_attributes.bin'
    ids, donors, attributes = [0x228, 0x229, 0x22A], [0x1C5, 0x1C6, 0x1C7], [0, 0x65, 0]
    assert metadata['metatiles_path'] == meta_path and metadata['attributes_path'] == attrs_path
    assert metadata['private_metatile_ids'] == ids
    assert metadata['native_wooden_donors'] == donors
    assert metadata['attributes'] == attributes
    assert metadata['previously_blank_and_unreferenced']
    assert metadata['all_other_metatiles_and_attributes_unchanged']
    assert metadata['original_metal_ramps_unchanged']
    before_metas = (baseline/meta_path).read_bytes()
    before_attrs = (baseline/attrs_path).read_bytes()
    expected_metas, expected_attrs = bytearray(before_metas), bytearray(before_attrs)
    assert len(before_metas) == 640 * 16 and len(before_attrs) == 640 * 4
    reviewed = []
    for layout in layouts.values():
        if layout['primary_tileset'] != 'gTileset_General_Frlg':
            continue
        reviewed.append(layout['id'])
        for path in [layout['blockdata_filepath'], layout['border_filepath']]:
            raw = (baseline/path).read_bytes()
            values = struct.unpack('<'+'H'*(len(raw)//2), raw)
            assert not {value & 1023 for value in values} & set(ids), path
    assert reviewed and metadata['reviewed_layouts'] == sorted(reviewed)
    for mid, donor, attr in zip(ids, donors, attributes):
        assert before_metas[mid*16:(mid+1)*16] == bytes(16)
        assert before_attrs[mid*4:(mid+1)*4] == bytes(4)
        expected_metas[mid*16:(mid+1)*16] = before_metas[donor*16:(donor+1)*16]
        struct.pack_into('<I', expected_attrs, mid*4, attr)
    assert (source/meta_path).read_bytes() == expected_metas
    assert (source/attrs_path).read_bytes() == expected_attrs
    # Tile pixels and every palette remain untouched; this swaps definitions,
    # not shared graphics or the original metal ferry ramps.
    folder = baseline/Path(meta_path).parent
    for path in [folder/'tiles.png', *sorted((folder/'palettes').glob('*.pal'))]:
        assert path.read_bytes() == (source/path.relative_to(baseline)).read_bytes()
    return {meta_path, attrs_path}


def audit_coastal_piers(source, baseline, layouts, metadata):
    """Reconstruct the seven authorized decks and their exact ferry changes."""
    towns = {
        'One': 'OneIsland_Frlg', 'Two': 'TwoIsland_Frlg',
        'Three': 'ThreeIsland_Port_Frlg', 'Four': 'FourIsland_Frlg',
        'Five': 'FiveIsland_Frlg', 'Six': 'SixIsland_Frlg',
        'Seven': 'SevenIsland_Frlg'}
    beach, first_harbor = 'OneIsland_TreasureBeach_Frlg', 'OneIsland_Harbor_Frlg'
    allowed_maps = set(towns.values()) | {beach, first_harbor}
    records = {row['island']: row for row in metadata['town_bridges']}
    assert len(metadata['town_bridges']) == 7 and set(records) == set(towns)
    old_ferries = {row['map']: row for row in json.loads(
        (baseline/'.journey-extra-gyms').read_text())['landscape_review']
        if row.get('obsolete_ferry_roof_removed')}
    maps, old_maps, grids, old_grids = {}, {}, {}, {}
    def load(name):
        if name not in maps:
            old_maps[name] = json.loads((baseline/f'data/maps/{name}/map.json').read_text())
            maps[name] = copy.deepcopy(old_maps[name])
            layout = layouts[maps[name]['layout']]
            raw = (baseline/layout['blockdata_filepath']).read_bytes()
            old_grids[name] = list(struct.unpack('<'+'H'*(len(raw)//2), raw))
            grids[name] = old_grids[name].copy()
        return maps[name]
    expected_rectangles = []
    boards = [0x31C5, 0x31C6, 0x31C7]
    wooden_paths = audit_wooden_endcaps(source, baseline, layouts, metadata['wooden_endcaps'])
    wooden_endpoint = [0x3228, 0x3229, 0x322A]
    for island, town in towns.items():
        row = records[island]
        assert row['town'] == town
        harbor = island+'Island_Harbor_Frlg'
        assert row['harbor'] == harbor
        data, back = load(town), load(harbor)
        ferry = old_ferries[town]
        rx, ry = ferry['ramp']
        wid = ferry['ramp_warp_id']
        layout = layouts[data['layout']]
        width = layout['width']
        old_endpoint = old_grids[town][ry*width+rx-1:ry*width+rx+2]
        endpoint = wooden_endpoint
        assert row['old_ramp'] == [rx, ry]
        assert row['start'] == [town, rx, ry-1]
        assert row['width'] == 3 and row['foot_elevation'] == 3
        assert row['native_board_metatiles'] == boards
        assert row['endpoint_metatiles'] == endpoint
        assert row['old_endpoint_metatiles'] == old_endpoint
        assert row['endpoint_attributes'] == [0, 0x65, 0]
        assert row['metal_endpoint_art_removed']
        bank, old_ids = {
            'One': ('sevii_islands_123_frlg', [0x2B4, 0x2B5, 0x2B6]),
            'Two': ('sevii_islands_123_frlg', [0x2B4, 0x2B5, 0x2B6]),
            'Three': ('sevii_islands_123_frlg', [0x2B4, 0x2B5, 0x2B6]),
            'Four': ('sevii_islands_45_frlg', [0x2F8, 0x2F9, 0x2FA]),
            'Five': ('sevii_islands_45_frlg', [0x2F8, 0x2F9, 0x2FA]),
            'Six': ('sevii_islands_67_frlg', [0x2E3, 0x2E4, 0x2E5]),
            'Seven': ('sevii_islands_67_frlg', [0x2E3, 0x2E4, 0x2E5]),
        }[island]
        assert old_endpoint == [0x3000 | mid for mid in old_ids]
        attr_path = f'data/tilesets/secondary/{bank}/metatile_attributes.bin'
        native_attrs = (baseline/attr_path).read_bytes()
        assert [struct.unpack_from('<I', native_attrs, (mid-640)*4)[0]
                for mid in old_ids] == [0, 0x65, 0]
        assert row['warp_before'] == old_maps[town]['warp_events'][wid]
        assert row['return_warp_before'] == old_maps[harbor]['warp_events'][0]
        if island == 'One':
            load(beach)
            assert wid == 3 and len(data['warp_events']) == 4
            assert not maps[beach]['warp_events']
            segments = [(town, rx-1, ry, 3, layout['height']-ry), (beach, rx-1, 0, 3, 4)]
            end_map, ex, ey, endpoint_id = beach, rx, 3, 0
            outward = data['warp_events'].pop()
            outward.update(x=ex, y=ey, elevation=3)
            maps[beach]['warp_events'].append(outward)
            back['warp_events'][0].update(dest_map=maps[beach]['id'], dest_warp_id='0')
            assert row['removed_last_town_warp_id'] == 3 and row['new_beach_warp_id'] == 0
            assert row['beach_before_warps'] == []
            assert row['beach_after_warps'] == maps[beach]['warp_events']
        else:
            ex, ey, end_map, endpoint_id = rx, ferry['roof_footprint'][1]+ferry['roof_footprint'][3]-1, town, wid
            segments = [(town, rx-1, ry, 3, ey-ry+1)]
            data['warp_events'][wid].update(x=ex, y=ey, elevation=3)
        assert row['end'] == [end_map, ex, ey]
        assert row['endpoint_warp_id'] == endpoint_id
        assert row['warp_after'] == maps[end_map]['warp_events'][endpoint_id]
        assert row['return_warp_after'] == back['warp_events'][0]
        assert row['objects_and_surface_connections_preserved'] and row['old_roof_not_reintroduced']
        assert row['deck_segments'] == [dict(map=n, footprint=[x, y, w, h]) for n, x, y, w, h in segments]
        for name, x, y, w, h in segments:
            load(name)
            segment_width = layouts[maps[name]['layout']]['width']
            for yy in range(y, y+h):
                for dx, value in enumerate(endpoint if name == end_map and yy == ey else boards):
                    grids[name][yy*segment_width+x+dx] = value
            expected_rectangles.append(dict(map=name, map_id=maps[name]['id'],
                                            bounds=[x, y, x+w-1, y+h-1], kind='town_bridge'))

    low_piers = {row['map']: row for row in metadata['low_piers']}
    ports = json.loads((baseline/'.journey-sevii-harbors').read_text())['ports']
    assert len(low_piers) == len(ports) == 7
    assert set(low_piers) == {port['exterior'] for port in ports}
    for port in ports:
        name, px = port['exterior'], port['pier_x']
        data = load(name)
        row = low_piers[name]
        assert row['map_id'] == data['id'] and row['pier_x'] == px
        bounds = [[7, 3, 9, 6], [10, 6, 16, 6], [7, 7, 16, 7], [px, 8, px+1, 10]]
        assert row['rectangles'] == bounds
        cells = sorted({(x, y) for x1, y1, x2, y2 in bounds
                        for y in range(y1, y2+1) for x in range(x1, x2+1)})
        assert len(cells) == 35 and row['blocked_cells'] == [list(point) for point in cells]
        assert row['low_wood_only'] and row['original_tiles_and_events_preserved']
        for box in bounds:
            expected_rectangles.append(dict(map=name, map_id=data['id'], bounds=box,
                                            kind='main_harbor_low_pier'))
        assert (source/layouts[data['layout']]['blockdata_filepath']).read_bytes() == (
            baseline/layouts[data['layout']]['blockdata_filepath']).read_bytes()
    assert metadata['collision_rectangles'] == expected_rectangles
    assert metadata['route107_high_bridge_unchanged']
    assert metadata['all_seven_surface_seams_preserved']
    assert metadata['native_pixels_and_palettes_unchanged']
    assert metadata['only_unused_primary_slots_changed']
    assert metadata['low_piers_block_surf_entry'] and metadata['saved_surfer_can_leave_old_underpass']
    assert metadata['connection_destination_resolved_before_crossing']
    assert metadata['npc_and_player_collision_interfaces_match']
    assert metadata['no_player_coordinate_or_elevation_writes']
    edits = {row['map']: row for row in metadata['source_edits']}
    assert len(metadata['source_edits']) == 9 and set(edits) == allowed_maps
    paths = {'include/journey_coastal_piers.h', 'src/event_object_movement.c'} | wooden_paths
    changed_maps = set()
    for name in allowed_maps:
        row = edits[name]
        map_path = f'data/maps/{name}/map.json'
        block_path = layouts[maps[name]['layout']]['blockdata_filepath']
        assert row['map_path'] == map_path and row['block_path'] == block_path
        assert row['map_changed'] and row['blocks_changed'] == (name != first_harbor)
        assert row['warps_before'] == old_maps[name]['warp_events']
        assert row['warps_after'] == maps[name]['warp_events']
        assert json.loads((source/map_path).read_text()) == maps[name], (name, 'Unauthorized map event/connection edit')
        paths.add(map_path)
        changed_maps.add(map_path)
        width = layouts[maps[name]['layout']]['width']
        actual = [dict(map=name, position=[i % width, i // width], before=a, after=b)
                  for i, (a, b) in enumerate(zip(old_grids[name], grids[name])) if a != b]
        assert row['changed_cells'] == actual
        if name != first_harbor:
            paths.add(block_path)
            assert len(actual) > 0
        assert (source/block_path).read_bytes() == struct.pack('<'+'H'*len(grids[name]), *grids[name])
    assert set(metadata['changed_paths']) == paths and len(paths) == 21
    # These new IDs are absent from every other GeneralFRLG map, including
    # borders and shared layouts. Exactly the seven three-tile endpoints use
    # them after the overlay, with no new art leaking into unrelated maps.
    actual_endpoint_cells, expected_endpoint_cells = set(), set()
    for row in records.values():
        name, x, y = row['end']
        expected_endpoint_cells.update((name, x+dx, y, mid)
                                       for dx, mid in zip((-1, 0, 1), (0x228, 0x229, 0x22A)))
    for name, data in ((path.parent.name, json.loads(path.read_text()))
                       for path in (source/'data/maps').glob('*/map.json')):
        layout = layouts[data['layout']]
        if layout['primary_tileset'] != 'gTileset_General_Frlg':
            continue
        blob = (source/layout['blockdata_filepath']).read_bytes()
        values = struct.unpack('<'+'H'*(len(blob)//2), blob)
        actual_endpoint_cells.update((name, i % layout['width'], i // layout['width'], value & 1023)
                                     for i, value in enumerate(values) if value & 1023 in (0x228, 0x229, 0x22A))
    assert actual_endpoint_cells == expected_endpoint_cells and len(actual_endpoint_cells) == 21
    assert metadata['collision_header'] == 'include/journey_coastal_piers.h'
    header = (source/metadata['collision_header']).read_text()
    header_rects = re.findall(r'\{MAP_GROUP\((\w+)\), MAP_NUM\((\w+)\), (-?\d+), (-?\d+), (-?\d+), (-?\d+)\}', header)
    assert [(a, b, list(map(int, coords))) for a, b, *coords in header_rects] == [
        (row['map_id'], row['map_id'], row['bounds']) for row in expected_rectangles]
    assert not re.search(r'->(?:currentCoords|previousCoords|currentElevation|previousElevation)\s*=(?!=)', header)
    assert 'case CONNECTION_EAST:' in header and 'case CONNECTION_NORTH:' in header
    return paths, changed_maps


def compiled_values(tree, symbols, includes, generated_headers):
    code = ''.join('#include "'+header+'"\n' for header in includes)
    code += 'const unsigned int probe[] = {'+','.join(symbols)+'};\n'
    asm = subprocess.check_output([
        str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),
        '-S', '-mabi=apcs-gnu', '-iquote', str(tree/'include'),
        '-iquote', str(tree/'include/constants'),
        '-iquote', str(generated_headers/'include'),
        '-iquote', str(generated_headers/'include/constants'),
        '-x', 'c', '-', '-o', '-'],
        input=code, text=True)
    values = [int(value) for value in re.findall(r'\.word\s+(\d+)', asm)]
    assert len(values) == len(symbols), (symbols, values)
    return values


def validate(source, baseline, output, preflight=False):
    source, baseline, output = map(Path, [source, baseline, output])
    source = source.resolve()
    baseline = baseline.resolve()
    assert source != baseline
    # A preflight may run while make writes its ROM. It certifies source only,
    # and must not record a transient binary hash as release evidence.
    rom_sha256 = None if preflight else digest(source/'pokeemerald.gba')
    parent_sha256 = digest(baseline/'pokeemerald.gba')
    assert parent_sha256 == PARENT_ROM_SHA256, 'The layer-160 baseline ROM changed'
    if not preflight:
        assert rom_sha256 != parent_sha256, 'Compile the repaired ROM before release validation'

    marker = '.journey-'+LAYER
    report = json.loads((source/marker).read_text())
    assert report['layer'] == LAYER
    expected = dict(json.loads((baseline/'.source-acquired.json').read_text())['sha256'])
    assert len(PRIOR) == 160
    for name in PRIOR:
        expected.update(json.loads((baseline/('.journey-'+name)).read_text())['prepared_sha256'])
    layouts_path = 'data/layouts/layouts.json'
    assert (source/layouts_path).read_bytes() == (baseline/layouts_path).read_bytes()
    layouts = {layout['id']: layout for layout in json.loads((baseline/layouts_path).read_text())['layouts']}
    cave_paths, cave_audit = audit_completed_caves(source, baseline, layouts, report['caves'])
    pier_paths, port_map_changes = audit_coastal_piers(source, baseline, layouts, report['piers'])
    allowed_changed_files = sorted(set(DEWFORD_CHANGED_FILES) | cave_paths | pier_paths)
    assert len(allowed_changed_files) == 35
    outputs = report['prepared_sha256']
    assert sorted(outputs) == allowed_changed_files
    changed = sorted(path for path, sha256 in outputs.items() if expected.get(path) != sha256)
    assert changed == allowed_changed_files
    assert len(expected) > 30000

    # Check both sides independently: replaying from a modified local baseline
    # cannot certify the published source, even if the two trees happen to agree.
    for path, sha256 in expected.items():
        assert digest(baseline/path) == sha256, ('baseline', path)
    for path, sha256 in (expected | outputs).items():
        assert digest(source/path) == sha256, ('source', path)
    for name in ['.source-acquired.json', *['.journey-'+name for name in PRIOR]]:
        assert (source/name).read_bytes() == (baseline/name).read_bytes(), name

    # Layer.stage always replaces an inode atomically. Hard links keep this
    # full 32k-file replay fast while the immutable baseline remains untouched.
    with tempfile.TemporaryDirectory(prefix='dewford-coast-replay-', dir='/tmp') as temporary:
        replay = Path(temporary)
        for name in [*expected, '.source-acquired.json', *['.journey-'+name for name in PRIOR]]:
            target = replay/name
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.link(baseline/name, target)
            except OSError:
                shutil.copyfile(baseline/name, target)
        fresh = json.loads(json.dumps(prepare(replay)))
        assert fresh == report, 'Independent overlay replay disagrees with the prepared source'
        assert prepare(replay) == fresh, 'Prepared layer is not idempotent'
        for name, sha256 in outputs.items():
            assert digest(replay/name) == sha256, ('replay', name)
        # In particular, a source file shared with the baseline must never have
        # been modified through a hard link by the independent replay.
        for name in outputs.keys() & expected.keys():
            assert digest(baseline/name) == expected[name], ('replay changed baseline', name)

    route = json.loads((source/'data/maps/Route107/map.json').read_text())
    layout = layouts[route['layout']]
    assert (layout['width'], layout['height']) == (60, 20)
    town = json.loads((source/'data/maps/DewfordTown/map.json').read_text())
    assert (layouts[town['layout']]['width'], layouts[town['layout']]['height']) == (20, 20)
    old = struct.unpack('<1200H', (baseline/layout['blockdata_filepath']).read_bytes())
    new = struct.unpack('<1200H', (source/layout['blockdata_filepath']).read_bytes())
    # Do not trust the helper's own report to define which ground may change.
    allowed_cells = {
        (4, 15): (0x022a, 0x322a),
        (5, 16): (0x0124, 0x3124),
        (6, 16): (0x0124, 0x3124),
        (8, 18): (0x15f9, 0x111d),
        (7, 19): (0x15f9, 0x0639),
        (8, 19): (0x15f9, 0x1525),
    }
    actual_cells = {(i % 60, i // 60): (before, after)
                    for i, (before, after) in enumerate(zip(old, new)) if before != after}
    assert actual_cells == allowed_cells, actual_cells
    assert new[18*60+7] == old[18*60+7] == 0x313e
    assert (source/layout['border_filepath']).read_bytes() == (baseline/layout['border_filepath']).read_bytes()
    assert (source/layouts[town['layout']]['border_filepath']).read_bytes() == (baseline/layouts[town['layout']]['border_filepath']).read_bytes()
    assert [obj for obj in route['object_events'] if obj['script'] == 'JourneyCompetitive_Trainer'] == [
        obj for obj in json.loads((baseline/'data/maps/Route107/map.json').read_text())['object_events']
        if obj['script'] == 'JourneyCompetitive_Trainer']
    assert [(obj['x'], obj['y']) for obj in route['object_events']
            if obj['script'] in ('JourneyCompetitive_Trainer', 'JourneyCompetitive_Seller')] == [(1, 15), (2, 15)]

    origin = json.loads((baseline/'.source-acquired.json').read_text())
    assert origin['commit'] == UPSTREAM_COMMIT
    assert origin['sha256']['data/layouts/Route107/map.bin'] == UPSTREAM_ROUTE107_SHA256
    landscape = report['landscape']
    assert landscape['upstream_commit'] == UPSTREAM_COMMIT
    assert landscape['upstream_route107_sha256'] == UPSTREAM_ROUTE107_SHA256
    assert [(row['tile'], row['native'], row['restored']) for row in landscape['upstream_native_cells']] == [
        ([8, 18], 0x111d, 0x111d), ([7, 19], 0x0239, 0x0639), ([8, 19], 0x1125, 0x1525)]

    preserved_maps = 0
    events = 0
    for path in sorted((baseline/'data/maps').glob('*/map.json')):
        relative = path.relative_to(baseline)
        # Those nine ferry event edits were reconstructed from the original
        # seven ramps above. Every other map header remains byte-identical.
        if relative.as_posix() not in port_map_changes:
            assert path.read_bytes() == (source/relative).read_bytes(), str(relative)
        data = json.loads(path.read_text())
        events += sum(len(data.get(key, [])) for key in ('object_events', 'warp_events', 'coord_events', 'bg_events'))
        preserved_maps += 1
    assert preserved_maps > 500
    gym_report = json.loads((baseline/'.journey-extra-gyms').read_text())
    assert len(gym_report['gyms']) == 8
    for gym in gym_report['gyms']:
        data = json.loads((baseline/f'data/maps/{gym["name"]}/map.json').read_text())
        current = layouts[data['layout']]
        for key in ['blockdata_filepath', 'border_filepath']:
            path = current[key]
            assert (source/path).read_bytes() == (baseline/path).read_bytes(), path
    for path in ['src/journey_campaign_gates.c', 'src/journey_crossover.c',
                 'include/journey_team_missions.h', 'src/data/journey_pwt_trainers.h',
                 'include/constants/vars.h', 'include/constants/flags.h',
                 'include/constants/items.h', 'include/trainer_card.h',
                 'include/global.h', 'include/link.h', 'include/pokemon.h',
                 'src/data/journey_world_map.h', 'src/journey_world_map.c']:
        assert (source/path).read_bytes() == (baseline/path).read_bytes(), path
    for name in ['sWorldTiles', 'sWorldTilemap', 'sWorldPalette', 'sWorldDetailPixels']:
        pattern = name+r'\[\].*?=\s*\{([^}]+)'
        assert re.search(pattern, (source/'src/data/journey_world_map.h').read_text(), re.S)[1] == re.search(
            pattern, (baseline/'src/data/journey_world_map.h').read_text(), re.S)[1]
    abi_symbols = ['sizeof(struct SaveBlock1)', 'sizeof(struct SaveBlock2)',
                   'sizeof(struct ObjectEvent)', 'sizeof(struct LinkPlayer)',
                   'sizeof(struct LinkPlayerBlock)', 'FLAGS_COUNT']
    abi_includes = ['global.h', 'constants/flags.h', 'link.h']
    generated = ['include/constants/map_groups.h', 'include/constants/layouts.h']
    for path in generated:
        # Independent, uncompiled replay trees omit these make-generated
        # headers. Their defining maps/layouts JSON is already byte-identical.
        if not preflight or (source/path).exists():
            assert (source/path).read_bytes() == (baseline/path).read_bytes(), path
    source_abi = compiled_values(source, abi_symbols, abi_includes, baseline)
    assert source_abi == compiled_values(baseline, abi_symbols, abi_includes, baseline)
    moves = re.findall(r'F\((\w+)\)', (baseline/'include/constants/tms_hms.h').read_text().split('#define FOREACH_HM')[0])
    item_symbols = ['ITEM_TM_'+move for move in moves] + [
        'ITEM_HM_SURF', 'ITEM_HM_DIVE', 'ITEM_HM_WATERFALL', 'ITEM_HM_FLY',
        'ITEM_FULL_RESTORE', 'ITEM_MAX_REVIVE', 'ITEM_POKE_BALL']
    item_values = compiled_values(source, item_symbols, ['global.h', 'constants/items.h'], baseline)
    assert item_values == compiled_values(baseline, item_symbols, ['global.h', 'constants/items.h'], baseline)

    # Guard against compilation or ROM replacement while this evidence is read.
    if not preflight:
        assert digest(source/'pokeemerald.gba') == rom_sha256
    assert digest(baseline/'pokeemerald.gba') == parent_sha256
    result = dict(
        passed=True, rom_sha256=rom_sha256, parent_rom_sha256=parent_sha256,
        layers=PRIOR+[LAYER], independent_replay=True, idempotent=True,
        compiled_rom=not preflight, preflight=bool(preflight),
        source_hashes_checked=len(expected | outputs),
        baseline_source_hashes_checked=len(expected),
        changed_files=changed, allowed_changed_files=allowed_changed_files,
        unrelated_source_files_unchanged=True,
        other_maps_events_and_gyms_unchanged=True,
        atlas_graphics_unchanged=True, save_and_link_abi_unchanged=True,
        original_tm_hm_and_item_numbers_preserved=True,
        map_dimensions_connections_and_npcs_unchanged=True,
        authorized_port_warp_changes_only=True,
        cave_events_and_warps_unchanged=True,
        cave_mountains_rebuilt_from_exact_native_donor=True,
        both_dewford_vendors_preserved=True,
        maps_preserved=preserved_maps, events_preserved=events,
        extra_gyms_preserved=8, compiled_abi=dict(zip(abi_symbols, source_abi)),
        generated_map_and_layout_ids_preserved=True,
        compiled_item_constants_preserved=len(item_symbols),
        route107_changed_cells=[dict(tile=list(tile), before=values[0], after=values[1])
                                for tile, values in sorted(actual_cells.items())],
        upstream_commit=UPSTREAM_COMMIT, upstream_route107_sha256=UPSTREAM_ROUTE107_SHA256,
        bridge=report['bridge'], landscape=landscape, view=report['view'],
        caves=report['caves'], cave_audit=cave_audit, piers=report['piers'])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--preflight', action='store_true', help='Audit prepared source before the repaired ROM is built; not release evidence')
    args = parser.parse_args()
    result = validate(args.source, args.baseline, args.output, args.preflight)
    print(json.dumps({key: result[key] for key in ['passed', 'rom_sha256', 'parent_rom_sha256', 'source_hashes_checked', 'changed_files', 'preflight']}, indent=2))
