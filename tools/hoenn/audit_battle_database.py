"""Compare compiled GBA learnsets, move attributes and types to a pinned Gen 9 reference."""
import argparse, hashlib, json, re, struct, subprocess, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REFERENCE=ROOT/'tools/hoenn/data/scarlet-violet-database.json'
def move_constants(source):
 text=(Path(source)/'include/constants/moves.h').read_text().split('{',1)[1].split('};',1)[0]
 text=re.sub(r'//[^\n]*|/\*.*?\*/','',text,flags=re.S)
 values={};current=-1;names={}
 for name,value in re.findall(r'\b([A-Z][A-Z0-9_]*)\s*(?:=\s*([A-Z][A-Z0-9_]*|\d+))?\s*[,}]',text+'}'):
  current=int(value) if value.isdigit() else values[value] if value else current+1
  values[name]=current
  if name.startswith('MOVE_'):names.setdefault(current,name)
 return names
def compiled(source):
 source=Path(source);rom=(source/'pokeemerald.gba').read_bytes()
 fields=['sizeof(struct SpeciesInfo)','offsetof(struct SpeciesInfo, levelUpLearnset)','offsetof(struct SpeciesInfo, types)','NUM_SPECIES','sizeof(struct LevelUpMove)','offsetof(struct LevelUpMove, level)','sizeof(struct MoveInfo)','offsetof(struct MoveInfo, effect)+sizeof(enum BattleMoveEffects)','offsetof(struct MoveInfo, pp)','MOVES_COUNT_ALL']
 with tempfile.TemporaryDirectory(dir='/tmp',prefix='battle-db-') as d:
  d=Path(d);(d/'abi.c').write_text('#include "global.h"\n#include "pokemon.h"\n#include "move.h"\n#include <stddef.h>\nconst unsigned fields[]={'+','.join(fields)+'};\nconst struct MoveInfo priority_probe={.priority=1};\n')
  subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-iquote',str(source/'include'),'-DMODERN=1','-DPOKEEMERALD','-mthumb','-march=armv4t','-mabi=apcs-gnu',str(d/'abi.c'),'-o',str(d/'abi.s')],check=True)
  abi=[int(n) for n in re.findall(r'\.word\s+(\d+)',(d/'abi.s').read_text())]
  priority_offset=int(re.search(r'priority_probe:\s*\.space\s+(\d+)\s*\.byte\s+1',(d/'abi.s').read_text())[1])
 raw=subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),'--defined-only',str(source/'pokeemerald.elf')],text=True)
 symbols={n:int(a,16)-0x08000000 for a,_,n in re.findall(r'^(\w+) (\w) (\S+)$',raw,re.M)}
 names={int(v):n for n,v in re.findall(r'\b(SPECIES_\w+)\s*=\s*(\d+)',(source/'include/constants/species.h').read_text())}
 learnset_symbols={at:name for name,at in symbols.items() if re.fullmatch(r's\w+LevelUpLearnset',name)}
 layout=dict(abi=abi,symbols={n:symbols[n] for n in ['gSpeciesInfo','gMovesInfo']},priority_offset=priority_offset)
 return decode_database(rom,layout,names,move_constants(source),learnset_symbols)
def decode_database(rom,layout,names=None,move_names=None,learnset_symbols=None):
 abi=layout['abi'];symbols=layout['symbols'];priority_offset=layout['priority_offset']
 names=names or {};move_names=move_names or {};learnset_symbols=learnset_symbols or {}
 species={};moves={}
 for sid in range(1,abi[3]):
  at=symbols['gSpeciesInfo']+sid*abi[0]
  if not rom[at]:continue
  ptr=struct.unpack_from('<I',rom,at+abi[1])[0]-0x08000000
  learn=[]
  if ptr>=0:
   for i in range(512):
    mid=struct.unpack_from('<H',rom,ptr+i*abi[4])[0]
    if mid==65535:break
    learn.append([struct.unpack_from('<H',rom,ptr+i*abi[4]+abi[5])[0],mid])
   else:raise ValueError(('Unterminated learnset',sid))
  species[sid]=dict(name=names.get(sid),types=list(rom[at+abi[2]:at+abi[2]+2]),learnset=learn,learnset_symbol=learnset_symbols.get(ptr))
 for mid in range(1,abi[9]):
  at=symbols['gMovesInfo']+mid*abi[6];bits=struct.unpack_from('<H',rom,at+abi[7])[0]
  accuracy=rom[at+abi[7]+2]&127;priority=rom[at+priority_offset]&15
  moves[mid]=dict(name=move_names.get(mid),type=bits&31,category=(bits>>5)&3,power=bits>>7,accuracy=accuracy,pp=rom[at+abi[8]],priority=priority-16 if priority>=8 else priority)
 return dict(rom_sha256=hashlib.sha256(rom).hexdigest(),species=species,moves=moves,abi=abi,compiled_layout=layout)
def audit(source,reference=REFERENCE):
 return compare_database(compiled(source),reference)
def compare_database(data,reference=REFERENCE):
 ref=json.loads(Path(reference).read_text());differences=[]
 for sid,wanted in ref['species'].items():
  actual=data['species'][int(sid)]
  for field in ['types','learnset']:
   observed=actual[field]
   if field=='learnset':observed=sorted(set(map(tuple,observed)));expected=sorted(set(map(tuple,wanted[field])))
   else:expected=wanted[field]
   if observed!=expected:differences.append(dict(kind='species',id=int(sid),name=actual['name'],field=field,actual=observed,expected=expected))
 for mid,wanted in ref['moves'].items():
  actual=data['moves'][int(mid)]
  for field in ['type','category','power','accuracy','pp','priority']:
   expected=wanted.get('engine_power',wanted[field]) if field=='power' else wanted[field]
   if actual[field]!=expected:differences.append(dict(kind='move',id=int(mid),name=actual['name'],field=field,actual=actual[field],expected=expected))
 return dict(passed=not differences,rom_sha256=data['rom_sha256'],reference_sha256=hashlib.sha256(Path(reference).read_bytes()).hexdigest(),reference_commit=ref['provenance']['commit'],species_checked=len(ref['species']),moves_checked=len(ref['moves']),fairy_species_checked=sum(19 in r['types'] for r in ref['species'].values()),differences=differences,compiled_layout=data['compiled_layout'],full_campaign_playthrough=False)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 r=audit(a.source);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print('Database audit:',r['species_checked'],'species,',r['moves_checked'],'moves,',len(r['differences']),'differences');raise SystemExit(0 if r['passed'] else 1)
