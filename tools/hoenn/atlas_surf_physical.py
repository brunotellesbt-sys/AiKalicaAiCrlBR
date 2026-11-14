"""Stage bounded connection copies and a physical halo for affine Atlas maps.

Call after atlas_surf_runtime.stage. This prepares source; compiled-ROM
travel, camera, bank and timing proofs remain mandatory for every candidate.
"""
import hashlib
import json

from atlas_surf_runtime import _replace_once, bind_groups
from badge_story_layer import read


HEADER_PATH = 'src/data/journey_atlas_physical.h'


HELPERS = r'''
// An Atlas connection may be narrower than the engine's seven-tile apron.
// Intersect source and destination coordinates BEFORE forming any pointer.
static void JourneyAtlasCopyConnection(int x, int y,
    const struct MapHeader *next, int x2, int y2, int width, int height)
{
    s32 i, j, left = 0, top = 0, right = width, bottom = height;
    const struct MapLayout *layout = next->mapLayout;
    u16 word, value;
    if (-x2 > left) left = -x2;
    if (-x > left) left = -x;
    if (-y2 > top) top = -y2;
    if (-y > top) top = -y;
    if (layout->width - x2 < right) right = layout->width - x2;
    if (gBackupMapLayout.width - x < right) right = gBackupMapLayout.width - x;
    if (layout->height - y2 < bottom) bottom = layout->height - y2;
    if (gBackupMapLayout.height - y < bottom) bottom = gBackupMapLayout.height - y;
    for (i = top; i < bottom; i++)
        for (j = left; j < right; j++)
        {
            word = layout->map[(y2 + i) * layout->width + x2 + j];
            value = MAPGRID_UNDEFINED;
            JourneyAtlasPhysicalWord(layout, word, &value);
            gBackupMapLayout.map[(y + i) * gBackupMapLayout.width + x + j] = value;
        }
}

// A direct native coast owns its entrance face, including blocked scenery.
// It precedes global rectangle lookup so a blocked Atlas background cannot
// hide a legitimate return to shore. Conflicting owners fail closed.
static bool8 JourneyAtlasNativeFace(const struct MapHeader *current,
    s32 x, s32 y, u16 *result)
{
    s32 i, nx, ny, xx, yy;
    bool8 found = FALSE;
    u16 candidate, value = MAPGRID_UNDEFINED;
    const struct MapHeader *next;
    const struct MapConnection *connection;
    if (current->connections == NULL)
        return FALSE;
    for (i = 0; i < current->connections->count; i++)
    {
        connection = &current->connections->connections[i];
        if (!((connection->direction == CONNECTION_WEST && x < 0)
            || (connection->direction == CONNECTION_EAST && x >= current->mapLayout->width)
            || (connection->direction == CONNECTION_NORTH && y < 0)
            || (connection->direction == CONNECTION_SOUTH && y >= current->mapLayout->height)))
            continue;
        if (!JourneyMarineConnectionOrigin(current->mapLayout, connection, &next, &nx, &ny)
            || JourneyAtlasHeaderChunk(next) != NULL)
            continue;
        xx = x - nx; yy = y - ny;
        if (xx < 0 || yy < 0 || xx >= next->mapLayout->width || yy >= next->mapLayout->height)
            continue;
        candidate = MAPGRID_UNDEFINED;
        JourneyAtlasPhysicalWord(next->mapLayout,
            next->mapLayout->map[yy * next->mapLayout->width + xx], &candidate);
        if (found && candidate != value)
        {
            *result = MAPGRID_UNDEFINED;
            return TRUE;
        }
        found = TRUE; value = candidate;
    }
    if (found) *result = value;
    return found;
}

static void JourneyAtlasFillPhysicalView(const struct MapHeader *current)
{
    const struct JourneyAtlasChunk *chunk = JourneyAtlasHeaderChunk(current);
    const struct JourneyAtlasChunk *owner;
    const struct MapHeader *next;
    const struct MapLayout *layout;
    s32 x, y, xx, yy, gx, gy;
    u16 value;
    if (chunk == NULL)
        return;
    for (y = 0; y < gBackupMapLayout.height; y++)
        for (x = 0; x < gBackupMapLayout.width; x++)
        {
            xx = x - MAP_OFFSET; yy = y - MAP_OFFSET;
            // Never replace the current map, including runtime changes.
            if (xx >= 0 && yy >= 0 && xx < current->mapLayout->width && yy < current->mapLayout->height)
                continue;
            value = MAPGRID_UNDEFINED;
            if (!JourneyAtlasNativeFace(current, xx, yy, &value))
            {
                gx = chunk->x + xx; gy = chunk->y + yy;
                owner = JourneyAtlasWorldChunk(gx, gy);
                if (owner != NULL)
                {
                    next = Overworld_GetMapHeaderByGroupAndId(owner->map >> 8, owner->map & 255);
                    layout = next->mapLayout;
                    xx = gx - owner->x; yy = gy - owner->y;
                    if (xx >= 0 && yy >= 0 && xx < layout->width && yy < layout->height)
                        JourneyAtlasPhysicalWord(layout, layout->map[yy * layout->width + xx], &value);
                }
            }
            gBackupMapLayout.map[y * gBackupMapLayout.width + x] = value;
        }
}

// A diagonal halo cell may be visible and have real terrain, but crossing a
// face still requires the engine's actual direct connection at that offset.
static bool8 JourneyAtlasBorderConnectionValid(s32 x, s32 y)
{
    const struct JourneyAtlasChunk *chunk = JourneyAtlasHeaderChunk(&gMapHeader);
    const struct JourneyAtlasChunk *owner;
    const struct MapConnection *connection;
    enum Connection direction;
    if (chunk == NULL)
        return TRUE;
    x -= MAP_OFFSET; y -= MAP_OFFSET;
    if (x >= gMapHeader.mapLayout->width) direction = CONNECTION_EAST;
    else if (x < 0) direction = CONNECTION_WEST;
    else if (y >= gMapHeader.mapLayout->height) direction = CONNECTION_SOUTH;
    else if (y < 0) direction = CONNECTION_NORTH;
    else return TRUE;
    if (gMapHeader.connections == NULL || gMapHeader.connections->connections == NULL)
        return FALSE;
    connection = GetIncomingConnection(direction, x, y);
    if (connection == NULL)
        return FALSE;
    if (JourneyAtlasChunk(connection->mapGroup, connection->mapNum) == NULL)
        return TRUE;
    owner = JourneyAtlasWorldChunk(chunk->x + x, chunk->y + y);
    return owner != NULL && owner->map == ((connection->mapGroup << 8) | connection->mapNum);
}
'''


