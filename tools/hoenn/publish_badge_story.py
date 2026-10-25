"""Publish layer 164 only after its exact current proof contracts pass.

The download keeps all original historical report JSONs. Historical captures
remain in the repository and have immutable commit URLs and hashes in the ZIP;
the archive does not claim an offline replay of previous releases.
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
from publish_coastal_closures import (
    LEGACY_MEDIA, attachment_rows, copy_current_proof, relative_name,
    report_dependencies,
)
from verify_badge_story_update import (
    COMMON_KINDS, EDITION_KINDS, SCOPE, current_report, require_final_contract,
    verify_baseline_bytes, verify_proof,
)
from verify_fuchsia_update import previous_release
from verify_versions import verify


HISTORICAL_COMMIT = '4f7e33cd49004cde4dfb668d76deb95803981cf9'
ATTACHMENT_SCOPES = {SCOPE, 'coastal-closures', 'sevii-integrated-piers'}


def releases(info):
    while True:
        yield info
        if 'previous_port_validation' not in info:
            break
        info = previous_release(info)


def edition_report(validation, folder, kind):
    path = Path(validation) / folder / (kind + '.json')
    assert path.is_file(), ('Missing current proof', folder, kind)
    return path


def preserve_history(old, output):
    """Preserve the original reports and all inputs needed by their verifiers."""
    output = Path(output)
    current = ROOT / 'mods/hoenn/versions'
    for release in releases(old):
        for proof in release['proofs']:
            name = relative_name(proof['file'])
            source, target = current / name, output / name
            raw = source.read_bytes()
            assert hashlib.sha256(raw).hexdigest() == proof['sha256'], name
            if target.exists():
                assert target.read_bytes() == raw, ('Historical report changed', name)
            if release['validation_scope'] in ATTACHMENT_SCOPES:
                if source.resolve() == target.resolve():
                    report_dependencies(source, expected_sha=proof['sha256'])
                else:
                    copy_current_proof(source, target)
            elif not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
    output.mkdir(parents=True, exist_ok=True)
    if not (output / 'START-HERE.md').exists():
        shutil.copyfile(current / 'START-HERE.md', output / 'START-HERE.md')


def archive_plan(info, output, *, include_roms=True):
    """Hash every input; separate historical media from included current files."""
    output = Path(output)
    entries, media, visited_manifests = {}, {}, set()

    def add(path, name=None, sha=None, *, historical_scope=None):
        path = Path(path)
        name = relative_name(name or path.relative_to(ROOT))
        raw = path.read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        if sha is not None:
            assert actual == sha, name
        if historical_scope is not None and path.suffix in {'.png', '.mp4', '.gif'}:
            if path.is_relative_to(output):
                repository_file = (Path('mods/hoenn/versions') / path.relative_to(output)).as_posix()
            else:
                repository_file = path.relative_to(ROOT).as_posix()
            row = media.setdefault(name, dict(file=name, repository_file=repository_file,
                                              sha256=actual, required_by_historical_scopes=[]))
            assert row['sha256'] == actual, ('Historical media identity changed', name)
            assert row['repository_file'] == repository_file, ('Historical media path changed', name)
            if historical_scope not in row['required_by_historical_scopes']:
                row['required_by_historical_scopes'].append(historical_scope)
        else:
            if name in entries:
                assert hashlib.sha256(entries[name].read_bytes()).hexdigest() == actual, name
            else:
                entries[name] = path
        return raw

    def root_reference(reference, scope):
        name = relative_name(reference['file'])
        raw = add(ROOT / name, name, reference['sha256'], historical_scope=scope)
        for capture in reference.get('captures', []):
            root_reference(capture, scope)
        if name.endswith('.json'):
            report = json.loads(raw)
            for row in attachment_rows(report):
                path = Path(name).parent / relative_name(row['file'])
                add(ROOT / path, path, row['sha256'], historical_scope=scope)

    def metadata_references(release, historical_scope):
        for key, reference in release.items():
            if key == 'baseline_diagnostics':
                for row in reference:
                    root_reference(row, historical_scope)
            elif isinstance(reference, dict) and (key.endswith('_validation') or key.startswith('baseline_')):
                if 'file' in reference and 'sha256' in reference:
                    root_reference(reference, historical_scope)
                elif 'manifest' in reference and 'manifest_sha256' in reference:
                    name = relative_name(reference['manifest'])
                    raw = add(ROOT / name, name, reference['manifest_sha256'])
                    if name not in visited_manifests:
                        visited_manifests.add(name)
                        older = json.loads(raw)
                        metadata_references(older, older['validation_scope'])

    if include_roms:
        for row in info['variants']:
            add(output / row['file'], row['file'], row['sha256'])
        for name in ['review.json', 'SHA256SUMS', 'Pokemon-Journey-TESTE.sav']:
            add(ROOT / 'roms/rom-de-teste' / name)
    for name in ['versions.json', 'SHA256SUMS', 'START-HERE.md']:
        add(output / name, name)
    for name in ['AGENTS.md', '.agents/skills/gba-map-review/SKILL.md']:
        add(ROOT / name, name)
    for release in releases(info):
        historical_scope = None if release['validation_scope'] == SCOPE else release['validation_scope']
        for proof in release['proofs']:
            name = relative_name(proof['file'])
            add(output / name, name, proof['sha256'])
            if release['validation_scope'] in ATTACHMENT_SCOPES:
                dependencies = report_dependencies(output / name, expected_sha=proof['sha256'])
                for relative, (path, sha) in dependencies.items():
                    target = Path(name) if relative == Path('.') else Path(name).parent / relative
                    add(path, target, sha, historical_scope=historical_scope)
        metadata_references(release, historical_scope)
    for name, scope in LEGACY_MEDIA.items():
        add(ROOT / name, name, historical_scope=scope)
    for path in (ROOT / 'docs/design/badge-story').rglob('*'):
        if path.is_file():
            add(path)
    for name in ['docs/badge-story.md', 'docs/AJUSTES-GBA.txt']:
        path = ROOT / name
        if path.exists():
            add(path)
    for path in (ROOT / 'assets/tiles').rglob('*'):
        if path.is_file():
            add(path)
    assert not (set(entries) & set(media)), 'Current and historical media must not conflict'
    return entries, media


def archive_entries(info, output, *, include_roms=True):
    return archive_plan(info, output, include_roms=include_roms)[0]


def historical_media(rows):
    result = []
    for name, row in sorted(rows.items()):
        # These bytes must already exist in the immutable merged parent. New
        # current evidence can never be disguised as historical media.
        repository_file = relative_name(row['repository_file'])
        raw = subprocess.check_output(['git', 'show', HISTORICAL_COMMIT + ':' + repository_file], cwd=ROOT)
        assert hashlib.sha256(raw).hexdigest() == row['sha256'], name
        result.append(dict(row, url='https://github.com/brunotellesbt-sys/AiKalicaAiCrlBR/blob/'
                           + HISTORICAL_COMMIT + '/' + repository_file))
    return result


def build_archive(info, output):
    output = Path(output)
    entries, media = archive_plan(info, output)
    media_rows = historical_media(media)
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
            notes='Current evidence is included. Historical capture bytes remain in the repository at the pinned parent commit; original report JSONs and hashes are preserved.',
            commit=HISTORICAL_COMMIT, files=media_rows), indent=2) + '\n')
        review = json.loads((ROOT / 'roms/rom-de-teste/review.json').read_bytes())
        bundle.writestr('TESTE-DOWNLOAD.md',
                        '# Separate exploration edition\n\n'
                        'This archive contains the four normal editions. The current TESTE ROM '
                        'is published separately at ' + test_url + '.\n\n'
                        'File: `' + review['file'] + '`\n\nSHA-256: `' + review['sha256'] + '`\n\n'
                        'Its current review metadata, checksum list and native battery save '
                        'are included under `roms/rom-de-teste/`.\n')
        assert len(bundle.namelist()) == len(set(bundle.namelist()))
    assert pending.stat().st_size < 100 * 1024 * 1024, 'Archive exceeds the 100 MiB limit'
    with zipfile.ZipFile(pending) as bundle:
        assert bundle.testzip() is None
        for name, path in entries.items():
            assert hashlib.sha256(bundle.read(name)).digest() == hashlib.sha256(path.read_bytes()).digest(), name
        assert len([name for name in bundle.namelist() if name.endswith('.gba')]) == 4
    pending.replace(archive)
    return archive


def prevalidate_inputs(source, validation, old):
    """Bind all current reports before changing any public ROM or metadata."""
    source, validation = Path(source), Path(validation)
    save = ROOT / 'roms/rom-de-teste/Pokemon-Journey-TESTE.sav'
    review_raw = (validation / 'baseline/review.json').read_bytes()
    historical_save = validation / 'baseline/test.sav'
    verify_baseline_bytes('review.json', review_raw)
    verify_baseline_bytes('test.sav', historical_save.read_bytes())
    from verify_coastal_closures_update import verify_update as verify_previous
    verify_previous(ROOT / 'mods/hoenn/versions', old,
                    historical_review=json.loads(review_raw), historical_save=historical_save)
    with tempfile.TemporaryDirectory(prefix='badge-story-publish-check-', dir='/tmp') as temporary:
        scratch = Path(temporary)
        info = package(source, scratch)
        test = package_review(source, scratch / 'Pokemon-Journey-Gen1-9-Normal.gba', scratch / 'test')
        reports = [(validation / 'source.json', info['parent_rom_sha256'], 'badge-story-source', False)]
        for row in info['variants']:
            folder = row['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba')
            reports.extend((edition_report(validation, folder, kind), row['sha256'], kind, False)
                           for kind in sorted(EDITION_KINDS))
        reports.extend((edition_report(validation, 'TESTE', kind), test['sha256'], kind, True)
                       for kind in sorted(EDITION_KINDS))
        source_elf = json.loads((validation / 'source.json').read_bytes())['elf_sha256']
        for file, sha, kind, is_test in reports:
            report_dependencies(file)
            report = current_report(file.read_bytes(), sha, (file.parent.name, kind))
            verify_proof(report, file.parent, kind, is_test, save, info, old)
            if kind in {'qualifier-event', 'rival-identities'}:
                assert report['elf_sha256'] == source_elf, 'Native proof used an unaudited ELF'
    return len(reports)


def publish(source, validation, output):
    require_final_contract()
    source, validation, output = map(Path, [source, validation, output])
    baseline = validation / 'baseline'
    raw = (baseline / 'versions.json').read_bytes()
    old = verify_baseline_bytes('versions.json', raw)
    assert prevalidate_inputs(source, validation, old) == 26

    def reference(name):
        path = baseline / name
        return dict(file=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(path.read_bytes()).hexdigest())

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
                historical_release=dict(scope=old['validation_scope'], parent_rom_sha256=old['parent_rom_sha256'],
                                        variants={row['file']: row['sha256'] for row in old['variants']},
                                        test_rom_sha256=previous_review['sha256'], proof_count=31,
                                        retested_on_current_rom=False))

    def add(file, target, kind):
        rel = Path('evidence/badge-story') / target.removesuffix('.gba') / kind / (kind + '.json')
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
    parser.add_argument('--validation', type=Path, default=ROOT / 'mods/hoenn/badge-story-validation')
    parser.add_argument('--output', type=Path, default=ROOT / 'mods/hoenn/versions')
    options = parser.parse_args()
    publish(options.source, options.validation, options.output)
