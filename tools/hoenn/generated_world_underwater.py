"""Use complete native underwater terrain instead of repeated wall fragments."""
import hashlib
import json
import struct

from badge_story_layer import read


NAMES = ['JourneyDepth' + theme for theme in
         ['Abismo', 'Dimensoes', 'Mares', 'Origens', 'Profundezas']]


def repair(layer):
    layouts = {row['id']: row for row in json.loads(
        read(layer, 'data/layouts/layouts.json'))['layouts']}
    attributes = read(layer, 'data/tilesets/secondary/underwater/metatile_attributes.bin')
    # This changes artwork, not the floor's native behavior or draw priority.
    assert struct.unpack_from('<H', attributes, (0x216-512)*2)[0] == \
           struct.unpack_from('<H', attributes, (0x254-512)*2)[0] == 0x1000
    donor = json.loads(read(layer, 'data/maps/Underwater_Route128/map.json'))
    dl = layouts[donor['layout']]
    dv = struct.unpack('<'+'H'*(dl['width']*dl['height']), read(layer, dl['blockdata_filepath']))
    arch = [[dv[y*dl['width']+x] for x in range(37, 40)] for y in (25, 26)]
    assert arch == [[0x0665, 0x0666, 0x0667], [0x066D, 0x326E, 0x066F]]
    # Native rock face, side walls and bottom corners around the complete arch.
    ridge = [[0x3606, 0x361E, 0x361E, 0x361E, 0x3607],
             [0x3614, 0x3613, 0x3613, 0x3613, 0x3612],
             [0x3614, 0x3665, 0x3666, 0x3667, 0x3612],
             [0x3623, 0x366D, 0x326E, 0x366F, 0x3622]]
    records = []
    for name in NAMES:
        mapping = json.loads(read(layer, f'data/maps/{name}/map.json'))
        layout = layouts[mapping['layout']]
        assert mapping['map_type'] == 'MAP_TYPE_UNDERWATER'
        assert layout['primary_tileset'] == dl['primary_tileset'] == 'gTileset_General'
        assert layout['secondary_tileset'] == dl['secondary_tileset'] == 'gTileset_Underwater'
        width, height = layout['width'], layout['height']
        path = layout['blockdata_filepath']
        raw = read(layer, path)
        before = list(struct.unpack('<'+'H'*(width*height), raw))
        after = [0x3216 if value == 0x3254 else value for value in before]
        assert len(mapping['warp_events']) == 1
        warp = mapping['warp_events'][0]
        cx, cy = warp['x'], warp['y']
        assert 3 <= cx < width-3 and 4 <= cy < height-2
        for y in range(height):
            for x in range(width):
                index = y*width+x
                if y == 0:
                    after[index] = 0x3606 if x == 0 else 0x3607 if x == width-1 else 0x361E
                elif y == height-1:
                    after[index] = 0x3623 if x == 0 else 0x3622 if x == width-1 else 0x360B
                elif x == 0:
                    after[index] = 0x3614
                elif x == width-1:
                    after[index] = 0x3612
        for dy, row in enumerate(ridge):
            for dx, value in enumerate(row):
                after[(cy-3+dy)*width+cx-2+dx] = value
        assert after[cy*width+cx] == before[cy*width+cx] == 0x326E
        # No obstruction between the dive patch's southern cells and the cave.
        assert all(not after[(cy+1)*width+x] & 0xC00 for x in range(cx-2, cx+3))
        for index, (a, b) in enumerate(zip(before, after)):
            assert a >> 12 == b >> 12 == 3, (name, index, a, b)
        changed = [[i % width, i // width, a, b] for i, (a, b)
                   in enumerate(zip(before, after)) if a != b]
        if changed:
            layer.stage(path, struct.pack('<'+'H'*len(after), *after))
        records.append(dict(map=name, dimensions=[width, height],
                            before_sha256=hashlib.sha256(raw).hexdigest(),
                            after_sha256=hashlib.sha256(read(layer, path)).hexdigest(),
                            changed_cells=changed, cave_entrance=[cx, cy],
                            cave_ridge_bounds=[cx-2, cy-3, cx+3, cy+1],
                            original_floor_behavior_and_all_elevations_preserved=True,
                            connections_warps_events_and_atlas_preserved=True))
    return dict(kind='complete-native-underwater-terrain', maps=records,
                floor_metatile=0x216, former_wall_floor_metatile=0x254,
                entrance_donor=dict(map='Underwater_Route128', bounds=[37,25,40,27]),
                complete_ridge_words=ridge)
