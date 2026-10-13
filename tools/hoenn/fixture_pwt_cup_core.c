/* Host-only property checks. Never linked into the ROM. */
#include "global.h"
#include "journey_pwt_cup.h"
#include <assert.h>
#include <stdio.h>

static u32 seed;
static struct JourneyCup cup;
static u32 groupSimulations, knockoutSimulations;
static u8 seen[JOURNEY_CUP_MAX_ENTRANTS][JOURNEY_CUP_MAX_ENTRANTS];
u16 Random(void)
{
    seed = seed * 1664525u + 1013904223u;
    return seed >> 16;
}
static void Simulate(u16 a, u16 b, u8 *sa, u8 *sb)
{
    assert(a < cup.count && b < cup.count && a != b);
    if (cup.stage == JOURNEY_CUP_GROUP_STAGE)
    {
        assert(!seen[a][b] && !seen[b][a]);
        seen[a][b] = seen[b][a] = 1;
        groupSimulations++;
    }
    else knockoutSimulations++;
    *sa = 6; *sb = Random() % 6;
    if (Random() & 1) { u8 t = *sa; *sa = *sb; *sb = t; }
}

static void Run(u32 count, u32 initialSeed, bool32 loseKnockout)
{
    u16 ids[JOURNEY_CUP_MAX_ENTRANTS];
    u32 i, expectedGames = 0, humanGroupMatches = 0, humanMatches = 0;
    seed = initialSeed; groupSimulations = knockoutSimulations = 0;
    memset(seen, 0, sizeof(seen));
    for (i = 0; i < count; i++) ids[i] = i;
    ids[0] = JOURNEY_CUP_EMPTY;
    assert(JourneyCupInit(&cup, ids, count));
    for (i = 0; i < cup.groupCount; i++)
    {
        u32 size = cup.groupSize[i];
        assert(size >= 3 && size <= 6);
        expectedGames += size * (size - 1) / 2;
    }
    while (JourneyCupNext(&cup, Simulate))
    {
        u16 opponent = cup.opponent;
        u32 stage = cup.stage, simulationsBefore = groupSimulations + knockoutSimulations;
        assert(opponent > 0 && opponent < count);
        // Reading standings/re-opening a round must not simulate its games twice.
        assert(JourneyCupNext(&cup, Simulate));
        assert(opponent == cup.opponent);
        assert(groupSimulations + knockoutSimulations == simulationsBefore);
        if (stage == JOURNEY_CUP_GROUP_STAGE)
        {
            assert(cup.groupOf[opponent] == cup.groupOf[0]);
            assert(!seen[0][opponent]);
            seen[0][opponent] = seen[opponent][0] = 1;
            humanGroupMatches++;
        }
        else
        {
            if (cup.round == 0 && cup.groupCount > 1)
                assert(cup.groupOf[opponent] != cup.groupOf[0]);
            // A drawn knockout must retain the exact fixture for a replay.
            assert(JourneyCupResult(&cup, 0, 6, 6));
            assert(JourneyCupNext(&cup, Simulate));
            assert(cup.opponent == opponent);
            assert(groupSimulations + knockoutSimulations == simulationsBefore);
        }
        humanMatches++;
        assert(humanMatches < 20);
        assert(JourneyCupResult(&cup, loseKnockout && stage == JOURNEY_CUP_KNOCKOUT ? 2 : 1,
                               loseKnockout && stage == JOURNEY_CUP_KNOCKOUT ? 0 : 6,
                               loseKnockout && stage == JOURNEY_CUP_KNOCKOUT ? 6 : 0));
    }
    assert(cup.stage == (loseKnockout ? JOURNEY_CUP_ELIMINATED : JOURNEY_CUP_CHAMPION));
    assert(humanGroupMatches == cup.groupSize[cup.groupOf[0]] - 1u);
    assert(groupSimulations + humanGroupMatches == expectedGames);
    for (i = 0; i < count; i++) assert(cup.played[i] == cup.groupSize[cup.groupOf[i]] - 1);
    for (i = 0; i < cup.groupCount; i++)
    {
        u32 rank, mask = 0;
        for (rank = 0; rank < cup.groupSize[i]; rank++)
        {
            u16 entrant = JourneyCupRankedEntrant(&cup, i, rank);
            assert(entrant < count && cup.groupOf[entrant] == i);
            assert(!(mask & (1 << cup.groupSlot[entrant])));
            mask |= 1 << cup.groupSlot[entrant];
        }
        assert(mask == (1u << cup.groupSize[i]) - 1);
    }
}

int main(void)
{
    u32 count, trial, runs = 0;
    u16 invalid[] = {JOURNEY_CUP_EMPTY, 1, 1, 3, 4, 5};
    assert(!JourneyCupInit(&cup, invalid, 6));
    assert(!JourneyCupInit(&cup, invalid, 5));
    for (count = 6; count <= 256; count++)
        for (trial = 0; trial < 20; trial++)
        {
            Run(count, trial * 31 + count, trial & 1);
            runs++;
        }
    printf("%u tournaments passed: all sizes 6..256, complete round-robin, unique qualification, drawn knockout replay, elimination and championship.\n", runs);
    return 0;
}
