"""Read compiled species records, evolution links and sprites from the pinned candidate."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[2]

def audit(source):
 source=Path(source);rom=(source/'pokeemerald.gba').read_bytes()
 declarations=['sizeof(struct SpeciesInfo)','offsetof(struct SpeciesInfo, frontPic)','offsetof(struct SpeciesInfo, backPic)',
 'offsetof(struct SpeciesInfo, palette)','offsetof(struct SpeciesInfo, shinyPalette)','offsetof(struct SpeciesInfo, iconSprite)',
 'offsetof(struct SpeciesInfo, types)','offsetof(struct SpeciesInfo, catchRate)','offsetof(struct SpeciesInfo, enemyShadowXOffset) - 4',
 'offsetof(struct SpeciesInfo, evolutions)','sizeof(struct Evolution)','offsetof(struct Evolution, targetSpecies)',
 'offsetof(struct SpeciesInfo, speciesName)','NUM_SPECIES','offsetof(struct SpeciesInfo, height) - 2']
 with tempfile.TemporaryDirectory(prefix='catalog-abi-',dir='/tmp') as d:
  d=Path(d);p=d/'abi.c';p.write_text('#include "global.h"\n#include "pokemon.h"\n#include <stddef.h>\nconst unsigned fields[] = {'+', '.join(declarations)+'};\n')
  subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-iquote',str(source/'include'),'-DMODERN=1','-DPOKEEMERALD','-mthumb','-march=armv4t','-mabi=apcs-gnu',str(p),'-o',str(d/'abi.s')],check=True)
  abi=[int(n) for n in re.findall(r'\.word\s+(\d+)',(d/'abi.s').read_text())]
 symbols=subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),'--defined-only',str(source/'pokeemerald.elf')],text=True)
 address=int(re.search(r'^([0-9a-f]+) . gSpeciesInfo$',symbols,re.M)[1],16)-0x08000000
 def ptr(record,offset):return struct.unpack_from('<I',rom,record+offset)[0]-0x08000000
 def decompress(offset):
  assert 0<=offset<len(rom),offset
  if rom[offset]!=0x10:return None
  size=int.from_bytes(rom[offset+1:offset+4],'little');out=bytearray();p=offset+4
  assert size<=65536,size
  while len(out)<size:
   flags=rom[p];p+=1
   for bit in range(8):
    if len(out)>=size:break
    if flags&(0x80>>bit):
     pair=(rom[p]<<8)|rom[p+1];p+=2;length=(pair>>12)+3;distance=(pair&4095)+1
     assert distance<=len(out)
     for _ in range(length):out.append(out[-distance])
    else:out.append(rom[p]);p+=1
  return bytes(out[:size])
 names={int(v):n for n,v in re.findall(r'\b(SPECIES_\w+)\s*=\s*(\d+)',(source/'include/constants/species.h').read_text())}
 rows={};missing=[]
 for species in range(1,abi[13]):
  at=address+species*abi[0]
  if not rom[at]:continue
  flags=struct.unpack_from('<I',rom,at+abi[8])[0]
  targets=[];evo=ptr(at,abi[9])
  if evo>=0:
   for i in range(64):
    method=struct.unpack_from('<H',rom,evo+i*abi[10])[0]
    if method == 0xFFFF:break
    targets.append(struct.unpack_from('<H',rom,evo+i*abi[10]+abi[11])[0])
  dex=struct.unpack_from('<H',rom,at+abi[14])[0]
  row=dict(id=species,national_dex=dex,name=names.get(species,str(species)),stats=list(rom[at:at+6]),types=list(rom[at+abi[6]:at+abi[6]+2]),
   catch_rate=rom[at+abi[7]],flags=flags,special=bool(flags&15),legendary=bool(flags&3),mythical=bool(flags&4),ultra_beast=bool(flags&8),
   regional=bool(flags&((1<<11)|(1<<12)|(1<<13)|(1<<14))),evolutions=sorted(set(targets)))
  if 1 <= dex <= 1025:
   sprite_info={}
   for label,index,minimum in [('front',1,2048),('back',2,2048),('palette',3,32),('shiny_palette',4,32)]:
    try:
     offset=ptr(at,abi[index]);assert 0<=offset<len(rom)-32
     if label in ['palette','shiny_palette']:
      data=rom[offset:offset+32];assert any(data)
      sprite_info[label]=dict(bytes=32,sha256=hashlib.sha256(data).hexdigest(),format='raw')
     elif rom[offset]==0x10:
      data=decompress(offset);assert len(data)>=minimum
      sprite_info[label]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),format='lz77')
     else:
      header=struct.unpack_from('<I',rom,offset)[0];mode=header&15;size=((header>>4)&16383)*4
      assert 0<mode<15 and minimum<=size<=16384,(mode,size)
      sprite_info[label]=dict(bytes=size,header_sha256=hashlib.sha256(rom[offset:offset+8]).hexdigest(),format='smol',decompression_validated=False)
    except (AssertionError,IndexError,struct.error):missing.append(dict(id=species,name=row['name'],asset=label))
   icon=ptr(at,abi[5])
   if not 0<=icon<len(rom)-512:missing.append(dict(id=species,name=row['name'],asset='icon'))
   row['assets']=sprite_info
  rows[species]=row
 canonical={}
 for i,r in rows.items():
  if 1<=r['national_dex']<=1025:canonical.setdefault(r['national_dex'],i)
 absent=[i for i in range(1,1026) if i not in canonical]
 missing=[m for m in missing if m['id'] in canonical.values()]
 return dict(source_commit=json.loads((source/'.source-acquired.json').read_text())['commit'],
  rom_sha256=hashlib.sha256(rom).hexdigest(),base_species_count=len(canonical),canonical_species=canonical,disabled_base_species=absent,
  missing_assets=missing,compiled_abi=abi,species={str(i):r for i,r in rows.items()},
  special_species=[i for i,r in rows.items() if i in canonical.values() and r['special']],passed=not absent and not missing)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
 p.add_argument('--output',type=Path,default=ROOT/'mods/hoenn/integration-validation/native-catalog.json')
 p.add_argument('--summary',action='store_true',help='Omit detailed species rows, retaining their deterministic digest')
 a=p.parse_args();r=audit(a.source)
 if a.summary:
  rows=r.pop('species')
  r['species_rows_sha256']=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  r['species_rows_count']=len(rows)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n')
 print('Compiled catalog:',r['base_species_count'],'base species;',len(r['missing_assets']),'missing assets; audit passed:',r['passed'])
