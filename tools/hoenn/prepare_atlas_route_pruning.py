"""Remove the marked H, J and K lanes from the compiled world and chart."""
import argparse
from collections import defaultdict, deque
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import re
import struct

from atlas_surf_background import HEADER, cells, render
from atlas_surf_ecology import DEX_ROW
from atlas_surf_geometry import chunk_water, rasterize
from atlas_surf_overlay import OverlaySource
from atlas_surf_route_borders import _native_core_rectangles, _neighbor, _runs
from atlas_surf_source import CARDINAL, Source
from atlas_surf_truth import array_values, decode_atlas
from badge_story_layer import read
from candidate_layer import Layer
from prepare_atlas_surf_redesign import source_audit
from prepare_generated_area_review import PRIOR, LAYER as PARENT
from validate_atlas_surf_ecology_source import CompiledEcology, census, compare, terrain_triggers

ROOT = Path(__file__).resolve().parents[2]
LAYER = 'atlas-route-pruning'
PRIOR = PRIOR + [PARENT, 'atlas-surf-layout']
PARENT_MARKER_SHA = 'b7ec6da5cb9ff9214dde31505a51edb05206c2d6d12b2e45f1bcb3b94664ff87'
PROJECTION_MARKER_SHA = '580c35cb95ef5b868193b8251e8c50e557ce5fd17d350c698a9c92d2038c8314'
ART = 'src/data/journey_world_map.h'
H = {(126, 86)}
J = {(125, y) for y in range(85, 89)}
K = {(x, 60) for x in range(96, 106) if x != 101}
TRAINER_MAP = 'JourneyAtlasSea326'
TRAINER_START = (10, 9)
TRAINER_DESTINATION = (10, 2)
K_ISLAND = 'JourneyAtlasScene023'
K_ISLAND_DRY_RESCUE = ('JourneyAtlasScene024', 12, 12)


