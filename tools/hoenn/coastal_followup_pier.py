"""Give the Cinnabar terminal a real foot level before its multilevel quay.

Leaving the old elevation-zero door directly onto elevation15 retained zero.
That wildcard level hid the pedestrian behind the quay and allowed stepping
into level1 sea without Surf. Keep the high bridge and its lower Surf route.
"""
import hashlib
import json
import struct

from badge_story_layer import read


RECOVERY_OLD = '''    if (gSaveBlock1Ptr->location.mapGroup != MAP_GROUP(MAP_ONE_ISLAND_TREASURE_BEACH)
     || gSaveBlock1Ptr->location.mapNum != MAP_NUM(MAP_ONE_ISLAND_TREASURE_BEACH)
     || !TestPlayerAvatarFlags(PLAYER_AVATAR_FLAG_ON_FOOT)'''
RECOVERY_NEW = '''    if (!((gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(MAP_ONE_ISLAND_TREASURE_BEACH)
        && gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_ONE_ISLAND_TREASURE_BEACH))
       || (gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(MAP_CINNABAR_ISLAND)
        && gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_CINNABAR_ISLAND)))
     || !TestPlayerAvatarFlags(PLAYER_AVATAR_FLAG_ON_FOOT)'''

BRIDGE_HELPER = '''// Old batteries can retain elevation0 after exiting the former level0 door.
// Restore only that invalid pedestrian state on Cinnabar's high quay.
static void JourneyCinnabarLegacyBridgeLevel(struct ObjectEvent *objectEvent)
{
    s16 x = objectEvent->currentCoords.x - MAP_OFFSET;
    s16 y = objectEvent->currentCoords.y - MAP_OFFSET;

    if (objectEvent->isPlayer && objectEvent->currentElevation == ELEVATION_TRANSITION
        && (gPlayerAvatar.flags & PLAYER_AVATAR_FLAG_ON_FOOT)
        && !(gPlayerAvatar.flags & PLAYER_AVATAR_FLAG_SURFING)
        && gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(MAP_CINNABAR_ISLAND)
        && gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_CINNABAR_ISLAND)
        && x >= 6 && x <= 11 && y == 15
        && MapGridGetElevationAt(objectEvent->currentCoords.x, objectEvent->currentCoords.y) == ELEVATION_MULTI_LEVEL
        && MetatileBehavior_IsBridgeOverWater(MapGridGetMetatileBehaviorAt(
            objectEvent->currentCoords.x, objectEvent->currentCoords.y)))
    {
        objectEvent->currentElevation = ELEVATION_DEFAULT;
        objectEvent->previousElevation = ELEVATION_DEFAULT;
    }
}

'''
PROTOTYPE = 'static void JourneyCinnabarLegacyBridgeLevel(struct ObjectEvent *objectEvent);\n'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def repair(layer):
    layouts = {r['id']: r for r in json.loads(read(layer, 'data/layouts/layouts.json'))['layouts']}
    mapping = json.loads(read(layer, 'data/maps/CinnabarIsland_Frlg/map.json'))
    layout = layouts[mapping['layout']]
    raw = read(layer, layout['blockdata_filepath'])
    values = list(struct.unpack('<'+'H'*(len(raw)//2), raw))
    width = layout['width'];index = 14*width+7
    assert values[index] == 0x03F6
    assert any(e['x'] == 7 and e['y'] == 14 and e['dest_map'] == 'MAP_JOURNEY_CINNABAR_HARBOR'
               for e in mapping['warp_events'])
    bridge = [values[15*width+x] for x in range(6, 12)]
    assert all(word >> 12 == 15 and not word & 0xC00 for word in bridge)
    values[index] = 0x33F6
    packed = struct.pack('<'+'H'*len(values), *values)
    layer.stage(layout['blockdata_filepath'], packed)

    path = 'src/overworld.c'
    old = read(layer, path).decode()
    assert old.count(RECOVERY_OLD) == 1 and RECOVERY_NEW not in old
    after = old.replace(RECOVERY_OLD, RECOVERY_NEW)
    layer.stage(path, after)
    recovery = dict(file=path, before_sha256=digest(old.encode()), after_sha256=digest(after.encode()),
        existing_native_surf_transition_reused=True, only_new_map='CinnabarIsland_Frlg',
        saved_coordinates_and_save_abi_unchanged=True)

    path = 'src/event_object_movement.c'
    old = read(layer, path).decode()
    helper_anchor = '// The whole dry approach must stay above the adjacent high quay, too.\n'
    collision_anchor = '''enum Collision GetCollisionAtCoords(struct ObjectEvent *objectEvent, s16 x, s16 y, enum Direction dir)
{
    u8 currentBehavior = MapGridGetMetatileBehaviorAt(objectEvent->currentCoords.x, objectEvent->currentCoords.y);
    u8 nextBehavior = MapGridGetMetatileBehaviorAt(x, y);
    enum Collision collision;
'''
    update_anchor = '    JourneyDewfordBridgeRestoreLevel(objEvent);\n'
    assert old.count(helper_anchor) == old.count(collision_anchor) == old.count(update_anchor) == 1
    assert 'JourneyCinnabarLegacyBridgeLevel' not in old
    after = old.replace(helper_anchor, BRIDGE_HELPER+helper_anchor)
    after = after.replace(collision_anchor, PROTOTYPE+'\n'+collision_anchor+'    JourneyCinnabarLegacyBridgeLevel(objectEvent);\n')
    after = after.replace(update_anchor, update_anchor+'    JourneyCinnabarLegacyBridgeLevel(objEvent);\n')
    layer.stage(path, after)
    bridge_recovery = dict(file=path, before_sha256=digest(old.encode()), after_sha256=digest(after.encode()),
        map='CinnabarIsland_Frlg', bounds=[6, 15, 11, 15], invalid_foot_elevation=0,
        restored_native_foot_elevation=3, surf_level1_not_modified=True,
        all_other_maps_actors_elevations_and_coordinates_unchanged=True)
    return dict(kind='arrival-coast-cinnabar-door',
        changed_paths=[layout['blockdata_filepath'], 'src/overworld.c', path],
        door=dict(map='CinnabarIsland_Frlg', cell=[7,14], before=0x03F6, after=0x33F6,
                  behavior_graphics_and_warp_unchanged=True),
        blockdata_before_sha256=digest(raw), blockdata_after_sha256=digest(packed),
        bridge_words_preserved=bridge, legacy_water_recovery=recovery,
        legacy_bridge_recovery=bridge_recovery,
        interior_door_bridge_water_attempt_and_return_controller_proof_required=True,
        native_lower_surf_route_and_old_battery_continue_proofs_required=True)
