#include "global.h"
#include "pokemon.h"
#include "journey_birth.h"
#include "journey_family.h"
#include "event_data.h"
#include "event_object_movement.h"
#include "overworld.h"
#include "fieldmap.h"
#include "script.h"
#include "script_pokemon_util.h"
#include "constants/maps.h"
#include "constants/flags.h"
#include "constants/vars.h"
#include "constants/regions.h"
#include "constants/species.h"
#include "constants/items.h"
#include "constants/event_objects.h"
#include "constants/event_object_movement.h"

struct JourneyBirthArrival {
    u16 map;
    s16 truckX, truckY, landingX, landingY;
    bool8 boat;
};
#include "journey_birth_arrivals.h"
extern const u8 JourneyBirth_Arrival[];
extern const u8 PalletTown_PlayersHouse_2F_EventScript_SetIntroFlags[];

bool32 JourneyBirthIsBoat(void)
{
    u16 index = VarGet(VAR_JOURNEY_FAMILY_HOME);
    return index != 0 && index <= ARRAY_COUNT(sJourneyBirthArrivals) && sJourneyBirthArrivals[index - 1].boat;
}

void JourneyBirthArrivalVehicle(void)
{
    gSpecialVar_Result = JourneyBirthIsBoat();
}

void JourneyBirthRegion(void)
{
    gSpecialVar_Result = gSaveBlock2Ptr->playerRegion == REGION_KANTO;
}

void JourneyBirthHomeRegion(void)
{
    gSpecialVar_Result = VarGet(VAR_JOURNEY_FAMILY_HOME) >= 17;
}

void JourneyBirthChooseCity(void)
{
    u16 choice = gSpecialVar_Result;
    bool32 hoenn = gSaveBlock2Ptr->playerRegion != REGION_KANTO;
    if (choice >= (hoenn ? 15 : 16)) choice = 0;
    gSpecialVar_Result = choice + (hoenn ? 16 : 0);
    JourneyFamilyChooseHome();
    VarSet(VAR_JOURNEY_FAMILY_MENU_STATE, 1);
    if (hoenn && choice == 0) VarSet(VAR_JOURNEY_FAMILY_STAGE, 2);
}

bool32 JourneyBirthMenuFinished(void)
{
    return VarGet(VAR_JOURNEY_FAMILY_HOME) != 0 && !ArePlayerFieldControlsLocked();
}

void JourneyBirthTruckDestination(void)
{
    u16 index = VarGet(VAR_JOURNEY_FAMILY_HOME);
    const struct JourneyFamilyHome *home = JourneyFamilySelectedHome();
    const struct JourneyBirthArrival *arrival;
    if (index == 0 || index > ARRAY_COUNT(sJourneyBirthArrivals) || home == NULL) return;
    // Littleroot keeps its gender-specific native truck, mother and clock scenes.
    if (index == 17) return;
    arrival = &sJourneyBirthArrivals[index - 1];
    RunScriptImmediately(PalletTown_PlayersHouse_2F_EventScript_SetIntroFlags);
    SetDynamicWarpWithCoords(0, MAP_GROUP(arrival->map), MAP_NUM(arrival->map), -1,
        arrival->landingX, arrival->landingY);
    SetLastHealLocationWarp(home->healLocation);
    VarSet(VAR_JOURNEY_BIRTH_ARRIVAL, 2);
}

bool32 JourneyBirthTryArrival(void)
{
    u16 index = VarGet(VAR_JOURNEY_FAMILY_HOME);
    const struct JourneyBirthArrival *arrival;
    if (VarGet(VAR_JOURNEY_BIRTH_ARRIVAL) != 2 || index == 0 || index > ARRAY_COUNT(sJourneyBirthArrivals)) return FALSE;
    arrival = &sJourneyBirthArrivals[index - 1];
    if (gSaveBlock1Ptr->location.mapGroup != MAP_GROUP(arrival->map)
        || gSaveBlock1Ptr->location.mapNum != MAP_NUM(arrival->map)) return FALSE;
    VarSet(VAR_JOURNEY_BIRTH_ARRIVAL, 3);
    ScriptContext_SetupScript(JourneyBirth_Arrival);
    return TRUE;
}

