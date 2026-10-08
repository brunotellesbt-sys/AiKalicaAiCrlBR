"""Compare the native ARM sprite decoder with the build's original 4bpp pixels."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
from audit_native_catalog import audit

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--library', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--megas-only', action='store_true')
options = parser.parse_args()
megas_only = options.megas_only
sys.argv = [sys.argv[0], '--source', str(options.source), '--library', str(options.library),
            '--output', str(options.output), '--ability-slot', '0']
bootstrap = (ROOT / 'tools/hoenn/validate_abilities.py').read_text().split('\nability_field,')[0]
exec(compile(bootstrap, str(ROOT / 'tools/hoenn/validate_abilities.py'), 'exec'))
catalog = audit(source)
rom = (source / 'pokeemerald.gba').read_bytes()
abi_catalog = catalog['compiled_abi']
paths = {}
for name, path in re.findall(r'const u32 (\w+)\[\] = INCBIN_U32\("([^"]+)"\)',
                             (source / 'src/data/graphics/pokemon.h').read_text()):
    paths.setdefault(name, []).append(path)
by_pointer = {address: paths[name] for name, address in s.items() if name in paths}
records = []
with tempfile.TemporaryDirectory(prefix='female-pic-abi-', dir='/tmp') as directory:
    temp = Path(directory)
    (temp / 'abi.c').write_text('#include "global.h"\n#include "pokemon.h"\n#include <stddef.h>\n'
                              'const unsigned fields[] = {offsetof(struct SpeciesInfo, frontPicFemale),'
                              'offsetof(struct SpeciesInfo, backPicFemale)};\n')
    subprocess.run([str(ROOT / '.local/arm-gcc/usr/bin/arm-none-eabi-gcc'), '-S', '-iquote', str(source / 'include'),
                    '-DMODERN=1', '-DPOKEEMERALD', '-mthumb', '-march=armv4t', '-mabi=apcs-gnu',
                    str(temp / 'abi.c'), '-o', str(temp / 'abi.s')], check=True)
    female_offsets = [int(n) for n in re.findall(r'\.word\s+(\d+)', (temp / 'abi.s').read_text())]
for key, row in catalog['species'].items():
    if megas_only and not row['flags'] & (1 << 6):
        continue
    for asset, offset in [('front', abi_catalog[1]), ('back', abi_catalog[2]),
                          ('front_female', female_offsets[0]), ('back_female', female_offsets[1])]:
        pointer = struct.unpack_from('<I', rom, s['gSpeciesInfo'] - 0x08000000 + int(key) * abi_catalog[0] + offset)[0]
        if not pointer and asset.endswith('_female'):
            continue
        assert pointer in by_pointer, (row['name'], asset, hex(pointer))
        # Several symbols have conditional GBA/modern art declarations. Select
        # the source stream that actually appears at this ROM pointer.
        candidates = []
        for path in by_pointer[pointer]:
            compressed = source / path
            if compressed.exists():
                raw_stream = compressed.read_bytes()
                at = pointer - 0x08000000
                if rom[at:at + len(raw_stream)] == raw_stream:
                    candidates.append(path)
        assert candidates, (row['name'], asset, 'compiled art source not found')
        path = candidates[0]
        original = source / re.sub(r'\.(smol|lz)$', '', path)
        assert original.exists(), original
        expected = original.read_bytes()
        assert 2048 <= len(expected) <= 16384
        records.append((row, asset, pointer, expected))
size = max(len(expected) for row, asset, pointer, expected in records)
buffer = native('AllocZeroed_', size + 16)
assert buffer
native('DisableWildEncounters', 1)
checks = []
for row, asset, pointer, expected in records:
    lib.write32(buffer, 0xA17E5AFE)
    lib.write32(buffer + 4 + len(expected), 0xB17E5AFE)
    native('DecompressDataWithHeaderWram', pointer, buffer + 4, max_frames=6000)
    assert lib.read32(buffer) == 0xA17E5AFE
    assert lib.read32(buffer + 4 + len(expected)) == 0xB17E5AFE, (row['name'], asset, 'buffer overrun')
    decoded = bytes(lib.read8(buffer + 4 + index) for index in range(len(expected)))
    if decoded != expected:
        (args.output / 'codec-diagnostic-native.bin').write_bytes(decoded)
        (args.output / 'codec-diagnostic-expected.bin').write_bytes(expected)
        print('Decode mismatch:', row['name'], asset, hex(pointer), len(expected),
              list(decoded[:32]), list(expected[:32]),
              next((i for i, (a, b) in enumerate(zip(decoded, expected)) if a != b), None), flush=True)
    assert decoded == expected, (row['name'], asset, 'native pixels differ')
    checks.append(dict(species=row['id'], name=row['name'], asset=asset,
                       bytes=len(decoded), sha256=hashlib.sha256(decoded).hexdigest()))
    if len(checks) % 100 == 0:
        print('Native sprite pixels verified:', len(checks), flush=True)
native('Free', buffer)
lib.stop()
result = dict(passed=True, rom_sha256=catalog['rom_sha256'],
              mode='megas' if megas_only else 'all_enabled_species',
              species=len({row['species'] for row in checks}), pictures=len(checks),
              native_decoder_matches_original_pixels=True, buffer_bounds_verified=True,
              all_battle_animations_validated=False, checks=checks)
# Keep per-asset evidence on one line so reviewers can inspect the summary.
header = json.dumps({k: v for k, v in result.items() if k != 'checks'}, indent=2)[:-2]
report_text = header + ',\n  "checks": [\n' + ',\n'.join(
    '    ' + json.dumps(row) for row in checks) + '\n  ]\n}\n'

(args.output / ('sprite-codec-megas.json' if megas_only else 'sprite-codec.json')).write_text(report_text)
print({key: value for key, value in result.items() if key != 'checks'}, flush=True)
