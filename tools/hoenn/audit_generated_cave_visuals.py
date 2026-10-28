"""Render whole generated caves and non-gym rooms for explicit human review.

This records source geometry and static objects only; it makes no emulator,
collision, animation, or visual-quality pass claim.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

from PIL import Image, ImageDraw
from render_sea_maps import MapRenderer


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def creature(renderer, graphics):
    name = re.fullmatch(r'OBJ_EVENT_GFX_SPECIES\((\w+)\)', graphics)[1].lower()
    path = renderer.source / 'graphics/pokemon' / name / 'overworld.png'
    if not path.exists():
        parts = name.split('_')
        for split in range(1, len(parts)):
            candidate = renderer.source / 'graphics/pokemon' / '_'.join(parts[:split]) / '_'.join(parts[split:]) / 'overworld.png'
            if candidate.exists():
                path = candidate
                break
    original = Image.open(path)
    width = height = original.height
    assert width in (16, 32, 64, 128) and original.width >= width, (path, original.size)
    frame = original.crop((0, 0, width, height))
    result = frame.convert('RGBA')
    result.putalpha(Image.frombytes('L', frame.size, bytes(255 if i else 0 for i in frame.tobytes())))
    return result


def draw_map(renderer, name):
    image, mapping = renderer.render(name, npcs=False)
    unresolved, rendered = [], []
    for index, obj in sorted(enumerate(mapping['object_events'], 1), key=lambda row: row[1]['y']):
        graphics = obj['graphics_id']
        try:
            sprite = creature(renderer, graphics) if graphics.startswith('OBJ_EVENT_GFX_SPECIES(') else renderer.sprite(graphics)
            dx, dy = renderer.sprite_offset(graphics)
            image.paste(sprite, (obj['x'] * 16 + 8 - sprite.width // 2 + dx,
                                 obj['y'] * 16 + 16 - sprite.height + dy), sprite)
            rendered.append(index)
        except (TypeError, IndexError, KeyError, FileNotFoundError, AssertionError) as error:
            # A variable graphics selector needs a declared runtime fixture.
            # Mark it explicitly instead of silently inventing its appearance.
            unresolved.append(dict(local_id=index, graphics_id=graphics, position=[obj['x'], obj['y']],
                                   reason=type(error).__name__))
            draw = ImageDraw.Draw(image)
            draw.rectangle((obj['x'] * 16, obj['y'] * 16, obj['x'] * 16 + 15, obj['y'] * 16 + 15), outline='red')
    return image, mapping, rendered, unresolved


def run(source, output):
    source, output = Path(source), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    renderer = MapRenderer(source)
    initial = json.loads((source / '.source-acquired.json').read_text())['sha256']
    groups = {'caves': [], 'rooms': []}
    for file in sorted((source / 'data/maps').glob('*/map.json')):
        mapping = json.loads(file.read_text())
        layout = renderer.layouts[mapping['layout']]
        relative = file.relative_to(source).as_posix()
        changed_terrain = initial.get(layout['blockdata_filepath']) != sha(source / layout['blockdata_filepath'])
        if mapping['map_type'] == 'MAP_TYPE_UNDERGROUND' and changed_terrain:
            groups['caves'].append(file.parent.name)
        elif mapping['map_type'] == 'MAP_TYPE_INDOOR' and relative not in initial:
            name = file.parent.name
            if not ('Gym' in name or 'PWT' in name or 'EverGrandeHouse' in name):
                groups['rooms'].append(name)
    records, sheets = [], []
    for category, names in groups.items():
        panels = []
        for name in names:
            image, mapping, rendered, unresolved = draw_map(renderer, name)
            layout = renderer.layouts[mapping['layout']]
            target = output / (name + '-source.png')
            image.save(target)
            records.append(dict(map=name, category=category, dimensions=[layout['width'], layout['height']],
                map_sha256=sha(source / f'data/maps/{name}/map.json'),
                blockdata=layout['blockdata_filepath'], blockdata_sha256=sha(source / layout['blockdata_filepath']),
                image=target.name, image_sha256=sha(target), static_npcs_rendered=rendered,
                unresolved_static_npcs=unresolved, original_geometry=layout['blockdata_filepath'] in initial,
                source_render_not_emulator=True, human_reviewed=False))
            scale = min(1, 600 / image.width, 640 / image.height)
            panels.append((name, image.resize((int(image.width * scale), int(image.height * scale)), Image.Resampling.NEAREST), unresolved))
        for start in range(0, len(panels), 6):
            sheet = Image.new('RGB', (1860, 1400), '#20313d')
            draw = ImageDraw.Draw(sheet)
            draw.text((10, 6), 'SOURCE RENDERS — WHOLE MAPS — NOT EMULATOR CAPTURES', fill='white')
            for offset, (name, panel, unresolved) in enumerate(panels[start:start+6]):
                x, y = offset % 3 * 620 + 10, offset // 3 * 680 + 35
                draw.text((x, y), name + (' [VARIABLE/UNRESOLVED NPC]' if unresolved else ''), fill='white')
                sheet.paste(panel, (x, y + 22))
            target = output / (category + '-' + str(start // 6 + 1).zfill(2) + '-source-sheet.png')
            sheet.save(target)
            sheets.append(dict(file=target.name, sha256=sha(target), maps=[n for n, _, _ in panels[start:start+6]]))
    report = dict(source_rom_sha256=sha(source / 'pokeemerald.gba'), maps=records, contact_sheets=sheets,
                  source_render_not_emulator=True, visual_quality_certified=False,
                  limitations=['Static source sprites do not model state visibility or runtime palettes.',
                               'Variable graphics are marked red and require native review.',
                               'Walking, Surf, collision and animation are separate native checks.'])
    (output / 'source-renders.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(maps=len(records), categories={k:len(v) for k,v in groups.items()},
                         unresolved=sum(bool(r['unresolved_static_npcs']) for r in records))))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    run(options.source, options.output)
