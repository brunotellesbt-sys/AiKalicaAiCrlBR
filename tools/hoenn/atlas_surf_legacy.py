"""Preserve retired GPS solely for save migration, freeing active navigation.

The emitted GPS is an exact, row-indexed RLE copy of the old table, including
its edge clamp. It must never drive new travel. The independent one-bit water
mask uses collision-zero cells and the compiled native Surf flag. A clear bit
does not establish walkable land, elevation, or a safe migration destination.

Only two headers are staged. Map IDs, layouts, events and world artwork are
untouched; this is source preparation, not a ROM or save-migration certificate.
"""
import hashlib
import json
import re
import struct

from atlas_surf_overlay import OverlaySource
from atlas_surf_source import Source


NAVIGATION_PATH = 'src/data/journey_world_position.h'
HEADER_PATH = 'src/data/journey_atlas_legacy.h'
_NUMBER = r'(?:0[xX][0-9a-fA-F]+|[0-9]+)'
_GRID = re.compile(
    r'\{\s*(?P<first>[0-9]+)\s*,\s*'
    r'\(\s*MAP_GROUP\(\s*(?P<id>MAP_\w+)\s*\)\s*<<\s*8\s*\)\s*'
    r'\|\s*MAP_NUM\(\s*(?P=id)\s*\)\s*,\s*'
    r'(?P<width>[0-9]+)\s*,\s*(?P<height>[0-9]+)\s*\}\s*,')


class _LegacySource(OverlaySource):
    def __init__(self, layer):
        # Revision171 includes unused map files outside map_groups.json.
        # Their presence is harmless; only registry-backed IDs can migrate.
        # Keep the overlay's verified reads and native-enum compiler guard.
        self.layer = layer
        Source.__init__(self, layer.source)
        for path in sorted(layer.outputs):
            match = re.fullmatch(r'data/maps/([^/]+)/map.json', path)
            if match:
                name = match[1]
                if name not in self.identities:
                    raise ValueError(('Staged map missing from compiled registry', name))
                self.maps[name] = self.js(path)
        self.by_id = {}
        for name, row in self.maps.items():
            if row['id'] in self.by_id:
                raise ValueError(('Duplicate staged map constant', row['id']))
            self.by_id[row['id']] = name


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _words(values):
    return struct.pack('<' + 'H' * len(values), *values)


def _array(header, declaration):
    match = re.search(declaration + r'\s*=\s*\{(?P<body>.*?)\};', header, re.S)
    if match is None:
        raise ValueError('Missing or unsupported navigation array: ' + declaration)
    return match


def _navigation(header, source):
    pixels = _array(header, r'static\s+const\s+u16\s+sWorldNavigationPixels\s*\[\s*\]')
    tokens = re.findall(_NUMBER, pixels['body'])
    if not re.fullmatch(r'\s*' + _NUMBER + r'(?:\s*,\s*' + _NUMBER + r')*\s*,?\s*', pixels['body']):
        raise ValueError('Unsupported navigation pixel initializer')
    values = [int(token, 16 if token.lower().startswith('0x') else 10) for token in tokens]
    if any(value > 65535 for value in values):
        raise ValueError('Navigation pixel exceeds u16')
    grids = _array(header, r'static\s+const\s+struct\s+JourneyWorldTileGrid\s+sWorldTileGrids\s*\[\s*\]')
    rows, seen, end = [], set(), 0
    for match in _GRID.finditer(grids['body']):
        if grids['body'][end:match.start()].strip():
            raise ValueError('Unsupported navigation grid initializer')
        end = match.end()
        constant = match['id']
        name = source.by_id.get(constant)
        if name is None or name not in source.identities:
            raise ValueError(('Unknown navigation map constant', constant))
        packed = source.identities[name]
        first, width, height = (int(match[key]) for key in ('first', 'width', 'height'))
        if packed in seen or not (0 < width <= 32767 and 0 < height <= 32767):
            raise ValueError(('Duplicate map or invalid navigation dimensions', name))
        seen.add(packed)
        if first + width * height > len(values):
            raise ValueError(('Navigation grid exceeds pixel table', name))
        rows.append(dict(map=name, id=constant, packed_id=packed, first=first,
                         width=width, height=height, match=match))
    if not rows or grids['body'][end:].strip():
        raise ValueError('Unsupported or empty navigation grid initializer')
    previous_end = 0
    for row in sorted(rows, key=lambda row: row['first']):
        if row['first'] < previous_end:
            raise ValueError(('Overlapping navigation grids', row['map']))
        previous_end = row['first'] + row['width'] * row['height']
    return pixels, grids, tokens, values, rows


