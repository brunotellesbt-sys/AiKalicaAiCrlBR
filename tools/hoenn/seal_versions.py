"""Package validated variants without relabeling evidence from older ROMs."""
import argparse,hashlib,json,shutil,zipfile
from pathlib import Path
from package_versions import package
from verify_versions import verify,ROOT

def seal(source,validation,output,validation_scope='full'):
    validation=Path(validation);output=Path(output)
    info=package(source,output);proofs=[]
    partial=validation_scope in ('pwt-update','pwt-and-special-encounters')
    assert validation_scope in ('full','pwt-update','pwt-and-special-encounters')
    if partial:
        assert 'integration_layers' in info
        info['validation_scope']=validation_scope
        info['full_campaign_playthrough']=False
    # This directory contains only generated evidence from this packager.
    # Replacing it prevents unreferenced earlier-ROM reports from shipping.
    if (output/'evidence').exists():shutil.rmtree(output/'evidence')
    def add(path,target,kind):
        relative=Path('evidence')/target.removesuffix('.gba')/(kind+'.json')
        if target=='common':relative=Path('evidence/common')/path.parent.name/(kind+'.json')
        destination=output/relative;destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,destination)
        proofs.append(dict(file=relative.as_posix(),target=target,kind=kind,sha256=hashlib.sha256(destination.read_bytes()).hexdigest()))
    for row in info['variants']:
        view=row['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba')
        kinds=[] if partial else ['gym-teams','variant-rules']
        if partial and (validation/view/'gym-teams.json').exists():kinds.append('gym-teams')
        if validation_scope=='pwt-and-special-encounters':
            info['special_encounters_validated']=True
            kinds.append('special-encounters')
        if 'integration_layers' in info:kinds.append('pwt-world')
        for kind in kinds:add(validation/view/(kind+'.json'),row['file'],kind)
        if (validation/view/'battle-interactions.json').exists():
            info['battle_interactions_validated']=True
            add(validation/view/'battle-interactions.json',row['file'],'battle-interactions')
        completed=sorted((validation/view).glob('pwt-unboosted-*.json'))
        if completed:
            info['pwt_balance_validated']=True
            pools=[]
            for path in completed:
                report=json.loads(path.read_text())
                assert report['passed'] and report['full_cup_participation']
                pools.append(report['pool'])
                add(path,row['file'],path.stem)
            info.setdefault('pwt_balance_tested_pools',{})[row['file']]=sorted(pools)
        if (Path(source)/'.journey-move-history-rules').exists() and row['max_national']==493:
            info['generation_cups_validated']=True
            for generation in range(1,5):
                add(validation/view/f'generation-cup-{generation}.json',row['file'],f'generation-cup-{generation}')
    for path in sorted((validation/'common').rglob('*.json')):
        report=json.loads(path.read_text())
        if report.get('passed') is True:
            if path.stem!='reproduction' and report.get('rom_sha256')!=info['parent_rom_sha256']:
                print('Excluded evidence from an earlier ROM:',path)
                continue
            kind=path.stem
            if kind.endswith('league-completion'):kind='league-'+report['region']
            if path.parent.name.startswith('protagonist-'):kind=path.parent.name
            add(path,'common',kind)
    info['proofs']=proofs
    (output/'versions.json').write_text(json.dumps(info,indent=2)+'\n')
    verify(output,require_seal=False)
    info['validated']=True
    (output/'versions.json').write_text(json.dumps(info,indent=2)+'\n')
    verify(output)
    archive=output/'Pokemon-Journey-Four-Editions.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name in [r['file'] for r in info['variants']]+['versions.json','SHA256SUMS']:
            if (output/name).exists():z.write(output/name,name)
        readme=(output/'START-HERE.md').read_text().replace('../../../docs/','docs/').replace('../INTEGRATION-STATUS.md','docs/VALIDATION.md')
        readme=readme.replace('../../../roms/README.md','https://github.com/brunotellesbt-sys/AiKalicaAiCrlBR/tree/main/roms')
        z.writestr('START-HERE.md',readme)
        for proof in info['proofs']:z.write(output/proof['file'],proof['file'])
        for path in sorted((ROOT/'docs').rglob('*')):
            if not path.is_file():continue
            name='docs/'+path.relative_to(ROOT/'docs').as_posix()
            if path==ROOT/'docs/README.md':
                guide=path.read_text().replace('../roms/README.md','https://github.com/brunotellesbt-sys/AiKalicaAiCrlBR/tree/main/roms')
                guide=guide.replace('[ZIP](../mods/hoenn/versions/Pokemon-Journey-Four-Editions.zip)','[instruções das quatro edições](../START-HERE.md)')
                guide=guide.replace('../mods/hoenn/INTEGRATION-STATUS.md','VALIDATION.md')
                z.writestr(name,guide)
            else:z.write(path,name)
        z.write(ROOT/'mods/hoenn/INTEGRATION-STATUS.md','docs/VALIDATION.md')
    return archive

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--validation',required=True);p.add_argument('--output',required=True)
    p.add_argument('--validation-scope',choices=['full','pwt-update','pwt-and-special-encounters'],default='full')
    a=p.parse_args();print(seal(a.source,a.validation,a.output,a.validation_scope))
