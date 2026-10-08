#include "global.h"
#include "journey_pwt.h"
#include "pokemon.h"
#include "pokedex.h"
#include "data.h"
#include "event_data.h"
#include "party_menu.h"
#include "main.h"
#include "overworld.h"
#include "random.h"
#include "string_util.h"
#include "battle.h"
#include "battle_setup.h"
#include "constants/items.h"
#include "constants/species.h"
#include "constants/battle_frontier.h"
#include "constants/opponents.h"
#include "constants/vars.h"

struct PWTTrainer {
    u16 trainer;
    u16 species[6];
};
static const struct PWTTrainer sPWTTrainers[] = {
    {TRAINER_LEADER_BROCK, {SPECIES_ONIX, SPECIES_GOLEM, SPECIES_AERODACTYL, SPECIES_TYRANITAR, SPECIES_RHYPERIOR, SPECIES_GIGALITH}},
    {TRAINER_LEADER_MISTY, {SPECIES_STARMIE, SPECIES_LAPRAS, SPECIES_GYARADOS, SPECIES_QUAGSIRE, SPECIES_MILOTIC, SPECIES_GRENINJA}},
    {TRAINER_LEADER_LT_SURGE, {SPECIES_RAICHU, SPECIES_MAGNEZONE, SPECIES_ELECTIVIRE, SPECIES_JOLTEON, SPECIES_LUXRAY, SPECIES_ROTOM}},
    {TRAINER_LEADER_ERIKA, {SPECIES_VENUSAUR, SPECIES_TANGROWTH, SPECIES_VILEPLUME, SPECIES_LEAFEON, SPECIES_ROSERADE, SPECIES_BRELOOM}},
    {TRAINER_LEADER_KOGA, {SPECIES_CROBAT, SPECIES_MUK, SPECIES_WEEZING, SPECIES_VENOMOTH, SPECIES_DRAPION, SPECIES_TOXICROAK}},
    {TRAINER_LEADER_SABRINA, {SPECIES_ALAKAZAM, SPECIES_ESPEON, SPECIES_SLOWKING, SPECIES_GARDEVOIR, SPECIES_REUNICLUS, SPECIES_GALLADE}},
    {TRAINER_LEADER_BLAINE, {SPECIES_ARCANINE, SPECIES_RAPIDASH, SPECIES_NINETALES, SPECIES_MAGMORTAR, SPECIES_TORKOAL, SPECIES_VOLCARONA}},
    {TRAINER_JOURNEY_BLUE, {SPECIES_PIDGEOT, SPECIES_ALAKAZAM, SPECIES_RHYDON, SPECIES_ARCANINE, SPECIES_GYARADOS, SPECIES_EXEGGUTOR}},
    {TRAINER_ROXANNE_5, {SPECIES_PROBOPASS, SPECIES_CRADILY, SPECIES_ARMALDO, SPECIES_AGGRON, SPECIES_TYRANTRUM, SPECIES_LYCANROC}},
    {TRAINER_BRAWLY_5, {SPECIES_HARIYAMA, SPECIES_MACHAMP, SPECIES_MEDICHAM, SPECIES_BRELOOM, SPECIES_LUCARIO, SPECIES_MIENSHAO}},
    {TRAINER_WATTSON_5, {SPECIES_MANECTRIC, SPECIES_MAGNETON, SPECIES_ELECTRODE, SPECIES_AMPHAROS, SPECIES_GALVANTULA, SPECIES_MAGNEZONE}},
    {TRAINER_FLANNERY_5, {SPECIES_TORKOAL, SPECIES_CAMERUPT, SPECIES_MAGCARGO, SPECIES_CHANDELURE, SPECIES_DARMANITAN, SPECIES_TALONFLAME}},
    {TRAINER_NORMAN_5, {SPECIES_SLAKING, SPECIES_VIGOROTH, SPECIES_SNORLAX, SPECIES_BLISSEY, SPECIES_PORYGON_Z, SPECIES_KANGASKHAN}},
    {TRAINER_WINONA_5, {SPECIES_ALTARIA, SPECIES_SWELLOW, SPECIES_SKARMORY, SPECIES_PELIPPER, SPECIES_NOIVERN, SPECIES_TROPIUS}},
    {TRAINER_TATE_AND_LIZA_5, {SPECIES_SOLROCK, SPECIES_LUNATONE, SPECIES_CLAYDOL, SPECIES_XATU, SPECIES_BRONZONG, SPECIES_MEOWSTIC}},
    {TRAINER_JUAN_5, {SPECIES_KINGDRA, SPECIES_WHISCASH, SPECIES_WALREIN, SPECIES_CRAWDAUNT, SPECIES_FLOATZEL, SPECIES_VAPOREON}},
    {TRAINER_WALLACE, {SPECIES_MILOTIC, SPECIES_LUDICOLO, SPECIES_TENTACRUEL, SPECIES_GYARADOS, SPECIES_SWAMPERT, SPECIES_STARMIE}},
    {TRAINER_STEVEN, {SPECIES_METAGROSS, SPECIES_AGGRON, SPECIES_SKARMORY, SPECIES_CRADILY, SPECIES_ARMALDO, SPECIES_CLAYDOL}},
};

