#include "global.h"
#include "data.h"
#include "journey_gym_scaling.h"
#include "event_data.h"
#include "constants/maps.h"
#include "constants/flags.h"
#include "constants/trainers.h"

struct JourneyGym { u16 map; bool8 kanto; };
#include "journey_gym_maps.h"
static const u8 sAceLevels[] = {14, 21, 28, 35, 42, 48, 54, 60};

u32 JourneyGymBadgeCount(bool32 kanto)
{
    u32 i, count = 0;
    u16 start = kanto ? FLAG_KANTO_BADGE01_GET : FLAG_BADGE01_GET;
    // Read the explicit regional bank, independent of the active map's
    // FlagGet remapping. Battle code must never borrow the other region's badges.
    for (i = 0; i < 8; i++)
    {
        u16 flag = start + i;
        if (gSaveBlock1Ptr->flags[flag / 8] & (1 << (flag & 7)))
            count++;
    }
    return count;
}

u32 JourneyGymLevel(const struct Trainer *trainer, u32 originalLevel)
{
    u32 gym, i, highest = 0, count, gap;
    for (gym = 0; gym < ARRAY_COUNT(sJourneyGyms); gym++)
        if (gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(sJourneyGyms[gym].map)
            && gSaveBlock1Ptr->location.mapNum == MAP_NUM(sJourneyGyms[gym].map))
            break;
    if (gym == ARRAY_COUNT(sJourneyGyms))
        return originalLevel;
    count = JourneyGymBadgeCount(sJourneyGyms[gym].kanto);
    if (count > 7)
        count = 7;
    for (i = 0; i < (trainer->poolSize ? trainer->poolSize : trainer->partySize); i++)
        if (trainer->party[i].lvl > highest)
            highest = trainer->party[i].lvl;
    gap = highest > originalLevel ? highest - originalLevel : 0;
    if (gap > 6)
        gap = 6;
    return sAceLevels[count] - gap
        - ((trainer->trainerClass == TRAINER_CLASS_LEADER
            || trainer->trainerClass == TRAINER_CLASS_LEADER_FRLG) ? 0 : 2);
}
