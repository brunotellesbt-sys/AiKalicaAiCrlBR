"""Ship four Fuchsia editions with focused current proof and unchanged history."""
import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from package_versions import ROOT,package
from verify_versions import verify


def publish(source,validation,output):
    source,validation,output=Path(source),Path(validation),Path(output)
    original=(validation/'baseline/versions.json').read_bytes()
    previous=json.loads(original)
    info=package(source,output)
    info.update(validation_scope='fuchsia-harbor',fuchsia_harbor_validated=True,
                full_campaign_playthrough=False,proofs=[],
                previous_port_validation=dict(manifest=(validation/'baseline/versions.json').relative_to(ROOT).as_posix(),
                    manifest_sha256=hashlib.sha256(original).hexdigest(),retested_on_current_rom=False))
    info['historical_validation']=previous['historical_validation']
    info['previous_validation']=previous['previous_validation']
    def add(path,target,kind):
        relative=Path('evidence/fuchsia-harbor')/target.removesuffix('.gba')/(kind+'.json')
        dest=output/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
        info['proofs'].append(dict(file=relative.as_posix(),target=target,kind=kind,sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
    add(validation/'source.json','common','fuchsia-source')
    add(validation/'validation/fuchsia-harbor.json','common','fuchsia-harbor')
    for row in info['variants']:
        name=row['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba')
        add(validation/name/'fuchsia-harbor.json',row['file'],'fuchsia-harbor')
    (output/'versions.json').write_text(json.dumps(info,indent=2)+'\n')
    verify(output,require_seal=False)
    info['validated']=True
    (output/'versions.json').write_text(json.dumps(info,indent=2)+'\n');verify(output)
    archive=output/'Pokemon-Journey-Four-Editions.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for n in [r['file'] for r in info['variants']]+['versions.json','SHA256SUMS','START-HERE.md']:
            z.write(output/n,n)
        for proof in info['proofs']:z.write(output/proof['file'],proof['file'])
        # The previous manifest and each original report retain their hashes.
        z.write(validation/'baseline/versions.json','history/pre-fuchsia-versions.json')
        for proof in previous['proofs']:
            z.write(output/proof['file'],proof['file'])
        for p in sorted((ROOT/'docs').rglob('*')):
            if p.is_file():z.write(p,'docs/'+p.relative_to(ROOT/'docs').as_posix())
        for p in sorted((validation/'validation').glob('*.png')):
            z.write(p,p.relative_to(ROOT).as_posix())
    return archive


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--validation',type=Path,default=ROOT/'mods/hoenn/fuchsia-harbor-validation');p.add_argument('--output',type=Path,default=ROOT/'mods/hoenn/versions')
    a=p.parse_args();print(publish(a.source,a.validation.resolve(),a.output))
