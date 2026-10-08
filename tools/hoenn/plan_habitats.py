"""Assign every ordinary evolutionary family to one map section, using native habitat traits."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[2]

def plan(source,catalog):
 source=Path(source);data=json.loads(Path(catalog).read_text());assert data['passed']
 species={int(i):s for i,s in data['species'].items()};canonical={int(n):int(i) for n,i in data['canonical_species'].items()}
 allowed={i for i in canonical.values() if not species[i]['special']}
 allowed.update(i for i,s in species.items() if s['regional'] and not s['special'])
 parents={}
 for i,s in sorted(species.items()):
  for child in s['evolutions']:
   if i in allowed and child in allowed:parents.setdefault(child,i)
 for i in allowed:
  base=canonical.get(species[i]['national_dex'])
  if i!=base and i not in parents and base in allowed:parents[i]=base
 def root(i):
  seen=set()
  while i in parents:
   assert i not in seen,i
   seen.add(i);i=parents[i]
  return i
 families=defaultdict(list)
 for i in sorted(allowed):families[root(i)].append(i)
 groups=json.loads((source/'data/maps/map_groups.json').read_text());maps={}
 for g in groups['group_order']:
  for n in groups[g]:
   m=json.loads((source/f'data/maps/{n}/map.json').read_text());m['source_name']=n;maps[m['id']]=m
 encounters=json.loads((source/'src/data/wild_encounters.json').read_text())['wild_encounter_groups'][0]['encounters']
 habitats={}
 for e in encounters:
  if not e.get('land_mons',{}).get('mons'):continue
  m=maps[e['map']];section=m['region_map_section']
  if any(t in section for t in ['CHAMBER']):section='MAPSEC_TANOBY_RUINS'
  h=habitats.setdefault(section,dict(section=section,maps=[],names=[],original_species=set()))
  if m['id'] not in h['maps']:h['maps'].append(m['id']);h['names'].append(m['source_name'])
  h['original_species'].update(x['species'] for x in e['land_mons']['mons'])
 def traits(h):
  n=h['section'];tags=set();remote=3
  if any(t in n for t in ['FOREST','WOODS','BUSH','BERRY','ROUTE_104','ROUTE_119','ROUTE_120']):tags.update([6,12,3,2])
  if any(t in n for t in ['WATER','BEACH','CAPE','ISLAND','SEAFOAM','ROUTE_12','ROUTE_13','ROUTE_21','ROUTE_118','ROUTE_130']):tags.update([11,2,13])
  if any(t in n for t in ['SHOAL','ICEFALL','SEAFOAM']):tags.update([15,11]);remote=7
  if any(t in n for t in ['EMBER','FIERY','JAGGED','MAGMA','ROUTE_112']):tags.update([10,4,5]);remote=7
  if any(t in n for t in ['CAVE','TUNNEL','MOON','FALLS','DESERT','ROAD','TOWER','RUINS','CHAMBER']):tags.update([4,5,8,16])
  if any(t in n for t in ['TOWER','PYRE','MEMORIAL','LOST','MANSION']):tags.update([7,14,17])
  if any(t in n for t in ['SAFARI','ARTISAN','SKY_PILLAR','CANYON','ALTERING','CERULEAN_CAVE','ORIGIN','SEAFLOOR']):remote=9
  if any(t in n for t in ['ROUTE_1','ROUTE_2','ROUTE_3','ROUTE_5','ROUTE_6','ROUTE_101','ROUTE_102','ROUTE_103','ROUTE_104']):
   if re.search(r'ROUTE_(1|2|3|5|6|101|102|103|104)$',n):remote=0
  if not tags:tags.update([0,1,2,3,6,12,13,18])
  return sorted(tags),remote
 sites=sorted(habitats)
 low,extra=divmod(len(families),len(sites));capacities={s:low+(i<extra) for i,s in enumerate(sites)}
 assigned={s:[] for s in sites}
 def rarity(root_id,members):
  catch=min(species[i]['catch_rate'] for i in members)
  rootcatch=species[root_id]['catch_rate']
  return 3 if rootcatch<=45 else 2 if rootcatch<=90 else 1 if catch<=45 else 0
 # Rarer families choose their habitats first, before dense common species.
 for r,members in sorted(families.items(),key=lambda kv:(-rarity(*kv),kv[0])):
  types={t for i in members for t in species[i]['types']}
  names={species[i]['name'] for i in members}
  rare=rarity(r,members)
  candidates=[]
  for section,h in habitats.items():
   if len(assigned[section])>=capacities[section]:continue
   tags,remote=traits(h)
   score=4*len(types&set(tags)) + rare*remote
   if rare==0:score-=max(0,remote-4)
   if names & h['original_species']:score+=5
   # Stable tie-breaks distribute generations instead of filling one region first.
   tie=int(hashlib.sha256((str(r)+section).encode()).hexdigest()[:8],16)
   candidates.append((-score,tie,section))
  section=min(candidates)[2];assigned[section].append(r)
 locations=[]
 for section in sites:
  h=habitats[section];rows=[]
  for r in sorted(assigned[section]):
   members=families[r];rare=rarity(r,members)
   weight=[10,6,3,1][rare]
   rows.append(dict(root=r,name=species[r]['name'],weight=weight,rarity=rare,
    species=[dict(id=i,name=species[i]['name'],national_dex=species[i]['national_dex']) for i in members]))
  denominator=sum(r['weight'] for r in rows)
  for row in rows:row['base_family_chance_percent']=round(row['weight']*100/denominator,3)
  locations.append(dict(section=section,maps=sorted(h['maps']),family_count=len(rows),families=rows,
   habitat_types=traits(h)[0],remoteness=traits(h)[1]))
 assert sum(h['family_count'] for h in locations)==len(families)
 assigned_base={i for h in locations for f in h['families'] for i in [s['id'] for s in f['species']] if i in canonical.values()}
 assert assigned_base==set(canonical.values())-set(data['special_species'])
 return dict(status='habitat_distribution_plan_not_installed',ordinary_base_species=len(assigned_base),special_species=len(data['special_species']),
  families=len(families),locations=len(locations),family_count_range=[low,low+bool(extra)],no_family_repeated_between_locations=True,
  locations_data=locations,special_catalog=[species[i] for i in data['special_species']],
  level_policy='party mean -5 to +2, clamped 1..100',evolution_progress='floor mean of regional badge counts',
  special_unlock='16 badges before either League',map_complete=False)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
 p.add_argument('--catalog',type=Path,default=ROOT/'mods/hoenn/integration-validation/native-catalog.json')
 p.add_argument('--output',type=Path,default=ROOT/'mods/hoenn/integration-validation/habitat-plan.json')
 a=p.parse_args();r=plan(a.source,a.catalog);a.output.write_text(json.dumps(r,indent=2)+'\n')
 print('Plan:',r['ordinary_base_species'],'ordinary species;',r['families'],'families;',r['locations'],'habitats;',r['family_count_range'],'families per habitat')
