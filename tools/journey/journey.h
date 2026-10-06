#ifndef GUARD_JOURNEY_H
#define GUARD_JOURNEY_H
#define VAR_JOURNEY_CITY 0x40CB
#define VAR_JOURNEY_HOME 0x40CC
#define VAR_JOURNEY_GIFTS 0x40CD
#define VAR_JOURNEY_STAGE 0x40CE
#define FLAG_JOURNEY_HIDE_VISITOR 0x8E0
#define FLAG_JOURNEY_STARTER_RECEIVED 0x8E1
struct MapHeader;
const struct MapHeader *JourneyHomeHeader(u16 group, u16 number);
void JourneyChooseHome(void);
void JourneyWarpBedroom(void);
void JourneySetRespawn(void);
void JourneySetupVisitors(void);
void JourneyFamilyInfo(void);
void JourneyGiveGift(void);
void JourneyGiveStarter(void);
#endif
