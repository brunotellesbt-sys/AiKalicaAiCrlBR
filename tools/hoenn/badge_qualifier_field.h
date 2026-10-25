#ifndef GUARD_JOURNEY_QUALIFIER_FIELD_H
#define GUARD_JOURNEY_QUALIFIER_FIELD_H

#include "global.h"

struct ObjectEventTemplate;
void JourneyQualifierFieldSetup(void);
bool32 JourneyQualifierFieldObjectVisible(const struct ObjectEventTemplate *, u8 mapGroup, u8 mapNum);
void JourneyQualifierFieldNeedsGather(void);
void JourneyQualifierFieldSpeaker(void);
void JourneyQualifierFieldCanCelebrate(void);
void JourneyQualifierFieldFinishCelebration(void);
void JourneyQualifierFieldGalacticPending(void);
void JourneyQualifierFieldOpponentEnter(void);
void JourneyQualifierFieldOpponentExit(void);
void JourneyQualifierFieldRound(void);
void JourneyBadgeStoryNotice(void);

#endif
