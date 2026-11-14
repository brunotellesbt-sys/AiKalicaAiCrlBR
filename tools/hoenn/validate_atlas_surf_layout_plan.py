"""Independently audit the physical raster proposed for the immutable atlas.

This module deliberately imports no generator. Its inputs are a geometry plan
and independently supplied, classified atlas pixels. It proves properties of
those files only; it does not certify source inputs, compiled ROMs or gameplay.
"""
import argparse
from collections import Counter, deque
import hashlib
import json
from pathlib import Path


VECTORS = {'left': (-1, 0), 'right': (1, 0), 'up': (0, -1), 'down': (0, 1)}
OPPOSITE = {'left': 'right', 'right': 'left', 'up': 'down', 'down': 'up'}


def integer(value, label):
    assert type(value) is int, ('Expected an integer', label, value)
    return value


def pixels(values, label):
    """Reject duplicates instead of silently normalizing a classification."""
    result = set()
    for value in values:
        assert isinstance(value, (list, tuple)) and len(value) == 2, (label, value)
        point = tuple(integer(v, label) for v in value)
        assert 0 <= point[0] < 224 and 0 <= point[1] < 112, (label, point)
        assert point not in result, ('Duplicate classified atlas pixel', label, point)
        result.add(point)
    return result


def reference_raster(points, scale=8, width=6):
    """Construct cores and only the two-tile joins justified by four-neighbors."""
    margin = (scale-width)//2
    water = set()
    for x, y in points:
        water.update((x*scale+xx, y*scale+yy)
                     for yy in range(margin, margin+width)
                     for xx in range(margin, margin+width))
        if (x+1, y) in points:
            water.update((xx, y*scale+yy)
                         for xx in range(x*scale+margin+width, (x+1)*scale+margin)
                         for yy in range(margin, margin+width))
        if (x, y+1) in points:
            water.update((x*scale+xx, yy)
                         for yy in range(y*scale+margin+width, (y+1)*scale+margin)
                         for xx in range(margin, margin+width))
    return water


def local_water(chunk):
    result = set()
    width = integer(chunk['width'], 'chunk width')
    height = integer(chunk['height'], 'chunk height')
    for run in chunk['water_runs']:
        assert isinstance(run, (list, tuple)) and len(run) == 3, ('Invalid water run', chunk['name'], run)
        y, left, right = (integer(v, 'water run') for v in run)
        assert 0 <= y < height and 0 <= left < right <= width, ('Out-of-bounds water run', chunk['name'], run)
        for x in range(left, right):
            assert (x, y) not in result, ('Overlapping water runs', chunk['name'], x, y)
            result.add((x, y))
    assert result, ('Empty generated map', chunk['name'])
    return result


