#include "global.h"
#include "data.h"
#include "event_data.h"
#include "journey_birth.h"
#include "journey_story_rivals.h"
#include "constants/event_objects.h"
#include "constants/maps.h"
#include "constants/opponents.h"
#include "constants/regions.h"
#include "constants/vars.h"

struct JourneyNativeRival
{
    u16 trainer;
    bool8 kanto;
    u8 awaySlot;
};

// The explicit list deliberately excludes Wally, gym Blue and PWT trainers.
static const struct JourneyNativeRival sNativeRivals[] = {
    {TRAINER_RIVAL_OAKS_LAB_SQUIRTLE, TRUE, 2},
    {TRAINER_RIVAL_OAKS_LAB_BULBASAUR, TRUE, 2},
    {TRAINER_RIVAL_OAKS_LAB_CHARMANDER, TRUE, 2},
    {TRAINER_RIVAL_ROUTE22_EARLY_SQUIRTLE, TRUE, 2},
    {TRAINER_RIVAL_ROUTE22_EARLY_BULBASAUR, TRUE, 2},
    {TRAINER_RIVAL_ROUTE22_EARLY_CHARMANDER, TRUE, 2},
    {TRAINER_RIVAL_CERULEAN_SQUIRTLE, TRUE, 1},
    {TRAINER_RIVAL_CERULEAN_BULBASAUR, TRUE, 1},
    {TRAINER_RIVAL_CERULEAN_CHARMANDER, TRUE, 1},
    {TRAINER_RIVAL_SS_ANNE_SQUIRTLE, TRUE, 2},
    {TRAINER_RIVAL_SS_ANNE_BULBASAUR, TRUE, 2},
    {TRAINER_RIVAL_SS_ANNE_CHARMANDER, TRUE, 2},
    {TRAINER_RIVAL_POKEMON_TOWER_SQUIRTLE, TRUE, 1},
    {TRAINER_RIVAL_POKEMON_TOWER_BULBASAUR, TRUE, 1},
    {TRAINER_RIVAL_POKEMON_TOWER_CHARMANDER, TRUE, 1},
    {TRAINER_RIVAL_SILPH_SQUIRTLE, TRUE, 2},
    {TRAINER_RIVAL_SILPH_BULBASAUR, TRUE, 2},
    {TRAINER_RIVAL_SILPH_CHARMANDER, TRUE, 2},
    {TRAINER_RIVAL_ROUTE22_LATE_SQUIRTLE, TRUE, 1},
    {TRAINER_RIVAL_ROUTE22_LATE_BULBASAUR, TRUE, 1},
    {TRAINER_RIVAL_ROUTE22_LATE_CHARMANDER, TRUE, 1},
    {TRAINER_CHAMPION_FIRST_SQUIRTLE, TRUE, 2},
    {TRAINER_CHAMPION_FIRST_BULBASAUR, TRUE, 2},
    {TRAINER_CHAMPION_FIRST_CHARMANDER, TRUE, 2},
    {TRAINER_CHAMPION_REMATCH_SQUIRTLE, TRUE, 2},
    {TRAINER_CHAMPION_REMATCH_BULBASAUR, TRUE, 2},
    {TRAINER_CHAMPION_REMATCH_CHARMANDER, TRUE, 2},
    {TRAINER_BRENDAN_ROUTE_103_TREECKO, FALSE, 2},
    {TRAINER_BRENDAN_ROUTE_103_TORCHIC, FALSE, 2},
    {TRAINER_BRENDAN_ROUTE_103_MUDKIP, FALSE, 2},
    {TRAINER_MAY_ROUTE_103_TREECKO, FALSE, 2},
    {TRAINER_MAY_ROUTE_103_TORCHIC, FALSE, 2},
    {TRAINER_MAY_ROUTE_103_MUDKIP, FALSE, 2},
    {TRAINER_BRENDAN_RUSTBORO_TREECKO, FALSE, 1},
    {TRAINER_BRENDAN_RUSTBORO_TORCHIC, FALSE, 1},
    {TRAINER_BRENDAN_RUSTBORO_MUDKIP, FALSE, 1},
    {TRAINER_MAY_RUSTBORO_TREECKO, FALSE, 1},
    {TRAINER_MAY_RUSTBORO_TORCHIC, FALSE, 1},
    {TRAINER_MAY_RUSTBORO_MUDKIP, FALSE, 1},
    {TRAINER_BRENDAN_ROUTE_110_TREECKO, FALSE, 2},
    {TRAINER_BRENDAN_ROUTE_110_TORCHIC, FALSE, 2},
    {TRAINER_BRENDAN_ROUTE_110_MUDKIP, FALSE, 2},
    {TRAINER_MAY_ROUTE_110_TREECKO, FALSE, 2},
    {TRAINER_MAY_ROUTE_110_TORCHIC, FALSE, 2},
    {TRAINER_MAY_ROUTE_110_MUDKIP, FALSE, 2},
    {TRAINER_BRENDAN_ROUTE_119_TREECKO, FALSE, 1},
    {TRAINER_BRENDAN_ROUTE_119_TORCHIC, FALSE, 1},
    {TRAINER_BRENDAN_ROUTE_119_MUDKIP, FALSE, 1},
    {TRAINER_MAY_ROUTE_119_TREECKO, FALSE, 1},
    {TRAINER_MAY_ROUTE_119_TORCHIC, FALSE, 1},
    {TRAINER_MAY_ROUTE_119_MUDKIP, FALSE, 1},
    {TRAINER_BRENDAN_LILYCOVE_TREECKO, FALSE, 2},
    {TRAINER_BRENDAN_LILYCOVE_TORCHIC, FALSE, 2},
    {TRAINER_BRENDAN_LILYCOVE_MUDKIP, FALSE, 2},
    {TRAINER_MAY_LILYCOVE_TREECKO, FALSE, 2},
    {TRAINER_MAY_LILYCOVE_TORCHIC, FALSE, 2},
    {TRAINER_MAY_LILYCOVE_MUDKIP, FALSE, 2},
};

