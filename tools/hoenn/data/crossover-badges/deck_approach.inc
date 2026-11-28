static bool8 JourneyCrossoverDeckApproach(s16 x, s16 y, s16 *spawnX, s16 *spawnY)
{
    // Both entrances from Route 108 lead to this two-tile-wide gangway.
    if (y != 14 + MAP_OFFSET || (x != 13 + MAP_OFFSET && x != 14 + MAP_OFFSET))
        return FALSE;

    u8 elevation = MapGridGetElevationAt(x, y);
    if (!JourneyApproachTileClear(x, y - 3, elevation)
        || !JourneyApproachTileClear(x, y - 2, elevation)
        || !JourneyApproachTileClear(x, y - 1, elevation))
        return FALSE;

    *spawnX = x;
    *spawnY = y - 3;
    gJourneyCrossoverMovement[0] = MOVEMENT_ACTION_WALK_NORMAL_DOWN;
    gJourneyCrossoverMovement[1] = MOVEMENT_ACTION_WALK_NORMAL_DOWN;
    gJourneyCrossoverMovement[2] = MOVEMENT_ACTION_STEP_END;
    return TRUE;
}
