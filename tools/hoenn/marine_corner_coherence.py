"""Make overlapping marine corner terrain agree without changing the map graph.

The generated connection graph projects some real water cells onto existing
reefs in another map. Keep those reefs, and extend their complete native art
into the overlapping water. Unlike a drawing tie breaker, this also keeps the
visible barrier and its physical collision in agreement in every camera.
"""
from collections import Counter
import hashlib
import json
import re
import struct

from badge_story_layer import read
from sevii_boundary_camera import translate_block
from validate_sevii_route_boundaries_source import Inputs

CARDINAL = {'left', 'right', 'up', 'down'}
WATER = {0x12B, 0x170}
REEF = {0x243, 0x1F9, 0x110, 0x111, 0x118, 0x119,
        0x150, 0x151, 0x158, 0x159}


def align_tanoby_banks(layer):
    """Select the native reef palette without changing existing map artwork."""
    data = json.loads(read(layer, 'data/layouts/layouts.json'))
    layouts = {row['id']: row for row in data['layouts']}
    headers = read(layer, 'src/data/tilesets/headers.h').decode()
    definitions = read(layer, 'src/data/tilesets/metatiles.h').decode()
    names = ('gTileset_General_Frlg', 'gTileset_JourneySeviiSea')
    banks = []
    for name in names:
        body = re.search(r'const struct Tileset '+name+r'\s*=\s*\{(.*?)\};', headers, re.S)[1]
        fields = dict(re.findall(r'\.(\w+)\s*=\s*(\w+)\s*,', body))
        symbol = fields.pop('metatiles')
        path = re.search(r'\b'+symbol+r'\[\].*?"([^"]+)"', definitions)[1]
        banks.append((fields, path, read(layer, path)))
    assert banks[0][0] == banks[1][0], 'Native graphics/palettes/attributes/animation must be shared'
    assert len(banks[0][2]) == len(banks[1][2]) >= 640*16
    evidence = []
    for name in ('JourneyWorldSea06', 'JourneyWorldSea07'):
        mapping = json.loads(read(layer, f'data/maps/{name}/map.json'))
        layout = layouts[mapping['layout']]
        assert layout['primary_tileset'] == names[0] and layout['layout_version'] == 'frlg'
        raw = read(layer, layout['blockdata_filepath'])
        ids = sorted({word[0] & 1023 for word in struct.iter_unpack('<H', raw) if word[0] & 1023 < 640})
        assert ids and not {0x110, 0x111, 0x118, 0x119}.intersection(ids)
        used = []
        for mid in ids:
            a, b = (bank[2][mid*16:(mid+1)*16] for bank in banks)
            assert a == b, ('Existing primary artwork would change', name, hex(mid))
            used.append(a)
        layout['primary_tileset'] = names[1]
        evidence.append(dict(map=name, layout=layout['id'], before=names[0], after=names[1],
            used_primary_ids=ids, unchanged_used_art_sha256=hashlib.sha256(b''.join(used)).hexdigest(),
            native_shared_symbols=banks[0][0], existing_own_art_and_behavior_unchanged=True,
            secondary_bank_dimensions_events_connections_unchanged=True))
    layer.stage('data/layouts/layouts.json', json.dumps(data, indent=2)+'\n')
    return evidence


def extend_dedicated_ocean_camera(layer):
    """Include dedicated coastal banks outside the two original link groups."""
    path = 'src/fieldmap.c'
    before = read(layer, path).decode()
    anchor = '    if (JourneyMarineViewGroup(gSaveBlock1Ptr->location.mapGroup))\n'
    addition = ('    // Dedicated generated coasts also expose diagonal scenery outside\n'
                '    // the original link groups. This changes drawing queries only.\n'
                '    if (header->mapType == MAP_TYPE_OCEAN_ROUTE\n'
                '        && header->mapLayout->primaryTileset == &gTileset_JourneySeviiSea)\n'
                '        return TRUE;\n')
    assert before.count(anchor) == 1 and '#include "tilesets.h"' not in before
    after = before.replace('#include "tv.h"', '#include "tv.h"\n#include "tilesets.h"')
    after = after.replace(anchor, addition+anchor)
    assert after != before
    layer.stage(path, after)
    return dict(path=path, dedicated_primary='gTileset_JourneySeviiSea',
                map_type='MAP_TYPE_OCEAN_ROUTE', visual_queries_only=True,
                collision_elevation_and_movement_code_unchanged=True)

