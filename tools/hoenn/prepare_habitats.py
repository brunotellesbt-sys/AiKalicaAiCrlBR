"""Install the complete ordinary catalog in distinct habitats and enable National Dex."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from prepare_family import LAYERS_BEFORE, HERE
from prepare_crossing import PIN
from plan_habitats import plan


def prepare(source):
 source=Path(source);marker=source/'.journey-habitats'
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in r['prepared_sha256'].items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  return r
 acquired=json.loads((source/'.source-acquired.json').read_text());assert acquired['commit']==PIN
 expected=dict(acquired['sha256'])
 for layer in LAYERS_BEFORE+['family','travel-rules','birth','wild']:
  expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 originals,outputs,inputs={},{},{}
 def read(p):
  if p in outputs:return outputs[p]
  raw=(source/p).read_bytes();assert hashlib.sha256(raw).hexdigest()==expected[p],p
  if p in acquired['sha256']:inputs[p]=acquired['sha256'][p]
  return raw
 def stage(p,body):
  if p in expected and p not in originals:originals[p]=hashlib.sha256(read(p)).hexdigest()
  outputs[p]=body.encode()
 catalog=HERE/'catalog_metadata.json'
 data=json.loads(catalog.read_text());species={int(i):s for i,s in data['species'].items()}
 distribution=plan(source,catalog);by_map={m:h for h in distribution['locations_data'] for m in h['maps']}
 family_by_member={s['id']:f for h in distribution['locations_data'] for f in h['families'] for s in f['species']}
 def stages(f):
  members={s['id'] for s in f['species']};root=f['root'];depth={root:0};pending=[root]
  while pending:
   i=pending.pop(0)
   for t in species[i]['evolutions']:
    if t in members and t not in depth:depth[t]=min(2,depth[i]+1);pending.append(t)
  # Regional base forms share the family's stage, and their evolution follows it.
  for i in members-depth.keys():
   same=next((j for j in depth if species[j]['national_dex']==species[i]['national_dex']),None)
   if same is not None:depth[i]=depth[same]
  for _ in range(3):
   for i in members:
    for t in species[i]['evolutions']:
     if t in members and i in depth:depth.setdefault(t,min(2,depth[i]+1))
  for i in members:depth.setdefault(i,0)
  result=[sorted(i for i in members if depth[i]==d) for d in range(3)]
  for d in [1,2]:
   if not result[d]:result[d]=result[d-1]
  assert all(1<=len(s)<=8 for s in result),(f['name'],result)
  return result
 chains={f['root']:stages(f) for h in distribution['locations_data'] for f in h['families']}
 names={i:s['name'] for i,s in species.items()};names[0]='SPECIES_NONE'
 rows=[]
 for i in range(data['compiled_abi'][13]):
  f=family_by_member.get(i);ss=chains[f['root']] if f else [[i]]*3
  name=names.get(i,'SPECIES_NONE');rows.append('{'+', '.join([names[f['root']] if f else name,
   '{'+', '.join(str(len(x)) for x in ss)+'}','{'+', '.join('{'+', '.join(names.get(j,'SPECIES_NONE') for j in x)+'}' for x in ss)+'}'])+'}')
 # Derive weighted native slots: rare families receive the one-percent slots.
 encounters=json.loads(read('src/data/wild_encounters.json'))
 rates=[20,20,10,10,10,10,5,5,4,4,1,1]
 slots_by_map={};poolrows=[]
 for m,h in by_map.items():
  families=sorted(h['families'],key=lambda f:(f['weight'],f['root']))
  slots={};available=list(range(11,-1,-1))
  for f in families:slots[available.pop(0)]=f['root']
  while available:
   index=available.pop(0)
   best=max(families,key=lambda f:100*f['weight']/sum(x['weight'] for x in families)-sum(rates[s] for s,v in slots.items() if v==f['root']))
   slots[index]=best['root']
  # Native slot sizes are indivisible. Rank final allocations so that a rarer
  # family can never receive a larger total chance than a common family.
  ranked=sorted(families,key=lambda f:(sum(rates[i] for i,v in slots.items() if v==f['root']),f['root']))
  relabel={old['root']:new['root'] for old,new in zip(ranked,families)}
  slots={i:relabel[root] for i,root in slots.items()}
  slots_by_map[m]=[slots[i] for i in range(12)]
  for area in range(5):
   fs=slots_by_map[m]
   poolrows.append('{'+', '.join([m,str(area),str(len(fs)),'{'+', '.join(names[i] for i in fs)+'}'])+'}')
  h.setdefault('slot_chances',{})[m]={names[f['root']]:sum(rates[i] for i,v in slots.items() if v==f['root']) for f in h['families']}
 for e in encounters['wild_encounter_groups'][0]['encounters']:
  if e['map'] not in by_map:continue
  slots=slots_by_map[e['map']]
  for field in ['land_mons','water_mons','rock_smash_mons','fishing_mons','hidden_mons']:
   if field not in e:continue
   for index,mon in enumerate(e[field]['mons']):mon['species']=names[slots[index%12]]
 stage('src/data/wild_encounters.json',json.dumps(encounters,indent=2)+'\n')
 stage('include/journey_wild_data.h','static const struct JourneyWildStages sJourneyWildStages[] = {\n'+',\n'.join(rows)+'\n};\nstatic const struct JourneyWildPool sJourneyWildPools[] = {\n'+',\n'.join(poolrows)+'\n};\n')
 p='src/journey_wild.c';body=read(p).decode()
 # Slot weighting is authoritative; home affinity only adds a small within-habitat variation.
 old=body[body.index('    for (i = 0; i < ARRAY_COUNT(sJourneyWildPools); i++)'):body.index('    family = &sJourneyWildStages[selected];')]
 new="""    for (i = 0; i < ARRAY_COUNT(sJourneyWildPools); i++)
    {
        const struct JourneyWildPool *pool = &sJourneyWildPools[i];
        if (MAP_GROUP(pool->map) == gSaveBlock1Ptr->location.mapGroup
         && MAP_NUM(pool->map) == gSaveBlock1Ptr->location.mapNum && pool->area == area)
        {
            static const u8 rates[] = {20,20,10,10,10,10,5,5,4,4,1,1};
            u32 j, owned = FALSE, roll = Random() % 100;
            for (j = 0; j < pool->count; j++)
                if (sJourneyWildStages[original].root == pool->species[j]) owned = TRUE;
            // Overrides must stay in the assigned habitat; native slots retain their rates.
            if (!owned)
                for (j = 0; j < pool->count; j++)
                {
                    if (roll < rates[j]) { selected = pool->species[j]; break; }
                    roll -= rates[j];
                }
            break;
        }
    }
