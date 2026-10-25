/* Host observations of the actual field glue, without modifying its logic. */
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int16_t s16;
typedef bool bool32;
#define TRUE true
#define FALSE false
#define _(s) s
#define COMPOUND_STRING(s) (const u8 *)(s)
#define MAP_GROUP(n) ((n) >> 8)
#define MAP_NUM(n) ((n) & 255)
#define MAP_BATTLE_FRONTIER_OUTSIDE_WEST 0x0102
#define MAP_JOURNEY_PWT_ARENA 0x0304
#define MAP_OFFSET 7
#define MOVEMENT_TYPE_FACE_LEFT 1
#define OBJECT_EVENTS_COUNT 16
#define OBJ_EVENT_GFX_JOURNEY_LUFFY 501
#define OBJ_EVENT_GFX_JOURNEY_EREN 502
#define VAR_OBJ_GFX_ID_0 0x4010
#define VAR_JOURNEY_QUALIFIER_STATE 0x40DB
#define VAR_JOURNEY_GALACTIC_STATE 0x40DA
#define FLAG_JOURNEY_QUALIFIER_CELEBRATED 0x1051
#define FLAG_JOURNEY_QUALIFIER_NOTIFIED 0x1052
#define FLAG_JOURNEY_GALACTIC_NOTIFIED 0x1053
#define JOURNEY_QUALIFIER_FINAL 1

struct ObjectEventTemplate { u8 localId; };
struct JourneyQualifierCore { u8 stage; };
static struct { struct { u8 mapGroup, mapNum; } location; } saveBlock;
static __typeof__(saveBlock) *gSaveBlock1Ptr = &saveBlock;
static struct JourneyQualifierCore core;
static u8 gStringVar1[100];
static u32 gSpecialVar_Result, gSpecialVar_0x8004, gSpecialVar_LastTalked;
static u16 variables[0x5000];
static bool flags[0x2000], won;
static u32 badgeCount, aborts, opponentHero, collision, objectAtCell, spawnResult;
static u32 removeCount, spawnCount, spawnedGraphics, spawnedLocal, spawnedMovement;
static s16 playerX, playerY, spawnedX, spawnedY;
static u8 roleHeroes[3] = {4, 2, 3};
static u16 VarGet(u16 v) { return variables[v]; }
static void VarSet(u16 v, u16 value) { variables[v] = value; }
static bool32 FlagGet(u16 f) { return flags[f]; }
static void FlagSet(u16 f) { flags[f] = true; }
static bool32 JourneyQualifierWon(void) { return won; }
static u32 JourneyTotalBadgeCount(void) { return badgeCount; }
static void JourneyQualifierAbort(void) { aborts++; variables[VAR_JOURNEY_QUALIFIER_STATE] = 0; }
static u32 JourneyStoryRivalHero(u32 role) { assert(role < 3); return roleHeroes[role]; }
static u16 JourneyStoryHeroGraphics(u32 hero) { return 100 + hero; }
static const u8 *JourneyStoryHeroName(u32 hero)
{
    static const u8 *names[] = {COMPOUND_STRING("None"), COMPOUND_STRING("Red"),
        COMPOUND_STRING("Leaf"), COMPOUND_STRING("Brendan"), COMPOUND_STRING("May")};
    assert(hero < 5); return names[hero];
}
static void PlayerGetDestCoords(s16 *x, s16 *y) { *x = playerX; *y = playerY; }
static u8 *StringCopy(u8 *dst, const u8 *src) { return (u8 *)strcpy((char *)dst, (const char *)src); }
static void RemoveObjectEventByLocalIdAndMap(u8 local, u8 map, u8 group)
{
    assert(local >= 14 && local <= 30);
    assert(map == saveBlock.location.mapNum && group == saveBlock.location.mapGroup);
    removeCount++;
}
static u32 JourneyQualifierOpponentHero(void) { return opponentHero; }
static u8 MapGridGetCollisionAt(s16 x, s16 y)
{
    assert(x == 24 && y == 13); return collision;
}
static u8 GetObjectEventIdByXY(s16 x, s16 y)
{
    assert(x == 24 && y == 13); return objectAtCell;
}
static u8 MapGridGetElevationAt(s16 x, s16 y)
{
    assert(x == 24 && y == 13); return 3;
}
static u8 SpawnSpecialObjectEventParameterized(u16 gfx, u8 movement, u8 local, s16 x, s16 y, u8 elevation)
{
    assert(elevation == 3); spawnCount++; spawnedGraphics = gfx;
    spawnedMovement = movement; spawnedLocal = local; spawnedX = x; spawnedY = y;
    return spawnResult;
}
static const struct JourneyQualifierCore *JourneyQualifierState(void) { return &core; }
static const u8 *JourneyQualifierOpponentName(void) { return COMPOUND_STRING("Eren"); }

/* The test runner inserts the unedited field implementation here. */
/* FIELD_IMPLEMENTATION */

static void outside(void)
{
    saveBlock.location.mapGroup = MAP_GROUP(MAP_BATTLE_FRONTIER_OUTSIDE_WEST);
    saveBlock.location.mapNum = MAP_NUM(MAP_BATTLE_FRONTIER_OUTSIDE_WEST);
}

