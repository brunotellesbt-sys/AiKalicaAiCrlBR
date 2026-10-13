#include "global.h"
#include "journey_pwt.h"
#include "journey_pwt_cup.h"
#include "event_data.h"
#include "event_object_movement.h"
#include "constants/event_objects.h"
#include "constants/event_object_movement.h"

#include "data/journey_pwt_walking.h"
bool32 JourneyPWTWalkingAvailable(u32 trainer)
{ return trainer < ARRAY_COUNT(sPWTWalking) && sPWTWalking[trainer] != 0xFFFF; }
void JourneyPWTExit(void)
{
    RemoveObjectEventByLocalIdAndMap(14,gSaveBlock1Ptr->location.mapNum,gSaveBlock1Ptr->location.mapGroup);
}
void JourneyPWTEntrance(void)
{
    const struct JourneyCup *cup=JourneyPWTCupState();
    JourneyPWTExit();gSpecialVar_Result=FALSE;
    if(cup->opponent>=cup->count)return;
    u32 trainer=cup->entrants[cup->opponent];
    if(!JourneyPWTWalkingAvailable(trainer))return;
    u8 event=SpawnSpecialObjectEventParameterized(sPWTWalking[trainer],MOVEMENT_TYPE_FACE_LEFT,14,17,6,0);
    gSpecialVar_Result=event<OBJECT_EVENTS_COUNT;
}
