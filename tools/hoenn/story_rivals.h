#ifndef GUARD_JOURNEY_STORY_RIVALS_H
#define GUARD_JOURNEY_STORY_RIVALS_H

#include "global.h"
#include "constants/trainers.h"

enum JourneyStoryHero
{
    JOURNEY_HERO_RED = 1,
    JOURNEY_HERO_LEAF,
    JOURNEY_HERO_BRENDAN,
    JOURNEY_HERO_MAY,
};

// Slots are stable roles shared by the story qualifier and native encounters.
// 0: opposite sex at home; 1: opposite sex away; 2: same sex away.
u32 JourneyStoryPlayerHero(void);
u32 JourneyStoryRivalHero(u32 slot);
const u8 *JourneyStoryHeroName(u32 hero);
u16 JourneyStoryHeroGraphics(u32 hero);
enum TrainerPicID JourneyStoryHeroTrainerPic(u32 hero);

// Zero means an unrelated trainer; never substitute Wally, gym Blue or PWT.
u32 JourneyStoryNativeTrainerHero(u16 trainerId);
u32 JourneyStoryCurrentRivalHero(void);
const u8 *JourneyStoryTrainerName(u16 trainerId);
enum TrainerPicID JourneyStoryTrainerPic(u16 trainerId);
u16 JourneyStoryRivalGraphics(u16 graphicsId);

#endif
