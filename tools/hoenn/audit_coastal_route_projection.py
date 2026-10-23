"""Independently compare seven source GPS grids on the unchanged compiled atlas.

These diagrams are source-data plots, never emulator screenshots. This audit
intentionally does not import the repair helper or trust its metadata.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

import numpy as np
from PIL import Image, ImageDraw

TARGETS = tuple(island + 'Island_Harbor_Frlg' for island in ('One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven'))
IDS = tuple('MAP_' + island + '_ISLAND_HARBOR' for island in ('ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN'))


def array(header, symbol):
    return list(map(int, re.search(symbol + r'\[\] = \{([^}]+)', header)[1].split(',')))


def read(source):
    header = (source / 'src/data/journey_world_position.h').read_text()
    packed = np.array(array(header, 'sWorldNavigationPixels'), dtype=np.int32)
    rows = {}
    maps = {path.parent.name: json.loads(path.read_text()) for path in (source / 'data/maps').glob('*/map.json')}
    by_id = {data['id']: name for name, data in maps.items()}
    for start, ident, width, height in re.findall(r'\{(\d+), \(MAP_GROUP\((\w+)\)<<8\)\|MAP_NUM\(\2\), (\d+), (\d+)\}', header):
        start, width, height = map(int, (start, width, height))
        values = packed[start:start + width * height].reshape(height, width)
        rows[by_id[ident]] = dict(first=start, id=ident, width=width, height=height,
                                 pixels=np.stack([values & 255, values >> 8], axis=2))
    return header, packed, rows, maps, by_id


def atlas(header):
    tiles, tilemap, palette = (array(header, symbol) for symbol in ('sWorldTiles', 'sWorldTilemap', 'sWorldPalette'))
    colors = [tuple(((word >> shift) & 31) * 255 // 31 for shift in (0, 5, 10)) for word in palette]
    image = Image.new('RGB', (224, 112))
    for y in range(112):
        for x in range(224):
            entry = tilemap[(y // 8 + 3) * 32 + x // 8 + 1]
            xx, yy = (7 - x % 8 if entry & 0x400 else x % 8), (7 - y % 8 if entry & 0x800 else y % 8)
            byte = tiles[(entry & 1023) * 32 + yy * 4 + xx // 2]
            color = (byte >> ((xx % 2) * 4)) & 15
            image.putpixel((x, y), colors[(entry >> 12) * 16 + color])
    return image


def crossings(pixels):
    result = []
    for name, values in [('east', pixels[6]), ('south', pixels[:, 8])]:
        delta = values[-1] - values[0]
        main = int(np.argmax(abs(delta)))
        sign = int(np.sign(delta[main]))
        backwards = -np.minimum(np.diff(values[:, main]) * sign, 0).sum()
        minor = 1 - main
        low, high = sorted([int(values[0, minor]), int(values[-1, minor])])
        detour = max(0, low - int(values[:, minor].min()), int(values[:, minor].max()) - high)
        result.append(dict(direction=name, primary_axis='xy'[main], primary_direction=sign,
                           backward_pixels=int(backwards), maximum_minor_axis_excursion=detour,
                           pixels=values.tolist()))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--after', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    before_h, before_p, before, maps, by_id = read(args.before)
    after_h, after_p, after, final_maps, final_by_id = read(args.after)
    assert before_p.shape == after_p.shape
    assert re.sub(r'sWorldNavigationPixels\[\] = \{[^}]+', '', before_h) == re.sub(r'sWorldNavigationPixels\[\] = \{[^}]+', '', after_h)
    before_world = (args.before / 'src/data/journey_world_map.h').read_text()
    after_world = (args.after / 'src/data/journey_world_map.h').read_text()
    atlas_hashes = {}
    for symbol in ('sWorldTiles', 'sWorldTilemap', 'sWorldPalette'):
        old = re.search(symbol + r'\[\] = \{[^}]+\}', before_world)[0]
        new = re.search(symbol + r'\[\] = \{[^}]+\}', after_world)[0]
        assert old == new, symbol
        atlas_hashes[symbol] = hashlib.sha256(old.encode()).hexdigest()
    image = atlas(after_world)
    image.resize((1344, 672), Image.Resampling.NEAREST).save(args.output / 'unchanged-atlas-source.png')
    records, seam_count, changed = [], 0, set()
    for name, ident in zip(TARGETS, IDS):
        old, new = before[name]['pixels'], after[name]['pixels']
        assert before[name]['id'] == after[name]['id'] == ident
        assert old.shape == new.shape == (13, 17, 2)
        assert maps[name]['connections'] == final_maps[name]['connections']
        for connection in maps[name]['connections']:
            other = by_id[connection['map']]
            direction, offset = connection['direction'], connection['offset']
            other_grid = before[other]
            oh, ow, _ = other_grid['pixels'].shape
            for t in range(max(0, offset), min(13 if direction in ('left', 'right') else 17,
                                             offset + (oh if direction in ('left', 'right') else ow))):
                x, y = ((0 if direction == 'left' else 16), t) if direction in ('left', 'right') else (t, 0 if direction == 'up' else 12)
                xx, yy = ((ow - 1 if direction == 'left' else 0), t - offset) if direction in ('left', 'right') else (t - offset, oh - 1 if direction == 'up' else 0)
                assert np.array_equal(old[y, x], new[y, x]), (name, other, 'changed shared edge')
                assert np.array_equal(new[y, x], after[other]['pixels'][yy, xx]), (name, other, 'seam mismatch')
            seam_count += 1
        maximum = max(int(abs(np.diff(new, axis=0)).max()), int(abs(np.diff(new, axis=1)).max()))
        assert maximum <= 2
        old_lines, new_lines = crossings(old), crossings(new)
        assert all(row['backward_pixels'] == 0 for row in new_lines)
        changed.update(range(before[name]['first'], before[name]['first'] + 221))
        # Each panel shows exactly the same atlas crop; colored traces represent
        # eastward (magenta) and southward (yellow) local controller paths.
        points = np.concatenate([old.reshape(-1, 2), new.reshape(-1, 2)])
        x0, y0 = np.maximum(points.min(axis=0) - 4, 0)
        x1, y1 = np.minimum(points.max(axis=0) + 5, [224, 112])
        scale = 14
        crop = image.crop((int(x0), int(y0), int(x1), int(y1))).resize((int(x1-x0)*scale, int(y1-y0)*scale), Image.Resampling.NEAREST)
        canvas = Image.new('RGB', (crop.width * 2 + 24, crop.height + 62), '#142230')
        draw = ImageDraw.Draw(canvas)
        for side, (label, values, lines) in enumerate([('BEFORE', old, old_lines), ('AFTER', new, new_lines)]):
            offset_x = side * (crop.width + 24)
            canvas.paste(crop, (offset_x, 44))
            draw.text((offset_x + 4, 4), name.removesuffix('Island_Harbor_Frlg').upper() + ' ISLAND COAST / ' + label, fill='white')
            draw.text((offset_x + 4, 20), 'E back=%d / S back=%d pixels' % tuple(row['backward_pixels'] for row in lines), fill='white')
            for line, color in zip(lines, ('#ff40e0', '#ffff40')):
                coords = [(offset_x + int(x-x0)*scale + scale//2, 44 + int(y-y0)*scale + scale//2) for x, y in line['pixels']]
                draw.line(coords, fill=color, width=3)
                for x, y in coords:
                    draw.ellipse((x-2, y-2, x+2, y+2), fill=color)
        draw.text((4, canvas.height - 15), 'SOURCE GPS PLOT on unchanged atlas; magenta=east, yellow=south', fill='white')
        filename = name.replace('_Harbor_Frlg', '').lower() + '-gps-before-after.png'
        canvas.save(args.output / filename)
        records.append(dict(map=name, id=ident, changed_cells=int(np.any(old != new, axis=2).sum()),
                            maximum_neighbor_pixel_step=maximum, before_crossings=old_lines,
                            after_crossings=new_lines, source_plot=filename))
    assert seam_count == 25
    assert all(index in changed for index in np.flatnonzero(before_p != after_p))
    report = dict(passed=True, kind='coastal-route-projection-source-audit',
                  source_data_plots_not_emulator_captures=True, atlas_arrays_unchanged=True,
                  atlas_arrays_sha256=atlas_hashes, all_other_grids_bitwise_unchanged=True,
                  shared_connections=25, all_shared_border_pixels_bitwise_unchanged=True,
                  maximum_seam_delta=0, maximum_neighbor_pixel_step=2,
                  all_central_crossings_primary_axis_monotonic=True,
                  changed_cells=int(np.count_nonzero(before_p != after_p)), maps=records)
    (args.output / 'route-projection-source-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'maps'}, indent=2))


if __name__ == '__main__':
    main()
