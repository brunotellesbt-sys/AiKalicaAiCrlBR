"""Independently audit layer 170 whole scenery, navigation and compiled bytes."""
import argparse
from collections import Counter, deque
import hashlib
import json
from pathlib import Path
import re
import struct

import coast_scenery_review_contract as contract
from validate_sevii_route_boundaries_source import (
    Inputs, digest, safe_relative, marine_scope, gps, graph_limitations,
    compiled_bindings as previous_compiled_bindings, symbols)


SCENERY_PATH = 'src/event_object_movement.c'
CAMERA_PATH = 'src/fieldmap.c'
SCENERY_GRAPHICS = 'OBJ_EVENT_GFX_JOURNEY_COAST_BOUNDARY_ROCK'
RUNTIME_SYMBOLS = ('MapGridGetMetatileIdAt', 'NewGameInitData',
                   'CopyPartyAndObjectsFromSave', 'TrySpawnObjectEvents')
# Native object families, independently identified from their complete donors.
FRLG_FAMILIES = ((0x110, 0x111, 0x118, 0x119),
                 (0x1CB, 0x1CC, 0x1D3, 0x1D4),
                 (0x212, 0x213, 0x21A, 0x21B),
                 (0x244, 0x245, 0x24C, 0x24D),
                 (0x25E, 0x25F, 0x24C, 0x24D))
EMERALD_FAMILIES = ((0x150, 0x151, 0x158, 0x159),)
REPLACED_MAPS = {'OneIsland_KindleRoad_Frlg', 'TwoIsland_Harbor_Frlg',
                 'ThreeIsland_Port_Frlg', 'FourIsland_Frlg'}
BANK_MAPS = ('JourneyWorldSea06', 'JourneyWorldSea07')
BANK_BEFORE, BANK_AFTER = 'gTileset_General_Frlg', 'gTileset_JourneySeviiSea'
BANK_SHARED = ('isCompressed', 'isSecondary', 'tiles', 'palettes', 'metatileAttributes', 'callback')


def check_layout_metadata(current, old):
    """Allow exactly two compatible primary-bank selections, no other metadata.

    Equal bank names or shared graphics do not prove equal metatiles: the
    Tanoby reef differs in its palette nibbles. Check every existing primary
    metatile used by these two maps, plus all shared native loading symbols.
    """
    assert current.layouts.keys() == old.layouts.keys()
    changed = []
    for ident, before in old.layouts.items():
        after = current.layouts[ident]
        if before == after:
            continue
        consumers = sorted(n for n, m in current.maps.items() if m['layout'] == ident)
        assert len(consumers) == 1 and consumers[0] in BANK_MAPS, ('Unreviewed layout metadata', ident)
        name = consumers[0]
        assert before['primary_tileset'] == BANK_BEFORE and after['primary_tileset'] == BANK_AFTER
        assert before | {'primary_tileset': BANK_AFTER} == after, ('Other layout field changed', ident)
        assert before['layout_version'] == 'frlg'

        def bank(inputs, symbol):
            body = re.search(r'const struct Tileset '+re.escape(symbol)+r'\s*=\s*\{(.*?)\};', inputs.headers, re.S)[1]
            fields = dict(re.findall(r'\.(\w+)\s*=\s*(\w+)\s*,', body))
            meta = fields['metatiles']
            path = re.search(r'\b'+re.escape(meta)+r'\[\].*?"([^"]+)"', inputs.definitions)[1]
            raw = (inputs.source/path).read_bytes()
            assert len(raw) >= 640*16
            return fields, path, raw

        a, apath, araw = bank(old, BANK_BEFORE)
        b, bpath, braw = bank(current, BANK_AFTER)
        assert {k: a[k] for k in BANK_SHARED} == {k: b[k] for k in BANK_SHARED}, 'Bank graphics/loading/behavior differs'
        assert old.grid(name) == current.grid(name), ('Bank-aligned own map terrain changed', name)
        mids = sorted({word & 1023 for word in old.grid(name) if word & 1023 < 640})
        assert mids and not {0x110, 0x111, 0x118, 0x119}.intersection(mids)
        observed = []
        for mid in mids:
            span = slice(mid*16, (mid+1)*16)
            assert araw[span] == braw[span], ('Existing map artwork changes with bank', name, hex(mid))
            observed.append(araw[span])
        changed.append(dict(map=name, before=BANK_BEFORE, after=BANK_AFTER,
            used_primary_ids=mids, used_metatiles_sha256=hashlib.sha256(b''.join(observed)).hexdigest(),
            shared_symbols={k: a[k] for k in BANK_SHARED},
            original_metatiles=dict(file=apath, sha256=hashlib.sha256(araw).hexdigest()),
            selected_metatiles=dict(file=bpath, sha256=hashlib.sha256(braw).hexdigest()),
            every_existing_primary_metatile_identical=True, secondary_bank_unchanged=True,
            dimensions_events_connections_and_own_terrain_unchanged=True))
    return sorted(changed, key=lambda r: r['map'])


