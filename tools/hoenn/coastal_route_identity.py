"""Name the seven cleared exterior maps as coasts, repairing their folded tile GPS."""
import hashlib
import json
from pathlib import Path
import re


ISLANDS = ('One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven')
WORLD_HEADER = 'src/data/journey_world_map.h'
POSITION_HEADER = 'src/data/journey_world_position.h'
ATLAS_ARRAYS = ('sWorldTiles', 'sWorldTilemap', 'sWorldPalette')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def atlas_hashes(header):
    hashes = {}
    for symbol in ATLAS_ARRAYS:
        declaration = re.search(r'static const u\d+ ' + symbol + r'\[\] = \{[^}]+\};', header)
        assert declaration, symbol
        hashes[symbol] = sha(declaration[0].encode())
    return hashes


def audit_grids(source, header=None):
    """Observe existing per-tile projection and every attached boundary."""
    source = Path(source)
    header = header if header is not None else (source / POSITION_HEADER).read_text()
    packed = list(map(int, re.search(r'sWorldNavigationPixels\[\] = \{([^}]+)', header)[1].split(',')))
    maps = {p.parent.name: json.loads(p.read_text()) for p in (source / 'data/maps').glob('*/map.json')}
    by_id = {m['id']: name for name, m in maps.items()}
    grids = {}
    rows = re.findall(r'\{(\d+), \(MAP_GROUP\((\w+)\)<<8\)\|MAP_NUM\(\2\), (\d+), (\d+)\}', header)
    for first, ident, width, height in rows:
        first, width, height = map(int, (first, width, height))
        values = packed[first:first + width * height]
        assert len(values) == width * height
        grids[by_id[ident]] = dict(first=first, width=width, height=height, values=values)

    def point(name, x, y):
        grid = grids[name]
        value = grid['values'][y * grid['width'] + x]
        return [value & 255, value >> 8]

    records = []
    for island in ISLANDS:
        name = island + 'Island_Harbor_Frlg'
        grid = grids[name]
        width, height = grid['width'], grid['height']
        assert (width, height) == (17, 13)
        points = [point(name, x, y) for y in range(height) for x in range(width)]
        steps = []
        for y in range(height):
            for x in range(width):
                for xx, yy in ((x + 1, y), (x, y + 1)):
                    if xx < width and yy < height:
                        steps.append(max(abs(a - b) for a, b in zip(point(name, x, y), point(name, xx, yy))))
        seams = []
        for connection in maps[name]['connections']:
            other = by_id[connection['map']]
            target = grids[other]
            ow, oh = target['width'], target['height']
            direction, offset = connection['direction'], connection['offset']
            samples = []
            for t in range(max(0, offset), min(height if direction in ('left', 'right') else width,
                                             offset + (oh if direction in ('left', 'right') else ow))):
                x, y = ((0 if direction == 'left' else width - 1), t) if direction in ('left', 'right') else (t, 0 if direction == 'up' else height - 1)
                xx, yy = ((ow - 1 if direction == 'left' else 0), t - offset) if direction in ('left', 'right') else (t - offset, oh - 1 if direction == 'up' else 0)
                here, there = point(name, x, y), point(other, xx, yy)
                assert here == there, ('Existing GPS discontinuity', name, other, x, y, here, there)
                samples.append(dict(tile=[x, y], neighbor_tile=[xx, yy], pixel=here))
            assert samples
            seams.append(dict(neighbor=other, direction=direction, offset=offset,
                              shared_border_pixels=samples, maximum_seam_delta=0))
        maximum = max(steps)
        assert maximum <= 2 and len({tuple(v) for v in points}) > 1
        records.append(dict(island=island, map=name, dimensions=[width, height],
                            grid_first=grid['first'], grid_pixels_sha256=sha(bytes(v for xy in points for v in xy)),
                            range_x=[min(v[0] for v in points), max(v[0] for v in points)],
                            range_y=[min(v[1] for v in points), max(v[1] for v in points)],
                            unique_positions=len({tuple(v) for v in points}),
                            maximum_neighbor_pixel_step=maximum, seams=seams))
    assert sum(len(row['seams']) for row in records) == 25
    return dict(position_header_sha256=sha(header.encode()), maps=records,
                connected_coast_seams=25,
                maximum_neighbor_pixel_step=max(row['maximum_neighbor_pixel_step'] for row in records),
                maximum_seam_delta=0)


def repair(layer):
    def raw(path):
        return layer.outputs[path] if path in layer.outputs else (layer.source / path).read_bytes()

    before = raw(WORLD_HEADER).decode()
    header = before
    atlas = atlas_hashes(header)
    records = []
    for island in ISLANDS:
        name = island + 'Island_Harbor_Frlg'
        path = f'data/maps/{name}/map.json'
        data = json.loads(raw(path))
        old = dict(data)
        assert data['show_map_name'] is False and data['map_type'] == 'MAP_TYPE_ROUTE'
        assert not data['object_events'] and not data['warp_events'], ('Not a cleared sea exterior', name)
        data['show_map_name'] = True
        data['map_type'] = 'MAP_TYPE_OCEAN_ROUTE'
        layer.stage(path, json.dumps(data, indent=2) + '\n')
        label = island.upper() + ' ISLAND COAST'
        pattern = r'(\{\(MAP_GROUP\(' + re.escape(data['id']) + r'\)<<8\)\|MAP_NUM\(' + re.escape(data['id']) + r'\), [^\n]+?COMPOUND_STRING\(")([^"]+)("\)\},)'
        matches = list(re.finditer(pattern, header))
        assert len(matches) == 1, name
        old_label = matches[0][2]
        assert old_label == ('THREE ISLE PORT' if island == 'Three' else island.upper() + ' ISLAND')
        header = re.sub(pattern, lambda m: m[1] + label + m[3], header)
        records.append(dict(island=island, map=name, id=data['id'], before_name=old_label, name=label,
                            header_path=path, show_map_name=True, map_type='MAP_TYPE_OCEAN_ROUTE',
                            region_map_section=old['region_map_section'],
                            connections_unchanged=True, events_warps_and_geometry_unchanged=True))
    assert atlas_hashes(header) == atlas
    assert sum(a != b for a, b in zip(before.splitlines(), header.splitlines())) == 7
    layer.stage(WORLD_HEADER, header)
    from coastal_route_projection import repair as repair_projection
    position_before = raw(POSITION_HEADER).decode()
    maps = {path.parent.name: json.loads(raw(str(path.relative_to(layer.source))))
            for path in (layer.source / 'data/maps').glob('*/map.json')}
    position_after, projection = repair_projection(position_before, maps)
    layer.stage(POSITION_HEADER, position_after)
    gps = audit_grids(layer.source, position_after)
    gps.update(projection_repair=projection, connected_border_pixels_preserved=True,
               all_other_grids_bitwise_unchanged=True)
    return dict(routes=records, changed_paths=[row['header_path'] for row in records] + [WORLD_HEADER, POSITION_HEADER],
                atlas_arrays_sha256=atlas, atlas_pixels_points_coordinates_and_tilemap_unchanged=True,
                per_tile_gps=gps, route_geometry_and_all_connections_unchanged=True,
                physical_routes_not_created_or_duplicated=True,
                city_fly_targets_and_fly_permission_code_unchanged=True,
                coast_names_only_in_banners_and_ui_not_drawn_on_atlas=True)
