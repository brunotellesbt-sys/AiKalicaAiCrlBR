#include "global.h"
#include "data.h"
#include "battle_setup.h"
#include "constants/pokemon.h"
#include "constants/trainers.h"
#include "constants/battle.h"
#include <stddef.h>
const unsigned journey_fixture_abi[] = {
    sizeof(struct Trainer), sizeof(struct TrainerMon), sizeof(struct Pokemon),
    offsetof(struct Trainer, party), offsetof(struct Trainer, trainerClass),
    offsetof(struct TrainerMon, lvl), MON_DATA_LEVEL, MON_DATA_SPECIES,
    TRAINER_CLASS_LEADER, TRAINER_CLASS_LEADER_FRLG, BATTLE_TYPE_TRAINER,
    TRAINERS_COUNT, DIFFICULTY_NORMAL,
    offsetof(TrainerBattleParameter, params.opponentA),
    offsetof(TrainerBattleParameter, params.opponentB),
    TRAINER_PARTNER(2)
};
