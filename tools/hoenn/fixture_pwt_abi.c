// Compile with -include <candidate>/src/journey_pwt.c; never link into the ROM.
const u32 gPWTFixtureABI[] = {
    sizeof(struct PWTState), offsetof(struct PWTState, bracket),
    offsetof(struct PWTState, size), offsetof(struct PWTState, round),
    offsetof(struct PWTState, playerNode), offsetof(struct PWTState, active),
    offsetof(struct SaveBlock2, frontier.battlePoints), offsetof(struct SaveBlock1, money),
    offsetof(struct Pokemon, attack), offsetof(struct Pokemon, speed),
    sizeof(struct PWTTrainer), MON_DATA_EXP, MON_DATA_IS_EGG,
    ITEM_LEFTOVERS, ITEM_SITRUS_BERRY,
    offsetof(struct BattlePokemon, attack), offsetof(struct BattlePokemon, speed),
    offsetof(struct Pokemon, level),
    B_OUTCOME_FORFEITED, MON_DATA_MOVE1,
    offsetof(struct BattlePokemon, maxHP), offsetof(struct Pokemon, maxHP),
};
