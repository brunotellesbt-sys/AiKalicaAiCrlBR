#include "global.h"
#include "pokemon.h"
#include "move.h"
#include "journey_pwt.h"
#include "constants/moves.h"
#include "constants/pokemon.h"
struct PWTSpread { u16 species,moves[4][6]; u8 evs[6],nature,priority,zeroAttack,zeroSpeed; };
#include "data/journey_pwt_spreads.h"

static bool32 OwnAttack(u16 move)
{
    if(move==MOVE_NONE)return FALSE;
    switch(move)
    {
    case MOVE_BODY_PRESS:case MOVE_FOUL_PLAY:case MOVE_COUNTER:
    case MOVE_SEISMIC_TOSS:case MOVE_ENDEAVOR:case MOVE_SUPER_FANG:
    case MOVE_FINAL_GAMBIT:case MOVE_METAL_BURST:return FALSE;
    default:return gMovesInfo[move].category==DAMAGE_CATEGORY_PHYSICAL;
    }
}
static bool32 OwnSpecialAttack(u16 move)
{
    if(move==MOVE_NONE)return FALSE;
    switch(move)
    {
    case MOVE_MIRROR_COAT:case MOVE_NIGHT_SHADE:case MOVE_DRAGON_RAGE:
    case MOVE_SONIC_BOOM:case MOVE_NATURES_MADNESS:case MOVE_RUINATION:return FALSE;
    default:return gMovesInfo[move].category==DAMAGE_CATEGORY_SPECIAL;
    }
}
static void OptimizeForTeam(struct Pokemon *mon,bool32 trickRoomTeam)
{
    static const u8 evFields[]={MON_DATA_HP_EV,MON_DATA_ATK_EV,MON_DATA_DEF_EV,MON_DATA_SPATK_EV,MON_DATA_SPDEF_EV,MON_DATA_SPEED_EV};
    static const u8 ivFields[]={MON_DATA_HP_IV,MON_DATA_ATK_IV,MON_DATA_DEF_IV,MON_DATA_SPATK_IV,MON_DATA_SPDEF_IV,MON_DATA_SPEED_IV};
    u16 species=GetMonData(mon,MON_DATA_SPECIES),moves[4];
    const struct SpeciesInfo *info=&gSpeciesInfo[species];
    const struct PWTSpread *best=NULL;
    s32 bestScore=-100000;
    u32 i,j,k,physical=0,special=0,matched=0;
    bool32 gyro=FALSE,bodyPress=FALSE;
    u8 evs[6]={0},nature,zero=0;
    for(i=0;i<4;i++)
    {
        moves[i]=GetMonData(mon,MON_DATA_MOVE1+i);
        physical+=OwnAttack(moves[i]);special+=OwnSpecialAttack(moves[i]);
        gyro|=moves[i]==MOVE_GYRO_BALL;
        bodyPress|=moves[i]==MOVE_BODY_PRESS;
    }
    // Published singles spreads are matched to actual selected moves. A
    // species' first offensive set must not replace a custom defensive set.
    for(i=0;i<ARRAY_COUNT(sPWTSpreads);i++)
    {
        const struct PWTSpread *p=&sPWTSpreads[i];
        u32 same=0;
        if(p->species!=species)continue;
        for(j=0;j<4;j++)if(moves[j])
            for(k=0;k<24;k++)if(((const u16 *)p->moves)[k]==moves[j]){same++;break;}
        s32 score=same*100+p->priority*3;
        if(physical && !special && p->evs[3]>p->evs[1])score-=150;
        if(special && !physical && p->evs[1]>p->evs[3])score-=150;
        if((trickRoomTeam && info->baseSpeed<=65 && (physical || special)) || (gyro && info->baseSpeed<=65))
            score+=p->zeroSpeed?70:p->evs[5]?-200:0;
        if(score>bestScore){bestScore=score;best=p;matched=same;}
    }
    bool32 slow=(trickRoomTeam && info->baseSpeed<=65 && (physical || special)) || (gyro && info->baseSpeed<=65);
    if(best && matched>=2)
    {
        memcpy(evs,best->evs,sizeof(evs));nature=best->nature;
        slow|=best->zeroSpeed;
    }
    else
    {
        bool32 fast=info->baseSpeed>=75 && !slow;
        if(bodyPress || (!physical && !special))
        {
            evs[0]=252;evs[2]=252;evs[4]=6;
            nature=slow?NATURE_RELAXED:NATURE_BOLD;
        }
        else if(physical && special)
        {
            // Preserve both attacking stats for genuine mixed movesets.
            bool32 favorPhysical=info->baseAttack*physical>=info->baseSpAttack*special;
            evs[favorPhysical?1:3]=252;evs[fast?5:0]=252;evs[favorPhysical?3:1]=6;
            nature=slow?(favorPhysical?NATURE_BRAVE:NATURE_QUIET):fast?NATURE_NAIVE:favorPhysical?NATURE_LONELY:NATURE_MILD;
        }
        else
        {
            evs[physical?1:3]=252;evs[fast?5:0]=252;evs[2]=6;
            nature=physical?(slow?NATURE_BRAVE:fast?NATURE_JOLLY:NATURE_ADAMANT)
                           :(slow?NATURE_QUIET:fast?NATURE_TIMID:NATURE_MODEST);
        }
    }
    // A reference may offer both physical and mixed move alternatives. Its
    // first listed nature must not weaken an attacking stat the chosen moves
    // actually use (e.g. Jolly plus Overheat on a mixed Infernape).
    if(physical && special)
    {
        switch(nature)
        {
        case NATURE_ADAMANT:case NATURE_JOLLY:case NATURE_IMPISH:case NATURE_CAREFUL:
        case NATURE_MODEST:case NATURE_TIMID:case NATURE_BOLD:case NATURE_CALM:
            nature=slow?(info->baseAttack*physical>=info->baseSpAttack*special?NATURE_BRAVE:NATURE_QUIET)
                       :evs[5]?NATURE_NAIVE:info->baseAttack*physical>=info->baseSpAttack*special?NATURE_LONELY:NATURE_MILD;
        }
    }
    else if(physical)
    {
        switch(nature)
        {
        case NATURE_BOLD:nature=NATURE_IMPISH;break;
        case NATURE_CALM:nature=NATURE_CAREFUL;break;
        case NATURE_TIMID:nature=NATURE_JOLLY;break;
        case NATURE_MODEST:nature=NATURE_ADAMANT;break;
        }
    }
    else if(special)
    {
        switch(nature)
        {
        case NATURE_IMPISH:nature=NATURE_BOLD;break;
        case NATURE_CAREFUL:nature=NATURE_CALM;break;
        case NATURE_JOLLY:nature=NATURE_TIMID;break;
        case NATURE_ADAMANT:nature=NATURE_MODEST;break;
        }
    }
    if(slow)
    {
        // Do not keep Speed EVs when intentionally minimizing Speed.
        u32 extra=evs[5];evs[5]=0;
        for(i=0;i<5 && extra;i++){u32 add=min(extra,252-evs[i]);evs[i]+=add;extra-=add;}
        switch(nature)
        {
        case NATURE_BRAVE:case NATURE_QUIET:case NATURE_RELAXED:case NATURE_SASSY:break;
        default:nature=physical?NATURE_BRAVE:special?NATURE_QUIET:evs[2]>=evs[4]?NATURE_RELAXED:NATURE_SASSY;
        }
    }
    SetMonData(mon,MON_DATA_HIDDEN_NATURE,&nature);
    bool32 reducedAttack=nature==NATURE_BOLD || nature==NATURE_MODEST
        || nature==NATURE_CALM || nature==NATURE_TIMID;
    for(i=0;i<6;i++)
    {
        u8 iv=(i==1 && reducedAttack)||(i==5 && slow)?0:31;
        SetMonData(mon,ivFields[i],&iv);SetMonData(mon,evFields[i],&evs[i]);
        // Hyper Training must not undo an intentional zero IV.
        SetMonData(mon,MON_DATA_HYPER_TRAINED_HP+i,&zero);
    }
    CalculateMonStats(mon);
}

void JourneyPWTOptimizeMon(struct Pokemon *mon)
{
    bool32 room=FALSE;
    for(u32 i=0;i<4;i++)room|=GetMonData(mon,MON_DATA_MOVE1+i)==MOVE_TRICK_ROOM;
    OptimizeForTeam(mon,room);
}
void JourneyPWTOptimizeParty(struct Pokemon *party,u32 count)
{
    bool32 room=FALSE;
    count=min(count,PARTY_SIZE);
    for(u32 i=0;i<count;i++)
        for(u32 slot=0;slot<4;slot++)
            room|=GetMonData(&party[i],MON_DATA_MOVE1+slot)==MOVE_TRICK_ROOM;
    for(u32 i=0;i<count;i++)OptimizeForTeam(&party[i],room);
}
