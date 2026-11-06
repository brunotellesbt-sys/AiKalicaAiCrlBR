"""Keep generated marine corners visible without opening movement boundaries.

Only fieldmap.c is staged. Undefined cells stay undefined for every movement,
collision and elevation query; the drawing lookup resolves nearby actual map
blocks, then the connected map's repeated border in its own coordinate system.
"""
import hashlib
import json
from pathlib import Path
import re
import struct

from badge_story_layer import read

PATH = 'src/fieldmap.c'
REPRO_CASES = [
    dict(map='JourneySurfLink03502', player=[4, 0], direction='up',
         neighbor='JourneySurfLink03503', target=[1, 65],
         cell=[-1, 1], neighbor_cell=[-4, 67], expected_metatile=0x12B,
         source_map='JourneySurfLink03501', source_cell=[111, 1]),
    dict(map='JourneySurfLink03502', player=[0, 1], direction='left',
         neighbor='JourneySurfLink03501', target=[111, 1],
         cell=[4, -1], neighbor_cell=[116, -1], expected_metatile=0x12B,
         source_map='JourneySurfLink03503', source_cell=[1, 65]),
]

C_HELPERS = r'''
// Generated ocean routes can expose a third map around an elbow. Resolve its
// artwork only: the underlying undefined cell must retain its invalid movement
// boundary, collision and elevation. At most two cardinal hops are inspected.
static bool8 JourneyMarineViewGroup(u16 group)
{
    return group == MAP_GROUP(MAP_JOURNEYSURFLINK00000)
        || group == MAP_GROUP(MAP_JOURNEYSURFLINK03002);
}

static bool8 JourneyMarineViewMap(const struct MapHeader *header)
{
    s32 i;
    if (header->mapType != MAP_TYPE_ROUTE && header->mapType != MAP_TYPE_OCEAN_ROUTE
        && header->mapType != MAP_TYPE_TOWN && header->mapType != MAP_TYPE_CITY)
        return FALSE;
    if (JourneyMarineViewGroup(gSaveBlock1Ptr->location.mapGroup))
        return TRUE;
    if (header->connections == NULL)
        return FALSE;
    for (i = 0; i < header->connections->count; i++)
    {
        const struct MapConnection *c = &header->connections->connections[i];
        if (c->direction >= CONNECTION_SOUTH && c->direction <= CONNECTION_EAST
            && JourneyMarineViewGroup(c->mapGroup))
            return TRUE;
    }
    return FALSE;
}

static u16 JourneyMarineTranslateBlock(const struct MapLayout *from,
                                      const struct MapLayout *to, u16 block)
{
    u16 id = block & MAPGRID_METATILE_ID_MASK;
    u16 translated;
    if (from->isFrlg == to->isFrlg)
        return block;
    translated = (to->isFrlg ? 0x112B : 0x1170) | (block & MAPGRID_COLLISION_MASK);
    if (id == (to->isFrlg ? 0x1F9 : 0x243))
        translated = (block & ~MAPGRID_METATILE_ID_MASK) | (to->isFrlg ? 0x243 : 0x1F9);
    else if (JourneyMarineViewMap(&gMapHeader) && !to->isFrlg
        && ((id >= 0x110 && id <= 0x111) || (id >= 0x118 && id <= 0x119)))
        translated = (block & ~MAPGRID_METATILE_ID_MASK) | (id + 0x40);
    else if (JourneyMarineViewMap(&gMapHeader) && to->isFrlg
        && ((id >= 0x150 && id <= 0x151) || (id >= 0x158 && id <= 0x159)))
        translated = (block & ~MAPGRID_METATILE_ID_MASK) | (id - 0x40);
    else if (!to->isFrlg && ((id >= 0x10C && id <= 0x10E) || (id >= 0x114 && id <= 0x116) || (id >= 0x11C && id <= 0x11E)))
        translated = (block & ~MAPGRID_METATILE_ID_MASK) | (id + 15);
    else if (to->isFrlg && ((id >= 0x11B && id <= 0x11D) || (id >= 0x123 && id <= 0x125) || (id >= 0x12B && id <= 0x12D)))
        translated = (block & ~MAPGRID_METATILE_ID_MASK) | (id - 15);
    return translated;
}

static bool8 JourneyMarineConnectionOrigin(const struct MapLayout *from,
    const struct MapConnection *connection, const struct MapHeader **next, s32 *x, s32 *y)
{
    *next = GetMapHeaderFromConnection(connection);
    if (*next == NULL)
        return FALSE;
    *x = *y = 0;
    switch (connection->direction)
    {
    case CONNECTION_WEST: *x = -(*next)->mapLayout->width; *y = connection->offset; break;
    case CONNECTION_EAST: *x = from->width; *y = connection->offset; break;
    case CONNECTION_NORTH: *x = connection->offset; *y = -(*next)->mapLayout->height; break;
    case CONNECTION_SOUTH: *x = connection->offset; *y = from->height; break;
    default: return FALSE;
    }
    return TRUE;
}

static bool8 JourneyMarineViewCompatible(const struct MapLayout *from, u16 block, u16 *result)
{
    const struct MapLayout *to = gMapHeader.mapLayout;
    u16 id = block & MAPGRID_METATILE_ID_MASK;
    u16 translated = JourneyMarineTranslateBlock(from, to, block) & MAPGRID_METATILE_ID_MASK;
    u32 cutoff, i, j;
    const struct Tileset *a, *b;
    const u16 *wordsA, *wordsB;
    if (from->isFrlg != to->isFrlg)
    {
        // Unknown objects must not become an invented patch of ocean.
        if (id != (from->isFrlg ? 0x12B : 0x170)
            && id != (from->isFrlg ? 0x243 : 0x1F9)
            && !((from->isFrlg ? 0x110 : 0x150) <= id && id <= (from->isFrlg ? 0x111 : 0x151))
            && !((from->isFrlg ? 0x118 : 0x158) <= id && id <= (from->isFrlg ? 0x119 : 0x159))
            && !(from->isFrlg && ((id >= 0x10C && id <= 0x10E) || (id >= 0x114 && id <= 0x116) || (id >= 0x11C && id <= 0x11E)))
            && !(!from->isFrlg && ((id >= 0x11B && id <= 0x11D) || (id >= 0x123 && id <= 0x125) || (id >= 0x12B && id <= 0x12D))))
            return FALSE;
        *result = translated;
        return TRUE;
    }
    cutoff = GetNumMetatilesInPrimary(to);
    a = id < cutoff ? from->primaryTileset : from->secondaryTileset;
    b = id < cutoff ? to->primaryTileset : to->secondaryTileset;
    id = id < cutoff ? id : id - cutoff;
    if (from->isFrlg)
    {
        if (((const u32 *)a->metatileAttributes)[id] != ((const u32 *)b->metatileAttributes)[id])
            return FALSE;
    }
    else if (a->metatileAttributes[id] != b->metatileAttributes[id])
        return FALSE;
    wordsA = &a->metatiles[id * NUM_TILES_PER_METATILE];
    wordsB = &b->metatiles[id * NUM_TILES_PER_METATILE];
    for (i = 0; i < NUM_TILES_PER_METATILE; i++)
    {
        u32 palette;
        if (wordsA[i] != wordsB[i])
            return FALSE;
        a = (wordsA[i] & 0x3FF) < cutoff ? from->primaryTileset : from->secondaryTileset;
        b = (wordsB[i] & 0x3FF) < cutoff ? to->primaryTileset : to->secondaryTileset;
        if (a->tiles != b->tiles || a->callback != b->callback)
            return FALSE;
        palette = wordsA[i] >> 12;
        a = palette < GetNumPalsInPrimary(to) ? from->primaryTileset : from->secondaryTileset;
        b = palette < GetNumPalsInPrimary(to) ? to->primaryTileset : to->secondaryTileset;
        for (j = 0; j < 16; j++)
            if (a->palettes[palette][j] != b->palettes[palette][j])
                return FALSE;
    }
    *result = translated;
    return TRUE;
}

static bool8 JourneyMarineActualView(const struct MapLayout *layout, s32 x, s32 y, u16 *result)
{
    return x >= 0 && y >= 0 && x < layout->width && y < layout->height
        && JourneyMarineViewCompatible(layout, layout->map[y * layout->width + x], result);
}

static bool8 JourneyMarineCornerMetatile(s32 x, s32 y, u16 *result)
{
    const struct MapHeader *current = &gMapHeader;
    s32 i, j;
    bool8 found = FALSE;
    u16 candidate, value = 0;
    if (!JourneyMarineViewMap(current) || current->connections == NULL)
        return FALSE;
    // Actual terrain always precedes repeated border patterns. Keep direct
    // connection order out of the decision when two paths expose one corner.
    for (i = 0; i < current->connections->count; i++)
    {
        const struct MapHeader *next;
        s32 nx, ny;
        if (!JourneyMarineConnectionOrigin(current->mapLayout,
            &current->connections->connections[i], &next, &nx, &ny))
            continue;
        if (JourneyMarineActualView(next->mapLayout, x - nx, y - ny, &candidate))
        {
            if (found && candidate != value) return FALSE;
            value = candidate; found = TRUE;
        }
        if (next->connections == NULL)
            continue;
        for (j = 0; j < next->connections->count; j++)
        {
            const struct MapHeader *other;
            s32 ox, oy;
            if (JourneyMarineConnectionOrigin(next->mapLayout,
                &next->connections->connections[j], &other, &ox, &oy)
                && JourneyMarineActualView(other->mapLayout, x - nx - ox, y - ny - oy, &candidate))
            {
                if (found && candidate != value) return FALSE;
                value = candidate; found = TRUE;
            }
        }
    }
    if (found)
    {
        *result = value;
        return TRUE;
    }
    // Continue a connected map's outer pattern only on its side of the seam.
    // Local modulo preserves the phase for odd dimensions and signed offsets.
    for (i = 0; i < current->connections->count; i++)
    {
        const struct MapConnection *c = &current->connections->connections[i];
        const struct MapHeader *next;
        const struct MapLayout *layout;
        s32 nx, ny, xx, yy, bw, bh;
        if (!JourneyMarineConnectionOrigin(current->mapLayout, c, &next, &nx, &ny))
            continue;
        if (!((c->direction == CONNECTION_WEST && x < 0)
            || (c->direction == CONNECTION_EAST && x >= current->mapLayout->width)
            || (c->direction == CONNECTION_NORTH && y < 0)
            || (c->direction == CONNECTION_SOUTH && y >= current->mapLayout->height)))
            continue;
        layout = next->mapLayout;
        bw = layout->isFrlg ? layout->borderWidth : 2;
        bh = layout->isFrlg ? layout->borderHeight : 2;
        if (bw == 0 || bh == 0)
            continue;
        xx = (x - nx) % bw; if (xx < 0) xx += bw;
        yy = (y - ny) % bh; if (yy < 0) yy += bh;
        if (JourneyMarineViewCompatible(layout, layout->border[xx + yy * bw], &candidate))
        {
            if (found && candidate != value) return FALSE;
            value = candidate; found = TRUE;
        }
    }
    if (found) *result = value;
    return found;
}
'''


