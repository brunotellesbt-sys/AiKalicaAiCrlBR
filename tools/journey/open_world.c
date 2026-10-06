#include "global.h"
#include "open_world.h"
#include "event_data.h"
#include "battle.h"
#include "constants/flags.h"
#include "constants/opponents.h"
#include "constants/trainers.h"
#include "constants/vars.h"
struct GymTrainer { u16 trainer; u8 highest; bool8 leader; };
#include "open_world_trainers.h"
static const u8 sAceLevels[] = {14, 21, 28, 35, 42, 48, 54, 60};
u8 OpenWorld_BadgeCount(void)
{
    u8 count = 0, i;
    for (i = 0; i < 8; i++)
        if (FlagGet(FLAG_BADGE01_GET + i)) count++;
    return count;
}
void OpenWorld_CountBadges(void)
{
    gSpecialVar_Result = OpenWorld_BadgeCount();
}
u8 OpenWorld_GymLevel(u16 trainer, u8 slot, u8 originalLevel)
{
    u16 i;
    u8 count = OpenWorld_BadgeCount();
    if (count > 7) count = 7;
    for (i = 0; i < ARRAY_COUNT(sGymTrainers); i++) {
        const struct GymTrainer *gym = &sGymTrainers[i];
        if (gym->trainer == trainer) {
            u8 gap = gym->highest > originalLevel ? gym->highest - originalLevel : 0;
            if (gap > 6) gap = 6;
            return sAceLevels[count] - (gym->leader ? 0 : 2) - gap;
        }
    }
    return originalLevel;
}
u8 OpenWorld_TrainerPic(u16 trainer)
{
    u8 cls = gTrainers[trainer].trainerClass;
    if (cls == TRAINER_CLASS_RIVAL_EARLY || cls == TRAINER_CLASS_RIVAL_LATE || cls == TRAINER_CLASS_CHAMPION)
        return gSaveBlock2Ptr->playerGender == MALE ? TRAINER_PIC_LEAF : TRAINER_PIC_RED;
    return gTrainers[trainer].trainerPic;
}
