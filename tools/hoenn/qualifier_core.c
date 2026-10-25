#include "global.h"
#include "journey_qualifier_core.h"

static u32 DrawRandom(u32 *seed)
{
    *seed ^= *seed << 13;
    *seed ^= *seed >> 17;
    *seed ^= *seed << 5;
    return *seed;
}

static bool32 Higher(const struct JourneyQualifierCore *core, u8 a, u8 b)
{
    if (core->wins[a] != core->wins[b]) return core->wins[a] > core->wins[b];
    if (core->balance[a] != core->balance[b]) return core->balance[a] > core->balance[b];
    if (core->survivors[a] != core->survivors[b]) return core->survivors[a] > core->survivors[b];
    return core->tieOrder[a] > core->tieOrder[b];
}

u8 JourneyQualifierCoreRank(const struct JourneyQualifierCore *core, u32 group, u32 rank)
{
    u8 order[JOURNEY_QUALIFIER_GROUP_SIZE];
    u32 i, j;
    if (group >= JOURNEY_QUALIFIER_GROUPS || rank >= JOURNEY_QUALIFIER_GROUP_SIZE)
        return JOURNEY_QUALIFIER_EMPTY;
    for (i = 0; i < JOURNEY_QUALIFIER_GROUP_SIZE; i++)
    {
        u8 entrant = core->groups[group][i];
        for (j = i; j && Higher(core, entrant, order[j - 1]); j--)
            order[j] = order[j - 1];
        order[j] = entrant;
    }
    return order[rank];
}

bool32 JourneyQualifierCoreInitDraw(struct JourneyQualifierCore *core, const u8 *heroes, const u8 *order, u32 seed, bool32 immediateGroupLoss)
{
    static const u8 schedule[JOURNEY_QUALIFIER_GROUP_MATCHES][2] = {
        {0, 1}, {3, 4}, {1, 2}, {3, 5}, {0, 2}, {4, 5}
    };
    u32 i, j;
    u8 tie[JOURNEY_QUALIFIER_ENTRANTS] = {0, 1, 2, 3, 4, 5};
    if (heroes[0] != 0 || order[0] != 0) return FALSE;
    for (i = 0; i < JOURNEY_QUALIFIER_ENTRANTS; i++)
    {
        if (order[i] >= JOURNEY_QUALIFIER_ENTRANTS || (i && (!heroes[i] || heroes[i] > 6))) return FALSE;
        for (j = 0; j < i; j++)
            if (order[i] == order[j] || heroes[i] == heroes[j]) return FALSE;
    }
    memset(core, 0, sizeof(*core));
    memcpy(core->hero, heroes, sizeof(core->hero));
    for (i = 0; i < JOURNEY_QUALIFIER_ENTRANTS; i++)
        core->groups[i / JOURNEY_QUALIFIER_GROUP_SIZE][i % JOURNEY_QUALIFIER_GROUP_SIZE] = order[i];
    for (i = 0; i < JOURNEY_QUALIFIER_GROUP_MATCHES; i++)
    {
        core->ledger[i].a = order[schedule[i][0]];
        core->ledger[i].b = order[schedule[i][1]];
    }
    seed ^= 0xA5A58D31u;
    if (!seed) seed = 0x6D2B79F5u;
    for (i = JOURNEY_QUALIFIER_ENTRANTS - 1; i; i--)
    {
        u8 temporary;
        j = DrawRandom(&seed) % (i + 1);
        temporary = tie[i]; tie[i] = tie[j]; tie[j] = temporary;
    }
    for (i = 0; i < JOURNEY_QUALIFIER_ENTRANTS; i++) core->tieOrder[tie[i]] = i;
    core->opponent = core->finalWinner = JOURNEY_QUALIFIER_EMPTY;
    core->finalists[0] = core->finalists[1] = JOURNEY_QUALIFIER_EMPTY;
    core->immediateGroupLoss = immediateGroupLoss;
    return TRUE;
}

bool32 JourneyQualifierCoreInit(struct JourneyQualifierCore *core, const u8 *heroes, u32 seed, bool32 immediateGroupLoss)
{
    u8 order[JOURNEY_QUALIFIER_ENTRANTS] = {0, 1, 2, 3, 4, 5};
    u32 random = seed ? seed : 0x62C72E31u;
    for (u32 i = JOURNEY_QUALIFIER_ENTRANTS - 1; i > 1; i--)
    {
        u32 j = 1 + DrawRandom(&random) % i;
        u8 temporary = order[i]; order[i] = order[j]; order[j] = temporary;
    }
    return JourneyQualifierCoreInitDraw(core, heroes, order, seed, immediateGroupLoss);
}