def render_header(plan, layouts, maps):
    """Direct layout identity lookup, independent of transient save position."""
    indices = {row['id']: i+1 for i, row in enumerate(layouts)}
    slots = {}
    for i, chunk in enumerate(plan['chunks']):
        mapping = maps[chunk['name']]
        layout = indices[mapping['layout']]
        if layout in slots:
            raise ValueError('Atlas chunks cannot share one layout identity')
        slots[layout] = i+1
    first, last = min(slots), max(slots)
    if last > 65535 or len(plan['chunks']) > 65534:
        raise ValueError('Atlas physical layout index exceeds native u16')
    values = [slots.get(i, 0) for i in range(first, last+1)]
    if len(values) > 4096:
        raise ValueError('Unreviewed sparse Atlas layout registry')
    code = ('// Generated by atlas_surf_physical.py; include after indexed runtime.\n'
            'static const u16 sAtlasLayoutSlots[] = {' + ','.join(map(str, values)) + '};\n'
            f'#define JOURNEY_ATLAS_LAYOUT_BASE {first}\n')
    code += r'''
static const struct JourneyAtlasChunk *JourneyAtlasHeaderChunk(const struct MapHeader *header)
{
    s32 index;
    u16 slot;
    const struct JourneyAtlasChunk *chunk;
    if (header == NULL || header->mapLayout == NULL)
        return NULL;
    index = (s32)header->mapLayoutId - JOURNEY_ATLAS_LAYOUT_BASE;
    if (index < 0 || index >= (s32)ARRAY_COUNT(sAtlasLayoutSlots))
        return NULL;
    slot = sAtlasLayoutSlots[index];
    if (slot == 0) return NULL;
    chunk = &sAtlasChunks[slot - 1];
    // Reject a stale layoutId paired with a different header/layout.
    return Overworld_GetMapHeaderByGroupAndId(chunk->map >> 8, chunk->map & 255)->mapLayout
        == header->mapLayout ? chunk : NULL;
}
'''
    return code, dict(layout_slots=len(values), layout_index_bytes=2*len(values))


