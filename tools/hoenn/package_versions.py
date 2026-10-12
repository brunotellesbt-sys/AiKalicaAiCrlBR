"""Export four variants by patching only a verified, compiled build-rules record."""
import argparse,hashlib,json,re,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def package(source,output):
 source=Path(source);output=Path(output);output.mkdir(parents=True,exist_ok=True);base=(source/'pokeemerald.gba').read_bytes()
 nm=subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),'-S',str(source/'pokeemerald.elf')],text=True)
 m=re.search(r'^(\w+) (\w+) R gJourneyBuildRules$',nm,re.M);assert m,'Build rules must be a separate ROM record'
 at,size=int(m[1],16)-0x08000000,int(m[2],16);assert size==4 and base[at:at+4]==struct.pack('<HBB',1025,1,0)
 rows=[]
 for generation,maxdex in [(4,493),(9,1025)]:
  for difficulty,perfect in [('Normal',0),('Hard',1)]:
   raw=bytearray(base);raw[at:at+4]=struct.pack('<HBB',maxdex,perfect,0)
   title=f'JOURNEY G{generation} {difficulty[0]}'.encode().ljust(12,b' ')[:12];raw[0xA0:0xAC]=title;raw[0xBD]=(-sum(raw[0xA0:0xBD])-0x19)&255
   name=f'Pokemon-Journey-Gen1-{generation}-{difficulty}.gba';(output/name).write_bytes(raw)
   changes=[i for i,(a,b) in enumerate(zip(base,raw)) if a!=b];assert all(at<=i<at+4 or 0xA0<=i<0xAC or i==0xBD for i in changes)
   rows.append(dict(file=name,max_national=maxdex,perfect_trainer_ivs=bool(perfect),important_opponents_only=True,evs=510,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),patched_byte_offsets=changes,requires_new_save=True))
 r=dict(parent_rom_sha256=hashlib.sha256(base).hexdigest(),build_rules_offset=at,variants=rows,all_other_bytes_identical=True,validated=False)
 (output/'versions.json').write_text(json.dumps(r,indent=2)+'\n');(output/'SHA256SUMS').write_text(''.join(row['sha256']+'  '+row['file']+'\n' for row in rows));return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(package(a.source,a.output),indent=2))
