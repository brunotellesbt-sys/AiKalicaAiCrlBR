"""Render whole source maps with a content-addressed input closure.

These are source renders, not emulator or movement proofs. A later change to
the map, layout, graphics, palette, actor definition or renderer invalidates
the corresponding record rather than silently reusing an old picture.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

from PIL import Image, ImageDraw

from audit_generated_cave_visuals import draw_map
from render_sea_maps import MapRenderer


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def actor_inputs(renderer, graphics):
    """Follow the same native sprite/palette references as MapRenderer."""
    source = renderer.source
    if graphics.startswith('OBJ_EVENT_GFX_SPECIES('):
        species = re.fullmatch(r'OBJ_EVENT_GFX_SPECIES\((\w+)\)', graphics)[1].lower()
        candidates = [source/'graphics/pokemon'/species/'overworld.png']
        pieces = species.split('_')
        candidates += [source/'graphics/pokemon'/'_'.join(pieces[:n])/'_'.join(pieces[n:])/'overworld.png'
                       for n in range(1,len(pieces))]
        return [next(p.relative_to(source).as_posix() for p in candidates if p.exists())]
    folder = source/'src/data/object_events'
    pointers = (folder/'object_event_graphics_info_pointers.h').read_text()
    symbol = re.search(r'\['+re.escape(graphics)+r'\]\s*=\s*&([A-Za-z0-9_]+)',pointers)[1]
    info = re.search(r'const struct ObjectEventGraphicsInfo '+symbol+r'\s*=\s*\{(.*?)\};',
                     (folder/'object_event_graphics_info.h').read_text(),re.S)[1]
    pic = re.search(r'\.images\s*=\s*(\w+)',info)[1]
    table = re.search(r'static const struct SpriteFrameImage '+pic+r'\[\]\s*=\s*\{(.*?)\};',
                      (folder/'object_event_pic_tables.h').read_text(),re.S)[1]
    graphic = re.search(r'(?:overworld_(?:ascending_frames|frame)|obj_frame_tiles)\((\w+)',table)[1]
    definitions = (folder/'object_event_graphics.h').read_text()
    path = re.search(r'\b'+graphic+r'\[\].*?"([^"]+)"',definitions)[1]
    palette_tag = re.search(r'\.paletteTag\s*=\s*(\w+)',info)[1]
    palette_symbol = re.search(r'\{(gObjectEventPal_\w+),\s*'+palette_tag+r'\}',
                               (source/'src/event_object_movement.c').read_text())[1]
    palette = re.search(r'\b'+palette_symbol+r'\[\].*?"([^"]+)"',definitions)[1]
    palette_file = Path(palette).with_suffix('.pal')
    if not (source/palette_file).exists():
        palette_file = Path(palette)
    return [Path(path).with_suffix('.png').as_posix(),palette_file.as_posix()]


def render(source, names, output):
    source,output = Path(source),Path(output)
    output.mkdir(parents=True,exist_ok=True)
    renderer = MapRenderer(source)
    inputs,records,panels = {},[],[]
    static = ['data/layouts/layouts.json','src/data/tilesets/headers.h','src/data/tilesets/metatiles.h',
              'src/data/object_events/object_event_graphics_info_pointers.h',
              'src/data/object_events/object_event_graphics_info.h',
              'src/data/object_events/object_event_pic_tables.h',
              'src/data/object_events/object_event_graphics.h','src/event_object_movement.c']
    if (source/'.journey-close-vertical-boats').exists():
        static.append('.journey-close-vertical-boats')
    for name in names:
        image,mapping,actors,unresolved = draw_map(renderer,name)
        layout = renderer.layouts[mapping['layout']]
        paths = set(static+[f'data/maps/{name}/map.json',layout['blockdata_filepath'],layout['border_filepath']])
        for field in ('primary_tileset','secondary_tileset'):
            symbol = layout[field]
            declaration = re.search(r'const struct Tileset '+re.escape(symbol)+r'\s*=\s*\{(.*?)\};',renderer.headers,re.S)[1]
            for prop in ('metatiles','metatileAttributes'):
                target = re.search(r'\.'+prop+r'\s*=\s*(\w+)',declaration)[1]
                filename = re.search(r'\b'+re.escape(target)+r'\[\].*?"([^"]+)"',renderer.metas)[1]
                paths.add(filename)
                if prop == 'metatiles':
                    folder = (source/filename).parent
                    paths.add((folder/'tiles.png').relative_to(source).as_posix())
                    paths.update(p.relative_to(source).as_posix() for p in (folder/'palettes').glob('*.pal'))
        for index,event in enumerate(mapping['object_events'],1):
            if index in actors:
                paths.update(actor_inputs(renderer,event['graphics_id']))
        for path in sorted(paths):
            inputs[path] = digest((source/path).read_bytes())
        closure = {path:inputs[path] for path in sorted(paths)}
        target = output/(name+'-source.png')
        image.save(target)
        records.append(dict(map=name,image=target.name,image_sha256=digest(target.read_bytes()),
                            rendered_pixels_sha256=digest(image.tobytes()),dimensions=[layout['width'],layout['height']],
                            layout=layout,layout_entry_sha256=digest(json.dumps(layout,sort_keys=True).encode()),
                            input_paths=sorted(paths),input_closure_sha256=digest(json.dumps(closure,sort_keys=True).encode()),
                            static_actors_rendered=actors,unresolved_static_actors=unresolved,
                            source_render_not_emulator=True,visually_inspected=False))
        scale = min(1,600/image.width,650/image.height)
        panels.append((name,image.resize((int(image.width*scale),int(image.height*scale)),Image.Resampling.NEAREST)))
    sheets=[]
    for start in range(0,len(panels),6):
        sheet = Image.new('RGB',(1860,1420),'#20313d')
        draw = ImageDraw.Draw(sheet)
        draw.text((10,5),'FINAL WHOLE SOURCE MAPS — NOT EMULATOR CAPTURES',fill='white')
        for offset,(name,panel) in enumerate(panels[start:start+6]):
            x,y=10+offset%3*620,30+offset//3*690
            draw.text((x,y),name,fill='white');sheet.paste(panel,(x,y+20))
        target=output/('whole-source-sheet-'+str(start//6+1).zfill(2)+'.png')
        sheet.save(target)
        sheets.append(dict(file=target.name,sha256=digest(target.read_bytes()),maps=[n for n,_ in panels[start:start+6]]))
    marker = '.journey-generated-world-audit' if (source/'.journey-generated-world-audit').exists() else '.journey-badge-story'
    report=dict(kind='generated-visual-source-provenance',source_rom_sha256=digest((source/'pokeemerald.gba').read_bytes()),
                source_marker=marker,source_marker_sha256=digest((source/marker).read_bytes()),
                input_sha256=inputs,maps=records,contact_sheets=sheets,
                renderer_sha256={name:digest((Path(__file__).parent/name).read_bytes()) for name in
                                 ['render_sea_maps.py','audit_generated_cave_visuals.py',Path(__file__).name]},
                source_render_not_emulator=True,movement_and_animation_certified=False,
                note='visually_inspected changes only after an actual image review; the manifest itself does not approve artwork.')
    (output/'source-provenance.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--maps',required=True,help='Comma-separated map directory names')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report=render(args.source,list(dict.fromkeys(args.maps.split(','))),args.output)
    print(json.dumps(dict(maps=len(report['maps']),inputs=len(report['input_sha256']),
                         rom_sha256=report['source_rom_sha256'])))
