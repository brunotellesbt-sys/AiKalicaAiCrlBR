#ifndef GUARD_JOURNEY_BIRTH_H
#define GUARD_JOURNEY_BIRTH_H
bool32 JourneyBirthIsBoat(void);
void JourneyBirthArrivalVehicle(void);
void JourneyBirthRegion(void);
void JourneyBirthChooseCity(void);
void JourneyBirthTruckDestination(void);
bool32 JourneyBirthMenuFinished(void);
bool32 JourneyBirthTryArrival(void);
void JourneyBirthSpawnArrival(void);
void JourneyBirthRemoveArrival(void);
void JourneyBirthHomeRegion(void);
void JourneyBirthGiveHomeStarter(void);
void JourneyBirthVisitOak(void);
void JourneyBirthGiveKantoVisitStarter(void);
void JourneyBirthCheckPartySpace(void);
void JourneyBirthRecordHoennStarter(void);
extern const u8 JourneyBirth_ChooseCity[];
#endif
