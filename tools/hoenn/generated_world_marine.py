"""Repair complete coastal objects without changing route footprints or the atlas.

The surf-review overlay compared complete block words instead of metatile IDs.
It consequently replaced two quarters of some native 2x2 rocks and retained
the other two at a different elevation. Restore the complete native object
only inside the existing blocked footprint. A half rock beside open water is
replaced with whole small rocks, preserving the open passage.
"""
import hashlib
import json
import struct

from badge_story_layer import read


SURFACE_TYPES = {'MAP_TYPE_CITY', 'MAP_TYPE_TOWN', 'MAP_TYPE_ROUTE',
                 'MAP_TYPE_OCEAN_ROUTE'}
PRIMARY_FAMILIES = {
    'gTileset_General': ((0x150, 0x151, 0x158, 0x159), 0x1F9),
    'gTileset_General_Frlg': ((0x110, 0x111, 0x118, 0x119), 0x243),
    'gTileset_JourneySeviiSea': ((0x110, 0x111, 0x118, 0x119), 0x243),
}


def repair(layer):
    layouts = {row['id']: row for row in json.loads(
        read(layer, 'data/layouts/layouts.json'))['layouts']}
    maps = {}
    for path in sorted((layer.source / 'data/maps').glob('*/map.json')):
        relative = path.relative_to(layer.source).as_posix()
        maps[path.parent.name] = json.loads(read(layer, relative))
    by_id = {mapping['id']: name for name, mapping in maps.items()}
    terrain, originals = {}, {}
    for name, mapping in maps.items():
        layout = layouts[mapping['layout']]
        path = layout['blockdata_filepath']
        if path not in terrain:
            raw = read(layer, path)
            originals[path] = raw
            terrain[path] = list(struct.unpack('<' + 'H' * (len(raw) // 2), raw))

    def locate(name, x, y, depth=0):
        layout = layouts[maps[name]['layout']]
        width, height = layout['width'], layout['height']
        if 0 <= x < width and 0 <= y < height:
            return layout['blockdata_filepath'], y * width + x, name, x, y
        if depth >= 2:
            return None
        direction = ('left' if x < 0 else 'right' if x >= width
                     else 'up' if y < 0 else 'down')
        for connection in maps[name].get('connections') or []:
            if connection['direction'] != direction:
                continue
            target = by_id[connection['map']]
            other = layouts[maps[target]['layout']]
            offset = connection['offset']
            xx = (x - offset if direction in ('up', 'down') else
                  x + other['width'] if direction == 'left' else x - width)
            yy = (y - offset if direction in ('left', 'right') else
                  y + other['height'] if direction == 'up' else y - height)
            if 0 <= xx < other['width'] and 0 <= yy < other['height']:
                return locate(target, xx, yy, depth + 1)
        return None

    # Plan against the immutable incoming values; deduplicate a 2x2 object
    # straddling map boundaries by its physical source cells.
    incoming = {path: tuple(values) for path, values in terrain.items()}
    donor_layout = layouts[maps['VictoryRoad_B2F']['layout']]
    donor_values = incoming[donor_layout['blockdata_filepath']]
    donor_width = donor_layout['width']
    rock_donor = [donor_values[(14 + dy) * donor_width + 23 + dx]
                  for dy in range(2) for dx in range(2)]
    assert donor_layout['primary_tileset'] == 'gTileset_General'
    assert rock_donor == [0x0550, 0x0551, 0x0558, 0x0559]
    seen, rocks, inspected, unrecognized = set(), [], [], []
    for name, mapping in maps.items():
        layout = layouts[mapping['layout']]
        if (mapping['map_type'] not in SURFACE_TYPES or
                layout['primary_tileset'] not in PRIMARY_FAMILIES):
            continue
        inspected.append(name)
        quadrants, small = PRIMARY_FAMILIES[layout['primary_tileset']]
        values = incoming[layout['blockdata_filepath']]
        width = layout['width']
        anchors = set()
        for index, value in enumerate(values):
            if value & 1023 in quadrants:
                quadrant = quadrants.index(value & 1023)
                anchors.add((index % width - quadrant % 2,
                             index // width - quadrant // 2))
        for x, y in sorted(anchors):
            cells = [locate(name, x + dx, y + dy)
                     for dy in range(2) for dx in range(2)]
            if any(cell is None for cell in cells):
                continue  # A different native multi-row object or outer border.
            key = tuple(sorted((cell[0], cell[1]) for cell in cells))
            actual = [incoming[cell[0]][cell[1]] for cell in cells]
            mids = [value & 1023 for value in actual]
            if (key in seen or mids == list(quadrants) or small not in mids):
                continue
            if not all(mid in (expected, small)
                       for mid, expected in zip(mids, quadrants)):
                # Route126's lower row is open sea. Retain that water and
                # replace its one surviving upper-left fragment in place.
                if not (name == 'Route126' and (x, y) == (46, 77) and
                        mids == [0x150, small, 0x170, 0x170]):
                    unrecognized.append(dict(map=name, anchor=[x, y], metatiles=mids))
                    continue
                replacements = [small, small, 0x170, 0x170]
                method = 'whole-small-rocks-preserve-open-water'
            else:
                assert all(value & 0xC00 for value in actual), (name, x, y)
                replacements = quadrants
                method = 'restore-native-2x2-blocked-footprint'
            seen.add(key)
            result = [(value & ~1023) | mid
                      for value, mid in zip(actual, replacements)]
            assert all((before & ~1023) == (after & ~1023)
                       for before, after in zip(actual, result))
            for cell, value in zip(cells, result):
                terrain[cell[0]][cell[1]] = value
            rocks.append(dict(map=name, anchor=[x, y], method=method,
                              cells=[[c[2], c[3], c[4]] for c in cells],
                              before=actual, after=result,
                              elevation_and_collision_preserved=True))

    # Three Island's gym clearing removed only the crowns above row20.
    # Remove the three orphan bodies and terminate the remaining overlapping
    # forest with complete native pine crowns and bodies one row lower.
    # SixIsland (2,3) is the native 2x3 pine donor. 0x00C/0x00D are palm
    # crowns and must not be combined with these conifer bodies.
    name = 'ThreeIsland_Frlg'
    layout = layouts[maps[name]['layout']]
    path, width = layout['blockdata_filepath'], layout['width']
    values = terrain[path]
    before_tree = [[values[y * width + x] for x in range(6)]
                   for y in range(19, 24)]
    assert before_tree[0] == [0x3001] * 6
    assert before_tree[1] == [0x041E, 0x041F] * 3
    assert before_tree[2] == [0x0414, 0x0415, 0x0414, 0x0415, 0x0414, 0x0417]
    assert before_tree[3] == [0x041C, 0x041D, 0x041C, 0x041D, 0x041C, 0x041F]
    donor = layouts[maps['SixIsland_Frlg']['layout']]
    donor_values = terrain[donor['blockdata_filepath']]
    donor_width = donor['width']
    assert [donor_values[3 * donor_width + x] for x in (2, 3)] == [0x300E, 0x300F]
    assert [donor_values[4 * donor_width + x] for x in (2, 3)] == [0x041E, 0x041F]
    for x in range(6):
        values[20 * width + x] = 0x3001
        values[21 * width + x] = 0x300E + x % 2
        values[22 * width + x] = 0x041E + x % 2
    after_tree = [[values[y * width + x] for x in range(6)]
                  for y in range(19, 24)]
    assert before_tree[0] == after_tree[0] and before_tree[4] == after_tree[4]
    tree = dict(map=name, donor='SixIsland_Frlg', donor_top_left=[2, 3],
                bounds=[0, 19, 6, 5], before=before_tree, after=after_tree,
                gym_entry=[4, 18], entry_and_two_clear_rows_preserved=True,
                lower_forest_and_house_unchanged=True)

    assert not unrecognized, ('Unreviewed mixed native boulder', unrecognized)
    changed = []
    for path, values in sorted(terrain.items()):
        raw = struct.pack('<' + 'H' * len(values), *values)
        if raw != originals[path]:
            layer.stage(path, raw)
            changed.append(dict(path=path,
                                before_sha256=hashlib.sha256(originals[path]).hexdigest(),
                                after_sha256=hashlib.sha256(raw).hexdigest()))
    return dict(kind='complete-native-marine-objects',
                inspected_surface_maps=inspected, rocks=rocks, forest=tree,
                native_boulder_donor=dict(map='VictoryRoad_B2F', anchor=[23, 14],
                                         primary_tileset='gTileset_General',
                                         blocks=rock_donor),
                changed_files=changed, atlas_and_connections_unchanged=True,
                rock_collision_and_elevation_bits_unchanged=True)
