"""Finish Six's native three-row trees and the cliffs beside its gym.

Stage only.  Read prior staged bytes so this composes with the integrated
terminal overlay without modifying the immutable 161-layer source snapshot.
"""
import hashlib
import json
import struct


MAP = 'SixIsland_Frlg'
# Upper-left corners of complete native 2 x 3 trees.  The last crown is one
# row north of the old truncated tree, leaving the southern cliff untouched.
TREE_ANCHORS = ([(x, y) for y in (3, 6) for x in (0, 2, 4, 6)]
                + [(x, 9) for x in (0, 2, 4)]
                + [(0, 12), (0, 16), (0, 19)])
OLD_TREES = ([(x, y) for y in (3, 6) for x in (0, 2, 4, 6)]
             + [(x, 9) for x in (0, 2, 4)]
             + [(0, 12), (0, 16), (0, 20)])


def repair(layer):
    def raw(path):
        return layer.outputs[path] if path in layer.outputs else (layer.source / path).read_bytes()

    mapping = json.loads(raw(f'data/maps/{MAP}/map.json'))
    layouts = json.loads(raw('data/layouts/layouts.json'))['layouts']
    layout = next(row for row in layouts if row['id'] == mapping['layout'])
    assert (layout['width'], layout['height'], layout['layout_version']) == (24, 30, 'frlg')
    path = layout['blockdata_filepath']
    before = raw(path)
    values = list(struct.unpack('<720H', before))

    def at(x, y):
        return values[y * 24 + x]

    def put(x, y, value):
        assert 0 <= x < 24 and 0 <= y < 30
        values[y * 24 + x] = value

    # The untouched native tree immediately west of the house is the donor.
    # In FRLG 1e/1f is the MIDDLE, not the crown of a two-row tree.  Preserve
    # each donor row's native elevation and collision bits as well as its art.
    donor = [[at(13 + dx, 14 + dy) for dx in range(2)] for dy in range(3)]
    assert donor == [[0x300E, 0x300F], [0x041E, 0x041F], [0x0426, 0x0427]]
    for x, y in OLD_TREES:
        assert [[at(x + dx, y + dy) & 1023 for dx in range(2)] for dy in range(2)] == [
            [0x1E, 0x1F], [0x26, 0x27]], (x, y)
        for dy in range(2):
            for dx in range(2):
                put(x + dx, y + dy, 0x3001)
    for x, y in TREE_ANCHORS:
        for dy, row in enumerate(donor):
            for dx, value in enumerate(row):
                assert at(x + dx, y + dy) == 0x3001, (x + dx, y + dy, hex(at(x + dx, y + dy)))
                put(x + dx, y + dy, value)

    # The former forest to the Center's southwest left only a right crown.
    assert at(9, 12) == 0x300F
    put(9, 12, 0x3001)
    # The lower trees have their crowns cut by the cliff above and cannot fit
    # between that cliff and the terminal.  Remove their entire remnants.
    assert [at(x, 21) & 1023 for x in range(4, 8)] == [0x1E, 0x1F, 0x1E, 0x1F]
    assert [at(x, 22) & 1023 for x in range(4, 8)] == [0x26, 0x27, 0x26, 0x27]
    for y in (21, 22):
        for x in range(4, 8):
            put(x, y, 0x3001)

    # The original overlapping forest hid the northern coast.  With complete
    # freestanding trees its bare grass edge needs the native rocky lip too.
    # Water Path provides the whole north-water/grass lip and its right elbow;
    # Six's own wave-backed cliff cap then joins both columns of the side.
    water_path = json.loads(raw('data/maps/SixIsland_WaterPath_Frlg/map.json'))
    water_layout = next(row for row in layouts if row['id'] == water_path['layout'])
    water_values = struct.unpack('<' + 'H' * (water_layout['width'] * water_layout['height']),
                                 raw(water_layout['blockdata_filepath']))
    north_lip = water_values[4 * water_layout['width'] + 8]
    north_elbow = water_values[4 * water_layout['width'] + 13]
    assert (north_lip, north_elbow) == (0x3133, 0x3134)
    assert (at(9, 4), at(9, 5), at(10, 5)) == (0x067C, 0x0475, 0x1271)
    cap, land_side, water_side = at(9, 4), at(9, 5), at(10, 5)
    for x in range(9):
        put(x, 2, north_lip)
    put(9, 2, north_elbow)
    put(10, 2, cap)
    for y in (3, 4, 5):
        put(9, y, land_side)
        put(10, y, water_side)

    # Plain cliff faces replace the tree-over-cliff composite art.  The old
    # corner was shifted west to x2 but its former side/corner at x3 survived;
    # remove that entire duplicate side, retaining x2's complete native elbow.
    assert (at(2, 20), at(2, 21), at(2, 22)) == (0x04B2, 0x0472, 0x047A)
    assert (at(3, 21), at(3, 22)) == (0x0472, 0x047A)
    for x in range(3, 8):
        put(x, 20, 0x0479)
    for y in (21, 22):
        put(3, y, 0x3001)

    after = struct.pack('<720H', *values)
    old_values = struct.unpack('<720H', before)
    changed = [dict(position=[i % 24, i // 24], before=old, after=new)
               for i, (old, new) in enumerate(zip(old_values, values)) if old != new]
    assert changed
    layer.stage(path, after)
    # This helper intentionally stages no events, dimensions, palette, tileset
    # definitions, border blocks, connections, water routes or other islands.
    return dict(map=MAP, changed_paths=[path], changed_cells=changed,
                before_sha256=hashlib.sha256(before).hexdigest(),
                after_sha256=hashlib.sha256(after).hexdigest(),
                native_tree_donor=dict(map=MAP, bounds=[13, 14, 2, 3], values=donor),
                complete_replanted_trees=[dict(bounds=[x, y, 2, 3]) for x, y in TREE_ANCHORS],
                orphan_crown_removed=[9, 12],
                severed_lower_tree_remnants_removed=[4, 21, 4, 2],
                northwest_cliff=dict(north_lip=[0, 2, 9, 1], north_elbow=[9, 2], cap=[10, 2],
                                     sides=[[9, y] for y in (3, 4, 5)] + [[10, y] for y in (3, 4, 5)],
                                     north_lip_donor=dict(map='SixIsland_WaterPath_Frlg',
                                                          lip=[8, 4], elbow=[13, 4],
                                                          values=[north_lip, north_elbow]),
                                     donor_cap=[9, 4], donor_side=[9, 5, 2, 1]),
                southwest_cliff=dict(elbow=[2, 20], side=[2, 21], corner=[2, 22],
                                     plain_face=[3, 20, 5, 1], obsolete_side_removed=[3, 21, 1, 2]),
                all_tree_crowns_middles_bases_native=True,
                events_connections_dimensions_and_border_unchanged=True,
                center_gym_homes_and_integrated_terminal_unchanged=True,
                other_islands_unchanged=True)
