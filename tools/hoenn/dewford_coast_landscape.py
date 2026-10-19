"""Restore Dewford's native forest continuation beside the Route 107 coast.

The shared ocean-rim overlay replaced Route 107's entire border with reef.
That border is also visible below the native forest at its western end, so
restoring the twenty-row layout alone still left a cut canopy over the sea.
Keep the original twenty rows and the original forest, and make the *visible
border* continue the terrain actually present above it. This is deliberately
restricted to Dewford and Route 107; the route's eastern ocean limit remains
the same reef and every event, connection, building and dry tile is retained.
"""
import json
import struct


UPSTREAM_REPOSITORY = 'eonlynx/pokecrossroads'
UPSTREAM_COMMIT = 'e05c82865d38a6638173fd30b2c830d1250aa50d'
UPSTREAM_ROUTE107_SHA256 = 'af88a3d526aa59d8f263514364c2ae76f333d3e0dc9222c3b1786f10f025e097'
# These exact source blocks were checked against the immutable upstream file.
# Collision is added to the tree and the last coast tile because they delimit
# the playable map, without changing either native picture or elevation.
NATIVE_SOUTH_CELLS = [(8, 18, 0x111d, 0x111d),
                      (7, 19, 0x0239, 0x0639),
                      (8, 19, 0x1125, 0x1525)]


HEADER = '''#ifndef GUARD_JOURNEY_DEWFORD_COAST_H
#define GUARD_JOURNEY_DEWFORD_COAST_H
#include "constants/maps.h"

static bool8 JourneyDewfordSouthBorderBlock(int x, int y, u16 *block)
{
    int worldX = x - MAP_OFFSET;
    int worldY = y - MAP_OFFSET;

    if (gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(MAP_DEWFORD_TOWN)
        && gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_DEWFORD_TOWN))
        worldX -= 20;
    else if (gSaveBlock1Ptr->location.mapGroup != MAP_GROUP(MAP_ROUTE107)
        || gSaveBlock1Ptr->location.mapNum != MAP_NUM(MAP_ROUTE107))
        return FALSE;

    if (worldY < 20)
        return FALSE;

    // Native Dewford's forest continues beyond the walkable map. A regional
    // border is necessary because Route 107 contains both that forest and sea.
    // All three cases are impassable; no new traversable map area is created.
    if (worldX < 8)
        *block = 0x0643;
    else if (worldX == 8)
        *block = 0x1525;
    else
        *block = 0x15F9;
    return TRUE;
}
#endif
'''


def south_border_block(map_name, x, y):
    """Mirror the native border rule for whole-map source review renders."""
    assert map_name in ('DewfordTown', 'Route107')
    if y < 20:
        return None
    world_x = x - (20 if map_name == 'DewfordTown' else 0)
    return 0x0643 if world_x < 8 else 0x1525 if world_x == 8 else 0x15f9


def repair(layer):
    def raw(path):
        return layer.outputs[path] if path in layer.outputs else (layer.source/path).read_bytes()

    origin = json.loads(raw('.source-acquired.json'))
    assert origin['commit'] == UPSTREAM_COMMIT
    assert origin['sha256']['data/layouts/Route107/map.bin'] == UPSTREAM_ROUTE107_SHA256
    data = json.loads(raw('data/layouts/layouts.json'))
    layouts = {layout['id']: layout for layout in data['layouts']}
    route = json.loads(raw('data/maps/Route107/map.json'))
    town = json.loads(raw('data/maps/DewfordTown/map.json'))
    rlayout = layouts[route['layout']]
    tlayout = layouts[town['layout']]
    assert (rlayout['width'], rlayout['height']) == (60, 20)
    assert (tlayout['width'], tlayout['height']) == (20, 20)

    path = rlayout['blockdata_filepath']
    values = list(struct.unpack('<1200H', raw(path)))
    before = values.copy()
    changes = []
    # Restore the native corner's complete neighbors. The dry corner at (7,18)
    # was correct; the ocean-rim overlay replaced its neighbors with reef and
    # turned a complete bend into a square sand fragment and a missing tree.
    assert values[17*60+7] == 0x1641
    assert values[18*60+7] == 0x313e
    for x, y, native, replacement in NATIVE_SOUTH_CELLS:
        at = y*60+x
        assert values[at] in (0x15f9, replacement), (x, y, hex(values[at]))
        if values[at] != replacement:
            changes.append([x, y, values[at], replacement])
            values[at] = replacement
        assert replacement & ~0xc00 == native & ~0xc00
    if changes:
        layer.stage(path, struct.pack('<1200H', *values))
    assert all(a == b for i, (a, b) in enumerate(zip(before, values))
               if i not in [y*60+x for x, y, _, _ in NATIVE_SOUTH_CELLS])

    path = 'src/fieldmap.c'
    text = raw(path).decode()
    include = '#include "journey_dewford_coast.h"'
    anchor = 'static inline u16 GetBorderBlockAt(int x, int y)'
    if include not in text:
        assert text.count(anchor) == 1
        text = text.replace(anchor, include+'\n\n'+anchor)
    anchor = '    const struct MapLayout *mapLayout = gMapHeader.mapLayout;\n'
    insert = '''    u16 coastBlock;
    if (JourneyDewfordSouthBorderBlock(x, y, &coastBlock))
        return coastBlock;
'''
    if 'JourneyDewfordSouthBorderBlock(x, y, &coastBlock)' not in text:
        assert text.count(anchor) == 1
        text = text.replace(anchor, anchor+insert)
    layer.stage(path, text)
    layer.stage('include/journey_dewford_coast.h', HEADER)

    assert all((south_border_block('Route107', x, 20) & 0xc00) == 0x400
               for x in range(-7, 68))
    assert all(south_border_block('DewfordTown', x+20, y)
               == south_border_block('Route107', x, y)
               for x in range(-27, 68) for y in range(20, 28))
    return dict(
        maps=['DewfordTown', 'Route107'],
        map_dimensions_unchanged=True,
        native_forest_and_dry_ground_preserved=True,
        native_coast_corner_and_missing_crown_restored=True,
        original_dry_corner_retained=[7, 18, 0x313e],
        upstream_repository=UPSTREAM_REPOSITORY,
        upstream_commit=UPSTREAM_COMMIT,
        upstream_route107_sha256=UPSTREAM_ROUTE107_SHA256,
        upstream_native_cells=[dict(tile=[x,y],native=native,restored=replacement,
                                   picture_and_elevation_unchanged=True,
                                   boundary_collision_added=bool(native ^ replacement))
                               for x,y,native,replacement in NATIVE_SOUTH_CELLS],
        original_town_border_unchanged=True,
        regional_border_restores_forest_continuation=True,
        regional_border_forest_max_x=7,
        regional_border_coast_x=8,
        regional_border_reef_min_x=9,
        regional_border_first_y=20,
        regional_border_blocks=[0x0643, 0x1525, 0x15f9],
        regional_border_always_impassable=True,
        border_rule_matches_across_town_route_seam=True,
        coast_changed_cells=changes,
        buildings_events_connections_and_vendors_unchanged=True)
