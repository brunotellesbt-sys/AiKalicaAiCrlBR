"""Correct native type IDs and assign unique ordinary families across land and water."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import struct
from prepare_family import LAYERS_BEFORE, HERE
from prepare_crossing import PIN

FIELDS=['land_mons','water_mons','rock_smash_mons','fishing_mons','hidden_mons']
LAND_RATES=[20,20,10,10,10,10,5,5,4,4,1,1]
WATER_RATES=[60,30,5,4,1]

def weighted_slots(families,rates):
 families=sorted(families,key=lambda f:(f['weight'],f['root']))
 assert len(families)<=len(rates)
 slots={};available=sorted(range(len(rates)),key=lambda i:(rates[i],i))
 for f in families:slots[available.pop(0)]=f['root']
 while available:
  i=available.pop()
  f=max(families,key=lambda f:sum(rates)*f['weight']/sum(x['weight'] for x in families)-sum(rates[k] for k,v in slots.items() if v==f['root']))
  slots[i]=f['root']
 ranked=sorted(families,key=lambda f:(sum(rates[k] for k,v in slots.items() if v==f['root']),f['root']))
 renames={old['root']:new['root'] for old,new in zip(ranked,families)}
 return [renames[slots[i]] for i in range(len(rates))]

def prepare(source):
 source=Path(source);marker=source/'.journey-ecology'
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in r['prepared_sha256'].items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  return r
 acquired=json.loads((source/'.source-acquired.json').read_text());assert acquired['commit']==PIN
 expected=dict(acquired['sha256'])
 for layer in LAYERS_BEFORE+['family','travel-rules','birth','wild','habitats','sanctuaries']:
  expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 outputs,inputs,originals={},{},{}
 def read(p):
  if p in outputs:return outputs[p]
  raw=(source/p).read_bytes();assert hashlib.sha256(raw).hexdigest()==expected[p],p
  if p in acquired['sha256']:inputs[p]=acquired['sha256'][p]
  return raw
 def stage(p,raw):
  if p in expected and p not in originals:originals[p]=hashlib.sha256(read(p)).hexdigest()
  outputs[p]=raw if isinstance(raw,bytes) else raw.encode()
 catalog=json.loads((HERE/'catalog_metadata.json').read_text());species={int(i):s for i,s in catalog['species'].items()}
 type_ids={name:int(value) for name,value in re.findall(r'\b(TYPE_\w+)\s*=\s*(\d+)',read('include/constants/pokemon.h').decode())}
 assert type_ids['TYPE_WATER']==12 and type_ids['TYPE_GRASS']==13
 old=json.loads((source/'.journey-habitats').read_text());families={f['root']:copy.deepcopy(f) for h in old['locations_data'] for f in h['families']}
 for f in families.values():
  f['species']=[m for m in f['species'] if not species[m['id']]['flags'] & sum(1<<i for i in range(5,11))]
  f['types']=sorted({t for m in f['species'] for t in species[m['id']]['types']})
 water_roots={r for r,f in families.items() if type_ids['TYPE_WATER'] in f['types']}
 groups=json.loads(read('data/maps/map_groups.json'));maps={}
 for g in groups['group_order']:
  for n in groups[g]:
   m=json.loads(read(f'data/maps/{n}/map.json'));m['source_name']=n;maps[m['id']]=m
 encounters=json.loads(read('src/data/wild_encounters.json'));rows=encounters['wild_encounter_groups'][0]['encounters']
 special=json.loads((source/'.journey-sanctuaries').read_text());template_land=next(e['land_mons'] for e in rows if e['map']=='MAP_ROUTE101');template_water=next(e for e in rows if e['map']=='MAP_ROUTE108')
 # New mountain islands have real grass, Surf and fishing encounters; new coast
 # connectors have aquatic encounters without changing their story opponents.
 for site in special['sites']:
  m=next(m for m in maps.values() if m['source_name']==site['surface'])
  row=dict(map=m['id'],base_label='g'+site['surface'],water_mons=copy.deepcopy(template_water['water_mons']),fishing_mons=copy.deepcopy(template_water['fishing_mons']))
  if site['access']=='surf':
   row['land_mons']=copy.deepcopy(template_land)
   layouts=json.loads(read('data/layouts/layouts.json'))['layouts'];lay=next(l for l in layouts if l['id']==m['layout']);raw=read(lay['blockdata_filepath']);blocks=list(struct.unpack('<'+'H'*(len(raw)//2),raw));cx,cy=site['entry']
   for y in range(cy+1,cy+5):
    for x in range(cx-5,cx+6):blocks[y*lay['width']+x]=0x300D
   stage(lay['blockdata_filepath'],struct.pack('<'+'H'*len(blocks),*blocks))
  rows.append(row)
 def section(m):
  s=m['region_map_section']
  if 'CHAMBER' in s:s='MAPSEC_TANOBY_RUINS'
  # Dive follows the same marine habitat as the surface route.
  if s in ['MAPSEC_UNDERWATER_124','MAPSEC_UNDERWATER_126']:s=s.replace('UNDERWATER_','ROUTE_')
  if s=='MAPSEC_S_S_ANNE':s='MAPSEC_VERMILION_CITY'
  return s
 habitats={}
 for e in rows:
  m=maps[e['map']];s=section(m);h=habitats.setdefault(s,dict(section=s,maps=[],land=False,water=False,families=[]))
  if e['map'] not in h['maps']:h['maps'].append(e['map'])
  h['land']|=bool(e.get('land_mons',{}).get('mons'))
  h['water']|=any(bool(e.get(k,{}).get('mons')) for k in ['water_mons','fishing_mons'])
 marine=sorted(s for s,h in habitats.items() if h['water'] and not h['land']);terrestrial=sorted(s for s,h in habitats.items() if h['land'])
 assert len(marine)<=len(water_roots),(len(marine),len(water_roots))
 land_base,land_extra=divmod(len(families)-len(marine),len(terrestrial))
 capacities={s:1 if s in marine else land_base+(terrestrial.index(s)<land_extra) for s in habitats}
 used=set()
 def tags(h):
  n=h['section'];names=[];remote=3
  if any(t in n for t in ['FOREST','WOODS','BUSH','BERRY','ROUTE_104','ROUTE_119','ROUTE_120']):names+=['GRASS','BUG','POISON','FLYING']
  if any(t in n for t in ['SHOAL','ICEFALL','SEAFOAM']):names+=['ICE','WATER'];remote=7
  if any(t in n for t in ['EMBER','FIERY','JAGGED','MAGMA','ROUTE_112']):names+=['FIRE','GROUND','ROCK'];remote=7
  if any(t in n for t in ['CAVE','TUNNEL','MOON','FALLS','DESERT','ROAD','TOWER','RUINS']):names+=['GROUND','ROCK','STEEL','DRAGON']
  if any(t in n for t in ['TOWER','PYRE','MEMORIAL','LOST','MANSION']):names+=['GHOST','PSYCHIC','DARK']
  if not h['land'] and any(t in n for t in ['ABANDONED','OUTCAST','LABYRINTH','EVER_GRANDE','ROUTE_128','ROUTE_129','ROUTE_131','ROUTE_132','ROUTE_133','ROUTE_134']):remote=9
  if any(t in n for t in ['SAFARI','ARTISAN','SKY_PILLAR','CANYON','ALTERING','CERULEAN_CAVE','ORIGIN','SEAFLOOR']):remote=9
  if re.search(r'ROUTE_(1|2|3|5|6|101|102|103|104)$',n):remote=0
  if not names:names=['NORMAL','FIGHTING','FLYING','BUG','GRASS','ELECTRIC','FAIRY']
  if h['water']:names+=['WATER']
  return {type_ids['TYPE_'+t] for t in names},remote
 def score(root,h):
  f=families[root];ts,remote=tags(h)
  return 4*len(set(f['types'])&ts)+f['rarity']*remote-max(0,remote-4)*(f['rarity']==0)
 # Reserve one unique aquatic family for every exclusively marine location.
 marine=sorted(marine,key=lambda s:(-tags(habitats[s])[1],s))
 canonical_ids=set(catalog['canonical_species'].values())
 marine_roots={r for r in water_roots if all(type_ids['TYPE_WATER'] in species[m['id']]['types'] for m in families[r]['species'] if m['id'] in canonical_ids)}
 for s in marine:
  candidates=marine_roots-used;r=max(candidates,key=lambda r:(score(r,habitats[s]),int(hashlib.sha256((str(r)+s).encode()).hexdigest()[:8],16)))
  habitats[s]['families'].append(families[r]);used.add(r)
 # The remaining Water families fill distinct shore/river habitats. If there are
 # more ponds than aquatic families, quiet ponds have no encounters: no repeats.
 mixed=sorted((s for s in terrestrial if habitats[s]['water']),key=lambda s:(-tags(habitats[s])[1],s))
 for r in sorted(water_roots-used,key=lambda r:(-families[r]['rarity'],r)):
  candidates=[s for s in mixed if not any(f['root'] in water_roots for f in habitats[s]['families'])]
  if not candidates:candidates=[s for s in terrestrial if len(habitats[s]['families'])<capacities[s]]
  s=max(candidates,key=lambda s:(score(r,habitats[s]),int(hashlib.sha256((str(r)+s).encode()).hexdigest()[:8],16)))
  habitats[s]['families'].append(families[r]);used.add(r)
 for r in sorted(set(families)-used,key=lambda r:(-families[r]['rarity'],r)):
  candidates=[s for s in terrestrial if len(habitats[s]['families'])<capacities[s]]
  s=max(candidates,key=lambda s:(score(r,habitats[s]),int(hashlib.sha256((str(r)+s).encode()).hexdigest()[:8],16)))
  habitats[s]['families'].append(families[r]);used.add(r)
 assert used==set(families)
 by_map={m:h for h in habitats.values() for m in h['maps']};pools={};quiet=set();map_members={};field_chances={}
 for e in rows:
  h=by_map[e['map']];all_f=h['families'];aquatic=[f for f in all_f if f['root'] in water_roots]
  members=map_members.setdefault(e['map'],set());chances=field_chances.setdefault(e['map'],{})
  for area,field in enumerate(FIELDS):
   if field not in e:continue
   fs=aquatic if field in ['water_mons','fishing_mons'] else all_f
   if not fs:del e[field];quiet.add(e['map']);continue
   if field=='fishing_mons':
    slot_roots=[]
    for rates in [[70,30],[60,20,20],[40,40,15,4,1]]:
     tier=sorted(fs,key=lambda f:(f['rarity'],f['root']))[:len(rates)]
     slot_roots+=weighted_slots(tier,rates)
   else:
    rates=LAND_RATES if field in ['land_mons','hidden_mons'] else WATER_RATES
    rates=rates[:len(e[field]['mons'])]
    slot_roots=weighted_slots(fs[:len(rates)],rates)
   if field=='water_mons':e[field]['encounter_rate']=[8,6,3,1][min(f['rarity'] for f in fs)]
   for mon,r in zip(e[field]['mons'],slot_roots):mon['species']=species[r]['name']
   pool_slots=weighted_slots(fs,LAND_RATES);pools[(e['map'],area)]=pool_slots
   members.update(mon['id'] for f in fs for mon in f['species'])
   chances[field]=dict(slots=[species[r]['name'] for r in slot_roots])
 stage('src/data/wild_encounters.json',json.dumps(encounters,indent=2)+'\n')
 family_by_member={m['id']:f for f in families.values() for m in f['species']}
 def stages(f):
  ids={m['id'] for m in f['species']};depth={f['root']:0};pending=[f['root']]
  while pending:
   parent=pending.pop(0)
   for child in species[parent]['evolutions']:
    if child in ids and child not in depth:depth[child]=min(2,depth[parent]+1);pending.append(child)
  for i in ids-depth.keys():
   same=next((j for j in depth if species[j]['national_dex']==species[i]['national_dex']),None)
   if same is not None:depth[i]=depth[same]
  for _ in range(3):
   for i in ids:
    for child in species[i]['evolutions']:
     if child in ids and i in depth:depth.setdefault(child,min(2,depth[i]+1))
  for i in ids:depth.setdefault(i,0)
  result=[sorted(i for i in ids if depth[i]==d) for d in range(3)]
  for d in [1,2]:
   if not result[d]:result[d]=result[d-1]
  assert all(0<len(s)<=8 for s in result)
  return result
 chains={r:stages(f) for r,f in families.items()};stage_rows=[]
 for i in range(catalog['compiled_abi'][13]):
  f=family_by_member.get(i);ss=chains[f['root']] if f else [[i]]*3
  name=species.get(i,{}).get('name','SPECIES_NONE')
  stage_rows.append('{'+', '.join([species[f['root']]['name'] if f else name,'{'+', '.join(str(len(x)) for x in ss)+'}','{'+', '.join('{'+', '.join(species.get(j,{}).get('name','SPECIES_NONE') for j in x)+'}' for x in ss)+'}'])+'}')
 p='include/journey_wild_data.h';body='static const struct JourneyWildStages sJourneyWildStages[] = {\n'+',\n'.join(stage_rows)+'\n};\n'

 body+='static const struct JourneyWildPool sJourneyWildPools[] = {\n'+',\n'.join('{'+', '.join([m,str(a),str(len(slots)),'{'+', '.join(species[r]['name'] for r in slots)+'}'])+'}' for (m,a),slots in sorted(pools.items()))+'\n};\n';stage(p,body)
 fishing_rates={m:[100,75,40,15][min(f['rarity'] for f in by_map[m]['families'] if f['root'] in water_roots)] for m,a in pools if a==3}
 stage('include/journey_wild_data.h',outputs['include/journey_wild_data.h']+('struct JourneyFishingHabitat { u16 map; u8 percent; };\nstatic const struct JourneyFishingHabitat sJourneyFishingHabitats[] = {\n'+',\n'.join('{'+m+', '+str(percent)+'}' for m,percent in sorted(fishing_rates.items()))+'\n};\n').encode())
 p='src/journey_wild.c';body=read(p).decode()
 anchor='    return family->stages[stage][Random() % family->count[stage]];'
 assert body.count(anchor)==1
 body=body.replace(anchor,"""    if (area == 1 || area == 3)
    {
        u16 eligible[8]; u32 count = 0;
        for (i = 0; i < family->count[stage]; i++)
        {
            u32 mon = family->stages[stage][i];
            if (gSpeciesInfo[mon].types[0] == TYPE_WATER || gSpeciesInfo[mon].types[1] == TYPE_WATER)
                eligible[count++] = mon;
        }
        if (count) return eligible[Random() % count];
    }
