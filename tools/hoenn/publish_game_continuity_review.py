"""Publish five editions only after current campaign/camera proofs and pinned history pass."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile

from game_continuity_review_contract import HISTORICAL_COMMIT,SCOPE
from package_review_rom import package as package_review
from package_versions import ROOT,package
from publish_badge_story import build_archive,preserve_history
from publish_coastal_closures import copy_current_proof,relative_name,report_dependencies
from publish_generated_world_audit import load_plan
from verify_game_continuity_review_update import (COMMON_KINDS,EDITION_KINDS,OPTIONAL_COMMON_KINDS,
    baseline,require_final_contract,required_keys,verify_elf_binding,verify_proof)
from verify_versions import verify


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_plan(validation,frozen,output):
    validation=Path(validation);frozen=json.loads(Path(frozen).read_bytes())
    expected={frozen['parent_rom_sha256']:'common'}
    for row in frozen['editions']:
        target='test' if row['edition']=='TESTE' else 'Pokemon-Journey-'+row['edition']+'.gba'
        assert row['sha256'] not in expected
        expected[row['sha256']]=target
    selected={}
    for path in sorted(validation.rglob('*.json')):
        report=json.loads(path.read_bytes())
        if not isinstance(report,dict) or report.get('rom_sha256') not in expected or report.get('passed') is not True:
            continue
        target=expected[report['rom_sha256']];kind=report.get('kind',path.stem)
        if target=='common':
            if kind not in COMMON_KINDS|OPTIONAL_COMMON_KINDS:continue
        elif kind not in EDITION_KINDS:continue
        key=target,kind
        assert key not in selected,('Ambiguous current proof',key,selected.get(key),path)
        selected[key]=dict(target=target,kind=kind,file=path.relative_to(validation).as_posix())
    info=dict(variants=[dict(file=t) for t in expected.values() if t not in {'common','test'}])
    assert required_keys(info)<=selected.keys(),('Current native runs incomplete',sorted(required_keys(info)-selected.keys()))
    result=dict(proofs=[selected[key] for key in sorted(selected)])
    Path(output).write_text(json.dumps(result,indent=2)+'\n')
    return result


def prevalidate(source,validation,plan,save=None):
    require_final_contract()
    source,validation,plan=(Path(path).resolve() for path in (source,validation,plan))
    save=(Path(save) if save is not None else validation/'test-save/Pokemon-Journey-TESTE.sav').resolve()
    assert save.is_file() and save.stat().st_size==131072, 'The tested staged review save is required'
    save_sha=digest(save)
    old=baseline('versions.json',(validation/'baseline/versions.json').read_bytes())
    baseline('review.json',(validation/'baseline/review.json').read_bytes())
    baseline('test.sav',(validation/'baseline/test.sav').read_bytes())
    previous_review=json.loads((validation/'baseline/review.json').read_bytes())
    from verify_arrival_coast_review_update import verify_update as verify_previous
    verify_previous(ROOT/'mods/hoenn/versions',old,historical_review=previous_review,
                    historical_save=validation/'baseline/test.sav')
    rows=load_plan(plan,validation)
    with tempfile.TemporaryDirectory(prefix='game-continuity-publish-',dir='/tmp') as temporary:
        scratch=Path(temporary);info=package(source,scratch)
        test=package_review(source,scratch/'Pokemon-Journey-Gen1-9-Normal.gba',scratch/'test')
        expected={'common':info['parent_rom_sha256'],'test':test['sha256'],
                  **{r['file']:r['sha256'] for r in info['variants']}}
        required=required_keys(info);observed={(r['target'],r['kind']) for r in rows}
        assert required<=observed,('Missing current proof',sorted(required-observed))
        assert observed-required<={('common',k) for k in OPTIONAL_COMMON_KINDS}
        reports=[]
        for row in rows:
            file=row['path']
            # Exercise the actual recursive export before replacing public
            # bytes. Checking only the original folder can miss attachments
            # that a strict child verifier needs but the copier omitted.
            copied=scratch/'proof-export'/row['target']/row['kind']/'proof.json'
            copy_current_proof(file,copied)
            assert copied.read_bytes()==file.read_bytes()
            report=json.loads(copied.read_bytes())
            assert report['rom_sha256']==expected[row['target']],('Stale current proof',row)
            reports.append((row['kind'],report))
            verify_proof(report,copied.parent,row['kind'],row['target'],
                         save,info,old)
        verify_elf_binding(reports)
    assert digest(save)==save_sha, 'Staged review save changed during preflight'
    return old,rows,save_sha


def publish(source,validation,output,plan,save=None):
    source,validation,output,plan=(Path(path).resolve() for path in (source,validation,output,plan))
    save=(Path(save) if save is not None else validation/'test-save/Pokemon-Journey-TESTE.sav').resolve()
    extras=[ROOT/'docs/design/game-continuity-review',ROOT/'docs/game-continuity-review.md',ROOT/'errors']
    assert all(path.exists() for path in extras), 'Complete review documentation before replacing public ROMs'
    old,rows,save_sha=prevalidate(source,validation,plan,save)
    tested_save=save.read_bytes()
    assert hashlib.sha256(tested_save).hexdigest()==save_sha, 'Staged review save changed after preflight'
    before=validation/'baseline';old_raw=(before/'versions.json').read_bytes()
    old_review=json.loads((before/'review.json').read_bytes())
    # Resolve and validate manifest references before replacing public bytes.
    # Relative CLI paths are supported; published references remain repo-relative.
    relative_baseline=before.relative_to(ROOT)
    def reference(name):
        path=before/name;return dict(file=(relative_baseline/name).as_posix(),sha256=digest(path))
    previous_review=reference('review.json');previous_save=reference('test.sav')
    preserve_history(old,output);info=package(source,output)
    package_review(source,output/'Pokemon-Journey-Gen1-9-Normal.gba',ROOT/'roms/rom-de-teste')
    assert save.read_bytes()==tested_save, 'Staged review save changed during publication'
    destination=ROOT/'roms/rom-de-teste/Pokemon-Journey-TESTE.sav'
    destination.write_bytes(tested_save)
    info.update(validation_scope=SCOPE,validated=False,full_campaign_playthrough=False,proofs=[],
        historical_validation=old['historical_validation'],previous_validation=old['previous_validation'],
        previous_port_validation=dict(manifest=(relative_baseline/'versions.json').as_posix(),
            manifest_sha256=hashlib.sha256(old_raw).hexdigest(),retested_on_current_rom=False),
        previous_review_validation=previous_review,previous_review_save_validation=previous_save,
        previous_features_retested_on_current_rom=False,
        historical_release=dict(scope=old['validation_scope'],parent_rom_sha256=old['parent_rom_sha256'],
            variants={r['file']:r['sha256'] for r in old['variants']},test_rom_sha256=old_review['sha256'],
            proof_count=len(old['proofs']),retested_on_current_rom=False))
    for row in rows:
        relative=Path('evidence')/SCOPE/row['target'].removesuffix('.gba')/row['kind']/(row['kind']+'.json')
        sha=copy_current_proof(row['path'],output/relative)
        info['proofs'].append(dict(file=relative.as_posix(),target=row['target'],kind=row['kind'],sha256=sha))
    manifest=output/'versions.json';manifest.write_text(json.dumps(info,indent=2)+'\n')
    verify(output,require_seal=False);info['validated']=True
    manifest.write_text(json.dumps(info,indent=2)+'\n');verify(output)
    build_archive(info,output,current_scope=SCOPE,historical_commit=HISTORICAL_COMMIT,extra_paths=extras)
    return info


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--validation',type=Path,default=ROOT/'mods/hoenn/game-continuity-review-validation')
    parser.add_argument('--plan',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'mods/hoenn/versions')
    parser.add_argument('--frozen',type=Path,default=ROOT/'.local/game-continuity-review-frozen.json')
    parser.add_argument('--save',type=Path,help='Tested staged TESTE battery save')
    parser.add_argument('--write-plan',action='store_true')
    parser.add_argument('--preflight',action='store_true')
    args=parser.parse_args();plan=args.plan or args.validation/'proof-plan.json'
    if args.write_plan:print('Explicit current reports:',len(write_plan(args.validation,args.frozen,plan)['proofs']))
    elif args.preflight:print('All current proofs passed; public ROMs unchanged:',len(prevalidate(args.source,args.validation,plan,args.save)[1]))
    else:publish(args.source,args.validation,args.output,plan,args.save)
