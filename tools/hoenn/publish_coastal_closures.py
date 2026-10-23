"""Publish layer 163 with exact current proofs and an explicit historical archive.

The archive contains current and layer-162 proof attachments once at their
canonical paths. Older media retain their original hashes and repository URLs;
this download does not claim a fully offline historical campaign replay.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

from package_review_rom import package as package_review
from package_versions import ROOT, package
from publish_sevii_integrated_piers import copy_proof
from verify_coastal_closures_update import (
    COMMON_KINDS, EDITION_KINDS, SCOPE, current_report, require_final_contract,
    verify_source, verify_six_closures, verify_dewford_movement,
    verify_coast_connections, verify_shore_animation, verify_review_mode,
    verify_cold_boot, verify_baseline_bytes,
)
from verify_fuchsia_update import previous_release
from verify_versions import verify


LEGACY_MEDIA = {
    'docs/videos/dewford-coast-corrected.mp4': 'dewford-coast-safety',
    'docs/videos/surf-connections-repaired.mp4': 'extra-gyms',
    'mods/hoenn/extra-gyms-validation/baseline/western-river-fallarbor.mp4': 'ever-grande-market',
    'docs/videos/mossdeep-one-island-surf.mp4': 'surf-review',
}


def relative_name(value):
    path = Path(value)
    assert not path.is_absolute() and '..' not in path.parts
    return path.as_posix()


def edition_report(validation, folder, kind):
    """Use the native owner's layout and reject a stale competing report."""
    base = Path(validation) / folder
    candidates = [base / (kind + '.json')]
    if kind == 'shore-animation':
        candidates.append(base / 'shore' / (kind + '.json'))
    existing = [path for path in candidates if path.is_file()]
    assert len(existing) == 1, ('Missing or ambiguous current proof', folder, kind, existing)
    return existing[0]


def attachment_rows(report):
    rows = list(report.get('captures', [])) + list(report.get('source_review_images', []))
    if 'video_sha256' in report:
        rows.append(dict(file=report['video'], sha256=report['video_sha256']))
    return rows


def report_dependencies(file, *, expected_sha=None, active=None):
    """Read a report's checked files without changing its paths or bytes."""
    file = Path(file)
    active = set() if active is None else active
    identity = file.resolve()
    assert identity not in active, ('Cyclic proof component', file)
    active.add(identity)
    raw = file.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if expected_sha is not None:
        assert actual == expected_sha, ('Proof component hash mismatch', file)
    result = {Path('.'): (file, actual)}
    report = json.loads(raw)
    for row in attachment_rows(report):
        path = Path(relative_name(row['file']))
        assert path.suffix in {'.png', '.mp4'}, path
        source = file.parent / path
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        assert digest == row['sha256'], ('Proof attachment hash mismatch', source)
        assert path not in result, ('Duplicate attachment path', path)
        result[path] = source, digest
    for component in report.get('components', []):
        path = Path(relative_name(component['file']))
        assert path.suffix == '.json', ('A proof component must be a JSON report', path)
        child = report_dependencies(file.parent / path, expected_sha=component['sha256'], active=active)
        for name, value in child.items():
            target = path if name == Path('.') else path.parent / name
            if target in result:
                assert result[target][1] == value[1], ('Conflicting proof dependency', target)
            else:
                result[target] = value
    active.remove(identity)
    return result


def copy_current_proof(file, destination):
    """Copy components and captures after checking every dependency first."""
    file, destination = Path(file), Path(destination)
    dependencies = report_dependencies(file)
    for name, (source, _) in dependencies.items():
        target = destination if name == Path('.') else destination.parent / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    return dependencies[Path('.')][1]


