"""Keep Galactic people in one story phase and make the bulkhead guard fight."""
import argparse,hashlib,json,re
from pathlib import Path
from prepare_trainer_item_evolutions import PRIOR,LAYER as PREVIOUS
LAYER='galactic-continuity';PRIOR=PRIOR+[PREVIOUS]
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
  h=hashlib.sha256((source/p).read_bytes()).hexdigest();assert h==expected[p],p;originals[p]=h;outputs[p]=text.encode()
 chapter=json.loads((source/'.journey-galactic-chapter').read_text());grunts=chapter['grunts']+[dict(key='GALACTIC_BULKHEAD_GUARD',map='AbandonedShip_HiddenFloorRooms',x=37,y=3,female=False,id=1588)]
 p='include/constants/opponents.h';t=(source/p).read_text();assert re.search(r'#define TRAINERS_COUNT\s+1588\b',t);t=re.sub(r'(#define TRAINERS_COUNT\s+)1588\b',r'\g<1>1589',t);stage(p,t+'\n#define TRAINER_JOURNEY_GALACTIC_BULKHEAD_GUARD 1588\n')
 p='src/data/journey_crossover_trainers.h';stage(p,(source/p).read_text()+'\n[DIFFICULTY_NORMAL][TRAINER_JOURNEY_GALACTIC_BULKHEAD_GUARD]={.trainerName=_("GALACTIC"),.trainerClass=TRAINER_CLASS_PKMN_TRAINER_1,.trainerPic=TRAINER_PIC_JOURNEY_GALACTIC_GRUNT_M,.gender=TRAINER_GENDER_MALE,.encounterMusic=TRAINER_ENCOUNTER_MUSIC_MALE,.aiFlags=AI_FLAG_BASIC_TRAINER,.partySize=3,.party=(const struct TrainerMon[]){{.species=SPECIES_BRONZOR,.lvl=40,.gender=TRAINER_MON_RANDOM_GENDER,.iv=TRAINER_PARTY_IVS(15,15,15,15,15,15),.ball=POKEBALL_COUNT,.nature=NATURE_HARDY},{.species=SPECIES_CROAGUNK,.lvl=40,.gender=TRAINER_MON_RANDOM_GENDER,.iv=TRAINER_PARTY_IVS(15,15,15,15,15,15),.ball=POKEBALL_COUNT,.nature=NATURE_HARDY},{.species=SPECIES_STUNKY,.lvl=40,.gender=TRAINER_MON_RANDOM_GENDER,.iv=TRAINER_PARTY_IVS(15,15,15,15,15,15),.ball=POKEBALL_COUNT,.nature=NATURE_HARDY}}},\n')
 p='include/journey_galactic.h';t=(source/p).read_text().replace('#endif','bool32 JourneyGalacticObjectVisible(const struct ObjectEventTemplate *,u8,u8);\nvoid JourneyGalacticBringEren(void);\nvoid JourneyGalacticBringLuffy(void);\nvoid JourneyGalacticSyncHeroes(void);\n#endif');stage(p,t)
 p='src/journey_galactic.c';t=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "event_object_movement.h"\n#include "constants/event_objects.h"\n#include "constants/event_object_movement.h"',1);needle=' static const u16 ids[]={';start=t.index(needle)+len(needle);t=t[:start]+'TRAINER_JOURNEY_GALACTIC_BULKHEAD_GUARD,'+t[start:]
 t+='\nextern const u8 JourneyGalactic_Observer[], JourneyGalactic_Cyrus[], JourneyGalactic_Gate[];\n'+''.join('extern const u8 JourneyGalactic_'+g['key']+'[];\n' for g in grunts[:-1])
 t+='''
bool32 JourneyGalacticObjectVisible(const struct ObjectEventTemplate *o,u8 group,u8 num)
{
 const u8 *script=o->script;
 u16 state=VarGet(VAR_JOURNEY_GALACTIC_STATE);
 // Special objects spawned by an approach scene have no template script.
 if(script==NULL)return TRUE;
 if(group==MAP_GROUP(MAP_JOURNEYGALACTICHALL) && num==MAP_NUM(MAP_JOURNEYGALACTICHALL))
 {
  if(state>=7)return FALSE;
  if(o->localId==6 && state<1)return FALSE;
  if(o->localId==7 && state<2)return FALSE;
 }
 static const u8 *const gruntScripts[]={GRUNT_SCRIPTS};
 for(u32 i=0;i<ARRAY_COUNT(gruntScripts);i++)
  if(script==gruntScripts[i])return JourneyGymBadgeCount(TRUE)==8 && JourneyGymBadgeCount(FALSE)==8 && state<7;
 return TRUE;
}
static void PlaceHero(u16 gfx,u8 localId,s16 x,s16 y)
{
 if(GetObjectEventIdByLocalIdAndMap(localId,gSaveBlock1Ptr->location.mapNum,gSaveBlock1Ptr->location.mapGroup)==OBJECT_EVENTS_COUNT)
  SpawnSpecialObjectEventParameterized(gfx,MOVEMENT_TYPE_FACE_UP,localId,x,y,3);
 else TryMoveObjectEventToMapCoords(localId,gSaveBlock1Ptr->location.mapNum,gSaveBlock1Ptr->location.mapGroup,x,y);
}
void JourneyGalacticBringEren(void) { PlaceHero(OBJ_EVENT_GFX_JOURNEY_EREN,6,10,26); }
void JourneyGalacticBringLuffy(void) { PlaceHero(OBJ_EVENT_GFX_JOURNEY_LUFFY,7,20,26); }
void JourneyGalacticSyncHeroes(void)
{
 u16 state=VarGet(VAR_JOURNEY_GALACTIC_STATE);
 if(state>=1 && state<7)PlaceHero(OBJ_EVENT_GFX_JOURNEY_EREN,6,13,8);
 if(state>=2 && state<7)PlaceHero(OBJ_EVENT_GFX_JOURNEY_LUFFY,7,17,8);
}
'''.replace('GRUNT_SCRIPTS',','.join('JourneyGalactic_'+g['key'] for g in grunts[:-1]));stage(p,t)
 p='src/event_object_movement.c';t=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_galactic.h"',1);needle='    if(!JourneyStoryObjectVisible(objectEventTemplate->script))return OBJECT_EVENTS_COUNT;';assert needle in t;t=t.replace(needle,needle+'\n    if(!JourneyGalacticObjectVisible(objectEventTemplate,mapGroup,mapNum))return OBJECT_EVENTS_COUNT;');stage(p,t)
 p='data/scripts/journey_galactic.inc';t=(source/p).read_text();needle='\tmsgbox JourneyGalactic_Text_Entry, MSGBOX_YESNO';assert t.count(needle)==1;t=t.replace(needle,'\ttrainerbattle_single TRAINER_JOURNEY_GALACTIC_BULKHEAD_GUARD, JourneyGalactic_Text_GruntIntro, JourneyGalactic_Text_GruntDefeat, JourneyGalactic_GateDefeated\nJourneyGalactic_GateDefeated::\n'+needle)
 # Heroes arrive from their own routes only when their tag battle starts.
 t=t.replace('\tapplymovement 6, JourneyGalactic_ErenApproach','\tspecial JourneyGalacticBringEren\n\tapplymovement 6, JourneyGalactic_ErenApproach').replace('\tapplymovement 7, JourneyGalactic_LuffyApproach','\tspecial JourneyGalacticBringLuffy\n\tapplymovement 7, JourneyGalactic_LuffyApproach')
 t=t.replace('\tsetvar VAR_JOURNEY_GALACTIC_STATE, 1','\tsetvar VAR_JOURNEY_GALACTIC_STATE, 1\n\tspecial JourneyGalacticSyncHeroes').replace('\tsetvar VAR_JOURNEY_GALACTIC_STATE, 2','\tsetvar VAR_JOURNEY_GALACTIC_STATE, 2\n\tspecial JourneyGalacticSyncHeroes').replace('JourneyGalactic_Rewards::','JourneyGalactic_Rewards::\n\tspecial JourneyGalacticSyncHeroes')
 stage(p,t)
 p='data/specials.inc';stage(p,(source/p).read_text()+'\n\tdef_special JourneyGalacticBringEren\n\tdef_special JourneyGalacticBringLuffy\n\tdef_special JourneyGalacticSyncHeroes\n')
 r=dict(layer=LAYER,grunts=grunts,no_ship_grunts_before_sixteen_badges=True,heroes_arrive_only_for_their_tag_battle=True,characters_leave_after_chapter=True,bulkhead_guard_is_battleable=True,original_sha256=originals,prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()})
 for p,raw in outputs.items():(source/p).write_bytes(raw)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(json.dumps(prepare(p.parse_args().source),indent=2))
