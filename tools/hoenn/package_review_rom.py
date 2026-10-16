"""Export one exploration ROM, isolated from the four normal editions."""
import argparse,hashlib,json,re,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
NAME='Pokemon-Journey-TESTE.gba'
def package(source,normal,output):
    source,normal,output=map(Path,[source,normal,output]);output.mkdir(parents=True,exist_ok=True)
    base=normal.read_bytes();nm=subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),'-S',str(source/'pokeemerald.elf')],text=True)
    m=re.search(r'^(\w+) (\w+) R gJourneyReviewMode$',nm,re.M);assert m and int(m[2],16)==1
    at=int(m[1],16)-0x8000000;assert base[at]==0
    raw=bytearray(base);raw[at]=1;raw[0xA0:0xAC]=b'JOURNEY TEST';raw[0xAC:0xB0]=b'JRTE';raw[0xBD]=(-sum(raw[0xA0:0xBD])-0x19)&255
    (output/NAME).write_bytes(raw)
    differences=[i for i,(a,b) in enumerate(zip(base,raw)) if a!=b]
    assert all(i==at or 0xA0<=i<0xB0 or i==0xBD for i in differences)
    r=dict(file=NAME,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),base_normal_file=normal.name,base_normal_sha256=hashlib.sha256(base).hexdigest(),review_mode_offset=at,patched_byte_offsets=differences,base_header_hex=base[0xA0:0xBE].hex(),automatic_trainer_approaches=False,random_wild_encounters=False,fishing_encounters=False,manual_trainer_and_legendary_interactions_preserved=True,separate_save_identity=True)
    (output/'review.json').write_text(json.dumps(r,indent=2)+'\n');(output/'SHA256SUMS').write_text(r['sha256']+'  '+NAME+'\n');return r

def verify(directory,normal):
    directory,normal=Path(directory),Path(normal);r=json.loads((directory/'review.json').read_text());raw=(directory/r['file']).read_bytes();base=normal.read_bytes();at=r['review_mode_offset']
    assert len(raw)==r['bytes']==33554432 and hashlib.sha256(raw).hexdigest()==r['sha256']
    assert hashlib.sha256(base).hexdigest()==r['base_normal_sha256'] and raw[at]==1 and base[at]==0
    restored=bytearray(raw);restored[at]=0;restored[0xA0:0xBE]=bytes.fromhex(r['base_header_hex']);assert restored==base
    assert raw[0xBD]==(-sum(raw[0xA0:0xBD])-0x19)&255
    return r
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--normal',type=Path,required=True);p.add_argument('--output',type=Path,default=ROOT/'roms/rom-de-teste');a=p.parse_args();print(json.dumps(package(a.source,a.normal,a.output),indent=2));verify(a.output,a.normal)
