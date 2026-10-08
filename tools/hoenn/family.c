#include "global.h"
#include "pokemon.h"
#include "journey_family.h"
#include "event_data.h"
#include "overworld.h"
#include "field_screen_effect.h"
#include "item.h"
#include "string_util.h"
#include "script_pokemon_util.h"
#include "constants/maps.h"
#include "constants/flags.h"
#include "constants/vars.h"
#include "constants/items.h"
#include "constants/species.h"
#include "constants/heal_locations.h"
#include "constants/regions.h"

struct JourneyFamilyHome {
    u16 originalMap, livingMap, bedroomMap, healLocation;
    u8 people, secondRole, thirdRole;
};
extern const struct MapHeader *const *const gMapGroups[];
#include "journey_family_homes.h"

static const struct JourneyFamilyHome *SelectedHome(void)
{
    u16 index = VarGet(VAR_JOURNEY_FAMILY_HOME);
    if (index == 0 || index > ARRAY_COUNT(sJourneyFamilyHomes)) return NULL;
    return &sJourneyFamilyHomes[index - 1];
}

const struct MapHeader *JourneyFamilyHomeHeader(u16 group, u16 number)
{
    const struct JourneyFamilyHome *home = SelectedHome();
    if (home == NULL || VarGet(VAR_JOURNEY_FAMILY_HOME) == 1) return NULL;
    if (group == MAP_GROUP(home->originalMap) && number == MAP_NUM(home->originalMap))
        return gMapGroups[MAP_GROUP(home->livingMap)][MAP_NUM(home->livingMap)];
    return NULL;
}

void JourneyFamilyChooseHome(void)
{
    u16 city = gSpecialVar_Result;
    if (city >= ARRAY_COUNT(sJourneyFamilyHomes)) city = 0;
    // A saved choice cannot be replaced on a later visit to Pallet.
    if (SelectedHome() != NULL) return;
    VarSet(VAR_JOURNEY_FAMILY_HOME, city + 1);
    VarSet(VAR_JOURNEY_FAMILY_STAGE, city == 0 ? 2 : 1);
    SetLastHealLocationWarp(sJourneyFamilyHomes[city].healLocation);
    gSpecialVar_Result = city;
}

void JourneyFamilyCanChooseCity(void)
{
    gSpecialVar_Result = gSaveBlock2Ptr->playerRegion == REGION_KANTO
        && gPlayerPartyCount == 0 && SelectedHome() == NULL;
}

void JourneyFamilyWarpBedroom(void)
{
    const struct JourneyFamilyHome *home = SelectedHome();
    if (home == NULL) return;
    SetWarpDestination(MAP_GROUP(home->bedroomMap), MAP_NUM(home->bedroomMap), -1, 6, 6);
    DoWarp();
    ResetInitialPlayerAvatarState();
}

void JourneyFamilySetupVisitors(void)
{
    if (FlagGet(FLAG_JOURNEY_FAMILY_STARTER_RECEIVED))
        FlagSet(FLAG_JOURNEY_FAMILY_HIDE_VISITOR);
    else
        FlagClear(FLAG_JOURNEY_FAMILY_HIDE_VISITOR);
}

void JourneyFamilyInfo(void)
{
    const struct JourneyFamilyHome *home = SelectedHome();
    u16 person = gSpecialVar_LastTalked - 1;
    gSpecialVar_Result = 0;
    if (home == NULL || person >= home->people) return;
    gSpecialVar_Result = person == 0 ? 1 : person == 1 ? home->secondRole : home->thirdRole;
}

void JourneyFamilyGiveGift(void)
{
    static const u16 items[] = {ITEM_HM_SURF, ITEM_HM_DIVE, ITEM_HM_WATERFALL};
    static const u8 texts[][32] = {_("SURF, DIVE e WATERFALL"), _("SURF e DIVE"), _("SURF"), _("DIVE"), _("WATERFALL")};
    const struct JourneyFamilyHome *home = SelectedHome();
    u16 person = gSpecialVar_LastTalked - 1;
    u16 mask = VarGet(VAR_JOURNEY_FAMILY_GIFTS), assigned, i;
    bool32 newlyGiven = FALSE;
    gSpecialVar_Result = 0;
    if (home == NULL || person >= home->people) return;
    assigned = home->people == 1 ? 7 : home->people == 2 ? (person == 0 ? 3 : 4) : 1 << person;
    StringCopy(gStringVar1, texts[home->people == 1 ? 0 : home->people == 2 ? (person == 0 ? 1 : 4) : person + 2]);
    for (i = 0; i < ARRAY_COUNT(items); i++)
    {
        u16 bit = 1 << i;
        if (!(assigned & bit) || (mask & bit)) continue;
        if (!CheckBagHasItem(items[i], 1))
        {
            if (!AddBagItem(items[i], 1)) { gSpecialVar_Result = 2; return; }
            newlyGiven = TRUE;
        }
        mask |= bit;
        VarSet(VAR_JOURNEY_FAMILY_GIFTS, mask);
    }
    if ((mask & 7) == 7) FlagSet(FLAG_JOURNEY_WATER_HMS_GIVEN);
    gSpecialVar_Result = newlyGiven ? 1 : 0;
}

void JourneyFamilyGiveStarter(void)
{
    static const enum Species species[] = {SPECIES_BULBASAUR, SPECIES_CHARMANDER, SPECIES_SQUIRTLE};
    static const u16 starterVars[] = {0, 2, 1};
    u16 choice = gSpecialVar_Result;
    gSpecialVar_Result = 0;
    if (FlagGet(FLAG_JOURNEY_FAMILY_STARTER_RECEIVED) || choice > 2 || gPlayerPartyCount >= PARTY_SIZE) return;
    if (ScriptGiveMon(species[choice], 5, ITEM_NONE) != 0) return;
    VarSet(VAR_STARTER_MON_FRLG, starterVars[choice]);
    FlagSet(FLAG_SYS_POKEMON_GET);
    FlagSet(FLAG_PALLET_LADY_NOT_BLOCKING_SIGN);
    FlagSet(FLAG_SYS_POKEDEX_GET);
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
    VarSet(VAR_MAP_SCENE_PALLET_TOWN_RIVALS_HOUSE, 1);
    VarSet(VAR_MAP_SCENE_POKEMON_CENTER_TEALA, 1);
    VarSet(VAR_MAP_SCENE_ROUTE22, 1);
    VarSet(VAR_JOURNEY_FAMILY_STAGE, 2);
    FlagSet(FLAG_JOURNEY_FAMILY_STARTER_RECEIVED);
    FlagSet(FLAG_JOURNEY_FAMILY_HIDE_VISITOR);
    gSpecialVar_Result = 1;
}

void JourneyFamilyVisitorIds(void)
{
    const struct JourneyFamilyHome *home = SelectedHome();
    gSpecialVar_0x8004 = home == NULL ? 0 : home->people + 1;
    gSpecialVar_0x8005 = gSpecialVar_0x8004 + 1;
}
