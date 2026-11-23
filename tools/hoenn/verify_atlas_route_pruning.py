"""Rebuild the five patched ROMs in memory and check their compiled map bytes."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

from prepare_atlas_route_pruning import H, J, K, LAYER
from verify_versions import VARIANTS

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / 'mods/hoenn/atlas-route-pruning'
sys.path.insert(0, str(ROOT / 'tools/unova'))
from bps import apply


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify(directory=DIRECTORY, base_root=ROOT, *, output=None):
    directory, base_root = Path(directory), Path(base_root)
    report = json.loads((directory / 'validation.json').read_bytes())
    assert report['layer'] == LAYER
    assert set(map(tuple, report['removed_atlas_pixels'])) == H | J | K
    assert sha((directory / 'mapa-HJK.png').read_bytes()) == report['map_png_sha256']
    rows = report['editions']
    assert len(rows) == 5 and {row['edition'] for row in rows} == set(VARIANTS) | {'Pokemon-Journey-TESTE.gba'}
    candidate = report['candidate_base_rom_sha256']
    evidence = directory / 'evidence'
    for filename, expected in report['evidence_sha256'].items():
        assert Path(filename).name == filename
        assert sha((evidence / filename).read_bytes()) == expected, filename
    native = json.loads((evidence / 'navigation.json').read_bytes())
    assert native['passed'] and native['new_rom_sha256'] == candidate
    assert native['elf_sha256'] == report['elf_sha256']
    assert native['marker_sha256'] == report['marker_sha256']
    assert report['input_files_checked'] >= 34000
    assert {row['case'] for row in native['trips']} == {
        'K-west-east', 'K-south-fork', 'H-J-around-mossdeep'}
    assert {row['case'].split('-')[1] for row in native['reef_bumps']} == {'H', 'J', 'K'}
    assert len(native['saves']) == 5 and {r['surfing'] for r in native['saves']} == {False, True}
    for row in rows:
        name = row['edition']
        expected_base = 'roms/rom-de-teste/' + name if name.endswith('-TESTE.gba') else 'roms/' + name
        assert row['base'] == expected_base
        base = (base_root / expected_base).read_bytes()
        assert sha(base) == row['base_sha256'], ('Select the matching published Atlas 172 base', name)
        patch_name = name.removesuffix('.gba') + '-atlas172-HJK.bps'
        assert row['patch'] == patch_name
        patch = (directory / patch_name).read_bytes()
        assert sha(patch) == row['patch_sha256'], patch_name
        rom = apply(patch, base)
        assert len(rom) == 33554432 and sha(rom) == row['rom_sha256'], name
        assert rom[0xbd] == (-sum(rom[0xa0:0xbd]) - 0x19) & 255
        for symbol, block in report['compiled_ranges'].items():
            offset, size = block['offset'], block['size']
            assert 0 <= offset <= len(rom) - size
            assert sha(rom[offset:offset + size]) == block['sha256'], (name, symbol)
        rules = json.loads(gzip.decompress((evidence / (name.removesuffix('.gba') + '-rules.json.gz')).read_bytes()))
        assert rules['passed'] and rules['artifact_sha256']['pokeemerald.gba'] == row['rom_sha256']
        assert rules['artifact_sha256']['pokeemerald.elf'] == report['elf_sha256']
        caps = rules['canonical_location_counts']
        assert len(caps) == 1025 and all(
            bool(v) == (int(k) <= rules['max_national']) for k, v in caps.items())
        boot = json.loads((evidence / (name.removesuffix('.gba') + '-boot.json')).read_bytes())
        assert boot['passed'] and boot['rom_sha256'] == row['rom_sha256']
        if name in ('Pokemon-Journey-Gen1-9-Normal.gba', 'Pokemon-Journey-TESTE.gba'):
            trainer = json.loads((evidence / (name.removesuffix('.gba') + '-trainer.json')).read_bytes())
            assert trainer['passed'] and trainer['artifact_sha256']['pokeemerald.gba'] == row['rom_sha256']
            battle, = trainer['cases']
            assert battle['trainer'] == 1846 and battle['outcome'] == 1 and battle['private_defeat_flag_set']
            assert trainer['current_cold_continue_preserves_private_flags']
        if output is not None:
            (output / name).write_bytes(rom)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-root', type=Path, default=ROOT)
    args = parser.parse_args()
    verify(base_root=args.base_root)
    print('Five exact BPS round trips, compiled blocks, chart and native reports verified')
