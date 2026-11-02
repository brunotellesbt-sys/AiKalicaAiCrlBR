"""Finish removal of clipped native boulders beneath coastal cliff feet.

The old Surf opening removed 0x118/0x119 but missed the combined cliff/rock
tops 0x108/0x109. Replace only those orphan tops with the native straight
cliff foot. The open sea, cliff body, physical flags and intact rocks stay put.
"""
import hashlib
import json
import struct

from badge_story_layer import read


ANCHORS = {
    'OneIsland_Frlg': ((6, 16), (15, 16)),
    'Route12_Frlg': ((17, 5),),
    'Route13_Frlg': ((42, 15),),
    'Route17_Frlg': ((1, 138), (20, 138)),
    'Route19_Frlg': ((17, 9),),
    'Route21_North_Frlg': ((17, 11), (5, 15)),
    'SevenIsland_TrainerTower_Frlg': ((48, 14), (67, 14), (51, 16), (63, 16)),
    'SixIsland_WaterPath_Frlg': ((4, 25), (13, 27)),
    'VermilionCity_Frlg': ((41, 29),),
}
PRIVATE_PRIMARY = ('gTileset_General_Frlg', 'gTileset_JourneySeviiSea')
BROKEN = (0x108, 0x109, 0x12B, 0x12B)
FINISHED = (0x123, 0x123, 0x12B, 0x12B)
COMPLETE = (0x108, 0x109, 0x118, 0x119)
DONOR_MAP = 'SixIsland_GreenPath_Frlg'
DONOR_ANCHORS = ((37, 17), (39, 17))


def repair(layer):
    layouts = {row['id']: row for row in json.loads(
        read(layer, 'data/layouts/layouts.json'))['layouts']}

    def load(name):
        mapping = json.loads(read(layer, f'data/maps/{name}/map.json'))
        layout = layouts[mapping['layout']]
        assert layout['layout_version'] == 'frlg'
        assert layout['primary_tileset'] in PRIVATE_PRIMARY, (name, layout['primary_tileset'])
        raw = read(layer, layout['blockdata_filepath'])
        assert len(raw) == layout['width'] * layout['height'] * 2
        values = list(struct.unpack('<' + 'H' * (len(raw) // 2), raw))
        return mapping, layout, raw, values

    _, donor_layout, donor_raw, donor_values = load(DONOR_MAP)
    complete_rocks = []
    for x, y in DONOR_ANCHORS:
        words = [donor_values[(y + dy) * donor_layout['width'] + x + dx]
                 for dy in range(2) for dx in range(2)]
        assert tuple(word & 1023 for word in words) == COMPLETE
        complete_rocks.append(dict(map=DONOR_MAP, anchor=[x, y], words=words))

    records, files, straight_cliff_donor = [], [], None
    for name, anchors in ANCHORS.items():
        mapping, layout, raw, before = load(name)
        width, height = layout['width'], layout['height']
        if name == 'OneIsland_Frlg':
            donor = before[16 * width + 8]
            assert donor & 1023 == 0x123
            straight_cliff_donor = dict(map=name, position=[8, 16], word=donor,
                                       primary_tileset=layout['primary_tileset'])
        after = before.copy()
        occupied = {(event['x'], event['y']) for kind in
                    ('object_events', 'warp_events', 'coord_events', 'bg_events')
                    for event in mapping.get(kind, [])}
        for x, y in anchors:
            assert 0 <= x < width - 1 and 0 <= y < height - 1
            cells = [(x + dx, y + dy) for dy in range(2) for dx in range(2)]
            words = [before[yy * width + xx] for xx, yy in cells]
            mids = tuple(word & 1023 for word in words)
            assert mids in (BROKEN, FINISHED), (name, x, y, mids)
            assert not occupied.intersection(cells[:2]), (name, x, y)
            result = [(word & ~1023) | mid for word, mid in zip(words, FINISHED)]
            for (xx, yy), value in zip(cells, result):
                after[yy * width + xx] = value
            records.append(dict(map=name, anchor=[x, y], before=words, after=result,
                                changed_cells=[[x, y], [x + 1, y]] if mids == BROKEN else [],
                                native_straight_cliff_foot=0x123,
                                lower_open_water_and_physical_flags_preserved=True))
        assert all(a & ~1023 == b & ~1023 for a, b in zip(before, after))
        changed = [[i % width, i // width, a, b]
                   for i, (a, b) in enumerate(zip(before, after)) if a != b]
        assert len(changed) in (0, 2 * len(anchors))
        path = layout['blockdata_filepath']
        packed = struct.pack('<' + 'H' * len(after), *after)
        if changed:
            layer.stage(path, packed)
        files.append(dict(map=name, file=path, changed_cells=changed,
                          before_sha256=hashlib.sha256(raw).hexdigest(),
                          after_sha256=hashlib.sha256(packed).hexdigest()))

    # The unchanged complete native variants prove that recognizing this
    # family must not remove every use of its upper metatiles indiscriminately.
    assert read(layer, donor_layout['blockdata_filepath']) == donor_raw
    assert len(records) == 16 and len(files) == 9
    return dict(kind='coastal-ecology-complete-cliff-feet', fragments=records, maps=files,
                changed_paths=[row['file'] for row in files if row['changed_cells']],
                replaced_top_cells=sum(len(row['changed_cells']) for row in files),
                native_straight_cliff_donor=straight_cliff_donor,
                preserved_complete_native_rocks=complete_rocks,
                cliff_body_open_water_elevations_and_collision_preserved=True,
                map_dimensions_events_connections_warps_and_atlas_unchanged=True,
                native_controller_validation_required=True)
