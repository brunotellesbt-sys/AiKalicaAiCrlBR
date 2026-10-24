#ifndef GUARD_JOURNEY_QUALIFIER_CORE_H
#define GUARD_JOURNEY_QUALIFIER_CORE_H

#include "global.h"

#define JOURNEY_QUALIFIER_ENTRANTS 6
#define JOURNEY_QUALIFIER_GROUPS 2
#define JOURNEY_QUALIFIER_GROUP_SIZE 3
#define JOURNEY_QUALIFIER_GROUP_MATCHES 6
#define JOURNEY_QUALIFIER_EMPTY 255
#define JOURNEY_QUALIFIER_MATCH 1
#define JOURNEY_QUALIFIER_WON 2
#define JOURNEY_QUALIFIER_ELIMINATED 3

enum JourneyQualifierStage
{
    JOURNEY_QUALIFIER_GROUP_STAGE,
    JOURNEY_QUALIFIER_FINAL,
    JOURNEY_QUALIFIER_CHAMPION,
    JOURNEY_QUALIFIER_FAILED,
};

struct JourneyQualifierMatch
{
    u8 a, b, leftA, leftB;
    bool8 resolved;
};

struct JourneyQualifierCore
{
    // Entrant zero is the human; the other entries are canonical hero IDs.
    u8 hero[JOURNEY_QUALIFIER_ENTRANTS];
    u8 groups[JOURNEY_QUALIFIER_GROUPS][JOURNEY_QUALIFIER_GROUP_SIZE];
    u8 wins[JOURNEY_QUALIFIER_ENTRANTS];
    s8 balance[JOURNEY_QUALIFIER_ENTRANTS];
    u8 survivors[JOURNEY_QUALIFIER_ENTRANTS];
    u8 playedMask[JOURNEY_QUALIFIER_ENTRANTS];
    // A unique, seeded final draw criterion. It never implicitly favors zero.
    u8 tieOrder[JOURNEY_QUALIFIER_ENTRANTS];
    struct JourneyQualifierMatch ledger[JOURNEY_QUALIFIER_GROUP_MATCHES];
    u8 cursor, stage, opponent;
    u8 finalists[JOURNEY_QUALIFIER_GROUPS], finalWinner;
    bool8 prepared, finalPlayed, immediateGroupLoss;
};

typedef void (*JourneyQualifierSimulate)(u8 heroA, u8 heroB, u8 *leftA, u8 *leftB);

bool32 JourneyQualifierCoreInit(struct JourneyQualifierCore *, const u8 *heroes, u32 seed, bool32 immediateGroupLoss);
bool32 JourneyQualifierCoreInitDraw(struct JourneyQualifierCore *, const u8 *heroes, const u8 *order, u32 seed, bool32 immediateGroupLoss);
u32 JourneyQualifierCoreNext(struct JourneyQualifierCore *, JourneyQualifierSimulate);
bool32 JourneyQualifierCoreResult(struct JourneyQualifierCore *, u32 outcome, u8 playerLeft, u8 opponentLeft);
u8 JourneyQualifierCoreRank(const struct JourneyQualifierCore *, u32 group, u32 rank);

#endif