int main(void)
{
    struct ObjectEventTemplate actor;
    outside();
    for (badgeCount = 0; badgeCount <= 24; badgeCount++)
        for (u32 celebrated = 0; celebrated <= 1; celebrated++)
            for (u32 local = 1; local <= 32; local++)
            {
                actor.localId = local;
                flags[FLAG_JOURNEY_QUALIFIER_CELEBRATED] = celebrated;
                bool expected = local < 26 || local > 30
                    || (badgeCount >= 18 && (!celebrated || local == 26));
                assert(JourneyQualifierFieldObjectVisible(&actor, 1, 2) == expected);
                assert(JourneyQualifierFieldObjectVisible(&actor, 1, 3));
            }
    memset(flags, 0, sizeof(flags));
    badgeCount = 18; variables[VAR_JOURNEY_QUALIFIER_STATE] = 1;
    JourneyQualifierFieldSetup();
    assert(aborts == 1 && variables[VAR_JOURNEY_QUALIFIER_STATE] == 0);
    variables[VAR_JOURNEY_QUALIFIER_STATE] = 4;
    JourneyQualifierFieldSetup();
    assert(aborts == 1 && variables[VAR_JOURNEY_QUALIFIER_STATE] == 4);
    assert(variables[VAR_OBJ_GFX_ID_0] == 104);
    assert(variables[VAR_OBJ_GFX_ID_0 + 1] == 102);
    assert(variables[VAR_OBJ_GFX_ID_0 + 2] == 103);
    won = true; JourneyQualifierFieldSetup();
    assert(variables[VAR_JOURNEY_QUALIFIER_STATE] == 2);
    JourneyQualifierFieldCanCelebrate(); assert(gSpecialVar_Result);
    JourneyQualifierFieldFinishCelebration();
    assert(gSpecialVar_Result && flags[FLAG_JOURNEY_QUALIFIER_CELEBRATED]);
    assert(removeCount == 4 && variables[VAR_JOURNEY_QUALIFIER_STATE] == 3);
    JourneyQualifierFieldCanCelebrate(); assert(!gSpecialVar_Result);
    JourneyQualifierFieldSetup(); assert(variables[VAR_JOURNEY_QUALIFIER_STATE] == 3);
    playerX = 33; playerY = 74;
    JourneyQualifierFieldNeedsGather(); assert(!gSpecialVar_Result);
    playerY--; JourneyQualifierFieldNeedsGather(); assert(gSpecialVar_Result);
    for (u32 role = 0; role < 5; role++)
    {
        gSpecialVar_0x8004 = role; JourneyQualifierFieldSpeaker();
        assert(gSpecialVar_Result == (role < 3 ? roleHeroes[role] : role + 2));
        assert(gSpecialVar_LastTalked == role + 26);
        assert(gStringVar1[0]);
    }
    for (u32 badges = 0; badges <= 24; badges++)
        for (u32 victory = 0; victory <= 1; victory++)
            for (u32 galactic = 0; galactic <= 7; galactic++)
            {
                memset(flags, 0, sizeof(flags)); badgeCount = badges; won = victory;
                variables[VAR_JOURNEY_GALACTIC_STATE] = galactic;
                JourneyBadgeStoryNotice();
                assert(gSpecialVar_Result == ((badges >= 18 && !victory ? 1 : 0)
                    | (badges >= 22 && galactic < 7 ? 2 : 0)));
                JourneyBadgeStoryNotice(); assert(!gSpecialVar_Result);
            }
    saveBlock.location.mapGroup = MAP_GROUP(MAP_JOURNEY_PWT_ARENA);
    saveBlock.location.mapNum = MAP_NUM(MAP_JOURNEY_PWT_ARENA);
    objectAtCell = OBJECT_EVENTS_COUNT; spawnResult = OBJECT_EVENTS_COUNT;
    opponentHero = 6; collision = 1;
    JourneyQualifierFieldOpponentEnter(); assert(!gSpecialVar_Result && !spawnCount);
    collision = 0; objectAtCell = 0;
    JourneyQualifierFieldOpponentEnter(); assert(!gSpecialVar_Result && !spawnCount);
    objectAtCell = OBJECT_EVENTS_COUNT;
    JourneyQualifierFieldOpponentEnter(); assert(!gSpecialVar_Result && spawnCount == 1);
    spawnResult = 7;
    JourneyQualifierFieldOpponentEnter(); assert(gSpecialVar_Result && spawnCount == 2);
    assert(spawnedGraphics == OBJ_EVENT_GFX_JOURNEY_EREN && spawnedLocal == 14);
    assert(spawnedMovement == MOVEMENT_TYPE_FACE_LEFT && spawnedX == 24 && spawnedY == 13);
    opponentHero = 7;
    JourneyQualifierFieldOpponentEnter(); assert(!gSpecialVar_Result && spawnCount == 2);
    core.stage = JOURNEY_QUALIFIER_FINAL;
    JourneyQualifierFieldRound(); assert(!strcmp((char *)gStringVar1, "Eren"));
    return 0;
}
