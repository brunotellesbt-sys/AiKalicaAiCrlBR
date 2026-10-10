"""Normalize pinned Pokémon Showdown data into the native Gen 9 reference.

Input JSON must be decoded from the TypeScript blobs listed in provenance.json.
Source must be the unmodified baseline ROM, before battle-database preparation.
"""
import argparse,sys
import json,re,hashlib,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--downloads',type=Path,required=True);p.add_argument('--source',type=Path,required=True);args=p.parse_args();root=args.downloads
provenance=json.loads((root/'provenance.json').read_text())
assert provenance['commit']=='942cda71d14bf0618bd57991708a2e2734b6daba'
for file in provenance['files']:
 raw=(root/(file['file']+'.ts')).read_bytes()
 assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==file['git_blob_sha']
for file,key in [('learnsets','Learnsets'),('pokedex','Pokedex'),('moves','Moves')]:
 code='const m=await import('+json.dumps((root/(file+'.ts')).resolve().as_uri())+');process.stdout.write(JSON.stringify(m['+json.dumps(key)+']));'
 (root/(file+'.json')).write_bytes(subprocess.check_output(['node','--input-type=module','-e',code]))
from audit_battle_database import compiled
(root/'compiled.json').write_text(json.dumps(compiled(args.source)))
learn=json.loads((root/'learnsets.json').read_text());dex=json.loads((root/'pokedex.json').read_text());moves=json.loads((root/'moves.json').read_text());actual=json.loads((root/'compiled.json').read_text());catalog=json.loads((Path(__file__).resolve().parent/'catalog_metadata.json').read_text())
normalize=lambda s:re.sub('[^a-z0-9]','',s.lower())
types={'Normal':1,'Fighting':2,'Flying':3,'Poison':4,'Ground':5,'Rock':6,'Bug':7,'Ghost':8,'Steel':9,'Fire':11,'Water':12,'Grass':13,'Electric':14,'Psychic':15,'Ice':16,'Dragon':17,'Dark':18,'Fairy':19}
refmoves={};move_by_key={};unmatched_moves=[]
for mid,a in actual['moves'].items():
 key=normalize(a['name'].removeprefix('MOVE_')) if a['name'] else ''
 key={'smellingsalts':'smellingsalts','faintattack':'feintattack'}.get(key,key)
 if key not in moves:unmatched_moves.append(a['name']);continue
 m=moves[key];move_by_key[key]=int(mid)
 if m.get('isZ') or m.get('isMax'):continue
 refmoves[mid]=dict(key=key,type=types[m['type']],category={'Physical':0,'Special':1,'Status':2}[m['category']],power=m['basePower'],accuracy=0 if m['accuracy'] is True else m['accuracy'],pp=m['pp'],priority=m.get('priority',0))
print('Unmatched moves:',unmatched_moves)
# Keep the user's explicitly requested changes.
refmoves['15']['type']=13;refmoves['70']['type']=6
canon={}
for k,v in dex.items():
 if 1<=v.get('num',0)<=1025 and not v.get('baseSpecies'):canon[v['num']]=k
