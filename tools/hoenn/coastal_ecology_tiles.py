"""Replace overlapping-forest fragments inside Pallet's isolated pine trees.

Only the graphics IDs change. Each complete 2x3 tree is reconstructed from
the native Viridian donor with all existing elevation/collision bits kept.
"""
import hashlib
import json
import struct

from badge_story_layer import read


BROKEN = (0x00E, 0x00F, 0x01C, 0x01F, 0x024, 0x027)
COMPLETE = (0x00E, 0x00F, 0x01E, 0x01F, 0x026, 0x027)
ANCHORS = tuple([(24, y) for y in range(0, 30, 3)] +
                [(x, y) for y in (12, 15) for x in (0,)] +
                [(x, y) for y in (18, 21, 24, 27) for x in (0, 2, 4)] +
                [(x, 27) for x in range(12, 24, 2)])


def repair(layer):
    layouts = {row['id']: row for row in json.loads(
        read(layer, 'data/layouts/layouts.json'))['layouts']}
    mapping = json.loads(read(layer, 'data/maps/PalletTown_Frlg/map.json'))
    layout = layouts[mapping['layout']]
    donor_mapping = json.loads(read(layer, 'data/maps/ViridianCity_Frlg/map.json'))
    donor = layouts[donor_mapping['layout']]
    assert layout['primary_tileset'] == donor['primary_tileset'] == 'gTileset_General_Frlg'
    donor_words = struct.unpack('<'+'H'*(donor['width']*donor['height']),
                                 read(layer, donor['blockdata_filepath']))
    donor_object = [donor_words[(23+dy)*donor['width']+12+dx]
                    for dy in range(3) for dx in range(2)]
    assert tuple(value & 1023 for value in donor_object) == COMPLETE
    path = layout['blockdata_filepath']
    raw = read(layer, path)
    before = list(struct.unpack('<'+'H'*(layout['width']*layout['height']), raw))
    after = before.copy()
    records = []
    assert len(ANCHORS) == len(set(ANCHORS)) == 30
    occupied = {(event['x'], event['y']) for kind in
                ('object_events', 'warp_events', 'coord_events', 'bg_events')
                for event in mapping.get(kind, [])}
    for x, y in sorted(ANCHORS):
        cells = [(x+dx, y+dy) for dy in range(3) for dx in range(2)]
        assert all(0 <= xx < layout['width'] and 0 <= yy < layout['height']
                   for xx, yy in cells)
        assert not occupied.intersection(cells), (x, y)
        words = [before[yy*layout['width']+xx] for xx, yy in cells]
        mids = tuple(word & 1023 for word in words)
        assert mids in (BROKEN, COMPLETE), (x, y, mids)
        result = [(word & ~1023) | mid for word, mid in zip(words, COMPLETE)]
        for (xx, yy), word in zip(cells, result):
            after[yy*layout['width']+xx] = word
        assert all(a & ~1023 == b & ~1023 for a, b in zip(words, result))
        records.append(dict(anchor=[x, y], before=words, after=result,
                            complete_object_dimensions=[2, 3],
                            elevation_and_collision_preserved=True))
    changed = [[i % layout['width'], i // layout['width'], a, b]
               for i, (a, b) in enumerate(zip(before, after)) if a != b]
    if changed:
        assert len(changed) == 60
        layer.stage(path, struct.pack('<'+'H'*len(after), *after))
    return dict(kind='coastal-ecology-complete-native-trees', map='PalletTown_Frlg',
                file=path, trees=records, changed_cells=changed,
                before_sha256=hashlib.sha256(raw).hexdigest(),
                after_sha256=hashlib.sha256(read(layer, path)).hexdigest(),
                donor=dict(map='ViridianCity_Frlg', anchor=[12, 23], words=donor_object),
                terrain_dimensions_and_elevations_unchanged=True,
                every_cell_collision_bits_unchanged=True,
                all_map_events_connections_warps_unchanged=True,
                atlas_unchanged=True)
