"""Keep pedestrians off the wet lower half of Pallet's north cliff lip.

The private half-grass/half-water cliff cells have ordinary floor behavior.
Their open collision lets a full-height actor put its feet over the visible
water. Block the eight mixed cells; the full grass above, eastern corridor,
wooden approaches, water elevations and every graphic remain unchanged.
"""
import hashlib
import json
import struct

from badge_story_layer import read


MAP = 'PalletTown_Frlg'
CELLS = tuple((x, 17, 0x3302 if x < 22 else 0x3303) for x in range(15, 23))


def repair(layer):
    layouts = {row['id']: row for row in json.loads(
        read(layer, 'data/layouts/layouts.json'))['layouts']}
    mapping = json.loads(read(layer, f'data/maps/{MAP}/map.json'))
    layout = layouts[mapping['layout']]
    assert (layout['width'], layout['height']) == (26, 30)
    assert layout['layout_version'] == 'frlg'
    assert (layout['primary_tileset'], layout['secondary_tileset']) == (
        'gTileset_General_Frlg', 'gTileset_PalletTown')
    path = layout['blockdata_filepath']
    raw = read(layer, path)
    before = list(struct.unpack('<780H', raw))
    after = before.copy()
    occupied = {(event['x'], event['y']) for kind in
                ('object_events', 'warp_events', 'coord_events', 'bg_events')
                for event in mapping.get(kind, [])}
    changes = []
    for x, y, original in CELLS:
        index = y * 26 + x
        blocked = original | 0x400
        assert before[index] in (original, blocked), (x, y, before[index])
        assert (x, y) not in occupied
        after[index] = blocked
        if before[index] != blocked:
            changes.append(dict(position=[x, y], before=before[index], after=blocked))
    assert len(changes) in (0, 8)
    assert all(a == b or a ^ b == 0x400 for a, b in zip(before, after))
    packed = struct.pack('<780H', *after)
    if changes:
        layer.stage(path, packed)
    return dict(kind='coastal-ecology-pallet-wet-cliff-lip', map=MAP, file=path,
        changed_cells=changes, blocked_mixed_shore_cells=8,
        before_sha256=hashlib.sha256(raw).hexdigest(),
        after_sha256=hashlib.sha256(packed).hexdigest(),
        only_collision_bit10_changed=True,
        metatiles_elevations_graphics_and_attributes_preserved=True,
        full_grass_and_east_corridor_and_both_bridge_approaches_preserved=True,
        true_water_elevations_and_multilevel_south_bridge_preserved=True,
        maps_events_connections_warps_trees_roof_and_atlas_unchanged=True,
        native_dry_land_approach_and_all_eight_blocked_edges_required=True)
