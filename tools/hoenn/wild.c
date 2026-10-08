#include "global.h"
#include "pokemon.h"
#include "random.h"
#include "event_data.h"
#include "journey_gym_scaling.h"
#include "journey_wild.h"
#include "constants/species.h"
#include "constants/vars.h"
#include "constants/maps.h"

struct JourneyWildStages { u16 root; u8 count[3]; u16 stages[3][8]; };
struct JourneyWildPool { u16 map; u8 area, count; u16 species[24]; };
#include "journey_wild_data.h"

u32 JourneyWildMean(void)
{
    u32 total = 0, count = 0, i;
    for (i = 0; i < PARTY_SIZE; i++)
        if (GetMonData(&gPlayerParty[i], MON_DATA_SPECIES) != SPECIES_NONE
         && !GetMonData(&gPlayerParty[i], MON_DATA_IS_EGG))
        {
            total += GetMonData(&gPlayerParty[i], MON_DATA_LEVEL);
            count++;
        }
    return count ? total / count : 5;
}

u32 JourneyWildLevel(void)
{
    u32 mean = JourneyWildMean();
    u32 low = mean > 5 ? mean - 5 : 1;
    u32 high = mean < 98 ? mean + 2 : 100;
    return low + Random() % (high - low + 1);
}

u32 JourneyWildNormalizeLevel(u32 level)
{
    u32 mean = JourneyWildMean();
    if (level >= (mean > 5 ? mean - 5 : 1) && level <= (mean < 98 ? mean + 2 : 100))
        return level;
    return JourneyWildLevel();
}

u32 JourneyWildPhase(void)
{
    u32 kanto = JourneyGymBadgeCount(TRUE), hoenn = JourneyGymBadgeCount(FALSE);
    u32 progress = (kanto + hoenn) / 2;
    return progress < 3 ? 0 : progress < 6 ? 1 : 2;
}

u32 JourneyWildSpecies(u32 original, u32 area)
{
    u32 i, selected = original, phase = JourneyWildPhase(), stage;
    const struct JourneyWildStages *family;
    if (original == SPECIES_UNOWN || original == SPECIES_NONE || original >= ARRAY_COUNT(sJourneyWildStages))
        return original;
    for (i = 0; i < ARRAY_COUNT(sJourneyWildPools); i++)
    {
        const struct JourneyWildPool *pool = &sJourneyWildPools[i];
        if (MAP_GROUP(pool->map) == gSaveBlock1Ptr->location.mapGroup
         && MAP_NUM(pool->map) == gSaveBlock1Ptr->location.mapNum && pool->area == area)
        {
            u32 roll = Random() % 8;
            if (roll < 2)
                selected = pool->species[roll == 0 ? Random() % pool->count
                    : (VarGet(VAR_JOURNEY_FAMILY_HOME) + pool->map + area) % pool->count];
            break;
        }
    }
    family = &sJourneyWildStages[selected];
    stage = phase == 0 ? 0 : phase == 1 ? Random() % 2 : 1 + Random() % 2;
    return family->stages[stage][Random() % family->count[stage]];
}