def _retired(source, records, grids):
    by_name = {row['map']: row for row in grids}
    result, seen = [], set()
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get('map'), str):
            raise ValueError('Retired maps must be inventory records with a map name')
        name = record['map']
        if name in seen or name not in by_name:
            raise ValueError(('Duplicate or missing retired navigation map', name))
        seen.add(name)
        row = by_name[name]
        layout = source.layout(name)
        expected = dict(id=row['id'], packed_id=row['packed_id'],
                        dimensions=[row['width'], row['height']],
                        layout=source.maps[name]['layout'],
                        banks=[layout['primary_tileset'], layout['secondary_tileset']],
                        blockdata=layout['blockdata_filepath'])
        if [layout['width'], layout['height']] != expected['dimensions']:
            raise ValueError(('Legacy navigation differs from native layout dimensions', name))
        for key, value in expected.items():
            if key in record and record[key] != value:
                raise ValueError(('Retired inventory differs from native source', name, key))
        for key, path in [('map_sha256', f'data/maps/{name}/map.json'),
                          ('blockdata_sha256', layout['blockdata_filepath'])]:
            if key in record and record[key] != _sha(source.read(path)):
                raise ValueError(('Retired inventory input hash differs', name, key))
        result.append(row)
    if not result:
        raise ValueError('At least one retired map is required')
    return sorted(result, key=lambda row: row['packed_id'])


def _tables(source, retired, pixels):
    row_first, run_ends, run_pixels, map_rows, known_rows = [], [], [], [], {}
    water, water_bits, wet_cells = bytearray(), 0, 0
    for grid in retired:
        name, width, height = grid['map'], grid['width'], grid['height']
        first_row, first_water = len(row_first), water_bits
        for y in range(height):
            first = grid['first'] + y * width
            row = tuple(pixels[first:first + width])
            if row not in known_rows:
                known_rows[row] = len(run_pixels)
                for x, pixel in enumerate(row):
                    if x + 1 == width or row[x + 1] != pixel:
                        run_ends.append(x + 1)
                        run_pixels.append(pixel)
            row_first.append(known_rows[row])
            for x in range(width):
                if water_bits % 8 == 0:
                    water.append(0)
                if source.water(name, x, y):
                    water[-1] |= 1 << (water_bits % 8)
                    wet_cells += 1
                water_bits += 1
        map_rows.append((first_water, grid['packed_id'], first_row, width, height))
    if len(row_first) > 65535 or water_bits > 0xFFFFFFFF:
        raise ValueError('Legacy map/row index exceeds its native integer budget')
    end_bytes = 1 if max(run_ends) <= 255 else 2
    index_bytes = 2 if max(row_first) <= 65535 else 4
    table_bytes = 12 * len(map_rows) + index_bytes * len(row_first)
    table_bytes += (2 + end_bytes) * len(run_pixels) + len(water)
    return dict(maps=map_rows, row_first=row_first, run_ends=run_ends,
                run_pixels=run_pixels, water=water, water_bits=water_bits,
                wet_cells=wet_cells, unique_rows=len(known_rows),
                end_bytes=end_bytes, index_bytes=index_bytes, table_bytes=table_bytes)


