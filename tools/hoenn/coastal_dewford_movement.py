"""Join Dewford's dry terminal floor to its existing level-three shoreline.

This stages a new layer only. The suspension bridge keeps its upper walking
level, drawing priority, lower Surf passage and original southern stairs.
"""
import hashlib
import io
import json
import struct

from PIL import Image
from dewford_coast_view import MAPS
from render_sea_maps import MapRenderer


HEADER = 'include/journey_dewford_bridge.h'
NORTH_STAIRS = {(5, 3), (6, 3)}
EXPECTED_CHANGES = {'DewfordTown': 27, 'Route106': 23, 'Route107': 17,
                    'JourneyDewfordPortIsland': 9}
FLOOR_METATILES = {0x124, 0x201, 0x248, 0x249, 0x2AD}
STAIR_GRAPHIC = 0x3FB
PRIVATE_BANK = 'data/tilesets/secondary/journey_dewford_harbor'


STAIR_FUNCTION = '''static bool8 JourneyDewfordBridgeStairConnects(const struct ObjectEvent *object, s16 x, s16 y)
{
    s16 sourceX = object->currentCoords.x - MAP_OFFSET;
    s16 sourceY = object->currentCoords.y - MAP_OFFSET;
    s16 targetX = x - MAP_OFFSET;
    s16 targetY = y - MAP_OFFSET;
    bool8 south, north;
    if (!JourneyDewfordBridgeMap() || JourneyDewfordBridgeLowerObject(object))
        return FALSE;
    // Preserve both original south stair edges. The north stairs also meet
    // dry sand at their sides; these exact existing approaches stay usable.
    // Water, rails, walls and every unrelated elevation boundary retain the
    // ordinary collision checks that run before this exception.
    south = sourceX == targetX && (sourceX == 5 || sourceX == 6)
        && ((sourceY == 16 && targetY == 15)
            || (sourceY == 15 && targetY == 16));
    north = (sourceX == targetX && (sourceX == 5 || sourceX == 6)
             && ((sourceY == 2 && targetY == 3)
                 || (sourceY == 3 && targetY == 2)))
        || (sourceY == 3 && targetY == 3
            && ((sourceX == 4 && targetX == 5)
                || (sourceX == 5 && targetX == 4)
                || (sourceX == 6 && targetX == 7)
                || (sourceX == 7 && targetX == 6)));
    return (south || north)
        && ((object->currentElevation == ELEVATION_DEFAULT
             && MapGridGetElevationAt(x, y) == 4)
            || (object->currentElevation == 4
                && MapGridGetElevationAt(x, y) == ELEVATION_DEFAULT));
}

'''