def families(inputs, name):
    return FRLG_FAMILIES if inputs.layout(name)['layout_version'] == 'frlg' else EMERALD_FAMILIES


def small(inputs, name):
    return 0x243 if inputs.layout(name)['layout_version'] == 'frlg' else 0x1F9


def locate(inputs, name, x, y, depth=0):
    layout = inputs.layout(name)
    if 0 <= x < layout['width'] and 0 <= y < layout['height']:
        return name, x, y
    if depth == 2:
        return None
    direction = 'left' if x < 0 else 'right' if x >= layout['width'] else 'up' if y < 0 else 'down'
    target = inputs.target(name, direction, x, y)
    return None if target is None else locate(inputs, *target, depth+1)


def boulder_patterns(inputs, names):
    """List every family-derived anchor, including native variants and outer cuts."""
    rows, seen = [], set()
    for name in names:
        width = inputs.layout(name)['width']
        for family in families(inputs, name):
            anchors = {(at % width-family.index(word & 1023) % 2,
                        at // width-family.index(word & 1023) // 2)
                       for at, word in enumerate(inputs.grid(name)) if word & 1023 in family}
            for x, y in sorted(anchors):
                cells = [locate(inputs, name, x+dx, y+dy) for dy in range(2) for dx in range(2)]
                key = tuple(sorted(cell for cell in cells if cell is not None))
                if key in seen:
                    continue
                seen.add(key)
                mids = [None if cell is None else inputs.word(*cell) & 1023 for cell in cells]
                if None in cells:
                    kind = 'outer_continuation'
                elif tuple(mids) in families(inputs, name):
                    kind = 'complete'
                elif any(all(mid in (expected, small(inputs, cell[0]))
                             for mid, expected, cell in zip(mids, candidate, cells))
                         for candidate in families(inputs, name)):
                    kind = 'mixed_small_and_large'
                else:
                    kind = 'native_context_variant'
                rows.append(dict(map=name, anchor=[x, y], family=list(family),
                                 cells=[None if cell is None else list(cell) for cell in cells],
                                 metatiles=mids, classification=kind))
    return rows


def _row_key(row):
    return json.dumps(row, sort_keys=True)


def parent_boundary_words(old):
    marker = json.loads((old.source/'.journey-sevii-route-boundaries').read_bytes())
    return {(row['map'], *cell['tile']): (cell['before'], cell['after'])
            for row in marker['boundaries']['outer_water_changes'] for cell in row['cells']}


def check_boulders(current, old, names, original_words=None):
    before, after = boulder_patterns(old, names), boulder_patterns(current, names)
    prior_context = {_row_key(row) for row in before if row['classification'] != 'complete'}
    original_words = {} if original_words is None else original_words
    def native_original(row):
        return all(cell is None or mid == (original_words.get(tuple(cell), (old.word(*cell),))[0] & 1023)
                   for cell, mid in zip(row['cells'], row['metatiles']))
    new_context = [row for row in after if row['classification'] != 'complete'
                   and _row_key(row) not in prior_context and not native_original(row)]
    assert not new_context, ('New incomplete/native-context boulder pattern', new_context[:3])
    mixed = [row for row in after if row['classification'] == 'mixed_small_and_large']
    assert not mixed, ('Mixed complete small rocks and large-reef fragments remain', mixed[:3])
    counts = Counter(row['classification'] for row in after)
    return dict(maps=len(names), map_names=names, family_metatiles=[list(row) for row in FRLG_FAMILIES+EMERALD_FAMILIES],
                objects=after, classifications=dict(counts), new_partial_objects=0,
                mixed_small_and_large_objects=0, inherited_context_patterns_preserved=True,
                source_census_not_native_camera_proof=True)


def _without_comments(text):
    return re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)


