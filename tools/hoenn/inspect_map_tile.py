"""Inspect real map blocks, height, collision, layers and graphic references."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

from PIL import ImageDraw

from render_sea_maps import MapRenderer


def inspect(source, name, x, y, radius=2, output=None):
    source = Path(source)
    renderer = MapRenderer(source)
    mapping = json.loads((source / f'data/maps/{name}/map.json').read_text())
    layout = renderer.layouts[mapping['layout']]
    width, height = layout['width'], layout['height']
    if not (0 <= x < width and 0 <= y < height):
        raise ValueError(f'{name}: ({x},{y}) outside {width}x{height}')
    if not 0 <= radius <= 8:
        raise ValueError('radius must be between 0 and 8')
    raw = (source / layout['blockdata_filepath']).read_bytes()
    values = struct.unpack('<' + 'H' * (width * height), raw)
    frlg = layout['layout_version'] == 'frlg'
    cutoff, attribute_size = (640, 4) if frlg else (512, 2)
    tables = {}
    for field in ('primary_tileset', 'secondary_tileset'):
        symbol = layout[field]
        body = re.search(r'const struct Tileset ' + re.escape(symbol) +
                         r'\s*=\s*\{(.*?)\};', renderer.headers, re.S)[1]
        attribute = re.search(r'\.metatileAttributes\s*=\s*(\w+)', body)[1]
        attribute_path = re.search(r'\b' + attribute + r'\[\].*?"([^"]+)"', renderer.metas)[1]
        tables[field] = (renderer.tileset(symbol)[2], (source / attribute_path).read_bytes())

    cells = []
    for yy in range(max(0, y - radius), min(height, y + radius + 1)):
        for xx in range(max(0, x - radius), min(width, x + radius + 1)):
            value = values[yy * width + xx]
            mid = value & 1023
            field = 'primary_tileset' if mid < cutoff else 'secondary_tileset'
            index = mid if mid < cutoff else mid - cutoff
            words, attributes = tables[field]
            attribute = int.from_bytes(attributes[index * attribute_size:(index + 1) * attribute_size], 'little')
            graphics = []
            for word in words[index * 8:(index + 1) * 8]:
                tile = word & 1023
                channel = None
                if frlg:
                    if 416 <= tile < 464:
                        channel = 'native water/current/land edge'
                    elif 464 <= tile < 482:
                        channel = 'native sand edge'
                else:
                    if 432 <= tile < 462:
                        channel = 'native water'
                    elif 464 <= tile < 474:
                        channel = 'native sand edge'
                    elif 480 <= tile < 490:
                        channel = 'native land edge'
                graphics.append(dict(word=f'0x{word:04X}', tile=tile, palette=word >> 12,
                                     flip_x=bool(word & 1024), flip_y=bool(word & 2048),
                                     native_animation_channel=channel))
            cells.append(dict(position=[xx, yy], block=f'0x{value:04X}',
                              metatile=f'0x{mid:03X}', elevation=value >> 12,
                              collision=(value >> 10) & 3, tileset=layout[field],
                              attribute=f'0x{attribute:0{attribute_size * 2}X}',
                              behavior=attribute & (511 if frlg else 255),
                              draw_layer=(attribute >> (29 if frlg else 12)) & 3,
                              graphics=graphics))
    result = dict(map=name, position=[x, y], layout_version=layout['layout_version'],
                  dimensions=[width, height], blockdata=layout['blockdata_filepath'],
                  blockdata_sha256=hashlib.sha256(raw).hexdigest(),
                  connections=mapping.get('connections'), cells=cells,
                  note='Source inspection, not native movement or animation proof. '
                       'Check private animation callbacks separately.')
    if output:
        output = Path(output)
        output.mkdir(parents=True, exist_ok=True)
        image, _ = renderer.render(name)
        image.save(output / 'whole-source.png')
        bounds = (max(0, x-radius), max(0, y-radius), min(width, x+radius+1), min(height, y+radius+1))
        crop = image.crop(tuple(v*16 for v in bounds)).resize(
            ((bounds[2]-bounds[0])*96, (bounds[3]-bounds[1])*96), resample=0)
        draw = ImageDraw.Draw(crop)
        for cell in cells:
            xx, yy = cell['position']
            left, top = (xx-bounds[0])*96, (yy-bounds[1])*96
            draw.rectangle((left, top, left+95, top+95), outline='yellow' if [xx, yy] == [x, y] else '#888888')
            draw.rectangle((left+1, top+1, left+88, top+25), fill='black')
            draw.text((left+3, top+2), f'{xx},{yy} {cell["block"]}\nh{cell["elevation"]} c{cell["collision"]} l{cell["draw_layer"]}', fill='white')
        crop.save(output / 'tile-source-grid.png')
        (output / 'tile.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--map', required=True)
    parser.add_argument('--x', type=int, required=True)
    parser.add_argument('--y', type=int, required=True)
    parser.add_argument('--radius', type=int, default=2)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = inspect(args.source, args.map, args.x, args.y, args.radius, args.output)
    if args.output:
        print(args.output / 'tile.json')
    else:
        print(json.dumps(report, indent=2))
