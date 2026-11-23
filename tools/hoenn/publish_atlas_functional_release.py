"""Install only preflighted immutable editions, replacing shared inodes safely."""
import argparse
import os
from pathlib import Path
import shutil

from verify_atlas_functional_release import ROOT,CONTRACT,load,sha,verify_update
from verify_versions import verify


def atomic_bytes(path,raw):
    path=Path(path);pending=path.with_name(path.name+'.atlas-tmp')
    pending.write_bytes(raw);pending.replace(path)


def publish(artifacts,preflight):
    artifacts,preflight=(Path(p).resolve() for p in (artifacts,preflight))
    info=load(preflight/'versions.json');draft=preflight/'final-contract.json'
    result=verify_update(artifacts,info,contract_path=draft,review_directory=artifacts/'test')
    assert result['passed']
    old=load(ROOT/'mods/hoenn/versions/versions.json')
    assert old['validation_scope']=='atlas-surf-layout-candidate' or (
        old['validation_scope']==info['validation_scope']
        and old['parent_rom_sha256']==info['parent_rom_sha256'])
    assert info['functional_contract_sha256']==sha(draft)
    for row in info['variants']:
        name=row['file'];source=artifacts/name;assert sha(source)==row['sha256']
        destination=ROOT/'mods/hoenn/versions'/name
        pending=destination.with_name(name+'.atlas-tmp');shutil.copyfile(source,pending)
        assert sha(pending)==row['sha256'];pending.chmod(0o444);pending.replace(destination)
        download=ROOT/'roms'/name;pending_download=download.with_name(name+'.atlas-tmp')
        os.link(destination,pending_download);pending_download.replace(download)
    review_dir=ROOT/'roms/rom-de-teste'
    for name in ('Pokemon-Journey-TESTE.gba','Pokemon-Journey-TESTE.sav','review.json','SHA256SUMS'):
        atomic_bytes(review_dir/name,(artifacts/'test'/name).read_bytes())
    sums=(artifacts/'SHA256SUMS').read_bytes()
    for path in (ROOT/'roms/SHA256SUMS',ROOT/'mods/hoenn/versions/SHA256SUMS'):atomic_bytes(path,sums)
    atomic_bytes(CONTRACT,draft.read_bytes())
    # The manifest is installed last, after all current bytes and the tested
    # TESTE battery are in place. No individual proof is relabeled or edited.
    atomic_bytes(ROOT/'mods/hoenn/versions/versions.json',(preflight/'versions.json').read_bytes())
    verify(ROOT/'mods/hoenn/versions')
    print('Published verified current source and five editions:',info['parent_rom_sha256'])
    return info


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--preflight',type=Path,required=True)
    a=p.parse_args();publish(a.artifacts,a.preflight)
