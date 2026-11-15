"""Run real emitted Dive C against independent coordinate/terrain expectations.

Host execution proves the resolver's arithmetic and rejection rules, not the
native effect, underwater avatar animation or portal traversal in a release ROM.
"""
import ctypes
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from atlas_surf_dives import HELPERS, patch_specs, reserve_patches, render_header, stage
from atlas_surf_runtime import render_runtime, stage as stage_runtime
from atlas_surf_source import Source


def fixture_plan(group=90):
    chunks = []
    for i, spec in enumerate(patch_specs()):
        x, y = spec['atlas']
        name = 'DiveTest' + spec['name']
        chunks.append(dict(name=name, id='MAP_' + name.upper(), group='AtlasDives',
                           group_index=group, number=i, origin=[8*x, 8*y], width=8, height=8,
                           water_runs=[[y, 1, 7] for y in range(1, 7)], connections=[]))
    return dict(scale=8, corridor_width=6, chunks=chunks, water_tiles=180)


class ReservationTests(unittest.TestCase):
    def test_exact_five_fixed_specs_and_affine_descent(self):
        expected = [('Mares', [125, 68], [38, 10]), ('Origens', [135, 87], [38, 10]),
                    ('Profundezas', [134, 97], [38, 10]), ('Dimensoes', [13, 89], [30, 64]),
                    ('Abismo', [14, 99], [30, 64])]
        self.assertEqual([(s['name'], s['atlas'], s['portal']) for s in patch_specs()], expected)
        for row in patch_specs():
            x, y = row['atlas']; px, py = row['portal']
            self.assertEqual(row['global_rect'], [8*x+2, 8*y+5, 5, 3])
            self.assertEqual(row['depth_origin'], [8*x+4-px, 8*y+4-py])
            left, top, _, _ = row['global_rect']
            self.assertEqual([left+2-row['depth_origin'][0], top+1-row['depth_origin'][1]], [px, py+2])

    def test_reservation_adds_only_exact_patch_cells_and_is_idempotent(self):
        original = fixture_plan()
        frozen = deepcopy(original)
        reserved = reserve_patches(original)
        self.assertEqual(original, frozen)
        self.assertEqual(reserve_patches(reserved), reserved)
        self.assertEqual(reserved['water_tiles'], 205)
        for before, after, spec in zip(original['chunks'], reserved['chunks'], patch_specs()):
            a = {(x, y) for y, first, last in before['water_runs'] for x in range(first, last)}
            b = {(x, y) for y, first, last in after['water_runs'] for x in range(first, last)}
            left, top, width, height = spec['global_rect']
            patch = {(gx-before['origin'][0], gy-before['origin'][1])
                     for gy in range(top, top+height) for gx in range(left, left+width)}
            self.assertEqual(b, a | patch)
            self.assertEqual(after['origin'], before['origin'])
            self.assertEqual([after['width'], after['height']], [before['width'], before['height']])

    def test_missing_or_ambiguous_owner_is_not_replaced_by_an_offshore_guess(self):
        plan = fixture_plan()
        del plan['chunks'][0]
        with self.assertRaisesRegex(ValueError, 'one real physical owner'):
            reserve_patches(plan)
        plan = fixture_plan()
        plan['chunks'].append(deepcopy(plan['chunks'][0]))
        with self.assertRaisesRegex(ValueError, 'one real physical owner'):
            reserve_patches(plan)
        plan = fixture_plan(); plan['scale'] = 4
        with self.assertRaisesRegex(ValueError, 'eight-tile'):
            reserve_patches(plan)

    def test_staging_requires_explicit_prepared_reservations(self):
        with self.assertRaisesRegex(ValueError, 'Reserve all five'):
            stage(None, fixture_plan(), donor={})


