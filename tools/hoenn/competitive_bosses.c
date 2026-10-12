#include "global.h"
#include "pokemon.h"
#include "move.h"
#include "data.h"
#include "item.h"
#include "constants/hold_effects.h"
#include "event_data.h"
#include "battle_setup.h"
#include "journey_gym_scaling.h"
#include "journey_competitive.h"
#include "constants/maps.h"
#include "constants/trainers.h"
#include "constants/opponents.h"
#include "constants/species.h"
#include "constants/moves.h"
#include "constants/abilities.h"
#include "constants/items.h"
#include "constants/pokemon.h"
#include "constants/battle_ai.h"
struct JourneyGym { u16 map; bool8 kanto; };
#include "journey_gym_maps.h"
struct JourneyBossProfile { u16 species; u16 moves[4][6]; u16 item,ability; u8 nature,physical; u8 evs[6]; };
#include "data/journey_competitive_profiles.h"
static EWRAM_DATA bool8 sBossLegalMoves[MOVES_COUNT];
static const u8 sPhysicalFast[6]={6,252,0,0,0,252};
static const u8 sSpecialFast[6]={6,0,0,252,0,252};
static const u8 sPhysicalBulky[6]={252,252,6,0,0,0};
static const u8 sSpecialBulky[6]={252,0,0,252,6,0};
static const u8 sWall[6]={252,0,252,0,6,0};
bool32 JourneyCompetitiveTrainer(const struct Trainer *trainer)
{
    return trainer->trainerClass==TRAINER_CLASS_LEADER || trainer->trainerClass==TRAINER_CLASS_LEADER_FRLG
       || trainer->trainerClass==TRAINER_CLASS_ELITE_FOUR || trainer->trainerClass==TRAINER_CLASS_ELITE_FOUR_FRLG
       || trainer->trainerClass==TRAINER_CLASS_CHAMPION || trainer->trainerClass==TRAINER_CLASS_CHAMPION_FRLG
       || trainer->trainerClass==TRAINER_CLASS_RIVAL || trainer->trainerClass==TRAINER_CLASS_RIVAL_EARLY_FRLG
       || trainer->trainerClass==TRAINER_CLASS_RIVAL_LATE_FRLG || trainer->trainerClass==TRAINER_CLASS_BOSS_FRLG
       || trainer->trainerClass==TRAINER_CLASS_AQUA_ADMIN || trainer->trainerClass==TRAINER_CLASS_AQUA_LEADER
       || trainer->trainerClass==TRAINER_CLASS_MAGMA_ADMIN || trainer->trainerClass==TRAINER_CLASS_MAGMA_LEADER
       || trainer == GetTrainerStructFromId(TRAINER_JOURNEY_TEAM_1505);

}
u64 JourneyCompetitiveAiFlags(u16 trainerId)
{
    if(!JourneyCompetitiveTrainer(GetTrainerStructFromId(trainerId)))return 0;
    return AI_FLAG_BASIC_TRAINER | AI_FLAG_TRY_TO_2HKO | AI_FLAG_HP_AWARE | AI_FLAG_SMART_SWITCHING
        | AI_FLAG_SMART_MON_CHOICES | AI_FLAG_OMNISCIENT | AI_FLAG_CONSERVATIVE
        | AI_FLAG_PREDICTION | AI_FLAG_PP_STALL_PREVENTION | AI_FLAG_KNOW_OPPONENT_PARTY;
}
bool32 JourneyBossMoveLegal(u16 species,u16 move,u32 level)
{
    u32 i;
    const struct LevelUpMove *levels=GetSpeciesLevelUpLearnset(species);
    const u16 *eggs=GetSpeciesEggMoves(species);
    if(move==MOVE_NONE || move==MOVE_UNAVAILABLE)return FALSE;
    if(CanLearnTeachableMove(species,move))return TRUE;
    for(i=0;eggs[i]!=MOVE_UNAVAILABLE;i++)if(eggs[i]==move)return TRUE;
    for(i=0;levels[i].move!=LEVEL_UP_MOVE_END;i++)if(levels[i].move==move && levels[i].level<=level)return TRUE;
    return FALSE;
}
static bool32 HasMove(const struct TrainerMon *mon,u16 move)
{
    u32 i;
    for(i=0;i<MAX_MON_MOVES;i++)if(mon->moves[i]==move)return TRUE;
    return FALSE;
}
static u16 FallbackMove(const struct TrainerMon *mon,u32 level,bool32 physical,u32 slot)
{
    u32 move,best=0;u16 chosen=MOVE_NONE;
    const struct SpeciesInfo *s=&gSpeciesInfo[mon->species];
    for(move=1;move<MOVES_COUNT;move++)
    {
        u32 score;
        if(HasMove(mon,move) || !sBossLegalMoves[move])continue;
        if(gMovesInfo[move].category==DAMAGE_CATEGORY_STATUS)
        {
            if(slot!=3)continue;
            switch(move)
            {
            case MOVE_RECOVER:case MOVE_ROOST:case MOVE_SOFT_BOILED:case MOVE_SLACK_OFF:case MOVE_MOONLIGHT:score=135;break;
            case MOVE_SWORDS_DANCE:case MOVE_NASTY_PLOT:case MOVE_DRAGON_DANCE:case MOVE_QUIVER_DANCE:case MOVE_CALM_MIND:score=125;break;
            case MOVE_STEALTH_ROCK:case MOVE_SPIKES:case MOVE_SPORE:case MOVE_THUNDER_WAVE:case MOVE_WILL_O_WISP:case MOVE_TOXIC:score=110;break;
            default:continue;
            }
        }
        else
        {
            if(gMovesInfo[move].explosion)continue;
            score=gMovesInfo[move].power;
            switch(move)
            {
            case MOVE_HYPER_BEAM:case MOVE_GIGA_IMPACT:case MOVE_BLAST_BURN:case MOVE_HYDRO_CANNON:case MOVE_FRENZY_PLANT:case MOVE_ROCK_WRECKER:case MOVE_ROAR_OF_TIME:case MOVE_METEOR_ASSAULT:score=score>90?score-90:1;break;
            case MOVE_SOLAR_BEAM:case MOVE_SOLAR_BLADE:case MOVE_FLY:case MOVE_DIG:case MOVE_DIVE:case MOVE_SKULL_BASH:score=score>45?score-45:1;break;
            }

            if(gMovesInfo[move].accuracy && gMovesInfo[move].accuracy<90)score=score*gMovesInfo[move].accuracy/100;
            if(gMovesInfo[move].category==(physical?DAMAGE_CATEGORY_PHYSICAL:DAMAGE_CATEGORY_SPECIAL))score+=45;
            if(gMovesInfo[move].type==s->types[0] || gMovesInfo[move].type==s->types[1])score+=45;
            for(u32 j=0;j<MAX_MON_MOVES;j++)
                if(mon->moves[j]!=MOVE_NONE && gMovesInfo[mon->moves[j]].category!=DAMAGE_CATEGORY_STATUS && gMovesInfo[mon->moves[j]].type==gMovesInfo[move].type)
                {score=score>50?score-50:1;break;}
            if(s->baseSpeed<60 && gMovesInfo[move].priority>0)score+=20;
        }
        if(score>best){best=score;chosen=move;}
    }
    return chosen;
}
static u16 RespectEvolutionLevel(u16 species,u32 level)
{
    u32 pass,i;
    for(pass=0;pass<3;pass++)
    {
        u16 previous=GetSpeciesPreEvolution(species);
        const struct Evolution *e;
        bool32 changed=FALSE;
        if(previous==SPECIES_NONE)break;
        e=GetSpeciesEvolutions(previous);
        for(i=0;e[i].method!=EVOLUTIONS_END;i++)
            if(e[i].targetSpecies==species && (e[i].method==EVO_LEVEL || e[i].method==EVO_LEVEL_BATTLE_ONLY) && e[i].param>level)
            {species=previous;changed=TRUE;break;}
        if(!changed)break;
    }
    return species;
}
void JourneyPrepareCompetitiveMon(struct TrainerMon *mon,u32 level)
{
    u32 i,j;
    u16 previousSpecies=mon->species,previousItem=mon->heldItem;
    if(level<mon->lvl)mon->species=RespectEvolutionLevel(mon->species,level);
    const struct JourneyBossProfile *p=NULL;
    const struct SpeciesInfo *s=&gSpeciesInfo[mon->species];
    bool32 physical=s->baseAttack>=s->baseSpAttack;
    for(i=0;i<ARRAY_COUNT(sBossProfiles);i++)if(sBossProfiles[i].species==mon->species){p=&sBossProfiles[i];break;}
    mon->iv=0x3FFFFFFF;
    mon->shouldUseDynamax=FALSE;mon->gigantamaxFactor=FALSE;
    if(p)
    {
        physical=p->physical;mon->ev=p->evs;mon->nature=p->nature;
        mon->heldItem=p->item;mon->ability=ABILITY_NONE;
        for(i=0;i<ARRAY_COUNT(s->abilities);i++)if(s->abilities[i]==p->ability)mon->ability=p->ability;
    }
    else
    {
        mon->ev=s->baseSpeed>=75?(physical?sPhysicalFast:sSpecialFast):(physical?sPhysicalBulky:sSpecialBulky);
        mon->nature=s->baseSpeed>=75?(physical?NATURE_JOLLY:NATURE_TIMID):(physical?NATURE_ADAMANT:NATURE_MODEST);
        mon->heldItem=ITEM_LEFTOVERS;
        if(mon->species==SPECIES_CHANSEY || mon->species==SPECIES_BLISSEY){mon->ev=sWall;mon->nature=NATURE_BOLD;}
        mon->ability=ABILITY_NONE;
    }
    if(mon->ability==ABILITY_NONE)
    {
        s32 best=-128;
        for(i=0;i<ARRAY_COUNT(s->abilities);i++)
            if(s->abilities[i]!=ABILITY_NONE && gAbilitiesInfo[s->abilities[i]].aiRating>best)
            {best=gAbilitiesInfo[s->abilities[i]].aiRating;mon->ability=s->abilities[i];}
    }
    if(mon->species==previousSpecies && (GetItemHoldEffect(previousItem)==HOLD_EFFECT_MEGA_STONE || GetItemHoldEffect(previousItem)==HOLD_EFFECT_PRIMAL_ORB))mon->heldItem=previousItem;
    for(i=0;i<MOVES_COUNT;i++)sBossLegalMoves[i]=FALSE;
    {
        const struct LevelUpMove *learn=GetSpeciesLevelUpLearnset(mon->species);
        const u16 *teach=GetSpeciesTeachableLearnset(mon->species),*eggs=GetSpeciesEggMoves(mon->species);
        for(i=0;learn[i].move!=LEVEL_UP_MOVE_END;i++)if(learn[i].level<=level && learn[i].move<MOVES_COUNT)sBossLegalMoves[learn[i].move]=TRUE;
        for(i=0;teach[i]!=MOVE_UNAVAILABLE;i++)if(teach[i]<MOVES_COUNT)sBossLegalMoves[teach[i]]=TRUE;
        for(i=0;eggs[i]!=MOVE_UNAVAILABLE;i++)if(eggs[i]<MOVES_COUNT)sBossLegalMoves[eggs[i]]=TRUE;
        sBossLegalMoves[MOVE_NONE]=FALSE;
    }
    for(i=0;i<MAX_MON_MOVES;i++)mon->moves[i]=MOVE_NONE;
    if(p)for(i=0;i<MAX_MON_MOVES;i++)for(j=0;j<6;j++)
        if(p->moves[i][j]<MOVES_COUNT && sBossLegalMoves[p->moves[i][j]] && !HasMove(mon,p->moves[i][j])){mon->moves[i]=p->moves[i][j];break;}
    for(i=0;i<MAX_MON_MOVES;i++)if(mon->moves[i]==MOVE_NONE)mon->moves[i]=FallbackMove(mon,level,physical,i);
}