def _function_span(text, name):
    matches = list(re.finditer(r'(?:static\s+)?void\s+'+re.escape(name)+r'\s*\([^;{}]*\)\s*\{', text))
    assert len(matches) == 1, ('Missing/duplicate runtime function', name)
    match = matches[0]
    depth, end = 1, match.end()
    while depth and end < len(text):
        depth += (text[end] == '{')-(text[end] == '}')
        end += 1
    assert depth == 0, ('Unclosed runtime function', name)
    return match.start(), end


def check_scenery_runtime(current, old):
    before = _without_comments((old.source/SCENERY_PATH).read_text())
    after = _without_comments((current.source/SCENERY_PATH).read_text())
    start, end = _function_span(after, 'JourneySpawnConnectedCoastScenery')
    helper = re.sub(r'\s+', '', after[start:end])
    required = (
        'original->graphicsId!=OBJ_EVENT_GFX_JOURNEY_COAST_BOUNDARY_ROCK',
        'FlagGet(original->flagId)',
        'GetObjectEventIdByLocalIdAndMap(original->localId,connection->mapNum,connection->mapGroup)!=OBJECT_EVENTS_COUNT',
        'connection->direction<CONNECTION_SOUTH||connection->direction>CONNECTION_EAST',
        'caseCONNECTION_WEST:originX=-incoming->mapLayout->width;originY=connection->offset;break;',
        'caseCONNECTION_EAST:originX=gMapHeader.mapLayout->width;originY=connection->offset;break;',
        'caseCONNECTION_NORTH:originX=connection->offset;originY=-incoming->mapLayout->height;break;',
        'caseCONNECTION_SOUTH:originX=connection->offset;originY=gMapHeader.mapLayout->height;break;',
        'scenery=*original;scenery.x=x;scenery.y=y;',
        'x=original->x+originX;y=original->y+originY;',
        's16left=gSaveBlock1Ptr->pos.x-2;', 's16right=gSaveBlock1Ptr->pos.x+MAP_OFFSET_W+2;',
        's16top=gSaveBlock1Ptr->pos.y;', 's16bottom=gSaveBlock1Ptr->pos.y+MAP_OFFSET_H+2;',
        'if(x+MAP_OFFSET<left||x+MAP_OFFSET>right||y+MAP_OFFSET<top||y+MAP_OFFSET>bottom)continue;',
        'TrySpawnObjectEventTemplate(&scenery,connection->mapNum,connection->mapGroup,cameraX,cameraY);')
    for token in required:
        assert token in helper, ('Scenery spawn safety/identity/transform changed', token)
    restored = after[:start]+after[end:]
    call = 'JourneySpawnConnectedCoastScenery(cameraX, cameraY);'
    assert restored.count(call) == 1
    a, b = _function_span(restored, 'TrySpawnObjectEvents')
    assert call in restored[a:b], 'Scenery call left native spawn lifecycle'
    restored = restored.replace(call, '')
    assert re.sub(r'\s+', '', restored) == re.sub(r'\s+', '', before), 'Other event runtime changed'
    actors = [(name, index+1, obj) for name, mapping in current.maps.items()
              for index, obj in enumerate(mapping.get('object_events', []))
              if obj['graphics_id'] == SCENERY_GRAPHICS]
    assert len(actors) == 1
    name, local_id, actor = actors[0]
    assert (name, local_id, actor['x'], actor['y'], actor['elevation']) == ('OneIsland_Frlg', 4, 0, 7, 1)
    assert actor['movement_type'] == 'MOVEMENT_TYPE_FACE_DOWN'
    assert actor['movement_range_x'] == actor['movement_range_y'] == 0
    assert actor['trainer_type'] == 'TRAINER_TYPE_NONE' and actor['script'] == actor['flag'] == '0'
    assert current.word(name, 0, 7) == old.word(name, 0, 7), 'Scenery cliff was replaced'
    return dict(only_dedicated_scenery=True, original_identity_preserved=True,
                event_templates_unchanged=True, native_spawn_and_unload_preserved=True,
                cardinal_transforms_checked=4, map=name, local_id=local_id, cell=[0, 7])