SHIMS = r'''
#include <stdint.h>
#include <stddef.h>
#include <string.h>
typedef uint8_t u8; typedef int8_t s8; typedef uint16_t u16; typedef uint32_t u32;
typedef int16_t s16; typedef int32_t s32; typedef uint8_t bool8;
#define TRUE 1
#define FALSE 0
#define ARRAY_COUNT(a) (sizeof(a)/sizeof((a)[0]))
#define MAPGRID_METATILE_ID_MASK 0x3FF
#define MAPGRID_COLLISION_MASK 0xC00
#define MAPGRID_ELEVATION_SHIFT 12
#define ELEVATION_SURF 1
#define ELEVATION_DEFAULT 3
#define METATILE_ATTR_BEHAVIOR_MASK 255
#define METATILE_ATTR_BEHAVIOR_MASK_FRLG 511
#define NUM_METATILES_TOTAL 1024
#define MAP_TYPE_UNDERWATER 5
#define WARP_ID_NONE -1
enum Connection { CONNECTION_NONE, CONNECTION_SOUTH, CONNECTION_NORTH,
                  CONNECTION_WEST, CONNECTION_EAST, CONNECTION_DIVE, CONNECTION_EMERGE };
struct Tileset { const void *metatileAttributes; };
struct MapLayout { int width, height; u16 *map; int isFrlg;
                   const struct Tileset *primaryTileset, *secondaryTileset; };
struct MapHeader { const struct MapLayout *mapLayout; int mapType; };
struct SaveBlock { struct { u8 mapGroup, mapNum; } location; };
static struct SaveBlock save;
static struct SaveBlock *gSaveBlock1Ptr = &save;
static struct MapHeader gMapHeader;
static u16 emeraldGeneral[512], emeraldSecondary[512];
static u32 frlgGeneral[640], frlgSecondary[384];
static const struct Tileset primary = { emeraldGeneral }, secondary = { emeraldSecondary };
static const struct Tileset primaryFrlg = { frlgGeneral }, secondaryFrlg = { frlgSecondary };
static u16 surfaceWords[5][64], depthWords[5][48*80];
static struct MapLayout surfaceLayouts[5], depthLayouts[5];
static struct MapHeader surfaceHeaders[5], depthHeaders[5];
static int warpCalls, targetGroup, targetNumber, targetX, targetY, targetWarp;

static u32 GetNumMetatilesInPrimary(const struct MapLayout *layout) { return layout->isFrlg ? 640 : 512; }
static bool8 MetatileBehavior_IsSurfableWaterOrUnderwater(u8 behavior) { return behavior == 0x10 || behavior == 0x12; }
static bool8 MetatileBehavior_IsDiveable(u8 behavior) { return behavior == 0x12; }
static bool8 MetatileBehavior_IsUnableToEmerge(u8 behavior) { return behavior == 0x30; }
static const struct MapHeader *Overworld_GetMapHeaderByGroupAndId(u16 group, u16 number) {
    int index;
    if (group == 90 && number < 5) return &surfaceHeaders[number];
    if (group == 83 && number >= 10 && number <= 18 && !(number & 1)) {
        index = (number-10)/2; return &depthHeaders[index];
    }
    return NULL;
}
static void SetWarpDestination(s8 group, s8 number, s8 warp, s8 x, s8 y) {
    ++warpCalls; targetGroup=group; targetNumber=number; targetWarp=warp; targetX=x; targetY=y;
}
'''