#define PWT_PLAYER 255
#define PWT_EMPTY 254
struct PWTState {
    struct Pokemon original[PARTY_SIZE];
    struct Pokemon selected[3];
    u8 bracket[15]; // Binary tree; eight leaves occupy indices 7..14.
    u8 originalCount, size, round, playerNode, pool;
    u16 facility;
    bool8 active, selecting, rewarded;
};
static EWRAM_DATA struct PWTState sPWT = {0};
static const u8 sPWTDefeat[] = _("Uma excelente batalha!");
static const u8 sPWTUnknown[] = _("A definir");
static const u8 sPWTNewline[] = _("\n");
static const u8 sPWTPage[] = _("\p");
static const u8 sPWTVersus[] = _(" x ");

void JourneyPWTActive(void)
{
    gSpecialVar_Result = sPWT.active;
}

bool8 JourneyPWTSelectionActive(void)
{
    return sPWT.selecting;
}

static void ReturnFromSelection(void)
{
    sPWT.selecting = FALSE;
    gSpecialVar_Result = gSelectedOrderFromParty[0] != 0;
    SetMainCallback2(CB2_ReturnToFieldContinueScriptPlayMapMusic);
}

void JourneyPWTChoose(void)
{
    if (sPWT.active || sPWT.selecting) { gSpecialVar_Result = FALSE; return; }
    sPWT.size = 3;
    sPWT.pool = gSpecialVar_0x8006;
    sPWT.facility = VarGet(VAR_FRONTIER_FACILITY);
    VarSet(VAR_FRONTIER_FACILITY, FRONTIER_FACILITY_TOWER);
    gSpecialVar_0x8004 = FRONTIER_LVL_OPEN; // Accept levels 1..100; normalize copies later.
    gSpecialVar_0x8005 = sPWT.size;
    sPWT.selecting = TRUE;
    gMain.savedCallback = ReturnFromSelection;
    InitChooseHalfPartyForBattle(0);
}

static bool8 SelectionValid(void)
{
    u32 i, j;
    for (i = 0; i < sPWT.size; i++)
    {
        u8 slot = gSelectedOrderFromParty[i];
        enum Species species;
        enum Item item;
        if (slot == 0 || slot > gPlayerPartyCount) return FALSE;
        species = GetMonData(&gParties[B_TRAINER_0][slot - 1], MON_DATA_SPECIES);
        item = GetMonData(&gParties[B_TRAINER_0][slot - 1], MON_DATA_HELD_ITEM);
        if (species == SPECIES_NONE || GetMonData(&gParties[B_TRAINER_0][slot - 1], MON_DATA_IS_EGG)
            || gSpeciesInfo[species].isFrontierBanned) return FALSE;
        for (j = 0; j < i; j++)
        {
            if (slot == gSelectedOrderFromParty[j]
                || SpeciesToNationalPokedexNum(species) == SpeciesToNationalPokedexNum(GetMonData(&gParties[B_TRAINER_0][gSelectedOrderFromParty[j] - 1], MON_DATA_SPECIES))
                || (item != ITEM_NONE && item == GetMonData(&gParties[B_TRAINER_0][gSelectedOrderFromParty[j] - 1], MON_DATA_HELD_ITEM)))
                return FALSE;
        }
    }
    return TRUE;
}

