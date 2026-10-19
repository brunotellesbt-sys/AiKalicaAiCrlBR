"""Extend Sevii's seven ferry approaches and keep Surf out of low wooden piers.

The tall Route107 bridge deliberately remains a two-level crossing. These
low Sevii docks are different: their boards sit immediately above the sea,
and a surfer entering beneath them is hidden by the foreground planks.
"""
import copy
import json
import struct

from extra_gym_landscape import OBSOLETE_FERRIES


def repair(layer):
    """Stage changes only; the caller owns the final atomic layer commit."""
    source = layer.source
    touched = set()

    def raw(path):
        return layer.outputs[path] if path in layer.outputs else (source / path).read_bytes()

    def read_json(path):
        return json.loads(raw(path))

    def stage(path, value):
        layer.stage(path, value)
        touched.add(path)

    def stage_json(path, value):
        stage(path, json.dumps(value, indent=2) + '\n')

    layouts = {row['id']: row for row in read_json('data/layouts/layouts.json')['layouts']}
    map_data, original_maps, grids = {}, {}, {}

    def load(name):
        if name not in map_data:
            data = read_json(f'data/maps/{name}/map.json')
            layout = layouts[data['layout']]
            blob = raw(layout['blockdata_filepath'])
            map_data[name] = data
            original_maps[name] = copy.deepcopy(data)
            grids[name] = (layout, list(struct.unpack('<' + 'H' * (len(blob) // 2), blob)))
        return map_data[name]

    def patch(name, x, y, value, changes):
        load(name)
        layout, values = grids[name]
        assert 0 <= x < layout['width'] and 0 <= y < layout['height'], (name, x, y)
        index = y * layout['width'] + x
        before = values[index]
        if before != value:
            changes.append(dict(map=name, position=[x, y], before=before, after=value))
            values[index] = value

    def stage_grid(name):
        layout, values = grids[name]
        stage(layout['blockdata_filepath'], struct.pack('<' + 'H' * len(values), *values))

    town_bridges, rectangles = [], []
    # Native GeneralFRLG boards have coherent left/middle/right edges. The
    # actual ferry arrow triplet appears once, at the new end of each deck.
    boards = [0x31C5, 0x31C6, 0x31C7]
    for ferry in OBSOLETE_FERRIES:
        island, town = ferry['island'], ferry['town']
        harbor = island + 'Island_Harbor_Frlg'
        before_town, before_harbor = copy.deepcopy(load(town)), copy.deepcopy(load(harbor))
        rx, ry = ferry['ramp']
        layout, values = grids[town]
        endpoint = list(values[ry * layout['width'] + rx - 1:ry * layout['width'] + rx + 2])
        assert all(value >> 12 == 3 and not value & 0xC00 for value in endpoint), (town, endpoint)
        assert before_town['warp_events'][ferry['ramp_warp']]['elevation'] == 3
        segments, changes = [], []
        if island == 'One':
            beach = 'OneIsland_TreasureBeach_Frlg'
            before_beach = copy.deepcopy(load(beach))
            assert len(before_town['warp_events']) == 4 and ferry['ramp_warp'] == 3
            assert not before_beach['warp_events']
            assert any(c['direction'] == 'down' and c['map'] == before_beach['id']
                       and c['offset'] == 0 for c in before_town['connections'])
            segments = [(town, rx - 1, ry, 3, layout['height'] - ry), (beach, rx - 1, 0, 3, 4)]
            end_map, ex, ey, outward_id = beach, rx, 3, 0
            outward = map_data[town]['warp_events'].pop()
            outward.update(x=ex, y=ey, elevation=3)
            map_data[beach]['warp_events'].append(outward)
            map_data[harbor]['warp_events'][0].update(dest_map=map_data[beach]['id'], dest_warp_id='0')
            # The removed warp was last: every other One Island door retains
            # its numeric ID. Only the main harbor referred to this ferry.
            references = []
            for path in sorted((source / 'data/maps').glob('*/map.json')):
                other_name = path.parent.name
                other = read_json(path.relative_to(source).as_posix())
                for wid, warp in enumerate(other.get('warp_events', [])):
                    if warp['dest_map'] == before_town['id'] and str(warp['dest_warp_id']) == '3':
                        references.append([other_name, wid])
            assert references == [[harbor, 0]], references
            stage_json(f'data/maps/{beach}/map.json', map_data[beach])
            stage_json(f'data/maps/{harbor}/map.json', map_data[harbor])
            assert map_data[beach]['object_events'] == before_beach['object_events']
        else:
            ey = ferry['roof'][1] + ferry['roof'][3] - 1
            end_map, ex, outward_id = town, rx, ferry['ramp_warp']
            segments = [(town, rx - 1, ry, 3, ey - ry + 1)]
            map_data[town]['warp_events'][outward_id].update(x=ex, y=ey, elevation=3)
        for name, x, y, w, h in segments:
            for yy in range(y, y + h):
                row = endpoint if name == end_map and yy == ey else boards
                for dx, value in enumerate(row):
                    patch(name, x + dx, yy, value, changes)
            rectangles.append(dict(map=name, map_id=load(name)['id'], bounds=[x, y, x + w - 1, y + h - 1], kind='town_bridge'))
            stage_grid(name)
        stage_json(f'data/maps/{town}/map.json', map_data[town])
        assert map_data[town]['object_events'] == before_town['object_events']
        assert map_data[town].get('connections') == before_town.get('connections')
        row = dict(island=island, town=town, harbor=harbor, start=[town, rx, ry - 1],
                   old_ramp=[rx, ry], end=[end_map, ex, ey], endpoint_warp_id=outward_id,
                   deck_segments=[dict(map=n, footprint=[x, y, w, h]) for n, x, y, w, h in segments],
                   changed_cells=changes, width=3, foot_elevation=3, native_board_metatiles=boards,
                   endpoint_metatiles=endpoint, warp_before=before_town['warp_events'][ferry['ramp_warp']],
                   warp_after=copy.deepcopy(map_data[end_map]['warp_events'][outward_id]),
                   return_warp_before=before_harbor['warp_events'][0],
                   return_warp_after=copy.deepcopy(map_data[harbor]['warp_events'][0]),
                   objects_and_surface_connections_preserved=True,
                   old_roof_not_reintroduced=True, one_beach_ferry_transfer=island == 'One')
        if island == 'One':
            row['removed_last_town_warp_id'] = 3
            row['new_beach_warp_id'] = 0
            row['beach_before_warps'] = before_beach['warp_events']
            row['beach_after_warps'] = copy.deepcopy(map_data[beach]['warp_events'])
        town_bridges.append(row)

    low_piers = []
    for port in read_json('.journey-sevii-harbors')['ports']:
        name, px = port['exterior'], port['pier_x']
        data = load(name)
        bounds = [[7, 3, 9, 6], [10, 6, 16, 6], [7, 7, 16, 7], [px, 8, px + 1, 10]]
        cells = sorted({(x, y) for x1, y1, x2, y2 in bounds
                        for y in range(y1, y2 + 1) for x in range(x1, x2 + 1)})
        layout, values = grids[name]
        assert len(cells) == 35
        assert all(values[y * layout['width'] + x] >> 12 in (3, 15)
                   and not values[y * layout['width'] + x] & 0xC00 for x, y in cells)
        for box in bounds:
            rectangles.append(dict(map=name, map_id=data['id'], bounds=box, kind='main_harbor_low_pier'))
        low_piers.append(dict(island=port['island'], map=name, map_id=data['id'], pier_x=px,
                              rectangles=bounds, blocked_cells=[list(p) for p in cells],
                              low_wood_only=True, original_tiles_and_events_preserved=True,
                              surface_connections=copy.deepcopy(data.get('connections'))))

    records = '\n'.join('    {MAP_GROUP(%s), MAP_NUM(%s), %d, %d, %d, %d},' %
                        (r['map_id'], r['map_id'], *r['bounds']) for r in rectangles)
    header = '''#ifndef GUARD_JOURNEY_COASTAL_PIERS_H
#define GUARD_JOURNEY_COASTAL_PIERS_H

struct JourneyLowPierRect
{
    u8 group, num;
    s16 left, top, right, bottom;
};

static bool8 JourneyLowPierAt(s16 gridX, s16 gridY)
{
    static const struct JourneyLowPierRect rects[] = {
RECTANGLES
    };
    u8 group = gSaveBlock1Ptr->location.mapGroup;
    u8 num = gSaveBlock1Ptr->location.mapNum;
    s16 x = gridX - MAP_OFFSET;
    s16 y = gridY - MAP_OFFSET;
    const struct MapConnection *connection;
    const struct MapHeader *incoming;
    u32 i;
    // Resolve the destination while the actor is still on the old map. In
    // particular, a low dock on the east seam must not admit a side entry.
    if (x < 0 || y < 0 || x >= gMapHeader.mapLayout->width || y >= gMapHeader.mapLayout->height)
    {
        connection = GetMapConnectionAtPos(gridX, gridY);
        if (connection == NULL)
            return FALSE;
        incoming = GetMapHeaderFromConnection(connection);
        group = connection->mapGroup;
        num = connection->mapNum;
        switch (connection->direction)
        {
        case CONNECTION_EAST:
            x -= gMapHeader.mapLayout->width;
            y -= connection->offset;
            break;
        case CONNECTION_WEST:
            x += incoming->mapLayout->width;
            y -= connection->offset;
            break;
        case CONNECTION_SOUTH:
            x -= connection->offset;
            y -= gMapHeader.mapLayout->height;
            break;
        case CONNECTION_NORTH:
            x -= connection->offset;
            y += incoming->mapLayout->height;
            break;
        default:
            return FALSE;
        }
    }
    for (i = 0; i < ARRAY_COUNT(rects); i++)
        if (group == rects[i].group && num == rects[i].num
            && x >= rects[i].left && x <= rects[i].right
            && y >= rects[i].top && y <= rects[i].bottom)
            return TRUE;
    return FALSE;
}

static bool8 JourneyLowPierBlocks(const struct ObjectEvent *object, s16 x, s16 y)
{
    bool8 lower = object->isPlayer
        ? (gPlayerAvatar.flags & PLAYER_AVATAR_FLAG_SURFING) != 0
        : object->currentElevation == 1;
    if (!lower || !JourneyLowPierAt(x, y))
        return FALSE;
    // A save made underneath an old dock may leave it using ordinary input.
    // New entries are blocked; no position or elevation is silently written.
    return !JourneyLowPierAt(object->currentCoords.x, object->currentCoords.y);
}
#endif
'''.replace('RECTANGLES', records)
    stage('include/journey_coastal_piers.h', header)
    path = 'src/event_object_movement.c'
    text = raw(path).decode()
    anchor = '#include "journey_dewford_bridge.h"\n'
    assert text.count(anchor) == 1
    text = text.replace(anchor, anchor + '#include "journey_coastal_piers.h"\n')
    before = 'if (JourneyDewfordBridgeRailBlocks(objectEvent, x, y))'
    assert text.count(before) == 1
    text = text.replace(before, 'if (JourneyLowPierBlocks(objectEvent, x, y) || JourneyDewfordBridgeRailBlocks(objectEvent, x, y))')
    before = 'if (JourneyDewfordBridgeRailBlocks(objectEvent, x, y) || MapGridGetCollisionAt(x, y) || '
    assert text.count(before) == 1
    text = text.replace(before, 'if (JourneyLowPierBlocks(objectEvent, x, y) || JourneyDewfordBridgeRailBlocks(objectEvent, x, y) || MapGridGetCollisionAt(x, y) || ')
    stage(path, text)
    source_edits = []
    for name, data in map_data.items():
        map_path = f'data/maps/{name}/map.json'
        block_path = grids[name][0]['blockdata_filepath']
        if map_path not in touched and block_path not in touched:
            continue
        source_edits.append(dict(map=name, map_path=map_path, block_path=block_path,
                                 map_changed=map_path in touched, blocks_changed=block_path in touched,
                                 changed_cells=[c for row in town_bridges for c in row['changed_cells'] if c['map'] == name],
                                 warps_before=original_maps[name]['warp_events'],
                                 warps_after=copy.deepcopy(data['warp_events'])))
    return dict(town_bridges=town_bridges, low_piers=low_piers, collision_rectangles=rectangles,
                source_edits=source_edits,
                changed_paths=sorted(touched), collision_header='include/journey_coastal_piers.h',
                low_piers_block_surf_entry=True, saved_surfer_can_leave_old_underpass=True,
                connection_destination_resolved_before_crossing=True,
                npc_and_player_collision_interfaces_match=True,
                no_player_coordinate_or_elevation_writes=True,
                route107_high_bridge_unchanged=True, all_seven_surface_seams_preserved=True,
                native_tilesets_and_palettes_unchanged=True)
