"""Compile updated allocations using the same weighted native ecology writer."""
import json,textwrap
from pathlib import Path
from prepare_ecology import FIELDS,LAND_RATES,WATER_RATES,weighted_slots
ROOT=Path(__file__).resolve().parents[2]
def compile_tables(source,locations):
 catalog=json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text());species={int(i):s for i,s in catalog['species'].items()};habitats={h['section']:h for h in locations};families={f['root']:f for h in locations for f in h['families']};water_roots={r for r in families if 12 in species[r]['types']}
 encounters=json.loads((Path(source)/'src/data/wild_encounters.json').read_text());rows=encounters['wild_encounter_groups'][0]['encounters'];outputs={}
 def stage(p,raw):outputs[p]=raw.encode() if isinstance(raw,str) else raw
 # Reuse the established native slot weights, family stages and fishing rates.
 code=(ROOT/'tools/hoenn/prepare_ecology.py').read_text();code=code.split(' by_map={m:h for h in habitats.values()',1)[1];code=' by_map={m:h for h in habitats.values()'+code;code=code.split(" p='src/journey_wild.c'",1)[0]
 ns=dict(catalog=catalog,species=species,habitats=habitats,families=families,water_roots=water_roots,encounters=encounters,rows=rows,outputs=outputs,stage=stage,FIELDS=FIELDS,LAND_RATES=LAND_RATES,WATER_RATES=WATER_RATES,weighted_slots=weighted_slots,json=json)
 exec(compile(textwrap.dedent(code),'ecology-writer','exec'),ns)
 members=ns['map_members'];size=max(map(len,members.values()))
 outputs['include/journey_habitat_data.h']=('struct JourneyHabitat {u16 map,count;u16 species['+str(size)+'];};\nstatic const struct JourneyHabitat sJourneyHabitats[]={\n'+''.join('{'+m+','+str(len(ids))+',{'+','.join(species[i]['name'] for i in sorted(ids))+'}},\n' for m,ids in sorted(members.items()))+'};\n').encode()
 return outputs,dict(locations_data=locations,map_species={m:sorted(ids) for m,ids in members.items()},pools=[dict(map=m,area=a,roots=roots) for (m,a),roots in ns['pools'].items()],field_slots=ns['field_chances'])
