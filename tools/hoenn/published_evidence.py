"""Keep earlier native evidence bound to the exact ROM bytes it tested.

A map-only release does not imply a new full tournament/mechanics playthrough.
The compressed parent and immutable variant patch rules preserve that baseline.
"""
import functools,gzip,hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CURRENT=ROOT/'mods/hoenn/versions'
def sha(raw):return hashlib.sha256(raw).hexdigest()


def pinned_release(reference):
 """Read a historical manifest without assigning its evidence to the caller."""
 path=Path(reference['manifest'])
 assert not path.is_absolute() and '..' not in path.parts,'Unsafe historical manifest path'
 resolved=(ROOT/path).resolve()
 assert resolved.is_relative_to(ROOT.resolve()),'Historical manifest escapes repository'
 raw=resolved.read_bytes()
 assert sha(raw)==reference['manifest_sha256'],'Historical manifest hash mismatch'
 assert reference['retested_on_current_rom'] is False,'Historical evidence cannot be relabeled as retested'
 release=json.loads(raw)
 if 'parent_rom_sha256' in reference:
  assert reference['parent_rom_sha256']==release['parent_rom_sha256'],'Historical parent mismatch'
 return resolved.parent,release


def resolve_previous_release(info):
 """Follow one authenticated layer edge; strict prefixes also reject cycles."""
 _,previous=pinned_release(info['previous_port_validation'])
 assert previous['validated'] is True,'Historical baseline is not validated'
 layers,prior=info['integration_layers'],previous['integration_layers']
 assert len(prior)<len(layers) and layers[:len(prior)]==prior,'Historical layers are not a strict prefix'
 return previous


def release_baseline(info):
 """Start historical reads at the pinned 171 when current bytes are candidate 172.

 The candidate keeps its empty proof list and unvalidated flags. Returning the
 separate manifest lets readers inspect old reports without certifying 172.
 """
 if info.get('validation_scope')=='atlas-surf-layout':
  assert info['candidate'] is False and info['validated'] is True
  assert info['final_release_validated'] is True and info['proofs']
  previous=resolve_previous_release(info)
  assert previous['validation_scope']=='generated-area-review'
  assert previous['integration_layers']==info['integration_layers'][:-1]
  return previous
 if info.get('validation_scope')!='atlas-surf-layout-candidate':return info
 assert info['candidate'] is True and info['validated'] is False
 assert info['final_release_validated'] is False and info['proofs']==[]
 assert info['integration_layers'][-1]=='atlas-surf-layout'
 previous=resolve_previous_release(info)
 assert previous['validation_scope']=='generated-area-review'
 assert previous['integration_layers']==info['integration_layers'][:-1]
 assert previous['parent_rom_sha256']!=info['parent_rom_sha256']
 return previous


@functools.lru_cache(None)
def baseline():
 directory=ROOT/'mods/hoenn/validation-baselines/pr79'
 release=json.loads((directory/'versions.json').read_text());raw=gzip.decompress((directory/'parent.gba.gz').read_bytes());assert sha(raw)==release['parent_rom_sha256']
 return directory,release,raw

def evidence_release(kind):
 release=json.loads((CURRENT/'versions.json').read_text())
 owner=release_baseline(release)
 if owner is release and any(p['kind']==kind for p in release['proofs']):return CURRENT,release
 # A copied 171 manifest does not provide its old ROM bytes. Its explicitly
 # archived PR79 remains the owner of mechanics/cup evidence, as before.
 reference=owner['historical_validation']
 directory,old=pinned_release(reference)
 root,archived,_=baseline();assert directory==root.resolve() and old==archived
 assert old['validated'] is True and reference['parent_rom_sha256']==old['parent_rom_sha256']
 assert sha((directory/'parent.gba.gz').read_bytes())==reference['compressed_parent_sha256']
 assert any(p['kind']==kind for p in old['proofs']),kind
 return directory,old
@functools.lru_cache(None)
def evidence_rom(directory,name):
 directory=Path(directory)
 if directory==CURRENT:return (ROOT/'roms'/name).read_bytes()
 root,release,parent=baseline();assert directory==root
 row=next(r for r in release['variants'] if r['file']==name);raw=bytearray(parent);at=release['build_rules_offset'];raw[at:at+4]=struct.pack('<HBB',row['max_national'],row['perfect_trainer_ivs'],0);generation=4 if row['max_national']==493 else 9;difficulty='H' if row['perfect_trainer_ivs'] else 'N';raw[0xA0:0xAC]=f'JOURNEY G{generation} {difficulty}'.encode().ljust(12,b' ');raw[0xBD]=(-sum(raw[0xA0:0xBD])-0x19)&255;assert sha(raw)==row['sha256'];return bytes(raw)
