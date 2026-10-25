#include "global.h"
#include "journey_extra_gyms.h"
#include "fieldmap.h"
#include "field_camera.h"
#include "journey_crossover.h"
#include "event_object_movement.h"
#include "constants/event_objects.h"
#include "constants/event_object_movement.h"
#include "journey_galactic.h"
#include "journey_gym_scaling.h"
#include "journey_team_missions.h"
#include "journey_story_continuity.h"
#include "event_data.h"
#include "constants/vars.h"
#include "constants/flags.h"
#include "constants/species.h"
#include "constants/opponents.h"
#include "constants/maps.h"
bool32 JourneyGalacticLeagueReady(void) { return JourneyTotalBadgeCount()==24 && JourneyCrossoverComplete() && VarGet(VAR_JOURNEY_GALACTIC_STATE)>=7 && JourneyPendingCampaignEvent(TRUE)==0 && JourneyPendingCampaignEvent(FALSE)==0; }
void JourneyGalacticAvailable(void) { gSpecialVar_Result=JourneyGymBadgeCount(TRUE)==8 && JourneyGymBadgeCount(FALSE)==8; }
void JourneyGalacticOtherMissions(void) { gSpecialVar_Result=JourneyPendingCampaignEvent(TRUE)!=0 || JourneyPendingCampaignEvent(FALSE)!=0; }
bool32 JourneyGalacticCaptureLocked(u32 species) { return (species==SPECIES_DIALGA || species==SPECIES_PALKIA || species==SPECIES_GIRATINA || species==SPECIES_GIRATINA_ORIGIN) && VarGet(VAR_JOURNEY_GALACTIC_STATE)<7; }
bool32 JourneyGalacticNoCatch(void) { return gSaveBlock1Ptr->location.mapGroup==MAP_GROUP(MAP_JOURNEYGALACTICHALL) && gSaveBlock1Ptr->location.mapNum==MAP_NUM(MAP_JOURNEYGALACTICHALL) && VarGet(VAR_JOURNEY_GALACTIC_STATE)==3; }
void JourneyGalacticGruntsCleared(void) {
 static const u16 ids[]={TRAINER_JOURNEY_GALACTIC_BULKHEAD_GUARD,TRAINER_JOURNEY_GALACTIC_GRUNT_0,TRAINER_JOURNEY_GALACTIC_GRUNT_1,TRAINER_JOURNEY_GALACTIC_GRUNT_2,TRAINER_JOURNEY_GALACTIC_GRUNT_3,TRAINER_JOURNEY_GALACTIC_GRUNT_4,TRAINER_JOURNEY_GALACTIC_GRUNT_5,TRAINER_JOURNEY_GALACTIC_GRUNT_6,TRAINER_JOURNEY_GALACTIC_GRUNT_7,TRAINER_JOURNEY_GALACTIC_GRUNT_8,TRAINER_JOURNEY_GALACTIC_GRUNT_9,TRAINER_JOURNEY_GALACTIC_GRUNT_10,TRAINER_JOURNEY_GALACTIC_GRUNT_11,TRAINER_JOURNEY_GALACTIC_GRUNT_12,TRAINER_JOURNEY_GALACTIC_GRUNT_13,TRAINER_JOURNEY_GALACTIC_GRUNT_14,TRAINER_JOURNEY_GALACTIC_GRUNT_15,TRAINER_JOURNEY_GALACTIC_GRUNT_16,TRAINER_JOURNEY_GALACTIC_GRUNT_17};
 gSpecialVar_Result=TRUE;
 for(u32 i=0;i<ARRAY_COUNT(ids);i++) { u16 flag=TRAINER_FLAGS_START+ids[i]; if(!(gSaveBlock1Ptr->flags[flag/8]&(1<<(flag&7))))gSpecialVar_Result=FALSE; }
}

extern const u8 JourneyGalactic_Observer[], JourneyGalactic_Cyrus[], JourneyGalactic_Gate[];
extern const u8 JourneyGalactic_GALACTIC_GRUNT_0[];
extern const u8 JourneyGalactic_GALACTIC_GRUNT_1[];
extern const u8 JourneyGalactic_GALACTIC_GRUNT_2[];
extern const u8 JourneyGalactic_GALACTIC_GRUNT_3[];
extern const u8 JourneyGalactic_GALACTIC_GRUNT_4[];
extern const u8 JourneyGalactic_GALACTIC_GRUNT_5[];
extern const u8 JourneyGalactic_GALACTIC_GRUNT_6[];
extern const u8 JourneyGalactic_GALACTIC_GRUNT_7[];
extern const u8 JourneyGalactic_GALACTIC_GRUNT_8[];
extern const u8 JourneyGalactic_GALACTIC_GRUNT_9[];
extern const u8 JourneyGalactic_GALACTIC_GRUNT_10[];
extern const u8 JourneyGalactic_GALACTIC_GRUNT_11[];
extern const u8 JourneyGalactic_GALACTIC_GRUNT_12[];
extern const u8 JourneyGalactic_GALACTIC_GRUNT_13[];
extern const u8 JourneyGalactic_GALACTIC_GRUNT_14[];
extern const u8 JourneyGalactic_GALACTIC_GRUNT_15[];
extern const u8 JourneyGalactic_GALACTIC_GRUNT_16[];
extern const u8 JourneyGalactic_GALACTIC_GRUNT_17[];

