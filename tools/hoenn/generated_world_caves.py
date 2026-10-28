"""Keep saves made in the seven retired Sevii lodges able to leave.

The lodges no longer have incoming doors after the terminal integration, but
their map IDs must survive for old saves. Their exits must use the same valid
outdoor landing as the corresponding current terminal, rather than warp 1 of
a coastal route whose warp table is now empty. No terrain or atlas changes.
"""
import copy
import hashlib
import json
import struct
from collections import deque

from badge_story_layer import read


RETURNS = {
    'One': ('MAP_ONE_ISLAND_TREASURE_BEACH', '0'),
    'Two': ('MAP_TWO_ISLAND', '3'),
    'Three': ('MAP_THREE_ISLAND_PORT', '2'),
    'Four': ('MAP_FOUR_ISLAND', '6'),
    'Five': ('MAP_FIVE_ISLAND', '0'),
    'Six': ('MAP_SIX_ISLAND', '0'),
    'Seven': ('MAP_SEVEN_ISLAND', '3'),
}


def repair_lodges(layer):
    maps = {}
    for path in sorted((layer.source / 'data/maps').glob('*/map.json')):
        relative = path.relative_to(layer.source).as_posix()
        mapping = json.loads(read(layer, relative))
        maps[mapping['id']] = mapping
    records = []
    for island, (destination, index) in RETURNS.items():
        name = f'Journey{island}IslandHarborPortLodge'
        path = f'data/maps/{name}/map.json'
        before_raw = read(layer, path)
        before = json.loads(before_raw)
        after = copy.deepcopy(before)
        assert len(after['warp_events']) == 1, name
        warp = after['warp_events'][0]
        assert (warp['x'], warp['y'], warp['elevation']) == (4, 7, 3), name
        old = (f'MAP_{island.upper()}_ISLAND_HARBOR', '1')
        current = (warp['dest_map'], str(warp['dest_warp_id']))
        assert current in (old, (destination, index)), (name, current)
        assert not maps[old[0]]['warp_events'], old
        terminal_path = f'data/maps/JourneySevii{island}Harbor/map.json'
        terminal = json.loads(read(layer, terminal_path))
        assert all((w['dest_map'], str(w['dest_warp_id'])) == (destination, index)
                   for w in terminal['warp_events']), island
        endpoint = maps[destination]['warp_events'][int(index)]
        assert endpoint['dest_map'] == terminal['id'], (island, endpoint)
        warp.update(dest_map=destination, dest_warp_id=index)
        # Only the two destination fields change; retain old map IDs, scripts,
        # objects, elevations, doorway artwork and all room geometry.
        expected = copy.deepcopy(before)
        expected['warp_events'][0].update(dest_map=destination, dest_warp_id=index)
        assert after == expected
        if after != before:
            layer.stage(path, (json.dumps(after, indent=2) + '\n').encode())
        records.append(dict(map=name, old_destination=list(old),
                            destination=[destination, int(index)],
                            landing=[endpoint['x'], endpoint['y']],
                            current_terminal=terminal['id'],
                            before_sha256=hashlib.sha256(before_raw).hexdigest(),
                            after_sha256=hashlib.sha256(read(layer, path)).hexdigest(),
                            terrain_events_and_map_ids_preserved=True))
    return dict(kind='retired-sevii-lodge-save-compatibility', maps=records,
                atlas_and_all_blockdata_unchanged=True)


