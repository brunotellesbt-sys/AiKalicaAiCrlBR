#include "global.h"
#include "journey_pwt.h"
#include "journey_pwt_cup.h"
#include "journey_competitive.h"
#include "journey_version.h"
#include "pokemon.h"
#include "pokedex.h"
#include "data.h"
#include "event_data.h"
#include "party_menu.h"
#include "main.h"
#include "overworld.h"
#include "random.h"
#include "string_util.h"
#include "script_menu.h"
#include "list_menu.h"
#include "malloc.h"
#include "battle.h"
#include "battle_setup.h"
#include "constants/items.h"
#include "constants/species.h"
#include "constants/battle_frontier.h"
#include "constants/opponents.h"
#include "constants/vars.h"
#include "constants/script_menu.h"

struct PWTTrainer { u16 trainer, generations; u16 species[6]; };
#include "data/journey_pwt_catalog.h"
struct PWTState
{
    struct Pokemon original[PARTY_SIZE], selected[PARTY_SIZE];
    struct JourneyCup cup;
    u16 facility;
    u8 originalCount, size, pool;
    bool8 active, selecting, registration, rewarded;
};
static EWRAM_DATA struct PWTState sPWT = {0};
static const u8 sDefeat[] = _("An excellent battle!");
static const u8 sUnknown[] = _("To be decided");
static const u8 sWorldCup[] = _("World Cup");
static const u8 sExit[] = _("Cancel");
static const u8 sGenerations[][16] = {
    _("Generation 1"), _("Generation 2"), _("Generation 3"),
    _("Generation 4"), _("Generation 5"), _("Generation 6"),
    _("Generation 7"), _("Generation 8"), _("Generation 9")
};

u32 JourneyPWTMaxGeneration(void) { return gJourneyBuildRules.maxNational == 493 ? 4 : 9; }
u32 JourneyPWTCatalogCount(void) { return ARRAY_COUNT(sPWTTrainers); }
bool32 JourneyPWTTrainerEligible(u32 id, u32 generation)
{
    u32 g, cap = JourneyPWTMaxGeneration();
    if (id >= ARRAY_COUNT(sPWTTrainers) || generation > cap) return FALSE;
    if (!sPWTTrainers[id].generations) return TRUE; // Ash, Eren, Luffy.
    if (generation) return !!(sPWTTrainers[id].generations & (1 << (generation - 1)));
    for (g = 0; g < cap; g++) if (sPWTTrainers[id].generations & (1 << g)) return TRUE;
    return FALSE;
}

void JourneyPWTMenu(void)
{
    u32 count = JourneyPWTMaxGeneration(), i;
    struct ListMenuItem *items = AllocZeroed(sizeof(*items) * (count + 2));
    if (items == NULL) { gSpecialVar_Result = 255; return; }
    for (i = 0; i < count + 2; i++)
    {
        const u8 *name = i == count ? sWorldCup : i == count + 1 ? sExit : sGenerations[i];
        u8 *label = AllocZeroed(StringLength(name) + 1);
        if (label == NULL)
        {
            for (u32 j = 0; j < i; j++) Free((void *)items[j].name);
            Free(items); gSpecialVar_Result = 255; return;
        }
        StringCopy(label, name); items[i].name = label;
        items[i].id = i == count ? 0 : i == count + 1 ? 255 : i + 1;
    }
    ScriptMenu_MultichoiceDynamic(1, 1, count + 2, items, FALSE, 6, 0, DYN_MULTICHOICE_CB_NONE);
}

