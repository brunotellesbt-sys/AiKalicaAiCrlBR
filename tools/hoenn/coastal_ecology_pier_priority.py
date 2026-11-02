"""Keep complete dry approaches visible below the two custom high quays.

Cinnabar's lower wooden appendage and Pallet's south grass approach meet
multi-level wooden bridges. A pedestrian's hat overlaps the foreground tile
north of its feet, so changing draw priority only on the bridge itself clips
the actor after a southward step. Keep the dry approaches above that layer;
the actor's elevation, collision, Surf state and lower water route stay native.
"""
import hashlib
import json
import struct

from badge_story_layer import read


PATH = 'src/event_object_movement.c'
APPROACHES = (
    ('CinnabarIsland_Frlg', 'MAP_CINNABAR_ISLAND', (9, 16, 10, 17)),
    ('PalletTown_Frlg', 'MAP_PALLET_TOWN', (11, 26, 22, 26)),
)
OLD = '''    if (displayElevation == ELEVATION_DEFAULT
        && MapGridGetElevationAt(objEvent->currentCoords.x, objEvent->currentCoords.y) == ELEVATION_MULTI_LEVEL
        && MetatileBehavior_IsBridgeOverWater(objEvent->currentMetatileBehavior))
        displayElevation = 4;'''
NEW = '''    if (displayElevation == ELEVATION_DEFAULT
        && ((MapGridGetElevationAt(objEvent->currentCoords.x, objEvent->currentCoords.y) == ELEVATION_MULTI_LEVEL
            && MetatileBehavior_IsBridgeOverWater(objEvent->currentMetatileBehavior))
            || JourneyCoastalPierFootPriority(objEvent)))
        displayElevation = 4;'''
HELPER = '''// The whole dry approach must stay above the adjacent high quay, too.
// This changes display priority only; Surf retains its native lower layer.
static bool8 JourneyCoastalPierFootPriority(const struct ObjectEvent *objectEvent)
{
    s16 x = objectEvent->currentCoords.x - MAP_OFFSET;
    s16 y = objectEvent->currentCoords.y - MAP_OFFSET;
    u8 group = gSaveBlock1Ptr->location.mapGroup;
    u8 num = gSaveBlock1Ptr->location.mapNum;

    if (!objectEvent->isPlayer || objectEvent->currentElevation != ELEVATION_DEFAULT
        || !(gPlayerAvatar.flags & PLAYER_AVATAR_FLAG_ON_FOOT)
        || (gPlayerAvatar.flags & PLAYER_AVATAR_FLAG_SURFING))
        return FALSE;
    if (group == MAP_GROUP(MAP_CINNABAR_ISLAND) && num == MAP_NUM(MAP_CINNABAR_ISLAND))
        return x >= 9 && x <= 10 && y >= 16 && y <= 17;
    if (group == MAP_GROUP(MAP_PALLET_TOWN) && num == MAP_NUM(MAP_PALLET_TOWN))
        return x >= 11 && x <= 22 && y == 26;
    return FALSE;
}

'''
ANCHOR = 'static void UpdateObjectEventElevationAndPriority(struct ObjectEvent *objEvent, struct Sprite *sprite)\n{'


def repair(layer):
    layouts = {row['id']: row for row in json.loads(
        read(layer, 'data/layouts/layouts.json'))['layouts']}
    reviewed = []
    for name, map_id, bounds in APPROACHES:
        mapping = json.loads(read(layer, f'data/maps/{name}/map.json'))
        assert mapping['id'] == map_id
        layout = layouts[mapping['layout']]
        assert layout['layout_version'] == 'frlg'
        raw = read(layer, layout['blockdata_filepath'])
        values = struct.unpack('<'+'H'*(len(raw)//2), raw)
        x1, y1, x2, y2 = bounds
        cells = [[x, y] for y in range(y1, y2+1) for x in range(x1, x2+1)]
        assert all(values[y*layout['width']+x] >> 12 == 3
                   and not values[y*layout['width']+x] & 0xC00 for x, y in cells), name
        # Confirm both complete high-quay footprints are still multilevel.
        bridges = [[x, 15] for x in range(6, 12)] if name == 'CinnabarIsland_Frlg' else [[18, 25]]
        assert all(values[y*layout['width']+x] >> 12 == 15
                   and not values[y*layout['width']+x] & 0xC00 for x, y in bridges), name
        reviewed.append(dict(map=name, map_id=map_id, dry_approach_bounds=list(bounds),
            dry_approach_cells=cells, multilevel_bridge_cells=bridges,
            blockdata_sha256=hashlib.sha256(raw).hexdigest()))
    before = read(layer, PATH).decode()
    if HELPER in before:
        assert before.count(HELPER) == 1 and before.count(NEW) == 1 and OLD not in before
        changed = []
    else:
        assert 'JourneyCoastalPierFootPriority' not in before
        assert before.count(OLD) == 1 and before.count(ANCHOR) == 1
        after = before.replace(ANCHOR, HELPER+ANCHOR).replace(OLD, NEW)
        assert after.replace(HELPER, '').replace(NEW, OLD) == before
        layer.stage(PATH, after)
        changed = [PATH]
    return dict(kind='coastal-ecology-dry-pier-priority', changed_paths=changed,
        reviewed_approaches=reviewed, display_elevation_only=True,
        foot_elevation3_uses_priority1_on_complete_approaches=True,
        surf_elevation1_and_lower_priority2_preserved=True,
        map_graphics_elevation_collision_events_warps_and_connections_unchanged=True,
        avatar_position_elevation_and_mode_never_written=True,
        native_full_avatar_pixels_and_both_surf_routes_required=True)
