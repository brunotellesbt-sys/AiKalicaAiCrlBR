#include "global.h"
#include "journey_qualifier_field.h"
#include "journey_badge_qualifier.h"
#include "journey_story_rivals.h"
#include "journey_extra_gyms.h"
#include "event_data.h"
#include "event_object_movement.h"
#include "field_player_avatar.h"
#include "fieldmap.h"
#include "string_util.h"
#include "constants/event_objects.h"
#include "constants/event_object_movement.h"
#include "constants/flags.h"
#include "constants/maps.h"
#include "constants/vars.h"

#define FIRST_QUALIFIER_LOCALID 26
#define QUALIFIER_OPPONENT_LOCALID 14
#define QUALIFIER_LUFFY 5
#define QUALIFIER_EREN 6
#define QUALIFIER_PENDING_GATHER 4

static const u8 sLuffyName[] = _("Luffy");
static const u8 sErenName[] = _("Eren");

static bool32 OutsideWest(void)
{
    return gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(MAP_BATTLE_FRONTIER_OUTSIDE_WEST)
        && gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_BATTLE_FRONTIER_OUTSIDE_WEST);
}

static bool32 Arena(void)
{
    return gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(MAP_JOURNEY_PWT_ARENA)
        && gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_JOURNEY_PWT_ARENA);
}

static u32 SpeakerHero(u32 speaker)
{
    return speaker < 3 ? JourneyStoryRivalHero(speaker)
        : speaker == 3 ? QUALIFIER_LUFFY : QUALIFIER_EREN;
}

static u16 HeroGraphics(u32 hero)
{
    if (hero == QUALIFIER_LUFFY) return OBJ_EVENT_GFX_JOURNEY_LUFFY;
    if (hero == QUALIFIER_EREN) return OBJ_EVENT_GFX_JOURNEY_EREN;
    return JourneyStoryHeroGraphics(hero);
}

static const u8 *HeroName(u32 hero)
{
    if (hero == QUALIFIER_LUFFY) return sLuffyName;
    if (hero == QUALIFIER_EREN) return sErenName;
    return JourneyStoryHeroName(hero);
}

void JourneyQualifierFieldSetup(void)
{
    for (u32 role = 0; role < 3; role++)
        VarSet(VAR_OBJ_GFX_ID_0 + role, JourneyStoryHeroGraphics(JourneyStoryRivalHero(role)));
    if (!OutsideWest()) return;
    if (JourneyQualifierWon())
        VarSet(VAR_JOURNEY_QUALIFIER_STATE, FlagGet(FLAG_JOURNEY_QUALIFIER_CELEBRATED) ? 3 : 2);
    else if (VarGet(VAR_JOURNEY_QUALIFIER_STATE)
        && VarGet(VAR_JOURNEY_QUALIFIER_STATE) != QUALIFIER_PENDING_GATHER)
        JourneyQualifierAbort();
}

bool32 JourneyQualifierFieldObjectVisible(const struct ObjectEventTemplate *object, u8 mapGroup, u8 mapNum)
{
    if (mapGroup != MAP_GROUP(MAP_BATTLE_FRONTIER_OUTSIDE_WEST)
        || mapNum != MAP_NUM(MAP_BATTLE_FRONTIER_OUTSIDE_WEST)
        || object->localId < FIRST_QUALIFIER_LOCALID || object->localId >= FIRST_QUALIFIER_LOCALID + 5)
        return TRUE;
    if (JourneyTotalBadgeCount() < 18) return FALSE;
    return !FlagGet(FLAG_JOURNEY_QUALIFIER_CELEBRATED)
        || object->localId == FIRST_QUALIFIER_LOCALID;
}

void JourneyQualifierFieldNeedsGather(void)
{
    s16 x, y;
    PlayerGetDestCoords(&x, &y);
    gSpecialVar_Result = !OutsideWest() || x != 26 + MAP_OFFSET || y != 67 + MAP_OFFSET;
}

void JourneyQualifierFieldSpeaker(void)
{
    u32 speaker = gSpecialVar_0x8004;
    gSpecialVar_Result = 0;
    if (speaker >= 5) return;
    u32 hero = SpeakerHero(speaker);
    StringCopy(gStringVar1, HeroName(hero));
    gSpecialVar_LastTalked = FIRST_QUALIFIER_LOCALID + speaker;
    gSpecialVar_Result = hero;
}

