"""Choose the region before the professor speaks; use Oak for Kanto/Sevii."""
import argparse,hashlib,json
from pathlib import Path
from prepare_story_continuity import PRIOR,LAYER as PREVIOUS
LAYER='intro-region';PRIOR=PRIOR+[PREVIOUS];ROOT=Path(__file__).resolve().parents[2]
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
  old=(source/p).read_bytes() if (source/p).exists() else None;h=hashlib.sha256(old).hexdigest() if old else None
  assert h==expected.get(p),p
  if h:originals[p]=h
  outputs[p]=text.encode()
 stage('include/journey_intro.h','#ifndef GUARD_JOURNEY_INTRO_H\n#define GUARD_JOURNEY_INTRO_H\nextern u8 gJourneyIntroRegion;\nvoid JourneyBirthApplyIntroRegion(void);\n#endif\n')
 stage('src/journey_intro.c','#include "global.h"\n#include "event_data.h"\n#include "journey_intro.h"\n#include "constants/vars.h"\n#include "constants/regions.h"\nEWRAM_DATA u8 gJourneyIntroRegion=0;\nvoid JourneyBirthApplyIntroRegion(void)\n{\n    u16 region=gJourneyIntroRegion<=2?gJourneyIntroRegion:0;\n    VarSet(VAR_JOURNEY_START_REGION,region);\n    gSaveBlock2Ptr->playerRegion=region==0?REGION_HOENN:REGION_KANTO;\n}\n')
 p='src/main_menu.c';t=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_intro.h"\n#include "script_menu.h"\n#include "constants/script_menu.h"',1)
 needle='static void Task_NewGameBirchSpeech_Init(u8);';assert needle in t;t=t.replace(needle,needle+'\nstatic void Task_JourneyIntroRegion(u8);')
 start=t.index('        case ACTION_NEW_GAME:');end=t.index('            gPlttBufferUnfaded[0] = RGB_BLACK;',start)
 t=t[:start]+'''        case ACTION_NEW_GAME:
        default:
'''+t[end:]
 needle='            gTasks[taskId].func = Task_NewGameBirchSpeech_Init;';assert t.count(needle)==1;t=t.replace(needle,'            gJourneyIntroRegion=0xFF;\n            gTasks[taskId].data[0]=0;\n            gTasks[taskId].func = Task_JourneyIntroRegion;')
 needle='static void Task_NewGameBirchSpeech_Init(u8 taskId)\n{';assert needle in t;t=t.replace(needle,(ROOT/'tools/hoenn/intro_region_menu.c.inc').read_text()+'\n'+needle)
 t=t.replace('birchSpriteId = AddNewGameBirchObject(0x88, 0x3C, 1);','birchSpriteId = gJourneyIntroRegion==0 ? AddNewGameBirchObject(0x88, 0x3C, 1) : CreateTrainerSprite(TRAINER_PIC_PROFESSOR_OAK_FRLG,0x88,0x3C,1,NULL);')
 t=t.replace('StringExpandPlaceholders(gStringVar4, gText_Birch_Welcome);','StringExpandPlaceholders(gStringVar4, gJourneyIntroRegion==0 ? gText_Birch_Welcome : sJourneyOakWelcome);');stage(p,t)
 p='data/specials.inc';stage(p,(source/p).read_text()+'\n\tdef_special JourneyBirthApplyIntroRegion\n')
 p='include/journey_birth.h';stage(p,(source/p).read_text().replace('#endif','void JourneyBirthApplyIntroRegion(void);\n#endif'))
 p='data/scripts/journey_birth.inc';t=(source/p).read_text();needle='\tmultichoice 0, 0, MULTI_JOURNEY_START_REGIONS, TRUE\n\tspecial JourneyBirthSelectRegion';assert needle in t;t=t.replace(needle,'\tspecial JourneyBirthApplyIntroRegion');stage(p,t)
 r=dict(layer=LAYER,region_chosen_before_professor=True,oak_for_kanto_and_sevii=True,birch_for_hoenn=True,original_sha256=originals,prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()})
 for p,raw in outputs.items():(source/p).write_bytes(raw)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.source),indent=2))
