"""Freeze Smogon analysis sets, prioritizing OU and retaining per-species provenance."""
import argparse,json,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def norm(value):return re.sub('[^a-z0-9]','',value.lower())
def symbols(source,kind,file):
 return {norm(v.removeprefix(kind+'_')):v for v in set(re.findall(kind+r'_\w+', (source/file).read_text()))}
def import_profiles(source,reference):
 source,reference=Path(source),Path(reference);catalog=json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text());db=json.loads((ROOT/'tools/hoenn/data/scarlet-violet-database.json').read_text())
 datasets={p.stem:json.loads(p.read_text()) for p in reference.glob('*.json')};lookup={name:{norm(k):v for k,v in data.items()} for name,data in datasets.items()}
 moves=symbols(source,'MOVE','include/constants/moves.h');moves.update({'highjumpkick':moves.get('hijumpkick'),'vicegrip':moves.get('visegrip')});items=symbols(source,'ITEM','include/constants/items.h');abilities=symbols(source,'ABILITY','include/constants/abilities.h');natures=symbols(source,'NATURE','include/constants/pokemon.h')
 statkeys=['hp','atk','def','spa','spd','spe'];tierorder=['ou','nationaldex','uu','nationaldexuu','ru','nationaldexru','nu','pu','zu','nfe','lc','ubers']
 def one(value):return value[0] if isinstance(value,list) else value
 profiles={};missing_moves=set()
 for sid,wanted in db['species'].items():
  species=catalog['species'].get(sid)
  if not species:continue
  key=wanted['key'];chosen=origin=tier=None
  for name in ['gen9ou','gen9nationaldex','gen8ou','gen9lc','gen8lc']:
   sets=lookup.get(name,{}).get(key)
   if sets:origin=name;chosen=next(iter(sets.items()));tier=name;break
  if chosen is None and key in lookup.get('gen9',{}):
   tiers=lookup['gen9'][key]
   eligible=[t for t in tiers if t in tierorder or t in ['nationaldexubers','nationaldexag','nationaldexru','nationaldexnu','nationaldexpu']]
   if not eligible:continue
   target=min(eligible,key=lambda t: tierorder.index(t) if t in tierorder else len(tierorder))
   if tiers[target]:chosen=next(iter(tiers[target].items()));origin='gen9';tier=target
  if chosen is None:continue
  setname,build=chosen;evdict=one(build.get('evs',{}));evs=[int(evdict.get(k,0)) for k in statkeys]
  if 'lc' in tier:
   # Level-5 LC breakpoints do not transfer to a level-scaled full campaign.
   major=sorted(range(6),key=lambda i:(evs[i],i),reverse=True)[:2];evs=[0]*6
   for i in major:evs[i]=252
  if not sum(evs):
   attack=1 if species['stats'][1]>=species['stats'][4] else 3;evs[attack]=252;evs[5 if species['stats'][3]>=75 else 0]=252
  assert all(0<=v<=252 for v in evs) and sum(evs)<=510,(sid,evs)
  for i in sorted(range(6),key=lambda i:(evs[i]==0,-evs[i],i)):
   add=min(510-sum(evs),252-evs[i]);evs[i]+=add
   if sum(evs)==510:break
  nature=one(build.get('nature','Jolly' if evs[1]>evs[3] else 'Timid'));nature=natures.get(norm(nature),'NATURE_ADAMANT' if evs[1]>evs[3] else 'NATURE_MODEST')
  groups=[]
  for options in build.get('moves',[])[:4]:
   options=options if isinstance(options,list) else [options];group=[]
   for option in options:
    symbol=moves.get(norm(option))
    if symbol and symbol not in group:group.append(symbol)
    else:
     if not symbol:missing_moves.add(option)
   groups.append(group[:6])
  while len(groups)<4:groups.append([])
  item=one(build.get('item','Leftovers'));item=items.get(norm(item),'ITEM_LEFTOVERS')
  # Z crystals and transformation-only items do not add banned mechanics.
  if item.endswith('_Z') or 'MEGA_' in item or 'DYNAMAX' in item or (norm(item.removeprefix('ITEM_'))!='eviolite' and norm(item).endswith(('ite','itex','itey'))) or item in ['ITEM_RED_ORB','ITEM_BLUE_ORB']:item='ITEM_LEFTOVERS'
  ability=abilities.get(norm(one(build.get('ability',''))),'ABILITY_NONE')
  profiles[sid]=dict(species=species['name'],source=origin,tier=tier,set=setname,nature=nature,evs=evs,item=item,ability=ability,moves=groups,role='physical' if evs[1]>evs[3] else 'special' if evs[3]>evs[1] else 'physical' if species['stats'][1]>=species['stats'][4] else 'special')
 result=dict(reference_repository='pkmn/smogon',reference_commit=(reference/'commit.txt').read_text().strip(),reference_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in reference.glob('*.json')},ou_prioritized=True,all_ivs=31,total_evs=510,level_5_lc_spreads_rescaled=True,missing_native_moves=sorted(missing_moves),profiles=profiles)
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=import_profiles(a.source,a.reference);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print('Frozen competitive profiles:',len(r['profiles']))
