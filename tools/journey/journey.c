#include "global.h"
#include "journey.h"
#include "event_data.h"
#include "overworld.h"
#include "field_fadetransition.h"
#include "save_location.h"
#include "item.h"
#include "string_util.h"
#include "script_pokemon_util.h"
#include "constants/maps.h"
#include "constants/flags.h"
#include "constants/vars.h"
#include "constants/items.h"
#include "constants/species.h"
#include "constants/heal_locations.h"
#include "constants/event_objects.h"

struct JourneyHome {
    u16 originalMap;
    u16 livingMap;
    u16 bedroomMap;
    u16 healLocation;
    u8 city;
    u8 people;
    u8 secondRole;
    u8 thirdRole;
};
extern const struct MapHeader *const *gMapGroups[];
#include "journey_homes.h"

static const u8 sGiftBoth[] = _("HM03 SURF e HM07 WATERFALL");
static const u8 sGiftSurf[] = _("HM03 SURF");
static const u8 sGiftWaterfall[] = _("HM07 WATERFALL");
static const u8 sGiftPotions[] = _("3 POTIONS");

static const struct JourneyHome *SelectedHome(void)
{
    u16 index = VarGet(VAR_JOURNEY_HOME);
    if (index == 0 || index > ARRAY_COUNT(sJourneyHomes))
        return NULL;
    return &sJourneyHomes[index - 1];
}

const struct MapHeader *JourneyHomeHeader(u16 group, u16 number)
{
    const struct JourneyHome *home = SelectedHome();
    // Pallet retains its original layout, mother and Oak's laboratory introduction.
    if (home == NULL || home->city == 0)
        return NULL;
    if (group == MAP_GROUP(home->originalMap) && number == MAP_NUM(home->originalMap))
        return gMapGroups[MAP_GROUP(home->livingMap)][MAP_NUM(home->livingMap)];
    return NULL;
}

void JourneyChooseHome(void)
{
    u16 city = gSpecialVar_Result;
    // Exactly one curated home per city, in the same order as the city menu.
    u16 i;
    if (city >= ARRAY_COUNT(sJourneyHomes))
        city = 0;
    i = city;
    FlagSet(FLAG_JOURNEY_EARLY_FERRY);
    VarSet(VAR_JOURNEY_CITY, city + 1);
    VarSet(VAR_JOURNEY_HOME, i + 1);
    VarSet(VAR_JOURNEY_STAGE, city == 0 ? 2 : 1);
    JourneySetRespawn();
    gSpecialVar_Result = city;
}

void JourneyWarpBedroom(void)
{
    const struct JourneyHome *home = SelectedHome();
    if (home == NULL) return;
    SetWarpDestination(MAP_GROUP(home->bedroomMap), MAP_NUM(home->bedroomMap), -1, 6, 6);
    DoWarp();
    ResetInitialPlayerAvatarState();
}

void JourneySetRespawn(void)
{
    const struct JourneyHome *home = SelectedHome();
    if (home != NULL) SetLastHealLocationWarp(home->healLocation);
}

void JourneySetupVisitors(void)
{
    if (FlagGet(FLAG_JOURNEY_STARTER_RECEIVED))
        FlagSet(FLAG_JOURNEY_HIDE_VISITOR);
    else
        FlagClear(FLAG_JOURNEY_HIDE_VISITOR);
}

void JourneyFamilyInfo(void)
{
    const struct JourneyHome *home = SelectedHome();
    u16 role = gSpecialVar_LastTalked - 1;
    gSpecialVar_Result = 0;
    if (home == NULL || role >= home->people) return;
    gSpecialVar_Result = role == 0 ? 1 : (role == 1 ? home->secondRole : home->thirdRole);
}