def preserve_history(old, output):
    """Copy the exact historical reports; layer 162 retains its native attachments."""
    output = Path(output)
    current = ROOT / 'mods/hoenn/versions'
    history = old
    while True:
        for proof in history['proofs']:
            name = relative_name(proof['file'])
            source, target = current / name, output / name
            raw = source.read_bytes()
            assert hashlib.sha256(raw).hexdigest() == proof['sha256'], name
            if target.exists():
                assert target.read_bytes() == raw, ('Historical report changed', name)
            if history['validation_scope'] == 'sevii-integrated-piers':
                if source.resolve() != target.resolve():
                    copy_proof(source, target)
                else:
                    for attachment in attachment_rows(json.loads(raw)):
                        path = source.parent / relative_name(attachment['file'])
                        assert hashlib.sha256(path.read_bytes()).hexdigest() == attachment['sha256']
            elif not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
        if 'previous_port_validation' not in history:
            break
        history = previous_release(history)
    output.mkdir(parents=True, exist_ok=True)
    if not (output / 'START-HERE.md').exists():
        shutil.copyfile(current / 'START-HERE.md', output / 'START-HERE.md')


def archive_entries(info, output, *, include_roms=True):
    """Return a hash-checked dependency graph without writing or packaging ROMs."""
    output = Path(output)
    entries, visited_manifests = {}, set()

    def add(path, name=None, sha=None):
        path = Path(path)
        name = relative_name(name or path.relative_to(ROOT))
        raw = path.read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        if sha is not None:
            assert actual == sha, name
        if name in entries:
            assert hashlib.sha256(entries[name].read_bytes()).hexdigest() == actual, name
        else:
            entries[name] = path
        return raw

    def root_reference(reference):
        name = relative_name(reference['file'])
        raw = add(ROOT / name, name, reference['sha256'])
        for capture in reference.get('captures', []):
            root_reference(capture)
        if name.endswith('.json'):
            report = json.loads(raw)
            for row in attachment_rows(report):
                path = Path(name).parent / relative_name(row['file'])
                add(ROOT / path, path, row['sha256'])

    def metadata_references(release):
        for key, reference in release.items():
            if key == 'baseline_diagnostics':
                for row in reference:
                    root_reference(row)
            elif isinstance(reference, dict) and (key.endswith('_validation') or key.startswith('baseline_')):
                if 'file' in reference and 'sha256' in reference:
                    root_reference(reference)
                elif 'manifest' in reference and 'manifest_sha256' in reference:
                    name = relative_name(reference['manifest'])
                    raw = add(ROOT / name, name, reference['manifest_sha256'])
                    if name not in visited_manifests:
                        visited_manifests.add(name)
                        metadata_references(json.loads(raw))

    if include_roms:
        for row in info['variants']:
            add(output / row['file'], row['file'], row['sha256'])
        review = ROOT / 'roms/rom-de-teste'
        for name in ['review.json', 'SHA256SUMS', 'Pokemon-Journey-TESTE.sav']:
            add(review / name)
    for name in ['versions.json', 'SHA256SUMS', 'START-HERE.md']:
        add(output / name, name)
    for name in ['AGENTS.md', '.agents/skills/gba-map-review/SKILL.md']:
        add(ROOT / name, name)
    history = info
    while True:
        for proof in history['proofs']:
            name = relative_name(proof['file'])
            report = json.loads(add(output / name, name, proof['sha256']))
            if history['validation_scope'] in {SCOPE, 'sevii-integrated-piers'}:
                dependencies = report_dependencies(output / name, expected_sha=proof['sha256'])
                for relative, (path, sha) in dependencies.items():
                    target = Path(name) if relative == Path('.') else Path(name).parent / relative
                    add(path, target, sha)
        metadata_references(history)
        if 'previous_port_validation' not in history:
            break
        history = previous_release(history)
    # Include only the current report's design directory and release notes.
    # Historical visual artifacts referenced by proofs were already added.
    for path in (ROOT / 'docs/design/coastal-closures').rglob('*'):
        if path.is_file():
            add(path)
    notes = ROOT / 'docs/coastal-closures.md'
    if notes.exists():
        add(notes)
    guide = ROOT / 'docs/AJUSTES-GBA.txt'
    if guide.exists():
        add(guide)
    for path in (ROOT / 'assets/tiles').rglob('*'):
        if path.is_file():
            add(path)
    return entries