def check_camera_runtime(current, old):
    before = _without_comments((old.source/CAMERA_PATH).read_text())
    after = _without_comments((current.source/CAMERA_PATH).read_text())
    include = '#include "tilesets.h"'
    condition = re.compile(r'\s*if\s*\(header->mapType\s*==\s*MAP_TYPE_OCEAN_ROUTE\s*'
        r'&&\s*header->mapLayout->primaryTileset\s*==\s*&gTileset_JourneySeviiSea\)\s*return TRUE;')
    assert after.count(include) == 1 and include not in before
    assert len(condition.findall(after)) == 1
    # The only new branch is inside the read-only drawing scope predicate.
    a = after.index('static bool8 JourneyMarineViewMap(')
    b = after.index('static u16 JourneyMarineTranslateBlock(', a)
    assert condition.search(after[a:b])
    restored = condition.sub('', after).replace(include, '')
    assert re.sub(r'\s+', '', restored) == re.sub(r'\s+', '', before), 'Other camera/movement runtime changed'
    return dict(dedicated_primary='gTileset_JourneySeviiSea', map_type='MAP_TYPE_OCEAN_ROUTE',
                visual_queries_only=True, collision_elevation_and_movement_code_unchanged=True,
                compatible_art_and_undefined_grid_rules_unchanged=True)