void JourneyPWTActive(void) { gSpecialVar_Result = sPWT.active; }
bool8 JourneyPWTSelectionActive(void) { return sPWT.selecting; }
static void ReturnFromSelection(void)
{
    sPWT.selecting = FALSE;
    gSpecialVar_Result = gSelectedOrderFromParty[0] != 0;
    SetMainCallback2(CB2_ReturnToFieldContinueScriptPlayMapMusic);
}
void JourneyPWTChoose(void)
{
    gSpecialVar_Result = FALSE;
    if (sPWT.active || sPWT.selecting || gSpecialVar_0x8006 > JourneyPWTMaxGeneration()) return;
    sPWT.size = PARTY_SIZE; sPWT.pool = gSpecialVar_0x8006;
    sPWT.facility = VarGet(VAR_FRONTIER_FACILITY); sPWT.registration = TRUE;
    VarSet(VAR_FRONTIER_FACILITY, FRONTIER_FACILITY_TOWER);
    gSpecialVar_0x8004 = FRONTIER_LVL_OPEN; gSpecialVar_0x8005 = PARTY_SIZE;
    sPWT.selecting = TRUE; gMain.savedCallback = ReturnFromSelection;
    InitChooseHalfPartyForBattle(0);
}
static bool32 SelectionValid(void)
{
    u32 i, j;
    for (i = 0; i < PARTY_SIZE; i++)
    {
        u8 slot = gSelectedOrderFromParty[i];
        enum Species species; enum Item item;
        if (!slot || slot > gPlayerPartyCount) return FALSE;
        species = GetMonData(&gPlayerParty[slot - 1], MON_DATA_SPECIES);
        item = GetMonData(&gPlayerParty[slot - 1], MON_DATA_HELD_ITEM);
        if (!species || !JourneySpeciesAllowed(species)
            || GetMonData(&gPlayerParty[slot - 1], MON_DATA_IS_EGG)
            || gSpeciesInfo[species].isFrontierBanned) return FALSE;
        for (j = 0; j < i; j++)
        {
            struct Pokemon *other = &gPlayerParty[gSelectedOrderFromParty[j] - 1];
            if (slot == gSelectedOrderFromParty[j]
                || SpeciesToNationalPokedexNum(species) == SpeciesToNationalPokedexNum(GetMonData(other, MON_DATA_SPECIES))
                || (item && item == GetMonData(other, MON_DATA_HELD_ITEM))) return FALSE;
        }
    }
    return TRUE;
}
static void Level50(struct Pokemon *mon)
{
    enum Species species = GetMonData(mon, MON_DATA_SPECIES);
    u32 exp = gExperienceTables[gSpeciesInfo[species].growthRate][50], status = 0;
    SetMonData(mon, MON_DATA_EXP, &exp); SetMonData(mon, MON_DATA_STATUS, &status);
    CalculateMonStats(mon);
    u16 hp = GetMonData(mon, MON_DATA_MAX_HP);
    SetMonData(mon, MON_DATA_HP, &hp); MonRestorePP(mon);
}
u16 JourneyPWTRosterSpecies(u32 trainer, u32 slot)
{
    if (trainer >= ARRAY_COUNT(sPWTTrainers) || slot >= PARTY_SIZE) return SPECIES_NONE;
    // Ash's generation-four entry uses his strongest eligible anime reserves.
    if (trainer == JOURNEY_PWT_ASH && JourneyPWTMaxGeneration() == 4)
    {
        static const u16 team[] = {SPECIES_PIKACHU,SPECIES_DRAGONITE,SPECIES_GENGAR,SPECIES_LUCARIO,SPECIES_CHARIZARD,SPECIES_SCEPTILE};
        return team[slot];
    }
    return JourneySpeciesAllowed(sPWTTrainers[trainer].species[slot])
        ? sPWTTrainers[trainer].species[slot] : JourneyTrainerSpecies(sPWTTrainers[trainer].species[slot], 100);
}
static u32 Strength(u32 trainer)
{
    u32 total = 0;
    for (u32 slot = 0; slot < PARTY_SIZE; slot++)
    {
        const struct SpeciesInfo *p = &gSpeciesInfo[JourneyPWTRosterSpecies(trainer, slot)];
        total += p->baseHP + p->baseDefense + p->baseSpDefense + p->baseSpeed
            + max(p->baseAttack,p->baseSpAttack) * 2;
    }
    return total;
}
static void Simulate(u16 a, u16 b, u8 *sa, u8 *sb)
{
    u32 strengthA = Strength(a), strengthB = Strength(b);
    bool32 winA = Random() % (strengthA + strengthB) < strengthA;
    u8 loser = Random() % 6;
    *sa = winA ? 6 : loser; *sb = winA ? loser : 6;
}
void JourneyPWTBegin(void)
{
    u16 entrants[JOURNEY_CUP_MAX_ENTRANTS];
    u32 count = 1, i;
    gSpecialVar_Result = FALSE;
    if (sPWT.active || sPWT.size != PARTY_SIZE || !SelectionValid()
        || sPWT.pool > JourneyPWTMaxGeneration()) return;
    entrants[0] = JOURNEY_CUP_EMPTY;
    for (i = 0; i < ARRAY_COUNT(sPWTTrainers); i++)
        if (JourneyPWTTrainerEligible(i, sPWT.pool)) entrants[count++] = i;
    if (!JourneyCupInit(&sPWT.cup, entrants, count)) return;
    sPWT.originalCount = gPlayerPartyCount;
    memcpy(sPWT.original, gPlayerParty, sizeof(sPWT.original));
    for (i = 0; i < PARTY_SIZE; i++)
    {
        sPWT.selected[i] = sPWT.original[gSelectedOrderFromParty[i] - 1];
        Level50(&sPWT.selected[i]);
    }
    sPWT.rewarded = FALSE; sPWT.active = TRUE;
    gSpecialVar_Result = JourneyCupNext(&sPWT.cup, Simulate);
}
const struct JourneyCup *JourneyPWTCupState(void) { return &sPWT.cup; }
const u8 *JourneyPWTEntrantName(u32 entrant)
{
    if (entrant == 0) return gSaveBlock2Ptr->playerName;
    if (entrant >= sPWT.cup.count) return sUnknown;
    return sPWTTrainerNames[sPWT.cup.entrants[entrant]];
}
u16 JourneyPWTCurrentTrainer(void)
{
    if (!sPWT.active || sPWT.cup.opponent >= sPWT.cup.count) return 0;
    return sPWTTrainers[sPWT.cup.entrants[sPWT.cup.opponent]].trainer;
}
void JourneyPWTBufferBracket(void)
{
    // The full graphical board is a separate modal; this buffer previews the
    // human's group/next match and is deliberately bounded to six rows.
    if (sPWT.cup.stage == JOURNEY_CUP_GROUP_STAGE)
    {
        u32 group = sPWT.cup.groupOf[0];
        StringCopy(gStringVar4, COMPOUND_STRING("GROUP STANDINGS"));
        for (u32 rank = 0; rank < sPWT.cup.groupSize[group]; rank++)
        {
            u16 entrant = JourneyCupRankedEntrant(&sPWT.cup, group, rank);
            StringAppend(gStringVar4, rank == 3 ? COMPOUND_STRING("\p") : COMPOUND_STRING("\n"));
            StringAppend(gStringVar4, JourneyPWTEntrantName(entrant));
            StringAppend(gStringVar4, COMPOUND_STRING("  "));
            ConvertIntToDecimalStringN(gStringVar1, sPWT.cup.points[entrant], STR_CONV_MODE_LEFT_ALIGN, 2);
            StringAppend(gStringVar4, gStringVar1); StringAppend(gStringVar4, COMPOUND_STRING(" pts"));
        }
    }
    else StringCopy(gStringVar4, COMPOUND_STRING("KNOCKOUT STAGE\nThe winner advances!"));
}
void JourneyPWTBufferRound(void)
{
    if (sPWT.cup.stage == JOURNEY_CUP_GROUP_STAGE) StringCopy(gStringVar1, COMPOUND_STRING("Group stage"));
    else if (sPWT.cup.leafBase == 1) StringCopy(gStringVar1, COMPOUND_STRING("Final"));
    else if (sPWT.cup.leafBase == 3) StringCopy(gStringVar1, COMPOUND_STRING("Semifinal"));
    else if (sPWT.cup.leafBase == 7) StringCopy(gStringVar1, COMPOUND_STRING("Quarterfinal"));
    else StringCopy(gStringVar1, COMPOUND_STRING("Knockout round"));
    StringCopy(gStringVar2, JourneyPWTEntrantName(sPWT.cup.opponent));
}
void JourneyPWTPrepareBattle(void)
{
    if (!sPWT.active || !sPWT.cup.prepared || !JourneyPWTCurrentTrainer()) return;
    u32 trainer = sPWT.cup.entrants[sPWT.cup.opponent];
    ZeroPlayerPartyMons(); memcpy(gPlayerParty,sPWT.selected,sizeof(sPWT.selected));
    gPlayerPartyCount = PARTY_SIZE; ZeroEnemyPartyMons();
    for (u32 i = 0; i < PARTY_SIZE; i++)
    {
        struct TrainerMon build = {0};
        struct Pokemon *mon = &gEnemyParty[i];
        u32 personality = Random32();
        build.species = JourneyPWTRosterSpecies(trainer, i); build.lvl = 100;
        JourneyPrepareCompetitiveMon(&build, 100);
        ModifyPersonalityForNature(&personality,build.nature);
        CreateMon(mon,build.species,100,personality,OTID_STRUCT_RANDOM_NO_SHINY);
        if (JourneyPerfectTrainerIvs()) SetMonData(mon,MON_DATA_IVS,&build.iv);
        SetMonData(mon,MON_DATA_HELD_ITEM,&build.heldItem);
        SetMonData(mon,MON_DATA_FRIENDSHIP,&build.friendship);
        static const u8 fields[] = {MON_DATA_HP_EV,MON_DATA_ATK_EV,MON_DATA_DEF_EV,MON_DATA_SPATK_EV,MON_DATA_SPDEF_EV,MON_DATA_SPEED_EV};
        for (u32 slot = 0; slot < 6; slot++) SetMonData(mon,fields[slot],&build.ev[slot]);
        for (u32 slot = 0; slot < MAX_MON_MOVES; slot++) SetMonMoveSlot(mon,build.moves[slot],slot);
        for (u32 ability = 0; ability < NUM_ABILITY_SLOTS; ability++)
            if (gSpeciesInfo[build.species].abilities[ability] == build.ability)
            { SetMonData(mon,MON_DATA_ABILITY_NUM,&ability); break; }
        Level50(mon);
    }
    gEnemyPartyCount = PARTY_SIZE;
    memset(&gTrainerBattleParameter,0,sizeof(gTrainerBattleParameter));
    TRAINER_BATTLE_PARAM.opponentA = JourneyPWTCurrentTrainer();
    TRAINER_BATTLE_PARAM.defeatTextA = (u8 *)sDefeat;
    gBattleTypeFlags = BATTLE_TYPE_TRAINER | BATTLE_TYPE_PWT;
}
void JourneyPWTAdvance(void)
{
    u32 outcome; u8 scored = 0, conceded = 0;
    gSpecialVar_Result = 0;
    if (!sPWT.active) return;
    if (gBattleOutcome == B_OUTCOME_WON) outcome = 1;
    else if (gBattleOutcome == B_OUTCOME_DREW) outcome = 0;
    else outcome = 2;
    for (u32 i = 0; i < PARTY_SIZE; i++)
    {
        scored += !GetMonData(&gEnemyParty[i],MON_DATA_HP);
        conceded += !GetMonData(&gPlayerParty[i],MON_DATA_HP);
    }
    if (!JourneyCupResult(&sPWT.cup,outcome,scored,conceded)) return;
    if (sPWT.cup.stage == JOURNEY_CUP_CHAMPION) gSpecialVar_Result = 2;
    else if (JourneyCupNext(&sPWT.cup,Simulate)) gSpecialVar_Result = 1;
}
void JourneyPWTFinish(void)
{
    gSpecialVar_Result = 0;
    if (sPWT.active)
    {
        memcpy(gPlayerParty,sPWT.original,sizeof(sPWT.original));
        gPlayerPartyCount = sPWT.originalCount;
        if (sPWT.cup.stage == JOURNEY_CUP_CHAMPION && !sPWT.rewarded)
        {
            u32 reward = sPWT.pool ? 10 : 25;
            gSaveBlock2Ptr->frontier.battlePoints = min(9999,gSaveBlock2Ptr->frontier.battlePoints + reward);
            sPWT.rewarded = TRUE; gSpecialVar_Result = reward;
            ConvertIntToDecimalStringN(gStringVar1,reward,STR_CONV_MODE_LEFT_ALIGN,2);
        }
    }
    if (sPWT.registration) VarSet(VAR_FRONTIER_FACILITY,sPWT.facility);
    sPWT.active = sPWT.selecting = sPWT.registration = FALSE; gBattleTypeFlags = 0;
}