def external_history_media():
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    rows = []
    for name, required_by in LEGACY_MEDIA.items():
        raw = (ROOT / name).read_bytes()
        # The immutable repository URL must identify the exact original media.
        committed = subprocess.check_output(['git', 'show', commit + ':' + name], cwd=ROOT)
        assert committed == raw, ('Historical media differs from its pinned repository commit', name)
        rows.append(dict(file=name, sha256=hashlib.sha256(raw).hexdigest(),
                         required_by_historical_scope=required_by,
                         url='https://github.com/brunotellesbt-sys/AiKalicaAiCrlBR/blob/' + commit + '/' + name))
    return rows


def build_archive(info, output):
    output = Path(output)
    entries = archive_entries(info, output)
    archive = output / 'Pokemon-Journey-Four-Editions.zip'
    pending = archive.with_suffix('.zip.tmp')
    branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip()
    reference = branch or subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    test_url = 'https://github.com/brunotellesbt-sys/AiKalicaAiCrlBR/tree/' + reference + '/roms/rom-de-teste'
    with zipfile.ZipFile(pending, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name, path in sorted(entries.items()):
            bundle.write(path, name)
        bundle.writestr('HISTORICAL-MEDIA.json', json.dumps(dict(
            full_historical_verification_available_offline=False,
            notes='Layer 162 and current proof attachments are included. Older native videos retain their original hashes and repository identities.',
            files=external_history_media()), indent=2) + '\n')
        review = json.loads((ROOT / 'roms/rom-de-teste/review.json').read_bytes())
        bundle.writestr('TESTE-DOWNLOAD.md',
                        '# Separate exploration edition\n\n'
                        'This archive contains the four normal editions. The current TESTE ROM '\
                        'is published separately at ' + test_url + '.\n\n'
                        'File: `' + review['file'] + '`\n\nSHA-256: `' + review['sha256'] + '`\n\n'
                        'Its current review metadata, checksum list and native battery save are '\
                        'included under `roms/rom-de-teste/`.\n')
        assert len(bundle.namelist()) == len(set(bundle.namelist()))
    assert pending.stat().st_size < 100 * 1024 * 1024, 'Archive exceeds the 100 MiB limit'
    with zipfile.ZipFile(pending) as bundle:
        assert bundle.testzip() is None
        for name, path in entries.items():
            assert hashlib.sha256(bundle.read(name)).digest() == hashlib.sha256(path.read_bytes()).digest(), name
    pending.replace(archive)
    return archive


def prevalidate_inputs(source, validation, old):
    """Reject missing/stale/failed proofs before replacing any public download."""
    source, validation = Path(source), Path(validation)
    save = ROOT / 'roms/rom-de-teste/Pokemon-Journey-TESTE.sav'
    from verify_sevii_integrated_piers_update import verify_update as verify_previous
    review_raw = (validation / 'baseline/review.json').read_bytes()
    historical_save = validation / 'baseline/test.sav'
    verify_baseline_bytes('review.json', review_raw)
    verify_baseline_bytes('test.sav', historical_save.read_bytes())
    verify_previous(ROOT / 'mods/hoenn/versions', old,
                    historical_review=json.loads(review_raw), historical_save=historical_save)
    # package() syncs public roms/ only for its real release directory. These
    # independent scratch editions let us bind all proofs before that mutation.
    with tempfile.TemporaryDirectory(prefix='coastal-publish-check-', dir='/tmp') as temporary:
        scratch = Path(temporary)
        info = package(source, scratch)
        test = package_review(source, scratch / 'Pokemon-Journey-Gen1-9-Normal.gba', scratch / 'test')
        reports = [(validation / 'source.json', info['parent_rom_sha256'], 'coastal-closures-source', False)]
        for row in info['variants']:
            folder = row['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba')
            reports.extend((edition_report(validation, folder, kind), row['sha256'], kind, False)
                           for kind in sorted(EDITION_KINDS))
        reports.extend((edition_report(validation, 'TESTE', kind), test['sha256'], kind, True)
                       for kind in sorted(EDITION_KINDS))
        native = {'six-coastal-closures': verify_six_closures,
                  'dewford-movement': verify_dewford_movement,
                  'affected-coast-connections': verify_coast_connections,
                  'shore-animation': verify_shore_animation}
        for file, sha, kind, is_test in reports:
            dependencies = report_dependencies(file)
            report = current_report(file.read_bytes(), sha, (file.parent.name, kind))
            assert dependencies[Path('.')][1] == hashlib.sha256(file.read_bytes()).hexdigest()
            if kind in EDITION_KINDS and kind != 'cold-boot':
                assert report['review_mode'] is is_test
            if kind == 'coastal-closures-source':
                verify_source(report, info, old)
            elif kind in native:
                native[kind](report, file.parent)
            elif kind == 'review-mode':
                verify_review_mode(report, is_test, save)
            elif kind == 'cold-boot':
                verify_cold_boot(report, is_test, save)
            else:
                raise AssertionError(('Unsupported current proof', kind))
    return len(reports)


def publish(source, validation, output):
    # This gate runs before package() can replace any downloadable ROM or save metadata.
    require_final_contract()
    source, validation, output = map(Path, [source, validation, output])
    baseline = validation / 'baseline'
    raw = (baseline / 'versions.json').read_bytes()
    old = verify_baseline_bytes('versions.json', raw)
    assert prevalidate_inputs(source, validation, old) == 31

    def reference(name):
        path = baseline / name
        return dict(file=path.relative_to(ROOT).as_posix(),
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    previous_review = json.loads((baseline / 'review.json').read_bytes())
    preserve_history(old, output)
    info = package(source, output)
    package_review(source, output / 'Pokemon-Journey-Gen1-9-Normal.gba', ROOT / 'roms/rom-de-teste')
    info.update(validation_scope=SCOPE, validated=False, full_campaign_playthrough=False,
                proofs=[], historical_validation=old['historical_validation'],
                previous_validation=old['previous_validation'],
                previous_port_validation=dict(manifest=(baseline / 'versions.json').relative_to(ROOT).as_posix(),
                                              manifest_sha256=hashlib.sha256(raw).hexdigest(),
                                              retested_on_current_rom=False),
                previous_review_validation=reference('review.json'),
                previous_review_save_validation=reference('test.sav'),
                previous_features_retested_on_current_rom=False,
                historical_release=dict(scope=old['validation_scope'],
                                        parent_rom_sha256=old['parent_rom_sha256'],
                                        variants={row['file']: row['sha256'] for row in old['variants']},
                                        test_rom_sha256=previous_review['sha256'],
                                        proof_count=42, retested_on_current_rom=False))

    def add(file, target, kind):
        rel = Path('evidence/coastal-closures') / target.removesuffix('.gba') / kind / (kind + '.json')
        sha = copy_current_proof(file, output / rel)
        info['proofs'].append(dict(file=rel.as_posix(), target=target, kind=kind, sha256=sha))

    for kind in sorted(COMMON_KINDS):
        add(validation / 'source.json', 'common', kind)
    targets = [(row['file'], row['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba'))
               for row in info['variants']] + [('test', 'TESTE')]
    for target, folder in targets:
        for kind in sorted(EDITION_KINDS):
            add(edition_report(validation, folder, kind), target, kind)
    manifest = output / 'versions.json'
    manifest.write_text(json.dumps(info, indent=2) + '\n')
    verify(output, require_seal=False)
    info['validated'] = True
    manifest.write_text(json.dumps(info, indent=2) + '\n')
    verify(output)
    build_archive(info, output)
    return info


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--validation', type=Path, default=ROOT / 'mods/hoenn/coastal-closures-validation')
    parser.add_argument('--output', type=Path, default=ROOT / 'mods/hoenn/versions')
    options = parser.parse_args()
    publish(options.source, options.validation, options.output)
