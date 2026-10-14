#define JOURNEY_PATH_RADIUS 16
#define JOURNEY_PATH_WIDTH (JOURNEY_PATH_RADIUS * 2 + 1)
#define JOURNEY_PATH_CELLS (JOURNEY_PATH_WIDTH * JOURNEY_PATH_WIDTH)
#define JOURNEY_PATH_MAX_STEPS 127

EWRAM_DATA u8 gJourneyCrossoverMovement[JOURNEY_PATH_MAX_STEPS + 1] = {0};
static EWRAM_DATA bool8 sJourneyCrossoverAttempted = FALSE;
static EWRAM_DATA s16 sJourneyAttemptX = 0, sJourneyAttemptY = 0;
static EWRAM_DATA u16 sJourneyAttemptMap = 0;

struct JourneyApproachSearch
{
    u16 parent[JOURNEY_PATH_CELLS];
    u16 queue[JOURNEY_PATH_CELLS];
};

static bool8 JourneyApproachTileClear(s16 x, s16 y, u8 elevation)
{
    if (x < MAP_OFFSET || y < MAP_OFFSET
        || x >= gMapHeader.mapLayout->width + MAP_OFFSET
        || y >= gMapHeader.mapLayout->height + MAP_OFFSET
        || MapGridGetCollisionAt(x, y)
        || MapGridGetElevationAt(x, y) != elevation
        || GetObjectEventIdByXY(x, y) != OBJECT_EVENTS_COUNT)
        return FALSE;
    u8 behavior = MapGridGetMetatileBehaviorAt(x, y);
    if (MetatileBehavior_IsSurfableWaterOrUnderwater(behavior)
        || MetatileBehavior_IsJumpNorth(behavior) || MetatileBehavior_IsJumpSouth(behavior)
        || MetatileBehavior_IsJumpWest(behavior) || MetatileBehavior_IsJumpEast(behavior))
        return FALSE;
    // NPCs cannot take shortcuts through doors or entrance warp tiles.
    for (u32 i = 0; i < gMapHeader.events->warpCount; i++)
        if (gMapHeader.events->warps[i].x == x - MAP_OFFSET
            && gMapHeader.events->warps[i].y == y - MAP_OFFSET)
            return FALSE;
    return TRUE;
}

static bool8 JourneyApproachFindPath(s16 x, s16 y, s16 *spawnX, s16 *spawnY)
{
    static const s8 directions[][2] = {{-1,0},{1,0},{0,-1},{0,1}};
    struct JourneyApproachSearch *search = Alloc(sizeof(*search));
    if (!search) return FALSE;
    for (u32 i = 0; i < JOURNEY_PATH_CELLS; i++) search->parent[i] = 0xFFFF;
    const u16 start = JOURNEY_PATH_RADIUS * JOURNEY_PATH_WIDTH + JOURNEY_PATH_RADIUS;
    u16 head = 0, tail = 1, goal = 0xFFFF;
    search->queue[0] = start;
    search->parent[start] = start;
    const struct ObjectEvent *player = &gObjectEvents[gPlayerAvatar.objectEventId];
    const struct Sprite *sprite = &gSprites[player->spriteId];
    const s16 screenX = sprite->x + sprite->x2 + gSpriteCoordOffsetX;
    const s16 screenY = sprite->y + sprite->y2 + gSpriteCoordOffsetY;
    const u8 elevation = MapGridGetElevationAt(x, y);
    while (head < tail)
    {
        u16 index = search->queue[head++];
        s16 gx = index % JOURNEY_PATH_WIDTH, gy = index / JOURNEY_PATH_WIDTH;
        s16 dx = gx - JOURNEY_PATH_RADIUS, dy = gy - JOURNEY_PATH_RADIUS;
        s16 px = screenX + dx * 16, py = screenY + dy * 16;
        // Include the whole 16x32 sprite plus a tile's margin: the actor is
        // born outside the current camera, including camera panning.
        if (index != start && (px + 8 <= -16 || px - 8 >= DISPLAY_WIDTH + 16
            || py + 16 <= -16 || py - 16 >= DISPLAY_HEIGHT + 16))
        {
            goal = index;
            *spawnX = x + dx;
            *spawnY = y + dy;
            break;
        }
        for (u32 d = 0; d < ARRAY_COUNT(directions); d++)
        {
            s16 nx = gx + directions[d][0], ny = gy + directions[d][1];
            if (nx < 0 || ny < 0 || nx >= JOURNEY_PATH_WIDTH || ny >= JOURNEY_PATH_WIDTH) continue;
            u16 next = ny * JOURNEY_PATH_WIDTH + nx;
            if (search->parent[next] != 0xFFFF
                || !JourneyApproachTileClear(x + nx - JOURNEY_PATH_RADIUS,
                    y + ny - JOURNEY_PATH_RADIUS, elevation)) continue;
            search->parent[next] = index;
            search->queue[tail++] = next;
        }
    }
    u32 steps = 0;
    if (goal != 0xFFFF)
    {
        for (u16 node = goal; search->parent[node] != start; node = search->parent[node])
        {
            if (steps >= JOURNEY_PATH_MAX_STEPS) {goal = 0xFFFF; break;}
            u16 next = search->parent[node];
            gJourneyCrossoverMovement[steps++] = next == node - 1 ? MOVEMENT_ACTION_WALK_NORMAL_LEFT
                : next == node + 1 ? MOVEMENT_ACTION_WALK_NORMAL_RIGHT
                : next < node ? MOVEMENT_ACTION_WALK_NORMAL_UP : MOVEMENT_ACTION_WALK_NORMAL_DOWN;
        }
        gJourneyCrossoverMovement[steps] = MOVEMENT_ACTION_STEP_END;
    }
    Free(search);
    return goal != 0xFFFF && steps > 0;
}