"""
 body=body.replace(old,new)
 stage(p,body)
 p='src/wild_encounter.c';body=read(p).decode()
 anchor='species = sWildFeebas.species;'
 assert body.count(anchor)==1
 body=body.replace(anchor,'species = JourneyWildSpecies(sWildFeebas.species, WILD_AREA_FISHING);')
 anchor='CreateWildMon(gSaveBlock1Ptr->outbreakPokemonSpecies, gSaveBlock1Ptr->outbreakPokemonLevel);'
 assert body.count(anchor)==1
 body=body.replace(anchor,'CreateWildMon(JourneyWildSpecies(gSaveBlock1Ptr->outbreakPokemonSpecies, WILD_AREA_LAND), gSaveBlock1Ptr->outbreakPokemonLevel);')
 anchor='for (i = 0; i < MAX_MON_MOVES; i++)\n        SetMonMoveSlot(&gParties[B_TRAINER_1][0], gSaveBlock1Ptr->outbreakPokemonMoves[i], i);'
 assert body.count(anchor)==1
 body=body.replace(anchor,'if (GetMonData(&gParties[B_TRAINER_1][0], MON_DATA_SPECIES) == gSaveBlock1Ptr->outbreakPokemonSpecies)\n        '+anchor.replace('\n        ', '\n            '))
 stage(p,body)
 p='src/event_data.c';body=read(p).decode();match=re.search(r'(u8 FlagSet\(u16 id\)\n\{)',body)
 assert match,'FlagSet anchor';body=body.replace(match[1],match[1]+'\n    if (id == FLAG_SYS_POKEDEX_GET) EnableNationalPokedex();',1);stage(p,body)
 # The area screen must recognize all stages, not just the root stored in a slot.
 stage('include/journey_habitats.h','#ifndef GUARD_JOURNEY_HABITATS_H\n#define GUARD_JOURNEY_HABITATS_H\nbool32 JourneyHabitatHasSpecies(u32 group, u32 map, u32 species);\n#endif\n')
 lookup=[]
 for m,h in sorted(by_map.items()):
  allowed=[s['id'] for f in h['families'] for s in f['species']]
  lookup.append('{'+m+', '+str(len(allowed))+', {'+', '.join(names[i] for i in allowed)+'}}')
 max_members=max(sum(len(f['species']) for f in h['families']) for h in distribution['locations_data'])
 stage('include/journey_habitat_data.h','struct JourneyHabitat { u16 map, count; u16 species['+str(max_members)+']; };\nstatic const struct JourneyHabitat sJourneyHabitats[] = {\n'+',\n'.join(lookup)+'\n};\n')
 stage('src/journey_habitats.c','''#include "global.h"
#include "journey_habitats.h"
#include "constants/maps.h"
#include "constants/species.h"
#include "journey_habitat_data.h"
bool32 JourneyHabitatHasSpecies(u32 group, u32 map, u32 species)
{
    u32 i, j;
    for (i = 0; i < ARRAY_COUNT(sJourneyHabitats); i++)
        if (group == MAP_GROUP(sJourneyHabitats[i].map) && map == MAP_NUM(sJourneyHabitats[i].map))
            for (j = 0; j < sJourneyHabitats[i].count; j++)
                if (species == sJourneyHabitats[i].species[j]) return TRUE;
    return FALSE;
}
''')
 p='src/pokedex_area_screen.c';body=read(p).decode().replace('#include "global.h"','#include "global.h"\n#include "journey_habitats.h"')
 a='if (MapHasSpecies(&gWildMonHeaders[i].encounterTypes[gAreaTimeOfDay], species))'
 assert body.count(a)==1;body=body.replace(a,'if (JourneyHabitatHasSpecies(gWildMonHeaders[i].mapGroup, gWildMonHeaders[i].mapNum, species))')
 body=body.replace('sFeebasData[i][0] != NUM_SPECIES', 'FALSE && sFeebasData[i][0] != NUM_SPECIES')
 a='if (sSpeciesHiddenFromAreaScreen[i] == species)';assert body.count(a)==1;body=body.replace(a,'if (FALSE && sSpeciesHiddenFromAreaScreen[i] == species)')
 stage(p,body)
 distribution.update(status='catalog_habitats_candidate',source_commit=PIN, catalog_sha256=hashlib.sha256(catalog.read_bytes()).hexdigest(),
  input_sha256=inputs,original_sha256=originals,prepared_sha256={p:hashlib.sha256(v).hexdigest() for p,v in outputs.items()},national_dex_on_first_pokedex=True,
  complete_legendary_maps=False,water_only_routes_not_yet_migrated=True)
 for p,v in outputs.items():(source/p).parent.mkdir(parents=True,exist_ok=True);(source/p).write_bytes(v)
 marker.write_text(json.dumps(distribution,indent=2)+'\n');return distribution

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
 print(json.dumps(prepare(p.parse_args().source),indent=2))