@unittest.skipUnless(shutil.which('gcc'), 'Host C compiler required for Dive equivalence')
class NativeHelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='atlas-dive-tests-')
        cls.path = Path(cls.temp.name)
        runtime, _ = render_runtime(fixture_plan())
        specs = patch_specs()
        for i, site in enumerate(specs):
            site.update(depth_id=(83 << 8) | (10 + 2*i),
                        depth_dimensions=[48, 24 if i < 3 else 80])
        cls.specs = specs
        code = SHIMS + runtime + render_header(specs) + HELPERS + r'''
void reset(void) {
    int i, j;
    memset(emeraldGeneral,0,sizeof(emeraldGeneral)); memset(emeraldSecondary,0,sizeof(emeraldSecondary));
    memset(frlgGeneral,0,sizeof(frlgGeneral)); memset(frlgSecondary,0,sizeof(frlgSecondary));
    emeraldGeneral[0x14F]=0x12; emeraldGeneral[0x170]=0x10;
    emeraldSecondary[0x80]=0x30;
    // Same numeric ID deliberately differs between the CURRENT underwater
    // Emerald bank and the TARGET FRLG bank. Reading gMapHeader is incorrect.
    frlgGeneral[0x12B]=0x10;
    for (i=0;i<5;++i) {
        for(j=0;j<64;++j) surfaceWords[i][j]=0x114F;
        for(j=0;j<48*80;++j) depthWords[i][j]=0x3216;
        surfaceLayouts[i]=(struct MapLayout){8,8,surfaceWords[i],0,&primary,&secondary};
        depthLayouts[i]=(struct MapLayout){48,i<3?24:80,depthWords[i],0,&primary,&secondary};
        surfaceHeaders[i]=(struct MapHeader){&surfaceLayouts[i],1};
        depthHeaders[i]=(struct MapHeader){&depthLayouts[i],MAP_TYPE_UNDERWATER};
    }
    warpCalls=0;
}
void current(int underwater,int index) {
    save.location.mapGroup=underwater?83:90;
    save.location.mapNum=underwater?10+2*index:index;
    gMapHeader=underwater?depthHeaders[index]:surfaceHeaders[index];
    warpCalls=0;
}
void unrelated(void) { save.location.mapGroup=2; save.location.mapNum=3; gMapHeader=surfaceHeaders[0]; warpCalls=0; }
void surface_word(int index,int x,int y,unsigned word) { surfaceWords[index][8*y+x]=word; }
void depth_word(int index,int x,int y,unsigned word) { depthWords[index][48*y+x]=word; }
void surface_frlg(int index) { surfaceLayouts[index].isFrlg=1;surfaceLayouts[index].primaryTileset=&primaryFrlg;surfaceLayouts[index].secondaryTileset=&secondaryFrlg; }
int request(int direction,unsigned x,unsigned y) { return JourneyAtlasSetDiveWarp(direction,x,y); }
int calls(void) { return warpCalls; }
int warp_group(void) { return targetGroup; } int warp_number(void) { return targetNumber; }
int warp_x(void) { return targetX; } int warp_y(void) { return targetY; }
int warp_id(void) { return targetWarp; }
int depth_position(int index,int x,int y) {
    u16 result=0xBEEF;
    if (!JourneyAtlasDepthPosition(83,10+2*index,x,y,&result)) return -1;
    return result;
}
// Exercise the otherwise intentionally shared helpers under -Werror.
int smoke(void) { u16 result; return JourneyAtlasGroup(90)+JourneyAtlasPosition(90,0,0,0,&result); }
'''
        (cls.path / 'probe.c').write_text(code)
        result = subprocess.run(['gcc', '-std=gnu89', '-shared', '-fPIC', '-O2', '-Wall', '-Wextra', '-Werror',
                                 str(cls.path / 'probe.c'), '-o', str(cls.path / 'probe.so')],
                                capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stderr)
        cls.lib = ctypes.CDLL(str(cls.path / 'probe.so'))
        for name, count in [('current', 2), ('surface_word', 4), ('depth_word', 4),
                            ('request', 3), ('depth_position', 3), ('surface_frlg', 1)]:
            getattr(cls.lib, name).argtypes = [ctypes.c_int] * count
            getattr(cls.lib, name).restype = ctypes.c_int

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.lib.reset()

    def target(self):
        return [self.lib.warp_group(), self.lib.warp_number(), self.lib.warp_id(),
                self.lib.warp_x(), self.lib.warp_y()]

    def test_all_75_patch_cells_descend_affinely_and_emerge_to_same_physical_tile(self):
        for i, site in enumerate(self.specs):
            left, top, width, height = site['global_rect']
            sx, sy = [8*v for v in site['atlas']]
            for gy in range(top, top+height):
                for gx in range(left, left+width):
                    dx, dy = gx-site['depth_origin'][0], gy-site['depth_origin'][1]
                    self.lib.current(0, i)
                    self.assertEqual(self.lib.request(5, gx-sx, gy-sy), 1)
                    self.assertEqual(self.lib.calls(), 1)
                    self.assertEqual(self.target(), [83, 10+2*i, -1, dx, dy])
                    self.lib.current(1, i)
                    self.assertEqual(self.lib.request(6, dx, dy), 1)
                    self.assertEqual(self.lib.calls(), 1)
                    self.assertEqual(self.target(), [90, i, -1, gx-sx, gy-sy])

    def test_center_arrival_is_two_tiles_below_the_preserved_portal(self):
        for i, site in enumerate(self.specs):
            self.lib.current(0, i)
            self.assertEqual(self.lib.request(5, 4, 6), 1)
            self.assertEqual(self.target()[3:], site['depth_arrival'])

    def test_depth_gps_every_tile_uses_same_affine_system_without_perpendicular_drift(self):
        for i, site in enumerate(self.specs):
            width, height = site['depth_dimensions']
            ox, oy = site['depth_origin']
            for y in range(height):
                for x in range(width):
                    self.assertEqual(self.lib.depth_position(i, x, y),
                                     (ox+x)//8 | ((oy+y)//8 << 8))

    def test_emerge_refuses_reef_land_nonsurf_water_and_cells_without_an_owner(self):
        for i, site in enumerate(self.specs):
            dx, dy = site['depth_arrival']
            for word in [0x154F, 0x314F, 0x1200]:
                self.lib.surface_word(i, 4, 6, word)
                self.lib.current(1, i)
                self.assertEqual(self.lib.request(6, dx, dy), 0, (site['name'], hex(word)))
                self.assertEqual(self.lib.calls(), 0)
            self.lib.current(1, i)
            self.assertEqual(self.lib.request(6, 0, 0), 0)
            self.assertEqual(self.lib.calls(), 0)

    def test_target_layout_attributes_are_read_even_when_current_bank_disagrees(self):
        for i, site in enumerate(self.specs):
            self.lib.surface_frlg(i)
            self.lib.surface_word(i, 4, 6, 0x112B)
            self.lib.current(1, i)
            self.assertEqual(self.lib.request(6, *site['depth_arrival']), 1)
            self.assertEqual(self.target(), [90, i, -1, 4, 6])

    def test_dive_rejects_ordinary_water_outside_patch_bad_depth_and_signed_wrap(self):
        self.lib.current(0, 0)
        self.assertEqual(self.lib.request(5, 1, 1), 0)
        self.assertEqual(self.lib.request(5, 65535, 6), 0)
        self.lib.surface_word(0, 4, 6, 0x1170)
        self.lib.current(0, 0)
        self.assertEqual(self.lib.request(5, 4, 6), 0)
        self.lib.surface_word(0, 4, 6, 0x114F)
        for word in [0x3616, 0x1216, 0x3280]:
            self.lib.depth_word(0, 38, 12, word)
            self.lib.current(0, 0)
            self.assertEqual(self.lib.request(5, 4, 6), 0)
            self.assertEqual(self.lib.calls(), 0)

    def test_unrelated_native_maps_retain_the_legacy_resolver(self):
        self.lib.unrelated()
        self.assertEqual(self.lib.request(5, 4, 6), -1)
        self.assertEqual(self.lib.request(6, 4, 6), -1)
        self.assertEqual(self.lib.calls(), 0)


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / '.local/generated-area-review-src'


@unittest.skipUnless((SOURCE / '.journey-generated-area-review').is_file(), 'Frozen source171 not installed')
class SourceIntegrationTests(unittest.TestCase):
    def prepare(self):
        from candidate_layer import Layer
        from prepare_generated_area_review import PRIOR, LAYER
        from atlas_surf_layer import stage_geometry
        layer = Layer(SOURCE, 'atlas-dive-staging-test', PRIOR+[LAYER])
        plan = reserve_patches(fixture_plan())
        for chunk in plan['chunks']:
            chunk.pop('group_index')
        # Native coordinates, not universal metatile IDs. The two samples are
        # authenticated afresh against the immutable layer171 source below.
        terrain = Source(SOURCE)
        words = terrain.words('Route127'); layout = terrain.layout('Route127')
        wet = next((i % layout['width'], i // layout['width']) for i, w in enumerate(words)
                   if w >> 12 == 1 and not w & 0xC00 and terrain.water('Route127', i % layout['width'], i // layout['width']))
        reef = next((i % layout['width'], i // layout['width']) for i, w in enumerate(words) if w & 0xC00)
        donors = {c['name']: dict(map='Route127', water_tile=list(wet), reef_tile=list(reef)) for c in plan['chunks']}
        bound, _ = stage_geometry(layer, plan, donors)
        stage_runtime(layer, bound)
        return layer, bound

    def test_real171_staging_preserves_underwater_geometry_portals_actors_and_native_effects(self):
        layer, plan = self.prepare()
        originals = {s['depth']: (SOURCE / f'data/maps/{s["depth"]}/map.json').read_bytes() for s in patch_specs()}
        report = stage(layer, plan, donor=dict(map='Route127', tile=[72, 49]))
        self.assertEqual(report['patch_cells'], 75)
        self.assertEqual(report['deep_water_word'], 0x114F)
        self.assertEqual(report['donor']['behavior'], 0x12)
        for spec in patch_specs():
            name = spec['depth']; original = json.loads(originals[name])
            actual = json.loads(layer.outputs[f'data/maps/{name}/map.json'])
            expected = deepcopy(original)
            expected['connections'] = [r for r in expected['connections'] if r['direction'] != 'emerge']
            self.assertEqual(actual, expected)
            self.assertEqual((SOURCE / f'data/maps/{name}/map.json').read_bytes(), originals[name])
            source_layouts = json.loads((SOURCE / 'data/layouts/layouts.json').read_text())['layouts']
            layout = next(r for r in source_layouts if r['id'] == actual['layout'])
            self.assertNotIn(layout['blockdata_filepath'], layer.outputs)
            self.assertNotIn(f'data/maps/{spec["sanctuary"]}/map.json', layer.outputs)
        self.assertNotIn('src/field_control_avatar.c', layer.outputs)
        self.assertNotIn('src/field_screen_effect.c', layer.outputs)
        overworld = layer.outputs['src/overworld.c'].decode()
        self.assertNotIn('GetAttributeByMetatileIdAndMapLayout(', overworld)
        self.assertLess(overworld.index('s8 atlas = JourneyAtlasSetDiveWarp'), overworld.index('    connection = GetMapConnection(dir);'))
        self.assertIn('SetWarpDestinationToDiveWarp();', overworld)
        self.assertTrue(report['signed_warp_abi_checked'])
        self.assertFalse(report['native_validated'])

    def test_frlg_donor_or_unreserved_bank_is_rejected_instead_of_copying_a_magic_id(self):
        layer, plan = self.prepare()
        with self.assertRaisesRegex(ValueError, 'Emerald bank'):
            stage(layer, plan, donor=dict(map='OneIsland_Frlg', tile=[0, 0]))
        layouts = json.loads(layer.outputs['data/layouts/layouts.json'])
        first = json.loads(layer.outputs[f'data/maps/{plan["chunks"][0]["name"]}/map.json'])
        layout = next(r for r in layouts['layouts'] if r['id'] == first['layout'])
        layout['secondary_tileset'] = 'gTileset_Fallarbor'
        layer.stage('data/layouts/layouts.json', json.dumps(layouts))
        with self.assertRaisesRegex(ValueError, 'donor graphics banks'):
            stage(layer, plan, donor=dict(map='Route127', tile=[72, 49]))


if __name__ == '__main__':
    unittest.main()
