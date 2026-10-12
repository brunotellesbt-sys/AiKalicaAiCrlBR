"""Enable the strongest implemented prediction/switching AI and legal boss builds."""
import argparse,hashlib,json
from pathlib import Path
from prepare_world_dex_map import PRIOR,LAYER as PREVIOUS
LAYER='competitive-bosses';PRIOR=PRIOR+[PREVIOUS];ROOT=Path(__file__).resolve().parents[2]
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
 reference=ROOT/'tools/hoenn/data/competitive-profiles.json';data=json.loads(reference.read_text());profiles=data['profiles'];lines=[]
 for sid,p in sorted(profiles.items(),key=lambda v:int(v[0])):
  groups=['{'+','.join(g+['MOVE_NONE']*(6-len(g)))+'}' for g in p['moves']]
  lines.append('{'+p['species']+',{'+','.join(groups)+'},'+p['item']+','+p['ability']+','+p['nature']+','+str(int(p['role']=='physical'))+',{'+','.join(map(str,p['evs']))+'}}')
 stage('src/data/journey_competitive_profiles.h','static const struct JourneyBossProfile sBossProfiles[] = {\n'+',\n'.join(lines)+'\n};\n')
 stage('src/journey_competitive.c',(ROOT/'tools/hoenn/competitive_bosses.c').read_text())
 stage('include/journey_competitive.h','#ifndef GUARD_JOURNEY_COMPETITIVE_H\n#define GUARD_JOURNEY_COMPETITIVE_H\nstruct Trainer;\nstruct TrainerMon;\nbool32 JourneyCompetitiveTrainer(const struct Trainer *);\nu64 JourneyCompetitiveAiFlags(u16);\nbool32 JourneyBossMoveLegal(u16,u16,u32);\nvoid JourneyPrepareCompetitiveMon(struct TrainerMon *,u32);\n#endif\n')
 p='src/battle_main.c';text=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_competitive.h"',1)
 needle='            const struct TrainerMon *partyData = trainer->party;\n';assert text.count(needle)==1
 text=text.replace(needle,needle+'''            struct TrainerMon competitiveMon;
            if (JourneyCompetitiveTrainer(trainer))
            {
                competitiveMon = partyData[monIndex];
                JourneyPrepareCompetitiveMon(&competitiveMon, JourneyGymLevel(trainer, competitiveMon.lvl));
                partyData = &competitiveMon;
                monIndex = 0;
            }
''',1);stage(p,text)
 p='src/battle_ai_main.c';text=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_competitive.h"',1)
 needle='            flags = GetTrainerAIFlagsFromId(trainerId);';assert text.count(needle)==1
 text=text.replace(needle,'''        {
            u64 competitive = JourneyCompetitiveAiFlags(trainerId);
            flags = competitive ? competitive : GetTrainerAIFlagsFromId(trainerId);
        }''',1);stage(p,text)
 r=dict(layer=LAYER,profiles=len(profiles),reference_commit=data['reference_commit'],reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),ivs=31,ev_budget=510,levels_counts_and_battle_formats_preserved=True,tm_tutor_egg_moves_allowed_at_low_levels=True,level_up_moves_level_limited=True,forbidden_mechanics_not_added=['Z-Moves','Dynamax','Gigantamax','Terastallization'],original_sha256=originals,prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()})
 for p,raw in outputs.items():(source/p).write_bytes(raw)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.source),indent=2))
