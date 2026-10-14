"""Keep earlier native evidence bound to the exact ROM bytes it tested.

A map-only release does not imply a new full tournament/mechanics playthrough.
The compressed parent and immutable variant patch rules preserve that baseline.
"""
import functools,gzip,hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CURRENT=ROOT/'mods/hoenn/versions'
def sha(raw):return hashlib.sha256(raw).hexdigest()
@functools.lru_cache(None)
def baseline():
 directory=ROOT/'mods/hoenn/validation-baselines/pr79'
 release=json.loads((directory/'versions.json').read_text());raw=gzip.decompress((directory/'parent.gba.gz').read_bytes());assert sha(raw)==release['parent_rom_sha256']
 return directory,release,raw

def evidence_release(kind):
 release=json.loads((CURRENT/'versions.json').read_text())
 if any(p['kind']==kind for p in release['proofs']):return CURRENT,release
 directory,old,_=baseline();reference=release['historical_validation'];assert reference['manifest']==str((directory/'versions.json').relative_to(ROOT));assert reference['manifest_sha256']==sha((directory/'versions.json').read_bytes());assert reference['parent_rom_sha256']==old['parent_rom_sha256'];assert reference['retested_on_current_rom'] is False
 assert any(p['kind']==kind for p in old['proofs']),kind
 return directory,old
@functools.lru_cache(None)
def evidence_rom(directory,name):
 directory=Path(directory)
 if directory==CURRENT:return (ROOT/'roms'/name).read_bytes()
 root,release,parent=baseline();assert directory==root
 row=next(r for r in release['variants'] if r['file']==name);raw=bytearray(parent);at=release['build_rules_offset'];raw[at:at+4]=struct.pack('<HBB',row['max_national'],row['perfect_trainer_ivs'],0);generation=4 if row['max_national']==493 else 9;difficulty='H' if row['perfect_trainer_ivs'] else 'N';raw[0xA0:0xAC]=f'JOURNEY G{generation} {difficulty}'.encode().ljust(12,b' ');raw[0xBD]=(-sum(raw[0xA0:0xBD])-0x19)&255;assert sha(raw)==row['sha256'];return bytes(raw)
