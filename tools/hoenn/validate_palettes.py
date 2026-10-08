"""Load every enabled species' normal/shiny palette through native ARM LoadPalette."""
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
options = parser.parse_args()
sys.argv = [sys.argv[0], '--source', str(options.source), '--library', str(options.library),
            '--output', str(options.output)]
bootstrap = (ROOT / 'tools/hoenn/validate_abilities.py').read_text().split('\nability_field,')[0]
exec(compile(bootstrap, str(ROOT / 'tools/hoenn/validate_abilities.py'), 'exec'))
catalog = audit(source)
rom = (source / 'pokeemerald.gba').read_bytes()
abi_catalog = catalog['compiled_abi']
paths = {}
for name, path in re.findall(r'const u16 (\w+)\[\] = INCBIN_U16\("([^"]+)"\)',
                             (source / 'src/data/graphics/pokemon.h').read_text()):
    paths.setdefault(name, []).append(path)
by_pointer = {address: paths[name] for name, address in s.items() if name in paths}
with tempfile.TemporaryDirectory(prefix='female-palette-abi-', dir='/tmp') as directory:
    temp = Path(directory)
    (temp / 'abi.c').write_text('#include "global.h"\n#include "pokemon.h"\n#include <stddef.h>\n'
                              'const unsigned fields[] = {offsetof(struct SpeciesInfo, paletteFemale),'
                              'offsetof(struct SpeciesInfo, shinyPaletteFemale), offsetof(struct SpeciesInfo, frontPicFemale),'
                              'offsetof(struct SpeciesInfo, backPicFemale)};\n')
    subprocess.run([str(ROOT / '.local/arm-gcc/usr/bin/arm-none-eabi-gcc'), '-S', '-iquote', str(source / 'include'),
                    '-DMODERN=1', '-DPOKEEMERALD', '-mthumb', '-march=armv4t', '-mabi=apcs-gnu',
                    str(temp / 'abi.c'), '-o', str(temp / 'abi.s')], check=True)
    female_offsets = [int(n) for n in re.findall(r'\.word\s+(\d+)', (temp / 'abi.s').read_text())]
picture_paths = {}
for name, path in re.findall(r'const u32 (\w+)\[\] = INCBIN_U32\("([^"]+)"\)',
                             (source / 'src/data/graphics/pokemon.h').read_text()):
    picture_paths.setdefault(name, []).append(path)
pictures_by_pointer = {address: picture_paths[name] for name, address in s.items() if name in picture_paths}
def max_picture_color(pointer):
    for path in pictures_by_pointer[pointer]:
        compressed = source / path
        if compressed.exists():
            at = pointer - 0x08000000
            data = compressed.read_bytes()
            if rom[at:at + len(data)] == data:
                pixels = (source / re.sub(r'\.(smol|lz)$', '', path)).read_bytes()
                return max(max(byte & 15, byte >> 4) for byte in pixels)
    raise AssertionError(('picture source not found', hex(pointer)))
checks = []
buffer = s['gPlttBufferUnfaded'] + 480 * 2
for key, row in catalog['species'].items():
    species_at = s['gSpeciesInfo'] - 0x08000000 + int(key) * abi_catalog[0]
    picture_colors = [max_picture_color(struct.unpack_from('<I', rom, species_at + offset)[0])
                      for offset in [abi_catalog[1], abi_catalog[2], *female_offsets[2:]]
                      if struct.unpack_from('<I', rom, species_at + offset)[0]]
    for asset, offset in [('normal', abi_catalog[3]), ('shiny', abi_catalog[4]),
                          ('normal_female', female_offsets[0]), ('shiny_female', female_offsets[1])]:
        pointer = struct.unpack_from('<I', rom, s['gSpeciesInfo'] - 0x08000000 + int(key) * abi_catalog[0] + offset)[0]
        if not pointer and asset.endswith('_female'):
            continue
        assert pointer in by_pointer, (row['name'], asset, hex(pointer))
        expected = None
        for path in by_pointer[pointer]:
            original = source / path
            if original.exists():
                data = original.read_bytes()
                at = pointer - 0x08000000
                if rom[at:at + len(data)] == data:
                    expected = data
                    break
        assert expected is not None and 0 < len(expected) <= 32 and len(expected) % 2 == 0, (row['name'], asset)
        before, after = lib.read16(buffer - 2), lib.read16(buffer + 32)
        native('LoadPalette', pointer, 480, 32)
        actual = bytes(lib.read8(buffer + i) for i in range(32))
        assert actual == rom[pointer - 0x08000000:pointer - 0x08000000 + 32]
        assert actual[:len(expected)] == expected, (row['name'], asset)
        assert max(picture_colors) < len(expected) // 2, (row['name'], asset, 'palette too short')
        assert lib.read16(buffer - 2) == before and lib.read16(buffer + 32) == after
        checks.append(dict(species=row['id'], name=row['name'], asset=asset,
                           bytes=32, original_colors=len(expected) // 2, highest_picture_color=max(picture_colors), sha256=hashlib.sha256(actual).hexdigest()))
    if int(key) % 100 == 0:
        print('Native palettes verified:', len(checks), flush=True)
lib.stop()
result = dict(passed=True, rom_sha256=catalog['rom_sha256'], species=len({r['species'] for r in checks}),
              palettes=len(checks), native_palette_loader_matches_build=True, adjacent_colors_preserved=True, all_picture_indices_fit_palettes=True,
              all_battle_animations_validated=False, checks=checks)
# Keep per-asset evidence on one line so reviewers can inspect the summary.
header = json.dumps({k: v for k, v in result.items() if k != 'checks'}, indent=2)[:-2]
report_text = header + ',\n  "checks": [\n' + ',\n'.join(
    '    ' + json.dumps(row) for row in checks) + '\n  ]\n}\n'

(args.output / 'palette-loader.json').write_text(report_text)
print({k: v for k, v in result.items() if k != 'checks'}, flush=True)
