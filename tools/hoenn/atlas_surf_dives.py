"""Attach five authenticated Dive sites to the affine physical sea mesh.

The underwater layouts, actors and cave portals stay intact. Only their obsolete
Emerge links are removed. SetDiveWarp receives a tri-state resolver before the
legacy connection lookup; the field move continues through native DoDiveWarp.
Surface patches require an explicit, bank-compatible Emerald deep-water donor.
This prepares source and does not certify native travel or release ROMs.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile

from atlas_surf_runtime import _replace_once, bind_groups
from atlas_surf_source import Source
from badge_story_layer import read


HEADER_PATH = 'src/data/journey_atlas_dives.h'
SITES = (
    ('Mares', (125, 68), (38, 10)),
    ('Origens', (135, 87), (38, 10)),
    ('Profundezas', (134, 97), (38, 10)),
    ('Dimensoes', (13, 89), (30, 64)),
    ('Abismo', (14, 99), (30, 64)),
)
OLD_SURFACES = dict(Mares='JourneyHoennNorthSea', Origens='JourneyHoennMiddleSea',
                    Profundezas='JourneyHoennSouthSea', Dimensoes='JourneyRustboroCoast',
                    Abismo='JourneyDewfordCoast')


def patch_specs():
    """Return explicit reservations for the five fixed icons, never new art."""
    return [dict(name=name, depth='JourneyDepth' + name,
                 sanctuary='JourneySanctuary' + name,
                 atlas=list(atlas), portal=list(portal),
                 depth_origin=[8 * atlas[k] + 4 - portal[k] for k in range(2)],
                 depth_arrival=[portal[0], portal[1] + 2],
                 global_rect=[8 * atlas[0] + 2, 8 * atlas[1] + 5, 5, 3],
                 preferred_donor_banks=dict(layout_version='emerald',
                                           primary_tileset='gTileset_General',
                                           secondary_tileset='gTileset_Mossdeep'))
            for name, atlas, portal in SITES]


def _owner(plan, x, y):
    owners = [c for c in plan['chunks'] if c['origin'][0] <= x < c['origin'][0] + c['width']
              and c['origin'][1] <= y < c['origin'][1] + c['height']]
    if len(owners) != 1:
        raise ValueError(('Dive patch needs one real physical owner', x, y, len(owners)))
    return owners[0]


def _runs(cells):
    rows = {}
    for x, y in cells:
        rows.setdefault(y, set()).add(x)
    result = []
    for y, values in sorted(rows.items()):
        values = sorted(values)
        start = previous = values[0]
        for x in values[1:]:
            if x != previous + 1:
                result.append([y, start, previous + 1])
                start = x
            previous = x
        result.append([y, start, previous + 1])
    return result


def reserve_patches(plan):
    """Reserve patch cells before map materialization and scenery placement.

    Existing bounding rectangles must already own every cell. This function
    neither invents an offshore map nor enlarges a rectangle to reach an icon.
    The caller must authenticate the surrounding route/access against the art.
    """
    if plan.get('scale') != 8:
        raise ValueError('Dive geometry requires the authenticated eight-tile scale')
    result = deepcopy(plan)
    reservations = patch_specs()
    if result.get('dive_reservations') not in (None, reservations):
        raise ValueError('Existing Dive reservations disagree with the fixed sites')
    changed = {}
    for site in reservations:
        left, top, width, height = site['global_rect']
        for gy in range(top, top + height):
            for gx in range(left, left + width):
                chunk = _owner(result, gx, gy)
                name = chunk['name']
                if name not in changed:
                    changed[name] = {(x, y) for y, start, end in chunk['water_runs']
                                     for x in range(start, end)}
                changed[name].add((gx - chunk['origin'][0], gy - chunk['origin'][1]))
    for chunk in result['chunks']:
        if chunk['name'] in changed:
            chunk['water_runs'] = _runs(changed[chunk['name']])
    result['dive_reservations'] = reservations
    result['water_tiles'] = sum(end - start for c in result['chunks'] for _, start, end in c['water_runs'])
    return result


class _Terrain:
    """Read staged geometry with the same compiled enum oracle as source audits."""
    def __init__(self, layer):
        self.layer = layer
        self.source = layer.source
        self._attrs, self._flags, self._maps = {}, None, {}
        self.layouts = {r['id']: r for r in json.loads(read(layer, 'data/layouts/layouts.json'))['layouts']}

    def read(self, path):
        return read(self.layer, path)

    def mapping(self, name):
        if name not in self._maps:
            self._maps[name] = json.loads(self.read(f'data/maps/{name}/map.json'))
        return self._maps[name]

    def layout(self, name):
        return self.layouts[self.mapping(name)['layout']]

    def values(self, name):
        layout = self.layout(name)
        raw = self.read(layout['blockdata_filepath'])
        if len(raw) != 2 * layout['width'] * layout['height']:
            raise ValueError(('Dive input dimensions disagree with block data', name))
        return list(struct.unpack('<' + 'H' * (len(raw) // 2), raw))

    def word(self, name, x, y):
        layout = self.layout(name)
        if not (0 <= x < layout['width'] and 0 <= y < layout['height']):
            raise ValueError(('Dive cell outside its real map', name, x, y))
        return self.values(name)[y * layout['width'] + x]

    behavior = Source.behavior
    behavior_flags = Source.behavior_flags

    def surfable(self, name, word):
        value = self.behavior(name, word)
        flags = self.behavior_flags
        if value >= len(flags['values']):
            raise ValueError(('Dive behavior outside the compiled native enum', name, value))
        return bool(flags['values'][value] & flags['surf_flag'])

    def dive_behaviors(self):
        compiler = shutil.which('cc') or shutil.which('gcc')
        if compiler is None:
            raise RuntimeError('C compiler required to authenticate the native Dive enum')
        self.read('include/constants/metatile_behaviors.h')
        code = ('#include <stdio.h>\n#include "constants/metatile_behaviors.h"\n'
                'int main(void) { printf("%u %u %u\\n", MB_INTERIOR_DEEP_WATER, '
                'MB_DEEP_WATER, MB_SOOTOPOLIS_DEEP_WATER); return 0; }\n')
        with tempfile.TemporaryDirectory(prefix='atlas-dive-enum-') as temporary:
            target = Path(temporary) / 'values'
            subprocess.run([compiler, '-std=gnu17', '-Wall', '-Wextra', '-Werror',
                            '-iquote', str(self.source / 'include'), '-x', 'c', '-', '-o', str(target)],
                           input=code, text=True, check=True, capture_output=True)
            return {int(value) for value in subprocess.check_output([str(target)], text=True).split()}


def _identity(groups, name):
    found = [(i, groups[group].index(name)) for i, group in enumerate(groups['group_order'])
             if name in groups[group]]
    if len(found) != 1:
        raise ValueError(('Dive map requires one native identity', name))
    group, number = found[0]
    if not 0 <= group < 128 or not 0 <= number < 128:
        raise ValueError(('Dive destination exceeds signed WarpData ABI', name, group, number))
    return (group << 8) | number


def _authenticate_donor(terrain, donor):
    name, point = donor['map'], donor['tile']
    if not (terrain.source / f'data/maps/{name}/map.json').is_file():
        raise ValueError('Dive donor must be a real preserved native map')
    layout = terrain.layout(name)
    if layout['layout_version'] != 'emerald':
        raise ValueError('Dive donor must use an authenticated Emerald bank')
    word = terrain.word(name, *point)
    behavior = terrain.behavior(name, word)
    if word & 0xC00 or word >> 12 != 1 or behavior not in terrain.dive_behaviors():
        raise ValueError(('Donor is not passable native deep water at Surf height', name, point))
    if not terrain.surfable(name, word):
        raise ValueError('Native Dive donor is not Surfable in the compiled behavior table')
    return word, dict(map=name, tile=list(point), word=word, behavior=behavior,
                      layout_version=layout['layout_version'],
                      banks=[layout['primary_tileset'], layout['secondary_tileset']],
                      blockdata_sha256=hashlib.sha256(terrain.read(layout['blockdata_filepath'])).hexdigest())


def render_header(sites):
    """Small shared data/GPS header; five Depth lookups require no cell grid."""
    code = '''// Generated by atlas_surf_dives.py; include after indexed Atlas runtime.
#ifndef GUARD_JOURNEY_ATLAS_DIVES_H
#define GUARD_JOURNEY_ATLAS_DIVES_H
struct JourneyAtlasDiveSite { u16 depth; s16 x, y; u16 width, height; s16 left, top; u16 patchWidth, patchHeight; };
static const struct JourneyAtlasDiveSite sAtlasDiveSites[] = {
'''
    for site in sites:
        x, y = site['depth_origin']
        left, top, width, height = site['global_rect']
        code += '    {%d,%d,%d,%d,%d,%d,%d,%d,%d},\n' % (
            site['depth_id'], x, y, *site['depth_dimensions'], left, top, width, height)
    code += '''};
static const struct JourneyAtlasDiveSite *JourneyAtlasDepthSite(u16 map)
{
    u32 i;
    for (i = 0; i < ARRAY_COUNT(sAtlasDiveSites); i++)
        if (sAtlasDiveSites[i].depth == map)
            return &sAtlasDiveSites[i];
    return NULL;
}

static bool8 JourneyAtlasDepthPosition(u16 group, u16 number, s16 x, s16 y, u16 *result)
{
    const struct JourneyAtlasDiveSite *site = JourneyAtlasDepthSite((group << 8) | number);
    s32 px, py;
    if (site == NULL)
        return FALSE;
    px = JourneyAtlasFloor8(site->x + (s32)x);
    py = JourneyAtlasFloor8(site->y + (s32)y);
    if (px < 0 || px > 255 || py < 0 || py > 255)
        return FALSE;
    *result = px | (py << 8);
    return TRUE;
}
#endif
'''
    return code


HELPERS = r'''
// Read the target layout's real attribute bank. The engine convenience getter
// uses gMapHeader and therefore cannot authenticate another map's terrain.
static u16 JourneyAtlasDiveBehavior(const struct MapLayout *layout, u16 word)
{
    u16 mid = word & MAPGRID_METATILE_ID_MASK;
    u32 cutoff;
    const struct Tileset *bank;
    if (layout == NULL || mid >= NUM_METATILES_TOTAL)
        return 0xFFFF;
    cutoff = GetNumMetatilesInPrimary(layout);
    bank = mid < cutoff ? layout->primaryTileset : layout->secondaryTileset;
    if (bank == NULL || bank->metatileAttributes == NULL)
        return 0xFFFF;
    if (mid >= cutoff) mid -= cutoff;
    if (layout->isFrlg)
        return ((const u32 *)bank->metatileAttributes)[mid] & METATILE_ATTR_BEHAVIOR_MASK_FRLG;
    return ((const u16 *)bank->metatileAttributes)[mid] & METATILE_ATTR_BEHAVIOR_MASK;
}

static bool8 JourneyAtlasDiveSurfaceCell(const struct MapHeader *header, s32 x, s32 y, bool8 requireDive)
{
    const struct MapLayout *layout;
    u16 word, behavior;
    if (header == NULL || header->mapLayout == NULL || header->mapType == MAP_TYPE_UNDERWATER)
        return FALSE;
    layout = header->mapLayout;
    if (x < 0 || y < 0 || x >= layout->width || y >= layout->height)
        return FALSE;
    word = layout->map[y * layout->width + x];
    behavior = JourneyAtlasDiveBehavior(layout, word);
    if ((word & MAPGRID_COLLISION_MASK) || (word >> MAPGRID_ELEVATION_SHIFT) != ELEVATION_SURF
        || behavior > 255 || !MetatileBehavior_IsSurfableWaterOrUnderwater(behavior))
        return FALSE;
    return !requireDive || MetatileBehavior_IsDiveable(behavior);
}

static bool8 JourneyAtlasDiveDepthCell(const struct MapHeader *header, s32 x, s32 y)
{
    const struct MapLayout *layout;
    u16 word, behavior;
    if (header == NULL || header->mapLayout == NULL || header->mapType != MAP_TYPE_UNDERWATER)
        return FALSE;
    layout = header->mapLayout;
    if (x < 0 || y < 0 || x >= layout->width || y >= layout->height)
        return FALSE;
    word = layout->map[y * layout->width + x];
    behavior = JourneyAtlasDiveBehavior(layout, word);
    return !(word & MAPGRID_COLLISION_MASK)
        && (word >> MAPGRID_ELEVATION_SHIFT) == ELEVATION_DEFAULT
        && behavior <= 255 && !MetatileBehavior_IsUnableToEmerge(behavior);
}

// -1 means an unrelated native map; 0 rejects an Atlas request; 1 resolved it.
// Returning 0 must not fall back to an obsolete Surface/Depth connection.
static s8 JourneyAtlasSetDiveWarp(enum Connection dir, u16 x, u16 y)
{
    u16 map = (gSaveBlock1Ptr->location.mapGroup << 8) | gSaveBlock1Ptr->location.mapNum;
    const struct JourneyAtlasDiveSite *site = JourneyAtlasDepthSite(map);
    const struct JourneyAtlasChunk *chunk;
    const struct MapHeader *target;
    s32 gx, gy, xx, yy;
    u32 i;
    if (site != NULL)
    {
        if (dir != CONNECTION_EMERGE || x >= site->width || y >= site->height
            || !JourneyAtlasDiveDepthCell(&gMapHeader, x, y))
            return 0;
        gx = site->x + x; gy = site->y + y;
        chunk = JourneyAtlasWorldChunk(gx, gy);
        if (chunk == NULL)
            return 0;
        xx = gx - chunk->x; yy = gy - chunk->y;
        target = Overworld_GetMapHeaderByGroupAndId(chunk->map >> 8, chunk->map & 255);
        if ((chunk->map >> 8) >= 128 || (chunk->map & 255) >= 128
            || xx < 0 || yy < 0 || xx >= 128 || yy >= 128
            || !JourneyAtlasDiveSurfaceCell(target, xx, yy, FALSE))
            return 0;
        SetWarpDestination(chunk->map >> 8, chunk->map & 255, WARP_ID_NONE, xx, yy);
        return 1;
    }
    chunk = JourneyAtlasChunk(gSaveBlock1Ptr->location.mapGroup, gSaveBlock1Ptr->location.mapNum);
    if (chunk == NULL)
        return -1;
    if (dir != CONNECTION_DIVE || x >= chunk->width || y >= chunk->height
        || !JourneyAtlasDiveSurfaceCell(&gMapHeader, x, y, TRUE))
        return 0;
    gx = chunk->x + x; gy = chunk->y + y;
    for (i = 0; i < ARRAY_COUNT(sAtlasDiveSites); i++)
    {
        site = &sAtlasDiveSites[i];
        if (gx < site->left || gy < site->top || gx >= site->left + site->patchWidth
            || gy >= site->top + site->patchHeight)
            continue;
        xx = gx - site->x; yy = gy - site->y;
        target = Overworld_GetMapHeaderByGroupAndId(site->depth >> 8, site->depth & 255);
        if ((site->depth >> 8) >= 128 || (site->depth & 255) >= 128
            || xx < 0 || yy < 0 || xx >= 128 || yy >= 128
            || !JourneyAtlasDiveDepthCell(target, xx, yy))
            return 0;
        SetWarpDestination(site->depth >> 8, site->depth & 255, WARP_ID_NONE, xx, yy);
        return 1;
    }
    return 0;
}
'''


def stage(layer, plan, *, donor):
    """Stage the five real sites after geometry/runtime and before freezing.

    ``donor`` must name a native Emerald map and a real Diveable Surf tile.
    Patch chunks must have exactly those graphics banks; unknown FRLG IDs are
    refused. Reservations must already have been materialized as clear water.
    """
    reservations = patch_specs()
    if plan.get('dive_reservations') != reservations:
        raise ValueError('Reserve all five authenticated Dive patches before staging')
    groups = json.loads(read(layer, 'data/maps/map_groups.json'))
    bound = bind_groups(plan, groups)
    for chunk in bound['chunks']:
        if chunk['group_index'] >= 128 or chunk['number'] >= 128:
            raise ValueError('Atlas Dive mesh exceeds signed warp map identity')
    terrain = _Terrain(layer)
    word, witness = _authenticate_donor(terrain, donor)
    banks = witness['banks']
    diveable = terrain.dive_behaviors()
    sites, updates, patches = [], {}, {}
    preserved = {}
    for spec in reservations:
        spec = deepcopy(spec)
        theme, depth, sanctuary = spec['name'], spec['depth'], spec['sanctuary']
        old_surface = OLD_SURFACES[theme]
        depth_map = deepcopy(terrain.mapping(depth))
        sanctuary_map = terrain.mapping(sanctuary)
        if depth_map['map_type'] != 'MAP_TYPE_UNDERWATER':
            raise ValueError(('Preserved Depth is not underwater', depth))
        portal = spec['portal']
        portals = [row for row in depth_map.get('warp_events') or []
                   if [row['x'], row['y']] == portal and row['dest_map'] == sanctuary_map['id']]
        if len(portals) != 1:
            raise ValueError(('Preserved real Depth portal changed', depth, portal))
        interior_warp = int(portals[0]['dest_warp_id'])
        reciprocal = sanctuary_map['warp_events'][interior_warp]
        if reciprocal['dest_map'] != depth_map['id']:
            raise ValueError(('Sanctuary return no longer targets its Depth', sanctuary))
        depth_layout = terrain.layout(depth)
        spec.update(depth_id=_identity(groups, depth),
                    depth_dimensions=[depth_layout['width'], depth_layout['height']],
                    old_surface=old_surface)
        if any(value >= 128 for value in spec['depth_dimensions']):
            raise ValueError(('Depth dimensions exceed signed warp coordinates', depth))
        old_surface_map = deepcopy(updates.get(old_surface, terrain.mapping(old_surface)))
        depth_links = depth_map.get('connections') or []
        old_emerge = [row for row in depth_links if row['direction'] == 'emerge']
        if len(old_emerge) != 1 or old_emerge[0]['map'] != old_surface_map['id']:
            raise ValueError(('Refusing to remove an unauthenticated Depth Emerge link', depth))
        old_dive = [row for row in old_surface_map.get('connections') or []
                    if row['direction'] == 'dive' and row['map'] == depth_map['id']]
        if len(old_dive) != 1:
            raise ValueError(('Refusing to remove an unauthenticated surface Dive link', old_surface))
        depth_map['connections'] = [row for row in depth_links if row not in old_emerge]
        old_surface_map['connections'] = [row for row in old_surface_map.get('connections') or []
                                          if row not in old_dive]
        updates[depth], updates[old_surface] = depth_map, old_surface_map
        preserved[depth] = dict(layout=depth_map['layout'],
                                blockdata_sha256=hashlib.sha256(terrain.read(depth_layout['blockdata_filepath'])).hexdigest(),
                                events_sha256=hashlib.sha256(json.dumps({field: depth_map.get(field) for field in (
                                    'object_events', 'warp_events', 'coord_events', 'bg_events')}, sort_keys=True).encode()).hexdigest())
        left, top, width, height = spec['global_rect']
        for gy in range(top, top + height):
            for gx in range(left, left + width):
                chunk = _owner(bound, gx, gy)
                name = chunk['name']
                mapping, layout = terrain.mapping(name), terrain.layout(name)
                if (layout['layout_version'] != 'emerald'
                        or [layout['primary_tileset'], layout['secondary_tileset']] != banks):
                    raise ValueError(('Dive patch requires authenticated donor graphics banks', name, banks))
                x, y = gx - chunk['origin'][0], gy - chunk['origin'][1]
                if not 0 <= x < 128 or not 0 <= y < 128:
                    raise ValueError(('Surface Dive coordinate exceeds signed warp ABI', name, x, y))
                for field in ('object_events', 'warp_events', 'coord_events', 'bg_events'):
                    for event in mapping.get(field) or []:
                        # Reserve a conservative actor/trigger halo. Complete
                        # scenery-footprint review remains an independent proof.
                        if abs(event['x'] - x) <= 4 and abs(event['y'] - y) <= 4:
                            raise ValueError(('Dive patch overlaps an actor or trigger reservation', name, field))
                before = terrain.word(name, x, y)
                if before & 0xC00 or before >> 12 != 1 or not terrain.surfable(name, before):
                    raise ValueError(('Dive patch was not reserved as clear Surf water', name, x, y))
                dx, dy = gx - spec['depth_origin'][0], gy - spec['depth_origin'][1]
                destination = terrain.word(depth, dx, dy)
                if destination & 0xC00 or destination >> 12 != 3:
                    raise ValueError(('Affine Dive arrival intersects preserved Depth terrain', depth, dx, dy))
                if name not in patches:
                    patches[name] = terrain.values(name)
                patches[name][y * layout['width'] + x] = word
        # Check the documented central descent, independently of chunk borders.
        gx, gy = left + 2, top + 1
        if [gx - spec['depth_origin'][0], gy - spec['depth_origin'][1]] != spec['depth_arrival']:
            raise AssertionError('Dive center no longer arrives two tiles below its real portal')
        spec['deep_water_behavior'] = witness['behavior']
        sites.append(spec)
    for name, values in patches.items():
        layout = terrain.layout(name)
        layer.stage(layout['blockdata_filepath'], struct.pack('<' + 'H' * len(values), *values))
    for name, mapping in updates.items():
        layer.stage(f'data/maps/{name}/map.json', json.dumps(mapping, indent=2) + '\n')
    header = render_header(sites)
    layer.stage(HEADER_PATH, header)
    path = 'src/overworld.c'
    overworld = read(layer, path).decode()
    if 'JourneyAtlasSetDiveWarp' in overworld:
        raise ValueError('Atlas Dive resolver already installed')
    overworld = _replace_once(overworld, '#include "global.h"',
                              '#include "global.h"\n#include "data/journey_atlas_runtime.h"\n'
                              '#include "data/journey_atlas_dives.h"')
    anchor = '''static bool8 SetDiveWarp(enum Connection dir, u16 x, u16 y)
{
    const struct MapConnection *connection = GetMapConnection(dir);'''
    replacement = HELPERS + '''
static bool8 SetDiveWarp(enum Connection dir, u16 x, u16 y)
{
    const struct MapConnection *connection;
    s8 atlas = JourneyAtlasSetDiveWarp(dir, x, y);
    if (atlas >= 0)
        return atlas != 0;
    connection = GetMapConnection(dir);'''
    overworld = _replace_once(overworld, anchor, replacement)
    layer.stage(path, overworld)
    world_path = 'src/journey_world_map.c'
    world = read(layer, world_path).decode()
    if '#include "data/journey_atlas_runtime.h"' not in world:
        raise ValueError('Install affine Atlas runtime before the Dive resolver')
    world = _replace_once(world, '#include "data/journey_atlas_runtime.h"',
                          '#include "data/journey_atlas_runtime.h"\n#include "data/journey_atlas_dives.h"')
    anchor = '''    if (JourneyAtlasPosition(gSaveBlock1Ptr->location.mapGroup,
        gSaveBlock1Ptr->location.mapNum, x, y, &atlasPosition))
        return atlasPosition;'''
    world = _replace_once(world, anchor, anchor + '''
    if (JourneyAtlasDepthPosition(gSaveBlock1Ptr->location.mapGroup,
        gSaveBlock1Ptr->location.mapNum, x, y, &atlasPosition))
        return atlasPosition;''')
    layer.stage(world_path, world)
    return dict(kind='atlas-native-dive-affine-sites', sites=sites, donor=witness,
                deep_water_word=word, deep_water_native_behaviors=sorted(diveable),
                patches=sorted(patches), patch_cells=75, preserved_depths=preserved,
                removed_exact_obsolete_dive_and_emerge_links=True,
                native_dive_effect_and_avatar_modes_preserved=True,
                target_layout_attributes_used=True, per_cell_gps_arrays=False,
                signed_warp_abi_checked=True,
                changed_paths=[HEADER_PATH, path, world_path,
                               *[terrain.layout(n)['blockdata_filepath'] for n in sorted(patches)],
                               *[f'data/maps/{n}/map.json' for n in sorted(updates)]],
                source_audit_finalized=False, native_validated=False,
                final_release_validated=False)
