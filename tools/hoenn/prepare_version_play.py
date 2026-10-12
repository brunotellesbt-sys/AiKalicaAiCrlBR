"""Enforce the selected generation in trainers, evolution, wild pools and Dex."""
import argparse,hashlib,json,re
from pathlib import Path
from prepare_campaign_variants import PRIOR,LAYER as PREVIOUS
from allocate_generation4 import allocate
LAYER='version-play';PRIOR=PRIOR+[PREVIOUS];ROOT=Path(__file__).resolve().parents[2]
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
 p='include/journey_version.h';stage(p,(source/p).read_text().replace('#endif','u16 JourneyTrainerSpecies(u16,u32);\n#endif'))
 p='src/journey_version.c';stage(p,(source/p).read_text().replace('#include "pokemon.h"','#include "pokemon.h"\n#include "constants/species.h"\n#include "constants/pokemon.h"')+'\n'+(ROOT/'tools/hoenn/version_trainer.c.inc').read_text())
 p='src/battle_main.c';t=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_version.h"',1)
 old='''            struct TrainerMon competitiveMon;
            if (JourneyCompetitiveTrainer(trainer))
            {
                competitiveMon = partyData[monIndex];
                JourneyPrepareCompetitiveMon(&competitiveMon, JourneyGymLevel(trainer, competitiveMon.lvl));
                partyData = &competitiveMon;
                monIndex = 0;
            }
''';assert old in t
 new='''            struct TrainerMon competitiveMon = partyData[monIndex];
            u16 validSpecies = JourneyTrainerSpecies(competitiveMon.species, JourneyGymLevel(trainer, competitiveMon.lvl));
            if (validSpecies != competitiveMon.species)
            {
                competitiveMon.species = validSpecies;
                competitiveMon.ability = ABILITY_NONE;
                for (u32 moveSlot=0;moveSlot<MAX_MON_MOVES;moveSlot++)competitiveMon.moves[moveSlot]=MOVE_NONE;
            }
            if (JourneyCompetitiveTrainer(trainer))
                JourneyPrepareCompetitiveMon(&competitiveMon, JourneyGymLevel(trainer, competitiveMon.lvl));
            partyData = &competitiveMon;
            monIndex = 0;
''';stage(p,t.replace(old,new))
 p='src/pokemon.c';t=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_version.h"',1);t=t.replace('if (SanitizeSpeciesId(evolutions[i].targetSpecies) == SPECIES_NONE)','if (SanitizeSpeciesId(evolutions[i].targetSpecies) == SPECIES_NONE || !JourneySpeciesAllowed(evolutions[i].targetSpecies))');stage(p,t)
 p='src/journey_special.c';t=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_version.h"',1);needle='void JourneySpecialStatus(void *ctx)\n{';assert needle in t;t=t.replace(needle,needle+'\n    if(!JourneySpeciesAllowed(gSpecialVar_0x8004)){gSpecialVar_Result=0;return;}');stage(p,t)
 allocation=allocate(source)
 pools='static const struct JourneyWildPool sJourneyGeneration4Pools[] = {\n'+''.join('{'+p['map']+','+str(p['area'])+','+str(len(p['roots']))+',{'+','.join(p['roots'])+'}},\n' for p in allocation['pools'])+'};\n'
 stage('include/journey_generation4_pools.h',pools)
 p='src/journey_wild.c';t=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_version.h"',1).replace('#include "journey_wild_data.h"','#include "journey_wild_data.h"\n#include "journey_generation4_pools.h"')
 needle='u32 JourneyWildSpecies(u32 original, u32 area)\n{';assert needle in t
 extra='''
    if(gJourneyBuildRules.maxNational==493)
    {
        u32 k,j,phase=JourneyWildPhase();
        for(k=0;k<ARRAY_COUNT(sJourneyGeneration4Pools);k++)
        {
            const struct JourneyWildPool *pool=&sJourneyGeneration4Pools[k];
            if(MAP_GROUP(pool->map)==gSaveBlock1Ptr->location.mapGroup && MAP_NUM(pool->map)==gSaveBlock1Ptr->location.mapNum && pool->area==area)
            {
                if(!pool->count)return SPECIES_NONE;
                const struct JourneyWildStages *family=&sJourneyWildStages[pool->species[Random()%pool->count]];
                u32 stage=phase==0?0:phase==1?Random()%2:1+Random()%2;
                for(u32 attempt=0;attempt<3;attempt++)
                {
                    u16 eligible[8];u32 count=0;
                    for(j=0;j<family->count[stage];j++)
                    {
                        u16 mon=family->stages[stage][j];
                        if(JourneySpeciesAllowed(mon) && (area==0 || area==2 || gSpeciesInfo[mon].types[0]==TYPE_WATER || gSpeciesInfo[mon].types[1]==TYPE_WATER))eligible[count++]=mon;
                    }
                    if(count)return eligible[Random()%count];
                    stage=stage?stage-1:0;
                }
                return SPECIES_NONE;
            }
        }
        return JourneySpeciesAllowed(original)?original:SPECIES_NONE;
    }
''';t=t.replace(needle,needle+extra)
 t+='''
bool32 JourneyWildPoolAvailable(u32 area)
{
    if(gJourneyBuildRules.maxNational!=493)return TRUE;
    for(u32 i=0;i<ARRAY_COUNT(sJourneyGeneration4Pools);i++)
    {
        const struct JourneyWildPool *p=&sJourneyGeneration4Pools[i];
        if(MAP_GROUP(p->map)==gSaveBlock1Ptr->location.mapGroup && MAP_NUM(p->map)==gSaveBlock1Ptr->location.mapNum && p->area==area)return p->count>0;
    }
    return FALSE;
}
''';stage(p,t)
 p='include/journey_wild.h';stage(p,(source/p).read_text().replace('#endif','bool32 JourneyWildPoolAvailable(u32);\n#endif'))
 p='src/wild_encounter.c';t=(source/p).read_text();needle='static bool8 TryGenerateWildMon(const struct WildPokemonInfo *wildMonInfo, enum WildPokemonArea area, u8 flags)\n{';assert needle in t;t=t.replace(needle,needle+'\n    if(!JourneyWildPoolAvailable(area))return FALSE;');t=t.replace('bool8 DoesCurrentMapHaveFishingMons(void)\n{','bool8 DoesCurrentMapHaveFishingMons(void)\n{\n    if(!JourneyWildPoolAvailable(WILD_AREA_FISHING))return FALSE;');stage(p,t)
 habitats='static const struct JourneyHabitat sJourneyGeneration4Habitats[] = {\n'+''.join('{'+h['map']+','+str(len(h['species']))+',{'+','.join(h['species'])+'}},\n' for h in allocation['habitats'])+'};\n';stage('include/journey_generation4_habitats.h',habitats)
 p='src/journey_habitats.c';t=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_version.h"',1).replace('#include "journey_habitat_data.h"','#include "journey_habitat_data.h"\n#include "journey_generation4_habitats.h"');needle='    u32 i, j;';t=t.replace(needle,needle+'''\n    if(gJourneyBuildRules.maxNational==493)
    {
        for(i=0;i<ARRAY_COUNT(sJourneyGeneration4Habitats);i++)
            if(group==MAP_GROUP(sJourneyGeneration4Habitats[i].map) && map==MAP_NUM(sJourneyGeneration4Habitats[i].map))
                for(j=0;j<sJourneyGeneration4Habitats[i].count;j++)if(species==sJourneyGeneration4Habitats[i].species[j])return TRUE;
        return FALSE;
    }
''');stage(p,t)
 r=dict(layer=LAYER,generation4=allocation,original_sha256=originals,prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()})
 for p,raw in outputs.items():(source/p).write_bytes(raw)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.source),indent=2))