def repair(layer):
    original = read(layer, PATH)
    text = original.decode()
    assert 'JourneyMarineCornerMetatile' not in text
    anchor = 'static void FillConnection(int x, int y, struct MapHeader const *connectedMapHeader, int x2, int y2, int width, int height)\n{'
    assert text.count(anchor) == 1
    text = text.replace(anchor, C_HELPERS + '\n' + anchor)
    start = text.index('                u16 id = src[j] & 0x3FF;', text.index(anchor))
    end = text.index('                dest[j] = translated;', start) + len('                dest[j] = translated;')
    text = text[:start] + ('                dest[j] = JourneyMarineTranslateBlock(connectedMapHeader->mapLayout,\n'
                         '                    gMapHeader.mapLayout, src[j]);') + text[end:]
    unused = '            u16 water = gMapHeader.mapLayout->isFrlg ? 0x112B : 0x1170;\n'
    assert text.count(unused) == 1
    text = text.replace(unused, '')
    branch = '    if (block == MAPGRID_UNDEFINED)\n        return GetBorderBlockAt(x, y) & MAPGRID_METATILE_ID_MASK;'
    assert text.count(branch) == 1
    text = text.replace(branch, '''    if (block == MAPGRID_UNDEFINED)
    {
        u16 visible;
        if (JourneyMarineCornerMetatile(x - MAP_OFFSET, y - MAP_OFFSET, &visible))
            return visible;
        return GetBorderBlockAt(x, y) & MAPGRID_METATILE_ID_MASK;
    }''')
    # Everything outside the drawing lookup and cross-format graphic translation
    # remains byte-identical; in particular no map-grid write is added.
    layer.stage(PATH, text)
    return dict(kind='marine-boundary-camera', changed_paths=[PATH],
        before_sha256=hashlib.sha256(original).hexdigest(),
        after_sha256=hashlib.sha256(text.encode()).hexdigest(),
        generated_surf_groups=['JourneySurfLinks0', 'JourneySurfLinks1'],
        immediate_cardinal_coasts_only=True, maximum_graph_hops=2,
        undefined_grid_collision_elevation_and_connection_validity_preserved=True,
        map_blocks_events_connections_and_world_map_unchanged=True,
        cross_format_complete_small_and_large_reefs_translated=True,
        added_large_reef_translation_scoped_to_marine_camera_maps=True,
        ambiguous_actual_terrain_and_border_candidates_retain_current_border=True,
        same_format_art_attributes_graphics_callbacks_and_palettes_checked=True,
        reproduction_cases=REPRO_CASES)