void JourneyQualifierFieldCanCelebrate(void)
{
    gSpecialVar_Result = OutsideWest() && JourneyTotalBadgeCount() >= 18 && JourneyQualifierWon()
        && !FlagGet(FLAG_JOURNEY_QUALIFIER_CELEBRATED)
        && VarGet(VAR_JOURNEY_QUALIFIER_STATE) == 2;
    if (!gSpecialVar_Result && VarGet(VAR_JOURNEY_QUALIFIER_STATE) == 2)
        VarSet(VAR_JOURNEY_QUALIFIER_STATE, JourneyQualifierWon() ? 3 : 0);
}

void JourneyQualifierFieldFinishCelebration(void)
{
    gSpecialVar_Result = FALSE;
    if (!OutsideWest() || !JourneyQualifierWon() || JourneyTotalBadgeCount() < 18) return;
    FlagSet(FLAG_JOURNEY_QUALIFIER_CELEBRATED);
    VarSet(VAR_JOURNEY_QUALIFIER_STATE, 3);
    for (u32 localId = FIRST_QUALIFIER_LOCALID + 1; localId < FIRST_QUALIFIER_LOCALID + 5; localId++)
        RemoveObjectEventByLocalIdAndMap(localId, gSaveBlock1Ptr->location.mapNum,
            gSaveBlock1Ptr->location.mapGroup);
    gSpecialVar_Result = TRUE;
}

void JourneyQualifierFieldGalacticPending(void)
{
    gSpecialVar_Result = JourneyTotalBadgeCount() >= 22 && VarGet(VAR_JOURNEY_GALACTIC_STATE) < 7;
}

void JourneyQualifierFieldOpponentExit(void)
{
    if (Arena()) RemoveObjectEventByLocalIdAndMap(QUALIFIER_OPPONENT_LOCALID,
        gSaveBlock1Ptr->location.mapNum, gSaveBlock1Ptr->location.mapGroup);
}

void JourneyQualifierFieldOpponentEnter(void)
{
    u32 hero = JourneyQualifierOpponentHero();
    gSpecialVar_Result = FALSE;
    if (!Arena() || !hero || hero > QUALIFIER_EREN) return;
    JourneyQualifierFieldOpponentExit();
    const s16 x = 17 + MAP_OFFSET, y = 6 + MAP_OFFSET;
    if (MapGridGetCollisionAt(x, y) || GetObjectEventIdByXY(x, y) != OBJECT_EVENTS_COUNT) return;
    u8 event = SpawnSpecialObjectEventParameterized(HeroGraphics(hero), MOVEMENT_TYPE_FACE_LEFT,
        QUALIFIER_OPPONENT_LOCALID, x, y, MapGridGetElevationAt(x, y));
    gSpecialVar_Result = event < OBJECT_EVENTS_COUNT;
}

void JourneyQualifierFieldRound(void)
{
    const struct JourneyQualifierCore *core = JourneyQualifierState();
    StringCopy(gStringVar1, JourneyQualifierOpponentName());
    StringCopy(gStringVar2, core->stage == JOURNEY_QUALIFIER_FINAL
        ? COMPOUND_STRING("FINAL") : COMPOUND_STRING("GROUP MATCH"));
}

void JourneyBadgeStoryNotice(void)
{
    u32 badges = JourneyTotalBadgeCount(), notices = 0;
    if (badges >= 18 && !JourneyQualifierWon() && !FlagGet(FLAG_JOURNEY_QUALIFIER_NOTIFIED))
    {
        FlagSet(FLAG_JOURNEY_QUALIFIER_NOTIFIED);
        notices |= 1;
    }
    if (badges >= 22 && VarGet(VAR_JOURNEY_GALACTIC_STATE) < 7
        && !FlagGet(FLAG_JOURNEY_GALACTIC_NOTIFIED))
    {
        FlagSet(FLAG_JOURNEY_GALACTIC_NOTIFIED);
        notices |= 2;
    }
    gSpecialVar_Result = notices;
}
