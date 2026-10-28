"""Publish five current ROMs after checking every layer-165 proof and history.

The explicit plan names reports, never invents or relabels evidence. Historical
JSON bytes remain unchanged; their media use pinned parent URLs in the ZIP.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from generated_world_contract import HISTORICAL_COMMIT, SCOPE
from package_review_rom import package as package_review
from package_versions import ROOT, package
from publish_badge_story import build_archive, preserve_history
from publish_coastal_closures import copy_current_proof, relative_name, report_dependencies
from verify_generated_world_update import (COMMON_KINDS, EDITION_KINDS, OPTIONAL_COMMON_KINDS,
                                           baseline, required_keys, verify_proof)
from verify_versions import verify


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def visual_archive_inputs(visual_commit, *, root=ROOT):
    """Keep canonical current images; pin duplicate/reference renders in Git.

    These new source renders did not exist in the merged layer-164 commit and
    must never be mislabeled as its historical native evidence. All native
    proof dependencies remain managed by ``archive_plan`` independently.
    """
    root = Path(root)
    assert re.fullmatch(r'[0-9a-f]{40}', visual_commit or ''), 'A full pinned visual commit is required'
    assert subprocess.check_output(['git', 'cat-file', '-t', visual_commit], cwd=root).strip() == b'commit'
    audit = root/'docs/design/generated-world-audit'
    assert audit.is_dir()
    included, references, whole_images = [], [], []
    for path in sorted(audit.rglob('*')):
        if not path.is_file() or path.name == 'SOURCE-RENDERS.json':
            continue
        relative = path.relative_to(root).as_posix()
        canonical = path.suffix == '.png' and path.parent.name == 'final' and path.name.endswith('-source.png')
        if path.suffix != '.png' or canonical:
            included.append(path)
            if canonical:
                whole_images.append(dict(file=relative, sha256=digest(path)))
            continue
        # Verify the exact bytes at the pinned commit before producing a URL.
        raw = subprocess.check_output(['git', 'show', visual_commit+':'+relative], cwd=root)
        actual = digest(path)
        assert hashlib.sha256(raw).hexdigest() == actual, ('Uncommitted or stale reference render', relative)
        references.append(dict(file=relative, sha256=actual,
            url='https://github.com/brunotellesbt-sys/AiKalicaAiCrlBR/blob/'+visual_commit+'/'+relative))
    assert whole_images, 'Canonical final source images are missing'
    manifest = audit/'SOURCE-RENDERS.json'
    manifest.write_text(json.dumps(dict(
        kind='generated-world-source-render-references', commit=visual_commit,
        source_renders_are_not_native_proofs=True,
        native_proof_attachments_managed_separately=True,
        notes='Canonical final whole-map images, all audit JSON/Markdown and current native proof attachments are included in the ZIP. Duplicate contact sheets and diagnostic/source reference PNGs remain in the repository at this pinned commit; their exact hashes are listed below. This list is separate from historical layer-164 native evidence.',
        included_final_whole_images=whole_images, repository_reference_images=references), indent=2)+'\n')
    included.append(manifest)
    document = root/'docs/generated-world-audit.md'
    if document.exists():
        included.append(document)
    return included


def load_plan(path, validation):
    value = json.loads(Path(path).read_bytes())
    rows = value['proofs'] if isinstance(value, dict) else value
    assert isinstance(rows, list) and rows
    result, seen = [], set()
    for row in rows:
        assert set(row) == {'target', 'kind', 'file'}, row
        key = row['target'], row['kind']
        assert key not in seen, ('Duplicate current proof', key)
        seen.add(key)
        file = Path(validation)/relative_name(row['file'])
        assert file.is_file(), ('Missing planned current proof', row)
        result.append(dict(row, path=file))
    return result


def write_plan(validation, frozen, output):
    """Materialize an explicit plan from complete, correctly identified runs.

    This is selection only. ``prevalidate`` still checks all native contracts
    and rejects a report whose observations do not prove its declared result.
    """
    validation = Path(validation)
    frozen = json.loads(Path(frozen).read_bytes())
    expected = {frozen['parent_rom_sha256']:'common'}
    for row in frozen['editions']:
        target = 'test' if row['edition'] == 'TESTE' else 'Pokemon-Journey-'+row['edition']+'.gba'
        assert row['sha256'] not in expected
        expected[row['sha256']] = target
    selected = {}
    for path in sorted(validation.rglob('*.json')):
        report = json.loads(path.read_bytes())
        if not isinstance(report,dict) or report.get('rom_sha256') not in expected:
            continue
        target = expected[report['rom_sha256']]
        kind = report.get('kind',path.stem)
        if kind == 'generated-shore-animation-source-census':
            if report.get('source_only') is not True:
                continue
        elif report.get('passed') is not True:
            continue
        if target == 'common':
            if kind not in COMMON_KINDS | OPTIONAL_COMMON_KINDS:
                continue
        elif kind not in EDITION_KINDS and (target,kind) != ('test','generated-gym-native-walk'):
            continue
        if kind == 'generated-navigation' and not report.get('native_all_planned_cases_executed'):
            continue
        if kind == 'generated-cave-routes' and not report.get('all_cases_executed'):
            continue
        if kind == 'generated-shore-animation-native-banks' and report.get('native_bank_pairs') != 43:
            continue
        key = target,kind
        assert key not in selected, ('Ambiguous current proof',key,selected.get(key),path)
        selected[key] = dict(target=target,kind=kind,file=path.relative_to(validation).as_posix())
    info = dict(variants=[dict(file=target) for target in expected.values() if target not in {'common','test'}])
    missing = required_keys(info)-selected.keys()
    assert not missing, ('Native runs are not complete',sorted(missing))
    result = dict(proofs=[selected[key] for key in sorted(selected)])
    Path(output).write_text(json.dumps(result,indent=2)+'\n')
    return result


def prevalidate(source, validation, plan):
    source, validation = Path(source), Path(validation)
    old = baseline('versions.json', (validation/'baseline/versions.json').read_bytes())
    review = json.loads((validation/'baseline/review.json').read_bytes())
    baseline('review.json', (validation/'baseline/review.json').read_bytes())
    baseline('test.sav', (validation/'baseline/test.sav').read_bytes())
    from verify_badge_story_update import verify_update as verify_previous
    verify_previous(ROOT/'mods/hoenn/versions', old, historical_review=review,
                    historical_save=validation/'baseline/test.sav')
    rows = load_plan(plan, validation)
    with tempfile.TemporaryDirectory(prefix='generated-world-publish-check-', dir='/tmp') as temporary:
        scratch = Path(temporary)
        info = package(source, scratch)
        test = package_review(source, scratch/'Pokemon-Journey-Gen1-9-Normal.gba', scratch/'test')
        expected = {'common':info['parent_rom_sha256'], 'test':test['sha256'],
                    **{r['file']:r['sha256'] for r in info['variants']}}
        required = required_keys(info)
        observed = {(r['target'],r['kind']) for r in rows}
        assert required <= observed, ('Missing required current proof', sorted(required-observed))
        assert observed-required <= {('common',kind) for kind in OPTIONAL_COMMON_KINDS}
        for row in rows:
            file = row['path']
            report_dependencies(file)
            report = json.loads(file.read_bytes())
            assert report['rom_sha256'] == expected[row['target']], ('Stale proof', row)
            verify_proof(report, file.parent, row['kind'], row['target']=='test',
                         ROOT/'roms/rom-de-teste/Pokemon-Journey-TESTE.sav', info, old)
    return old, rows


def publish(source, validation, output, plan, visual_commit):
    source, validation, output = map(Path, (source,validation,output))
    extras = visual_archive_inputs(visual_commit)
    old, rows = prevalidate(source,validation,plan)
    before = validation/'baseline'
    old_raw = (before/'versions.json').read_bytes()
    old_review = json.loads((before/'review.json').read_bytes())
    preserve_history(old,output)
    info = package(source,output)
    package_review(source,output/'Pokemon-Journey-Gen1-9-Normal.gba',ROOT/'roms/rom-de-teste')
    def reference(name):
        path = before/name
        return dict(file=path.relative_to(ROOT).as_posix(),sha256=digest(path))
    info.update(validation_scope=SCOPE,validated=False,full_campaign_playthrough=False,
        proofs=[],historical_validation=old['historical_validation'],previous_validation=old['previous_validation'],
        previous_port_validation=dict(manifest=(before/'versions.json').relative_to(ROOT).as_posix(),
                                      manifest_sha256=hashlib.sha256(old_raw).hexdigest(),retested_on_current_rom=False),
        previous_review_validation=reference('review.json'),previous_review_save_validation=reference('test.sav'),
        previous_features_retested_on_current_rom=False,
        historical_release=dict(scope=old['validation_scope'],parent_rom_sha256=old['parent_rom_sha256'],
            variants={r['file']:r['sha256'] for r in old['variants']},test_rom_sha256=old_review['sha256'],
            proof_count=len(old['proofs']),retested_on_current_rom=False))
    for row in rows:
        relative = Path('evidence')/SCOPE/row['target'].removesuffix('.gba')/row['kind']/(row['kind']+'.json')
        sha = copy_current_proof(row['path'],output/relative)
        info['proofs'].append(dict(file=relative.as_posix(),target=row['target'],kind=row['kind'],sha256=sha))
    manifest = output/'versions.json'
    manifest.write_text(json.dumps(info,indent=2)+'\n')
    verify(output,require_seal=False)
    info['validated'] = True
    manifest.write_text(json.dumps(info,indent=2)+'\n')
    verify(output)
    build_archive(info,output,current_scope=SCOPE,historical_commit=HISTORICAL_COMMIT,extra_paths=extras)
    return info


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--validation',type=Path,default=ROOT/'mods/hoenn/generated-world-audit-validation')
    parser.add_argument('--plan',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'mods/hoenn/versions')
    parser.add_argument('--preflight',action='store_true',help='Validate reports without writing public ROMs')
    parser.add_argument('--write-plan',action='store_true',help='Select complete current reports into the explicit plan only')
    parser.add_argument('--frozen',type=Path,default=ROOT/'.local/generated-world-audit-frozen.json')
    parser.add_argument('--visual-commit',help='Full commit containing the reviewed source-reference PNGs')
    args = parser.parse_args()
    plan = args.plan or args.validation/'proof-plan.json'
    if args.write_plan:
        assert not args.preflight
        result = write_plan(args.validation,args.frozen,plan)
        print('Wrote explicit plan for',len(result['proofs']),'current reports; public ROMs unchanged.')
    elif args.preflight:
        if args.visual_commit:
            visual_archive_inputs(args.visual_commit)
        _, rows = prevalidate(args.source,args.validation,plan)
        print('All',len(rows),'current proofs checked; no public ROMs changed.')
    else:
        publish(args.source,args.validation,args.output,plan,args.visual_commit)