def translate_block(word, source_frlg, target_frlg):
    """Mirror the native mapper for source-camera audits, including complete reefs."""
    if source_frlg == target_frlg:
        return word
    mid = word & 1023
    if mid == (0x1F9 if target_frlg else 0x243):
        return (word & ~1023) | (0x243 if target_frlg else 0x1F9)
    if not target_frlg and (0x110 <= mid <= 0x111 or 0x118 <= mid <= 0x119):
        return (word & ~1023) | (mid + 0x40)
    if target_frlg and (0x150 <= mid <= 0x151 or 0x158 <= mid <= 0x159):
        return (word & ~1023) | (mid - 0x40)
    if not target_frlg and (0x10C <= mid <= 0x10E or 0x114 <= mid <= 0x116 or 0x11C <= mid <= 0x11E):
        return (word & ~1023) | (mid + 15)
    if target_frlg and (0x11B <= mid <= 0x11D or 0x123 <= mid <= 0x125 or 0x12B <= mid <= 0x12D):
        return (word & ~1023) | (mid - 15)
    return (0x112B if target_frlg else 0x1170) | (word & 0xC00)


def audit_camera_holes(source):
    """Return exact previously missed elbow fixtures for source/native validators.

    This reports source facts; the native validator still needs a controller
    crossing and real MapGridGetMetatileIdAt/BG/scanout checks for both cameras.
    """
    source = Path(source)
    layouts = {row['id']: row for row in json.loads((source/'data/layouts/layouts.json').read_bytes())['layouts']}
    maps = {p.parent.name: json.loads(p.read_bytes()) for p in (source/'data/maps').glob('*/map.json')}
    rows = []
    for case in REPRO_CASES:
        layout = layouts[maps[case['source_map']]['layout']]
        x, y = case['source_cell']
        raw = (source/layout['blockdata_filepath']).read_bytes()
        block = struct.unpack_from('<H', raw, 2*(y*layout['width']+x))[0]
        current = layouts[maps[case['map']]['layout']]
        neighbor = layouts[maps[case['neighbor']]['layout']]
        border = (source/neighbor['border_filepath']).read_bytes()
        bx, by = case['neighbor_cell']
        bw = neighbor.get('border_width', 2)
        bh = neighbor.get('border_height', 2)
        previous = struct.unpack_from('<H', border, 2*((bx % bw)+(by % bh)*bw))[0] & 1023
        rows.append(dict(case, historical_expected_metatile=case['expected_metatile'],
                         expected_metatile=block & 1023, source_block=block,
                         previous_neighbor_border_metatile=previous,
                         same_primary=current['primary_tileset'] == neighbor['primary_tileset'],
                         source_blockdata_sha256=hashlib.sha256(raw).hexdigest()))
    return dict(kind='marine-camera-hole-reproductions', cases=rows,
                source_inspection_only=True, native_controller_and_scanout_proof_required=True)
