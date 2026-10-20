"""Render complete native Dewford maps, real neighbors and the regional border.

These are source-map review renders, not emulator screenshots. Native movement
and loaded-map checks are recorded separately by validate_dewford_coast.py.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image
from dewford_coast_landscape import south_border_block
from dewford_coast_view import MAPS
from render_sea_maps import MapRenderer


def render(source, output):
    source, output = Path(source), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    renderer = MapRenderer(source)
    records, grids, actors = {}, {}, []
    for name, (origin_x, origin_y) in MAPS.items():
        mapping = json.loads((source / f'data/maps/{name}/map.json').read_text())
        layout = renderer.layouts[mapping['layout']]
        raw = (source / layout['blockdata_filepath']).read_bytes()
        values = struct.unpack('<' + 'H' * (len(raw) // 2), raw)
        border_raw = (source / layout['border_filepath']).read_bytes()
        border = struct.unpack('<' + 'H' * (len(border_raw) // 2), border_raw)
        grids[name] = dict(width=layout['width'], height=layout['height'], values=values,
                           border=border, mapping=mapping, layout=layout)
        records[name] = dict(origin=[origin_x, origin_y], width=layout['width'],
            height=layout['height'], blockdata_sha256=hashlib.sha256(raw).hexdigest(),
            border_sha256=hashlib.sha256(border_raw).hexdigest())
        for actor in mapping['object_events']:
            if str(actor['flag']) == '0' or actor['script'] in [
                    'JourneyCompetitive_FullRestore', 'JourneyCompetitive_PlayRough']:
                actors.append((origin_x + actor['x'], origin_y + actor['y'], actor))

    def block_at(name, x, y):
        origin_x, origin_y = MAPS[name]
        world_x, world_y = x + origin_x, y + origin_y
        for donor, (donor_x, donor_y) in MAPS.items():
            grid = grids[donor]
            xx, yy = world_x - donor_x, world_y - donor_y
            if 0 <= xx < grid['width'] and 0 <= yy < grid['height']:
                return grid['values'][yy * grid['width'] + xx]
        if name in ['DewfordTown', 'Route107']:
            regional = south_border_block(name, x, y)
            if regional is not None:
                return regional
        border = grids[name]['border']
        return border[(x & 1) + 2 * (y & 1)]

    def draw_actors(image, left, top):
        for world_x, world_y, actor in sorted(actors, key=lambda entry: entry[1]):
            frame = 2 if actor['graphics_id'] == 'OBJ_EVENT_GFX_MR_BRINEYS_BOAT' and actor[
                'movement_type'] in ['MOVEMENT_TYPE_FACE_LEFT', 'MOVEMENT_TYPE_FACE_RIGHT'] else 0
            sprite = renderer.sprite(actor['graphics_id'], frame)
            dx, dy = renderer.sprite_offset(actor['graphics_id'])
            image.paste(sprite, ((world_x - left) * 16 + 8 - sprite.width // 2 + dx,
                        (world_y - top) * 16 + 16 - sprite.height + dy), sprite)

    for name, grid in grids.items():
        # The native backup has seven tiles west/north/south and eight east.
        width, height = grid['width'] + 15, grid['height'] + 14
        values = [block_at(name, x - 7, y - 7) for y in range(height) for x in range(width)]
        image, _ = renderer.render(name, values=values, dimensions=(width, height), npcs=False)
        origin_x, origin_y = MAPS[name]
        draw_actors(image, origin_x - 7, origin_y - 7)
        filename = name + '-whole-with-neighbors.png'
        image.save(output / filename)
        records[name].update(image=filename, review_width=width, review_height=height,
                            image_sha256=hashlib.sha256((output / filename).read_bytes()).hexdigest())

    left, top, right, bottom = -80, -20, 60, 27
    connected = Image.new('RGB', ((right - left) * 16, (bottom - top) * 16), '#263642')
    for name, grid in grids.items():
        image, _ = renderer.render(name, npcs=False)
        origin_x, origin_y = MAPS[name]
        connected.paste(image, ((origin_x - left) * 16, (origin_y - top) * 16))
    for name in ['DewfordTown', 'Route107']:
        grid = grids[name]
        values = [block_at(name, x, y) for y in range(20, 27) for x in range(grid['width'])]
        image, _ = renderer.render(name, values=values, dimensions=(grid['width'], 7), npcs=False)
        origin_x, origin_y = MAPS[name]
        connected.paste(image, ((origin_x - left) * 16, (20 - top) * 16))
    draw_actors(connected, left, top)
    connected.save(output / 'Dewford-connected-whole-maps.png')
    focus = connected.crop(((-12 - left) * 16, (-12 - top) * 16,
                            (18 - left) * 16, (27 - top) * 16))
    focus.resize((focus.width * 2, focus.height * 2), Image.Resampling.NEAREST).save(
        output / 'Dewford-port-bridge-and-south-coast.png')
    inside, _ = renderer.render('JourneyDewfordHarbor')
    inside.save(output / 'DewfordHarbor-interior.png')
    result = dict(rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
        source_map_renders_not_emulator_captures=True, native_tiles_and_complete_maps=True,
        real_neighbor_maps_include_diagonals=True, regional_southern_border_included=True,
        border_rule='dewford_coast_landscape.south_border_block',
        conditional_items_shown_as_unclaimed_fixture=True, maps=records,
        connected_whole_maps='Dewford-connected-whole-maps.png',
        port_bridge_south_focus='Dewford-port-bridge-and-south-coast.png',
        functional_evidence='mods/hoenn/dewford-coast-validation')
    (output / 'review.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(render(arguments.source, arguments.output), indent=2))
