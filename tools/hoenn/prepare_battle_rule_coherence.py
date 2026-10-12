"""Apply NPC item thresholds to held items/alternatives and isolate custom ability."""
import argparse,hashlib,json
from pathlib import Path
from prepare_sharp_world_map import PRIOR,LAYER as PREVIOUS
LAYER='battle-rule-coherence';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
 source=Path(source);marker=source/('.journey-'+LAYER)
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in r['prepared_sha256'].items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  return r
 expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
 for layer in PRIOR:expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 outputs={};originals={}
 def stage(p,text):
  old=(source/p).read_bytes();h=hashlib.sha256(old).hexdigest();assert h==expected[p],p;originals[p]=h;outputs[p]=text.encode()
 p='src/journey_version.c';t=(source/p).read_text();needle='        u32 required=101;';assert t.count(needle)==1;t=t.replace(needle,needle+'\n        bool32 itemEvolution=FALSE;')
 start=t.index('                if(e[i].method==EVO_ITEM)');end=t.index('                if(threshold<required)',start)
 t=t[:start]+'''                if(e[i].method==EVO_ITEM)itemEvolution=TRUE;
                if(e[i].params!=NULL)
                    for(u32 condition=0;e[i].params[condition].condition!=CONDITIONS_END;condition++)
                        if(e[i].params[condition].condition==IF_HOLD_ITEM)itemEvolution=TRUE;
'''+t[end:]
 needle='        if(required>level && required<=100)eligible=previous;';assert needle in t;t=t.replace(needle,'''        if(itemEvolution)
        {
            const struct SpeciesInfo *form=&gSpeciesInfo[child];
            u32 total=form->baseHP+form->baseAttack+form->baseDefense+form->baseSpeed+form->baseSpAttack+form->baseSpDefense;
            required=max(required,total>=530?40:total>=500?35:30);
        }
'''+needle);stage(p,t)
 p='src/pokemon.c';t=(source/p).read_text();needle='if (species == SPECIES_REGIGIGAS && TRAINER_BATTLE_PARAM.opponentA == TRAINER_JOURNEY_EREN_6';assert needle in t;t=t.replace(needle,'if ((gBattleTypeFlags & BATTLE_TYPE_TRAINER) && species == SPECIES_REGIGIGAS && TRAINER_BATTLE_PARAM.opponentA == TRAINER_JOURNEY_EREN_6');stage(p,t)
 p='src/journey_competitive.c';t=(source/p).read_text();needle='    if(mon->species==previousSpecies && (GetItemHoldEffect(previousItem)==HOLD_EFFECT_MEGA_STONE || GetItemHoldEffect(previousItem)==HOLD_EFFECT_PRIMAL_ORB))mon->heldItem=previousItem;';assert needle in t;t=t.replace(needle,'''    if(mon->species==previousSpecies && (GetItemHoldEffect(previousItem)==HOLD_EFFECT_MEGA_STONE || GetItemHoldEffect(previousItem)==HOLD_EFFECT_PRIMAL_ORB))
    {
        const struct FormChange *forms=GetSpeciesFormChanges(mon->species);
        if(forms!=NULL)for(i=0;forms[i].method!=FORM_CHANGE_TERMINATOR;i++)
            if((forms[i].method==FORM_CHANGE_BATTLE_MEGA_EVOLUTION_ITEM || forms[i].method==FORM_CHANGE_BATTLE_PRIMAL_REVERSION) && forms[i].param1==previousItem)
            {mon->heldItem=previousItem;break;}
    }
''');t=t.replace('#include "global.h"','#include "global.h"\n#include "constants/form_change_types.h"',1)
 needle='    for(i=0;i<MAX_MON_MOVES;i++)if(mon->moves[i]==MOVE_NONE)mon->moves[i]=FallbackMove(mon,level,physical,i);';assert needle in t;t=t.replace(needle,needle+'\n    if(HasMove(mon,MOVE_RETURN))mon->friendship=255;\n    else if(HasMove(mon,MOVE_FRUSTRATION))mon->friendship=0;');stage(p,t)
 p='src/data/journey_crossover_trainers.h';t=(source/p).read_text()
 for name in ['MARS','JUPITER']:
  a=t.index('[DIFFICULTY_NORMAL][TRAINER_JOURNEY_'+name+']');b=t.index('.party=',a);t=t[:a]+t[a:b].replace('.gender=TRAINER_GENDER_MALE','.gender=TRAINER_GENDER_FEMALE')+t[b:]
 stage(p,t)
 r=dict(layer=LAYER,npc_stone_and_held_item_evolutions_require_30_to_40=True,alternate_methods_do_not_bypass_npc_item_policy=True,custom_mold_breaker_only_in_eren_trainer_battle=True,held_mega_stones_must_match_current_species=True,return_and_frustration_friendship_correct=True,player_stone_methods_unchanged=True,original_sha256=originals,prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()})
 for p,raw in outputs.items():(source/p).write_bytes(raw)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(json.dumps(prepare(p.parse_args().source),indent=2))
