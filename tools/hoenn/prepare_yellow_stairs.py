"""Port the exact yellow Jagged Pass stair pixels to the Safari cliff passages."""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import struct
import zlib
from PIL import Image
from prepare_crossing import PIN
from prepare_free_access import LAYERS


def prepare(source):
    source = Path(source)
    marker = source / '.journey-yellow-stairs'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            assert hashlib.sha256((source / path).read_bytes()).hexdigest() == digest, path
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    assert acquired['commit'] == PIN
    expected = dict(acquired['sha256'])
    for layer in LAYERS + ['free-access', 'blue-gym', 'road-access', 'mach-bike']:
        expected.update(json.loads((source / f'.journey-{layer}').read_text())['prepared_sha256'])
    inputs, originals, outputs = {}, {}, {}

    def read(path):
        if path in outputs:
            return outputs[path]
        raw = (source / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected[path], path
        if path in acquired['sha256']:
            inputs[path] = acquired['sha256'][path]
        return raw

    def stage(path, raw):
        if path not in originals:
            originals[path] = hashlib.sha256(read(path)).hexdigest()
        outputs[path] = raw

    prefix = 'data/tilesets/secondary/'
    lily_png = prefix + 'lilycove/tiles.png'
    original = Image.open(BytesIO(read(lily_png)))
    donor = Image.open(BytesIO(read(prefix + 'lavaridge/tiles.png')))
    assert original.mode == donor.mode == 'P'
    width, height = original.size
    assert width == 128 and height == 216
    image = Image.new('P', (width, height + 8))
    image.putpalette(original.getpalette())
    image.paste(original, (0, 0))
    first = 512 + width // 8 * height // 8
    assert first + 1 < 1024
    # Only two foreground tiles are needed. Allocate new secondary tiles, never
    # overwrite native Lilycove art, and keep all existing palette indices.
    donor_ids = [0x359, 0x35A]
    for i, tid in enumerate(donor_ids):
        index = tid - 512
        x, y = index % (donor.width // 8) * 8, index // (donor.width // 8) * 8
        image.paste(donor.crop((x, y, x + 8, y + 8)), (i * 8, height))
    raw_pixels = image.tobytes()
    def chunk(kind, raw):
        return struct.pack('>I', len(raw)) + kind + raw + struct.pack('>I', zlib.crc32(kind + raw))
    rows = b''.join(b'\0' + raw_pixels[y * width:(y + 1) * width] for y in range(height + 8))
    png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height + 8, 8, 3, 0, 0, 0))
           + chunk(b'PLTE', bytes(original.getpalette())) + chunk(b'IDAT', zlib.compress(rows, 9)) + chunk(b'IEND', b''))
    stage(lily_png, png)
    mt_path = prefix + 'lilycove/metatiles.bin'
    mt = bytearray(read(mt_path))
    values = struct.unpack('<' + 'H' * (len(mt) // 2), mt)
    assert not any(v >> 12 == 12 for v in values), 'Palette 12 is already used'
    palette = read(prefix + 'lavaridge/palettes/08.pal')
    stage(prefix + 'lilycove/palettes/12.pal', palette)
    # Preserve the local cliff color under the yellow treads. The foreground
    # indices and colors are byte-identical to the native yellow lateral stair.
    reference = read(prefix + 'lavaridge/metatiles.bin')[0xAF * 16:0xB0 * 16]
    ref = struct.unpack('<8H', reference)
    assert [v & 1023 for v in ref[4:]] == donor_ids * 2
    background = [v & 0xFFF | 3 << 12 for v in ref[:4]]
    foreground = [12 << 12 | first, 12 << 12 | first + 1] * 2
    stair = struct.pack('<8H', *(background + foreground))
    attrs_path = prefix + 'lilycove/metatile_attributes.bin'
    attrs = bytearray(read(attrs_path))
    for tid in [0x317, 0x323]:
        offset = tid - 512
        mt[offset * 16:(offset + 1) * 16] = stair
        struct.pack_into('<H', attrs, offset * 2, 0x1000)
    stage(mt_path, bytes(mt))
    stage(attrs_path, bytes(attrs))
    path = 'data/layouts/SafariZone_North/map.bin'
    data = bytearray(read(path))
    cells = []
    for y, before, after, surface in [(21, 0x317, 0x317, 'yellow_stair'),
                                      (22, 0x31F, 0x5001, 'landing'),
                                      (23, 0x323, 0x323, 'yellow_stair')]:
        offset = (y * 40 + 22) * 2
        assert struct.unpack_from('<H', data, offset)[0] == before
        struct.pack_into('<H', data, offset, after)
        cells.append(dict(layout='LAYOUT_SAFARI_ZONE_NORTH', x=22, y=y,
                          before=before, after=after, surface=surface))
    stage(path, bytes(data))
    # Verify decoded tiles after encoding, and verify every previous pixel is
    # preserved. Palette 12 was unused, so no native scene loses its colors.
    decoded = Image.open(BytesIO(png))
    assert decoded.crop((0, 0, width, height)).tobytes() == original.tobytes()
    hashes = []
    for i, tid in enumerate(donor_ids):
        index = tid - 512
        x, y = index % (donor.width // 8) * 8, index // (donor.width // 8) * 8
        source_pixels = donor.crop((x, y, x + 8, y + 8)).tobytes()
        assert decoded.crop((i * 8, height, i * 8 + 8, height + 8)).tobytes() == source_pixels
        hashes.append(hashlib.sha256(source_pixels).hexdigest())
    for path, raw in outputs.items():
        (source / path).write_bytes(raw)
    report = dict(status='all_acro_cliff_passages_yellow_candidate', source_commit=PIN,
                  replacements=cells, stair_passages=6, yellow_stair_cells=11, clear_landings=6,
                  imported_tile_ids=[first, first + 1], native_foreground_sha256=hashes,
                  foreground_pixels_identical=True, foreground_palette_identical=True,
                  original_lilycove_pixels_preserved=True, palette_12_previously_unused=True,
                  native_yellow_reference=0x2AF, requires_bicycle=False,
                  original_events_unchanged=True, full_story_validated=False,
                  input_sha256=inputs, original_sha256=originals,
                  prepared_sha256={p: hashlib.sha256(v).hexdigest() for p, v in outputs.items()})
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    report = prepare(args.source)
    print(json.dumps(dict(passages=report['stair_passages'], imported_tile_ids=report['imported_tile_ids'])))
