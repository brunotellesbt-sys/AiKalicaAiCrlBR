"""Publish the coast repairs and retain immutable earlier gym validation."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

from package_versions import ROOT, package
from package_review_rom import package as package_review
from verify_fuchsia_update import previous_release
from verify_versions import verify


def publish(source, validation, output):
    source, validation, output = map(Path, [source, validation, output])
    baseline = validation / 'baseline'
    raw = (baseline / 'versions.json').read_bytes()
    old = json.loads(raw)
    assert old['validated'] and old['validation_scope'] == 'extra-gyms'
    info = package(source, output)
    package_review(source, output / 'Pokemon-Journey-Gen1-9-Normal.gba',
                   ROOT / 'roms/rom-de-teste')

    def reference(name):
        path = baseline / name
        return dict(file=path.relative_to(ROOT).as_posix(),
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    info.update(validation_scope='dewford-coast-safety', validated=False,
                full_campaign_playthrough=False, proofs=[],
                historical_validation=old['historical_validation'],
                previous_validation=old['previous_validation'],
                previous_port_validation=dict(
                    manifest=(baseline / 'versions.json').relative_to(ROOT).as_posix(),
                    manifest_sha256=hashlib.sha256(raw).hexdigest(),
                    retested_on_current_rom=False),
                previous_review_validation=reference('review.json'),
                previous_review_save_validation=reference('test.sav'),
                previous_features_retested_on_current_rom=False)

    def add(file, target, kind):
        rel = Path('evidence/dewford-coast') / target.removesuffix('.gba') / (kind + '.json')
        destination = output / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(file, destination)
        info['proofs'].append(dict(file=rel.as_posix(), target=target, kind=kind,
                                   sha256=hashlib.sha256(destination.read_bytes()).hexdigest()))

    add(validation / 'source.json', 'common', 'dewford-coast-source')
    add(validation / 'all-surf/all-surf-links.json', 'common', 'all-surf-links')
    targets = [(row['file'], row['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba'))
               for row in info['variants']] + [('test', 'TESTE')]
    for target, folder in targets:
        for kind in ['dewford-coast', 'review-mode', 'coastal-pier-safety',
                     'coastal-cave-finishing', 'cold-boot']:
            add(validation / folder / (kind + '.json'), target, kind)
    manifest = output / 'versions.json'
    manifest.write_text(json.dumps(info, indent=2) + '\n')
    verify(output, require_seal=False)
    info['validated'] = True
    manifest.write_text(json.dumps(info, indent=2) + '\n')
    verify(output)

    archive = output / 'Pokemon-Journey-Four-Editions.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        archived = set()

        def include(path, name=None):
            name = name or path.relative_to(ROOT).as_posix()
            if name not in archived:
                bundle.write(path, name)
                archived.add(name)

        for name in [row['file'] for row in info['variants']] + ['versions.json', 'SHA256SUMS', 'START-HERE.md']:
            include(output / name, name)
        for path in (output / 'evidence').rglob('*.json'):
            include(path, path.relative_to(output).as_posix())
        for name in ['AGENTS.md', '.agents/skills/gba-map-review/SKILL.md']:
            include(ROOT / name)
        # Preserve current focused evidence and the original gym evidence as
        # separate files with their original hashes and ROM identities.
        for evidence in [ROOT / 'mods/hoenn/extra-gyms-validation', validation]:
            for path in evidence.rglob('*'):
                if path.is_file() and path.suffix in ['.json', '.png', '.sav']:
                    include(path)
        references = {path.relative_to(ROOT).as_posix()
                      for path in (ROOT / 'docs/design').glob('proposta*.png')} | {
                          'docs/images/fallarbor/proposal.png',
                          'docs/images/island-harbors/Dewford-shore-reference.png',
                          'docs/images/harbor-concept-reference.png'}
        for path in (ROOT / 'docs').rglob('*'):
            if path.is_file() and path.suffix != '.mp4' and path.relative_to(ROOT).as_posix() not in references:
                include(path)
        bundle.writestr('REFERENCE-IMAGES.md',
                        '# Earlier concept references\n\nNative captures and evidence are included. '
                        'Earlier concept images remain in the repository to keep this four-ROM archive below GitHub\'s file-size limit.\n\n' +
                        ''.join('- [' + name + '](https://github.com/brunotellesbt-sys/AiKalicaAiCrlBR/blob/main/' + name + ')\n'
                                for name in sorted(references)))
        # Keep historical videos in Git with their original proof hashes. The
        # download contains four ROMs; including those older, duplicated videos
        # leaves no space for the current repairs under GitHub's 100 MiB limit.
        old_videos = [ROOT / 'docs/videos/surf-connections-repaired.mp4',
                      ROOT / 'docs/videos/western-river-fallarbor.mp4',
                      *sorted((ROOT / 'mods/hoenn/extra-gyms-validation/baseline').glob('*.mp4'))]
        bundle.writestr('HISTORICAL-VIDEOS.md',
                        '# Earlier native recordings\n\nThese recordings retain their original ROM identities; '
                        'they are historical evidence, not tests of this release.\n\n' +
                        ''.join('- [' + path.relative_to(ROOT).as_posix() +
                                '](https://github.com/brunotellesbt-sys/AiKalicaAiCrlBR/blob/main/' +
                                path.relative_to(ROOT).as_posix() + ')\n'
                                for path in old_videos if path.exists()))
        for name in ['dewford-coast-corrected.mp4']:
            path = ROOT / 'docs/videos' / name
            if path.exists():
                include(path)
        history = old
        while 'previous_port_validation' in history:
            include(ROOT / history['previous_port_validation']['manifest'])
            history = previous_release(history)
        assert len(bundle.namelist()) == len(set(bundle.namelist()))
    assert archive.stat().st_size < 100 * 1024 * 1024
    return info


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--validation', type=Path, default=ROOT / 'mods/hoenn/dewford-coast-validation')
    parser.add_argument('--output', type=Path, default=ROOT / 'mods/hoenn/versions')
    arguments = parser.parse_args()
    publish(arguments.source, arguments.validation, arguments.output)
