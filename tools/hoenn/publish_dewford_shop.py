"""Package the four current editions and their separate inspection derivative."""
import argparse,hashlib,json,shutil,zipfile
from pathlib import Path
from package_versions import ROOT,package
from package_review_rom import package as package_review
from verify_versions import verify


def publish(source,validation,output):
    source,validation,output=map(Path,[source,validation,output])
    raw=(validation/'baseline/versions.json').read_bytes();old=json.loads(raw)
    info=package(source,output)
    package_review(source,output/'Pokemon-Journey-Gen1-9-Normal.gba',ROOT/'roms/rom-de-teste')
    previous_review=validation/'baseline/review.json'
    info.update(validation_scope='dewford-competitive-shop',proofs=[],full_campaign_playthrough=False,
                historical_validation=old['historical_validation'],previous_validation=old['previous_validation'],
                previous_port_validation=dict(manifest=(validation/'baseline/versions.json').relative_to(ROOT).as_posix(),
                    manifest_sha256=hashlib.sha256(raw).hexdigest(),retested_on_current_rom=False),
                previous_review_validation=dict(file=previous_review.relative_to(ROOT).as_posix(),
                    sha256=hashlib.sha256(previous_review.read_bytes()).hexdigest()))
    def add(file,target,kind):
        rel=Path('evidence/dewford-shop')/target.removesuffix('.gba')/(kind+'.json');dest=output/rel
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(file,dest)
        info['proofs'].append(dict(file=rel.as_posix(),target=target,kind=kind,sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
    add(validation/'source.json','common','dewford-shop-source')
    for target,folder in [(r['file'],r['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba')) for r in info['variants']]+[('test','TESTE')]:
        add(validation/folder/'dewford-competitive-shop.json',target,'dewford-competitive-shop')
    (output/'versions.json').write_text(json.dumps(info,indent=2)+'\n');verify(output,require_seal=False)
    info['validated']=True;(output/'versions.json').write_text(json.dumps(info,indent=2)+'\n');verify(output)
    with zipfile.ZipFile(output/'Pokemon-Journey-Four-Editions.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for n in [r['file'] for r in info['variants']]+['versions.json','SHA256SUMS','START-HERE.md']:z.write(output/n,n)
        for p in (output/'evidence').rglob('*.json'):z.write(p,p.relative_to(output).as_posix())
        for p in validation.rglob('*'):
            if p.is_file():z.write(p,p.relative_to(ROOT).as_posix())
        for p in (ROOT/'docs').rglob('*'):
            if p.is_file():z.write(p,p.relative_to(ROOT).as_posix())
        from verify_fuchsia_update import previous_release
        history=info;archived=set(z.namelist())
        while 'previous_port_validation' in history:
            name=history['previous_port_validation']['manifest']
            if name not in archived:z.write(ROOT/name,name);archived.add(name)
            history=previous_release(history)
    return info


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    p.add_argument('--validation',type=Path,default=ROOT/'mods/hoenn/dewford-shop-validation')
    p.add_argument('--output',type=Path,default=ROOT/'mods/hoenn/versions');a=p.parse_args()
    publish(a.source,a.validation.resolve(),a.output)
