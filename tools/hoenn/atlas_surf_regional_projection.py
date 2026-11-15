"""Read-only reproduction of revision171's native regional-map projection.

This is the engine's quantized cursor, followed by the authenticated regional
PNG/panel transform. It is NOT an embedding of native terrain at eight local
tiles per atlas pixel. ``atlas`` is the continuous position of the *UI cursor*;
``atlas_pixels`` is the exact NEAREST-resized footprint of its regional cell.
Neither claims that every pixel in that cell is physically native water.

No sWorldPoint, generated/interpolated GPS, nearest label or invented local
center participates. Stateful indoor/cave/ship projections require their real
save-state context; missing context fails explicitly. The optional host-C
oracle compiles the unchanged native function bodies and real map tables in a
temporary directory, without an ARM build or any writes to the input source.
"""
from collections import defaultdict
from fractions import Fraction
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from atlas_surf_truth import decode_atlas


ROOT = Path(__file__).resolve().parents[2]
FUNCTION_HASHES = {
    'InitMapBasedOnPlayerLocation': 'dd9f60b595ae002abb558a686f73d5bd102ec4970faa380e02ab278c1c4d379e',
    'RegionMap_InitializeStateBasedOnSSTidalLocation': '7a44f72f2bbfcf93480633d2a3d95499d551835936d3948578542ee1a7731068',
    'GetMarineCaveCoords': '3af470ba6616b21049541b25fdf2e9111ae52086f142da3fb1614038904ffb07',
    'IsPlayerInAquaHideout': 'd9e85d4cb6ae9b4e315667a8ff8421f69de87e5393816dcecaa8b352af8c9009',
}
OUTDOOR = frozenset(('MAP_TYPE_TOWN', 'MAP_TYPE_CITY', 'MAP_TYPE_ROUTE',
                     'MAP_TYPE_UNDERWATER', 'MAP_TYPE_OCEAN_ROUTE'))
TIDAL_NAMES = ('SSTidalCorridor', 'SSTidalLowerDeck', 'SSTidalRooms')
TIDAL_LOCATIONS = ('SS_TIDAL_LOCATION_CURRENTS', 'SS_TIDAL_LOCATION_SLATEPORT',
                   'SS_TIDAL_LOCATION_LILYCOVE', 'SS_TIDAL_LOCATION_ROUTE124',
                   'SS_TIDAL_LOCATION_ROUTE131')


class ProjectionContextRequired(ValueError):
    """A native calculation depends on save state not present in (map,x,y)."""


def _function(text, name):
    match = re.search(r'(?:static\s+)?(?:void|bool32|enum\s+Region)\s+'
                      + re.escape(name) + r'\([^;]*?\)\s*\{', text)
    if match is None:
        raise ValueError(('Missing native projection function', name))
    depth, end = 1, match.end()
    while depth and end < len(text):
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    if depth:
        raise ValueError(('Truncated native projection function', name))
    return text[match.start():end]


def _s16(value):
    if not isinstance(value, int) or isinstance(value, bool) or not -32768 <= value <= 32767:
        raise ValueError(('Position does not fit native s16', value))
    return value


def _uint16(value):
    return value & 65535


