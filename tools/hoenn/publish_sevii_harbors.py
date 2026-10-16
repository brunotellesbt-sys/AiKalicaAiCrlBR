"""Ship seven terminals with fresh Surf evidence and keep prior port proof intact."""
import argparse,hashlib,json,shutil,zipfile
from pathlib import Path
from package_versions import ROOT,package
from verify_versions import verify
from verify_fuchsia_update import previous_release


def publish(source,validation,output):
    source,validation,output=Path(source),Path(validation),Path(output)
    raw=(validation/'baseline/versions.json').read_bytes();old=json.loads(raw);info=package(source,output)
    info.update(validation_scope='sevii-harbors',sevii_harbors_validated=True,full_campaign_playthrough=False,proofs=[],
        previous_port_validation=dict(manifest=(validation/'baseline/versions.json').relative_to(ROOT).as_posix(),
            manifest_sha256=hashlib.sha256(raw).hexdigest(),retested_on_current_rom=False),
        historical_validation=old['historical_validation'],previous_validation=old['previous_validation'])
    def add(path,target,kind):
        relative=Path('evidence/sevii-harbors')/target.removesuffix('.gba')/(kind+'.json')
        dest=output/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
        info['proofs'].append(dict(file=relative.as_posix(),target=target,kind=kind,sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
    add(validation/'source.json','common','sevii-harbor-source')
    add(validation/'connectivity/coast-connectivity.json','common','coast-connectivity')
    add(validation/'chart/world-route-chart.json','common','world-route-chart')
    for target,folder in [('common','validation')]+[(r['file'],r['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba')) for r in info['variants']]:
        for kind in ['sevii-harbors','sevii-surf-connections','sevii-world-surf']:add(validation/folder/(kind+'.json'),target,kind)
    (output/'versions.json').write_text(json.dumps(info,indent=2)+'\n');verify(output,require_seal=False)
    info['validated']=True;(output/'versions.json').write_text(json.dumps(info,indent=2)+'\n');verify(output)
    archive=output/'Pokemon-Journey-Four-Editions.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for n in [r['file'] for r in info['variants']]+['versions.json','SHA256SUMS','START-HERE.md']:z.write(output/n,n)
        archived=set()
        for manifest in [info,old]:
            while True:
                for p in manifest['proofs']:
                    if p['file'] not in archived:z.write(output/p['file'],p['file']);archived.add(p['file'])
                if 'previous_port_validation' not in manifest:break
                reference=manifest['previous_port_validation']['manifest']
                name='history/'+Path(reference).parent.parent.name+'-versions.json'
                if name not in archived:z.write(ROOT/reference,name);archived.add(name)
                manifest=previous_release(manifest)
        for p in sorted((ROOT/'docs').rglob('*')):
            if p.is_file():z.write(p,'docs/'+p.relative_to(ROOT/'docs').as_posix())
        for p in sorted((validation/'validation').glob('*.png')):z.write(p,p.relative_to(ROOT).as_posix())
    return archive


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--validation',type=Path,default=ROOT/'mods/hoenn/sevii-harbors-validation');p.add_argument('--output',type=Path,default=ROOT/'mods/hoenn/versions');a=p.parse_args();print(publish(a.source,a.validation.resolve(),a.output))
