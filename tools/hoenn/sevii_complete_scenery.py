"""Restore complete native scenery clipped by the layer-169 marine boundary.

The perimeter replacement changed only the cells on the map edge. Some of
those cells were one half of a native 2x2 reef, so their other halves remained
beside the new complete small rocks. Replace the rest of each *known* footprint
with the same complete native rock. Keep every cell's collision and elevation.
This is deliberately not a global replacement of the native boulder family.
Cliff and sand pieces use their original authenticated artwork with the new
boundary's collision and elevation; the cliff-attached reef keeps its top row.
"""
import hashlib
import json
import struct

from badge_story_layer import read
from coast_scenery_review_contract import PARENT_MARKER_SHA256


SMALL = 0x243
LARGE = (0x110, 0x111, 0x118, 0x119)
KINDLE = 'OneIsland_KindleRoad_Frlg'
HARBOR = 'TwoIsland_Harbor_Frlg'
THREE = 'ThreeIsland_Port_Frlg'
FOUR = 'FourIsland_Frlg'
ONE = 'OneIsland_Frlg'
SIX = 'SixIsland_Frlg'
SEVEN = 'SevenIsland_Frlg'
PARENT_MARKER = '.journey-sevii-route-boundaries'
# Coordinates are the top-left of each entire original 2x2 object. The exact
# layer-169 pattern is required before changing any cells.
FOOTPRINTS = {
    KINDLE: [
        *((0, y, (SMALL, 0x111, SMALL, 0x119))
          for y in (21, 23, 27, 33, 37, 45, 47)),
        *((22, y, (0x110, SMALL, 0x118, SMALL))
          for y in (19, 21, 27, 78, 80, 94, 104, 110, 112, 114,
                    116, 118, 122, 124, 130, 132)),
        (17, 138, (0x110, 0x111, SMALL, SMALL)),
        *((22, y, (0x1CB, SMALL, 0x1D3, SMALL))
          for y in (23, 76, 82, 92, 106, 108)),
        (0, 43, (SMALL, 0x1CC, SMALL, 0x1D4)),
        (0, 56, (SMALL, 0x213, SMALL, 0x21B)),
    ],
    HARBOR: [
        (0, 0, (0x110, SMALL, 0x118, 0x119)),
        (2, 0, (SMALL, SMALL, 0x118, 0x119)),
        (4, 0, (SMALL, SMALL, 0x118, 0x119)),
    ],
    THREE: [(46, 2, (0x244, SMALL, 0x24C, SMALL))],
    FOUR: [(0, 11, (SMALL, 0x245, SMALL, 0x24D)),
           (28, 38, (0x25E, 0x25F, SMALL, SMALL))],
}
DIMENSIONS = {KINDLE: (24, 140), HARBOR: (17, 13), THREE: (48, 20),
              FOUR: (48, 40), ONE: (24, 20), SIX: (24, 30), SEVEN: (24, 20)}
# This reef shares its top row with the cliff. Preserve those merged pieces
# and restore its original lower halves, keeping the new blocked water level.
OBJECT_TARGETS = {(FOUR, 28, 38): (0x25E, 0x25F, 0x24C, 0x24D)}
# Explicitly reviewed native shoreline pieces erased by the boundary fill.
# The immutable parent marker supplies the exact old block and donor path.
EDGE_RESTORES = {
    KINDLE: [(0, 13, 0x1FB), (23, 13, 0x1FA),
             *((23, y, 0x202) for y in range(14, 18)),
             (23, 18, 0x20A), (23, 71, 0x1FB), (0, 119, 0x1FC)],
    THREE: [(43, 0, 0x24E), (44, 0, 0x273)],
    ONE: [(0, y, 0x274) for y in range(7)],
    FOUR: [(1, 0, 0x24F), *((x, 39, 0x273) for x in range(3, 8)),
           (32, 39, 0x26F), (33, 39, 0x273), (34, 39, 0x257),
           *((x, 39, 0x265) for x in range(35, 48))],
    SIX: [(15, 0, 0x274), (0, 2, 0x273), (0, 3, 0x270),
          *((0, y, 0x274) for y in range(4, 17)),
          (2, 29, 0x273), (15, 29, 0x278),
          *((x, 29, 0x26B) for x in range(16, 23))],
    SEVEN: [(0, 4, 0x269), (23, 4, 0x26B), (0, 5, 0x274),
            (23, 5, 0x26D), (0, 6, 0x274)],
}


