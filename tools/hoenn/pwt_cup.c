#include "global.h"
#include "journey_pwt_cup.h"
#include "random.h"

static void MiniLeague(const struct JourneyCup *cup, u16 entrant, s32 *points, s32 *difference, s32 *scored)
{
    u32 slot, group = cup->groupOf[entrant];
    s32 delta = (s32)cup->scored[entrant] - cup->conceded[entrant];
    *points = *difference = *scored = 0;
    for (slot = 0; slot < cup->groupSize[group]; slot++)
    {
        u16 other = cup->groups[group][slot];
        if (other == entrant || !(cup->playedMask[entrant] & (1 << slot))) continue;
        if (cup->points[other] != cup->points[entrant]
            || (s32)cup->scored[other] - cup->conceded[other] != delta
            || cup->scored[other] != cup->scored[entrant]) continue;
        *points += cup->headToHead[entrant][slot] > 0 ? 3 : cup->headToHead[entrant][slot] == 0 ? 1 : 0;
        *difference += (s32)cup->goalsFor[entrant][slot] - cup->goalsAgainst[entrant][slot];
        *scored += cup->goalsFor[entrant][slot];
    }
}

static bool32 Higher(const struct JourneyCup *cup, u16 a, u16 b)
{
    s32 da = (s32)cup->scored[a] - cup->conceded[a];
    s32 db = (s32)cup->scored[b] - cup->conceded[b];
    if (cup->points[a] != cup->points[b]) return cup->points[a] > cup->points[b];
    if (da != db) return da > db;
    if (cup->scored[a] != cup->scored[b]) return cup->scored[a] > cup->scored[b];
    {
        s32 pa, pb, da, db, sa, sb;
        MiniLeague(cup, a, &pa, &da, &sa); MiniLeague(cup, b, &pb, &db, &sb);
        if (pa != pb) return pa > pb;
        if (da != db) return da > db;
        if (sa != sb) return sa > sb;
    }
    if (cup->tieSeed[a] != cup->tieSeed[b]) return cup->tieSeed[a] > cup->tieSeed[b];
    return a < b;
}

u16 JourneyCupRankedEntrant(const struct JourneyCup *cup, u32 group, u32 rank)
{
    u16 order[JOURNEY_CUP_GROUP_SIZE];
    u32 i, j;
    if (group >= cup->groupCount || rank >= cup->groupSize[group]) return JOURNEY_CUP_EMPTY;
    for (i = 0; i < cup->groupSize[group]; i++)
    {
        u16 entrant = cup->groups[group][i];
        for (j = i; j > 0 && Higher(cup, entrant, order[j - 1]); j--) order[j] = order[j - 1];
        order[j] = entrant;
    }
    return order[rank];
}

static void Score(struct JourneyCup *cup, u16 a, u16 b, u8 sa, u8 sb, u32 outcome)
{
    cup->played[a]++; cup->played[b]++;
    cup->scored[a] += sa; cup->scored[b] += sb;
    cup->conceded[a] += sb; cup->conceded[b] += sa;
    cup->playedMask[a] |= 1 << cup->groupSlot[b];
    cup->playedMask[b] |= 1 << cup->groupSlot[a];
    cup->goalsFor[a][cup->groupSlot[b]] = sa; cup->goalsFor[b][cup->groupSlot[a]] = sb;
    cup->goalsAgainst[a][cup->groupSlot[b]] = sb; cup->goalsAgainst[b][cup->groupSlot[a]] = sa;
    if (outcome == 0)
    {
        cup->points[a]++; cup->points[b]++;
    }
    else
    {
        u16 winner = outcome == 1 ? a : b, loser = outcome == 1 ? b : a;
        cup->points[winner] += 3; cup->wins[winner]++;
        cup->headToHead[winner][cup->groupSlot[loser]] = 1;
        cup->headToHead[loser][cup->groupSlot[winner]] = -1;
    }
}

bool32 JourneyCupInit(struct JourneyCup *cup, const u16 *ids, u32 count)
{
    u16 order[JOURNEY_CUP_MAX_ENTRANTS], temporary;
    u32 i, j, groups = 1, cursor = 0;
    if (count < 6 || count > JOURNEY_CUP_MAX_ENTRANTS) return FALSE;
    // A power-of-two group count gives exactly 2^n qualified entrants.
    while ((count + groups - 1) / groups > JOURNEY_CUP_GROUP_SIZE) groups *= 2;
    if (groups > JOURNEY_CUP_MAX_GROUPS || count / groups < 3) return FALSE;
    for (i = 0; i < count; i++)
    {
        if (ids[i] == JOURNEY_CUP_EMPTY && i != 0) return FALSE;
        for (j = 0; j < i; j++) if (ids[i] == ids[j]) return FALSE;
    }
    memset(cup, 0, sizeof(*cup));
    cup->count = count; cup->groupCount = groups; cup->opponent = JOURNEY_CUP_EMPTY;
    for (i = 0; i < count; i++)
    {
        cup->entrants[i] = ids[i]; order[i] = i; cup->tieSeed[i] = Random();
    }
    for (i = count - 1; i > 0; i--)
    {
        j = Random() % (i + 1); temporary = order[i]; order[i] = order[j]; order[j] = temporary;
    }
    for (i = 0; i < groups; i++)
    {
        u32 size = count / groups + (i < count % groups);
        cup->groupSize[i] = size;
        cup->maxGroupRounds = max(cup->maxGroupRounds, size + (size & 1) - 1);
        for (j = 0; j < size; j++)
        {
            u16 entrant = order[cursor++];
            cup->groups[i][j] = entrant; cup->groupOf[entrant] = i; cup->groupSlot[entrant] = j;
        }
    }
    for (i = 0; i < ARRAY_COUNT(cup->bracket); i++) cup->bracket[i] = JOURNEY_CUP_EMPTY;
    return TRUE;
}