struct JourneyRivalMap
{
    u16 map;
    bool8 kanto;
    u8 awaySlot;
};

// Rival-looking placeholders in the Pyramid and underwater maps are not actors.
// Only the native story maps below resolve the legacy rival graphics tokens.
static const struct JourneyRivalMap sRivalMaps[] = {
    {MAP_PALLET_TOWN_PROFESSOR_OAKS_LAB, TRUE, 2},
    {MAP_ROUTE22, TRUE, 2},
    {MAP_CERULEAN_CITY, TRUE, 1},
    {MAP_SSANNE_2F_CORRIDOR, TRUE, 2},
    {MAP_POKEMON_TOWER_2F, TRUE, 1},
    {MAP_SILPH_CO_7F, TRUE, 2},
    {MAP_POKEMON_LEAGUE_CHAMPIONS_ROOM, TRUE, 2},
    {MAP_INDIGO_PLATEAU_EXTERIOR, TRUE, 2},
    {MAP_FOUR_ISLAND, TRUE, 1},
    {MAP_SIX_ISLAND_POKEMON_CENTER_1F, TRUE, 2},
    {MAP_LITTLEROOT_TOWN, FALSE, 2},
    {MAP_LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB, FALSE, 2},
    {MAP_LITTLEROOT_TOWN_BRENDANS_HOUSE_1F, FALSE, 2},
    {MAP_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F, FALSE, 2},
    {MAP_LITTLEROOT_TOWN_MAYS_HOUSE_1F, FALSE, 2},
    {MAP_LITTLEROOT_TOWN_MAYS_HOUSE_2F, FALSE, 2},
    {MAP_OLDALE_TOWN, FALSE, 2},
    {MAP_ROUTE103, FALSE, 2},
    {MAP_RUSTBORO_CITY, FALSE, 1},
    {MAP_ROUTE104, FALSE, 1},
    {MAP_ROUTE110, FALSE, 2},
    {MAP_LAVARIDGE_TOWN, FALSE, 1},
    {MAP_ROUTE119, FALSE, 1},
    {MAP_LILYCOVE_CITY, FALSE, 2},
    {MAP_EVER_GRANDE_CITY_CHAMPIONS_ROOM, FALSE, 2},
};

static const u8 sHeroNames[][8] = {
    _("RED"), _("RED"), _("LEAF"), _("BRENDAN"), _("MAY"),
};

static u32 ValidHero(u32 hero)
{
    return hero >= JOURNEY_HERO_RED && hero <= JOURNEY_HERO_MAY ? hero : JOURNEY_HERO_RED;
}

u32 JourneyStoryPlayerHero(void)
{
    u32 choice = VarGet(VAR_EVER_GRANDE_CITY_STATE);
    if (choice >= JOURNEY_HERO_RED && choice <= JOURNEY_HERO_MAY)
        return choice;
    // Preserve the avatar fallback of older saves; do not add save fields.
    return (JourneyAvatarIsKanto() ? JOURNEY_HERO_RED : JOURNEY_HERO_BRENDAN)
        + (gSaveBlock2Ptr->playerGender == FEMALE);
}

u32 JourneyStoryRivalHero(u32 slot)
{
    u32 player = JourneyStoryPlayerHero();
    u32 gender = (player - 1) & 1;
    bool32 homeKanto = VarGet(VAR_JOURNEY_START_REGION) != 0;
    u32 home = homeKanto ? JOURNEY_HERO_RED : JOURNEY_HERO_BRENDAN;
    u32 away = homeKanto ? JOURNEY_HERO_BRENDAN : JOURNEY_HERO_RED;
    if (slot == 1)
        return away + (gender ^ 1);
    if (slot == 2)
        return away + gender == player ? home + gender : away + gender;
    return home + (gender ^ 1);
}

const u8 *JourneyStoryHeroName(u32 hero)
{
    return sHeroNames[ValidHero(hero)];
}

u16 JourneyStoryHeroGraphics(u32 hero)
{
    static const u16 graphics[] = {
        OBJ_EVENT_GFX_RED_NORMAL, OBJ_EVENT_GFX_RED_NORMAL,
        OBJ_EVENT_GFX_GREEN_NORMAL, OBJ_EVENT_GFX_BRENDAN_NORMAL,
        OBJ_EVENT_GFX_MAY_NORMAL,
    };
    return graphics[ValidHero(hero)];
}