def stage(layer, plan):
    groups = json.loads(read(layer, 'data/maps/map_groups.json'))
    bound = bind_groups(plan, groups)
    layouts = json.loads(read(layer, 'data/layouts/layouts.json'))['layouts']
    maps = {c['name']: json.loads(read(layer, f"data/maps/{c['name']}/map.json")) for c in bound['chunks']}
    header, metadata = render_header(bound, layouts, maps)
    path = 'src/fieldmap.c'
    field = read(layer, path).decode()
    if 'JourneyAtlasFillPhysicalView' in field:
        raise ValueError('Atlas physical runtime already installed')
    if '#include "data/journey_atlas_runtime.h"' not in field:
        raise ValueError('Install indexed Atlas runtime before the physical runtime')
    field = _replace_once(field, '#include "wild_encounter.h"',
                          '#include "wild_encounter.h"\n#include "data/journey_atlas_physical.h"')
    field = _replace_once(field, 'static void InitBackupMapLayoutConnections(struct MapHeader *mapHeader);',
                          'static void InitBackupMapLayoutConnections(struct MapHeader *mapHeader);\n'
                          'static void JourneyAtlasFillPhysicalView(const struct MapHeader *current);')
    field = _replace_once(field, '        InitBackupMapLayoutConnections(mapHeader);',
                          '        if (JourneyAtlasHeaderChunk(mapHeader) != NULL)\n'
                          '            sMapConnectionFlags = sDummyConnectionFlags;\n'
                          '        InitBackupMapLayoutConnections(mapHeader);\n'
                          '        JourneyAtlasFillPhysicalView(mapHeader);')
    # ViewCompatible returns only the metatile. Physical cells must retain
    # all original collision/elevation bits, including transitional height0.
    word = r'''
static bool8 JourneyAtlasPhysicalWord(const struct MapLayout *from, u16 word, u16 *result)
{
    u16 translated;
    if (from->isFrlg == gMapHeader.mapLayout->isFrlg
        && from->primaryTileset == gMapHeader.mapLayout->primaryTileset
        && from->secondaryTileset == gMapHeader.mapLayout->secondaryTileset)
    {
        *result = word;
        return TRUE;
    }
    if (!JourneyMarineViewCompatible(from, word, &translated))
        return FALSE;
    *result = (word & ~MAPGRID_METATILE_ID_MASK) | (translated & MAPGRID_METATILE_ID_MASK);
    return TRUE;
}
'''
    anchor = 'static void FillConnection(int x, int y, struct MapHeader const *connectedMapHeader, int x2, int y2, int width, int height)\n{'
    field = _replace_once(field, anchor, word+HELPERS+'\n'+anchor)
    anchor = '    mapWidth = connectedMapHeader->mapLayout->width;'
    field = _replace_once(field, anchor, '''    if (JourneyAtlasHeaderChunk(&gMapHeader) != NULL
        || JourneyAtlasHeaderChunk(connectedMapHeader) != NULL)
    {
        JourneyAtlasCopyConnection(x, y, connectedMapHeader, x2, y2, width, height);
        return;
    }
''' + anchor)
    anchor = 'enum Connection GetMapBorderIdAt(int x, int y)\n{'
    field = _replace_once(field, anchor, anchor+'''
    if (!JourneyAtlasBorderConnectionValid(x, y))
        return CONNECTION_INVALID;
''')
    layer.stage(HEADER_PATH, header)
    layer.stage(path, field)
    return dict(kind='atlas-physical-halo-and-bounded-connections', **metadata,
                changed_paths=[HEADER_PATH, path], header_sha256=hashlib.sha256(header.encode()).hexdigest(),
                current_map_runtime_cells_preserved=True, native_face_priority=True,
                unknown_bank_translation_fails_closed=True, movement_requires_direct_connection=True,
                historical_non_atlas_copies_preserved=True, per_cell_gps_table=False,
                source_audit_finalized=False, native_validated=False, final_release_validated=False)