static void Record(struct JourneyQualifierCore *core, struct JourneyQualifierMatch *match, u8 leftA, u8 leftB)
{
    u8 a = match->a, b = match->b;
    match->leftA = leftA; match->leftB = leftB; match->resolved = TRUE;
    core->playedMask[a] |= 1 << b; core->playedMask[b] |= 1 << a;
    core->wins[leftA ? a : b]++;
    core->balance[a] += (s32)leftA - leftB;
    core->balance[b] += (s32)leftB - leftA;
    core->survivors[a] += leftA; core->survivors[b] += leftB;
}

u32 JourneyQualifierCoreNext(struct JourneyQualifierCore *core, JourneyQualifierSimulate simulate)
{
    if (core->stage == JOURNEY_QUALIFIER_CHAMPION) return JOURNEY_QUALIFIER_WON;
    if (core->stage == JOURNEY_QUALIFIER_FAILED) return JOURNEY_QUALIFIER_ELIMINATED;
    if (core->prepared) return JOURNEY_QUALIFIER_MATCH;
    while (core->cursor < JOURNEY_QUALIFIER_GROUP_MATCHES)
    {
        struct JourneyQualifierMatch *match = &core->ledger[core->cursor];
        u8 leftA, leftB;
        if (!match->a || !match->b)
        {
            core->opponent = match->a ? match->a : match->b;
            core->prepared = TRUE;
            return JOURNEY_QUALIFIER_MATCH;
        }
        simulate(core->hero[match->a], core->hero[match->b], &leftA, &leftB);
        // Invalid simulation cannot create a phantom winner or advance a game.
        if (leftA > 6 || leftB > 6 || (!leftA == !leftB))
        {
            core->stage = JOURNEY_QUALIFIER_FAILED;
            return JOURNEY_QUALIFIER_ELIMINATED;
        }
        Record(core, match, leftA, leftB);
        core->cursor++;
    }
    core->finalists[0] = JourneyQualifierCoreRank(core, 0, 0);
    core->finalists[1] = JourneyQualifierCoreRank(core, 1, 0);
    if (core->finalists[0] != 0)
    {
        core->stage = JOURNEY_QUALIFIER_FAILED;
        return JOURNEY_QUALIFIER_ELIMINATED;
    }
    core->stage = JOURNEY_QUALIFIER_FINAL;
    core->opponent = core->finalists[1];
    core->prepared = TRUE;
    return JOURNEY_QUALIFIER_MATCH;
}

bool32 JourneyQualifierCoreResult(struct JourneyQualifierCore *core, u32 outcome, u8 playerLeft, u8 opponentLeft)
{
    if (!core->prepared || core->opponent >= JOURNEY_QUALIFIER_ENTRANTS
        || outcome > 2 || playerLeft > 6 || opponentLeft > 6) return FALSE;
    if (outcome == 0) return TRUE; // A drawn match is replayed without scoring it twice.
    if ((outcome == 1 && (!playerLeft || opponentLeft))
        || (outcome == 2 && (playerLeft || !opponentLeft))) return FALSE;
    if (core->stage == JOURNEY_QUALIFIER_GROUP_STAGE)
    {
        struct JourneyQualifierMatch *match;
        if (core->cursor >= JOURNEY_QUALIFIER_GROUP_MATCHES) return FALSE;
        match = &core->ledger[core->cursor];
        if (match->resolved || (match->a && match->b)) return FALSE;
        Record(core, match, match->a ? opponentLeft : playerLeft, match->a ? playerLeft : opponentLeft);
        core->cursor++;
        if (outcome == 2 && core->immediateGroupLoss) core->stage = JOURNEY_QUALIFIER_FAILED;
    }
    else if (core->stage == JOURNEY_QUALIFIER_FINAL)
    {
        core->finalPlayed = TRUE;
        core->finalWinner = outcome == 1 ? 0 : core->opponent;
        core->stage = outcome == 1 ? JOURNEY_QUALIFIER_CHAMPION : JOURNEY_QUALIFIER_FAILED;
    }
    else return FALSE;
    core->prepared = FALSE;
    core->opponent = JOURNEY_QUALIFIER_EMPTY;
    return TRUE;
}
