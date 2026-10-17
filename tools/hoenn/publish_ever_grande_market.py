"""Package the town update and exact current native proofs for all five ROMs."""
import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from package_versions import ROOT,package
from verify_versions import verify
from verify_fuchsia_update import previous_release

def publish(source,validation,output):
    source,validation,output=map(Path,[source,validation,output])
    raw=(validation/'baseline/versions.json').read_bytes();old=json.loads(raw)
    info=package(source,output)
    info.update(validation_scope='ever-grande-market',validated=False,full_campaign_playthrough=False,proofs=[],
        historical_validation=old['historical_validation'],previous_validation=old['previous_validation'],
        previous_port_validation=dict(manifest=(validation/'baseline/versions.json').relative_to(ROOT).as_posix(),manifest_sha256=hashlib.sha256(raw).hexdigest(),retested_on_current_rom=False),
        previous_review_validation=dict(file=(validation/'baseline/review.json').relative_to(ROOT).as_posix(),sha256=hashlib.sha256((validation/'baseline/review.json').read_bytes()).hexdigest()))
    def add(file,target,kind):
        rel=Path('evidence/ever-grande-market')/target.removesuffix('.gba')/(kind+'.json')
        dest=output/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(file,dest)
        info['proofs'].append(dict(file=rel.as_posix(),target=target,kind=kind,sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
    add(validation/'source.json','common','ever-grande-source')
    add(validation/'native/ever-grande-market.json','common','ever-grande-market')
    add(validation/'river-native/fallarbor-physics.json','common','fallarbor-physics')
    for target,folder in [(r['file'],r['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba')) for r in info['variants']]+[('test','TESTE')]:
        for k in ['ever-grande-market','dewford-competitive-shop','review-mode','fallarbor-physics']:add(validation/folder/(k+'.json'),target,k)
    add(validation/'river/fallarbor-river.json','Pokemon-Journey-Gen1-9-Normal.gba','fallarbor-river')
    (output/'versions.json').write_text(json.dumps(info,indent=2)+'\n');verify(output,require_seal=False)
    info['validated']=True;(output/'versions.json').write_text(json.dumps(info,indent=2)+'\n');verify(output)
    with zipfile.ZipFile(output/'Pokemon-Journey-Four-Editions.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for n in [r['file'] for r in info['variants']]+['versions.json','SHA256SUMS','START-HERE.md']:z.write(output/n,n)
        for p in (output/'evidence').rglob('*.json'):z.write(p,p.relative_to(output).as_posix())
        for p in validation.rglob('*'):
            if p.is_file() and p.suffix in ['.json','.png']:z.write(p,p.relative_to(ROOT).as_posix())
        for p in (ROOT/'docs').rglob('*'):
            if p.is_file():z.write(p,p.relative_to(ROOT).as_posix())
        for folder in [ROOT/'mods/hoenn/surf-review-validation/native']:
            for p in folder.glob('*.png'):z.write(p,p.relative_to(ROOT).as_posix())
        archived=set(z.namelist());history=old
        while 'previous_port_validation' in history:
            n=history['previous_port_validation']['manifest']
            if n not in archived:z.write(ROOT/n,n);archived.add(n)
            history=previous_release(history)
    assert (output/'Pokemon-Journey-Four-Editions.zip').stat().st_size<100*1024*1024
    return info

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--validation',type=Path,default=ROOT/'mods/hoenn/ever-grande-market-validation');p.add_argument('--output',type=Path,default=ROOT/'mods/hoenn/versions')
    a=p.parse_args();publish(Path(a.source),a.validation,a.output)
