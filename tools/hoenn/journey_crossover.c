#include "global.h"
#include "pokemon.h"
#include "event_data.h"
#include "event_object_movement.h"
#include "field_player_avatar.h"
#include "fieldmap.h"
#include "metatile_behavior.h"
#include "script.h"
#include "constants/maps.h"
#include "constants/flags.h"
#include "constants/vars.h"
#include "constants/event_objects.h"
#include "constants/event_object_movement.h"

#define JOURNEY_RIVAL_VISITS 0x40FF
#define JOURNEY_GALACTIC_STATE 0x40FE
#define JOURNEY_RIVAL_LOCALID 240
struct JourneyCrossoverLocation { u16 map; u16 gfx; };
static const struct JourneyCrossoverLocation sJourneyCrossoverLocations[] = {
    {MAP_ROUTE4, OBJ_EVENT_GFX_JOURNEY_EREN},
    {MAP_ROUTE10, OBJ_EVENT_GFX_JOURNEY_EREN},
    {MAP_ROUTE17, OBJ_EVENT_GFX_JOURNEY_EREN},
    {MAP_ROUTE112, OBJ_EVENT_GFX_JOURNEY_EREN},
    {MAP_ROUTE113, OBJ_EVENT_GFX_JOURNEY_EREN},
    {MAP_PETALBURG_WOODS, OBJ_EVENT_GFX_JOURNEY_EREN},
    {MAP_ROUTE6, OBJ_EVENT_GFX_JOURNEY_LUFFY},
    {MAP_ROUTE13, OBJ_EVENT_GFX_JOURNEY_LUFFY},
    {MAP_ROUTE20, OBJ_EVENT_GFX_JOURNEY_LUFFY},
    {MAP_ROUTE106, OBJ_EVENT_GFX_JOURNEY_LUFFY},
    {MAP_ROUTE108, OBJ_EVENT_GFX_JOURNEY_LUFFY},
    {MAP_ROUTE125, OBJ_EVENT_GFX_JOURNEY_LUFFY},
};
extern const u8 JourneyCrossover_Encounter[];
static EWRAM_DATA u8 sJourneyCrossoverActive = 0;

u32 JourneyCrossoverCount(u32 hero)
{
    u16 visits = VarGet(JOURNEY_RIVAL_VISITS) >> (hero ? 6 : 0);
    u32 count = 0;
    for (u32 i=0; i<6; i++) count += (visits >> i) & 1;
    return count;
}

bool8 JourneyCrossoverTryEncounter(void)
{
    s16 x,y;
    static const s8 directions[][2]={{-1,0},{1,0},{0,-1},{0,1}};
    if (!FlagGet(FLAG_SYS_POKEMON_GET) || VarGet(JOURNEY_GALACTIC_STATE)>=4)
        return FALSE;
    PlayerGetDestCoords(&x,&y);
    if (MetatileBehavior_IsSurfableWaterOrUnderwater(MapGridGetMetatileBehaviorAt(x,y)))
        return FALSE;
    for (u32 i=0;i<ARRAY_COUNT(sJourneyCrossoverLocations);i++)
    {
        const struct JourneyCrossoverLocation *entry=&sJourneyCrossoverLocations[i];
        if (MAP_GROUP(entry->map)!=gSaveBlock1Ptr->location.mapGroup || MAP_NUM(entry->map)!=gSaveBlock1Ptr->location.mapNum
            || (VarGet(JOURNEY_RIVAL_VISITS)&(1<<i))) continue;
        for (u32 d=0;d<ARRAY_COUNT(directions);d++)
        {
            s16 xx=x+2*directions[d][0],yy=y+2*directions[d][1];
            s16 middleX=x+directions[d][0],middleY=y+directions[d][1];
            if (xx<7 || yy<7 || xx>=gMapHeader.mapLayout->width+7 || yy>=gMapHeader.mapLayout->height+7
                || MapGridGetCollisionAt(xx,yy) || MapGridGetCollisionAt(middleX,middleY)
                || MapGridGetElevationAt(xx,yy)!=MapGridGetElevationAt(x,y)
                || MapGridGetElevationAt(middleX,middleY)!=MapGridGetElevationAt(x,y)
                || GetObjectEventIdByXY(xx,yy)!=OBJECT_EVENTS_COUNT
                || GetObjectEventIdByXY(middleX,middleY)!=OBJECT_EVENTS_COUNT) continue;
            u8 id=SpawnSpecialObjectEventParameterized(entry->gfx,MOVEMENT_TYPE_FACE_DOWN,JOURNEY_RIVAL_LOCALID,xx-7,yy-7,MapGridGetElevationAt(xx,yy));
            if (id>=OBJECT_EVENTS_COUNT) return FALSE;
            sJourneyCrossoverActive=i+1;
            gSpecialVar_0x8007=d;
            ScriptContext_SetupScript(JourneyCrossover_Encounter);
            return TRUE;
        }
    }
    return FALSE;
}
void JourneyCrossoverInfo(void)
{
    u32 index=sJourneyCrossoverActive ? sJourneyCrossoverActive-1 : 0;
    u32 hero=index>=6;
    gSpecialVar_Result=JourneyCrossoverCount(hero)+6*hero;
}
void JourneyCrossoverFinish(void)
{
    if (sJourneyCrossoverActive)
        VarSet(JOURNEY_RIVAL_VISITS,VarGet(JOURNEY_RIVAL_VISITS)|(1<<(sJourneyCrossoverActive-1)));
    RemoveObjectEventByLocalIdAndMap(JOURNEY_RIVAL_LOCALID,gSaveBlock1Ptr->location.mapNum,gSaveBlock1Ptr->location.mapGroup);
    sJourneyCrossoverActive=0;
}