void JourneyBirthSpawnArrival(void)
{
    u16 index = VarGet(VAR_JOURNEY_FAMILY_HOME);
    const struct JourneyBirthArrival *arrival;
    u8 elevation;
    if (index == 0 || index > ARRAY_COUNT(sJourneyBirthArrivals)) return;
    arrival = &sJourneyBirthArrivals[index - 1];
    elevation = MapGridGetElevationAt(arrival->truckX + 7, arrival->truckY + 7);
    if (!(index >= 10 && index <= 16))
    SpawnSpecialObjectEventParameterized(arrival->boat ? OBJ_EVENT_GFX_MR_BRINEYS_BOAT : OBJ_EVENT_GFX_TRUCK, MOVEMENT_TYPE_FACE_RIGHT,
        LOCALID_JOURNEY_ARRIVAL_TRUCK, arrival->truckX, arrival->truckY, elevation);
    SpawnSpecialObjectEventParameterized(index <= 16 ? OBJ_EVENT_GFX_MOM_FRLG : OBJ_EVENT_GFX_MOM,
        MOVEMENT_TYPE_FACE_DOWN, LOCALID_JOURNEY_ARRIVAL_MOM,
        arrival->boat ? arrival->landingX : arrival->truckX + 2,
        arrival->boat ? arrival->landingY - 1 : arrival->truckY - 1,
        MapGridGetElevationAt(arrival->landingX + 7, arrival->landingY + 7));
}

void JourneyBirthRemoveArrival(void)
{
    RemoveObjectEventByLocalIdAndMap(LOCALID_JOURNEY_ARRIVAL_TRUCK, gSaveBlock1Ptr->location.mapNum, gSaveBlock1Ptr->location.mapGroup);
    RemoveObjectEventByLocalIdAndMap(LOCALID_JOURNEY_ARRIVAL_MOM, gSaveBlock1Ptr->location.mapNum, gSaveBlock1Ptr->location.mapGroup);
}

static bool32 GiveRegionalStarter(bool32 hoenn, u16 choice)
{
    static const enum Species species[2][3] = {
        {SPECIES_BULBASAUR, SPECIES_CHARMANDER, SPECIES_SQUIRTLE},
        {SPECIES_TREECKO, SPECIES_TORCHIC, SPECIES_MUDKIP}};
    static const u16 kantoChoice[] = {0, 2, 1};
    u16 flag = hoenn ? FLAG_JOURNEY_HOENN_STARTER_GIVEN : FLAG_JOURNEY_KANTO_STARTER_GIVEN;
    if (choice > 2 || FlagGet(flag) || gPlayerPartyCount >= PARTY_SIZE) return FALSE;
    if (ScriptGiveMon(species[hoenn][choice], 5, ITEM_NONE) != 0) return FALSE;
    VarSet(hoenn ? VAR_STARTER_MON : VAR_STARTER_MON_FRLG, hoenn ? choice : kantoChoice[choice]);
    FlagSet(flag);
    FlagSet(FLAG_SYS_POKEMON_GET);
    FlagSet(FLAG_SYS_POKEDEX_GET);
    if (hoenn)
    {
        FlagSet(FLAG_RESCUED_BIRCH);
        FlagSet(FLAG_HIDE_ROUTE_101_BIRCH_ZIGZAGOON_BATTLE);
        FlagSet(FLAG_HIDE_ROUTE_101_BIRCH_STARTERS_BAG);
        FlagClear(FLAG_HIDE_LITTLEROOT_TOWN_BIRCHS_LAB_BIRCH);
        VarSet(VAR_ROUTE101_STATE, 3);
        VarSet(VAR_BIRCH_LAB_STATE, 5);
    }
    else
    {
        FlagSet(FLAG_PALLET_LADY_NOT_BLOCKING_SIGN);
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
    }
    return TRUE;
}

void JourneyBirthGiveHomeStarter(void)
{
    u16 choice = gSpecialVar_Result;
    gSpecialVar_Result = FALSE;
    if (FlagGet(FLAG_JOURNEY_FAMILY_STARTER_RECEIVED)) return;
    if (!GiveRegionalStarter(VarGet(VAR_JOURNEY_FAMILY_HOME) >= 17, choice)) return;
    VarSet(VAR_JOURNEY_FAMILY_STAGE, 2);
    FlagSet(FLAG_JOURNEY_FAMILY_STARTER_RECEIVED);
    FlagSet(FLAG_JOURNEY_FAMILY_HIDE_VISITOR);
    gSpecialVar_Result = TRUE;
}

void JourneyBirthVisitOak(void)
{
    gSpecialVar_Result = gSaveBlock2Ptr->playerRegion == REGION_HOENN
        && !FlagGet(FLAG_JOURNEY_KANTO_STARTER_GIVEN);
}

void JourneyBirthGiveKantoVisitStarter(void)
{
    u16 choice = gSpecialVar_Result;
    gSpecialVar_Result = GiveRegionalStarter(FALSE, choice);
}

void JourneyBirthCheckPartySpace(void)
{
    gSpecialVar_Result = gPlayerPartyCount < PARTY_SIZE;
}

void JourneyBirthRecordHoennStarter(void)
{
    FlagSet(FLAG_JOURNEY_HOENN_STARTER_GIVEN);
}
