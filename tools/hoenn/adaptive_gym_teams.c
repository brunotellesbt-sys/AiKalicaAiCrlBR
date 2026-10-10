#include "global.h"
#include "pokemon.h"
#include "move.h"
#include "data.h"
#include "battle_setup.h"
#include "journey_gym_scaling.h"
#include "event_data.h"
#include "constants/maps.h"
#include "constants/trainers.h"
#include "constants/species.h"
#include "constants/moves.h"
#include "constants/abilities.h"
#include "constants/items.h"
struct JourneyGym { u16 map; bool8 kanto; };
#include "journey_gym_maps.h"
static void LeaderMoves(struct TrainerMon *mon, u32 level)
{
    const struct LevelUpMove *learnset = GetSpeciesLevelUpLearnset(mon->species);
    const struct SpeciesInfo *species = &gSpeciesInfo[mon->species];
    u32 limit = level < 20 ? 60 : level < 30 ? 80 : level < 42 ? 100 : 140;
    u32 i, slot;
    for (slot = 0; slot < MAX_MON_MOVES; slot++) mon->moves[slot] = MOVE_NONE;
    for (slot = 0; slot < 3; slot++)
    {
        u32 best = 0;
        for (i = 0; learnset[i].move != LEVEL_UP_MOVE_END; i++)
        {
            u32 move = learnset[i].move, j, score;
            bool32 duplicate = FALSE, sameType = FALSE;
            if (learnset[i].level > level || gMovesInfo[move].power < 2
                || gMovesInfo[move].power > limit || gMovesInfo[move].explosion) continue;
            for (j = 0; j < slot; j++)
            {
                if (mon->moves[j] == move) duplicate = TRUE;
                if (gMovesInfo[mon->moves[j]].type == gMovesInfo[move].type) sameType = TRUE;
            }
            if (duplicate) continue;
            score = gMovesInfo[move].power + ((gMovesInfo[move].type == species->types[0]
                || gMovesInfo[move].type == species->types[1]) ? 30 : 0);
            if (sameType) score = score > 40 ? score - 40 : 1;
            if (score > best) { best = score; mon->moves[slot] = move; }
        }
        if (mon->moves[slot] == MOVE_NONE) break;
    }
    // Keep one support move, learned at or before this level.
    for (i = 0; learnset[i].move != LEVEL_UP_MOVE_END; i++)
        if (learnset[i].level <= level && gMovesInfo[learnset[i].move].category == DAMAGE_CATEGORY_STATUS
            && learnset[i].move != MOVE_TELEPORT) mon->moves[3] = learnset[i].move;
    if (mon->moves[0] == MOVE_NONE)
        mon->moves[0] = mon->species == SPECIES_ABRA ? MOVE_HIDDEN_POWER : MOVE_TACKLE;
}
static u16 LeaderSpecies(const struct Trainer *trainer, u32 slot, u32 level)
{
    if (trainer->party == GetTrainerStructFromId(TRAINER_LEADER_BROCK)->party)
    {
        switch (slot)
        {
        case 0: return SPECIES_ONIX;
        case 1: return (level >= 40 ? SPECIES_GOLEM : (level >= 25 ? SPECIES_GRAVELER : SPECIES_GEODUDE));
        case 2: return (level >= 40 ? SPECIES_OMASTAR : SPECIES_OMANYTE);
        case 3: return (level >= 40 ? SPECIES_KABUTOPS : SPECIES_KABUTO);
        case 4: return (level >= 42 ? SPECIES_RHYDON : SPECIES_RHYHORN);
        case 5: return SPECIES_AERODACTYL;
        }
    }
    if (trainer->party == GetTrainerStructFromId(TRAINER_LEADER_MISTY)->party)
    {
        switch (slot)
        {
        case 0: return (level >= 21 ? SPECIES_STARMIE : SPECIES_STARYU);
        case 1: return (level >= 33 ? SPECIES_GOLDUCK : SPECIES_PSYDUCK);
        case 2: return (level >= 32 ? SPECIES_SEADRA : SPECIES_HORSEA);
        case 3: return (level >= 42 ? SPECIES_POLIWRATH : (level >= 25 ? SPECIES_POLIWHIRL : SPECIES_POLIWAG));
        case 4: return (level >= 33 ? SPECIES_SEAKING : SPECIES_GOLDEEN);
        case 5: return (level >= 35 ? SPECIES_CLOYSTER : SPECIES_SHELLDER);
        }
    }
    if (trainer->party == GetTrainerStructFromId(TRAINER_LEADER_LT_SURGE)->party)
    {
        switch (slot)
        {
        case 0: return (level >= 21 ? SPECIES_RAICHU : SPECIES_PIKACHU);
        case 1: return (level >= 30 ? SPECIES_ELECTRODE : SPECIES_VOLTORB);
        case 2: return (level >= 30 ? SPECIES_MAGNETON : SPECIES_MAGNEMITE);
        case 3: return SPECIES_ELECTABUZZ;
        case 4: return (level >= 27 ? SPECIES_LANTURN : SPECIES_CHINCHOU);
        case 5: return (level >= 30 ? SPECIES_AMPHAROS : (level >= 15 ? SPECIES_FLAAFFY : SPECIES_MAREEP));
        }
    }
    if (trainer->party == GetTrainerStructFromId(TRAINER_LEADER_ERIKA)->party)
    {
        switch (slot)
        {
        case 0: return (level >= 35 ? SPECIES_VILEPLUME : (level >= 21 ? SPECIES_GLOOM : SPECIES_ODDISH));
        case 1: return SPECIES_TANGELA;
        case 2: return (level >= 35 ? SPECIES_VICTREEBEL : (level >= 21 ? SPECIES_WEEPINBELL : SPECIES_BELLSPROUT));
        case 3: return (level >= 27 ? SPECIES_JUMPLUFF : (level >= 18 ? SPECIES_SKIPLOOM : SPECIES_HOPPIP));
        case 4: return (level >= 35 ? SPECIES_EXEGGUTOR : SPECIES_EXEGGCUTE);
        case 5: return SPECIES_ROSELIA;
        }
    }
    if (trainer->party == GetTrainerStructFromId(TRAINER_LEADER_KOGA)->party)
    {
        switch (slot)
        {
        case 0: return (level >= 35 ? SPECIES_WEEZING : SPECIES_KOFFING);
        case 1: return (level >= 38 ? SPECIES_MUK : SPECIES_GRIMER);
        case 2: return (level >= 31 ? SPECIES_VENOMOTH : SPECIES_VENONAT);
        case 3: return (level >= 42 ? SPECIES_CROBAT : (level >= 22 ? SPECIES_GOLBAT : SPECIES_ZUBAT));
        case 4: return (level >= 22 ? SPECIES_ARBOK : SPECIES_EKANS);
        case 5: return (level >= 30 ? SPECIES_TENTACRUEL : SPECIES_TENTACOOL);
        }
    }
    if (trainer->party == GetTrainerStructFromId(TRAINER_LEADER_SABRINA)->party)
    {
        switch (slot)
        {
        case 0: return (level >= 35 ? SPECIES_ALAKAZAM : (level >= 16 ? SPECIES_KADABRA : SPECIES_ABRA));
        case 1: return SPECIES_MR_MIME;
        case 2: return (level >= 26 ? SPECIES_HYPNO : SPECIES_DROWZEE);
        case 3: return (level >= 37 ? SPECIES_SLOWBRO : SPECIES_SLOWPOKE);
        case 4: return (level >= 30 ? SPECIES_GARDEVOIR : (level >= 20 ? SPECIES_KIRLIA : SPECIES_RALTS));
        case 5: return (level >= 35 ? SPECIES_EXEGGUTOR : SPECIES_EXEGGCUTE);
        }
    }
    if (trainer->party == GetTrainerStructFromId(TRAINER_LEADER_BLAINE)->party)
    {
        switch (slot)
        {
        case 0: return (level >= 35 ? SPECIES_ARCANINE : SPECIES_GROWLITHE);
        case 1: return (level >= 40 ? SPECIES_RAPIDASH : SPECIES_PONYTA);
        case 2: return (level >= 35 ? SPECIES_NINETALES : SPECIES_VULPIX);
        case 3: return SPECIES_MAGMAR;
        case 4: return (level >= 38 ? SPECIES_MAGCARGO : SPECIES_SLUGMA);
        case 5: return (level >= 24 ? SPECIES_HOUNDOOM : SPECIES_HOUNDOUR);
        }
    }
    if (trainer->party == GetTrainerStructFromId(TRAINER_JOURNEY_BLUE)->party)
    {
        switch (slot)
        {
        case 0: return (level >= 36 ? SPECIES_PIDGEOT : (level >= 18 ? SPECIES_PIDGEOTTO : SPECIES_PIDGEY));
        case 1: return (level >= 35 ? SPECIES_ARCANINE : SPECIES_GROWLITHE);
        case 2: return (level >= 35 ? SPECIES_ALAKAZAM : (level >= 16 ? SPECIES_KADABRA : SPECIES_ABRA));
        case 3: return (level >= 42 ? SPECIES_RHYDON : SPECIES_RHYHORN);
        case 4: return (level >= 35 ? SPECIES_EXEGGUTOR : SPECIES_EXEGGCUTE);
        case 5: return (level >= 20 ? SPECIES_GYARADOS : SPECIES_MAGIKARP);
        }
    }
    if (trainer->party == GetTrainerStructFromId(TRAINER_ROXANNE_1)->party)
    {
        switch (slot)
        {
        case 0: return SPECIES_NOSEPASS;
        case 1: return (level >= 40 ? SPECIES_GOLEM : (level >= 25 ? SPECIES_GRAVELER : SPECIES_GEODUDE));
        case 2: return (level >= 42 ? SPECIES_AGGRON : (level >= 32 ? SPECIES_LAIRON : SPECIES_ARON));
        case 3: return (level >= 40 ? SPECIES_OMASTAR : SPECIES_OMANYTE);
        case 4: return (level >= 40 ? SPECIES_KABUTOPS : SPECIES_KABUTO);
        case 5: return SPECIES_AERODACTYL;
        }
    }
    if (trainer->party == GetTrainerStructFromId(TRAINER_BRAWLY_1)->party)
    {
        switch (slot)
        {
        case 0: return (level >= 24 ? SPECIES_HARIYAMA : SPECIES_MAKUHITA);
        case 1: return (level >= 42 ? SPECIES_MACHAMP : (level >= 28 ? SPECIES_MACHOKE : SPECIES_MACHOP));
        case 2: return (level >= 37 ? SPECIES_MEDICHAM : SPECIES_MEDITITE);
        case 3: return SPECIES_HERACROSS;
        case 4: return (level >= 28 ? SPECIES_PRIMEAPE : SPECIES_MANKEY);
        case 5: return (level >= 20 ? SPECIES_HITMONTOP : SPECIES_TYROGUE);
        }
    }
    if (trainer->party == GetTrainerStructFromId(TRAINER_WATTSON_1)->party)
    {
        switch (slot)
        {
        case 0: return (level >= 26 ? SPECIES_MANECTRIC : SPECIES_ELECTRIKE);
        case 1: return (level >= 30 ? SPECIES_MAGNETON : SPECIES_MAGNEMITE);
        case 2: return (level >= 30 ? SPECIES_ELECTRODE : SPECIES_VOLTORB);
        case 3: return (level >= 30 ? SPECIES_AMPHAROS : (level >= 15 ? SPECIES_FLAAFFY : SPECIES_MAREEP));
        case 4: return (level >= 21 ? SPECIES_RAICHU : SPECIES_PIKACHU);
        case 5: return SPECIES_ELECTABUZZ;
        }
    }
    if (trainer->party == GetTrainerStructFromId(TRAINER_FLANNERY_1)->party)
    {
        switch (slot)
        {
        case 0: return SPECIES_TORKOAL;
        case 1: return (level >= 33 ? SPECIES_CAMERUPT : SPECIES_NUMEL);
        case 2: return (level >= 38 ? SPECIES_MAGCARGO : SPECIES_SLUGMA);
        case 3: return (level >= 35 ? SPECIES_NINETALES : SPECIES_VULPIX);
        case 4: return (level >= 40 ? SPECIES_RAPIDASH : SPECIES_PONYTA);
        case 5: return (level >= 35 ? SPECIES_ARCANINE : SPECIES_GROWLITHE);
        }
    }
    if (trainer->party == GetTrainerStructFromId(TRAINER_NORMAN_1)->party)
    {
        switch (slot)
        {
        case 0: return (level >= 36 ? SPECIES_SLAKING : (level >= 18 ? SPECIES_VIGOROTH : SPECIES_SLAKOTH));
        case 1: return SPECIES_SPINDA;
        case 2: return (level >= 20 ? SPECIES_LINOONE : SPECIES_ZIGZAGOON);
        case 3: return (level >= 40 ? SPECIES_EXPLOUD : (level >= 20 ? SPECIES_LOUDRED : SPECIES_WHISMUR));
        case 4: return SPECIES_ZANGOOSE;
        case 5: return SPECIES_KANGASKHAN;
        }
    }
    if (trainer->party == GetTrainerStructFromId(TRAINER_WINONA_1)->party)
    {
        switch (slot)
        {
        case 0: return (level >= 35 ? SPECIES_ALTARIA : SPECIES_SWABLU);
        case 1: return (level >= 22 ? SPECIES_SWELLOW : SPECIES_TAILLOW);
        case 2: return (level >= 25 ? SPECIES_PELIPPER : SPECIES_WINGULL);
        case 3: return SPECIES_SKARMORY;
        case 4: return SPECIES_TROPIUS;
        case 5: return (level >= 20 ? SPECIES_NOCTOWL : SPECIES_HOOTHOOT);
        }
    }
    if (trainer->party == GetTrainerStructFromId(TRAINER_TATE_AND_LIZA_1)->party)
    {
        switch (slot)
        {
        case 0: return SPECIES_SOLROCK;
        case 1: return SPECIES_LUNATONE;
        case 2: return (level >= 36 ? SPECIES_CLAYDOL : SPECIES_BALTOY);
        case 3: return (level >= 25 ? SPECIES_XATU : SPECIES_NATU);
        case 4: return (level >= 32 ? SPECIES_GRUMPIG : SPECIES_SPOINK);
        case 5: return SPECIES_CHIMECHO;
        }
    }
    if (trainer->party == GetTrainerStructFromId(TRAINER_JUAN_1)->party)
    {
        switch (slot)
        {
        case 0: return (level >= 48 ? SPECIES_KINGDRA : (level >= 32 ? SPECIES_SEADRA : SPECIES_HORSEA));
        case 1: return SPECIES_LUVDISC;
        case 2: return (level >= 30 ? SPECIES_WHISCASH : SPECIES_BARBOACH);
        case 3: return (level >= 44 ? SPECIES_WALREIN : (level >= 32 ? SPECIES_SEALEO : SPECIES_SPHEAL));
        case 4: return (level >= 30 ? SPECIES_CRAWDAUNT : SPECIES_CORPHISH);
        case 5: return (level >= 35 ? SPECIES_MILOTIC : SPECIES_FEEBAS);
        }
    }
    return SPECIES_NONE;
}
bool32 JourneyPrepareGymLeader(const struct Trainer *original, struct Trainer *trainer, struct TrainerMon *mons)
{
    u32 gym, rank, players = 0, count, i, highest = 0;
    for (gym = 0; gym < ARRAY_COUNT(sJourneyGyms); gym++)
        if (gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(sJourneyGyms[gym].map)
            && gSaveBlock1Ptr->location.mapNum == MAP_NUM(sJourneyGyms[gym].map)) break;
    if (gym == ARRAY_COUNT(sJourneyGyms) || LeaderSpecies(original, 0, 14) == SPECIES_NONE) return FALSE;
    for (i = 0; i < PARTY_SIZE; i++)
        if (GetMonData(&gPlayerParty[i], MON_DATA_SPECIES) != SPECIES_NONE
            && !GetMonData(&gPlayerParty[i], MON_DATA_IS_EGG)) players++;
    rank = JourneyGymBadgeCount(sJourneyGyms[gym].kanto);
    count = rank >= 4 ? 6 : rank + 2 + (players > rank + 2);
    *trainer = *original;
    for (i = 0; i < original->partySize; i++)
        if (original->party[i].lvl > highest) highest = original->party[i].lvl;
    for (i = 0; i < count; i++)
    {
        // Ace family first in the priority list, last in battle order.
        u32 slot = i == count - 1 ? 0 : i + 1;
        u32 originalLevel = highest - (slot == 0 ? 0 : (slot > 3 ? 3 : slot));
        u32 level = JourneyGymLevel(original, originalLevel);
        mons[i] = original->party[original->partySize - 1];
        mons[i].species = LeaderSpecies(original, slot, level);
        mons[i].lvl = originalLevel;
        mons[i].ability = ABILITY_NONE;
        mons[i].heldItem = slot == 0 ? original->party[original->partySize - 1].heldItem : ITEM_NONE;
        mons[i].ev = NULL;
        mons[i].nickname = NULL;
        LeaderMoves(&mons[i], level);
    }
    trainer->party = mons;
    trainer->partySize = count;
    trainer->poolSize = 0;
    return TRUE;
}
