"""Keep Dewford's two bridge levels separate at every entrance and rail.

The original rail check only recognised elevation 4. A pedestrian could enter
the cable tiles from the adjacent elevation-3 beach, or from a transition-0
landing. Level 15 then retained 0, which disables native elevation collision
and lets the pedestrian walk onto the ocean. Keep ordinary beach tiles at 3;
only the two actual stair edges may connect the upper bridge to the beach.
"""
import json
import struct


def repair(layer):
    """Stage the narrowly scoped engine/data repair in a new candidate layer."""
    source = layer.source

    def raw(path):
        return layer.outputs[path] if path in layer.outputs else (source / path).read_bytes()

    harbor = json.loads(raw('.journey-dewford-island-harbor'))
    layouts = {row['id']: row for row in json.loads(raw('data/layouts/layouts.json'))['layouts']}
    route = json.loads(raw('data/maps/Route107/map.json'))
    layout = layouts[route['layout']]
    path = layout['blockdata_filepath']
    values = list(struct.unpack('<' + 'H' * (len(raw(path)) // 2), raw(path)))
    width = layout['width']
    assert (width, layout['height']) == (60, 20)
    landings = []
    for x, y in [(4, 15), (5, 16), (6, 16)]:
        index = y * width + x
        before = values[index]
        assert before >> 12 == 0 and not before & 0xC00, (x, y, hex(before))
        values[index] = (before & 0xFFF) | 0x3000
        landings.append(dict(position=[x, y], before=before, after=values[index]))
    for x in (5, 6):
        assert values[15 * width + x] >> 12 == 4
        assert values[3 * width + x] >> 12 == 4
    layer.stage(path, struct.pack('<' + 'H' * len(values), *values))

    bridge_ids = []
    for x, y in harbor['bridge']:
        block = values[y * width + x]
        assert block >> 12 == 15, (x, y, hex(block))
        bridge_ids.append(block & 1023)
    rails = harbor['bridge_rail_metatiles']
    assert len(bridge_ids) == 44 and len(rails) == 22
    assert set(rails) < set(bridge_ids)
    header = '''#ifndef GUARD_JOURNEY_DEWFORD_BRIDGE_H
#define GUARD_JOURNEY_DEWFORD_BRIDGE_H

static bool8 JourneyDewfordBridgeMap(void)
{
    return gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(MAP_ROUTE107)
        && gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_ROUTE107);
}

static bool8 JourneyDewfordBridgeLowerObject(const struct ObjectEvent *object)
{
    // A pedestrian must not be mistaken for a vessel after a saved transition.
    // NPC vessels retain their native level; the player has an explicit state.
    if (object->isPlayer)
        return (gPlayerAvatar.flags & PLAYER_AVATAR_FLAG_SURFING) != 0;
    return object->currentElevation == 1;
}

static bool8 JourneyDewfordBridgeRailBlocks(const struct ObjectEvent *object, s16 x, s16 y)
{
    static const u16 rails[] = {RAIL_IDS};
    u32 i;
    u16 metatile;
    if (!JourneyDewfordBridgeMap() || JourneyDewfordBridgeLowerObject(object))
        return FALSE;
    metatile = MapGridGetMetatileIdAt(x, y);
    for (i = 0; i < ARRAY_COUNT(rails); i++)
        if (metatile == rails[i])
            return TRUE;
    return FALSE;
}

static bool8 JourneyDewfordBridgeStairConnects(const struct ObjectEvent *object, s16 x, s16 y)
{
    s16 sourceX = object->currentCoords.x - MAP_OFFSET;
    s16 sourceY = object->currentCoords.y - MAP_OFFSET;
    s16 targetX = x - MAP_OFFSET;
    s16 targetY = y - MAP_OFFSET;
    if (!JourneyDewfordBridgeMap() || JourneyDewfordBridgeLowerObject(object)
        || sourceX != targetX || (sourceX != 5 && sourceX != 6))
        return FALSE;
    // Precisely the two south stair edges: no lateral or water exemption.
    return (sourceY == 16 && targetY == 15
            && object->currentElevation == ELEVATION_DEFAULT
            && MapGridGetElevationAt(x, y) == 4)
        || (sourceY == 15 && targetY == 16
            && object->currentElevation == 4
            && MapGridGetElevationAt(x, y) == ELEVATION_DEFAULT);
}

static void JourneyDewfordBridgeRestoreLevel(struct ObjectEvent *object)
{
    static const u16 bridge[] = {BRIDGE_IDS};
    u32 i;
    u16 metatile;
    if (!JourneyDewfordBridgeMap())
        return;
    metatile = MapGridGetMetatileIdAt(object->currentCoords.x, object->currentCoords.y);
    for (i = 0; i < ARRAY_COUNT(bridge); i++)
        if (metatile == bridge[i])
        {
            // Native multi-level tiles retain their entering level. Explicitly
            // restore that level when loading a save on this custom bridge too.
            object->currentElevation = JourneyDewfordBridgeLowerObject(object) ? 1 : 4;
            object->previousElevation = object->currentElevation;
            return;
        }
}
#endif
'''.replace('RAIL_IDS', ', '.join(hex(mid) for mid in rails)).replace(
        'BRIDGE_IDS', ', '.join(hex(mid) for mid in bridge_ids))
    assert header.startswith('#ifndef GUARD_JOURNEY_DEWFORD_BRIDGE_H\n')
    layer.stage('include/journey_dewford_bridge.h', header)

    path = 'src/event_object_movement.c'
    text = raw(path).decode()
    # Native Surf/disembark checks still receive their elevation mismatch.
    # The only new exception is the physical 3-to-4 stair edge above.
    before = 'else if (IsElevationMismatchAt(objectEvent->currentElevation, x, y))\n        return COLLISION_ELEVATION_MISMATCH;'
    after = 'else if (IsElevationMismatchAt(objectEvent->currentElevation, x, y)\n        && !JourneyDewfordBridgeStairConnects(objectEvent, x, y))\n        return COLLISION_ELEVATION_MISMATCH;'
    assert text.count(before) == 1
    text = text.replace(before, after)
    # Trainer/NPC path probes use this second collision interface too.
    anchor = 'u8 GetCollisionFlagsAtCoords(struct ObjectEvent *objectEvent, s16 x, s16 y, enum Direction direction)\n{'
    start = text.index(anchor)
    end = text.index('\nstatic bool8 IsCoordOutsideObjectEventMovementRange', start)
    chunk = text[start:end]
    before = 'if (MapGridGetCollisionAt(x, y) || '
    assert chunk.count(before) == 1
    chunk = chunk.replace(before, 'if (JourneyDewfordBridgeRailBlocks(objectEvent, x, y) || MapGridGetCollisionAt(x, y) || ')
    before = 'if (IsElevationMismatchAt(objectEvent->currentElevation, x, y))'
    assert chunk.count(before) == 1
    chunk = chunk.replace(before, 'if (IsElevationMismatchAt(objectEvent->currentElevation, x, y)\n        && !JourneyDewfordBridgeStairConnects(objectEvent, x, y))')
    text = text[:start] + chunk + text[end:]
    before = '    u8 prevElevation = MapGridGetElevationAt(objEvent->previousCoords.x, objEvent->previousCoords.y);\n\n    if (curElevation == ELEVATION_MULTI_LEVEL'
    after = '    u8 prevElevation = MapGridGetElevationAt(objEvent->previousCoords.x, objEvent->previousCoords.y);\n\n    JourneyDewfordBridgeRestoreLevel(objEvent);\n    if (curElevation == ELEVATION_MULTI_LEVEL'
    assert text.count(before) == 1
    text = text.replace(before, after)
    layer.stage(path, text)
    return dict(transition_sand_normalized=landings,
                southern_stair_edges=[[[x, 16], [x, 15]] for x in (5, 6)],
                southern_stair_foot_elevation=3, upper_elevation=4, lower_elevation=1,
                rail_metatiles=rails, bridge_metatiles=bridge_ids,
                rails_block_every_non_surf_level=True,
                npc_collision_flags_match_player_collision=True,
                saved_bridge_level_restored_from_player_state=True,
                native_surf_and_disembark_mismatch_preserved=True,
                rule_limited_to_route107_custom_bridge=True,
                north_stairs_and_island_elevation_4_preserved=True)
