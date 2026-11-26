struct JourneyCrossoverLocation
{
    u16 map;
    u16 gfx;
    const u8 *name;
    u8 badges;
    u8 visitBit;
};

// Each row uses the persistent bit of its location. Bits from retired
// locations still count for players who won those battles in an older ROM.
static const struct JourneyCrossoverLocation sJourneyCrossoverLocations[] = {
    {MAP_ROUTE4, OBJ_EVENT_GFX_JOURNEY_EREN, COMPOUND_STRING("ROTA 4, KANTO"), 1, 0},
    {MAP_ROUTE112, OBJ_EVENT_GFX_JOURNEY_EREN, COMPOUND_STRING("ROTA 112, HOENN"), 5, 3},
    {MAP_ROUTE17, OBJ_EVENT_GFX_JOURNEY_EREN, COMPOUND_STRING("ROTA 17, KANTO"), 13, 2},
    {MAP_ROUTE123, OBJ_EVENT_GFX_JOURNEY_EREN, COMPOUND_STRING("OESTE DA ROTA 123"), 20, 12},
    {MAP_ROUTE106, OBJ_EVENT_GFX_JOURNEY_LUFFY, COMPOUND_STRING("ROTA 106, HOENN"), 2, 9},
    {MAP_ROUTE13, OBJ_EVENT_GFX_JOURNEY_LUFFY, COMPOUND_STRING("ROTA 13, KANTO"), 7, 7},
    {MAP_ABANDONED_SHIP_DECK, OBJ_EVENT_GFX_JOURNEY_LUFFY, COMPOUND_STRING("CONVÉS DA ROTA 108"), 11, 10},
    {MAP_SIX_ISLAND_WATER_PATH, OBJ_EVENT_GFX_JOURNEY_LUFFY, COMPOUND_STRING("CAMINHO AQUÁTICO, ILHA 6"), 15, 13},
};

static u32 JourneyCrossoverWon(bool8 luffy, u16 visits)
{
    u16 original = (visits >> (luffy ? 6 : 0)) & 0x3F;
    u32 count = (visits >> (luffy ? 13 : 12)) & 1;
    while (original)
    {
        original &= original - 1;
        count++;
    }
    return count;
}

static u32 JourneyCrossoverNext(bool8 luffy, u16 visits)
{
    u32 wins = JourneyCrossoverWon(luffy, visits);
    u32 first = luffy ? 4 : 0;
    u32 last = first + 3;
    if (wins >= 4)
        return ARRAY_COUNT(sJourneyCrossoverLocations);
    if (wins == 3 && !(visits & (1 << sJourneyCrossoverLocations[last].visitBit)))
        return last;
    for (u32 i = first; i < last; i++)
        if (!(visits & (1 << sJourneyCrossoverLocations[i].visitBit)))
            return i;
    return last;
}

static bool8 JourneyCrossoverReady(u32 index, u16 visits)
{
    const struct JourneyCrossoverLocation *entry = &sJourneyCrossoverLocations[index];
    return index == JourneyCrossoverNext(entry->gfx == OBJ_EVENT_GFX_JOURNEY_LUFFY, visits)
        && JourneyTotalBadgeCount() >= entry->badges;
}