def _render(tables):
    code = '''// Generated by atlas_surf_legacy.py. Migration only; never new travel.
#ifndef GUARD_JOURNEY_ATLAS_LEGACY_H
#define GUARD_JOURNEY_ATLAS_LEGACY_H
// A clear water bit does not certify walkable land or a safe destination.
struct JourneyAtlasLegacyMap { u32 waterFirst; u16 map, firstRow, width, height; };
typedef char JourneyAtlasLegacyMapMustHaveTwelveBytes[(sizeof(struct JourneyAtlasLegacyMap) == 12) ? 1 : -1];
static const struct JourneyAtlasLegacyMap sAtlasLegacyMaps[] = {
'''
    code += ''.join('    {%d,%d,%d,%d,%d},\n' % row for row in tables['maps']) + '};\n'
    for ctype, name, values in [
        ('u16' if tables['index_bytes'] == 2 else 'u32', 'sAtlasLegacyRows', tables['row_first']),
        ('u8' if tables['end_bytes'] == 1 else 'u16', 'sAtlasLegacyRunEnds', tables['run_ends']),
        ('u16', 'sAtlasLegacyRunPixels', tables['run_pixels']),
        ('u8', 'sAtlasLegacyWater', tables['water'])]:
        code += 'static const ' + ctype + ' ' + name + '[] = {\n'
        code += ''.join('    ' + ','.join(map(str, values[first:first + 24])) + ',\n'
                        for first in range(0, len(values), 24)) + '};\n'
    return code + r'''
static const struct JourneyAtlasLegacyMap *JourneyAtlasLegacyFind(u16 packedMap)
{
    u32 lo = 0, hi = ARRAY_COUNT(sAtlasLegacyMaps), mid;
    while (lo < hi)
    {
        mid = lo + (hi - lo) / 2;
        if (sAtlasLegacyMaps[mid].map < packedMap) lo = mid + 1;
        else hi = mid;
    }
    if (lo == ARRAY_COUNT(sAtlasLegacyMaps) || sAtlasLegacyMaps[lo].map != packedMap)
        return NULL;
    return &sAtlasLegacyMaps[lo];
}

// Same local-coordinate edge clamp as revision171. Migration callers only.
static bool8 JourneyAtlasLegacyWorldPosition(u16 packedMap, s16 x, s16 y, u16 *pixel)
{
    const struct JourneyAtlasLegacyMap *map = JourneyAtlasLegacyFind(packedMap);
    u32 run;
    if (map == NULL || pixel == NULL) return FALSE;
    if (x < 0) x = 0;
    if (y < 0) y = 0;
    if (x >= map->width) x = map->width - 1;
    if (y >= map->height) y = map->height - 1;
    run = sAtlasLegacyRows[map->firstRow + y];
    while (x >= sAtlasLegacyRunEnds[run]) run++;
    *pixel = sAtlasLegacyRunPixels[run];
    return TRUE;
}

// TRUE means this old cell is known, with its Surf-water result in *out.
// Outside coordinates are unknown; they are not clamped into a water cell.
static bool8 JourneyAtlasLegacyWater(u16 packedMap, s16 x, s16 y, bool8 *out)
{
    const struct JourneyAtlasLegacyMap *map = JourneyAtlasLegacyFind(packedMap);
    u32 bit;
    if (map == NULL || out == NULL || x < 0 || y < 0
        || x >= map->width || y >= map->height) return FALSE;
    bit = map->waterFirst + (u32)y * map->width + x;
    *out = (sAtlasLegacyWater[bit / 8] >> (bit % 8)) & 1;
    return TRUE;
}
#endif
'''


