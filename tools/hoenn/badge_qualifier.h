#ifndef GUARD_JOURNEY_BADGE_QUALIFIER_H
#define GUARD_JOURNEY_BADGE_QUALIFIER_H

#include "global.h"
#include "journey_qualifier_core.h"

struct Trainer;
bool32 JourneyQualifierWon(void);
void JourneyQualifierAvailable(void);
void JourneyQualifierBegin(void);
void JourneyQualifierCheckActive(void);
void JourneyQualifierBufferStandings(void);
void JourneyQualifierNext(void);
void JourneyQualifierPrepareBattle(void);
void JourneyQualifierFinishBattle(void);
void JourneyQualifierAbort(void);
void JourneyQualifierComplete(void);
void JourneyQualifierRestoreParty(void);
void JourneyQualifierOpponent(void);
u32 JourneyQualifierOpponentHero(void);
const u8 *JourneyQualifierOpponentName(void);
u16 JourneyQualifierCurrentTrainer(void);
const struct JourneyQualifierCore *JourneyQualifierState(void);
bool32 JourneyQualifierBattleReady(void);
void JourneyQualifierBattleStarted(void);
void JourneyQualifierBattleReturned(void);
bool32 JourneyQualifierTrainer(const struct Trainer *);
u32 JourneyQualifierTrainerLevel(const struct Trainer *, u32 originalLevel);
void BattleSetup_StartQualifierBattle(void);

#endif