void JourneyGiveGift(void)
{
    const struct JourneyHome *home = SelectedHome();
    u16 role = gSpecialVar_LastTalked - 1;
    u16 mask = VarGet(VAR_JOURNEY_GIFTS);
    u16 items[2], bits[2], quantities[2], n = 1, i;
    bool8 newlyGiven = FALSE;
    gSpecialVar_Result = 0;
    if (home == NULL || role >= home->people) return;
    if (role == 0) {
        items[0] = ITEM_HM03; bits[0] = 1; quantities[0] = 1;
        if (home->people == 1) {
            items[1] = ITEM_HM07; bits[1] = 2; quantities[1] = 1; n = 2;
        }
    } else if (role == 1) {
        items[0] = ITEM_HM07; bits[0] = 2; quantities[0] = 1;
    } else {
        items[0] = ITEM_POTION; bits[0] = 1 << role; quantities[0] = 3;
    }
    StringCopy(gStringVar1, role == 0 ? (n == 2 ? sGiftBoth : sGiftSurf) : (role == 1 ? sGiftWaterfall : sGiftPotions));
    // Record each successful item separately: retrying with a full bag cannot duplicate HMs.
    for (i = 0; i < n; i++) {
        if (mask & bits[i]) continue;
        if (!AddBagItem(items[i], quantities[i])) {
            gSpecialVar_Result = 2;
            return;
        }
        mask |= bits[i];
        VarSet(VAR_JOURNEY_GIFTS, mask);
        newlyGiven = TRUE;
    }
    gSpecialVar_Result = newlyGiven ? 1 : 0;
}

void JourneyGiveStarter(void)
{
    static const u16 species[] = {SPECIES_BULBASAUR, SPECIES_CHARMANDER, SPECIES_SQUIRTLE};
    static const u16 starterVars[] = {0, 2, 1};
    u16 choice = gSpecialVar_Result;
    if (FlagGet(FLAG_JOURNEY_STARTER_RECEIVED) || choice > 2) return;
    ScriptGiveMon(species[choice], 5, ITEM_NONE, 0, 0, 0);
    VarSet(VAR_STARTER_MON, starterVars[choice]);
    FlagSet(FLAG_SYS_POKEMON_GET);
    FlagSet(FLAG_PALLET_LADY_NOT_BLOCKING_SIGN);
    FlagSet(FLAG_SYS_POKEDEX_GET);
    SetUnlockedPokedexFlags();
    FlagSet(FLAG_BEAT_RIVAL_IN_OAKS_LAB);
    FlagSet(FLAG_GOT_POKEBALLS_FROM_OAK_AFTER_22_RIVAL);
    FlagSet(FLAG_HIDE_OAK_IN_PALLET_TOWN);
    FlagClear(FLAG_HIDE_OAK_IN_HIS_LAB);
    FlagSet(FLAG_HIDE_RIVAL_IN_LAB);
    FlagSet(FLAG_HIDE_BULBASAUR_BALL);
    FlagSet(FLAG_HIDE_SQUIRTLE_BALL);
    FlagSet(FLAG_HIDE_CHARMANDER_BALL);
    VarSet(VAR_MAP_SCENE_PALLET_TOWN_PROFESSOR_OAKS_LAB, 6);
    VarSet(VAR_MAP_SCENE_PALLET_TOWN_OAK, 1);
    VarSet(VAR_MAP_SCENE_VIRIDIAN_CITY_MART, 2);
    VarSet(VAR_MAP_SCENE_VIRIDIAN_CITY_OLD_MAN, 1);
    VarSet(VAR_MAP_SCENE_PALLET_TOWN_RIVALS_HOUSE, 1);
    VarSet(VAR_MAP_SCENE_POKEMON_CENTER_TEALA, 1);
    VarSet(VAR_MAP_SCENE_ROUTE22, 1);
    VarSet(VAR_JOURNEY_STAGE, 2);
    FlagSet(FLAG_JOURNEY_STARTER_RECEIVED);
    FlagSet(FLAG_JOURNEY_HIDE_VISITOR);
    JourneySetRespawn();
}
