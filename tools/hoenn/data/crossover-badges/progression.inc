struct JourneyCrossoverLocation
{
    u16 map;
    u16 gfx;
    const u8 *name;
    u8 badges;
    bool8 kanto;
};

// Keep the original indices: each is a persistent bit in JOURNEY_RIVAL_VISITS.
static const struct JourneyCrossoverLocation sJourneyCrossoverLocations[] = {
    {MAP_ROUTE4,          OBJ_EVENT_GFX_JOURNEY_EREN,  COMPOUND_STRING("ROUTE 4, KANTO"), 1, TRUE},
    {MAP_ROUTE10,         OBJ_EVENT_GFX_JOURNEY_EREN,  COMPOUND_STRING("ROUTE 10, KANTO"), 3, TRUE},
    {MAP_ROUTE17,         OBJ_EVENT_GFX_JOURNEY_EREN,  COMPOUND_STRING("ROUTE 17, KANTO"), 5, TRUE},
    {MAP_ROUTE112,        OBJ_EVENT_GFX_JOURNEY_EREN,  COMPOUND_STRING("ROUTE 112, HOENN"), 3, FALSE},
    {MAP_ROUTE113,        OBJ_EVENT_GFX_JOURNEY_EREN,  COMPOUND_STRING("ROUTE 113, HOENN"), 5, FALSE},
    {MAP_PETALBURG_WOODS, OBJ_EVENT_GFX_JOURNEY_EREN,  COMPOUND_STRING("PETALBURG WOODS"), 1, FALSE},
    {MAP_ROUTE6,          OBJ_EVENT_GFX_JOURNEY_LUFFY, COMPOUND_STRING("ROUTE 6, KANTO"), 2, TRUE},
    {MAP_ROUTE13,         OBJ_EVENT_GFX_JOURNEY_LUFFY, COMPOUND_STRING("ROUTE 13, KANTO"), 4, TRUE},
    {MAP_ROUTE20,         OBJ_EVENT_GFX_JOURNEY_LUFFY, COMPOUND_STRING("ROUTE 20, KANTO"), 6, TRUE},
    {MAP_ROUTE106,        OBJ_EVENT_GFX_JOURNEY_LUFFY, COMPOUND_STRING("ROUTE 106, HOENN"), 2, FALSE},
    {MAP_ABANDONED_SHIP_DECK, OBJ_EVENT_GFX_JOURNEY_LUFFY, COMPOUND_STRING("THE SHIP DECK, ROUTE 108"), 4, FALSE},
    {MAP_ROUTE125,        OBJ_EVENT_GFX_JOURNEY_LUFFY, COMPOUND_STRING("ROUTE 125, HOENN"), 6, FALSE},
};

static u32 JourneyCrossoverNext(bool8 kanto, u16 visits)
{
    u32 next = ARRAY_COUNT(sJourneyCrossoverLocations);
    for (u32 i = 0; i < ARRAY_COUNT(sJourneyCrossoverLocations); i++)
    {
        const struct JourneyCrossoverLocation *entry = &sJourneyCrossoverLocations[i];
        if (entry->kanto != kanto || (visits & (1 << i)))
            continue;
        if (next == ARRAY_COUNT(sJourneyCrossoverLocations) || entry->badges < sJourneyCrossoverLocations[next].badges)
            next = i;
    }
    return next;
}

static bool8 JourneyCrossoverReady(u32 index, u16 visits)
{
    const struct JourneyCrossoverLocation *entry = &sJourneyCrossoverLocations[index];
    return JourneyGymBadgeCount(entry->kanto) >= entry->badges
        && JourneyCrossoverNext(entry->kanto, visits) == index;
}
