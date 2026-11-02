"""Close the whole Kindle Road south cape across its One Island seam.

The recorded camera is Kindle Road (7,139), looking west at x0..6. Its rock
top ran into the southern map boundary without a south face. Reuse the
existing One Island southwest foot and southeast foot families, including
the water toe. The shared mountain crosses the real west connection, so
the closure includes the four adjacent town cells rather than half a cape.
"""
import hashlib
import json
from pathlib import Path
import struct

from badge_story_layer import read


TOWN = 'OneIsland_Frlg'
ROAD = 'OneIsland_KindleRoad_Frlg'
TREASURE = 'OneIsland_TreasureBeach_Frlg'
CHANGES = {
    TOWN: [(22, 18, 0x1121, 0x112C), (23, 18, 0x0473, 0x047B),
           (22, 19, 0x112C, 0x112B), (23, 19, 0x0473, 0x1123)],
    ROAD: [(x, 138, 0x0471, 0x047C) for x in range(6)]
          + [(6, 138, 0x0475, 0x047D), (7, 138, 0x112A, 0x1120)]
          + [(x, 139, 0x0471, 0x1123) for x in range(6)]
          + [(6, 139, 0x0475, 0x1123), (7, 139, 0x112A, 0x1131)],
    # This old west face continued south of the town into Treasure Beach.
    # Remove its whole face and water-edge footprint after closing the cape.
    TREASURE: [(22,0,0x112C,0x112B), (23,0,0x0473,0x112B),
               (22,1,0x112C,0x112B), (23,1,0x047B,0x112B),
               (22,2,0x1130,0x112B), (23,2,0x1123,0x112B)],
}


def repair(layer):
    layouts = {row['id']: row for row in json.loads(read(
        layer, 'data/layouts/layouts.json'))['layouts']}
    records = []
    for name, cells in CHANGES.items():
        mapping = json.loads(read(layer, f'data/maps/{name}/map.json'))
        layout = layouts[mapping['layout']]
        width, height = layout['width'], layout['height']
        assert (width, height) == (24, {TOWN:20, ROAD:140, TREASURE:40}[name]), name
        assert layout['layout_version'] == 'frlg'
        path = layout['blockdata_filepath']
        before = read(layer, path)
        words = list(struct.unpack('<' + 'H' * (width * height), before))
        # Check the complete connected footprint before staging either file.
        for x, y, expected, after in cells:
            assert words[y * width + x] == expected, (
                'Unreviewed Kindle cape input', name, x, y,
                hex(words[y * width + x]), hex(expected))
            words[y * width + x] = after
        final = struct.pack('<' + 'H' * len(words), *words)
        records.append(dict(map=name, path=path, dimensions=[width, height],
            before_sha256=hashlib.sha256(before).hexdigest(),
            after_sha256=hashlib.sha256(final).hexdigest(),
            changed_cells=[dict(position=[x,y],before=old,after=new)
                           for x,y,old,new in cells], _bytes=final))
    for record in records:
        layer.stage(record['path'], record.pop('_bytes'))
    return dict(kind='coastal-ecology-kindle-cliff', maps=records,
        changed_cells=sum(len(row['changed_cells']) for row in records),
        video_location=dict(map=ROAD, tile=[7,139], state='Surf'),
        native_donors=[dict(map=TOWN, southwest_face=[18,17],
                           southwest_water_toe=[18,18],
                           southeast_face=[2,17], southeast_water_corner=[3,18])],
        complete_face=dict(west_corner=[TOWN,23,18],
                           horizontal_face=[ROAD,0,138,6,1],
                           east_corner=[ROAD,6,138], water_toe_y=139,
                           retired_west_foot=[TREASURE,22,0,2,3]),
        native_surf_approaches=[[ROAD,7,137],[ROAD,7,138],[ROAD,7,139]],
        maps_events_warps_connections_dimensions_and_atlas_unchanged=True,
        helper_only_stages_bytes=True)


def render_review(source, output, metadata):
    """Render whole maps and their real joined southern context, using native art.

    This compares geometry using the selected source's current graphic banks;
    it is explicitly source evidence, not a capture of emulator movement.
    """
    from PIL import Image, ImageDraw
    from render_sea_maps import MapRenderer

    source, output = Path(source), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    renderer = MapRenderer(source)
    records = {row['map']: row for row in metadata['maps']}
    contexts = []
    images = []
    for state in ('before', 'after'):
        rendered = {}
        for name, record in records.items():
            raw = (source/record['path']).read_bytes()
            assert hashlib.sha256(raw).hexdigest() in (
                record['before_sha256'], record['after_sha256'])
            values = list(struct.unpack('<'+'H'*(len(raw)//2), raw))
            width, _ = record['dimensions']
            for cell in record['changed_cells']:
                x,y = cell['position']
                values[y*width+x] = cell[state]
            image, _ = renderer.render(name, values=values)
            path = output/f'{name}-{state}-whole-source.png'
            image.save(path)
            images.append(dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
            rendered[name] = image
        # The entire road, town and connected Treasure Beach. Road y120 is
        # town y0; Treasure y0 is town y20. Include the true southern border
        # water beside Treasure, exposing the previously blunt cape end.
        treasure = rendered[TREASURE]
        mapping = json.loads((source/f'data/maps/{ROAD}/map.json').read_text())
        road_layout = renderer.layouts[mapping['layout']]
        border_raw = (source/road_layout['border_filepath']).read_bytes()
        border = struct.unpack('<'+'H'*(len(border_raw)//2), border_raw)
        width, height = 48, 180
        tiles = [border[(x%road_layout['border_width'])+
                        road_layout['border_width']*(y%road_layout['border_height'])]
                 for y in range(height) for x in range(width)]
        context, _ = renderer.render(ROAD, values=tiles, dimensions=(width,height),npcs=False)
        context.paste(rendered[ROAD],(24*16,0))
        context.paste(rendered[TOWN],(0,120*16))
        context.paste(treasure,(0,140*16))
        label = Image.new('RGB',(context.width,context.height+24),'#17232b')
        label.paste(context,(0,24))
        ImageDraw.Draw(label).text((4,5),f'{state}: whole native source maps; real One/Kindle/Treasure connections',fill='white')
        path = output/f'Kindle-cape-{state}-whole-connected-source.png'
        label.save(path)
        images.append(dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        crop = context.crop((20*16,130*16,36*16,146*16))
        contexts.append(crop)
    comparison = Image.new('RGB',(contexts[0].width*2+16,contexts[0].height+24),'#17232b')
    draw = ImageDraw.Draw(comparison)
    for i,(state,context) in enumerate(zip(('before','after'),contexts)):
        x = i*(context.width+16)
        comparison.paste(context,(x,24))
        draw.text((x+4,5),f'{state}: native source geometry',fill='white')
    path = output/'Kindle-cape-connected-source-comparison.png'
    comparison.save(path)
    images.append(dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    return images