def _prune(header, pixels_match, grids_match, tokens, values, grids, retired):
    identities = {row['packed_id'] for row in retired}
    removed = sorted((row['first'], row['first'] + row['width'] * row['height']) for row in retired)
    keep_tokens, keep_values, cursor = [], [], 0
    for first, end in removed:
        keep_tokens.extend(tokens[cursor:first]); keep_values.extend(values[cursor:first])
        cursor = end
    keep_tokens.extend(tokens[cursor:]); keep_values.extend(values[cursor:])
    edits, retained_hashes = [], {}
    for grid in grids:
        match = grid['match']
        if grid['packed_id'] in identities:
            edits.append((*match.span(), ''))
            continue
        first = grid['first'] - sum(end - start for start, end in removed if end <= grid['first'])
        count = grid['width'] * grid['height']
        original = _words(values[grid['first']:grid['first'] + count])
        if original != _words(keep_values[first:first + count]):
            raise ValueError(('Retained navigation pixels changed', grid['map']))
        retained_hashes[grid['map']] = _sha(original)
        edits.append((*match.span('first'), str(first)))
    grid_body = grids_match['body']
    for first, end, replacement in sorted(edits, reverse=True):
        grid_body = grid_body[:first] + replacement + grid_body[end:]
    replacements = [(*pixels_match.span('body'), ','.join(keep_tokens)),
                    (*grids_match.span('body'), grid_body)]
    for first, end, replacement in sorted(replacements, reverse=True):
        header = header[:first] + replacement + header[end:]
    return header, keep_values, retained_hashes


def stage_navigation_prune(layer, retired_maps):
    """Stage exact migration data and remove only the retired active grids.

    ``retired_maps`` is the parent inventory's list of records. Supplied input
    hashes and identities are checked against the staged native Source view.
    Call before any tombstone or other alteration of the retired terrain.
    ``layer.finish`` remains the integration caller's responsibility.
    """
    if HEADER_PATH in layer.outputs or (layer.source / HEADER_PATH).exists():
        raise ValueError('Legacy migration navigation already installed')
    source = _LegacySource(layer)
    original = source.read(NAVIGATION_PATH)
    header = original.decode()
    pixel_match, grid_match, tokens, pixels, grids = _navigation(header, source)
    retired = _retired(source, retired_maps, grids)
    tables = _tables(source, retired, pixels)
    legacy = _render(tables)
    pruned, kept, retained_hashes = _prune(header, pixel_match, grid_match, tokens, pixels, grids, retired)
    source.assert_unchanged()
    retired_cells = sum(row['width'] * row['height'] for row in retired)
    before_bytes = 2 * len(pixels) + 12 * len(grids)
    active_bytes = 2 * len(kept) + 12 * (len(grids) - len(retired))
    metadata = dict(
        kind='atlas-legacy-migration-navigation', migration_only=True,
        retired_maps=[dict(map=row['map'], id=row['id'], packed_id=row['packed_id'],
                          dimensions=[row['width'], row['height']]) for row in retired],
        active_grids_before=len(grids), active_grids_after=len(grids) - len(retired),
        navigation_cells_before=len(pixels), navigation_cells_after=len(kept),
        retired_cells=retired_cells, retired_water_cells=tables['wet_cells'],
        gps_rows=len(tables['row_first']), gps_unique_rows=tables['unique_rows'],
        gps_runs=len(tables['run_pixels']), gps_run_end_bytes=tables['end_bytes'],
        gps_row_index_bytes=tables['index_bytes'], water_mask_bytes=len(tables['water']),
        navigation_data_bytes_before=before_bytes, navigation_data_bytes_after=active_bytes,
        legacy_data_bytes=tables['table_bytes'],
        combined_data_bytes_after=active_bytes + tables['table_bytes'],
        data_bytes_freed=before_bytes - active_bytes - tables['table_bytes'],
        byte_budget_excludes_function_code_and_linker_padding=True,
        navigation_header_sha256_before=_sha(original),
        navigation_header_sha256_after=_sha(pruned.encode()), legacy_header_sha256=_sha(legacy.encode()),
        retired_gps_sha256=_sha(_words([value for row in retired for value in
            pixels[row['first']:row['first'] + row['width'] * row['height']]])),
        retired_water_mask_sha256=_sha(tables['water']),
        retained_grid_pixels_sha256=retained_hashes,
        input_sha256=dict(source.inputs),
        input_manifest_sha256=_sha(json.dumps(source.inputs, sort_keys=True, separators=(',', ':')).encode()),
        native_rom_validation_pending=True)
    layer.stage(NAVIGATION_PATH, pruned)
    layer.stage(HEADER_PATH, legacy)
    return metadata