def repair(layer):
    def raw(path):
        return layer.outputs[path] if path in layer.outputs else (layer.source / path).read_bytes()

    layouts = {row['id']: row for row in json.loads(raw('data/layouts/layouts.json'))['layouts']}
    changes, paths, world_before, world_after = [], [], {}, {}
    per_map = {}
    for name, (origin_x, origin_y) in MAPS.items():
        mapping = json.loads(raw(f'data/maps/{name}/map.json'))
        layout = layouts[mapping['layout']]
        path = layout['blockdata_filepath']
        before = raw(path)
        blocks = list(struct.unpack('<' + 'H' * (len(before) // 2), before))
        assert len(blocks) == layout['width'] * layout['height']
        count = 0
        for index, block in enumerate(blocks):
            x, y = index % layout['width'], index // layout['width']
            world = x + origin_x, y + origin_y
            world_before[world] = dict(map=name, tile=[x, y], block=block)
            # The original generated terminal's ownership rectangle. No town
            # streets, southern coast, neighboring ocean or forest is lowered.
            owned = -7 <= world[0] < 14 and -11 <= world[1] < 7
            if (owned and block >> 12 == 4 and block & 0xC00 == 0
                    and world not in NORTH_STAIRS):
                assert block & 0x3FF in FLOOR_METATILES, (name, x, y, hex(block))
                after = (block & 0xFFF) | 0x3000
                blocks[index] = after
                changes.append(dict(map=name, tile=[x, y], world=list(world),
                                    before=block, after=after,
                                    old_elevation=4, elevation=3,
                                    metatile=block & 0x3FF, collision=0,
                                    art_behavior_and_collision_unchanged=True))
                count += 1
            world_after[world] = dict(map=name, tile=[x, y], block=blocks[index])
        assert count == EXPECTED_CHANGES[name], (name, count)
        after = struct.pack('<' + 'H' * len(blocks), *blocks)
        assert len(before) == len(after)
        assert sum(a != b for a, b in zip(before, after)) == count
        layer.stage(path, after)
        paths.append(path)
        per_map[name] = dict(changed_blocks=count,
                             before_sha256=hashlib.sha256(before).hexdigest(),
                             after_sha256=hashlib.sha256(after).hexdigest())

    repaired_edges = []
    for point, row in world_before.items():
        if row['block'] >> 12 != 4 or row['block'] & 0xC00:
            continue
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            other = point[0] + dx, point[1] + dy
            neighbor = world_before.get(other)
            if (neighbor is None or neighbor['block'] >> 12 != 3
                    or neighbor['block'] & 0xC00):
                continue
            if world_after[point]['block'] >> 12 == world_after[other]['block'] >> 12 == 3:
                repaired_edges.append(dict(interior=dict(map=row['map'], tile=row['tile']),
                                           shore=dict(map=neighbor['map'], tile=neighbor['tile']),
                                           before_elevations=[4, 3], after_elevations=[3, 3]))
    assert repaired_edges
    header = raw(HEADER).decode()
    start = header.index('static bool8 JourneyDewfordBridgeStairConnects(')
    end = header.index('static void JourneyDewfordBridgeRestoreLevel(', start)
    assert 'Precisely the two south stair edges' in header[start:end]
    updated = header[:start] + STAIR_FUNCTION + header[end:]
    assert updated[:start] == header[:start]
    assert updated[updated.index('static void JourneyDewfordBridgeRestoreLevel('):] == header[end:]
    layer.stage(HEADER, updated)
    paths.append(HEADER)
    # The old 32-pixel riser used native [left, middle], leaving its right
    # edge open. Keep its existing eight-pixel height and palette, but include
    # the complete native right cap from Mossdeep's final stair piece 0x332.
    # Only the two missing cap quadrants change; all original graphic slots,
    # the stair underlay, palettes, metatile IDs and attributes are retained.
    meta_path, graphic_path = PRIVATE_BANK + '/metatiles.bin', PRIVATE_BANK + '/tiles.png'
    meta_bytes = raw(meta_path)
    words = list(struct.unpack('<' + 'H' * (len(meta_bytes) // 2), meta_bytes))
    assert STAIR_GRAPHIC not in {word & 0x3FF for word in words}
    graphic_bytes = raw(graphic_path)
    with Image.open(io.BytesIO(graphic_bytes)) as original:
        canvas = original.copy()
    assert canvas.mode == 'P' and canvas.size == (128, 256)
    px, py = (STAIR_GRAPHIC - 512) % 16 * 8, (STAIR_GRAPHIC - 512) // 16 * 8
    assert set(canvas.crop((px, py, px + 8, py + 8)).getdata()) == {0}
    donor_bytes = raw('data/tilesets/secondary/mossdeep/metatiles.bin')
    assert struct.unpack_from('<8H', donor_bytes, (0x332 - 512) * 16) == (
        0x82C1, 0x82C2, 0x82D1, 0x82D2, 0, 0, 0, 0)
    donor = MapRenderer(layer.source).render('MossdeepCity', values=[0x332],
                                           dimensions=(1, 1), npcs=False)[0]
    native_cap = donor.crop((8, 8, 16, 16))
    # This is exactly the established bridge-footing palette conversion.
    def footing_color(color):
        if max(color) - min(color) > 55:
            return 0
        brightness = sum(color) // 3
        return 11 if brightness < 90 else 9 if brightness < 135 else 7 if brightness < 165 else 2 if brightness < 190 else 1
    cap = Image.new('P', (8, 8))
    cap.putdata([footing_color(color) for color in native_cap.getdata()])
    canvas.paste(cap, (px, py))
    cap_changes = []
    for mid, quadrant in [(0x2DF, 7), (0x2E1, 5)]:
        offset = (mid - 512) * 8 + quadrant
        assert words[offset] == 0x73F3, (hex(mid), hex(words[offset]))
        cap_changes.append(dict(metatile=mid, quadrant=quadrant,
                                before=words[offset], after=0x7000 | STAIR_GRAPHIC))
        words[offset] = 0x7000 | STAIR_GRAPHIC
    packed = struct.pack('<' + 'H' * len(words), *words)
    assert sum(a != b for a, b in zip(meta_bytes, packed)) == 2
    encoded = io.BytesIO()
    canvas.save(encoded, format='PNG')
    layer.stage(meta_path, packed)
    layer.stage(graphic_path, encoded.getvalue())
    paths.extend([meta_path, graphic_path])
    assert len(changes) == 76
    return dict(changed_paths=paths, changed_blocks=changes, maps=per_map,
                former_invisible_shore_boundaries=repaired_edges,
                dry_accessible_terminal_floor_and_shore_are_level3=True,
                terminal_door_floor_is_level3=True,
                northern_stairs_remain_level4=True,
                exact_north_dry_stair_approaches_preserved=True,
                original_southern_stair_edges_preserved=True,
                upper_bridge_multilevel15_and_pedestrian_level4_preserved=True,
                lower_surf_level1_and_rail_collision_preserved=True,
                terrain_graphics_metatile_behaviors_and_collisions_unchanged=True,
                stairs_complete_native_right_cap=dict(
                    donor_map='MossdeepCity', donor_metatile=0x332,
                    native_cap_rectangle=[8, 8, 16, 16],
                    source_metatile_words=[0x82C1, 0x82C2, 0x82D1, 0x82D2, 0, 0, 0, 0],
                    graphic=STAIR_GRAPHIC, palette=7,
                    graphic_previously_unreferenced_and_all_zero=True,
                    original_eight_pixel_riser_height_preserved=True,
                    entire_native_right_cap_preserved=True,
                    existing_graphic_slots_and_stair_underlays_unchanged=True,
                    changes=cap_changes),
                terminal_warps_connections_and_vendors_unchanged=True,
                atlas_and_southern_forest_unchanged=True,
                initial_video_defect=dict(interior=['Route107', 2, 5],
                                          shore=['Route107', 2, 6],
                                          before_elevations=[4, 3]),
                eastern_video_defect=dict(interior=['Route107', 8, 3],
                                         shore=['Route107', 9, 3],
                                         before_elevations=[4, 3]))
