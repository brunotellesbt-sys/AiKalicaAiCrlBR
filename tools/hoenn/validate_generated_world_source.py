"""Reproduce resource-only layer 165 and bind its source to the compiled ROM."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from prepare_generated_world_audit import LAYER, PRIOR, PARENT_ROM_SHA256, prepare, verify_parent

ROOT = Path(__file__).resolve().parents[2]
LODGE_FILES = frozenset('data/maps/Journey' + name + 'IslandHarborPortLodge/map.json'
                       for name in ['One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven'])
EVENT_FILES = LODGE_FILES | {'data/maps/JourneySanctuaryDimensoes/map.json'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def allowed_resource_path(name):
    # Terrain-only repairs must never smuggle campaign/runtime or atlas edits.
    return bool(re.fullmatch(r'data/layouts/[A-Za-z0-9_]+/(?:map|border).bin', name)) or name in EVENT_FILES


def validate(source, baseline, output, preflight=False):
    source, baseline, output = map(Path, (source, baseline, output))
    assert source.resolve() != baseline.resolve()
    expected = verify_parent(baseline)
    marker = json.loads((source / ('.journey-' + LAYER)).read_bytes())
    outputs = marker['prepared_sha256']
    assert outputs and all(allowed_resource_path(name) for name in outputs), 'Unreviewed resource scope'
    assert set(LODGE_FILES) <= set(outputs), 'All seven obsolete lodge exits need compatibility repairs'
    assert all(sha != expected.get(name) for name, sha in outputs.items()), 'No-op staged file'
    assert marker['parent_rom_sha256'] == PARENT_ROM_SHA256
    for name, sha in (expected | outputs).items():
        assert digest(source / name) == sha, ('Unexpected source change', name)
    for name in ['.source-acquired.json', *['.journey-' + layer for layer in PRIOR]]:
        assert (source / name).read_bytes() == (baseline / name).read_bytes(), name
    # Map/header/graphic generators emit build products outside the acquired
    # source manifest. Runtime C/header inputs may not grow during this layer.
    for directory in ('src', 'include'):
        old = {p.relative_to(baseline).as_posix() for p in (baseline / directory).rglob('*') if p.is_file()}
        new = {p.relative_to(source).as_posix() for p in (source / directory).rglob('*') if p.is_file()}
        assert new == old, ('No new source/graphics files expected', directory)
        for name in old - expected.keys():
            assert (source / name).read_bytes() == (baseline / name).read_bytes(), name
    with tempfile.TemporaryDirectory(prefix='generated-world-replay-', dir='/tmp') as temporary:
        replay = Path(temporary)
        for name in [*expected, '.source-acquired.json', *['.journey-' + layer for layer in PRIOR]]:
            target = replay / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(baseline / name, target)
        fresh = prepare(replay)
        assert fresh == marker and prepare(replay) == fresh, 'Repair replay or idempotence mismatch'
    checked_blocks = []
    rom_sha, elf_sha = None, None
    if not preflight:
        rom = (source / 'pokeemerald.gba').read_bytes()
        assert len(rom) == 33554432 and rom[-4096:] == b'\xff' * 4096
        assert rom[0xBD] == (-sum(rom[0xA0:0xBD])-0x19) & 255
        rom_sha, elf_sha = hashlib.sha256(rom).hexdigest(), digest(source / 'pokeemerald.elf')
        assert rom_sha != PARENT_ROM_SHA256, 'The resource overlay was not compiled'
        nm = subprocess.check_output([str(ROOT / '.local/arm-binutils/usr/bin/arm-none-eabi-nm'),
                                      '-S', '--defined-only', str(source / 'pokeemerald.elf')], text=True)
        symbols = {name: (int(address, 16), int(size, 16) if size else 0)
                   for address, size, name in re.findall(
                       r'^([\da-fA-F]+)\s+(?:([\da-fA-F]+)\s+)?\w\s+(\S+)$', nm, re.M)}
        layouts = json.loads((source / 'data/layouts/layouts.json').read_bytes())['layouts']
        for name in outputs:
            if not name.endswith(('/map.bin', '/border.bin')):
                continue
            border = name.endswith('/border.bin')
            key = 'border_filepath' if border else 'blockdata_filepath'
            matches = [layout for layout in layouts if layout[key] == name]
            assert len(matches) == 1, name
            layout = matches[0]
            symbol = layout['name'] + ('_Border' if border else '_Blockdata')
            assert symbol in symbols, ('Missing compiled blockdata symbol', name, symbol)
            address, size = symbols[symbol]
            raw = (source / name).read_bytes()
            dimensions = ((layout.get('border_width', 2), layout.get('border_height', 2))
                          if border else (layout['width'], layout['height']))
            assert len(raw) == dimensions[0] * dimensions[1] * 2
            assert size in (0, len(raw)) and rom[address-0x08000000:address-0x08000000+len(raw)] == raw, name
            checked_blocks.append(dict(file=name, symbol=symbol, bytes=len(raw), sha256=digest(source / name)))
    report = dict(passed=not preflight, preflight=bool(preflight), compiled_rom=not preflight,
                  kind='generated-world-source', rom_sha256=rom_sha, elf_sha256=elf_sha,
                  parent_rom_sha256=PARENT_ROM_SHA256, layers=PRIOR + [LAYER],
                  changed_files=sorted(outputs), prepared_sha256=outputs,
                  source_hashes_checked=len(expected | outputs), independent_replay=True, idempotent=True,
                  unrelated_source_files_unchanged=True, atlas_graphics_unchanged=True,
                  campaign_and_save_abi_source_unchanged=True, compiled_blockdata=checked_blocks,
                  full_campaign_playthrough=False)
    verify_parent(baseline)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--preflight', action='store_true')
    args = parser.parse_args()
    print(json.dumps(validate(args.source, args.baseline, args.output, args.preflight), indent=2))
