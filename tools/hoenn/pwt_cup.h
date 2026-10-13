#ifndef GUARD_JOURNEY_PWT_CUP_H
#define GUARD_JOURNEY_PWT_CUP_H

#define JOURNEY_CUP_MAX_ENTRANTS 256
#define JOURNEY_CUP_MAX_GROUPS 64
#define JOURNEY_CUP_GROUP_SIZE 6
#define JOURNEY_CUP_EMPTY 0xFFFF
#define JOURNEY_CUP_GROUP_STAGE 0
#define JOURNEY_CUP_KNOCKOUT 1
#define JOURNEY_CUP_CHAMPION 2
#define JOURNEY_CUP_ELIMINATED 3

// Entrant zero is always the human. IDs are catalog IDs, not trainer IDs.
struct JourneyCup
{
    u16 entrants[JOURNEY_CUP_MAX_ENTRANTS];
    u16 groups[JOURNEY_CUP_MAX_GROUPS][JOURNEY_CUP_GROUP_SIZE];
    u16 bracket[2 * JOURNEY_CUP_MAX_GROUPS * 2 - 1];
    u16 scored[JOURNEY_CUP_MAX_ENTRANTS], conceded[JOURNEY_CUP_MAX_ENTRANTS];
    u16 tieSeed[JOURNEY_CUP_MAX_ENTRANTS];
    s8 headToHead[JOURNEY_CUP_MAX_ENTRANTS][JOURNEY_CUP_GROUP_SIZE];
    u8 goalsFor[JOURNEY_CUP_MAX_ENTRANTS][JOURNEY_CUP_GROUP_SIZE];
    u8 goalsAgainst[JOURNEY_CUP_MAX_ENTRANTS][JOURNEY_CUP_GROUP_SIZE];
    u8 playedMask[JOURNEY_CUP_MAX_ENTRANTS];
    u8 points[JOURNEY_CUP_MAX_ENTRANTS], played[JOURNEY_CUP_MAX_ENTRANTS];
    u8 wins[JOURNEY_CUP_MAX_ENTRANTS], groupOf[JOURNEY_CUP_MAX_ENTRANTS];
    u8 groupSlot[JOURNEY_CUP_MAX_ENTRANTS], groupSize[JOURNEY_CUP_MAX_GROUPS];
    u16 count, opponent, playerNode, leafBase;
    u8 groupCount, round, maxGroupRounds, stage;
    bool8 prepared;
};

typedef void (*JourneyCupSimulate)(u16, u16, u8 *, u8 *);
bool32 JourneyCupInit(struct JourneyCup *, const u16 *, u32);
bool32 JourneyCupNext(struct JourneyCup *, JourneyCupSimulate);
bool32 JourneyCupResult(struct JourneyCup *, u32, u8, u8);
u16 JourneyCupRankedEntrant(const struct JourneyCup *, u32, u32);
#endif
