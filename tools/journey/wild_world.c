#include "global.h"
#include "pokemon.h"
#include "random.h"
#include "event_data.h"
#include "journey.h"
#include "open_world.h"
#include "wild_world.h"
#include "constants/species.h"
#include "constants/maps.h"
struct WildWorldFamily { u16 stages[3]; };
struct WildWorldPool { u8 group, map, area, count; u16 families[24]; };
#include "wild_world_data.h"

u8 WildWorld_Mean(void)
{
    u16 total = 0;
    u8 i, count = 0;
    for (i = 0; i < PARTY_SIZE; i++)
    {
        if (GetMonData(&gPlayerParty[i], MON_DATA_SPECIES) != SPECIES_NONE
         && !GetMonData(&gPlayerParty[i], MON_DATA_IS_EGG))
        {
            total += GetMonData(&gPlayerParty[i], MON_DATA_LEVEL);
            count++;
        }
    }
    return count ? total / count : 5;
}
u8 WildWorld_Level(void)
{
    u8 mean = WildWorld_Mean();
    u8 lo = mean > 5 ? mean - 5 : 1;
    u8 hi = mean < 98 ? mean + 2 : 100;
    return lo + Random() % (hi - lo + 1);
}
u16 WildWorld_Species(u16 original, u8 area)
{
    u16 i, family = sWildWorldRoots[original];
    u8 badges = OpenWorld_BadgeCount();
    u8 stage = badges < 3 ? 0 : (badges < 6 ? Random() % 2 : 1 + Random() % 2);
    if (original == SPECIES_UNOWN)
        return original;
    for (i = 0; i < ARRAY_COUNT(sWildWorldPools); i++)
    {
        const struct WildWorldPool *pool = &sWildWorldPools[i];
        if (pool->group == gSaveBlock1Ptr->location.mapGroup
         && pool->map == gSaveBlock1Ptr->location.mapNum && pool->area == area)
        {
            // Keep the original weighted slot 75% of the time. The remaining
            // encounters mix both versions; a home-city/map affinity raises
            // one native family's weight without introducing alien habitats.
            u16 roll = Random() % 8;
            if (roll < 2)
            {
                u16 index = roll == 0 ? Random() % pool->count
                    : (VarGet(VAR_JOURNEY_CITY) + pool->map * 3 + pool->group + area) % pool->count;
                family = pool->families[index];
            }
            break;
        }
    }
    return sWildWorldFamilies[family].stages[stage];
}