def position(chunk, x, y):
    """Reference affine GPS, including floor division at negative borders."""
    return ((chunk['origin'][0]+x)//8, (chunk['origin'][1]+y)//8)


def validate_plan(plan, *, route_pixels, access_pixels=(), native_pixels=(), icon_pixels=()):
    """Audit a plan against external classification, never its own totals.

    ``route_pixels`` names atlas pixels that require new geometry. Native
    pixels and icon centers are explicitly excluded. Access pixels are short,
    separately reviewed exceptions; their justification belongs to the
    classification auditor, not to this geometry check.
    """
    assert plan['scale'] == 8 and plan['corridor_width'] == 6, 'Unexpected atlas physical scale'
    chunk_tiles = integer(plan.get('chunk_tiles', 32), 'chunk_tiles')
    assert 1 <= chunk_tiles <= 127
    routes = pixels(route_pixels, 'route')
    accesses = pixels(access_pixels, 'access')
    natives = pixels(native_pixels, 'native')
    icons = pixels(icon_pixels, 'icon')
    for first, second in ((routes, accesses), (routes, natives), (routes, icons),
                          (accesses, natives), (accesses, icons), (natives, icons)):
        assert not first & second, ('Atlas classifications overlap', sorted(first & second)[:8])
    expected = reference_raster(routes | accesses)
    assert expected, 'No independently classified route pixels supplied'
    chunks = plan['chunks']
    assert chunks, 'No generated physical maps'
    names, ids, packed_ids, groups = {}, {}, set(), Counter()
    owners, local = {}, {}
    for chunk in chunks:
        name, ident = chunk['name'], chunk['id']
        assert isinstance(name, str) and name and name not in names, ('Duplicate map name', name)
        assert isinstance(ident, str) and ident and ident not in ids, ('Duplicate map ID', ident)
        names[name] = chunk
        ids[ident] = chunk
        group = chunk['group']
        assert isinstance(group, (str, int)) and not isinstance(group, bool), ('Invalid map group', group)
        number = integer(chunk['number'], 'map number')
        assert 0 <= number < 100, ('Map number exceeds signed WarpData-safe group contract', name, number)
        packed = group, number
        assert packed not in packed_ids, ('Duplicate group/map number', packed)
        packed_ids.add(packed)
        groups[group] += 1
        if 'group_index' in chunk:
            assert 0 <= integer(chunk['group_index'], 'group index') <= 127
        assert isinstance(chunk['origin'], (list, tuple)) and len(chunk['origin']) == 2
        ox, oy = (integer(v, 'global origin') for v in chunk['origin'])
        w, h = (integer(chunk[key], key) for key in ('width', 'height'))
        assert 1 <= w <= chunk_tiles and 1 <= h <= chunk_tiles, ('Invalid physical map dimensions', name, w, h)
        assert not any(key in chunk for key in ('gps_cells', 'gps_grid', 'gps_interpolation')), \
            ('Per-cell/interpolated GPS is outside the affine contract', name)
        cells = local_water(chunk)
        local[name] = cells
        for x, y in cells:
            point = ox+x, oy+y
            assert point not in owners, ('Generated maps overlap in physical water', point, owners.get(point), name)
            owners[point] = name
            assert position(chunk, x, y) == (point[0]//8, point[1]//8)
    assert all(count <= 100 for count in groups.values()), ('Too many maps in a group', dict(groups))
    actual = set(owners)
    assert actual == expected, ('Physical raster differs from independently classified atlas',
                               'missing', len(expected-actual), sorted(expected-actual)[:8],
                               'extra', len(actual-expected), sorted(actual-expected)[:8])

    connections, required = {}, set()
    for name, chunk in names.items():
        ox, oy = chunk['origin']
        for connection in chunk.get('connections') or []:
            direction = connection['direction']
            assert direction in VECTORS, ('Non-cardinal generated seam', name, direction)
            target = names.get(connection['map']) or ids.get(connection['map'])
            assert target is not None, ('Connection to map outside generated plan', name, connection['map'])
            other = target['name']
            offset = integer(connection['offset'], 'connection offset')
            key = name, other, direction
            assert key not in connections, ('Duplicate connection', key)
            connections[key] = offset
            tx, ty = target['origin']
            if direction == 'left': expected_origin = ox-target['width'], oy+offset
            elif direction == 'right': expected_origin = ox+chunk['width'], oy+offset
            elif direction == 'up': expected_origin = ox+offset, oy-target['height']
            else: expected_origin = ox+offset, oy+chunk['height']
            assert (tx, ty) == expected_origin, ('Connection folds or moves physical geography', key, (tx, ty), expected_origin)
    cardinal_checks = eight_tile_checks = 0
    for (x, y), name in owners.items():
        for direction in ('right', 'down'):
            dx, dy = VECTORS[direction]
            other = owners.get((x+dx, y+dy))
            if other is None:
                continue
            if name != other:
                required.add((name, other, direction))
                required.add((other, name, OPPOSITE[direction]))
            before, after = (x//8, y//8), ((x+dx)//8, (y+dy)//8)
            assert after[1 if dx else 0] == before[1 if dx else 0], 'Perpendicular GPS drift'
            assert after[0 if dx else 1]-before[0 if dx else 1] in (0, 1)
            cardinal_checks += 1
            if all((x+dx*k, y+dy*k) in owners for k in range(1, 9)):
                end = (x+dx*8)//8, (y+dy*8)//8
                assert end == (before[0]+dx, before[1]+dy), 'Eight-tile distance is not one atlas pixel'
                eight_tile_checks += 1
    assert set(connections) == required, ('Missing or spurious physical seams',
                                        sorted(required-set(connections))[:8], sorted(set(connections)-required)[:8])
    for (name, other, direction), offset in connections.items():
        assert connections.get((other, name, OPPOSITE[direction])) == -offset, ('Nonreciprocal physical seam', name, other)
    remaining, sizes = set(owners), []
    while remaining:
        point = remaining.pop()
        pending, count = deque([point]), 0
        while pending:
            x, y = pending.popleft()
            count += 1
            for dx, dy in VECTORS.values():
                target = x+dx, y+dy
                if target in remaining:
                    remaining.remove(target)
                    pending.append(target)
        sizes.append(count)
    raw = json.dumps(plan, sort_keys=True, separators=(',', ':')).encode()
    return dict(kind='atlas-surf-layout-plan-audit', passed=True,
                plan_sha256=hashlib.sha256(raw).hexdigest(),
                scope='Plan and independently supplied classified pixels only',
                source_validated=False, compiled_rom_validated=False, native_controls_validated=False,
                atlas_route_pixels=len(routes), access_pixels=len(accesses),
                excluded_native_pixels=len(natives), excluded_icon_pixels=len(icons),
                physical_water_cells=len(actual), generated_maps=len(chunks),
                map_groups=dict(groups), directed_seams=len(connections),
                cardinal_water_neighbor_checks=cardinal_checks,
                straight_eight_tile_distance_checks=eight_tile_checks,
                generated_water_components=len(sizes), component_sizes=sorted(sizes),
                all_water_covered_once=True, affine_direction_and_distance=True,
                physical_seams_reciprocal_and_global_origins_agree=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--classification', type=Path, required=True,
                        help='Independently reviewed route/access/native/icon pixel lists')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    classification = json.loads(args.classification.read_text())
    routes = classification.get('generated_pixels', classification.get('route_pixels'))
    assert routes is not None, 'Classification must supply generated_pixels'
    result = validate_plan(json.loads(args.plan.read_text()),
                           route_pixels=routes,
                           access_pixels=classification.get('access_pixels', []),
                           native_pixels=classification.get('native_pixels', []),
                           icon_pixels=classification.get('icon_pixels', []))
    result['classification_file_sha256'] = hashlib.sha256(args.classification.read_bytes()).hexdigest()
    result['plan_file_sha256'] = hashlib.sha256(args.plan.read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
