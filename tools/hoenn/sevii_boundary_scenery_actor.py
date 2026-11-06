"""Show the dedicated permanent coastal scenery from a connected map camera.

The rock overlays a complete animated-water/cliff metatile. Keep that native
artwork and its object identity; only let its original stationary template
enter the neighboring camera through the normal object spawn/unload lifecycle.
"""
import hashlib
import json

from badge_story_layer import read

PATH = 'src/event_object_movement.c'
GRAPHICS = 'OBJ_EVENT_GFX_JOURNEY_COAST_BOUNDARY_ROCK'

C_HELPER = r'''
// This dedicated permanent scenery overlays a complete cliff metatile. Its
// original identity must already be visible in a connected map's camera;
// ordinary actors and interactive obstacle templates keep their native rules.
static void JourneySpawnConnectedCoastScenery(s16 cameraX, s16 cameraY)
{
    s32 i;
    s16 left = gSaveBlock1Ptr->pos.x - 2;
    s16 right = gSaveBlock1Ptr->pos.x + MAP_OFFSET_W + 2;
    s16 top = gSaveBlock1Ptr->pos.y;
    s16 bottom = gSaveBlock1Ptr->pos.y + MAP_OFFSET_H + 2;

    if (gMapHeader.connections == NULL)
        return;
    for (i = 0; i < gMapHeader.connections->count; i++)
    {
        const struct MapConnection *connection = &gMapHeader.connections->connections[i];
        const struct MapHeader *incoming;
        s32 originX = 0;
        s32 originY = 0;
        u32 j;

        if (connection->direction < CONNECTION_SOUTH || connection->direction > CONNECTION_EAST)
            continue;
        incoming = GetMapHeaderFromConnection(connection);
        if (incoming == NULL || incoming->events == NULL)
            continue;
        switch (connection->direction)
        {
        case CONNECTION_WEST:
            originX = -incoming->mapLayout->width;
            originY = connection->offset;
            break;
        case CONNECTION_EAST:
            originX = gMapHeader.mapLayout->width;
            originY = connection->offset;
            break;
        case CONNECTION_NORTH:
            originX = connection->offset;
            originY = -incoming->mapLayout->height;
            break;
        case CONNECTION_SOUTH:
            originX = connection->offset;
            originY = gMapHeader.mapLayout->height;
            break;
        }
        for (j = 0; j < incoming->events->objectEventCount; j++)
        {
            const struct ObjectEventTemplate *original = &incoming->events->objectEvents[j];
            struct ObjectEventTemplate scenery;
            s32 x, y;

            if (original->graphicsId != OBJ_EVENT_GFX_JOURNEY_COAST_BOUNDARY_ROCK
                || FlagGet(original->flagId)
                || GetObjectEventIdByLocalIdAndMap(original->localId, connection->mapNum,
                    connection->mapGroup) != OBJECT_EVENTS_COUNT)
                continue;
            x = original->x + originX;
            y = original->y + originY;
            if (x + MAP_OFFSET < left || x + MAP_OFFSET > right
                || y + MAP_OFFSET < top || y + MAP_OFFSET > bottom)
                continue;
            scenery = *original;
            scenery.x = x;
            scenery.y = y;
            TrySpawnObjectEventTemplate(&scenery, connection->mapNum, connection->mapGroup,
                cameraX, cameraY);
        }
    }
}
'''


def repair(layer):
    """Stage the narrow spawn change without touching templates, IDs or tiles."""
    mapping = json.loads(read(layer, 'data/maps/OneIsland_Frlg/map.json'))
    objects = mapping['object_events']
    indices = [i for i, obj in enumerate(objects) if obj['graphics_id'] == GRAPHICS]
    assert indices == [3], ('Unexpected permanent scenery template', indices)
    rock = objects[3]
    assert [rock['x'], rock['y'], rock['elevation']] == [0, 7, 1]
    assert rock['movement_type'] == 'MOVEMENT_TYPE_FACE_DOWN'
    assert rock['movement_range_x'] == rock['movement_range_y'] == 0
    assert rock['trainer_type'] == 'TRAINER_TYPE_NONE' and rock['script'] == rock['flag'] == '0'
    before = read(layer, PATH).decode()
    anchor = 'void TrySpawnObjectEvents(s16 cameraX, s16 cameraY)\n'
    tail = '\n}\n\nvoid RemoveObjectEventsOutsideView(void)'
    assert before.count(anchor) == before.count(tail) == 1
    assert 'JourneySpawnConnectedCoastScenery' not in before
    after = before.replace(anchor, C_HELPER+'\n'+anchor)
    after = after.replace(tail, '\n    JourneySpawnConnectedCoastScenery(cameraX, cameraY);'+tail)
    assert after.replace(C_HELPER+'\n', '').replace(
        '\n    JourneySpawnConnectedCoastScenery(cameraX, cameraY);', '') == before
    layer.stage(PATH, after)
    return dict(kind='connected-permanent-coast-scenery', map='OneIsland_Frlg',
        cell=[0, 7], local_id=4, graphics=GRAPHICS,
        original_map_identity_and_template_unchanged=True,
        original_cliff_water_metatile_and_collision_unchanged=True,
        object_flag_respected=True, only_dedicated_scenery_graphics_accepted=True,
        cardinal_neighbor_coordinates_transformed=True,
        duplicate_identity_checked_before_spawn=True,
        native_spawn_view_range_and_unload_preserved=True,
        existing_current_map_spawn_and_return_path_unchanged=True,
        save_structure_and_event_ids_unchanged=True,
        native_graphics_info='gObjectEventGraphicsInfo_BreakableRockFrlg',
        source_before_sha256=hashlib.sha256(before.encode()).hexdigest(),
        source_after_sha256=hashlib.sha256(after.encode()).hexdigest())
