"""Close whole retired native portals in the generated Shoal Cave clone.

This stages one blockdata file.  It never changes an event, map layout, bank,
map chart or the acquired native donor.  Other cloned rooms are censused too.
"""
import hashlib
import json
import struct

MAP = 'JourneyCaveHorizonte'
DONOR = 'ShoalCave_LowTideInnerRoom'
# A contiguous, native two-row rock face; a single borrowed floor cell could
# preserve the original doorway or introduce a ledge in the room floor.
WALL_DONOR = [7, 0, 3, 2]
LIP_DONOR = [29, 30, 3, 1]
FLOOR_DONOR = [18, 14, 1, 1]
PORTALS = [
    dict(kind='north_arch', entry=[15, 19], bounds=[14, 18, 3, 2],
         extra_cells=[[13, 19]], approach=[15, 20]),
    dict(kind='north_arch', entry=[30, 25], bounds=[29, 24, 3, 2],
         extra_cells=[], approach=[30, 26]),
    dict(kind='south_threshold', entry=[34, 29], bounds=[33, 30, 3, 1],
         extra_cells=[], approach=[34, 29]),
    dict(kind='south_threshold', entry=[40, 33], bounds=[39, 34, 3, 1],
         extra_cells=[], approach=[40, 33]),
]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def clone_census(source, read=None):
    """Compare all eight cloned rooms with their declared native templates."""
    def raw(path):
        return read(path) if read else (source / path).read_bytes()
    layouts = {row['id']: row for row in json.loads(raw('data/layouts/layouts.json'))['layouts']}
    branches = json.loads(raw('.journey-surf-review'))['branches']
    rows = []
    for branch in branches:
        if branch['existing_cave']:
            continue
        name, donor = branch['map'], branch['interior_template']
        mapping = json.loads(raw(f'data/maps/{name}/map.json'))
        native = json.loads(raw(f'data/maps/{donor}/map.json'))
        layout, original = layouts[mapping['layout']], layouts[native['layout']]
        assert [layout[k] for k in ('width', 'height', 'layout_version', 'primary_tileset', 'secondary_tileset')] == [original[k] for k in ('width', 'height', 'layout_version', 'primary_tileset', 'secondary_tileset')]
        width, height = layout['width'], layout['height']
        values = struct.unpack('<'+'H'*(width*height), raw(layout['blockdata_filepath']))
        donor_values = struct.unpack('<'+'H'*(width*height), raw(original['blockdata_filepath']))
        active = {(w['x'], w['y']) for w in mapping['warp_events']}
        removed = [dict(position=[w['x'], w['y']],
                        native_block=donor_values[w['y']*width+w['x']],
                        current_block=values[w['y']*width+w['x']])
                   for w in native['warp_events'] if (w['x'], w['y']) not in active]
        rows.append(dict(map=name, native_template=donor, dimensions=[width, height],
                         tilesets=[layout['primary_tileset'], layout['secondary_tileset']],
                         current_warps=mapping['warp_events'], removed_warps=removed,
                         map_sha256=digest(raw(f'data/maps/{name}/map.json')),
                         blockdata=layout['blockdata_filepath'],
                         blockdata_sha256=digest(raw(layout['blockdata_filepath']))))
    assert len(rows) == 8
    return rows


def repair(layer):
    def raw(path):
        return layer.outputs[path] if path in layer.outputs else (layer.source / path).read_bytes()
    layouts = {row['id']: row for row in json.loads(raw('data/layouts/layouts.json'))['layouts']}
    mapping = json.loads(raw(f'data/maps/{MAP}/map.json'))
    native = json.loads(raw(f'data/maps/{DONOR}/map.json'))
    layout, original = layouts[mapping['layout']], layouts[native['layout']]
    assert [layout[k] for k in ('width', 'height', 'layout_version', 'primary_tileset', 'secondary_tileset')] == [46, 38, 'emerald', 'gTileset_General', 'gTileset_Cave']
    assert (original['primary_tileset'], original['secondary_tileset']) == ('gTileset_General', 'gTileset_Cave')
    path = layout['blockdata_filepath']
    before = raw(path)
    old = list(struct.unpack('<1748H', before))
    values = old.copy()
    donor_raw = raw(original['blockdata_filepath'])
    donor_values = struct.unpack('<1748H', donor_raw)
    def rectangle(bounds):
        x, y, width, height = bounds
        return [[donor_values[(y+dy)*46+x+dx] for dx in range(width)] for dy in range(height)]
    wall, lip, floor = rectangle(WALL_DONOR), rectangle(LIP_DONOR), rectangle(FLOOR_DONOR)
    assert wall == [[0x619]*3]*2 and lip == [[0x609]*3] and floor == [[0x4211]]
    repaired = []
    for portal in PORTALS:
        x, y, width, height = portal['bounds']
        expected = [[0x60B, 0x60C, 0x60D], [0x613, 0x3214, 0x615]] if portal['kind'] == 'north_arch' else [[0x658, 0x659, 0x65A]]
        actual = [[values[(y+dy)*46+x+dx] for dx in range(width)] for dy in range(height)]
        assert actual == expected, (portal, actual)
        replacement = wall if portal['kind'] == 'north_arch' else lip
        for dy, row in enumerate(replacement):
            for dx, value in enumerate(row):
                values[(y+dy)*46+x+dx] = value
        for xx, yy in portal['extra_cells']:
            assert values[yy*46+xx] == 0x613
            values[yy*46+xx] = wall[1][0]
        repaired.append(dict(**portal, before_rows=actual, after_rows=replacement,
                             donor_bounds=WALL_DONOR if portal['kind'] == 'north_arch' else LIP_DONOR))
    assert values[14*46+19] == 0x4209
    values[14*46+19] = floor[0][0]
    changed = [dict(position=[i%46, i//46], before=a, after=b)
               for i, (a, b) in enumerate(zip(old, values)) if a != b]
    assert len(changed) == 20
    removed_floor = [row['position'] for row in changed
                     if not row['before'] & 0xC00 and row['after'] & 0xC00]
    assert removed_floor == [[15, 19], [30, 25]]
    assert all(row['position'] in removed_floor or (row['before'] & 0xFC00) == (row['after'] & 0xFC00)
               for row in changed)
    active = {(w['x'], w['y']) for w in mapping['warp_events']}
    assert active == {(14, 33)} and not active.intersection(tuple(row['position']) for row in changed)
    after = struct.pack('<1748H', *values)
    layer.stage(path, after)
    return dict(map=MAP, changed_paths=[path], changed_cells=changed,
                before_sha256=digest(before), after_sha256=digest(after),
                portals=repaired, false_ledge=dict(position=[19, 14], before=0x4209, after=0x4211,
                                                    donor_bounds=FLOOR_DONOR),
                donor=dict(map=DONOR, blockdata_sha256=digest(donor_raw),
                           tilesets=[original['primary_tileset'], original['secondary_tileset']],
                           wall_bounds=WALL_DONOR, wall_rows=wall,
                           lip_bounds=LIP_DONOR, lip_rows=lip, floor_bounds=FLOOR_DONOR, floor_rows=floor),
                removed_unused_portal_floor=removed_floor,
                clone_census=clone_census(layer.source, raw),
                all_events_connections_layouts_borders_banks_and_chart_preserved=True)
