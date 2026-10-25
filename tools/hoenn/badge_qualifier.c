#include "global.h"
#include "journey_badge_qualifier.h"
#include "journey_story_rivals.h"
#include "journey_extra_gyms.h"
#include "journey_wild.h"
#include "battle.h"
#include "battle_setup.h"
#include "data.h"
#include "event_data.h"
#include "pokemon.h"
#include "random.h"
#include "script_pokemon_util.h"
#include "string_util.h"
#include "constants/flags.h"
#include "constants/opponents.h"
#include "constants/vars.h"

// This is the campaign's qualifying competition. It owns no PWT state, level
// normalization, registration copies, facility records or battle-point reward.
#define QUALIFIER_IMMEDIATE_GROUP_DEFEAT FALSE
#define QUALIFIER_LUFFY 5
#define QUALIFIER_EREN 6
#define QUALIFIER_STATE_ARENA 1
#define QUALIFIER_STATE_CELEBRATION 2

struct JourneyQualifierRuntime
{
    struct JourneyQualifierCore core;
    u16 heldItems[PARTY_SIZE];
    u32 personalities[PARTY_SIZE], trainerIds[PARTY_SIZE];
    u8 partyCount;
    bool8 active, snapshotValid, battlePrepared, battleStarted, battleReturned;
};
static EWRAM_DATA struct JourneyQualifierRuntime sQualifier = {0};
static const u8 sLuffyName[] = _("Luffy");
static const u8 sErenName[] = _("Eren");
static const u8 sNoOpponent[] = _("No opponent");
static const u8 sDefeat[] = _("That was a worthy challenge!");

static const u16 sQualifierTrainers[] = {
    0, TRAINER_JOURNEY_QUALIFIER_RED, TRAINER_JOURNEY_QUALIFIER_LEAF,
    TRAINER_JOURNEY_QUALIFIER_BRENDAN, TRAINER_JOURNEY_QUALIFIER_MAY,
    TRAINER_JOURNEY_QUALIFIER_LUFFY, TRAINER_JOURNEY_QUALIFIER_EREN
};

static const u8 *HeroName(u32 hero)
{
    if (hero == QUALIFIER_LUFFY) return sLuffyName;
    if (hero == QUALIFIER_EREN) return sErenName;
    return JourneyStoryHeroName(hero);
}

static const u8 *EntrantName(u32 entrant)
{
    if (entrant == 0) return gSaveBlock2Ptr->playerName;
    if (entrant >= JOURNEY_QUALIFIER_ENTRANTS) return sNoOpponent;
    return HeroName(sQualifier.core.hero[entrant]);
}

bool32 JourneyQualifierWon(void)
{
    return FlagGet(FLAG_JOURNEY_QUALIFIER_WON);
}

void JourneyQualifierAvailable(void)
{
    gSpecialVar_Result = JourneyTotalBadgeCount() >= 18 && !JourneyQualifierWon();
}

static bool32 HasUsableParty(void)
{
    if (!gPlayerPartyCount || gPlayerPartyCount > PARTY_SIZE) return FALSE;
    for (u32 i = 0; i < gPlayerPartyCount; i++)
        if (GetMonData(&gPlayerParty[i], MON_DATA_SPECIES)
            && !GetMonData(&gPlayerParty[i], MON_DATA_IS_EGG)) return TRUE;
    return FALSE;
}

void JourneyQualifierRestoreParty(void)
{
    // Heal the actual, evolved/current party. Never roll back EXP, EVs,
    // friendship, learned moves or spent Bag items by restoring a party copy.
    HealPlayerParty();
    if (sQualifier.snapshotValid)
    {
        bool8 restored[PARTY_SIZE] = {FALSE};
        for (u32 i = 0; i < sQualifier.partyCount && i < gPlayerPartyCount; i++)
            for (u32 original = 0; original < sQualifier.partyCount; original++)
            {
                // Native battle switches can reorder the actual party. Keep
                // an item with its Pokemon, including after an evolution.
                if (!restored[original]
                    && GetMonData(&gPlayerParty[i], MON_DATA_PERSONALITY) == sQualifier.personalities[original]
                    && GetMonData(&gPlayerParty[i], MON_DATA_OT_ID) == sQualifier.trainerIds[original])
                {
                    SetMonData(&gPlayerParty[i], MON_DATA_HELD_ITEM, &sQualifier.heldItems[original]);
                    restored[original] = TRUE;
                    break;
                }
            }
    }
}

