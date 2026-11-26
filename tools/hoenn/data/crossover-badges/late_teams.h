// The competitive trainer pipeline selects legal moves and scales every member
// to the player's party. Keep both teams available at the Gen 4 cap.
#define JOURNEY_LATE_RIVAL_MON(monSpecies) \
    { .species = SPECIES_##monSpecies, .lvl = 50, .gender = TRAINER_MON_RANDOM_GENDER, \
      .iv = TRAINER_PARTY_IVS(20, 20, 20, 20, 20, 20), .ball = POKEBALL_COUNT, .nature = NATURE_HARDY }

[DIFFICULTY_NORMAL][TRAINER_JOURNEY_EREN_4] =
{
    .trainerName = _("EREN"),
    .trainerClass = TRAINER_CLASS_RIVAL,
    .trainerPic = TRAINER_PIC_JOURNEY_EREN_TITAN,
    .gender = TRAINER_GENDER_MALE,
    .encounterMusic = TRAINER_ENCOUNTER_MUSIC_MALE,
    .aiFlags = AI_FLAG_BASIC_TRAINER,
    .partySize = 6,
    .party = (const struct TrainerMon[]) {
        JOURNEY_LATE_RIVAL_MON(STEELIX),
        JOURNEY_LATE_RIVAL_MON(TYRANITAR),
        JOURNEY_LATE_RIVAL_MON(SCIZOR),
        JOURNEY_LATE_RIVAL_MON(DUSKNOIR),
        JOURNEY_LATE_RIVAL_MON(GARCHOMP),
        JOURNEY_LATE_RIVAL_MON(REGIGIGAS),
    },
},

[DIFFICULTY_NORMAL][TRAINER_JOURNEY_LUFFY_4] =
{
    .trainerName = _("LUFFY"),
    .trainerClass = TRAINER_CLASS_RIVAL,
    .trainerPic = TRAINER_PIC_JOURNEY_LUFFY,
    .gender = TRAINER_GENDER_MALE,
    .encounterMusic = TRAINER_ENCOUNTER_MUSIC_MALE,
    .aiFlags = AI_FLAG_BASIC_TRAINER,
    .partySize = 6,
    .party = (const struct TrainerMon[]) {
        JOURNEY_LATE_RIVAL_MON(POLIWRATH),
        JOURNEY_LATE_RIVAL_MON(SOLROCK),
        JOURNEY_LATE_RIVAL_MON(LUDICOLO),
        JOURNEY_LATE_RIVAL_MON(TOGEKISS),
        JOURNEY_LATE_RIVAL_MON(SNORLAX),
        JOURNEY_LATE_RIVAL_MON(EMPOLEON),
    },
},

#undef JOURNEY_LATE_RIVAL_MON
