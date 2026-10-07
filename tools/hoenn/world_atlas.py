#!/usr/bin/env python3
"""Reconstruct native town maps and a truthful web atlas; no ROM changes."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import urllib.request

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PIN = '731ad5bfd6e6f265508d0efcca0ba42f9dcf5881'
PANELS = [
    ('kanto', 'Kanto', 32, 80, 440, 300),
    ('sevii_123', 'Sevii · ilhas 1–3', 520, 80, 352, 240),
    ('sevii_45', 'Sevii · ilhas 4–5', 904, 80, 352, 240),
    ('sevii_67', 'Sevii · ilhas 6–7', 904, 400, 352, 240),
    ('hoenn', 'Hoenn · cartografia de Emerald', 32, 450, 560, 300),
]
ISLANDS = ['ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN']
PORT_IDS = ['MAPSEC_VERMILION_CITY'] + ['MAPSEC_' + n + '_ISLAND' for n in ISLANDS] + ['MAPSEC_BIRTH_ISLAND_FRLG', 'MAPSEC_NAVEL_ROCK_FRLG']
KANTO_CITIES = ['PALLET_TOWN', 'VIRIDIAN_CITY', 'PEWTER_CITY', 'CERULEAN_CITY',
    'LAVENDER_TOWN', 'VERMILION_CITY', 'CELADON_CITY', 'FUCHSIA_CITY',
    'CINNABAR_ISLAND', 'INDIGO_PLATEAU', 'SAFFRON_CITY']


def palette(raw):
    lines = raw.decode().splitlines()
    if lines[:2] != ['JASC-PAL', '0100']: raise ValueError('Not a JASC palette')
    colors = [tuple(map(int, line.split())) for line in lines[3:] if line.strip()]
    if len(colors) != int(lines[2]): raise ValueError('Wrong palette length')
    return colors


def render(tilemap, tiles, colors, bits, width, crop, affine=False):
    entry_bytes = 1 if affine else 2
    if len(tilemap) % (width * entry_bytes): raise ValueError('Invalid tilemap dimensions')
    height = len(tilemap) // (width * entry_bytes)
    result = Image.new('RGB', (width * 8, height * 8))
    entries = tilemap if affine else struct.unpack('<' + 'H' * (len(tilemap) // 2), tilemap)
    for cell, entry in enumerate(entries):
        tile, bank = entry & 1023, entry >> 12
        if (tile + 1) * (8 * bits) > len(tiles): raise ValueError(f'Invalid tile {tile}')
        for y in range(8):
            for x in range(8):
                tx = 7 - x if entry & 0x400 else x
                ty = 7 - y if entry & 0x800 else y
                pixel = ty * 8 + tx
                if bits == 4:
                    color = (tiles[tile * 32 + pixel // 2] >> ((pixel % 2) * 4)) & 15
                    color += 16 * bank
                else:
                    color = tiles[tile * 64 + pixel]
                if color >= len(colors): raise ValueError('Palette index out of range')
                result.putpixel((cell % width * 8 + x, cell // width * 8 + y), colors[color])
    return result.crop(crop)


def png_tiles(raw):
    image = Image.open(io.BytesIO(raw))
    if image.mode != 'P' or image.width % 8 or image.height % 8:
        raise ValueError('Expected indexed 8x8 tile sheet')
    return bytes(image.getpixel((left + x, top + y))
                 for top in range(0, image.height, 8) for left in range(0, image.width, 8)
                 for y in range(8) for x in range(8))


def build(source, output):
    output.mkdir(parents=True, exist_ok=True)
    assets = output / 'atlas'; assets.mkdir(exist_ok=True)
    hashes = {}

    def local(path):
        data = (source / path).read_bytes(); hashes['leafgreen/' + path] = hashlib.sha256(data).hexdigest()
        return data

    def emerald(path):
        url = f'https://raw.githubusercontent.com/pret/pokeemerald/{PIN}/{path}'
        with urllib.request.urlopen(url, timeout=30) as response: data = response.read()
        hashes['emerald/' + path] = hashlib.sha256(data).hexdigest()
        return data

    colors = palette(local('graphics/region_map/region_map.pal'))
    tiles = local('graphics/region_map/region_map.4bpp')
    for name in ['kanto', 'sevii_123', 'sevii_45', 'sevii_67']:
        render(local(f'graphics/region_map/{name}.bin'), tiles, colors, 4, 30,
               (32, 32, 208, 152)).save(assets / f'{name}.png')
    # Hoenn is the actual Emerald PokéNav tilemap, not an invented continent.
    hoenn_map = emerald('graphics/pokenav/region_map/map.bin')
    render(hoenn_map, png_tiles(emerald('graphics/pokenav/region_map/map.png')),
           [(0, 0, 0)] * 0x70 + palette(emerald('graphics/pokenav/region_map/map.pal')), 8, 64,
           (8, 16, 232, 136), affine=True).save(assets / 'hoenn.png')
    kanto_sections = json.loads(local('src/data/region_map/region_map_sections.json'))['map_sections']
    hoenn_sections = json.loads(emerald('src/data/region_map/region_map_sections.json'))['map_sections']
    panels = [dict(id=n, name=label, x=x, y=y, width=w, height=h,
                   image=f'atlas/{n}.png', status='planned' if n == 'hoenn' else 'playable')
              for n, label, x, y, w, h in PANELS]
    by_panel = {p['id']: p for p in panels}
    ports = json.loads((ROOT / 'mods/sea-routes/routes.json').read_text())['routes']
    points = []

    def point(section, panel_id, port_index=None):
        panel = by_panel[panel_id]; scale = panel['width'] / (224 if panel_id == 'hoenn' else 176)
        px = (section['x'] + section.get('width', 1) / 2) * 8
        py = (section['y'] + section.get('height', 1) / 2) * 8
        points.append(dict(id=section['id'], name=section['name'].title(), panel=panel_id,
            x=panel['x'] + px * scale, y=panel['y'] + py * scale,
            status=panel['status'], port_index=port_index,
            map=ports[port_index]['port'] if port_index is not None else None))

    for section in kanto_sections:
        name = section['id']
        if name in ['MAPSEC_' + n for n in KANTO_CITIES] + ['MAPSEC_ROUTE_21']: point(section, 'kanto', PORT_IDS.index(name) if name in PORT_IDS else None)
        elif name in PORT_IDS:
            index = PORT_IDS.index(name)
            panel_id = 'sevii_123' if index <= 3 else 'sevii_45' if index in [4, 5, 9] else 'sevii_67'
            point(section, panel_id, index)
    for section in hoenn_sections[:16]: point(section, 'hoenn')
    point(next(s for s in hoenn_sections if s['id'] == 'MAPSEC_ROUTE_127'), 'hoenn')
    # Consecutive ports correspond to the east/west seams in the shipped ROM.
    links = [dict(id=f'sea-{i:02d}-{i+1:02d}', source=PORT_IDS[i], target=PORT_IDS[i + 1],
                  status='playable', mode='Surf', maps=[ports[i]['name'], ports[i + 1]['name']])
             for i in range(len(PORT_IDS) - 1)]
    links += [dict(id='hoenn-surf', source='MAPSEC_ROUTE_21', target='MAPSEC_ROUTE_127', status='planned', mode='Surf'),
              dict(id='hoenn-ferry', source=PORT_IDS[0], target='MAPSEC_SLATEPORT_CITY', status='planned', mode='Barco com ticket')]
    report = dict(title='Atlas da jornada', width=1288, height=810, panels=panels, points=points, links=links,
        projection='Native regional maps arranged as an atlas; inter-panel links are schematic, not ocean distances.',
        hoenn_story_integrated=False, emerald_source_commit=PIN,
        generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        sea_rom_sha256=json.loads((ROOT / 'mods/sea-routes/manifest.json').read_text())['target_sha256'],
        input_sha256=hashes,
        output_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(assets.glob('*.png'))})
    (output / 'world-map.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f'Built {len(panels)} native maps, {len(points)} places, {len(links)} connections; Hoenn remains preview only.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'web')
    args = parser.parse_args(); build(args.source, args.output)
