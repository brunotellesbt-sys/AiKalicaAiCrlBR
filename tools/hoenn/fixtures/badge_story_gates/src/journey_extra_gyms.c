#include "global.h"
#include "event_data.h"
#include "journey_extra_gyms.h"
#include "journey_gym_scaling.h"
#include "journey_version.h"
#include "constants/flags.h"
#include "constants/vars.h"
#include "constants/event_objects.h"
static const u16 sExtraBadgeFlags[] = {FLAG_JOURNEY_BADGE_MORTY, FLAG_JOURNEY_BADGE_WHITNEY, FLAG_JOURNEY_BADGE_STEVEN, FLAG_JOURNEY_BADGE_BUGSY, FLAG_JOURNEY_BADGE_CANDICE, FLAG_JOURNEY_BADGE_CLAIR, FLAG_JOURNEY_BADGE_KAREN, FLAG_JOURNEY_BADGE_OAK};
bool32 JourneyBadgeAt(u32 index)
{
    u16 flag;
    if (index >= 24) return FALSE;
    flag = index < 8 ? FLAG_BADGE01_GET + index
        : index < 16 ? FLAG_KANTO_BADGE01_GET + index - 8
        : sExtraBadgeFlags[index - 16];
    return (gSaveBlock1Ptr->flags[flag / 8] >> (flag & 7)) & 1;
}
u32 JourneyExtraBadgeCount(void)
{
    u32 i, count = 0;
    for (i = 16; i < 24; i++) count += JourneyBadgeAt(i);
    return count;
}
u32 JourneyTotalBadgeCount(void)
{
    return JourneyGymBadgeCount(TRUE) + JourneyGymBadgeCount(FALSE) + JourneyExtraBadgeCount();
}
void JourneyExtraGymEdition(void)
{
    bool32 modern = gJourneyBuildRules.maxNational > 493;
    VarSet(VAR_OBJ_GFX_ID_0, modern ? OBJ_EVENT_GFX_JOURNEY_PWT_VALERIE : OBJ_EVENT_GFX_JOURNEY_PWT_WHITNEY);
    gSpecialVar_Result = modern;
}

void JourneyExtraLeagueBadges(void) { gSpecialVar_Result = JourneyTotalBadgeCount() == 24; }
