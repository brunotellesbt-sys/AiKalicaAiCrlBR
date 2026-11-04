"""Close One Island's exposed west cliff and all three steps of its cape.

The LEFT Surf connection made an old map edge visible. 0x0471 is a blocked
metatile 0x071, the interior of the mountain, rather than a finished face.
Use the complete native Six Island water/solid cliff pair and its feet.
"""
import hashlib
import json
import struct

from badge_story_layer import read


MAP = 'OneIsland_Frlg'
DONOR = 'SixIsland_Frlg'
PRIMARY = 'gTileset_JourneySeviiSea'

# Exact full block words, including collision and elevation. The short wall
# rows continue into the stepped southern cape; no tree or town tile moves.
WALL_BEFORE = {(x, y): 0x0471 for y in range(13) for x in (0, 1)}
WALL_AFTER = {(x, y): (0x1274 if x == 0 else 0x0473)
              for y in range(13) for x in (0, 1)}
CAPE = {
    (0, 13): (0x0471, 0x1274), (1, 13): (0x04B2, 0x047B),
    (0, 14): (0x047C, 0x1278), (1, 14): (0x047D, 0x1269),
    (2, 14): (0x04B2, 0x047B),
    (0, 15): (0x0471, 0x112B), (1, 15): (0x04B2, 0x1278),
    (2, 15): (0x047D, 0x1269), (3, 15): (0x04B2, 0x047B),
    (0, 16): (0x047C, 0x112B), (1, 16): (0x047D, 0x112B),
    (2, 16): (0x04B2, 0x1278), (3, 16): (0x047D, 0x126B),
    (4, 16): (0x1120, 0x126B),
    (0, 17): (0x047C, 0x112B), (1, 17): (0x047C, 0x112B),
    (2, 17): (0x047D, 0x112B), (3, 17): (0x1120, 0x112B),
    (4, 17): (0x1131, 0x112B),
    (0, 18): (0x1123, 0x112B), (1, 18): (0x1123, 0x112B),
    (2, 18): (0x1123, 0x112B), (3, 18): (0x1131, 0x112B),
}
BEFORE = {**WALL_BEFORE, **{cell: pair[0] for cell, pair in CAPE.items()}}
AFTER = {**WALL_AFTER, **{cell: pair[1] for cell, pair in CAPE.items()}}
TREE = ((0x04B4, 0x04B5), (0x041E, 0x041F), (0x0416, 0x0415),
        (0x041E, 0x041F), (0x0416, 0x0417), (0x041E, 0x041F),
        (0x0416, 0x0417), (0x041E, 0x041F), (0x0426, 0x0427))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def repair(layer):
    layouts = {row['id']: row for row in json.loads(
        read(layer, 'data/layouts/layouts.json'))['layouts']}
    maps = {}
    for name in (MAP, DONOR):
        path = f'data/maps/{name}/map.json'
        mapping_raw = read(layer, path)
        mapping = json.loads(mapping_raw)
        layout = layouts[mapping['layout']]
        assert layout['layout_version'] == 'frlg'
        assert layout['primary_tileset'] == PRIMARY
        raw = read(layer, layout['blockdata_filepath'])
        assert len(raw) == layout['width'] * layout['height'] * 2
        words = list(struct.unpack('<' + 'H' * (len(raw) // 2), raw))
        maps[name] = mapping, mapping_raw, layout, raw, words
    mapping, mapping_raw, layout, raw, words = maps[MAP]
    _, _, donor_layout, donor_raw, donor_words = maps[DONOR]
    assert (layout['width'], layout['height']) == (24, 20)
    assert (donor_layout['width'], donor_layout['height']) == (24, 30)
    connections = mapping.get('connections') or []
    assert dict(map='MAP_JOURNEYSURFLINK05000', direction='left', offset=7) in connections
    assert dict(map='MAP_ONE_ISLAND_TREASURE_BEACH', direction='down', offset=0) in connections

    # Check the whole donor side, the two-piece solid foot and the complete
    # water foot below it. The concave corner comes from the same native bank.
    for y in range(4, 22):
        assert donor_words[y * 24:y * 24 + 2] == [0x1274, 0x0473]
    assert donor_words[22 * 24:22 * 24 + 3] == [0x1274, 0x047B, 0x047A]
    assert donor_words[23 * 24:23 * 24 + 3] == [0x1278, 0x126B, 0x126B]
    assert donor_words[29 * 24 + 23] == 0x1269
    assert words[19 * 24 + 20] == 0x112B
    assert words[14 * 24 + 4] == 0x047A
    tree_before = [words[y * 24 + x] for y in range(6, 15) for x in (5, 6)]
    assert tree_before == [word for pair in TREE for word in pair]
    assert len(BEFORE) == len(AFTER) == 49 and BEFORE.keys() == AFTER.keys()
    for (x, y), value in BEFORE.items():
        assert words[y * 24 + x] == value, (MAP, x, y, value, words[y * 24 + x])
    occupied = {(event['x'], event['y']) for kind in
                ('object_events', 'warp_events', 'coord_events', 'bg_events')
                for event in mapping.get(kind, [])}
    assert not occupied.intersection(AFTER), ('Cliff repair overlaps events', occupied.intersection(AFTER))

    after = words.copy()
    for (x, y), value in AFTER.items():
        after[y * 24 + x] = value
    changed = [(i % 24, i // 24) for i, pair in enumerate(zip(words, after)) if pair[0] != pair[1]]
    assert set(changed) == set(AFTER)
    assert all(0 <= x <= 4 and 0 <= y <= 18 for x, y in changed)
    assert [after[y * 24 + x] for y in range(6, 15) for x in (5, 6)] == tree_before
    assert all(after[i] == value for i, value in enumerate(words)
               if (i % 24, i // 24) not in AFTER)
    packed = struct.pack('<' + 'H' * len(after), *after)
    path = layout['blockdata_filepath']
    layer.stage(path, packed)
    return dict(kind='arrival-coast-west-cliff', map=MAP, file=path,
        changed_paths=[path], changed_cell_count=len(changed),
        changed_cells=[dict(cell=[x, y], before=words[y * 24 + x], after=after[y * 24 + x])
                       for x, y in changed],
        before_sha256=sha(raw), after_sha256=sha(packed),
        donor=dict(map=DONOR, file=donor_layout['blockdata_filepath'], sha256=sha(donor_raw),
                   primary_tileset=PRIMARY, west_face=[[0, 4, 0x1274], [1, 4, 0x0473]],
                   solid_foot=[[1, 22, 0x047B], [2, 22, 0x047A]],
                   water_foot=[[0, 23, 0x1278], [1, 23, 0x126B], [2, 23, 0x126B]],
                   concave_water_corner=[23, 29, 0x1269]),
        retained_tree=dict(bounds=[5, 6, 7, 15], words=tree_before),
        retained_east_foot=dict(cell=[4, 14], word=0x047A),
        map_json_sha256=sha(mapping_raw), connections=connections,
        event_cells_preserved=True, all_cells_outside_repair_preserved=True,
        city_tree_graphics_pier_and_connections_preserved=True,
        native_whole_map_neighbors_camera_collision_and_surf_proof_required=True)