def repair(layer):
    marker_raw = (layer.source/PARENT_MARKER).read_bytes()
    assert hashlib.sha256(marker_raw).hexdigest() == PARENT_MARKER_SHA256, 'Scenery donor marker changed'
    marker = json.loads(marker_raw)
    donors = {(row['map'], *cell['tile']): dict(cell, path=row['path'])
              for row in marker['boundaries']['outer_water_changes'] for cell in row['cells']}
    layouts = {row['id']: row for row in
               json.loads(read(layer, 'data/layouts/layouts.json'))['layouts']}
    names = sorted(set(FOOTPRINTS) | set(EDGE_RESTORES))
    maps = {name: json.loads(read(layer, f'data/maps/{name}/map.json'))
            for name in names}
    prepared, reports = [], []
    for name in names:
        footprints = FOOTPRINTS.get(name, [])
        layout = layouts[maps[name]['layout']]
        width, height = layout['width'], layout['height']
        assert (width, height) == DIMENSIONS[name], (name, width, height)
        assert layout['layout_version'] == 'frlg'
        assert layout['primary_tileset'] == 'gTileset_JourneySeviiSea'
        path = layout['blockdata_filepath']
        before = read(layer, path)
        assert len(before) == width*height*2, path
        original = struct.unpack('<'+'H'*(width*height), before)
        if name == KINDLE:
            assert tuple(original[(29+dy)*width+21+dx] & 1023
                         for dy in range(2) for dx in range(2)) == LARGE, 'Native boulder donor changed'
            assert original[19*width+23] & 1023 == SMALL, 'Native small reef donor changed'
        words, rows, restored_edges, touched = list(original), [], [], set()
        for x, y, expected in footprints:
            assert 0 <= x < width-1 and 0 <= y < height-1, (name, x, y)
            cells = [(x+dx, y+dy) for dy in range(2) for dx in range(2)]
            positions = [yy*width+xx for xx, yy in cells]
            actual = tuple(original[index] & 1023 for index in positions)
            assert actual == expected, ('Reviewed reef footprint changed', name, x, y, actual)
            assert not touched.intersection(positions), ('Overlapping reef objects', name, x, y)
            touched.update(positions)
            changes = []
            targets = OBJECT_TARGETS.get((name, x, y), (SMALL,)*4)
            for (xx, yy), index, target in zip(cells, positions, targets):
                old = original[index]
                words[index] = (old & ~1023) | target
                assert (words[index] & ~1023) == (old & ~1023)
                donor = None
                if old != words[index] and target != SMALL:
                    donor = donors[name, xx, yy]
                    assert donor['path'] == path and donor['after'] == old
                    assert donor['before'] & 1023 == target
                changes.append(dict(cell=[xx, yy], before=old, after=words[index], donor=donor,
                                    changed=old != words[index],
                                    collision=(old >> 10) & 3, elevation=old >> 12))
            rows.append(dict(anchor=[x, y], dimensions=[2, 2],
                             metatiles_before=list(actual),
                             metatiles_after=list(targets), cells=changes,
                             complete_native_object_restored=True,
                             cliff_merged_top_preserved=(name, x, y) in OBJECT_TARGETS))
        for x, y, native_mid in EDGE_RESTORES.get(name, []):
            assert 0 <= x < width and 0 <= y < height
            index = y*width+x
            assert index not in touched
            touched.add(index)
            donor = donors[name, x, y]
            assert donor['path'] == path and donor['after'] == original[index] == 0x1643
            assert donor['before'] & 1023 == native_mid, ('Unreviewed shoreline donor', name, x, y)
            words[index] = (original[index] & ~1023) | native_mid
            restored_edges.append(dict(cell=[x, y], before=original[index], after=words[index],
                                       native_metatile=native_mid, native_donor=donor,
                                       collision=(words[index] >> 10) & 3, elevation=words[index] >> 12,
                                       kind='sand-edge' if name == KINDLE else 'cliff-edge'))
        assert all(a == b for i, (a, b) in enumerate(zip(original, words)) if i not in touched)
        after = struct.pack('<'+'H'*len(words), *words)
        prepared.append((path, after))
        reports.append(dict(map=name, path=path, dimensions=[width, height],
                            before_sha256=hashlib.sha256(before).hexdigest(),
                            after_sha256=hashlib.sha256(after).hexdigest(),
                            objects=rows, restored_native_edges=restored_edges,
                            changed_cells=sum(a != b for a, b in zip(original, words)),
                            all_upper_bits_preserved=True,
                            all_cells_outside_reviewed_objects_and_edges_unchanged=True,
                            event_templates_connections_and_borders_unchanged=True))
    # The dedicated actor repair changes only event_object_movement.c. Import
    # it after validating every terrain footprint so the two repairs compose.
    from sevii_boundary_scenery_actor import repair as repair_actor
    permanent_scenery = repair_actor(layer)
    # Do not leave a partially staged terrain repair if a reviewed pattern fails.
    for path, raw in prepared:
        layer.stage(path, raw)
    return dict(kind='sevii-complete-boundary-scenery', maps=reports,
                permanent_scenery=permanent_scenery,
                original_object_count=sum(len(rows) for rows in FOOTPRINTS.values()),
                restored_native_edge_cells=sum(len(rows) for rows in EDGE_RESTORES.values()),
                native_donor_marker=dict(path=PARENT_MARKER, sha256=PARENT_MARKER_SHA256,
                                         original_layer168_blocks_from_layer169_changes=True),
                changed_cells=sum(row['changed_cells'] for row in reports),
                native_small_reef=dict(metatile=SMALL, primary_tileset='gTileset_JourneySeviiSea',
                                       donor_map=KINDLE, donor_cell=[23, 19],
                                       already_present_in_reviewed_boundary=True),
                native_large_object_reference=dict(map=KINDLE, anchor=[21, 29],
                                                   dimensions=[2, 2], metatiles=list(LARGE)),
                existing_geology_outside_reviewed_cells_unchanged=True,
                navigation_geometry_and_save_event_ids_unchanged=True,
                source_inspection_not_native_camera_or_movement_proof=True)
