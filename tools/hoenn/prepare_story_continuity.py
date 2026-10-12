"""Keep recurring important characters in the appropriate native story chapter."""
import argparse,hashlib,json,re
from pathlib import Path
from prepare_arrival_continuity import PRIOR,LAYER as PREVIOUS
LAYER='story-continuity';PRIOR=PRIOR+[PREVIOUS]
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
 guards=[]
 events={'MtChimney':3,'MagmaHideout_4F':4,'MossdeepCity_SpaceCenter_2F':5,'AquaHideout_B2F':16,'Route119_WeatherInstitute_2F':14,'SeafloorCavern_Room3':6,'RocketHideout_B4F_Frlg':1,'SilphCo_11F_Frlg':2}
 for file in sorted((source/'data/maps').glob('*/map.json')):
  m=json.loads(file.read_text());name=m.get('name',file.parent.name)
  for o in m.get('object_events',[]):
   label=o.get('script','');condition=None
   if name in events and re.search('Maxie|Tabitha|Shelly|Matt$|Giovanni|Boss$',label):condition=f'JourneyPendingCampaignEvent({"TRUE" if name.endswith("Frlg") else "FALSE"})=={events[name]}'
   if label=='Route120_EventScript_Steven':condition='FlagGet(FLAG_DELIVERED_STEVEN_LETTER)'
   if label=='MossdeepCity_StevensHouse_EventScript_Steven':condition='FlagGet(FLAG_DELIVERED_STEVEN_LETTER) && FlagGet(FLAG_RECEIVED_DEVON_SCOPE) && FlagGet(FLAG_RECEIVED_HM_DIVE)'
   if label=='SootopolisCity_EventScript_Steven':condition='FlagGet(FLAG_DELIVERED_STEVEN_LETTER) && FlagGet(FLAG_RECEIVED_DEVON_SCOPE) && VarGet(VAR_MOSSDEEP_SPACE_CENTER_STATE)==3'
   if label in ['SootopolisCity_EventScript_Maxie','SootopolisCity_EventScript_Archie']:condition='FlagGet(FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN)'
   if condition:guards.append(dict(map=name,script=label,condition=condition))
 body='#include "global.h"\n#include "event_data.h"\n#include "journey_campaign_gates.h"\n#include "constants/flags.h"\n#include "constants/vars.h"\n#include "journey_story_continuity.h"\n'+''.join('extern const u8 '+g['script']+'[];\n' for g in guards)+'bool32 JourneyStoryObjectVisible(const u8 *script)\n{\n'+''.join('    if(script=='+g['script']+')return '+g['condition']+';\n' for g in guards)+'    return TRUE;\n}\n'
 stage('src/journey_story_continuity.c',body);stage('include/journey_story_continuity.h','#ifndef GUARD_JOURNEY_STORY_CONTINUITY_H\n#define GUARD_JOURNEY_STORY_CONTINUITY_H\nbool32 JourneyStoryObjectVisible(const u8 *);\nu32 JourneyPendingCampaignEvent(bool32);\n#endif\n')
 p='src/event_object_movement.c';t=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_story_continuity.h"',1);needle='    graphicsInfo = GetObjectEventGraphicsInfo(graphicsId);\n    CopyObjectGraphicsInfoToSpriteTemplate_WithMovementType';assert t.count(needle)==1;t=t.replace(needle,'    if(!JourneyStoryObjectVisible(objectEventTemplate->script))return OBJECT_EVENTS_COUNT;\n'+needle);stage(p,t)
 r=dict(layer=LAYER,guards=guards,original_hide_flags_preserved=True,routes_remain_open=True,gym_checkpoint_order_reused=True,original_sha256=originals,prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()})
 for p,raw in outputs.items():(source/p).write_bytes(raw)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.source),indent=2))