def _signed_div(numerator, denominator):
    return (1 if numerator >= 0 else -1) * (abs(numerator) // denominator)


def _defines(text):
    definitions = dict(re.findall(r'^#define\s+(\w+)\s+([^\n/]+)', text, re.M))
    result = {}

    def value(name):
        if name not in result:
            expression = definitions[name].strip()
            expression = re.sub(r'\b[A-Z]\w*\b', lambda m: str(value(m[0])), expression)
            tree = ast.parse(expression, mode='eval')
            if any(not isinstance(node, (ast.Expression, ast.BinOp, ast.Add, ast.Sub,
                                         ast.Constant)) for node in ast.walk(tree)):
                raise ValueError(('Unsupported native arithmetic definition', name))
            result[name] = eval(compile(tree, '<native integer constants>', 'eval'),
                                {'__builtins__': {}}, {})
        return result[name]

    for name in ('MARINE_CAVE_LOCATIONS_START', 'ABNORMAL_WEATHER_LOCATIONS'):
        value(name)
    for name in definitions:
        if name.startswith('ABNORMAL_WEATHER_ROUTE_'):
            value(name)
    return result


class NativeProjection:
    def __init__(self, inputs, assets_root=ROOT):
        from PIL import Image
        self.inputs = inputs
        self.assets_root = Path(assets_root)
        self.native_text = inputs.read('src/region_map.c').decode()
        self.functions = {name: _function(self.native_text, name) for name in FUNCTION_HASHES}
        for name, body in self.functions.items():
            if hashlib.sha256(body.encode()).hexdigest() != FUNCTION_HASHES[name]:
                raise ValueError(('Native engine changed; revalidate Python port against C', name))
        rows = inputs.js('src/data/region_map/region_map_sections.json')['map_sections']
        self.sections = {row['id']: dict(x=0, y=0, width=1, height=1, **{
            k: v for k, v in row.items() if k not in ('x', 'y', 'width', 'height')})
            for row in rows}
        for row in rows:
            self.sections[row['id']].update(row)
        self.section_ids = {row['id']: number for number, row in enumerate(rows)}
        if len(self.sections) != len(rows) or len(rows) > 254:
            raise ValueError('Invalid native section enum')
        # These are the defaults in the actual jsonproc templates, not guessed
        # dimensions for sections which omit their rectangle.
        template = inputs.read('src/data/region_map/region_map_sections.json.txt').decode()
        constant_template = inputs.read('src/data/region_map/region_map_sections.constants.json.txt').decode()
        if '.width = 1,' not in template or '.height = 1,' not in template or 'KANTO_MAPSEC_START  MAPSEC_PALLET_TOWN' not in constant_template:
            raise ValueError('Native region-map table template changed')
        region_header = inputs.read('include/regions.h').decode()
        self.region_function = _function(region_header, 'GetRegionForSectionId')
        expected_condition = ('sectionId == MAPSEC_LAVENDER_PORT || sectionId == MAPSEC_EMERALD_CAY || '
            'sectionId == MAPSEC_SUNLIT_ISLE || sectionId == MAPSEC_TIDEWOOD_ISLE || '
            '(sectionId >= KANTO_MAPSEC_START && sectionId < MAPSEC_SPECIAL_AREA)')
        if expected_condition not in self.region_function:
            raise ValueError('Native section-to-region rule changed')
        self.regions_text = inputs.read('src/regions.c').decode()
        self.subregions = {}
        for suffix, panel in (('SEVII123', 'sevii_123'), ('SEVII45', 'sevii_45'),
                              ('SEVII67', 'sevii_67')):
            match = re.search(r'\[KANTO_SUBREGION_' + suffix + r'\]\s*=\s*\{([^}]+)\}',
                              self.regions_text)
            if match is None:
                raise ValueError(('Native subregion list missing', suffix))
            for section in re.findall(r'MAPSEC_\w+', match[1]):
                if section != 'MAPSEC_NONE':
                    if section in self.subregions:
                        raise ValueError(('Conflicting native subregion', section))
                    self.subregions[section] = panel
        weather = inputs.read('include/constants/weather.h').decode()
        self.weather = _defines(weather)
        self.marine_array = re.search(r'static const struct UCoords16 sMarineCaveLocationCoords\[.*?\};',
                                      self.native_text, re.S)[0]
        self.marine_coords = {self.weather['ABNORMAL_WEATHER_' + name]: (int(x), int(y))
            for name, x, y in re.findall(r'MARINE_CAVE_COORD\((\w+)\)\]\s*=\s*\{(\d+),\s*(\d+)\}',
                                        self.marine_array)}
        self.hideout_array = re.search(r'static const mapsec_u8_t sMapSecAquaHideoutOld\[\].*?\};',
                                       self.native_text, re.S)[0]
        self.hideout_sections = set(re.findall(r'MAPSEC_\w+', self.hideout_array))
        inputs.read('include/constants/field_specials.h')
        self.marker = inputs.js('.journey-coastal-world-map')
        self.panels, self.assets = {}, {}
        for name, rectangle in self.marker['panels'].items():
            relative = f'web/atlas/{name}.png'
            raw = (self.assets_root / relative).read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if self.marker['asset_sha256'].get(relative) != digest:
                raise ValueError(('Regional asset differs from authenticated panel marker', relative))
            with Image.open(self.assets_root / relative) as picture:
                dimensions = picture.size
            if len(rectangle) != 4 or any(type(v) is not int for v in rectangle) or min(rectangle[2:]) <= 0:
                raise ValueError(('Invalid authenticated panel rectangle', name))
            self.panels[name] = dict(rectangle=rectangle, source_size=dimensions)
            self.assets[relative] = digest
        self.truth = decode_atlas(inputs.read('src/data/journey_world_map.h').decode())
        self._cell_cache = {}

    def panel_for_section(self, section):
        number = self.section_ids[section]
        special = section in ('MAPSEC_LAVENDER_PORT', 'MAPSEC_EMERALD_CAY',
                              'MAPSEC_SUNLIT_ISLE', 'MAPSEC_TIDEWOOD_ISLE')
        is_kanto = special or self.section_ids['MAPSEC_PALLET_TOWN'] <= number < self.section_ids['MAPSEC_SPECIAL_AREA']
        return self.subregions.get(section, 'kanto') if is_kanto else 'hoenn'

    def _map_name(self, name):
        if isinstance(name, int):
            matches = [n for n, ident in self.inputs.identities.items() if ident == name]
            if len(matches) != 1:
                raise ValueError(('Unknown native map identity', name))
            return matches[0]
        name = self.inputs.by_id.get(name, name)
        if name not in self.inputs.maps:
            raise ValueError(('Unknown native map', name))
        if name not in self.inputs.identities:
            raise ValueError(('Native map has no compiled identity', name))
        return name

    def _warp(self, context, key):
        if not context or key not in context:
            raise ProjectionContextRequired(f'Native projection requires real {key} map/x/y')
        value = context[key]
        name = self._map_name(value['map'])
        return name, _s16(value['x']), _s16(value['y'])

    def _quantize(self, section, name, x, y, signed=False):
        entry, layout = self.sections[section], self.inputs.layout(name)
        dimensions = layout['width'], layout['height']
        if not all(0 < d <= 65535 for d in dimensions + (entry['width'], entry['height'])):
            raise ValueError(('Invalid native section or layout dimension', name, section))
        scale = tuple(max(1, d // entry[k]) for d, k in zip(dimensions, ('width', 'height')))
        if signed:
            local = [_uint16(_signed_div(p, s)) for p, s in zip((x, y), scale)]
        else:
            local = [_uint16(p) // s for p, s in zip((x, y), scale)]
        return [min(local[i], entry[k] - 1) for i, k in enumerate(('width', 'height'))], scale

    def native_cursor(self, name, x, y, context=None):
        name = self._map_name(name)
        x, y = _s16(x), _s16(y)
        context = context or {}
        if context.get('forced_flight_region') is not None:
            raise ProjectionContextRequired('Forced flight selection is not player geography')
        row = self.inputs.maps[name]
        section, origin, cave = row['region_map_section'], 'player-position', False
        source_name, sx, sy = name, x, y
        if name in TIDAL_NAMES:
            if 'sstidal' not in context:
                raise ProjectionContextRequired('Native SS Tidal projection requires GetSSTidalLocation state')
            tidal = context['sstidal']
            kind = tidal['location']
            if kind not in TIDAL_LOCATIONS:
                raise ValueError(('Unknown native SS Tidal location', kind))
            if kind != TIDAL_LOCATIONS[0]:
                section = dict(zip(TIDAL_LOCATIONS[1:], ('MAPSEC_SLATEPORT_CITY', 'MAPSEC_LILYCOVE_CITY',
                                'MAPSEC_ROUTE_124', 'MAPSEC_ROUTE_131')))[kind]
                local, scale = [0, 0], None
            else:
                source_name = self._map_name(tidal['map'])
                sx, sy = _s16(tidal['x']), _s16(tidal['y'])
                section = self.inputs.maps[source_name]['region_map_section']
                local, scale = self._quantize(section, source_name, sx, sy, signed=True)
            origin = 'GetSSTidalLocation:' + kind
        else:
            kind = row['map_type']
            if kind in ('MAP_TYPE_UNDERGROUND', 'MAP_TYPE_UNKNOWN'):
                cave = True
                if row['allow_escaping']:
                    source_name, sx, sy = self._warp(context, 'escape_warp')
                    section = self.inputs.maps[source_name]['region_map_section']
                    origin = 'escapeWarp'
                else:
                    source_name, sx, sy, origin = name, 1, 1, 'non-escaping-cave-fixed-1x1'
            elif kind == 'MAP_TYPE_SECRET_BASE':
                source_name, sx, sy = self._warp(context, 'dynamic_warp')
                section, cave, origin = self.inputs.maps[source_name]['region_map_section'], True, 'dynamicWarp'
            elif kind == 'MAP_TYPE_INDOOR':
                key = 'dynamic_warp' if section == 'MAPSEC_DYNAMIC' else 'escape_warp'
                source_name, sx, sy = self._warp(context, key)
                if section == 'MAPSEC_DYNAMIC':
                    section = self.inputs.maps[source_name]['region_map_section']
                cave, origin = section in self.hideout_sections, key.replace('_w', 'W')
            if origin == 'non-escaping-cave-fixed-1x1':
                entry = self.sections[section]
                scale = (max(1, 1 // entry['width']), max(1, 1 // entry['height']))
                local = [min(1 // scale[0], entry['width'] - 1), min(1 // scale[1], entry['height'] - 1)]
            else:
                local, scale = self._quantize(section, source_name, sx, sy)
            if kind not in ('MAP_TYPE_UNDERGROUND', 'MAP_TYPE_UNKNOWN', 'MAP_TYPE_SECRET_BASE', 'MAP_TYPE_INDOOR'):
                cave = section in ('MAPSEC_UNDERWATER_SEAFLOOR_CAVERN', 'MAPSEC_UNDERWATER_MARINE_CAVE')
            if section == 'MAPSEC_ROUTE_114' and local[1] != 0:
                local[0] = 0
            elif section in ('MAPSEC_ROUTE_126', 'MAPSEC_UNDERWATER_126'):
                # C uses *current player position*, not a selected warp, here.
                local = [int(x > 32) + int(x > 51), int(y > 37) + int(y > 56)]
            elif section == 'MAPSEC_ROUTE_121':
                local[0] = sum(_uint16(sx) > cutoff for cutoff in (14, 28, 54))
            elif section == 'MAPSEC_UNDERWATER_MARINE_CAVE':
                if 'marine_weather_location' not in context:
                    raise ProjectionContextRequired('Native Marine Cave requires VAR_ABNORMAL_WEATHER_LOCATION')
                index = _uint16(context['marine_weather_location'])
                if not self.weather['MARINE_CAVE_LOCATIONS_START'] <= index <= self.weather['ABNORMAL_WEATHER_LOCATIONS']:
                    index = self.weather['MARINE_CAVE_LOCATIONS_START']
                cx, cy = self.marine_coords[index]
                return dict(map=name, section=section, cursor=[cx + 1, cy + 2], player_in_cave=cave,
                            origin='GetMarineCaveCoords', projection_map=source_name,
                            projection_local=[sx, sy], dimension_scale=list(scale))
        entry = self.sections[section]
        return dict(map=name, section=section, cursor=[entry['x'] + local[0] + 1, entry['y'] + local[1] + 2],
                    player_in_cave=cave, origin=origin, projection_map=source_name,
                    projection_local=[sx, sy], dimension_scale=list(scale) if scale else None)

    def _atlas_cell(self, panel, cursor):
        key = panel, tuple(cursor)
        if key not in self._cell_cache:
            left, top, width, height = self.panels[panel]['rectangle']
            sw, sh = self.panels[panel]['source_size']
            cx, cy = cursor[0] - 1, cursor[1] - 2
            source_rect = [cx * 8, cy * 8, cx * 8 + 8, cy * 8 + 8]
            # Pillow's NEAREST resize samples centers; exact integer arithmetic
            # avoids rounding at borders and never clamps atlas y to 107.
            xs = [left + i for i in range(width) if cx * 8 <= (2 * i + 1) * sw // (2 * width) < cx * 8 + 8]
            ys = [top + i for i in range(height) if cy * 8 <= (2 * i + 1) * sh // (2 * height) < cy * 8 + 8]
            pixels = [[x, y] for y in ys for x in xs if 0 <= x < 224 and 0 <= y < 112]
            ax, ay = Fraction(left) + Fraction((cx * 8 + 4) * width, sw), Fraction(top) + Fraction((cy * 8 + 4) * height, sh)
            self._cell_cache[key] = dict(panel=panel, regional_cell=[cx, cy], regional_source_rect=source_rect,
                atlas=[float(ax), float(ay)], atlas_rational=[[ax.numerator, ax.denominator], [ay.numerator, ay.denominator]],
                atlas_pixels=pixels, atlas_blue_pixels=[p for p in pixels if self.truth.pixel(tuple(p)) == 2],
                pixel_ownership_proven=False, local_tiles_per_atlas_pixel=None)
        return self._cell_cache[key]

    def project(self, name, x, y, context=None):
        native = self.native_cursor(name, x, y, context)
        # Native GetActiveRegionMapType uses gMapHeader's section, including
        # indoor cases whose projected section came from an outside warp.
        panel = self.panel_for_section(self.inputs.maps[native['map']]['region_map_section'])
        cell = self._atlas_cell(panel, native['cursor'])
        return dict(native, **cell, provenance='native-InitMapBasedOnPlayerLocation+authenticated-panel',
                    old_gps_used=False, worldpoint_used=False, native_rom_validated=False)

    def assert_unchanged(self):
        self.inputs.assert_unchanged()
        for relative, digest in self.assets.items():
            if hashlib.sha256((self.assets_root / relative).read_bytes()).hexdigest() != digest:
                raise ValueError(('Regional asset changed during projection', relative))


def project_native(inputs, name, x, y, context=None, assets_root=ROOT):
    """Return the native UI projection with exact regional-cell provenance."""
    reader = getattr(inputs, '_atlas_regional_projection', None)
    if reader is None or reader.assets_root != Path(assets_root):
        reader = NativeProjection(inputs, assets_root)
        inputs._atlas_regional_projection = reader
    return reader.project(name, x, y, context)


class NativeCOracle:
    """Unmodified engine function bodies, compiled for the host in isolation."""
    def __init__(self, projection):
        self.projection = projection

    def code(self):
        p, inputs = self.projection, self.projection.inputs
        maps = {name: row for name, row in inputs.maps.items() if name in inputs.identities}
        maptypes = sorted({row['map_type'] for row in maps.values()}
                          | set(re.findall(r'\bMAP_TYPE_\w+', '\n'.join(p.functions.values()))))
        definitions = '\n'.join('#define ' + name + ' ' + str(i) for i, name in enumerate(maptypes))
        definitions += '\nenum {' + ','.join(p.sections) + ',MAPSEC_NONE};\n'
        definitions += '\n'.join('#define ' + row['id'] + ' ' + str(inputs.identities[name])
                                  for name, row in maps.items())
        entries = ',\n'.join('[' + row['id'] + ']={' + ','.join(str(row[k]) for k in ('x', 'y', 'width', 'height')) + '}'
                              for row in p.sections.values())
        layouts = '\n'.join('static struct MapLayout layout_' + str(i) + '={' + str(inputs.layout(name)['width']) + ','
                             + str(inputs.layout(name)['height']) + '};' for i, name in enumerate(maps))
        headers = ',\n'.join('[' + str(inputs.identities[name]) + ']={&layout_' + str(i) + ',' + row['region_map_section'] + ','
                              + str(int(row.get('allow_escaping', False))) + ',' + row['map_type'] + '}'
                              for i, (name, row) in enumerate(maps.items()))
        # Everything below the shims is copied verbatim from region_map.c.
        return r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "constants/weather.h"
#include "constants/field_specials.h"
typedef uint8_t u8; typedef int8_t s8; typedef uint16_t u16; typedef int16_t s16;
typedef uint32_t u32; typedef uint8_t bool8; typedef uint32_t bool32;
typedef uint16_t mapsec_u16_t; typedef uint8_t mapsec_u8_t;
#define TRUE 1
#define FALSE 0
#define ARRAY_COUNT(a) (sizeof(a)/sizeof((a)[0]))
#define MAPCURSOR_X_MIN 1
#define MAPCURSOR_Y_MIN 2
#define MAP_GROUP(m) ((m)>>8)
#define MAP_NUM(m) ((m)&255)
''' + definitions + r'''
struct UCoords16 {u16 x,y;};
struct MapLayout {u16 width,height;};
struct MapHeader {struct MapLayout *mapLayout; mapsec_u8_t regionMapSectionId; bool8 allowEscaping; u8 type;};
struct WarpData {u8 mapGroup,mapNum; s16 x,y;};
struct SaveBlock {struct WarpData location,escapeWarp,dynamicWarp; struct {s16 x,y;} pos;};
struct RegionMap {mapsec_u16_t mapSecId; bool8 playerIsInCave; u16 cursorPosX,cursorPosY;};
struct Entry {u16 x,y,width,height;};
static struct Entry gRegionMapEntries[]={''' + entries + r'''};
''' + layouts + '\nstatic struct MapHeader headers[65536]={' + headers + r'''};
static struct MapHeader gMapHeader;
static struct SaveBlock save, *gSaveBlock1Ptr=&save;
static struct RegionMap region, *sRegionMap=&region;
static int sUseForcedFlightRegion=0;
static int tidalLocation, tidalMap, tidalX, tidalY, weather;
static void InitMapForForcedFlightRegion(void) { abort(); }
static const struct MapHeader *Overworld_GetMapHeaderByGroupAndId(u16 g,u16 n) {return &headers[(g<<8)|n];}
static u8 GetMapTypeByGroupAndId(u16 g,u16 n) {return headers[(g<<8)|n].type;}
static u8 GetSSTidalLocation(s8 *g,s8 *n,s16 *x,s16 *y) {*g=tidalMap>>8;*n=tidalMap&255;*x=tidalX;*y=tidalY;return tidalLocation;}
#define VAR_ABNORMAL_WEATHER_LOCATION 0
static u16 VarGet(int unused) {(void)unused;return weather;}
static void RegionMap_InitializeStateBasedOnSSTidalLocation(void);
static void GetMarineCaveCoords(u16 *,u16 *);
static bool32 IsPlayerInAquaHideout(mapsec_u8_t);
#define MARINE_CAVE_COORD(location) (ABNORMAL_WEATHER_##location - MARINE_CAVE_LOCATIONS_START)
''' + p.marine_array + '\n' + p.hideout_array + '\n' + '\n'.join(p.functions.values()) + r'''
int main(void) {
    int map,x,y,escape,ex,ey,dynamic,dx,dy;
    while(scanf("%d%d%d%d%d%d%d%d%d%d%d%d%d%d", &map,&x,&y,&escape,&ex,&ey,&dynamic,&dx,&dy,
                &tidalLocation,&tidalMap,&tidalX,&tidalY,&weather)==14) {
        gMapHeader=headers[map]; save.location=(struct WarpData){map>>8,map&255,0,0};
        save.pos.x=x;save.pos.y=y;
        save.escapeWarp=(struct WarpData){escape>>8,escape&255,ex,ey};
        save.dynamicWarp=(struct WarpData){dynamic>>8,dynamic&255,dx,dy};
        region=(struct RegionMap){0}; InitMapBasedOnPlayerLocation();
        printf("%u %u %u %u\n",region.mapSecId,region.cursorPosX,region.cursorPosY,region.playerIsInCave);
    }
    return 0;
}
'''

    def compare(self, cases):
        compiler = shutil.which('cc') or shutil.which('gcc')
        if compiler is None:
            raise RuntimeError('Host C compiler is required for native projection oracle')
        cases = list(cases)
        expected, lines = [], []
        p = self.projection
        for case in cases:
            name, x, y, *extra = case
            context = extra[0] if extra else {}
            result = p.native_cursor(name, x, y, context)
            name = result['map']
            expected.append([p.section_ids[result['section']], *result['cursor'], int(result['player_in_cave'])])
            values = [p.inputs.identities[name], x, y]
            for key in ('escape_warp', 'dynamic_warp'):
                warp = context.get(key, dict(map=name, x=0, y=0))
                values += [p.inputs.identities[p._map_name(warp['map'])], warp['x'], warp['y']]
            tidal = context.get('sstidal', dict(location=TIDAL_LOCATIONS[0], map=name, x=0, y=0))
            values += [TIDAL_LOCATIONS.index(tidal['location']), p.inputs.identities[p._map_name(tidal.get('map', name))],
                       tidal.get('x', 0), tidal.get('y', 0), context.get('marine_weather_location', 0)]
            lines.append(' '.join(map(str, values)))
        code = self.code()
        with tempfile.TemporaryDirectory(prefix='atlas-regional-native-oracle-') as temporary:
            executable = Path(temporary) / 'projection'
            subprocess.run([compiler, '-std=gnu17', '-Wall', '-Wextra', '-Werror', '-iquote', str(p.inputs.source / 'include'),
                            '-x', 'c', '-', '-o', str(executable)], input=code, text=True, capture_output=True, check=True)
            result = subprocess.run([str(executable)], input='\n'.join(lines) + '\n', text=True,
                                    capture_output=True, check=True)
        actual = [[int(v) for v in line.split()] for line in result.stdout.splitlines()]
        if len(actual) != len(expected):
            raise ValueError('Native C oracle returned a different number of cases')
        for case, first, second in zip(cases, expected, actual):
            if first != second:
                raise ValueError(('Native Python/C projection mismatch', case, first, second))
        p.assert_unchanged()
        return dict(cases=len(cases), mismatches=0, unmodified_engine_function_bodies=True,
                    oracle_code_sha256=hashlib.sha256(code.encode()).hexdigest(),
                    function_sha256=dict(FUNCTION_HASHES), arm_build=False, source_written=False)


def diagnose_registrations(projection, registration_report):
    """Report authored registration conflicts against native regional intervals.

    A mouth outside its native UI cell is a useful conflict, not a license to
    move terrain or assume the opposite pixel owns an entire native map.
    """
    result = []
    for row in registration_report['registrations']:
        name, local = row['native_map'], row['native_tile']
        native = projection.project(name, *local)
        authored = [v // 8 for v in row['global_tile']]
        result.append(dict(map=name, component=row['component'], local=local, authored_atlas=authored,
            native_atlas=native['atlas'], native_atlas_pixels=native['atlas_pixels'],
            native_cursor=native['cursor'], section=native['section'], panel=native['panel'],
            authored_pixel_in_native_regional_cell=authored in native['atlas_pixels'],
            geographical_registration_proven=False))
    return dict(registrations=result, compared=len(result),
                outside_native_regional_cell=sum(not row['authored_pixel_in_native_regional_cell'] for row in result),
                terrain_changed=False, gps_changed=False)


def census_native_water(projection, names):
    """Group real surfable cells by native UI bin; retain ambiguity explicitly.

    A blue pixel with a real water witness is a *candidate* native pixel. Dry
    witnesses and multiple maps remain visible; this never emits exclusions.
    """
    inputs, candidates, bins = projection.inputs, defaultdict(list), []
    for name in sorted(set(names)):
        if inputs.maps[name]['map_type'] not in OUTDOOR:
            raise ValueError(('Water census requires a native outdoor map', name))
        layout, groups = inputs.layout(name), {}
        for y in range(layout['height']):
            for x in range(layout['width']):
                native = projection.native_cursor(name, x, y)
                key = tuple(native['cursor'])
                if key not in groups:
                    groups[key] = dict(result=projection.project(name, x, y), wet=0, dry=0,
                                       wet_witness=None, dry_witness=None)
                group = groups[key]
                kind = 'wet' if inputs.water(name, x, y) else 'dry'
                group[kind] += 1
                if group[kind + '_witness'] is None:
                    group[kind + '_witness'] = [x, y]
        for cursor, group in sorted(groups.items()):
            native = group['result']
            row = dict(map=name, section=native['section'], panel=native['panel'], cursor=list(cursor),
                       atlas_pixels=native['atlas_pixels'], atlas_blue_pixels=native['atlas_blue_pixels'],
                       wet_cells=group['wet'], dry_or_blocked_cells=group['dry'],
                       wet_witness=group['wet_witness'], dry_or_blocked_witness=group['dry_witness'])
            bins.append(row)
            if group['wet']:
                for point in native['atlas_blue_pixels']:
                    candidates[tuple(point)].append(dict(map=name, cursor=list(cursor),
                        local_water_witness=group['wet_witness'], mixed_native_bin=bool(group['dry'])))
    projection.assert_unchanged()
    return dict(kind='native-engine-regional-water-candidates-not-physical-ownership', bins=bins,
                candidate_native_blue_pixels=[dict(atlas=list(point), witnesses=candidates[point])
                    for point in sorted(candidates, key=lambda q: (q[1], q[0]))],
                candidate_native_blue_count=len(candidates), exact_pixel_ownership_proven=False,
                generated_geometry_exclusions=[], eight_local_tiles_per_pixel_assumed=False,
                old_gps_used=False, source_written=False, native_rom_validated=False)


def main():
    from atlas_surf_source import Source
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--registrations', type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    inputs = Source(args.source)
    projection = NativeProjection(inputs)
    registrations = json.loads(args.registrations.read_bytes()) if args.registrations else None
    names = sorted({r['native_map'] for r in registrations['registrations']}) if registrations else [
        n for n, r in inputs.maps.items() if n in inputs.identities
        and r['map_type'] in OUTDOOR and not n.startswith('Journey')]
    cases = [(name, x, y) for name in names for y in range(inputs.layout(name)['height'])
             for x in range(inputs.layout(name)['width'])]
    report = dict(kind='atlas-regional-native-projection-readonly', oracle=NativeCOracle(projection).compare(cases),
                  water=census_native_water(projection, names),
                  registrations=diagnose_registrations(projection, registrations) if registrations else None,
                  art_sha256=dict(projection.truth.array_sha256), asset_sha256=dict(projection.assets),
                  limitations=['Native UI quantization is not a physical embedding or per-pixel ownership proof',
                               'Indoor/cave/SS Tidal projections require real save-state context',
                               'No native ROM, reachability or controller validation in this report'],
                  input_sha256=dict(sorted(inputs.inputs.items())), source_written=False,
                  generated_gps_changed=False, world_art_changed=False, native_rom_validated=False)
    projection.assert_unchanged()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(dict(report=str(args.report), cases=report['oracle']['cases'],
                          candidates=report['water']['candidate_native_blue_count'],
                          conflicts=report['registrations']['outside_native_regional_cell'] if registrations else None)))


if __name__ == '__main__':
    main()
