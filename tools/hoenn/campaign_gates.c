#include "global.h"
#include "event_data.h"
#include "journey_gym_scaling.h"
#include "journey_campaign_gates.h"
#include "script.h"
#include "fieldmap.h"
#include "constants/flags.h"
#include "constants/maps.h"
#include "constants/vars.h"

struct JourneyGymCity { u16 map; bool8 kanto; u8 badge; u16 x; u16 y; u8 guide; };
#include "journey_gym_cities.h"
extern const u8 Journey_GymGuide[];

static bool32 RegionalFlag(u16 flag)
{
    return (gSaveBlock1Ptr->flags[flag / 8] >> (flag & 7)) & 1;
}

// Return the first unfinished mandatory event. Neither the active map nor
// the other region's badges may change this regional progression.
u32 JourneyPendingCampaignEvent(bool32 kanto)
{
    u32 count = JourneyGymBadgeCount(kanto);
    if (kanto)
    {
        if (count >= 2 && !RegionalFlag(FLAG_HIDE_CELADON_ROCKETS))
            return 1;
        if (count >= 3 && !RegionalFlag(FLAG_HIDE_SAFFRON_ROCKETS))
            return 2;
    }
    else
    {
        if (count >= 2 && !RegionalFlag(FLAG_DEFEATED_EVIL_TEAM_MT_CHIMNEY))
            return 3;
        if (count >= 5 && !RegionalFlag(FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT))
            return 4;
        if (count >= 6 && !RegionalFlag(FLAG_DEFEATED_MAGMA_SPACE_CENTER))
            return 5;
        if (count >= 6 && !RegionalFlag(FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN))
            return 6;
    }
    return 0;
}

void JourneyStartSpaceCenterInvasion(void)
{
    // The original invasion was started by winning a particular gym. It must
    // be reachable before the seventh arbitrary gym, without awarding a badge.
    // Keep completed/in-progress states: never respawn defeated Magma members.
    if (JourneyGymBadgeCount(FALSE) < 6
        || !RegionalFlag(FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT)
        || RegionalFlag(FLAG_DEFEATED_MAGMA_SPACE_CENTER)
        || VarGet(VAR_MOSSDEEP_SPACE_CENTER_STATE) != 0)
        return;
    FlagClear(FLAG_HIDE_SLATEPORT_CITY_HARBOR_PATRONS);
    FlagClear(FLAG_HIDE_MOSSDEEP_CITY_TEAM_MAGMA);
    FlagClear(FLAG_HIDE_MOSSDEEP_CITY_SPACE_CENTER_1F_TEAM_MAGMA);
    FlagClear(FLAG_HIDE_MOSSDEEP_CITY_SPACE_CENTER_2F_TEAM_MAGMA);
    FlagClear(FLAG_HIDE_MOSSDEEP_CITY_SPACE_CENTER_2F_STEVEN);
    FlagSet(FLAG_HIDE_MOSSDEEP_CITY_SPACE_CENTER_1F_STEVEN);
    VarSet(VAR_MOSSDEEP_CITY_STATE, 1);
    VarSet(VAR_MOSSDEEP_SPACE_CENTER_STATE, 1);
}

u32 JourneyCurrentGymGate(void)
{
    u32 i;
    for (i = 0; i < ARRAY_COUNT(sJourneyGymCities); i++)
    {
        const struct JourneyGymCity *city = &sJourneyGymCities[i];
        if (gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(city->map)
            && gSaveBlock1Ptr->location.mapNum == MAP_NUM(city->map))
        {
            u16 first = city->kanto ? FLAG_KANTO_BADGE01_GET : FLAG_BADGE01_GET;
            if (RegionalFlag(first + city->badge))
                return 0; // Already won gyms remain accessible for revisits.
            return JourneyPendingCampaignEvent(city->kanto);
        }
    }
    return 0;
}

void JourneyUpdateGymGate(void)
{
    u16 flag = isFrlg ? FLAG_HIDE_JOURNEY_KANTO_GYM_GUIDE : FLAG_HIDE_JOURNEY_HOENN_GYM_GUIDE;
    u32 gate;
    if (!isFrlg)
        JourneyStartSpaceCenterInvasion();
    gate = JourneyCurrentGymGate();
    if (gate)
        FlagClear(flag);
    else
        FlagSet(flag);
}

void JourneyExplainGymGate(void)
{
    gSpecialVar_Result = JourneyCurrentGymGate();
}

bool32 JourneyTryGymDoorGate(s16 x, s16 y)
{
    u32 i;
    if (!JourneyCurrentGymGate())
        return FALSE;
    for (i = 0; i < ARRAY_COUNT(sJourneyGymCities); i++)
    {
        const struct JourneyGymCity *city = &sJourneyGymCities[i];
        if (gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(city->map)
            && gSaveBlock1Ptr->location.mapNum == MAP_NUM(city->map)
            && x == city->x + MAP_OFFSET && y == city->y + MAP_OFFSET)
        {
            // Door warps run before normal object collision in this engine.
            // Intercept the actual entrance as well as providing a visible NPC.
            gSpecialVar_LastTalked = city->guide;
            ScriptContext_SetupScript(Journey_GymGuide);
            return TRUE;
        }
    }
    return FALSE;
}
