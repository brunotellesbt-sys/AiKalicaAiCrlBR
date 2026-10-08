#include "global.h"
#include "data.h"
#include "battle_setup.h"
#include "constants/pokemon.h"
#include "constants/trainers.h"
#include "constants/battle.h"
#include "constants/items.h"
#include "constants/abilities.h"
#include "party_menu.h"
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
      ITEM_MACH_BIKE, ITEM_BIKE_VOUCHER, FLAG_GOT_BICYCLE, FLAG_RECEIVED_BIKE, FLAG_GOT_BIKE_VOUCHER, BATTLE_TYPE_FIRST_BATTLE, MON_DATA_IS_EGG, FLAG_BADGE01_GET, ITEM_MASTER_BALL,
      MON_DATA_ABILITY_NUM, SPECIES_FROAKIE, SPECIES_FROGADIER, SPECIES_GRENINJA,
      SPECIES_GRENINJA_ASH, SPECIES_GRENINJA_BATTLE_BOND,
      ABILITY_TORRENT, ABILITY_PROTEAN, ABILITY_BATTLE_BOND,
      sizeof(struct BattlePokemon), offsetof(struct BattlePokemon, species),
      MOVE_SURF, MOVE_WATER_SHURIKEN, FORM_CHANGE_END_BATTLE, FORM_CHANGE_FAINT,
      ITEM_MEGA_RING, ITEM_CHARIZARDITE_X, ITEM_CHARIZARDITE_Y, ITEM_LEFTOVERS,
      SPECIES_CHARIZARD, SPECIES_CHARIZARD_MEGA_X, SPECIES_CHARIZARD_MEGA_Y,
      SPECIES_RAYQUAZA, SPECIES_RAYQUAZA_MEGA, MOVE_DRAGON_ASCENT,
      ITEM_GRENINJITE, SPECIES_GRENINJA_MEGA, MON_DATA_MOVE1,
      offsetof(struct BattlePokemon, moves), MON_DATA_STATUS,
      offsetof(struct BattlePokemon, status1), MON_DATA_MET_LEVEL,
      SPECIES_GARCHOMP, SPECIES_GARCHOMP_MEGA_Z, ITEM_GARCHOMPITE_Z,
      offsetof(struct PartyMenu, slotId), offsetof(struct Pokemon, hp),
      offsetof(struct BattlePokemon, hp), MOVE_GROWL, MOVE_DARK_PULSE,
      MON_DATA_PERSONALITY, MON_DATA_OT_ID, MON_DATA_HELD_ITEM,
      offsetof(struct SaveBlock1, vars), VAR_SOOTOPOLIS_CITY_STATE, VAR_SKY_PILLAR_STATE, FLAG_SYS_WEATHER_CTRL,
      TRAINER_PARTNER(1), TRAINER_MAXIE_MOSSDEEP, TRAINER_TABITHA_MOSSDEEP,
      VAR_MOSSDEEP_SPACE_CENTER_STATE, FLAG_DEFEATED_MAGMA_SPACE_CENTER
#ifdef FLAG_KANTO_IS_CHAMPION
      , TRAINER_ELITE_FOUR_LORELEI, TRAINER_ELITE_FOUR_LORELEI_2, TRAINER_SIDNEY,
      FLAG_DEFEATED_LORELEI, FLAG_DEFEATED_ELITE_4_SIDNEY
      , TRAINER_ELITE_FOUR_BRUNO, TRAINER_ELITE_FOUR_AGATHA, TRAINER_ELITE_FOUR_LANCE,
      TRAINER_CHAMPION_FIRST_CHARMANDER, TRAINER_PHOEBE, TRAINER_GLACIA, TRAINER_DRAKE, TRAINER_WALLACE,
      FLAG_DEFEATED_BRUNO, FLAG_DEFEATED_AGATHA, FLAG_DEFEATED_LANCE, FLAG_DEFEATED_CHAMP,
      FLAG_DEFEATED_ELITE_4_PHOEBE, FLAG_DEFEATED_ELITE_4_GLACIA, FLAG_DEFEATED_ELITE_4_DRAKE
#endif
#endif
};