REPRO_CASES = [
    dict(label='mossdeep', map='JourneyMossdeepOuterEastSea', player=[0, 0],
         direction='left', neighbor='JourneyMossdeepOuterSea', target=[109, 0],
         cell=[-2, -2], neighbor_cell=[108, -2], expected_metatile=0x1F9,
         parent_pop_confirmed=False),
    dict(label='five-corner', map='JourneySurfLink00701', player=[23, 3],
         direction='right', neighbor='JourneySurfLink00700', target=[0, 2],
         cell=[24, 0], neighbor_cell=[0, -1], expected_metatile=0x243),
    dict(label='kanto-corner', map='JourneyKantoCoastalBand', player=[83, 19],
         direction='down', neighbor='JourneySurfLink02700', target=[17, 0],
         cell=[88, 19], neighbor_cell=[22, -1], expected_metatile=0x243),
    dict(label='lane21-corner', map='JourneySurfLink04501', player=[1, 20],
         direction='down', neighbor='JourneySurfLink04500', target=[4, 0],
         cell=[-5, 20], neighbor_cell=[-2, -1], expected_metatile=0x243),
    dict(label='fill30-corner', map='JourneyWorldFill30Right', player=[1, 47],
         direction='down', neighbor='JourneySurfLink04000', target=[0, 0],
         cell=[-1, 48], neighbor_cell=[-2, 0], expected_metatile=0x243),
    dict(label='fill31-corner', map='JourneyWorldFill31Right', player=[4, 0],
         direction='up', neighbor='JourneySurfLink04300', target=[3, 15],
         cell=[0, -1], neighbor_cell=[-1, 15], expected_metatile=0x243),
    dict(label='three-corner', map='JourneyWorldSea03', player=[27, 0],
         direction='up', neighbor='ThreeIsland_Harbor_Frlg', target=[3, 12],
         cell=[23, -2], neighbor_cell=[-1, 11], expected_metatile=0x243),
    dict(label='tanoby-corner', map='JourneyWorldSea06', player=[63, 45],
         direction='right', neighbor='JourneyWorldSea07', target=[0, 45],
         cell=[64, 48], neighbor_cell=[0, 48], expected_metatile=0x110),
]
SOURCE_ONLY_CASES = [dict(map='JourneySurfLink03104', player=[0, 15],
    direction='left', neighbor='JourneySurfLink03103', target=[17, 15],
    cell=[-2, 21], neighbor_cell=[16, 21], visible_pixels_before=0,
    visible_pixels_after=0, reason='Outside the playable viewport in both cameras')]


