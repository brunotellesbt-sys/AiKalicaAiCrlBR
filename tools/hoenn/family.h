#ifndef GUARD_JOURNEY_FAMILY_H
#define GUARD_JOURNEY_FAMILY_H
const struct MapHeader *JourneyFamilyHomeHeader(u16 group, u16 number);
void JourneyFamilyChooseHome(void);
void JourneyFamilyCanChooseCity(void);
void JourneyFamilyWarpBedroom(void);
void JourneyFamilySetupVisitors(void);
void JourneyFamilyInfo(void);
void JourneyFamilyGiveGift(void);
void JourneyFamilyGiveStarter(void);
void JourneyFamilyVisitorIds(void);
#endif