void JourneyQualifierBegin(void)
{
    u8 heroes[JOURNEY_QUALIFIER_ENTRANTS];
    u32 player = JourneyStoryPlayerHero();
    gSpecialVar_Result = FALSE;
    if (sQualifier.active || JourneyTotalBadgeCount() < 18 || JourneyQualifierWon()
        || player < 1 || player > 4 || !HasUsableParty()) return;
    heroes[0] = 0;
    for (u32 i = 0; i < 3; i++)
    {
        heroes[i + 1] = JourneyStoryRivalHero(i);
        if (!heroes[i + 1] || heroes[i + 1] > 4 || heroes[i + 1] == player) return;
    }
    heroes[4] = QUALIFIER_LUFFY; heroes[5] = QUALIFIER_EREN;
    memset(&sQualifier, 0, sizeof(sQualifier));
    if (!JourneyQualifierCoreInit(&sQualifier.core, heroes, Random32(), QUALIFIER_IMMEDIATE_GROUP_DEFEAT)) return;
    sQualifier.partyCount = gPlayerPartyCount;
    for (u32 i = 0; i < sQualifier.partyCount; i++)
    {
        sQualifier.heldItems[i] = GetMonData(&gPlayerParty[i], MON_DATA_HELD_ITEM);
        sQualifier.personalities[i] = GetMonData(&gPlayerParty[i], MON_DATA_PERSONALITY);
        sQualifier.trainerIds[i] = GetMonData(&gPlayerParty[i], MON_DATA_OT_ID);
    }
    sQualifier.active = sQualifier.snapshotValid = TRUE;
    VarSet(VAR_JOURNEY_QUALIFIER_STATE, QUALIFIER_STATE_ARENA);
    JourneyQualifierRestoreParty();
    gSpecialVar_Result = TRUE;
}

void JourneyQualifierCheckActive(void)
{
    gSpecialVar_Result = sQualifier.active
        && VarGet(VAR_JOURNEY_QUALIFIER_STATE) == QUALIFIER_STATE_ARENA;
}

const struct JourneyQualifierCore *JourneyQualifierState(void)
{
    return &sQualifier.core;
}

u32 JourneyQualifierOpponentHero(void)
{
    if (!sQualifier.active || !sQualifier.core.prepared
        || sQualifier.core.opponent >= JOURNEY_QUALIFIER_ENTRANTS) return 0;
    return sQualifier.core.hero[sQualifier.core.opponent];
}

const u8 *JourneyQualifierOpponentName(void)
{
    u32 hero = JourneyQualifierOpponentHero();
    return hero ? HeroName(hero) : sNoOpponent;
}

void JourneyQualifierOpponent(void)
{
    StringCopy(gStringVar1, JourneyQualifierOpponentName());
    gSpecialVar_Result = JourneyQualifierOpponentHero();
}

u16 JourneyQualifierCurrentTrainer(void)
{
    u32 hero = JourneyQualifierOpponentHero();
    return hero < ARRAY_COUNT(sQualifierTrainers) ? sQualifierTrainers[hero] : 0;
}

static u32 Strength(u32 hero)
{
    const struct Trainer *trainer = GetTrainerStructFromId(sQualifierTrainers[hero]);
    u32 total = 0;
    for (u32 slot = 0; slot < trainer->partySize; slot++)
    {
        const struct SpeciesInfo *species = &gSpeciesInfo[trainer->party[slot].species];
        total += species->baseHP + species->baseDefense + species->baseSpDefense
            + species->baseSpeed + max(species->baseAttack, species->baseSpAttack) * 2;
    }
    return max(1, total);
}

static void Simulate(u8 heroA, u8 heroB, u8 *leftA, u8 *leftB)
{
    u32 strengthA = Strength(heroA), strengthB = Strength(heroB);
    bool32 winA = Random32() % (strengthA + strengthB) < strengthA;
    u8 surviving = 1 + Random() % PARTY_SIZE;
    *leftA = winA ? surviving : 0;
    *leftB = winA ? 0 : surviving;
}

void JourneyQualifierNext(void)
{
    gSpecialVar_Result = JOURNEY_QUALIFIER_ELIMINATED;
    if (!sQualifier.active || VarGet(VAR_JOURNEY_QUALIFIER_STATE) != QUALIFIER_STATE_ARENA) return;
    gSpecialVar_Result = JourneyQualifierCoreNext(&sQualifier.core, Simulate);
}

static void AppendNumber(u32 value)
{
    ConvertIntToDecimalStringN(gStringVar1, value, STR_CONV_MODE_LEFT_ALIGN, 2);
    StringAppend(gStringVar4, gStringVar1);
}

void JourneyQualifierBufferStandings(void)
{
    StringCopy(gStringVar4, COMPOUND_STRING("GROUP A - WINS / BALANCE"));
    if (!sQualifier.active) return;
    for (u32 group = 0; group < JOURNEY_QUALIFIER_GROUPS; group++)
    {
        if (group) StringAppend(gStringVar4, COMPOUND_STRING("\pGROUP B - WINS / BALANCE"));
        for (u32 rank = 0; rank < JOURNEY_QUALIFIER_GROUP_SIZE; rank++)
        {
            u8 entrant = JourneyQualifierCoreRank(&sQualifier.core, group, rank);
            s32 balance = sQualifier.core.balance[entrant];
            // Standard field dialogue has two visible text rows. The later
            // entrants scroll through the same box instead of clipping below
            // it; the other group starts its own page.
            StringAppend(gStringVar4, rank ? COMPOUND_STRING("\l") : COMPOUND_STRING("\n"));
            StringAppend(gStringVar4, EntrantName(entrant));
            StringAppend(gStringVar4, COMPOUND_STRING(": "));
            AppendNumber(sQualifier.core.wins[entrant]);
            StringAppend(gStringVar4, balance < 0 ? COMPOUND_STRING(" / -") : COMPOUND_STRING(" / +"));
            AppendNumber(balance < 0 ? -balance : balance);
        }
    }
}

