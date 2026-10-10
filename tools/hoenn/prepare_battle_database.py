"""Pin Gen 9 move data and replace native level-up tables with the audited reference."""
import argparse,hashlib,json,re
from pathlib import Path
from prepare_surf_passages import PRIOR,LAYER as PREVIOUS
from audit_battle_database import REFERENCE,move_constants
LAYER='battle-database'
PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
 source=Path(source);marker=source/('.journey-'+LAYER)
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in (r['prepared_sha256']|r['preserved_native_sha256']).items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  assert r['reference_sha256']==hashlib.sha256(REFERENCE.read_bytes()).hexdigest()
  return r
 expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
 for layer in PRIOR:expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 originals={};outputs={};preserved={}
 def read(p):
  raw=(source/p).read_bytes();h=hashlib.sha256(raw).hexdigest();assert h==expected[p],p;preserved[p]=h;return raw.decode()
 def stage(p,text):
  original=read(p);raw=text.encode()
  if original==text:return
  originals[p]=hashlib.sha256(original.encode()).hexdigest();outputs[p]=raw;preserved.pop(p,None)
 read('include/constants/moves.h');names=move_constants(source)
 ref=json.loads(REFERENCE.read_text());tables={}
 for row in ref['species'].values():
  key=row['native_table'];pairs=row['learnset']
  assert key not in tables or tables[key]==pairs,key;tables[key]=pairs
 path='src/data/pokemon/level_up_learnsets/gen_9.h';text=read(path);learnsets=[]
 for symbol,pairs in sorted(tables.items()):
  pattern=re.compile(r'(static const struct LevelUpMove '+re.escape(symbol)+r'\[\] = \{\n)(.*?)(\n\};)',re.S)
  match=pattern.search(text);assert match,symbol
  old=[(int(level),move) for level,move in re.findall(r'LEVEL_UP_MOVE\(\s*(\d+),\s*(MOVE_\w+)\)',match[2])]
  target={(level,names[mid]) for level,mid in pairs}
  if set(old)==target:continue
  # Keep cartridge ordering at the same level when the official pair exists.
  ordered=sorted(target,key=lambda pair:(pair[0],old.index(pair) if pair in old else len(old)+next(mid for level,mid in pairs if level==pair[0] and names[mid]==pair[1])))
  body=''.join('    LEVEL_UP_MOVE(%2d, %s),\n'%pair for pair in ordered)+'    LEVEL_UP_END'
  text=text[:match.start(2)]+body+text[match.end(2):];learnsets.append(symbol)
 stage(path,text)
 path='src/data/moves_info.h';text=read(path);move_changes=[]
 for mid,row in ref['moves'].items():
  name=names[int(mid)];pattern=re.compile(r'(\['+re.escape(name)+r'\] =\n    \{)(.*?)(\n    \},)',re.S);match=pattern.search(text);assert match,name
  pp=re.search(r'\.pp = (\d+),',match[2])
  # Conditional generational values are checked by the compiled ROM audit.
  if pp is None:continue
  if int(pp[1])==row['pp']:continue
  body=match[2][:pp.start(1)]+str(row['pp'])+match[2][pp.end(1):]
  text=text[:match.start(2)]+body+text[match.end(2):];move_changes.append(dict(move=name,old_pp=int(pp[1]),pp=row['pp']))
 stage(path,text)
 path='src/data/pokemon/species_info/gen_6_families.h';text=read(path)
 for name in ['SLIGGOO_HISUI','GOODRA_HISUI']:
  start=text.index('[SPECIES_'+name+']');end=text.find('[SPECIES_',start+1);end=len(text) if end<0 else end
  body=text[start:end];assert '.types = MON_TYPES(TYPE_DRAGON, TYPE_STEEL)' in body
  text=text[:start]+body.replace('.types = MON_TYPES(TYPE_DRAGON, TYPE_STEEL)','.types = MON_TYPES(TYPE_STEEL, TYPE_DRAGON)',1)+text[end:]
 stage(path,text)
 for path,defines in [('include/config/pokemon.h',['P_LVL_UP_LEARNSETS']),('include/config/battle.h',['B_UPDATED_MOVE_DATA','B_UPDATED_MOVE_TYPES','B_UPDATED_MOVE_FLAGS'])]:
  text=read(path)
  for define in defines:
   text,count=re.subn(r'(#define '+define+r'\s+)GEN_LATEST',r'\g<1>GEN_9',text);assert count==1,define
  stage(path,text)
 for p,raw in outputs.items():(source/p).write_bytes(raw)
 r=dict(layer=LAYER,reference_sha256=hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),reference_commit=ref['provenance']['commit'],learnsets_updated=learnsets,move_pp_changes=move_changes,canonical_species=1025,reference_species_forms=len(ref['species']),reference_moves=len(ref['moves']),custom_cut_strength_types_and_classic_battle_bond_preserved=True,original_sha256=originals,prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()},preserved_native_sha256=preserved)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);a=p.parse_args();r=prepare(a.source);print(len(r['learnsets_updated']),'learnsets updated;',r['move_pp_changes'])