def check_geometry(current, old, names, original_words=None):
    assert current.maps == old.maps, 'Map metadata/events/connections changed'
    bank_alignment = check_layout_metadata(current, old)
    original_words = {} if original_words is None else original_words
    changes, replaced, covered, restored = [], {}, set(), []
    for name in names:
        layout = current.layout(name)
        assert (current.source/layout['border_filepath']).read_bytes() == (old.source/layout['border_filepath']).read_bytes(), ('Repeated border changed', name)
        width = layout['width']
        for at, (a, b) in enumerate(zip(old.grid(name), current.grid(name))):
            if a == b:
                continue
            x, y = at % width, at // width
            family = next((f for f in families(old, name) if a & 1023 in f), None)
            if family is not None:
                assert name in REPLACED_MAPS and b & 1023 == small(current, name), ('Unreviewed native reef altered', name, x, y)
                q = family.index(a & 1023)
                anchor = (name, x-q % 2, y-q // 2, family)
                replaced[anchor] = True
            elif a & 1023 == small(old, name) and (name, x, y) in original_words:
                donor, boundary_word = original_words[name, x, y]
                assert a == boundary_word and b & 1023 == donor & 1023, ('Restored art is not authenticated pre169 terrain', name, x, y)
                assert a & ~1023 == b & ~1023, ('Restored native edge changed collision/elevation', name, x, y)
                assert 0x1FA <= b & 1023 <= 0x27F, ('Unreviewed native edge donor family', name, x, y)
                restored.append(dict(map=name, cell=[x, y], before=a, after=b, native_pre169_word=donor))
            else:
                assert old.behavior(name, a) in old.water and not a & 0xC00 and a >> 12 == 1, ('Dry land/object/passability changed', name, x, y, hex(a))
                allowed = {small(current, name), *families(current, name)[0]}
                assert b & 1023 in allowed and b & 0xC00 == 0x400 and b >> 12 == 1, ('Incomplete/non-native corner reef', name, x, y, hex(b))
            changes.append(dict(map=name, cell=[x, y], before=a, after=b))
    objects = []
    for name, x, y, family in sorted(replaced):
        cells = [locate(old, name, x+dx, y+dy) for dy in range(2) for dx in range(2)]
        assert None not in cells and all(cell[0] == name for cell in cells)
        before, after = [old.word(*cell) for cell in cells], [current.word(*cell) for cell in cells]
        assert all(a & 1023 in (expected, small(old, name)) for a, expected in zip(before, family)), ('Unreviewed complete object footprint', name, x, y)
        assert all(b & 1023 == small(current, name) for b in after), ('Partial reef repair', name, x, y)
        assert all(a & ~1023 == b & ~1023 for a, b in zip(before, after)), ('Object collision/elevation changed', name, x, y)
        assert not covered.intersection(cells), ('Overlapping object footprints', name, x, y)
        covered.update(cells)
        objects.append(dict(map=name, anchor=[x, y], family=list(family),
                            before=before, after=after, whole_footprint=True))
    assert len(objects) >= 37, ('Incomplete reviewed reef footprint census', len(objects))
    changed_maps = sorted({row['map'] for row in changes})
    return (dict(maps=len(names), map_names=names, changed_maps=changed_maps,
                 changed_cells=len(changes), cells=changes, no_dry_land_changed=True,
                 all_map_metadata_unchanged=True, all_borders_unchanged=True,
                 bank_alignment=bank_alignment, only_reviewed_primary_banks_changed=True),
            dict(whole_replaced_objects=len(objects), objects=objects,
                 restored_native_edge_cells=restored,
                 native_edge_cells_authenticated_by_parent_marker=True,
                 all_collision_and_elevation_preserved=True,
                 all_cells_outside_reviewed_changes_unchanged=True))


def passable(inputs, name, x, y):
    word = inputs.word(name, x, y)
    return word >> 12 == 1 and not word & 0xC00 and inputs.behavior(name, word) in inputs.water


def components(inputs, name):
    layout = inputs.layout(name)
    width, height = layout['width'], layout['height']
    pending = {(x, y) for y in range(height) for x in range(width) if passable(inputs, name, x, y)}
    labels, sizes = {}, []
    while pending:
        cell = pending.pop()
        queue, size, label = deque([cell]), 0, len(sizes)
        labels[cell] = label
        while queue:
            x, y = queue.popleft()
            size += 1
            for adjacent in ((x-1, y), (x+1, y), (x, y-1), (x, y+1)):
                if adjacent in pending:
                    pending.remove(adjacent)
                    labels[adjacent] = label
                    queue.append(adjacent)
        sizes.append(size)
    return labels, sizes


def check_navigation(current, old, names, changed_maps):
    network = set(names)
    pending = list(names)
    while pending:
        for connection in current.maps[pending.pop()].get('connections') or []:
            if connection['direction'] not in {'up', 'down', 'left', 'right'}:
                continue
            target = current.by_id[connection['map']]
            if target not in network:
                network.add(target)
                pending.append(target)
    network = sorted(network)
    before, after, old_sizes, new_sizes = {}, {}, {}, {}
    for name in network:
        before[name], old_sizes[name] = components(old, name)
        after[name], new_sizes[name] = components(current, name)
        assert set(after[name]) <= set(before[name]), ('New Surf passage opened', name)
    def joined(inputs, labels, sizes):
        parent = {(name, label): (name, label) for name in network for label in range(len(sizes[name]))}
        def find(node):
            while parent[node] != node:
                parent[node] = parent[parent[node]]
                node = parent[node]
            return node
        for name in network:
            for x, y, direction, xx, yy in inputs.perimeter(name):
                target = inputs.target(name, direction, xx, yy)
                if target is None or target[0] not in labels:
                    continue
                other, tx, ty = target
                if (x, y) in labels[name] and (tx, ty) in labels[other]:
                    a, b = find((name, labels[name][x, y])), find((other, labels[other][tx, ty]))
                    parent[b] = a
        return {node: find(node) for node in parent}
    prior_roots, current_roots = joined(old, before, old_sizes), joined(current, after, new_sizes)
    survivors = {root: set() for root in prior_roots.values()}
    for name in network:
        for cell, label in before[name].items():
            if cell in after[name]:
                survivors[prior_roots[name, label]].add(current_roots[name, after[name][cell]])
    assert all(len(roots) == 1 for roots in survivors.values()), ('World Surf component split/removed', {k:v for k,v in survivors.items() if len(v) != 1})
    rows = [dict(map=name, before_component_sizes=old_sizes[name], after_component_sizes=new_sizes[name],
                 removed_water_cells=len(before[name])-len(after[name]),
                 retained_local_components=len(old_sizes[name])) for name in changed_maps]
    connections = []
    for name in network:
        old_openings, new_openings = Counter(), Counter()
        for x, y, direction, xx, yy in old.perimeter(name):
            target = old.target(name, direction, xx, yy)
            if target is None:
                continue
            key = direction, target[0]
            if passable(old, name, x, y) and passable(old, *target):
                old_openings[key] += 1
            if passable(current, name, x, y) and passable(current, *target):
                new_openings[key] += 1
        for (direction, target), count in sorted(old_openings.items()):
            assert new_openings[direction, target] > 0, ('Physical water connection closed', name, direction, target)
            connections.append(dict(map=name, direction=direction, target=target,
                                    before_openings=count, after_openings=new_openings[direction, target]))
    return dict(surf_components_preserved=True, no_new_surf_passages=True,
                all_existing_water_connections_open=True, component_maps=rows,
                network_maps=network, network_maps_checked=len(network),
                global_components_before=len(set(prior_roots.values())),
                global_components_after=len(set(current_roots.values())),
                all_surviving_cells_retain_global_connectivity=True,
                physical_connections=connections, physical_connections_checked=len(connections))


def compiled_bindings(source, inputs, names):
    values, _ = gps(source)
    layouts, runtime, projection, segments = previous_compiled_bindings(source, inputs, names, values)
    rom = (source/'pokeemerald.gba').read_bytes()
    table = symbols(source)
    address, size = table['TrySpawnObjectEvents']
    assert size > 0 and 0x08000000 <= address < address+size <= 0x0A000000
    raw = rom[address-0x08000000:address-0x08000000+size]
    assert len(raw) == size
    runtime.append(dict(symbol='TrySpawnObjectEvents', address=address, bytes=size,
                        sha256=hashlib.sha256(raw).hexdigest()))
    return layouts, runtime, projection, segments


def validate(source, baseline, output, preflight=False, gallery=False):
    from candidate_layer import Layer
    from prepare_coast_scenery_review import PRIOR, LAYER, stage_repairs, verify_parent
    source, baseline, output = map(Path, (source, baseline, output))
    assert source.resolve() != baseline.resolve()
    expected = verify_parent(baseline)
    marker = json.loads((source/('.journey-'+contract.SCOPE)).read_bytes())
    changes = marker['prepared_sha256']
    assert changes and marker['layer'] == LAYER and len(PRIOR) == 169
    assert marker['parent_rom_sha256'] == contract.PARENT_ROM_SHA256
    if not preflight or contract.PREPARED_SHA256:
        assert contract.PREPARED_SHA256 and changes == contract.PREPARED_SHA256, 'Pin the exact reviewed layer170 inputs'
    for name, sha in changes.items():
        safe_relative(name)
        assert sha != expected.get(name), ('No-op staged source file', name)
    for name, sha in (expected | changes).items():
        assert digest(source/name) == sha, ('Unchanged input or reviewed overlay differs', name)
    for name in ['.source-acquired.json', *['.journey-'+name for name in PRIOR]]:
        assert (source/name).read_bytes() == (baseline/name).read_bytes(), ('Historical marker changed', name)
    replay = Layer(baseline, LAYER, PRIOR)
    metadata = stage_repairs(replay)
    replay_hashes = {name: hashlib.sha256(raw).hexdigest() for name, raw in replay.outputs.items()}
    result = dict(layer=LAYER, **metadata, original_sha256=replay.originals, prepared_sha256=replay_hashes)
    assert json.loads(json.dumps(result)) == marker, 'Independent in-memory repair replay differs'
    assert set(replay.outputs) == set(changes)
    for name, raw in replay.outputs.items():
        assert (source/name).read_bytes() == raw, ('Replayed overlay output differs', name)
    current, old = Inputs(source), Inputs(baseline)
    names = marine_scope(current)
    block_paths = {current.layout(name)['blockdata_filepath'] for name in names}
    assert set(changes) <= block_paths | {SCENERY_PATH, CAMERA_PATH, 'data/layouts/layouts.json'}, ('Unreviewed source/binary/atlas/script input', sorted(set(changes)-block_paths-{SCENERY_PATH, CAMERA_PATH, 'data/layouts/layouts.json'}))
    assert SCENERY_PATH in changes
    for name in set(current.maps)-set(names):
        assert current.layout(name) == old.layout(name) and current.grid(name) == old.grid(name), ('Unrelated layout/terrain changed', name)
    original_words = parent_boundary_words(old)
    geometry, scenery = check_geometry(current, old, names, original_words)
    actor = check_scenery_runtime(current, old)
    camera_runtime = check_camera_runtime(current, old)
    census = check_boulders(current, old, names, original_words)
    before_corners, after_corners = graph_limitations(old), graph_limitations(current)
    assert after_corners['ambiguous_graph_cells'] == 0, ('Contradictory diagonal candidates remain', after_corners)
    corners = dict(before_ambiguous_cells=before_corners['ambiguous_graph_cells'],
                   after_ambiguous_cells=0, all_actual_candidates_agree=True,
                   map_names_before=before_corners['ambiguous_graph_maps'],
                   movement_boundaries_and_runtime_unchanged=True,
                   full_world_camera_certified=False)
    navigation = check_navigation(current, old, names, geometry['changed_maps'])
    assert gps(source) == gps(baseline), 'GPS/world projection changed'
    layouts, runtime, projection, segments = [], [], None, 0
    rom_sha = elf_sha = None
    if not preflight:
        layouts, runtime, projection, segments = compiled_bindings(source, current, names)
        rom_sha, elf_sha = digest(source/'pokeemerald.gba'), digest(source/'pokeemerald.elf')
        assert rom_sha != contract.PARENT_ROM_SHA256 and elf_sha != contract.PARENT_ELF_SHA256
    changed_and_actor = set(geometry['changed_maps']) | {actor['map']} | {r['map'] for r in geometry['bank_alignment']}
    reviewed_maps = sorted(changed_and_actor | {
        current.by_id[connection['map']] for name in changed_and_actor
        for connection in current.maps[name].get('connections') or []})
    captures = []
    if gallery:
        from PIL import Image, ImageDraw
        from render_sea_maps import MapRenderer
        for phase, target in (('before', baseline), ('after', source)):
            renderer = MapRenderer(target)
            directory = output.parent/'source-gallery'/phase
            directory.mkdir(parents=True, exist_ok=True)
            for name in reviewed_maps:
                rendered, _ = renderer.render(name, npcs=True)
                image = Image.new('RGB', (max(rendered.width, 480), rendered.height+38), '#15232c')
                image.paste(rendered, (0, 38))
                draw = ImageDraw.Draw(image)
                draw.text((6, 4), phase.upper()+' '+name, fill='white')
                draw.text((6, 20), 'Native asset source render with NPCs - not emulator capture', fill='#d6e6eb')
                path = directory/(name+'.png')
                image.save(path)
                captures.append(dict(file=path.relative_to(output.parent).as_posix(), sha256=digest(path), map=name,
                                     phase=phase, width_tiles=current.layout(name)['width'], height_tiles=current.layout(name)['height'],
                                     full_map=True, npcs=True, source_render_not_emulator=True, label_present=True))
    report = dict(kind='coast-scenery-review-source', passed=not preflight, preflight=bool(preflight),
                  compiled_rom=not preflight, independent_replay=True, layers=PRIOR+[LAYER],
                  parent_rom_sha256=contract.PARENT_ROM_SHA256, prepared_sha256=changes,
                  changed_files=sorted(changes), rom_sha256=rom_sha, elf_sha256=elf_sha,
                  source_hashes_checked=len(expected | changes), prefix_markers_unchanged=True,
                  unrelated_source_files_unchanged=True, scripts_and_atlas_art_unchanged=True,
                  geometry_audit=geometry, scenery_audit=scenery, permanent_scenery=actor,
                  camera_runtime=camera_runtime,
                  boulder_census=census, corner_audit=corners, surface_navigation=navigation,
                  compiled_layouts=layouts, compiled_runtime=runtime, compiled_gps=projection,
                  runtime_export_names=list(RUNTIME_SYMBOLS), elf_rom_load_segments_checked=segments,
                  reviewed_maps=reviewed_maps, captures=captures, source_gallery_rendered=bool(gallery),
                  source_gallery_not_emulator=True, full_campaign_playthrough=False)
    verify_parent(baseline)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--gallery', action='store_true')
    args = parser.parse_args()
    print(json.dumps(validate(args.source, args.baseline, args.output, args.preflight, args.gallery), indent=2))
