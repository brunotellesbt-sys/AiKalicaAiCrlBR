"""Recover the obsolete walking-water battery through the native Surf state.

Continue restores saved object graphics instead of the terrain-aware initial
avatar state. A legacy on-foot save in Treasure Beach sea therefore needs a
native transition after its player object and sprite have been restored.
This helper stages one C file; it never edits a candidate or battery itself.
"""
import hashlib

from badge_story_layer import read


PATH = 'src/overworld.c'
ANCHOR = '''static void InitObjectEventsReturnToField(void)
{
    SpawnObjectEventsOnReturnToField(0, 0);
    RotatingGate_InitPuzzleAndGraphics();
    RunOnReturnToFieldMapScript();
}'''
RECOVERY = '''static void RecoverSeviiLegacyWalkingWater(void)
{
    const struct ObjectEvent *player;

    // Old batteries can retain walking graphics after the former pier leak.
    // Continue restores those graphics without the ordinary map-load check.
    if (gSaveBlock1Ptr->location.mapGroup != MAP_GROUP(MAP_ONE_ISLAND_TREASURE_BEACH)
     || gSaveBlock1Ptr->location.mapNum != MAP_NUM(MAP_ONE_ISLAND_TREASURE_BEACH)
     || !TestPlayerAvatarFlags(PLAYER_AVATAR_FLAG_ON_FOOT)
     || PlayerGetElevation() != ELEVATION_SURF
     || FlagGet(FLAG_SYS_CRUISE_MODE))
        return;

    player = &gObjectEvents[gPlayerAvatar.objectEventId];
    if (MapGridGetElevationAt(player->currentCoords.x, player->currentCoords.y) == ELEVATION_SURF
     && MetatileBehavior_IsSurfableWaterOrUnderwater(MapGridGetMetatileBehaviorAt(
            player->currentCoords.x, player->currentCoords.y)))
        SetPlayerAvatarTransitionFlags(PLAYER_AVATAR_FLAG_SURFING);
}'''


def repair(layer):
    before = read(layer, PATH).decode()
    assert before.count(ANCHOR) == 1, 'Native return-to-field lifecycle changed'
    assert 'RecoverSeviiLegacyWalkingWater' not in before
    updated = ANCHOR.replace('    SpawnObjectEventsOnReturnToField(0, 0);',
        '    SpawnObjectEventsOnReturnToField(0, 0);\n    RecoverSeviiLegacyWalkingWater();')
    after = before.replace(ANCHOR, RECOVERY + '\n\n' + updated)
    assert after.replace(RECOVERY + '\n\n' + updated, ANCHOR) == before
    layer.stage(PATH, after)
    return dict(kind='coastal-ecology-legacy-surf-recovery', changed_paths=[PATH],
        before_sha256=hashlib.sha256(before.encode()).hexdigest(),
        after_sha256=hashlib.sha256(after.encode()).hexdigest(),
        map='OneIsland_TreasureBeach_Frlg',
        lifecycle='after complete native object/sprite restoration on return to field',
        guards=['Treasure Beach map', 'on foot', 'player elevation 1',
                'map elevation 1', 'native surfable water', 'not cruise mode'],
        recovery='synchronous native Surf avatar transition and Surf blob creation',
        coordinates_and_elevations_preserved=True,
        native_avatar_transition_without_direct_state_or_save_memory_writes=True,
        save_abi_unchanged=True,
        other_maps_dry_tiles_bridges_and_existing_avatar_modes_preserved=True,
        legacy_battery_cold_continue_and_controller_reboard_validation_required=True)
