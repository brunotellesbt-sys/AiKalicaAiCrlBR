"""Snapshot the old release and freeze five immutable aliases of layer 165.

Packaging happens in an ignored artifact directory. Public ROMs and downloads
are updated only later by the proof-gated publisher.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from package_versions import ROOT, package
from package_review_rom import package as package_review
from generated_world_contract import BASELINE_SHA256, PARENT_ROM_SHA256


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def snapshot_baseline(output):
    output = Path(output)
    paths = {'versions.json': ROOT / 'mods/hoenn/versions/versions.json',
             'review.json': ROOT / 'roms/rom-de-teste/review.json',
             'test.sav': ROOT / 'roms/rom-de-teste/Pokemon-Journey-TESTE.sav'}
    for name, path in paths.items():
        assert digest(path) == BASELINE_SHA256[name], ('Layer-164 public baseline changed', name)
        target = output / name
        if target.exists():
            assert target.read_bytes() == path.read_bytes(), ('Existing baseline differs', target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
    old = json.loads((output / 'versions.json').read_bytes())
    assert old['validated'] is True and old['parent_rom_sha256'] == PARENT_ROM_SHA256
    assert old['validation_scope'] == 'badge-story' and len(old['integration_layers']) == 164


def freeze(source, artifacts, aliases, output):
    from prepare_generated_world_audit import LAYER, PRIOR
    source, artifacts, aliases, output = map(lambda p: Path(p).resolve(),
                                             (source, artifacts, aliases, output))
    assert not aliases.exists() and not output.exists(), 'Refusing to overwrite frozen aliases'
    raw_sha, elf_sha = digest(source / 'pokeemerald.gba'), digest(source / 'pokeemerald.elf')
    assert raw_sha != PARENT_ROM_SHA256, 'Layer 165 must be compiled before freezing'
    assert (source / ('.journey-' + LAYER)).is_file()
    release = package(source, artifacts)
    assert release['integration_layers'] == PRIOR + [LAYER]
    review = package_review(source, artifacts / 'Pokemon-Journey-Gen1-9-Normal.gba', artifacts / 'test')
    editions = []
    for name, rom, sha in [
        *[(row['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba'),
           artifacts / row['file'], row['sha256']) for row in release['variants']],
        ('TESTE', artifacts / 'test' / review['file'], review['sha256']),
    ]:
        target = aliases / name
        target.mkdir(parents=True)
        for path in source.iterdir():
            if path.name != 'pokeemerald.gba':
                (target / path.name).symlink_to(path, target_is_directory=path.is_dir())
        shutil.copyfile(rom, target / 'pokeemerald.gba')
        assert digest(target / 'pokeemerald.gba') == sha
        editions.append(dict(edition=name, source=str(target), rom_file=str(rom), sha256=sha))
    assert digest(source / 'pokeemerald.gba') == raw_sha and digest(source / 'pokeemerald.elf') == elf_sha
    result = dict(parent_source=str(source), parent_rom_sha256=raw_sha,
                  parent_elf_sha256=elf_sha, layer_marker_sha256=digest(source / ('.journey-' + LAYER)),
                  editions=editions, release=release, review=review)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--artifacts', type=Path, default=ROOT / '.local/generated-world-audit-artifacts')
    parser.add_argument('--aliases', type=Path, default=ROOT / '.local/generated-world-audit-editions')
    parser.add_argument('--output', type=Path, default=ROOT / '.local/generated-world-audit-frozen.json')
    parser.add_argument('--snapshot-baseline', type=Path)
    args = parser.parse_args()
    if args.snapshot_baseline:
        snapshot_baseline(args.snapshot_baseline)
    if args.source:
        print(json.dumps(freeze(args.source, args.artifacts, args.aliases, args.output), indent=2))
    else:
        assert args.snapshot_baseline, 'Supply --source and/or --snapshot-baseline'