bool32 JourneyGalacticObjectVisible(const struct ObjectEventTemplate *o,u8 group,u8 num)
{
 const u8 *script=o->script;
 if(group==MAP_GROUP(MAP_SILPH_CO_11F) && num==MAP_NUM(MAP_SILPH_CO_11F)
    && o->graphicsId==OBJ_EVENT_GFX_GIOVANNI)
     return JourneyPendingCampaignEvent(TRUE)==2;

 if(group!=MAP_GROUP(MAP_JOURNEYGALACTICHALL) || num!=MAP_NUM(MAP_JOURNEYGALACTICHALL))
 {
  extern const u8 JourneySanctuary_483[],JourneySanctuary_484[],JourneySanctuary_487[];
  if((script==JourneySanctuary_483 || script==JourneySanctuary_484 || script==JourneySanctuary_487) && VarGet(VAR_JOURNEY_GALACTIC_STATE)<7)return FALSE;
 }

 u16 state=VarGet(VAR_JOURNEY_GALACTIC_STATE);
 // Special objects spawned by an approach scene have no template script.
 if(script==NULL)return TRUE;
 if(group==MAP_GROUP(MAP_JOURNEYGALACTICHALL) && num==MAP_NUM(MAP_JOURNEYGALACTICHALL))
 {
  if(state>=7)return FALSE;
  if(o->localId==6 && state<1)return FALSE;
  if(o->localId==7 && state<2)return FALSE;
 }
 static const u8 *const gruntScripts[]={JourneyGalactic_GALACTIC_GRUNT_0,JourneyGalactic_GALACTIC_GRUNT_1,JourneyGalactic_GALACTIC_GRUNT_2,JourneyGalactic_GALACTIC_GRUNT_3,JourneyGalactic_GALACTIC_GRUNT_4,JourneyGalactic_GALACTIC_GRUNT_5,JourneyGalactic_GALACTIC_GRUNT_6,JourneyGalactic_GALACTIC_GRUNT_7,JourneyGalactic_GALACTIC_GRUNT_8,JourneyGalactic_GALACTIC_GRUNT_9,JourneyGalactic_GALACTIC_GRUNT_10,JourneyGalactic_GALACTIC_GRUNT_11,JourneyGalactic_GALACTIC_GRUNT_12,JourneyGalactic_GALACTIC_GRUNT_13,JourneyGalactic_GALACTIC_GRUNT_14,JourneyGalactic_GALACTIC_GRUNT_15,JourneyGalactic_GALACTIC_GRUNT_16,JourneyGalactic_GALACTIC_GRUNT_17};
 for(u32 i=0;i<ARRAY_COUNT(gruntScripts);i++)
  if(script==gruntScripts[i])return JourneyGymBadgeCount(TRUE)==8 && JourneyGymBadgeCount(FALSE)==8 && state<7;
 return TRUE;
}
static void PlaceHero(u16 gfx,u8 localId,s16 x,s16 y)
{
 if(GetObjectEventIdByLocalIdAndMap(localId,gSaveBlock1Ptr->location.mapNum,gSaveBlock1Ptr->location.mapGroup)==OBJECT_EVENTS_COUNT)
  SpawnSpecialObjectEventParameterized(gfx,MOVEMENT_TYPE_FACE_UP,localId,x+MAP_OFFSET,y+MAP_OFFSET,3);
 else TryMoveObjectEventToMapCoords(localId,gSaveBlock1Ptr->location.mapNum,gSaveBlock1Ptr->location.mapGroup,x,y);
}
void JourneyGalacticBringEren(void) { PlaceHero(OBJ_EVENT_GFX_JOURNEY_EREN,6,10,26); }
void JourneyGalacticBringLuffy(void) { PlaceHero(OBJ_EVENT_GFX_JOURNEY_LUFFY,7,20,26); }
void JourneyGalacticSyncHeroes(void)
{
 u16 state=VarGet(VAR_JOURNEY_GALACTIC_STATE);
 if(state>=1 && state<7)PlaceHero(OBJ_EVENT_GFX_JOURNEY_EREN,6,13,8);
 if(state>=2 && state<7)PlaceHero(OBJ_EVENT_GFX_JOURNEY_LUFFY,7,17,8);
}

void JourneyGalacticCellState(void)
{
    if(VarGet(VAR_JOURNEY_GALACTIC_STATE)<4)return;
    static const u8 centers[]={6,15,24};
    for(u32 i=0;i<3;i++)for(u32 y=2;y<=6;y++)for(u32 x=centers[i]-2;x<=centers[i]+2;x++)
        MapGridSetMetatileIdAt(x+7,y+7,776+(y%2)*2+x%2);
    DrawWholeMapView();
}
