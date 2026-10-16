"""Publish the integrated coasts, ports and atlas with current native evidence."""
import argparse,hashlib,json,shutil,zipfile
from pathlib import Path
from package_versions import ROOT,package
from verify_versions import verify

def publish(source,validation,output,pallet_validation,harbor_validation,chart_validation):
    source,validation,output=Path(source),Path(validation),Path(output)
    pallet_validation,harbor_validation,chart_validation=Path(pallet_validation),Path(harbor_validation),Path(chart_validation)
    original=(validation/'baseline/versions.json').read_bytes();previous=json.loads(original)
    info=package(source,output)
    info.update(validation_scope='sevii-surf-connections',full_campaign_playthrough=False,special_encounters_validated=True,
                pallet_harbor_validated=True,sootopolis_harbor_retested=True,world_route_chart_validated=True,
                compiled_gps_tiles=json.loads((validation/'scope/sevii-source-scope.json').read_text())['compiled_gps_tiles'],
                previous_validation=previous['previous_validation'],historical_validation=previous['historical_validation'],
                previous_sootopolis_validation=dict(manifest=str((validation/'baseline/versions.json').relative_to(ROOT)),manifest_sha256=hashlib.sha256(original).hexdigest(),retested_on_current_rom=False),proofs=[])
    def add(path,target,kind):
        relative=Path('evidence/sevii-surf')/target.removesuffix('.gba')/(kind+'.json');dest=output/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
        info['proofs'].append(dict(file=relative.as_posix(),target=target,kind=kind,sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
    add(validation/'common/sevii-surf-connections.json','common','sevii-surf-connections')
    add(validation/'connectivity/coast-connectivity.json','common','coast-connectivity')
    add(validation/'scope/sevii-source-scope.json','common','sevii-source-scope');add(validation/'reproduction.json','common','reproduction')
    add(pallet_validation/'validation/pallet-harbor.json','common','pallet-harbor')
    add(pallet_validation/'validation/reproduction.json','common','pallet-reproduction')
    add(harbor_validation/'validation/sootopolis-harbor.json','common','sootopolis-harbor')
    add(chart_validation/'world-route-chart.json','common','world-route-chart')
    if 'lavender-harbor' in info['integration_layers']:
        lavender=ROOT/'mods/hoenn/lavender-harbor-validation'
        info['lavender_harbor_validated']=True
        add(lavender/'validation/lavender-harbor.json','common','lavender-harbor')
    for row in info['variants']:
        name=row['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba')
        for kind in ['sevii-surf-connections','special-encounters']:add(validation/name/(kind+'.json'),row['file'],kind)
        add(pallet_validation/name/'pallet-harbor.json',row['file'],'pallet-harbor')
        add(harbor_validation/name/'sootopolis-harbor.json',row['file'],'sootopolis-harbor')
        if info.get('lavender_harbor_validated'):
            add(lavender/name/'lavender-harbor.json',row['file'],'lavender-harbor')
    (output/'versions.json').write_text(json.dumps(info,indent=2)+'\n');verify(output,require_seal=False)
    info['validated']=True;(output/'versions.json').write_text(json.dumps(info,indent=2)+'\n');verify(output)
    archive=output/'Pokemon-Journey-Four-Editions.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for n in [r['file'] for r in info['variants']]+['versions.json','SHA256SUMS','START-HERE.md']:z.write(output/n,n)
        for proof in info['proofs']:z.write(output/proof['file'],proof['file'])
        for p in sorted((ROOT/'docs').rglob('*')):
            if p.is_file():z.write(p,'docs/'+p.relative_to(ROOT/'docs').as_posix())
        for p in sorted((validation/'common').iterdir()):
            if p.suffix in ['.png','.gif']:z.write(p,p.relative_to(ROOT).as_posix())
    return archive

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--validation',type=Path,required=True);p.add_argument('--output',type=Path,default=ROOT/'mods/hoenn/versions');p.add_argument('--pallet-validation',type=Path,required=True);p.add_argument('--harbor-validation',type=Path,required=True);p.add_argument('--chart-validation',type=Path,required=True);a=p.parse_args();print(publish(a.source,a.validation.resolve(),a.output,a.pallet_validation,a.harbor_validation,a.chart_validation))
