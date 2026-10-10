"""Build/export the complete layered world as a versioned playable alpha."""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile
from prepare_crossing import PIN
from prepare_lavender_network import CHAIN, LAYER

ROOT = Path(__file__).resolve().parents[2]
LAYERS = CHAIN + [LAYER, 'world-map', 'kanto-open-sea', 'coastal-world-map', 'remote-islands']
VERSION = 'world-alpha-1'
ROM_NAME = 'Pokemon-Journey-World-Alpha-1.gba'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_source(source):
    acquired = json.loads((source / '.source-acquired.json').read_text())
    if acquired['commit'] != PIN:
        raise ValueError('Unexpected source revision')
    expected = {}
    marker_hashes = {}
    for layer in LAYERS:
        marker = source / ('.journey-' + layer)
        expected.update(json.loads(marker.read_text())['prepared_sha256'])
        marker_hashes[layer] = digest(marker)
    for name, wanted in expected.items():
        if digest(source / name) != wanted:
            raise ValueError('Layered source changed: ' + name)
    return expected, marker_hashes


def build(source, jobs):
    # A partially prepared checkout must contain a consecutive layer prefix.
    missing = False
    for layer in LAYERS:
        marker = source / ('.journey-' + layer)
        if marker.exists():
            if missing:
                raise ValueError('Non-consecutive layer markers: ' + layer)
            continue  # Later layers intentionally supersede earlier outputs.
        missing = True
        module = 'prepare_crossing' if layer == 'hoenn-crossing' else 'prepare_' + layer.replace('-', '_')
        importlib.import_module(module).prepare(source)
    verify_source(source)
    subprocess.run(['make', '-C', str(source), '-j' + str(jobs)], check=True)


def package(source, output, archive=None):
    source, output = Path(source), Path(output)
    expected, markers = verify_source(source)
    raw = (source / 'pokeemerald.gba').read_bytes()
    if not 192 <= len(raw) <= 32 * 1024 * 1024:
        raise ValueError('Invalid GBA ROM size')
    if raw[0xB2] != 0x96 or raw[0xBD] != (-sum(raw[0xA0:0xBD]) - 0x19) & 255:
        raise ValueError('Invalid GBA header')
    output.mkdir(parents=True, exist_ok=True)
    rom = output / ROM_NAME
    rom.write_bytes(raw)
    manifest = dict(version=VERSION, stage='playable_alpha', file=ROM_NAME,
        sha256=digest(rom), bytes=len(raw), game_code=raw[0xAC:0xB0].decode('ascii'),
        source_repository='eonlynx/pokecrossroads', source_commit=PIN,
        layers=LAYERS, layer_marker_sha256=markers,
        prepared_source_files=len(expected), requires_new_save=True,
        save_namespace=ROM_NAME, game_language='English',
        full_campaign_playthrough=False)
    (output / 'release.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (output / 'SHA256SUMS').write_text(manifest['sha256'] + '  ' + ROM_NAME + '\n')
    shutil.copyfile(ROOT / 'mods/hoenn/PLAYABLE-ALPHA.md', output / 'START-HERE.md')
    if archive:
        archive = Path(archive)
        archive.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
            for name in [ROM_NAME, 'release.json', 'SHA256SUMS', 'START-HERE.md']:
                info = zipfile.ZipInfo(name, (2026, 10, 10, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                bundle.writestr(info, (output / name).read_bytes(), compresslevel=9)
        print('ZIP:', archive, digest(archive))
    print(json.dumps(manifest, indent=2))
    return manifest


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, default=ROOT / 'mods/hoenn/playable')
    p.add_argument('--archive', type=Path)
    p.add_argument('--build', action='store_true')
    p.add_argument('--jobs', type=int, choices=range(1, 17), default=min(8, os.cpu_count() or 4))
    args = p.parse_args()
    if args.build:
        build(args.source, args.jobs)
    package(args.source, args.output, args.archive)
