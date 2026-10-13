"""Allocate the actual Gen 1–4 families once per habitat, retaining aquatic roots."""
from pathlib import Path
import copy,json
from aquatic_species import aquatic_ids
ROOT=Path(__file__).resolve().parents[2]
def allocate(source):
 source=Path(source);locations=copy.deepcopy(json.loads((source/'.journey-five-island-habitat').read_text())['locations_data']);catalog=json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text())['species']
 families={f['root']:copy.deepcopy(f) for l in locations for f in l['families'] if any(s['national_dex']<=493 for s in f['species'])}
 original={f['root']:l['section'] for l in locations for f in l['families']}
 for f in families.values():f['species']=[s for s in f['species'] if s['national_dex']<=493]
 swimmers=aquatic_ids(catalog)
 aquatic=lambda f:f['root'] in swimmers
 # Keep families with fixed story encounters in their established habitat.
 protected={96,104,131,201,352,446}
 for l in locations:l['families']=[]
 for root in protected & families.keys():
  target=next(l for l in locations if l['section']==original[root])
  target['families'].append(families.pop(root))
 def score(l,f):return (100 if original[f['root']]==l['section'] else 0)+4*len(set(l.get('native_types',[]))&set(f['types']))-abs(l.get('remoteness',8)-f['rarity']*3)
 # Water-only locations get swimming families, never a terrestrial base stage.
 for l in sorted(locations,key=lambda l:(l['land'],l['section'])):
  if l['families']:continue
  candidates=[f for f in families.values() if l['land'] or aquatic(f)]
  assert candidates,l['section'];f=max(candidates,key=lambda f:(score(l,f),-f['root']));l['families'].append(f);families.pop(f['root'])
 for f in sorted(families.values(),key=lambda f:(not aquatic(f),f['root'])):
  candidates=[l for l in locations if l['land'] or aquatic(f)]
  l=max(candidates,key=lambda l:(-len(l['families']),score(l,f),l['section']));l['families'].append(f)
 roots=[f['root'] for l in locations for f in l['families']];assert len(roots)==len(set(roots))==212
 pools=[];habitats=[]
 for l in locations:
  for ident in l['maps']:
   habitats.append(dict(map=ident,species=[s['name'] for f in l['families'] for s in f['species']]))
   for area in range(5):
    eligible=[f['name'] for f in l['families'] if (l['land'] if area in [0,2,4] else l['water'] and aquatic(f))]
    pools.append(dict(map=ident,area=area,roots=eligible))
 return dict(locations=locations,pools=pools,habitats=habitats,families=len(roots),no_family_repeated=True,aquatic_base_stages_only=True)