def _floor_component(values, width, start):
    free = {(i % width, i // width) for i, word in enumerate(values)
            if word & 0xC00 == 0}
    assert start in free
    visited, queue = {start}, deque([start])
    while queue:
        x, y = queue.popleft()
        for point in ((x-1,y), (x+1,y), (x,y-1), (x,y+1)):
            if point in free and point not in visited:
                visited.add(point)
                queue.append(point)
    return visited


def repair_rocket_objects(layer):
    """Replace seven stray desk corners with three complete native desks."""
    layouts = {row['id']: row for row in json.loads(
        read(layer, 'data/layouts/layouts.json'))['layouts']}
    donor_name = 'SlateportCity_SternsShipyard_1F'
    donor = json.loads(read(layer, f'data/maps/{donor_name}/map.json'))
    dl = layouts[donor['layout']]
    donor_values = struct.unpack('<' + 'H' * (dl['width'] * dl['height']),
                                 read(layer, dl['blockdata_filepath']))
    desk = [[donor_values[y * dl['width'] + x] for x in range(2)]
            for y in range(4, 6)]
    assert desk == [[0x3241, 0x3242], [0x0649, 0x064A]], desk
    records = []
    for floor in (1, 2):
        name = f'JourneyRocketBaseB{floor}F'
        mapping = json.loads(read(layer, f'data/maps/{name}/map.json'))
        layout = layouts[mapping['layout']]
        assert layout['primary_tileset'] == dl['primary_tileset'] == 'gTileset_General'
        assert layout['secondary_tileset'] == dl['secondary_tileset'] == 'gTileset_Facility'
        width, height = layout['width'], layout['height']
        raw = read(layer, layout['blockdata_filepath'])
        before = list(struct.unpack('<' + 'H' * (width * height), raw))
        after = before.copy()
        old_cells = {(10, y) for y in (5, 6, 7, 10, 11, 13, 14)}
        new_cells = {(10+dx, y+dy): value
                     for y in (4, 10, 13)
                     for dy, row in enumerate(desk)
                     for dx, value in enumerate(row)}
        footprint = old_cells | new_cells.keys()
        expected_broken = {point: 0x064A if point in old_cells else 0x3228
                           for point in footprint}
        expected_fixed = {point: new_cells.get(point, 0x3228) for point in footprint}
        observed = {point: before[point[1]*width+point[0]] for point in footprint}
        assert observed in (expected_broken, expected_fixed), (name, observed)
        for (x, y), value in expected_fixed.items():
            after[y*width+x] = value
        start = (3, 4)
        before_free = _floor_component(before, width, start)
        after_free = _floor_component(after, width, start)
        assert before_free - footprint <= after_free, name
        for group in ('object_events', 'warp_events', 'coord_events', 'bg_events'):
            for event in mapping[group]:
                point = event['x'], event['y']
                assert point not in footprint, (name, group, point)
                if group == 'object_events':
                    x, y = point
                    assert any(p in after_free for p in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))), (name, point)
        changed = [[i % width, i // width, a, b] for i, (a, b)
                   in enumerate(zip(before, after)) if a != b]
        if changed:
            layer.stage(layout['blockdata_filepath'], struct.pack('<'+'H'*len(after), *after))
        records.append(dict(map=name, donor_map=donor_name,
                            donor_bounds=[0, 4, 2, 6], complete_desks=3,
                            former_stray_corner_cells=7, changed_cells=changed,
                            doors_and_npc_positions_preserved=True,
                            useful_floor_and_all_npc_approaches_remain_connected=True))
    return dict(kind='complete-native-rocket-desks', maps=records,
                donor_words=desk)


def repair(layer):
    return dict(retired_lodges=repair_lodges(layer),
                rocket_objects=repair_rocket_objects(layer),
                paradox_entrances=repair_paradox_entrances(layer))


def repair_paradox_entrances(layer):
    """Restore the native south cliff and put complete ladders on open floor.

    The old generator read a blocked ladder *top* as its corridor floor,
    repeating that fragment fifteen times. Both new stair warps were stranded
    below it. The native one-cell downward ladder is a complete object in the
    same NavelRock bank; use it inside the room and retain the warp IDs.
    """
    layouts = {row['id']: row for row in json.loads(
        read(layer, 'data/layouts/layouts.json'))['layouts']}
    name = 'JourneySanctuaryDimensoes'
    path = f'data/maps/{name}/map.json'
    before_mapping = json.loads(read(layer, path))
    mapping = copy.deepcopy(before_mapping)
    layout = layouts[mapping['layout']]
    width, height = layout['width'], layout['height']
    assert (width, height) == (22, 22)
    donor = json.loads(read(layer, 'data/maps/NavelRock_Bottom/map.json'))
    dl = layouts[donor['layout']]
    assert all(layout[key] == dl[key] for key in ('primary_tileset','secondary_tileset','layout_version'))
    native = struct.unpack('<'+'H'*(width*height), read(layer, dl['blockdata_filepath']))
    raw = read(layer, layout['blockdata_filepath'])
    before = list(struct.unpack('<'+'H'*(width*height), raw))
    after = before.copy()
    # Restore the exact native, complete southern rock/ladder composition.
    restored = [(x,18) for x in range(4,19)] + [(4,19),(18,19)]
    for x,y in restored:
        assert before[y*width+x] in (native[y*width+x], 0x0783, 0x0364, 0x038B), (x,y)
        after[y*width+x] = native[y*width+x]
    floor_donor = json.loads(read(layer, 'data/maps/NavelRock_Down09/map.json'))
    fl = layouts[floor_donor['layout']]
    assert all(layout[key] == fl[key] for key in ('primary_tileset','secondary_tileset','layout_version'))
    fv = struct.unpack('<'+'H'*(fl['width']*fl['height']), read(layer, fl['blockdata_filepath']))
    ladder = fv[5*fl['width']+5]
    assert ladder == 0x323F
    portals = []
    for index, old_x, new_x, target in (
            (1,4,7,'MAP_JOURNEYPARADOXPAST'),
            (2,18,15,'MAP_JOURNEYPARADOXFUTURE')):
        warp = mapping['warp_events'][index]
        assert warp['dest_map'] == target and warp['dest_warp_id'] == '0'
        assert (warp['x'],warp['y']) in ((old_x,19),(new_x,15)), warp
        warp.update(x=new_x,y=15,elevation=0)
        assert before[15*width+new_x] in (0x0364,ladder)
        after[15*width+new_x] = ladder
        portals.append(dict(warp_id=index, old_position=[old_x,19],
                            position=[new_x,15], destination=target))
    footprint = set(restored) | {(7,15),(15,15)}
    for group in ('object_events','coord_events','bg_events'):
        assert not any((e['x'],e['y']) in footprint for e in mapping[group]), group
    component = _floor_component(after,width,(14,17))
    assert all(tuple(p['position']) in component for p in portals)
    assert (14,19) in component
    for obj in mapping['object_events']:
        x,y = obj['x'],obj['y']
        assert any(p in component for p in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))), obj
    changed = [[i%width,i//width,a,b] for i,(a,b) in enumerate(zip(before,after)) if a!=b]
    if changed:
        layer.stage(layout['blockdata_filepath'],struct.pack('<'+'H'*len(after),*after))
    if mapping != before_mapping:
        layer.stage(path,(json.dumps(mapping,indent=2)+'\n').encode())
    return dict(map=name, portals=portals, changed_cells=changed,
                south_cliff_and_original_exit_restored_from='NavelRock_Bottom',
                complete_single_cell_ladder_donor=dict(map='NavelRock_Down09',position=[5,5],block=ladder),
                original_exit_and_all_npc_approaches_connected=True,
                original_warp_ids_and_other_maps_preserved=True)