refs={};missing=[];aliases={'nidoranf':'nidoranf','nidoranm':'nidoranm','mimejr':'mimejr','mrmime':'mrmime','taurospaldeancombatbreed':'taurospaldeacombat','taurospaldeanaquabreed':'taurospaldeaaqua','taurospaldeanblazebreed':'taurospaldeablaze','ursalunabloodmoon':'ursalunabloodmoon'}
for sid,a in actual['species'].items():
 key=normalize(a['name'].removeprefix('SPECIES_'));key=aliases.get(key,key)
 if key not in dex:
  for old,new in [('alolan','alola'),('galarian','galar'),('hisuian','hisui'),('paldean','paldea')]:key=key.replace(old,new)
 if key not in dex:
  if sid in {str(x) for x in catalog['canonical_species'].values()}:
   nd=catalog['species'][sid]['national_dex'];key=canon[nd]
  else:missing.append(a['name']);continue
 d=dex[key]
 if 'types' not in d:
  parent=normalize(d.get('baseSpecies',d.get('changesFrom','')));d={**dex[parent],**d}
 l=learn.get(key,{})
 if not l.get('learnset'):
  keylearn=normalize(d.get('baseSpecies',d.get('changesFrom',d['name'])));l=learn.get(keylearn,{})
 else:keylearn=key
 available={}
 for move,sources in l.get('learnset',{}).items():
  for tag in sources:
   match=re.fullmatch(r'([1-9])L(\d+)',tag)
   if match:available.setdefault(int(match[1]),[]).append((int(match[2]),move))
 if not available:
  # Mega/form entries inherit their base level-up table.
  base=normalize(d.get('baseSpecies',d.get('changesFrom','')))
  for move,sources in learn.get(base,{}).get('learnset',{}).items():
   for tag in sources:
    match=re.fullmatch(r'([1-9])L(\d+)',tag)
    if match:available.setdefault(int(match[1]),[]).append((int(match[2]),move))
 if not available:missing.append(a['name']);continue
 gen=max(available);pairs=[]
 for level,move in available[gen]:
  if move not in move_by_key:raise ValueError((a['name'],move))
  pairs.append([level,move_by_key[move]])
 ts=[types[t] for t in d['types']];ts=ts if len(ts)==2 else ts*2
 refs[sid]=dict(key=key,reference_generation=gen,types=ts,learnset=sorted(set(map(tuple,pairs))))
# Transformed, costume and totem records share the native base level-up table.
# Their event/signature moves are separate from leveling and are not imported.
tables={}
for sid,w in refs.items():tables.setdefault(actual['species'][sid]['learnset_symbol'],[]).append(sid)
for ids in tables.values():
 primary=min(ids,key=int)
 for sid in ids:
  if sid!=primary:
   refs[sid]['learnset']=refs[primary]['learnset']
   refs[sid]['inherits_species_id']=int(primary)
   refs[sid]['reference_generation']=refs[primary]['reference_generation']
for sid,row in refs.items():row['native_table']=actual['species'][sid]['learnset_symbol']
canonical={str(x) for x in catalog['canonical_species'].values()}
assert canonical<=set(refs),(canonical-set(refs))
out=Path(__file__).resolve().parent/'data';out.mkdir(exist_ok=True)
(out/'scarlet-violet-database.json').write_text(json.dumps(dict(provenance=json.loads((root/'provenance.json').read_text()),species=refs,moves=refmoves,unmatched_forms=missing,custom_rules={'Cut':'Grass','Strength':'Rock','Battle Bond':'Gen 7 transformation'}),separators=(',',':'))+'\n')
print('Reference:',len(refs),'species/forms;',len(refmoves),'moves;',len(missing),'custom or unmatched forms')

# Preserve the engine's numeric sentinel/coefficient representation, rather than
# replacing dynamic, fixed-damage and OHKO moves with zero-damage attacks.
one=['guillotine','horndrill','sonicboom','lowkick','counter','seismictoss','dragonrage','fissure','nightshade','bide','psywave','superfang','flail','reversal','return','present','frustration','magnitude','mirrorcoat','beatup','spitup','naturepower','endeavor','sheercold','gyroball','naturalgift','metalburst','fling','trumpcard','grassknot','heavyslam','electroball','finalgambit','heatcrash','naturesmadness','pikapapow','veeveevolley','ruination','comeuppance']
representations=dict.fromkeys(one,1);representations.update(wringout=120,crushgrip=120,punishment=60,hardpress=100)
path=out/'scarlet-violet-database.json';reference=json.loads(path.read_text())
for move in reference['moves'].values():
 if move['key'] in representations:
  assert move['power']==0;move['engine_power']=representations[move['key']]
reference['engine_power_representation']='Nonzero sentinel or formula coefficient; official power stays zero for dynamic/fixed/OHKO moves.'
path.write_text(json.dumps(reference,separators=(',',':'))+'\n')
