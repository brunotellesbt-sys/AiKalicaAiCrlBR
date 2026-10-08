#include "global.h"
#include "data.h"
#include "battle_setup.h"
#include "constants/pokemon.h"
#include "constants/trainers.h"
#include "constants/battle.h"
#include "constants/items.h"
#include "item.h"
#include "move.h"
#include "constants/flags.h"
#include "constants/event_objects.h"
#include "constants/regions.h"
#include "constants/vars.h"
#include <stddef.h>
const unsigned journey_fixture_abi[] = {
    sizeof(struct Trainer), sizeof(struct TrainerMon), sizeof(struct Pokemon),
    offsetof(struct Trainer, party), offsetof(struct Trainer, trainerClass),
    offsetof(struct TrainerMon, lvl), MON_DATA_LEVEL, MON_DATA_SPECIES,
    TRAINER_CLASS_LEADER, TRAINER_CLASS_LEADER_FRLG, BATTLE_TYPE_TRAINER,
    TRAINERS_COUNT, DIFFICULTY_NORMAL,
    offsetof(TrainerBattleParameter, params.opponentA),
    offsetof(TrainerBattleParameter, params.opponentB),
    TRAINER_PARTNER(2), ITEM_HM_DIVE,
#ifdef FLAG_JOURNEY_WATER_HMS_GIVEN
    ITEM_HM_SURF, ITEM_HM_DIVE, ITEM_HM_WATERFALL,
    ITEM_TM_CUT, ITEM_TM_FLY, ITEM_TM_STRENGTH, ITEM_TM_FLASH, ITEM_TM_ROCK_SMASH,
    sizeof(struct TmHmIndexKey), offsetof(struct TmHmIndexKey, itemId), offsetof(struct TmHmIndexKey, moveId),
    sizeof(struct MoveInfo), offsetof(struct MoveInfo, effect) + sizeof(enum BattleMoveEffects),
    TYPE_GRASS, TYPE_ROCK
#ifdef GUARD_JOURNEY_RIVAL_H
    , offsetof(struct SaveBlock2, playerGender), OBJ_EVENT_GFX_BLUE,
    OBJ_EVENT_GFX_GREEN_NORMAL, OBJ_EVENT_GFX_RED_NORMAL, OBJ_EVENT_GFX_JOURNEY_GYM_BLUE,
    TRAINER_PIC_LEAF, TRAINER_PIC_RED, TRAINER_PIC_RIVAL_EARLY_FRLG,
    TRAINER_PIC_RIVAL_LATE_FRLG, TRAINER_PIC_CHAMPION_RIVAL_FRLG,
    OBJ_EVENT_GFX_VAR_0, offsetof(struct Trainer, trainerPic), sizeof(enum TrainerPicID),
    offsetof(struct SaveBlock2, playerRegion), REGION_KANTO
#endif
#endif
#ifdef FLAG_JOURNEY_FAMILY_STARTER_RECEIVED
    , MON_DATA_HP, MON_DATA_MAX_HP, VAR_STARTER_MON_FRLG, FLAG_SYS_POKEDEX_GET, REGION_HOENN,
      SPECIES_TREECKO, SPECIES_TORCHIC, SPECIES_MUDKIP, VAR_STARTER_MON,
      ITEM_MACH_BIKE, ITEM_BIKE_VOUCHER, FLAG_GOT_BICYCLE, FLAG_RECEIVED_BIKE, FLAG_GOT_BIKE_VOUCHER, BATTLE_TYPE_FIRST_BATTLE, MON_DATA_IS_EGG, FLAG_BADGE01_GET
#endif
};