bool8 JourneyCrossoverTryEncounter(void)
{
    s16 x, y;
    if (!FlagGet(FLAG_SYS_POKEMON_GET) || VarGet(JOURNEY_GALACTIC_STATE) >= 7)
    {sJourneyCrossoverAttempted = FALSE; return FALSE;}
    PlayerGetDestCoords(&x, &y);
    if (MetatileBehavior_IsSurfableWaterOrUnderwater(MapGridGetMetatileBehaviorAt(x, y))) return FALSE;
    u16 map = (gSaveBlock1Ptr->location.mapGroup << 8) | gSaveBlock1Ptr->location.mapNum;
    if (sJourneyCrossoverAttempted && sJourneyAttemptMap == map && sJourneyAttemptX == x && sJourneyAttemptY == y)
        return FALSE;
    for (u32 i = 0; i < ARRAY_COUNT(sJourneyCrossoverLocations); i++)
    {
        const struct JourneyCrossoverLocation *entry = &sJourneyCrossoverLocations[i];
        if (MAP_GROUP(entry->map) != gSaveBlock1Ptr->location.mapGroup
            || MAP_NUM(entry->map) != gSaveBlock1Ptr->location.mapNum
            || (VarGet(JOURNEY_RIVAL_VISITS) & (1 << i))) continue;
        sJourneyCrossoverAttempted = TRUE;
        sJourneyAttemptMap = map; sJourneyAttemptX = x; sJourneyAttemptY = y;
        s16 xx, yy;
        if (!JourneyApproachFindPath(x, y, &xx, &yy)) return FALSE;
        const u8 first = gJourneyCrossoverMovement[0];
        u8 facing = first == MOVEMENT_ACTION_WALK_NORMAL_UP ? MOVEMENT_TYPE_FACE_UP
            : first == MOVEMENT_ACTION_WALK_NORMAL_DOWN ? MOVEMENT_TYPE_FACE_DOWN
            : first == MOVEMENT_ACTION_WALK_NORMAL_LEFT ? MOVEMENT_TYPE_FACE_LEFT : MOVEMENT_TYPE_FACE_RIGHT;
        u8 id = SpawnSpecialObjectEventParameterized(entry->gfx, facing, JOURNEY_RIVAL_LOCALID,
            xx, yy, MapGridGetElevationAt(xx, yy));
        if (id >= OBJECT_EVENTS_COUNT) return FALSE;
        sJourneyCrossoverActive = i + 1;
        gSpecialVar_LastTalked = JOURNEY_RIVAL_LOCALID;
        ScriptContext_SetupScript(JourneyCrossover_Encounter);
        return TRUE;
    }
    return FALSE;
}
