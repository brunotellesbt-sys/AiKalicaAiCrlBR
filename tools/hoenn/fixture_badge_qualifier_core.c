/* Host-only exhaustive competition checks; never linked into the ROM. */
#include "global.h"
#include "journey_qualifier_core.h"
#include <assert.h>
#include <stdio.h>

static struct JourneyQualifierCore core;
static u32 mask, simulations, runs, recoveries, perfectTies;
static const u8 heroes[6] = {0, 2, 3, 4, 5, 6};

static u8 Left(u32 round, bool32 sideA)
{
    bool32 wonA = !(mask & (1u << round));
    return wonA == sideA ? 1 + round % 6 : 0;
}

static void Simulate(u8 a, u8 b, u8 *leftA, u8 *leftB)
{
    assert(a && b && a != b && a <= 6 && b <= 6);
    assert(core.cursor < 6 && !core.ledger[core.cursor].resolved);
    simulations++;
    *leftA = Left(core.cursor, TRUE);
    *leftB = Left(core.cursor, FALSE);
}

static u8 ReferenceWinner(u32 group)
{
    u8 wins[6] = {0}, survivors[6] = {0}, best = core.groups[group][0];
    s32 balance[6] = {0};
    for (u32 i = 0; i < 6; i++)
    {
        u8 a = core.ledger[i].a, b = core.ledger[i].b;
        u8 leftA = Left(i, TRUE), leftB = Left(i, FALSE);
        wins[leftA ? a : b]++;
        survivors[a] += leftA; survivors[b] += leftB;
        balance[a] += (s32)leftA - leftB;
        balance[b] += (s32)leftB - leftA;
    }
    assert(!memcmp(wins, core.wins, sizeof(wins)));
    assert(!memcmp(survivors, core.survivors, sizeof(survivors)));
    for (u32 i = 0; i < 6; i++) assert(balance[i] == core.balance[i]);
    for (u32 i = 1; i < 3; i++)
    {
        u8 candidate = core.groups[group][i];
        if (wins[candidate] > wins[best]
            || (wins[candidate] == wins[best] && balance[candidate] > balance[best])
            || (wins[candidate] == wins[best] && balance[candidate] == balance[best]
                && survivors[candidate] > survivors[best])
            || (wins[candidate] == wins[best] && balance[candidate] == balance[best]
                && survivors[candidate] == survivors[best]
                && core.tieOrder[candidate] > core.tieOrder[best])) best = candidate;
    }
    return best;
}

static u32 BitCount(u32 value)
{
    u32 result = 0;
    for (; value; value >>= 1) result += value & 1;
    return result;
}

static void Run(const u8 *order, u32 outcomes, bool32 loseFinal, bool32 immediate)
{
    u32 status, groupBattles = 0, finalBattles = 0, losses = 0;
    mask = outcomes; simulations = 0;
    assert(JourneyQualifierCoreInitDraw(&core, heroes, order, outcomes * 91 + 1, immediate));
    while ((status = JourneyQualifierCoreNext(&core, Simulate)) == JOURNEY_QUALIFIER_MATCH)
    {
        struct JourneyQualifierCore pending = core;
        u32 oldSimulations = simulations, stage = core.stage;
        u8 playerLeft = stage == JOURNEY_QUALIFIER_FINAL ? (loseFinal ? 0 : 4) : Left(core.cursor, TRUE);
        u8 opponentLeft = stage == JOURNEY_QUALIFIER_FINAL ? (loseFinal ? 4 : 0) : Left(core.cursor, FALSE);
        assert(core.opponent > 0 && core.opponent < 6);
        assert(JourneyQualifierCoreNext(&core, Simulate) == JOURNEY_QUALIFIER_MATCH);
        assert(!memcmp(&pending, &core, sizeof(core)) && simulations == oldSimulations);
        assert(!JourneyQualifierCoreResult(&core, 3, 6, 0));
        assert(!JourneyQualifierCoreResult(&core, 1, 7, 0));
        assert(!JourneyQualifierCoreResult(&core, 1, 6, 1));
        assert(!JourneyQualifierCoreResult(&core, 2, 1, 6));
        assert(!memcmp(&pending, &core, sizeof(core)));
        // A draw replays the exact fixture, without recording another game.
        assert(JourneyQualifierCoreResult(&core, 0, 0, 0));
        assert(!memcmp(&pending, &core, sizeof(core)));
        if (stage == JOURNEY_QUALIFIER_GROUP_STAGE)
        {
            groupBattles++;
            assert(core.cursor == 0 || core.cursor == 4);
            assert(!core.ledger[core.cursor].a && core.ledger[core.cursor].b == core.opponent);
            assert(!core.ledger[core.cursor].resolved);
            losses += !playerLeft;
        }
        else
        {
            finalBattles++;
            assert(core.finalists[0] == 0 && core.finalists[1] == core.opponent);
            assert(core.opponent == ReferenceWinner(1));
        }
        assert(JourneyQualifierCoreResult(&core, playerLeft ? 1 : 2, playerLeft, opponentLeft));
        assert(!JourneyQualifierCoreResult(&core, playerLeft ? 1 : 2, playerLeft, opponentLeft));
        assert(groupBattles <= 2 && finalBattles <= 1);
    }
    if (immediate && losses)
    {
        assert(status == JOURNEY_QUALIFIER_ELIMINATED && !finalBattles);
        assert(groupBattles == 1 || groupBattles == 2);
        runs++;
        return;
    }
    assert(groupBattles == 2 && simulations == 4 && core.cursor == 6);
    u8 seen[6][6] = {{0}};
    for (u32 i = 0; i < 6; i++)
    {
        u8 a = core.ledger[i].a, b = core.ledger[i].b;
        assert(a != b && !seen[a][b] && core.ledger[i].resolved);
        seen[a][b] = seen[b][a] = 1;
        assert(core.ledger[i].leftA == Left(i, TRUE) && core.ledger[i].leftB == Left(i, FALSE));
    }
    for (u32 group = 0; group < 2; group++)
    {
        u32 wins = 0, ranked = 0;
        for (u32 slot = 0; slot < 3; slot++)
        {
            u8 entrant = core.groups[group][slot];
            assert(BitCount(core.playedMask[entrant]) == 2);
            wins += core.wins[entrant];
            for (u32 peer = 0; peer < 3; peer++)
                if (peer != slot) assert(seen[entrant][core.groups[group][peer]]);
            u8 rank = JourneyQualifierCoreRank(&core, group, slot);
            assert(!(ranked & (1u << rank)));
            ranked |= 1u << rank;
        }
        assert(wins == 3 && JourneyQualifierCoreRank(&core, group, 0) == ReferenceWinner(group));
    }
    if (ReferenceWinner(0) == 0)
    {
        assert(finalBattles == 1 && core.finalPlayed);
        assert(status == (loseFinal ? JOURNEY_QUALIFIER_ELIMINATED : JOURNEY_QUALIFIER_WON));
        assert(core.finalWinner == (loseFinal ? core.finalists[1] : 0));
        recoveries += losses > 0;
    }
    else assert(!finalBattles && status == JOURNEY_QUALIFIER_ELIMINATED);
    struct JourneyQualifierCore terminal = core;
    assert(JourneyQualifierCoreNext(&core, Simulate) == status);
    assert(!memcmp(&terminal, &core, sizeof(core)));
    runs++;
}