def edit_atlas(header, removed):
    before = decode_atlas(header)
    if not removed <= before.blue_pixels:
        raise ValueError('Removed atlas pixels must all be original route ink')
    tiles = bytearray(array_values(header, 'sWorldTiles'))
    map_entries = list(array_values(header, 'sWorldTilemap'))
    detail = bytearray(array_values(header, 'sWorldDetailPixels'))
    patched_tiles = {}
    for x, y in sorted(removed):
        index = (y // 8 + 3) * 32 + x // 8 + 1
        entry = map_entries[index]
        if entry >> 12:
            raise ValueError(('Unexpected atlas palette bank', x, y))
        start = (entry & 1023) * 32
        tile = patched_tiles.setdefault(index, bytearray(tiles[start:start + 32]))
        lx = 7 - x % 8 if entry & 0x400 else x % 8
        ly = 7 - y % 8 if entry & 0x800 else y % 8
        shift = 4 * (lx % 2)
        offset = ly * 4 + lx // 2
        tile[offset] = tile[offset] & ~(15 << shift) | (1 << shift)
        for yy in (2 * y, 2 * y + 1):
            offset = yy * before.width + x
            value = detail[offset]
            low, high = value & 15, value >> 4
            detail[offset] = (1 if low == 2 else low) | ((1 if high == 2 else high) << 4)

    tile_indices = {bytes(tiles[i:i + 32]): i // 32 for i in range(0, len(tiles), 32)}
    for index, tile in sorted(patched_tiles.items()):
        tile = bytes(tile)
        if tile not in tile_indices:
            tile_indices[tile] = len(tiles) // 32
            tiles.extend(tile)
        map_entries[index] = (map_entries[index] & 0xfc00) | tile_indices[tile]
    if len(tiles) > 32 * 512:
        raise ValueError('Atlas tiles exceed the BG character block')
    for key, values in [('sWorldTiles', tiles), ('sWorldTilemap', map_entries), ('sWorldDetailPixels', detail)]:
        header, count = re.subn(r'(' + key + r'\[\] = \{)[^}]+(\})',
                                lambda m: m[1] + ','.join(map(str, values)) + m[2], header)
        if count != 1:
            raise ValueError(('Missing atlas array', key))
    after = decode_atlas(header)
    expected = list(before.indices)
    for x, y in removed:
        expected[y * before.width + x] = 1
    if tuple(expected) != after.indices or after.palette != before.palette:
        raise ValueError('Atlas edit affected unselected art')
    return header, after.array_sha256


def stage_terrain(layer, source, metadata, removed):
    plan = metadata['geometry_plan']
    pixels = set(map(tuple, plan['route_pixels']))
    if not removed <= pixels:
        raise ValueError('The selected routes are absent from the physical plan')
    bounds = dict(scale=plan['scale'], corridor_width=plan['corridor_width'])
    removed_cells = rasterize(pixels, **bounds) - rasterize(pixels - removed, **bounds)
    plan['route_pixels'] = [p for p in plan['route_pixels'] if tuple(p) not in removed]
    by_name = {row['name']: row for row in plan['chunks']}
    donors = {row['map']: row for row in metadata['geometry']['chunks']}
    affected = defaultdict(set)
    for name, row in by_name.items():
        ox, oy = row['origin']
        for x, y in removed_cells:
            if ox <= x < ox + row['width'] and oy <= y < oy + row['height']:
                affected[name].add((x - ox, y - oy))

    old_water = {n: chunk_water(by_name[n]) for n in affected}
    old_scenery = {n: cells(by_name[n]) for n in affected}
    cut = {(name, x, y) for name, points in affected.items() for x, y in points}
    if len(cut) != len(removed_cells) or any((x, y) not in old_water[n] for n, x, y in cut):
        raise ValueError('The removed route does not match unique active source cells')
    # K formerly exposed an event-free decorative sandbank. Keep its entire
    # footprint, including the water around it, outside the new limit reef.
    island_fringe = {(x, y) for y in range(9, 15) for x in range(8, 18)
                     if (x, y) in old_water[K_ISLAND]}
    island_dry = {(x, y) for y in range(9, 14) for x in range(9, 17)
                  if not source.word(K_ISLAND, x, y) & 0xc00 and (x, y) not in island_fringe}
    if (len(island_fringe) != 31 or not island_dry
            or any(source.maps[K_ISLAND].get(field) for field in
                   ('object_events', 'warp_events', 'coord_events', 'bg_events'))):
        raise ValueError('Expected an intact event-free sandbank beside K')
    all_scenery = {n: cells(row) for n, row in by_name.items()}
    all_scenery[K_ISLAND].update(island_fringe | island_dry)

    def adjacent(point):
        return [_neighbor(source, *point, dx, dy) for dx, dy in CARDINAL.values()]

    def live(point):
        if point is None or point in cut:
            return False
        name, x, y = point
        return (x, y) not in all_scenery.get(name, ()) and not source.word(*point) & 0xc00

    # Keep the connected route accessible and place one blocked reef across
    # each cut mouth. Restore normal water behind that line and clear its old sides.
    cleared = defaultdict(set)
    for point in cut:
        for other in adjacent(point):
            if other is None:
                continue
            n, x, y = other
            if n in affected and source.word(*other) == donors[n]['reef_word']:
                cleared[n].add((x, y))
    changes = {}
    background = set()
    for name, points in sorted(affected.items()):
        row, donor = by_name[name], donors[name]
        width = row['width']
        layout = source.layout(name)
        if (row['kind'] not in ('ordinary', 'stamp')
                or [layout['primary_tileset'], layout['secondary_tileset']] != donor['donor_banks']):
            raise ValueError(('Unexpected variant at route cut', name))
        reef, water = donor['reef_word'], donor['water_word']
        protected = _native_core_rectangles(source, row)
        before = source.words(name)
        after = list(before)
        scenery = set(old_scenery[name])
        abandoned = island_fringe if name == K_ISLAND else set()
        for x, y in points | cleared[name]:
            native_core = any(a <= x < c and b <= y < d for a, b, c, d in protected)
            point = (name, x, y)
            if point in cut and (before[y * width + x] != water or native_core):
                raise ValueError(('Cut overlaps unique native terrain', point))
            if native_core:
                continue
            if any(live(other) for other in adjacent(point)):
                after[y * width + x] = reef
            else:
                after[y * width + x] = water
                scenery.add((x, y))
                background.add(point)
        for field in ('warp_events', 'coord_events', 'bg_events', 'object_events'):
            for event in source.maps[name].get(field) or []:
                x, y = event['x'], event['y']
                if (x, y) in points | cleared[name] and event.get('script') != 'JourneyAtlasSwimmer39':
                    raise ValueError(('Cut overlaps event', name, field, event))
        row['decorative_water_runs'] = _runs(scenery | abandoned)
        row['water_runs'] = _runs(old_water[name] - points - abandoned)
        if not row['water_runs']:
            row['scenery_only'] = True
        changes[name] = sum(a != b for a, b in zip(before, after))
        layer.stage(layout['blockdata_filepath'], struct.pack('<' + 'H' * len(after), *after))

    # The swimmer keeps her real script, flag, elevation and native local ID.
    new_map = deepcopy(source.maps[TRAINER_MAP])
    trainer, = new_map['object_events']
    if trainer['script'] != 'JourneyAtlasSwimmer39' or (trainer['x'], trainer['y']) != TRAINER_START:
        raise ValueError('Unexpected swimmer on J')
    x, y = TRAINER_DESTINATION
    safe_line = {(x, y + step) for step in range(4)}
    if not safe_line <= old_water[TRAINER_MAP] - affected[TRAINER_MAP]:
        raise ValueError('Swimmer relocation lacks a clear sight line')
    trainer.update(x=x, y=y, movement_type='MOVEMENT_TYPE_FACE_DOWN')
    layer.stage(f'data/maps/{TRAINER_MAP}/map.json', json.dumps(new_map, indent=2) + '\n')
    metadata['route_pruning'] = dict(removed_pixels=sorted(removed),
                                     removed_active_cells=len(cut), changed_words_by_map=changes,
                                     new_scenery_cells=len(background) + len(island_fringe))
    return cut | {(K_ISLAND, x, y) for x, y in island_fringe}, adjacent, island_dry


def stage_save_migration(layer, source, view, cut, adjacent, island_dry):
    # The old routes' own connected water determines each nearest safe exit.
    # Start from known usable water adjoining the cut and trace the prior route.
    actor = (TRAINER_MAP, *TRAINER_DESTINATION)
    unavailable = cut | {actor}
    targets = {}
    queue = deque()
    for point in sorted(unavailable):
        for destination in adjacent(point):
            if (destination is not None and destination not in unavailable
                    and source.water(*destination) and view.water(*destination)
                    and source.word(*destination) >> 12 == 1):
                targets[point] = destination
                queue.append(point)
                break
    while queue:
        point = queue.popleft()
        for other in adjacent(point):
            if other in unavailable and other not in targets:
                targets[other] = targets[point]
                queue.append(other)
    if set(targets) != unavailable:
        raise ValueError('Some old Surf save coordinates have no safe target')
    for x, y in island_dry:
        targets[K_ISLAND, x, y] = K_ISLAND_DRY_RESCUE

    moves = []
    for (name, x, y), (dest, tx, ty) in sorted(targets.items(), key=lambda pair: (
            source.identities[pair[0][0]], pair[0][2], pair[0][1])):
        old_id, new_id = source.identities[name], source.identities[dest]
        height = view.word(dest, tx, ty) >> 12
        if height not in (1, 3) or view.word(dest, tx, ty) & 0xc00:
            raise ValueError(('Invalid position for an old save', dest, tx, ty))
        moves.append(f'    {{{old_id}, {x}, {y}, {new_id}, {tx}, {ty}, {height}}},')
    script = MIGRATION.replace('MOVE_ROWS', '\n'.join(moves))
    script = script.replace('SWIMMER_MAP', str(source.identities[TRAINER_MAP]))
    path = 'src/load_save.c'
    text = read(layer, path).decode()
    helper = 'static void JourneyAtlasMigrateCurrentSave(void)\n{\n'
    current_lookup = '''    const struct JourneyAtlasSaveMove *move = JourneyAtlasSavedMove(
        gSaveBlock1Ptr->location.mapGroup, gSaveBlock1Ptr->location.mapNum,
        gSaveBlock1Ptr->pos.x, gSaveBlock1Ptr->pos.y);
'''
    before = helper + current_lookup
    if text.count(before) != 1:
        raise ValueError('Unexpected current save migration helper')
    text = text.replace(before, 'static void JourneyAtlasApplySaveMove(const struct JourneyAtlasSaveMove *move)\n{\n')
    anchor = 'static void JourneyMigrateSeviiSaveGeometryVersion3(void)'
    wrapper = helper + current_lookup + '    JourneyAtlasApplySaveMove(move);\n}\n\n'
    if text.count(anchor) != 1:
        raise ValueError('Missing version 3 migration')
    text = text.replace(anchor, wrapper + anchor)
    version8 = 'static void JourneyMigrateSeviiSaveGeometry(void)'
    entry = 'void CopyPartyAndObjectsFromSave(void)'
    if text.count(version8) != 1 or text.count(entry) != 1:
        raise ValueError('Missing version 8 migration or Continue entry')
    text = text.replace(version8, 'static void JourneyMigrateSeviiSaveGeometryVersion8(void)')
    layer.stage(path, text.replace(entry, script + '\n' + entry))
    return [[*point, *dest] for point, dest in sorted(targets.items())]


def stage_dex(layer, view, graph, metadata, output):
    path = 'src/data/journey_world_dex_locations.h'
    header = read(layer, path).decode()
    reachable = defaultdict(set)
    for key, component in zip(graph.keys, graph.labels):
        if component == graph.ocean_component:
            name, x, y = graph.location(key // 32)
            reachable[name].add((x, y))
    parent_path = ROOT / 'mods/hoenn/versions/evidence/atlas-surf-layout/ecology/graph-bounded.json.gz'
    raw = parent_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != '09e346b3a8afc2632b5e02ef62b7b8fba11bc6c824e8b2f27a19edc738ed7f97':
        raise ValueError('Expected the published Atlas 172 habitat census')
    parent = json.loads(gzip.decompress(raw))
    current = census(view, retired_maps=parent['retired_maps'], reachable_cells=reachable)
    comparison = compare(parent, current)
    if not comparison['preserved']:
        raise ValueError(('Route cut lost a catchable family', comparison['missing_families']))
    catalog = json.loads((ROOT / 'tools/hoenn/catalog_metadata.json').read_bytes())['species']
    species_ids = {r['name']: int(sid) for sid, r in catalog.items()}
    affected = metadata['route_pruning']['changed_words_by_map']
    chunks = {r['name']: r for r in metadata['geometry_plan']['chunks']}
    native = CompiledEcology(view)
    current_triggers = {name: terrain_triggers(view, native, name, reachable[name])[0] for name in affected}
    by_species = defaultdict(set)
    exact = set()
    for row in current['map_areas']:
        name = row['map']
        if name not in chunks or not row['trigger_sample']:
            continue
        ox, oy = chunks[name]['origin']
        triggers = current_triggers[name][row['area']] if name in affected else row['trigger_sample']
        positions = {((ox + x) // 8, (oy + y) // 8) for x, y in triggers}
        for cap, members in row['species'].items():
            for species in members:
                for ax, ay in positions:
                    key = species, cap
                    by_species[key].add((name, ax, ay))
                    if name in affected:
                        exact.add((name, *key, ax, ay))
    emitted = set(DEX_ROW.findall(header))
    moves = []

    def replace(match):
        species, constant, x, y, fixed, cap = match.groups()
        name = view.by_id[constant]
        if name not in affected:
            return match[0]
        key = species_ids[species], '493' if cap == '4' else '1025'
        if (name, *key, int(x), int(y)) in exact:
            return match[0]
        candidates = by_species[key]
        if fixed != '0' or not candidates:
            raise ValueError(('No reachable AREA witness after route cut', match[0]))
        dest, ax, ay = min(candidates, key=lambda p: (
            current['aliases'].get(p[0], p[0]) != parent['aliases'].get(name, name),
            abs(p[1] - int(x)) + abs(p[2] - int(y)), p))
        new_row = (species, chunks[dest]['id'], str(ax), str(ay), '0', cap)
        moves.append(dict(species=species, cap=cap, old=[name, int(x), int(y)], new=[dest, ax, ay]))
        if new_row in emitted:
            return ''
        emitted.add(new_row)
        return '{' + ','.join(new_row) + '}'

    # The initializer is one row per line and each row has a trailing comma.
    new_header = DEX_ROW.sub(replace, header)
    new_header = re.sub(r'^\s*,\s*\n', '', new_header, flags=re.MULTILINE)
    if not moves or not new_header.count('sWorldDexLocations') == 1:
        raise ValueError('Expected the one active AREA table and its obsolete route references')
    layer.stage(path, new_header)
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)
        for name, report in [('graph-bounded', current), ('family-comparison', comparison)]:
            (output / (name + '.json.gz')).write_bytes(
                gzip.compress(json.dumps(report, sort_keys=True).encode(), mtime=0))
    metadata['route_pruning']['dex_relocations'] = moves
    metadata['route_pruning']['catchable_family_counts'] = comparison['after_counts']


MIGRATION = '''// The removed Surf lanes are now ordinary water beyond a continuous reef.
static const struct { u16 map; u8 x, y; u16 toMap; u8 toX, toY, elevation; } sJourneyPrunedRouteMoves[] = {
MOVE_ROWS
};

static bool32 JourneyPrunedRouteMove(u8 group, u8 num, s16 x, s16 y,
                                    struct JourneyAtlasSaveMove *move)
{
    u16 map = ((u16)group << 8) | num;
    u32 i;
    for (i = 0; i < ARRAY_COUNT(sJourneyPrunedRouteMoves); i++)
    {
        if (sJourneyPrunedRouteMoves[i].map != map
         || sJourneyPrunedRouteMoves[i].x != x || sJourneyPrunedRouteMoves[i].y != y)
            continue;
        move->newGroup = sJourneyPrunedRouteMoves[i].toMap >> 8;
        move->newNum = sJourneyPrunedRouteMoves[i].toMap & 255;
        move->dx = sJourneyPrunedRouteMoves[i].toX - x;
        move->dy = sJourneyPrunedRouteMoves[i].toY - y;
        move->elevation = sJourneyPrunedRouteMoves[i].elevation;
        move->mode = move->elevation == 1 ? 2 : 1;
        return TRUE;
    }
    return FALSE;
}

static void JourneyMigrateSeviiSaveGeometry(void)
{
    struct JourneyAtlasSaveMove move = {0};
    struct WarpData *location = &gSaveBlock1Ptr->location;
    struct WarpData *warps[] = {&gSaveBlock1Ptr->continueGameWarp, &gSaveBlock1Ptr->dynamicWarp,
        &gSaveBlock1Ptr->lastHealLocation, &gSaveBlock1Ptr->escapeWarp};
    u32 i;

    if (VarGet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION) >= 9)
        return;
    JourneyMigrateSeviiSaveGeometryVersion8();
    for (i = 0; i < ARRAY_COUNT(warps); i++)
    {
        struct WarpData *warp = warps[i];
        if (warp->warpId < 0 && JourneyPrunedRouteMove(warp->mapGroup, warp->mapNum, warp->x, warp->y, &move))
        {
            warp->mapGroup = move.newGroup;
            warp->mapNum = move.newNum;
            warp->x += move.dx;
            warp->y += move.dy;
        }
    }
    if (JourneyPrunedRouteMove(location->mapGroup, location->mapNum,
                               gSaveBlock1Ptr->pos.x, gSaveBlock1Ptr->pos.y, &move))
        JourneyAtlasApplySaveMove(&move);
    else if ((((u16)(u8)location->mapGroup << 8) | (u8)location->mapNum) == SWIMMER_MAP)
    {
        for (i = 0; i < OBJECT_EVENTS_COUNT; i++)
        {
            struct ObjectEvent *object = &gSaveBlock1Ptr->objectEvents[i];
            if (!object->isPlayer && object->localId != OBJ_EVENT_ID_FOLLOWER
             && object->localId != OBJ_EVENT_ID_NPC_FOLLOWER)
                object->active = FALSE;
        }
        CpuFill16(0, gSaveBlock1Ptr->objectEventTemplates, sizeof(gSaveBlock1Ptr->objectEventTemplates));
        sJourneyAtlasReloadSavedObjects = TRUE;
    }
    CpuFill16(0, gSaveBlock1Ptr->mapView, sizeof(gSaveBlock1Ptr->mapView));
    VarSet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION, 9);
}
'''


def prepare(source_path, inventory_source, output=None):
    source = Source(source_path)
    metadata_raw = source.read('.journey-atlas-surf-layout')
    if hashlib.sha256(metadata_raw).hexdigest() != PARENT_MARKER_SHA:
        raise ValueError('Expected the published Atlas 172 source')
    metadata = json.loads(metadata_raw)
    layer = Layer(source.source, LAYER, PRIOR)
    layer.expected['.journey-coastal-world-map'] = PROJECTION_MARKER_SHA
    existing = layer.existing()
    if existing:
        return existing
    if decode_atlas(read(layer, ART).decode()).array_sha256 != metadata['art_sha256']:
        raise ValueError('The source atlas does not match the published chart')
    removed = H | J | K
    cut, adjacent, island_dry = stage_terrain(layer, source, metadata, removed)
    art, hashes = edit_atlas(read(layer, ART).decode(), removed)
    layer.stage(ART, art)
    layer.stage(HEADER, render(metadata['geometry_plan'], source.identities)[0])
    metadata['art_sha256'] = hashes
    metadata['migration']['final_version'] = 9
    metadata['route_pruning']['save_moves'] = stage_save_migration(
        layer, source, OverlaySource(layer), cut, adjacent, island_dry)
    print('Verifying directed water access and route alternatives', flush=True)
    view, physical, graph, _ = source_audit(layer, metadata, inventory_source=inventory_source)
    for name, x, y, dest, tx, ty in metadata['route_pruning']['save_moves']:
        mode = 0 if dest == K_ISLAND_DRY_RESCUE[0] and (tx, ty) == K_ISLAND_DRY_RESCUE[1:] else 1
        if graph.component([dest, tx, ty], mode) != graph.ocean_component:
            raise ValueError(('Saved Surf position lacks a reachable rescue', name, x, y, dest, tx, ty))
    metadata['route_pruning']['physical_audit'] = physical
    print('Checking the remaining habitats and AREA markers', flush=True)
    stage_dex(layer, view, graph, metadata, output)
    if output is not None:
        (output / 'physical-source.json.gz').write_bytes(
            gzip.compress(json.dumps(physical, sort_keys=True).encode(), mtime=0))
    source.assert_unchanged()
    return layer.finish(geometry_plan=metadata['geometry_plan'], art_sha256=hashes,
                        migration=metadata['migration'], route_pruning=metadata['route_pruning'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('private_source', type=Path)
    parser.add_argument('--inventory-source', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = prepare(args.private_source, args.inventory_source, args.output)
    print(json.dumps(result['route_pruning']['changed_words_by_map'], sort_keys=True))