"""+anchor)
 body+="""
u32 JourneyFishingOdds(u32 base)
{
    u32 i;
    for (i = 0; i < ARRAY_COUNT(sJourneyFishingHabitats); i++)
        if (MAP_GROUP(sJourneyFishingHabitats[i].map) == gSaveBlock1Ptr->location.mapGroup
         && MAP_NUM(sJourneyFishingHabitats[i].map) == gSaveBlock1Ptr->location.mapNum)
            return max(1, base * sJourneyFishingHabitats[i].percent / 100);
    return base;
}
"""
 stage(p,body)
 p='include/journey_wild.h';body=read(p).decode();assert '#endif' in body;stage(p,body.replace('#endif','u32 JourneyFishingOdds(u32 base);\n#endif'))
 p='src/fishing.c';body=read(p).decode().replace('#include "global.h"','#include "global.h"\n#include "journey_wild.h"')
 anchor='<= CalculateFishingBiteOdds(rod, isStickyHold)';assert body.count(anchor)==1;stage(p,body.replace(anchor,'<= JourneyFishingOdds(CalculateFishingBiteOdds(rod, isStickyHold))'))
 max_members=max(map(len,map_members.values()));lookup=[]
 for m,ids in sorted(map_members.items()):lookup.append('{'+m+', '+str(len(ids))+', {'+', '.join(species[i]['name'] for i in sorted(ids))+'}}')
 stage('include/journey_habitat_data.h','struct JourneyHabitat { u16 map, count; u16 species['+str(max_members)+']; };\nstatic const struct JourneyHabitat sJourneyHabitats[] = {\n'+',\n'.join(lookup)+'\n};\n')
 p='src/pokedex_area_screen.c';body=read(p).decode();anchor='            case MAP_GROUP_SPECIAL_AREA_FRLG:\n                SetSpecialMapHasMon(gWildMonHeaders[i].mapGroup, gWildMonHeaders[i].mapNum);\n                break;'
 assert body.count(anchor)==1
 body=body.replace(anchor,anchor+'\n            default:\n                SetAreaHasMon(gWildMonHeaders[i].mapGroup, gWildMonHeaders[i].mapNum);\n                break;');stage(p,body)
 locations=[]
 for s,h in sorted(habitats.items()):
  locations.append(dict(section=s,maps=sorted(h['maps']),family_count=len(h['families']),families=sorted(h['families'],key=lambda f:f['root']),land=h['land'],water=h['water'],native_types=sorted(tags(h)[0]),remoteness=tags(h)[1]))
 r=dict(status='complete_ordinary_ecology_candidate',source_commit=PIN,type_ids=type_ids,ordinary_base_species=920,families=444,aquatic_families=len(water_roots),
  marine_locations=len(marine),terrestrial_locations=len(terrestrial),terrestrial_family_count_range=[land_base,land_base+bool(land_extra)],locations_data=locations,
  map_species={m:sorted(ids) for m,ids in sorted(map_members.items())},pools=[dict(map=m,area=a,roots=slots) for (m,a),slots in sorted(pools.items())],quiet_water_maps=sorted(quiet),fishing_bite_percent=fishing_rates,field_slots=field_chances,
  no_family_repeated_between_locations=True,all_random_encounters_exclude_specials=True,all_aquatic_slots_use_water_families=True,
  input_sha256=inputs,original_sha256=originals,prepared_sha256={p:hashlib.sha256(v).hexdigest() for p,v in outputs.items()},map_complete=False)
 for p,raw in outputs.items():(source/p).parent.mkdir(parents=True,exist_ok=True);(source/p).write_bytes(raw)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
 print(json.dumps(prepare(p.parse_args().source),indent=2))