class Source(Inputs):
    def __init__(self, source, layer=None):
        super().__init__(source)
        self.layer = layer

    def grid(self, name):
        layout = self.layout(name)
        path = layout['blockdata_filepath']
        if path not in self.grids:
            raw = read(self.layer, path) if self.layer else (self.source/path).read_bytes()
            assert len(raw) == 2*layout['width']*layout['height']
            self.grids[path] = list(struct.unpack('<'+'H'*(len(raw)//2), raw))
        return self.grids[path]


def adjacent(inputs, name):
    layout = inputs.layout(name)
    for c in inputs.maps[name].get('connections') or []:
        other = inputs.by_id[c['map']]
        target = inputs.layout(other)
        d = c['direction']
        if d == 'left': yield other, -target['width'], c['offset']
        elif d == 'right': yield other, layout['width'], c['offset']
        elif d == 'up': yield other, c['offset'], -target['height']
        elif d == 'down': yield other, c['offset'], layout['height']


def conflicts(inputs):
    """Enumerate actual conflicting cells, including unviewable census cells."""
    names = {n for n in inputs.maps if n.startswith('JourneySurfLink')}
    for n in list(names):
        names.update(q for q, _, _ in adjacent(inputs, n))
    rows = []
    for name in sorted(names):
        layout = inputs.layout(name)
        w, h = layout['width'], layout['height']
        direct = list(adjacent(inputs, name))
        candidates = [(r, nx+rx, ny+ry) for q, nx, ny in direct
                      for r, rx, ry in adjacent(inputs, q) if r != name]
        for y in range(-7, h+7):
            for x in range(-7, w+8):
                if 0 <= x < w and 0 <= y < h:
                    continue
                if any(0 <= x-dx < inputs.layout(q)['width'] and
                       0 <= y-dy < inputs.layout(q)['height'] for q, dx, dy in direct):
                    continue
                nodes = {}
                for q, dx, dy in candidates:
                    target = inputs.layout(q)
                    xx, yy = x-dx, y-dy
                    if 0 <= xx < target['width'] and 0 <= yy < target['height']:
                        block = inputs.word(q, xx, yy)
                        mid = translate_block(block, target['layout_version'] == 'frlg',
                                              layout['layout_version'] == 'frlg') & 1023
                        nodes[q, xx, yy] = dict(map=q, x=xx, y=yy, block=block,
                                               camera_metatile=mid)
                if len({r['camera_metatile'] for r in nodes.values()}) > 1:
                    rows.append(dict(map=name, cell=[x, y], candidates=[nodes[k] for k in sorted(nodes)]))
    return rows


def component_integrity(before, after, changed_names):
    """Prove preservation of all surviving passable cells across connections.

    Components are computed inside every map, then joined through the actual
    signed cardinal connections. This includes land and disembarkation in the
    second pass. The one local water split in NorthSea reconnects through its
    existing southern neighbor and is explicitly recorded.
    """
    names = set(changed_names)
    while True:
        more = names | {q for n in names for q, _, _ in adjacent(before, n)}
        if more == names: break
        names = more
    cache = {}

    def components(inputs, name, mode):
        key = id(inputs), name, mode
        if key in cache: return cache[key]
        layout = inputs.layout(name)
        w, h = layout['width'], layout['height']
        valid = set()
        for p, block in enumerate(inputs.grid(name)):
            water = inputs.behavior(name, block) in inputs.water
            collision = (block >> 10) & 3
            if (water and collision == 0) if mode == 'water' else collision == 0:
                valid.add(p)
        labels, sizes = {}, []
        for p in sorted(valid):
            if p in labels: continue
            label = len(sizes)
            queue = [p]
            labels[p] = label
            for at in queue:
                x, y = at % w, at // w
                for xx, yy in ((x-1, y), (x+1, y), (x, y-1), (x, y+1)):
                    pos = yy*w+xx
                    if 0 <= xx < w and 0 <= yy < h and pos in valid and pos not in labels:
                        labels[pos] = label
                        queue.append(pos)
            sizes.append(len(queue))
        cache[key] = labels, sizes
        return cache[key]

    def joined(inputs, mode):
        graph = {(n, i): set() for n in sorted(names)
                 for i in range(len(components(inputs, n, mode)[1]))}
        for name in sorted(names):
            width = inputs.layout(name)['width']
            labels, _ = components(inputs, name, mode)
            for x, y, d, xx, yy in inputs.perimeter(name):
                if y*width+x not in labels: continue
                target = inputs.target(name, d, xx, yy)
                if target is None: continue
                other, tx, ty = target
                other_labels, _ = components(inputs, other, mode)
                pos = ty*inputs.layout(other)['width']+tx
                if pos not in other_labels: continue
                a, b = (name, labels[y*width+x]), (other, other_labels[pos])
                graph[a].add(b)
                graph[b].add(a)
        seen = {}
        count = 0
        for start in graph:
            if start in seen: continue
            queue = [start]
            seen[start] = count
            for at in queue:
                for nxt in graph[at]:
                    if nxt not in seen:
                        seen[nxt] = count
                        queue.append(nxt)
            count += 1
        return seen, count

    checks = []
    for mode in ('water', 'all_walkable'):
        old_joined, old_count = joined(before, mode)
        new_joined, new_count = joined(after, mode)
        mapping = {}
        for name in sorted(names):
            old, _ = components(before, name, mode)
            new, _ = components(after, name, mode)
            for pos, label in new.items():
                assert pos in old, ('Unexpected passable opening', name, pos)
                mapping.setdefault(old_joined[name, old[pos]], set()).add(new_joined[name, label])
        assert all(len(v) == 1 for v in mapping.values()), ('Passable component split', mode)
        assert len(mapping) == old_count == new_count, ('Passable component lost', mode)
        checks.append(dict(mode=mode, maps=len(names), before_components=old_count,
            after_components=new_count, all_surviving_original_cells_preserve_connectivity=True,
            changed_map_component_sizes=[dict(map=n,
                before=components(before, n, mode)[1], after=components(after, n, mode)[1])
                for n in sorted(changed_names)]))
    spans = []
    for name in sorted(changed_names):
        layout = before.layout(name)
        w, h = layout['width'], layout['height']
        for c in before.maps[name].get('connections') or []:
            direction = c['direction']
            if direction not in CARDINAL: continue
            other = before.by_id[c['map']]
            coordinates = []
            for inputs in (before, after):
                here, _ = components(inputs, name, 'water')
                there, _ = components(inputs, other, 'water')
                values = []
                for x, y, d, xx, yy in inputs.perimeter(name):
                    if d != direction or y*w+x not in here: continue
                    target = inputs.target(name, d, xx, yy)
                    if target is None or target[0] != other: continue
                    _, tx, ty = target
                    if ty*inputs.layout(other)['width']+tx in there:
                        values.append(y if d in ('left', 'right') else x)
                coordinates.append(sorted(set(values)))
            assert not coordinates[0] or coordinates[1], ('Water connection closed', name, c)
            spans.append(dict(map=name, direction=direction, neighbor=other,
                before_water_coordinates=coordinates[0], after_water_coordinates=coordinates[1]))
    return dict(global_component_checks=checks, connection_spans=spans,
                all_original_water_connections_remain_open=True)


def repair(layer):
    before, current = Source(layer.source, layer), Source(layer.source, layer)
    original_conflicts = conflicts(current)
    assert len(original_conflicts) == 107, ('Unexpected parent corner census', len(original_conflicts))
    changes = {}
    for case in original_conflicts:
        candidates = case['candidates']
        water = [r for r in candidates if r['camera_metatile'] in WATER]
        reefs = [r for r in candidates if r['camera_metatile'] not in WATER]
        assert water and reefs
        assert {r['camera_metatile'] for r in reefs} <= REEF
        assert len({r['camera_metatile'] for r in reefs}) == 1
        donor = min(reefs, key=lambda r: (r['map'], r['y'], r['x']))
        for row in water:
            name, x, y = row['map'], row['x'], row['y']
            original = before.word(name, x, y)
            assert original in (0x112B, 0x1170), ('Only open native sea may be extended', row)
            assert before.behavior(name, original) in before.water
            assert all((event['x'], event['y']) != (x, y) for kind in
                       ('object_events', 'warp_events', 'coord_events', 'bg_events')
                       for event in before.maps[name].get(kind, [])), ('Event at repair', name, x, y)
            mid = translate_block(donor['block'],
                before.layout(donor['map'])['layout_version'] == 'frlg',
                before.layout(name)['layout_version'] == 'frlg') & 1023
            block = 0x1400 | mid  # Surf elevation 1, solid collision 1.
            key = name, x, y
            if key in changes: assert changes[key]['after'] == block
            changes[key] = dict(map=name, x=x, y=y, before=original, after=block,
                donor=dict(map=donor['map'], x=donor['x'], y=donor['y'], block=donor['block']))
    assert len(changes) == 118
    for (name, x, y), row in changes.items():
        current.grid(name)[y*current.layout(name)['width']+x] = row['after']
    assert not conflicts(current), 'The repair introduced or retained a contradictory corner'
    changed_names = {name for name, _, _ in changes}
    connectivity = component_integrity(before, current, changed_names)
    paths = sorted({current.layout(name)['blockdata_filepath'] for name in changed_names})
    files = []
    for path in paths:
        original = read(layer, path)
        result = struct.pack('<'+'H'*len(current.grids[path]), *current.grids[path])
        layer.stage(path, result)
        files.append(dict(path=path, before_sha256=hashlib.sha256(original).hexdigest(),
                          after_sha256=hashlib.sha256(result).hexdigest()))
    bank_alignment = align_tanoby_banks(layer)
    camera_scope = extend_dedicated_ocean_camera(layer)
    return dict(kind='marine-corner-coherence', changed_paths=paths, files=files,
        bank_alignment=bank_alignment, camera_scope=camera_scope,
        changed_cells=[changes[key] for key in sorted(changes)], changed_cell_count=118,
        changed_map_counts=dict(sorted(Counter(name for name, _, _ in changes).items())),
        before_ambiguous_corner_cells=107, after_ambiguous_corner_cells=0,
        source_only_cases=SOURCE_ONLY_CASES, reproduction_cases=REPRO_CASES,
        native_small_reefs_and_four_complete_tanoby_large_reefs=True,
        existing_land_reefs_buildings_objects_events_connections_and_world_map_preserved=True,
        **connectivity)