enum TrainerPicID JourneyStoryHeroTrainerPic(u32 hero)
{
    static const enum TrainerPicID pictures[] = {
        TRAINER_PIC_RED, TRAINER_PIC_RED, TRAINER_PIC_LEAF,
        TRAINER_PIC_BRENDAN, TRAINER_PIC_MAY,
    };
    return pictures[ValidHero(hero)];
}

static u32 RegionalRival(bool32 kanto, u32 awaySlot)
{
    bool32 homeKanto = VarGet(VAR_JOURNEY_START_REGION) != 0;
    return JourneyStoryRivalHero(kanto == homeKanto ? 0 : awaySlot);
}

u32 JourneyStoryNativeTrainerHero(u16 trainerId)
{
    u32 i;
    for (i = 0; i < ARRAY_COUNT(sNativeRivals); i++)
        if (sNativeRivals[i].trainer == trainerId)
            return RegionalRival(sNativeRivals[i].kanto, sNativeRivals[i].awaySlot);
    return 0;
}

static const struct JourneyRivalMap *CurrentRivalMap(void)
{
    u32 i;
    u16 map = (gSaveBlock1Ptr->location.mapGroup << 8) | gSaveBlock1Ptr->location.mapNum;
    for (i = 0; i < ARRAY_COUNT(sRivalMaps); i++)
        if (sRivalMaps[i].map == map)
            return &sRivalMaps[i];
    return NULL;
}

static u32 CurrentAwaySlot(const struct JourneyRivalMap *map)
{
    if (map->map == MAP_ROUTE22 && VarGet(VAR_MAP_SCENE_ROUTE22) >= 3)
        return 1;
    return map->awaySlot;
}

u32 JourneyStoryCurrentRivalHero(void)
{
    const struct JourneyRivalMap *map = CurrentRivalMap();
    if (map != NULL)
        return RegionalRival(map->kanto, CurrentAwaySlot(map));
    // Other native dialogues can still refer to the regional rival by name.
    return RegionalRival(isFrlg, 2);
}

const u8 *JourneyStoryTrainerName(u16 trainerId)
{
    u32 hero = JourneyStoryNativeTrainerHero(trainerId);
    if (hero != 0)
        return JourneyStoryHeroName(hero);
    return GetTrainerStructFromId(trainerId)->trainerName;
}

enum TrainerPicID JourneyStoryTrainerPic(u16 trainerId)
{
    u32 hero = JourneyStoryNativeTrainerHero(trainerId);
    if (hero != 0)
        return JourneyStoryHeroTrainerPic(hero);
    return GetTrainerStructFromId(trainerId)->trainerPic;
}

u16 JourneyStoryRivalGraphics(u16 graphicsId)
{
    const struct JourneyRivalMap *map = CurrentRivalMap();
    u32 hero;
    bool32 bike;
    if (map == NULL)
        return graphicsId;
    if (map->kanto)
    {
        if (graphicsId != OBJ_EVENT_GFX_BLUE)
            return graphicsId;
        return JourneyStoryHeroGraphics(RegionalRival(TRUE, CurrentAwaySlot(map)));
    }
    switch (graphicsId)
    {
    case OBJ_EVENT_GFX_RIVAL_BRENDAN_NORMAL:
    case OBJ_EVENT_GFX_RIVAL_MAY_NORMAL:
        bike = FALSE;
        break;
    case OBJ_EVENT_GFX_RIVAL_BRENDAN_MACH_BIKE:
    case OBJ_EVENT_GFX_RIVAL_BRENDAN_ACRO_BIKE:
    case OBJ_EVENT_GFX_RIVAL_MAY_MACH_BIKE:
    case OBJ_EVENT_GFX_RIVAL_MAY_ACRO_BIKE:
        bike = TRUE;
        break;
    default:
        return graphicsId;
    }
    hero = RegionalRival(FALSE, CurrentAwaySlot(map));
    if (!bike)
        return JourneyStoryHeroGraphics(hero);
    if (hero == JOURNEY_HERO_RED)
        return OBJ_EVENT_GFX_RED_BIKE;
    if (hero == JOURNEY_HERO_LEAF)
        return OBJ_EVENT_GFX_GREEN_BIKE;
    if (graphicsId == OBJ_EVENT_GFX_RIVAL_BRENDAN_ACRO_BIKE || graphicsId == OBJ_EVENT_GFX_RIVAL_MAY_ACRO_BIKE)
        return hero == JOURNEY_HERO_BRENDAN ? OBJ_EVENT_GFX_RIVAL_BRENDAN_ACRO_BIKE : OBJ_EVENT_GFX_RIVAL_MAY_ACRO_BIKE;
    return hero == JOURNEY_HERO_BRENDAN ? OBJ_EVENT_GFX_RIVAL_BRENDAN_MACH_BIKE : OBJ_EVENT_GFX_RIVAL_MAY_MACH_BIKE;
}
