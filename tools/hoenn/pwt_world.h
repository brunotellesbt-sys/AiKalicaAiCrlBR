#ifndef GUARD_JOURNEY_PWT_H
#define GUARD_JOURNEY_PWT_H
struct JourneyCup;
void JourneyPWTMenu(void);
void JourneyPWTBoard(void);
void JourneyPWTChoose(void);
void JourneyPWTBegin(void);
void JourneyPWTBufferBracket(void);
void JourneyPWTBufferRound(void);
void JourneyPWTPrepareBattle(void);
void JourneyPWTAdvance(void);
void JourneyPWTFinish(void);
void JourneyPWTActive(void);
bool8 JourneyPWTSelectionActive(void);
u32 JourneyPWTMaxGeneration(void);
u32 JourneyPWTCatalogCount(void);
bool32 JourneyPWTTrainerEligible(u32,u32);
u16 JourneyPWTRosterSpecies(u32,u32);
const struct JourneyCup *JourneyPWTCupState(void);
const u8 *JourneyPWTEntrantName(u32);
u16 JourneyPWTCurrentTrainer(void);
void BattleSetup_StartPWTBattle(void);
#endif