static void Level50(struct Pokemon *mon)
{
    enum Species species = GetMonData(mon, MON_DATA_SPECIES);
    u32 exp = gExperienceTables[gSpeciesInfo[species].growthRate][50];
    u32 status = 0;
    SetMonData(mon, MON_DATA_EXP, &exp);
    SetMonData(mon, MON_DATA_STATUS, &status);
    CalculateMonStats(mon);
    u16 hp = GetMonData(mon, MON_DATA_MAX_HP);
    SetMonData(mon, MON_DATA_HP, &hp);
    MonRestorePP(mon);
}

void JourneyPWTBegin(void)
{
    u32 i, j, count;
    u8 pool[ARRAY_COUNT(sPWTTrainers)], temp;
    gSpecialVar_Result = FALSE;
    if (sPWT.active || sPWT.size != 3 || !SelectionValid()) return;
    sPWT.originalCount = gPlayerPartyCount;
    memcpy(sPWT.original, gParties[B_TRAINER_0], sizeof(sPWT.original));
    for (i = 0; i < sPWT.size; i++)
    {
        sPWT.selected[i] = sPWT.original[gSelectedOrderFromParty[i] - 1];
        Level50(&sPWT.selected[i]);
    }
    count = sPWT.pool < 2 ? 8 : ARRAY_COUNT(sPWTTrainers);
    for (i = 0; i < count; i++) pool[i] = i + (sPWT.pool == 1 ? 8 : 0);
    for (i = count - 1; i > 0; i--)
    {
        j = Random() % (i + 1); temp = pool[i]; pool[i] = pool[j]; pool[j] = temp;
    }
    memset(sPWT.bracket, PWT_EMPTY, sizeof(sPWT.bracket));
    sPWT.bracket[7] = PWT_PLAYER;
    for (i = 1; i < 8; i++) sPWT.bracket[7 + i] = pool[i - 1];
    for (i = 7; i > 0; i--)
    {
        j = Random() % (i + 1); temp = sPWT.bracket[7 + i];
        sPWT.bracket[7 + i] = sPWT.bracket[7 + j]; sPWT.bracket[7 + j] = temp;
    }
    for (i = 7; i < 15; i++) if (sPWT.bracket[i] == PWT_PLAYER) sPWT.playerNode = i;
    sPWT.round = 0; sPWT.rewarded = FALSE; sPWT.active = TRUE;
    gSpecialVar_Result = TRUE;
}

static const u8 *Name(u8 index)
{
    if (index == PWT_PLAYER) return gSaveBlock2Ptr->playerName;
    if (index == PWT_EMPTY) return sPWTUnknown;
    return GetTrainerNameFromId(sPWTTrainers[index].trainer);
}

void JourneyPWTBufferBracket(void)
{
    u32 i, base, count;
    static const u8 titles[][20] = {_("QUARTAS DE FINAL"), _("SEMIFINAIS"), _("FINAL")};
    base = sPWT.round == 0 ? 7 : sPWT.round == 1 ? 3 : 1;
    count = sPWT.round == 0 ? 8 : sPWT.round == 1 ? 4 : 2;
    StringCopy(gStringVar4, titles[sPWT.round < 3 ? sPWT.round : 2]);
    for (i = 0; i < count; i += 2)
    {
        StringAppend(gStringVar4, i == 4 ? sPWTPage : sPWTNewline);
        StringAppend(gStringVar4, Name(sPWT.bracket[base + i]));
        StringAppend(gStringVar4, sPWTVersus);
        StringAppend(gStringVar4, Name(sPWT.bracket[base + i + 1]));
    }
}

void JourneyPWTBufferRound(void)
{
    static const u8 rounds[][20] = {_("quartas de final"), _("semifinais"), _("final")};
    u8 sibling = sPWT.playerNode & 1 ? sPWT.playerNode + 1 : sPWT.playerNode - 1;
    StringCopy(gStringVar1, rounds[sPWT.round < 3 ? sPWT.round : 2]);
    StringCopy(gStringVar2, Name(sPWT.bracket[sibling]));
}