static void Qualify(struct JourneyCup *cup)
{
    u32 group, slot, size = cup->groupCount * 2;
    cup->leafBase = size - 1;
    for (group = 0; group < cup->groupCount; group++)
    {
        // Winners and runners-up from the same group occupy opposite halves.
        // First knockout matches always cross adjacent groups.
        slot = group / 2 + (group & 1) * (cup->groupCount / 2);
        if (cup->groupCount == 1)
        {
            cup->bracket[cup->leafBase] = JourneyCupRankedEntrant(cup, 0, 0);
            cup->bracket[cup->leafBase + 1] = JourneyCupRankedEntrant(cup, 0, 1);
            break;
        }
        cup->bracket[cup->leafBase + slot * 2] = JourneyCupRankedEntrant(cup, group, 0);
        cup->bracket[cup->leafBase + slot * 2 + 1] = JourneyCupRankedEntrant(cup, group ^ 1, 1);
    }
    cup->stage = JOURNEY_CUP_ELIMINATED;
    for (slot = cup->leafBase; slot < cup->leafBase + size; slot++)
        if (cup->bracket[slot] == 0)
        {
            cup->playerNode = slot; cup->stage = JOURNEY_CUP_KNOCKOUT;
        }
    cup->round = 0; cup->prepared = FALSE;
}

bool32 JourneyCupNext(struct JourneyCup *cup, JourneyCupSimulate simulate)
{
    u32 group, i, round;
    if (cup->prepared) return cup->opponent != JOURNEY_CUP_EMPTY;
    if (cup->stage == JOURNEY_CUP_GROUP_STAGE)
    {
        while (cup->round < cup->maxGroupRounds)
        {
            cup->opponent = JOURNEY_CUP_EMPTY;
            for (group = 0; group < cup->groupCount; group++)
            {
                u16 order[JOURNEY_CUP_GROUP_SIZE];
                u32 count = cup->groupSize[group], padded = count + (count & 1);
                if (cup->round >= padded - 1) continue;
                for (i = 0; i < padded; i++) order[i] = i < count ? cup->groups[group][i] : JOURNEY_CUP_EMPTY;
                for (round = 0; round < cup->round; round++)
                {
                    u16 last = order[padded - 1];
                    for (i = padded - 1; i > 1; i--) order[i] = order[i - 1];
                    order[1] = last;
                }
                for (i = 0; i < padded / 2; i++)
                {
                    u16 a = order[i], b = order[padded - 1 - i];
                    u8 sa, sb;
                    if (a == JOURNEY_CUP_EMPTY || b == JOURNEY_CUP_EMPTY) continue;
                    if (a == 0 || b == 0) { cup->opponent = a == 0 ? b : a; continue; }
                    simulate(cup->entrants[a], cup->entrants[b], &sa, &sb);
                    Score(cup, a, b, sa, sb, sa > sb ? 1 : sa < sb ? 2 : 0);
                }
            }
            if (cup->opponent != JOURNEY_CUP_EMPTY) { cup->prepared = TRUE; return TRUE; }
            cup->round++; // Human bye: resolve this round and continue automatically.
        }
        Qualify(cup);
    }
    if (cup->stage != JOURNEY_CUP_KNOCKOUT) return FALSE;
    if (cup->playerNode == 0) { cup->stage = JOURNEY_CUP_CHAMPION; return FALSE; }
    for (i = cup->leafBase; i < cup->leafBase * 2u + 1u; i += 2)
    {
        u16 a = cup->bracket[i], b = cup->bracket[i + 1];
        u8 sa, sb;
        if (a == 0 || b == 0) continue;
        simulate(cup->entrants[a], cup->entrants[b], &sa, &sb);
        cup->bracket[(i - 1) / 2] = sa >= sb ? a : b;
    }
    cup->opponent = cup->bracket[cup->playerNode & 1 ? cup->playerNode + 1 : cup->playerNode - 1];
    cup->prepared = TRUE;
    return cup->opponent != JOURNEY_CUP_EMPTY;
}

bool32 JourneyCupResult(struct JourneyCup *cup, u32 outcome, u8 scored, u8 conceded)
{
    if (!cup->prepared || cup->opponent == JOURNEY_CUP_EMPTY || outcome > 2 || scored > 6 || conceded > 6) return FALSE;
    if (cup->stage == JOURNEY_CUP_GROUP_STAGE)
    {
        Score(cup, 0, cup->opponent, scored, conceded, outcome);
        cup->round++;
    }
    else if (cup->stage == JOURNEY_CUP_KNOCKOUT)
    {
        if (outcome == 0) return TRUE; // A drawn knockout is replayed; NPC fixtures remain resolved.
        if (outcome == 2) { cup->stage = JOURNEY_CUP_ELIMINATED; }
        else
        {
            cup->playerNode = (cup->playerNode - 1) / 2;
            cup->bracket[cup->playerNode] = 0;
            cup->leafBase = (cup->leafBase - 1) / 2;
            cup->round++;
            if (cup->playerNode == 0) cup->stage = JOURNEY_CUP_CHAMPION;
        }
    }
    else return FALSE;
    cup->prepared = FALSE; cup->opponent = JOURNEY_CUP_EMPTY;
    return TRUE;
}