void JourneyQualifierPrepareBattle(void)
{
    gSpecialVar_Result = FALSE;
    if (!sQualifier.active || !sQualifier.core.prepared || !JourneyQualifierCurrentTrainer()
        || sQualifier.battlePrepared) return;
    JourneyQualifierRestoreParty();
    memset(&gTrainerBattleParameter, 0, sizeof(gTrainerBattleParameter));
    TRAINER_BATTLE_PARAM.objEventLocalIdA = 14;
    TRAINER_BATTLE_PARAM.opponentA = JourneyQualifierCurrentTrainer();
    TRAINER_BATTLE_PARAM.defeatTextA = (u8 *)sDefeat;
    gBattleTypeFlags = BATTLE_TYPE_TRAINER;
    sQualifier.battlePrepared = TRUE;
    sQualifier.battleStarted = sQualifier.battleReturned = FALSE;
    gSpecialVar_Result = TRUE;
}

bool32 JourneyQualifierBattleReady(void)
{
    return sQualifier.active && sQualifier.battlePrepared && !sQualifier.battleStarted
        && sQualifier.core.prepared && JourneyQualifierCurrentTrainer()
        && TRAINER_BATTLE_PARAM.opponentA == JourneyQualifierCurrentTrainer()
        && gBattleTypeFlags == BATTLE_TYPE_TRAINER;
}

void JourneyQualifierBattleStarted(void)
{
    sQualifier.battleStarted = TRUE;
}

void JourneyQualifierBattleReturned(void)
{
    if (sQualifier.battleStarted) sQualifier.battleReturned = TRUE;
}

void JourneyQualifierFinishBattle(void)
{
    u32 outcome;
    u8 playerLeft = 0, opponentLeft = 0;
    gSpecialVar_Result = FALSE;
    if (!sQualifier.active || !sQualifier.battlePrepared || !sQualifier.battleReturned) return;
    outcome = gBattleOutcome == B_OUTCOME_WON ? 1 : gBattleOutcome == B_OUTCOME_DREW ? 0 : 2;
    for (u32 i = 0; i < PARTY_SIZE; i++)
    {
        playerLeft += GetMonData(&gPlayerParty[i], MON_DATA_SPECIES)
            && !GetMonData(&gPlayerParty[i], MON_DATA_IS_EGG) && GetMonData(&gPlayerParty[i], MON_DATA_HP) != 0;
        opponentLeft += GetMonData(&gEnemyParty[i], MON_DATA_SPECIES)
            && GetMonData(&gEnemyParty[i], MON_DATA_HP) != 0;
    }
    // Forfeit counts as defeat even when the party still has healthy members.
    if (outcome == 2) { playerLeft = 0; opponentLeft = max(1, opponentLeft); }
    if (!JourneyQualifierCoreResult(&sQualifier.core, outcome, playerLeft, opponentLeft)) return;
    sQualifier.battlePrepared = sQualifier.battleStarted = sQualifier.battleReturned = FALSE;
    JourneyQualifierRestoreParty();
    // Zero means a drawn battle: replay this unchanged fixture after healing.
    gSpecialVar_Result = outcome;
}

void JourneyQualifierAbort(void)
{
    JourneyQualifierRestoreParty();
    memset(&sQualifier, 0, sizeof(sQualifier));
    if (!JourneyQualifierWon()) VarSet(VAR_JOURNEY_QUALIFIER_STATE, 0);
}

void JourneyQualifierComplete(void)
{
    gSpecialVar_Result = FALSE;
    if (!sQualifier.active || sQualifier.core.stage != JOURNEY_QUALIFIER_CHAMPION
        || !sQualifier.core.finalPlayed || sQualifier.core.finalWinner != 0) return;
    JourneyQualifierRestoreParty();
    FlagSet(FLAG_JOURNEY_QUALIFIER_WON);
    VarSet(VAR_JOURNEY_QUALIFIER_STATE, QUALIFIER_STATE_CELEBRATION);
    sQualifier.active = sQualifier.snapshotValid = FALSE;
    gSpecialVar_Result = TRUE;
}

bool32 JourneyQualifierTrainer(const struct Trainer *trainer)
{
    if (!sQualifier.active) return FALSE;
    for (u32 hero = 1; hero < ARRAY_COUNT(sQualifierTrainers); hero++)
        if (trainer == GetTrainerStructFromId(sQualifierTrainers[hero])) return TRUE;
    return FALSE;
}

u32 JourneyQualifierTrainerLevel(const struct Trainer *trainer, u32 originalLevel)
{
    u32 highest = 0, mean = JourneyWildMean();
    for (u32 i = 0; i < trainer->partySize; i++) highest = max(highest, trainer->party[i].lvl);
    if (originalLevel >= highest) return min(mean + 5, 100);
    return min((mean > 1 ? mean - 1 : 1) + Random() % 6, 100);
}