void JourneyPWTPrepareBattle(void)
{
    u32 i, j;
    u8 picks[6] = {0, 1, 2, 3, 4, 5}, temp;
    static const u16 items[] = {ITEM_LEFTOVERS, ITEM_LIFE_ORB, ITEM_FOCUS_SASH, ITEM_SITRUS_BERRY, ITEM_EXPERT_BELT, ITEM_LUM_BERRY};
    u8 sibling = sPWT.playerNode & 1 ? sPWT.playerNode + 1 : sPWT.playerNode - 1;
    const struct PWTTrainer *trainer;
    if (!sPWT.active || sPWT.round >= 3) return;
    trainer = &sPWTTrainers[sPWT.bracket[sibling]];
    ZeroPlayerPartyMons();
    memcpy(gParties[B_TRAINER_0], sPWT.selected, sPWT.size * sizeof(struct Pokemon));
    gPlayerPartyCount = sPWT.size;
    ZeroEnemyPartyMons();
    for (i = 5; i > 0; i--)
    {
        j = Random() % (i + 1); temp = picks[i]; picks[i] = picks[j]; picks[j] = temp;
    }
    for (i = 0; i < sPWT.size; i++)
    {
        struct Pokemon *mon = &gParties[B_TRAINER_1][i];
        u8 ev = 252;
        enum Species species = trainer->species[picks[i]];
        CreateMonWithIVs(mon, species, 50, Random32(), OTID_STRUCT_RANDOM_NO_SHINY, 31);
        GiveMonInitialMoveset(mon);
        SetMonData(mon, MON_DATA_HELD_ITEM, &items[picks[i]]);
        SetMonData(mon, MON_DATA_SPEED_EV, &ev);
        SetMonData(mon, gSpeciesInfo[species].baseAttack >= gSpeciesInfo[species].baseSpAttack ? MON_DATA_ATK_EV : MON_DATA_SPATK_EV, &ev);
        Level50(mon);
    }
    gEnemyPartyCount = sPWT.size;
    memset(&gTrainerBattleParameter, 0, sizeof(gTrainerBattleParameter));
    TRAINER_BATTLE_PARAM.opponentA = trainer->trainer;
    TRAINER_BATTLE_PARAM.defeatTextA = (u8 *)sPWTDefeat;
    gBattleTypeFlags = BATTLE_TYPE_TRAINER | BATTLE_TYPE_PWT;
}

void JourneyPWTAdvance(void)
{
    u32 base, count, i;
    gSpecialVar_Result = 0;
    if (!sPWT.active || sPWT.round >= 3 || gBattleOutcome != B_OUTCOME_WON) return;
    base = sPWT.round == 0 ? 7 : sPWT.round == 1 ? 3 : 1;
    count = sPWT.round == 0 ? 8 : sPWT.round == 1 ? 4 : 2;
    for (i = base; i < base + count; i += 2)
    {
        u8 winner = sPWT.bracket[i] == PWT_PLAYER || sPWT.bracket[i + 1] == PWT_PLAYER
            ? PWT_PLAYER : sPWT.bracket[i + (Random() & 1)];
        sPWT.bracket[(i - 1) / 2] = winner;
    }
    sPWT.playerNode = (sPWT.playerNode - 1) / 2;
    sPWT.round++;
    gSpecialVar_Result = sPWT.round == 3 ? 2 : 1;
}

void JourneyPWTFinish(void)
{
    gSpecialVar_Result = 0;
    if (sPWT.active)
    {
        memcpy(gParties[B_TRAINER_0], sPWT.original, sizeof(sPWT.original));
        gPlayerPartyCount = sPWT.originalCount;
        if (sPWT.round == 3 && !sPWT.rewarded)
        {
            u32 points = gSaveBlock2Ptr->frontier.battlePoints + 3;
            gSaveBlock2Ptr->frontier.battlePoints = points > 9999 ? 9999 : points;
            sPWT.rewarded = TRUE;
            gSpecialVar_Result = 3;
        }
    }
    VarSet(VAR_FRONTIER_FACILITY, sPWT.facility);
    sPWT.active = FALSE; sPWT.selecting = FALSE;
    gBattleTypeFlags = 0;
}