static void Permute(u8 *order, u32 slot)
{
    if (slot == 6)
    {
        for (u32 outcomes = 0; outcomes < 64; outcomes++)
            for (u32 immediate = 0; immediate < 2; immediate++)
                for (u32 finalLoss = 0; finalLoss < 2; finalLoss++)
                    Run(order, outcomes, finalLoss, immediate);
        return;
    }
    for (u32 i = slot; i < 6; i++)
    {
        u8 temporary = order[slot]; order[slot] = order[i]; order[i] = temporary;
        Permute(order, slot + 1);
        temporary = order[slot]; order[slot] = order[i]; order[i] = temporary;
    }
}

static void InvalidSimulation(u8 a, u8 b, u8 *leftA, u8 *leftB)
{
    (void)a; (void)b; *leftA = 1; *leftB = 1;
}

static void Controls(void)
{
    u8 order[6] = {0, 1, 2, 3, 4, 5}, badHeroes[6] = {0, 2, 2, 4, 5, 6};
    struct JourneyQualifierCore original;
    memset(&core, 0xA5, sizeof(core)); original = core;
    assert(!JourneyQualifierCoreInitDraw(&core, badHeroes, order, 1, FALSE));
    assert(!memcmp(&original, &core, sizeof(core)));
    order[5] = 4;
    assert(!JourneyQualifierCoreInitDraw(&core, heroes, order, 1, FALSE));
    assert(!memcmp(&original, &core, sizeof(core)));
    assert(JourneyQualifierCoreInit(&core, heroes, 0, FALSE));
    assert(JourneyQualifierCoreRank(&core, 2, 0) == JOURNEY_QUALIFIER_EMPTY);
    assert(JourneyQualifierCoreRank(&core, 0, 3) == JOURNEY_QUALIFIER_EMPTY);
    assert(!JourneyQualifierCoreResult(&core, 1, 6, 0));
    assert(JourneyQualifierCoreNext(&core, Simulate) == JOURNEY_QUALIFIER_MATCH);
    assert(JourneyQualifierCoreResult(&core, 1, 6, 0));
    assert(JourneyQualifierCoreNext(&core, InvalidSimulation) == JOURNEY_QUALIFIER_ELIMINATED);
    for (u32 seed = 0; seed < 1000; seed++)
    {
        assert(JourneyQualifierCoreInit(&core, heroes, seed, FALSE));
        u32 priority = 0, entrants = 0;
        for (u32 i = 0; i < 6; i++)
        {
            priority |= 1u << core.tieOrder[i];
            entrants |= 1u << core.groups[i / 3][i % 3];
        }
        assert(priority == 63 && entrants == 63 && core.groups[0][0] == 0);
        // Complete equality is resolved by the unique registration draw.
        for (u32 i = 0; i < 6; i++) core.wins[i] = 1;
        for (u32 group = 0; group < 2; group++)
        {
            u8 winner = JourneyQualifierCoreRank(&core, group, 0);
            for (u32 slot = 0; slot < 3; slot++)
                assert(core.tieOrder[winner] >= core.tieOrder[core.groups[group][slot]]);
        }
        perfectTies++;
    }
}

int main(void)
{
    u8 order[6] = {0, 1, 2, 3, 4, 5};
    Controls(); Permute(order, 1);
    assert(runs == 30720 && recoveries > 0 && perfectTies == 1000);
    printf("%u tournaments passed; %u group-loss recoveries; %u full-tie draws\n",
           runs, recoveries, perfectTies);
    return 0;
}
