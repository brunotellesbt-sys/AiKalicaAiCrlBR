"""Compile original, pruned and RLE C together and compare native cells.

Host tests establish exact lookup/data equivalence, including revision171
when its immutable source is available. They do not certify ROM travel or
Continue/save migration.
"""
import copy
import ctypes
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from atlas_surf_legacy import HEADER_PATH, NAVIGATION_PATH, stage_navigation_prune
from atlas_surf_overlay import OverlaySource
from atlas_surf_source import Source
import test_atlas_surf_source_inventory as native_fixtures


def _original_symbols(header):
    names = set(re.findall(r'\b(sWorld\w+)\b', header))
    names.update(re.findall(r'\bstruct\s+(\w+)\s*\{', header))
    return re.sub(r'\b(?:' + '|'.join(sorted(names, key=len, reverse=True)) + r')\b',
                  lambda match: 'Original' + match[0], header)


class Probe:
    def __init__(self, source, layer, records):
        self.temporary = tempfile.TemporaryDirectory(prefix='atlas-legacy-c-')
        self.root = Path(self.temporary.name)
        self.original = (source.source / NAVIGATION_PATH).read_text()
        self.metadata = stage_navigation_prune(layer, records)
        retired = sorted((row['map'] for row in records), key=source.identities.__getitem__)
        ids = [source.identities[name] for name in retired]
        water = [int(source.water(name, x, y)) for name in retired
                 for y in range(source.layout(name)['height'])
                 for x in range(source.layout(name)['width'])]
        macros = '\n'.join(f'#define {row["id"]} {source.identities[name]}'
                           for name, row in source.maps.items() if name in source.identities)
        (self.root / 'original.h').write_text(_original_symbols(self.original))
        (self.root / 'pruned.h').write_bytes(layer.outputs[NAVIGATION_PATH])
        (self.root / 'legacy.h').write_bytes(layer.outputs[HEADER_PATH])
        code = '''
#include <stdint.h>
#include <stddef.h>
#include <string.h>
typedef uint8_t bool8;
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int16_t s16;
#define TRUE 1
#define FALSE 0
#define ARRAY_COUNT(a) (sizeof(a)/sizeof((a)[0]))
#define MAP_GROUP(map) ((map) >> 8)
#define MAP_NUM(map) ((map) & 255)
''' + macros + '''
#include "original.h"
#include "pruned.h"
#include "legacy.h"
static const u16 expectedMaps[] = {''' + ','.join(map(str, ids)) + '''};
static const u8 expectedWater[] = {''' + ','.join(map(str, water)) + '''};
static int retired(u16 map) {
    unsigned i;
    for (i=0; i<ARRAY_COUNT(expectedMaps); i++) if (expectedMaps[i]==map) return 1;
    return 0;
}
static const struct OriginalJourneyWorldTileGrid *original_grid(u16 map) {
    unsigned i;
    for (i=0; i<ARRAY_COUNT(OriginalsWorldTileGrids); i++)
        if (OriginalsWorldTileGrids[i].map==map) return &OriginalsWorldTileGrids[i];
    return NULL;
}
static const struct JourneyWorldTileGrid *active_grid(u16 map) {
    unsigned i;
    for (i=0; i<ARRAY_COUNT(sWorldTileGrids); i++)
        if (sWorldTileGrids[i].map==map) return &sWorldTileGrids[i];
    return NULL;
}
static u16 original_position(const struct OriginalJourneyWorldTileGrid *grid, s16 x, s16 y) {
    if (x<0) x=0;
    if (y<0) y=0;
    if (x>=grid->width) x=grid->width-1;
    if (y>=grid->height) y=grid->height-1;
    return OriginalsWorldNavigationPixels[grid->first+y*grid->width+x];
}
int every_retired_cell(void) {
    unsigned i, x, y, waterIndex=0;
    for (i=0; i<ARRAY_COUNT(expectedMaps); i++) {
        const struct OriginalJourneyWorldTileGrid *grid=original_grid(expectedMaps[i]);
        if (!grid) return 1;
        for (y=0; y<grid->height; y++) for (x=0; x<grid->width; x++) {
            u16 pixel=0xBEEF;
            bool8 water=77;
            if (!JourneyAtlasLegacyWorldPosition(grid->map,x,y,&pixel)) return 2;
            if (pixel!=original_position(grid,x,y)) return 3;
            if (!JourneyAtlasLegacyWater(grid->map,x,y,&water)) return 4;
            if (water!=expectedWater[waterIndex++]) return 5;
        }
    }
    return waterIndex!=ARRAY_COUNT(expectedWater);
}
int every_16_bit_id(void) {
    unsigned map;
    for (map=0; map<65536; map++) {
        u16 pixel=0xBEEF;
        bool8 water=77;
        int known=retired(map);
        if (!!JourneyAtlasLegacyWorldPosition(map,0,0,&pixel)!=known) return 1;
        if (!!JourneyAtlasLegacyWater(map,0,0,&water)!=known) return 2;
        if (!known && (pixel!=0xBEEF || water!=77)) return 3;
        if (JourneyAtlasLegacyWorldPosition(map,0,0,NULL)) return 4;
        if (JourneyAtlasLegacyWater(map,0,0,NULL)) return 5;
    }
    return 0;
}
int every_retained_grid(void) {
    unsigned i, found=0;
    for (i=0; i<ARRAY_COUNT(OriginalsWorldTileGrids); i++) {
        const struct OriginalJourneyWorldTileGrid *old=&OriginalsWorldTileGrids[i];
        const struct JourneyWorldTileGrid *now=active_grid(old->map);
        if (retired(old->map)) { if (now) return 1; continue; }
        if (!now || old->width!=now->width || old->height!=now->height) return 2;
        if (memcmp(&OriginalsWorldNavigationPixels[old->first],
                   &sWorldNavigationPixels[now->first],2*old->width*old->height)) return 3;
        found++;
    }
    return found!=ARRAY_COUNT(sWorldTileGrids);
}
int all_clamps_and_invalid_coordinates(void) {
    unsigned i, a, b;
    for (i=0; i<ARRAY_COUNT(expectedMaps); i++) {
        const struct OriginalJourneyWorldTileGrid *grid=original_grid(expectedMaps[i]);
        s16 xs[]={-32768,-1,0,grid->width-1,grid->width,grid->width+1,32767};
        s16 ys[]={-32768,-1,0,grid->height-1,grid->height,grid->height+1,32767};
        for (a=0; a<ARRAY_COUNT(xs); a++) for (b=0; b<ARRAY_COUNT(ys); b++) {
            u16 pixel=0xBEEF;
            bool8 water=77;
            int valid=xs[a]>=0 && ys[b]>=0 && xs[a]<grid->width && ys[b]<grid->height;
            if (!JourneyAtlasLegacyWorldPosition(grid->map,xs[a],ys[b],&pixel)) return 1;
            if (pixel!=original_position(grid,xs[a],ys[b])) return 2;
            if (!!JourneyAtlasLegacyWater(grid->map,xs[a],ys[b],&water)!=valid) return 3;
            if (!valid && water!=77) return 4;
        }
    }
    return 0;
}
unsigned legacy_bytes(void) {
    return sizeof(sAtlasLegacyMaps)+sizeof(sAtlasLegacyRows)+sizeof(sAtlasLegacyRunEnds)
        +sizeof(sAtlasLegacyRunPixels)+sizeof(sAtlasLegacyWater);
}
unsigned original_bytes(void) {
    return sizeof(OriginalsWorldNavigationPixels)+sizeof(OriginalsWorldTileGrids);
}
unsigned active_bytes(void) { return sizeof(sWorldNavigationPixels)+sizeof(sWorldTileGrids); }
int water_cell(unsigned map, short x, short y) {
    bool8 out=77;
    return JourneyAtlasLegacyWater(map,x,y,&out) ? out : -1;
}
'''
        (self.root / 'probe.c').write_text(code)
        compiler = shutil.which('gcc') or shutil.which('cc')
        subprocess.run([compiler, '-std=gnu89', '-shared', '-fPIC', '-O2', '-Wall', '-Wextra',
                        '-Werror', '-Wno-unused-const-variable', str(self.root / 'probe.c'),
                        '-o', str(self.root / 'probe.so')], check=True, capture_output=True, text=True)
        self.lib = ctypes.CDLL(str(self.root / 'probe.so'))
        self.lib.water_cell.argtypes = [ctypes.c_uint16, ctypes.c_int16, ctypes.c_int16]

    def close(self):
        self.temporary.cleanup()


class LegacyFixtureTests(unittest.TestCase):
    def fixture(self):
        helper = native_fixtures.NativeInventoryTests()
        self.addCleanup(helper.doCleanups)
        source, layer = helper.fixture({
            'Emerald': ('emerald', 5, 3, [0x1001,0x1200,0x1280,0x1C01,0x3000,
                0x3001,0x0001,0xF001,0x1401,0x1004, 0x1000,0x1001,0x1200,0x1280,0x1001]),
            'Frlg': ('frlg', 3, 2, [0x1200,0x1280,0x1001,0x1001,0x1680,0x1000]),
            'Retained': ('emerald', 4, 2, [0x1000]*8)})
        groups = dict(group_order=['Group']+[f'Empty{i}' for i in range(254)]+['Last'],
                      Group=['Emerald','Retained'], Last=[f'Padding{i}' for i in range(255)]+['Frlg'])
        groups.update({f'Empty{i}': [] for i in range(254)})
        layer.parent('data/maps/map_groups.json', groups)
        layer.parent('data/maps/Unused/map.json', dict(id='MAP_UNUSED',layout='LAYOUT_Retained'))
        layouts = json.loads((source / 'data/layouts/layouts.json').read_bytes())
        row = next(row for row in layouts['layouts'] if row['id']=='LAYOUT_Frlg')
        row.update(primary_tileset='FrlgPrimary', secondary_tileset='FrlgSecondary')
        layer.parent('data/layouts/layouts.json', layouts)
        layer.parent('src/data/tilesets/headers.h', (source/'src/data/tilesets/headers.h').read_bytes()+
                     b'const struct Tileset FrlgPrimary = { .metatileAttributes = FrlgPrimaryAttrs };\n'
                     b'const struct Tileset FrlgSecondary = { .metatileAttributes = FrlgSecondaryAttrs };\n')
        layer.parent('src/data/tilesets/metatiles.h', (source/'src/data/tilesets/metatiles.h').read_bytes()+
                     b'const u32 FrlgPrimaryAttrs[] = INCBIN_U32("frlg-primary.bin");\n'
                     b'const u32 FrlgSecondaryAttrs[] = INCBIN_U32("frlg-secondary.bin");\n')
        primary, secondary = [0]*640, [0]*384
        primary[1], secondary[0] = 0x81, 0x85
        layer.parent('frlg-primary.bin', struct.pack('<640I', *primary))
        layer.parent('frlg-secondary.bin', struct.pack('<384I', *secondary))
        pixels = [0,65535,65535,123,4,5] + [0xAAAA,0xBBBB] + list(range(8))
        pixels += [44,44,91,4,4, 0,1,2,3,4, 44,44,91,4,4]
        layer.parent(NAVIGATION_PATH, ('''// Untouched historical prefix.
struct JourneyWorldTileGrid { u32 first; u16 map, width, height; };
static const u16 sWorldNavigationPixels[] = {'''+','.join(map(str,pixels))+'''};
static const struct JourneyWorldTileGrid sWorldTileGrids[] = {
{0, (MAP_GROUP(MAP_FRLG)<<8)|MAP_NUM(MAP_FRLG), 3, 2},
{8, (MAP_GROUP(MAP_RETAINED)<<8)|MAP_NUM(MAP_RETAINED), 4, 2},
{16, (MAP_GROUP(MAP_EMERALD)<<8)|MAP_NUM(MAP_EMERALD), 5, 3},
};
// Untouched historical suffix.
''').encode())
        return source, layer, [dict(map='Frlg'),dict(map='Emerald')]

    @unittest.skipUnless(shutil.which('gcc') or shutil.which('cc'), 'Native host compiler required')
    def test_real_c_every_cell_id_clamp_and_native_bank(self):
        root, layer, records = self.fixture()
        before = {path: hashlib.sha256((root/path).read_bytes()).hexdigest() for path in layer.expected}
        probe = Probe(Source(root), layer, records)
        self.addCleanup(probe.close)
        for name in ('every_retired_cell','every_16_bit_id','every_retained_grid',
                     'all_clamps_and_invalid_coordinates'):
            self.assertEqual(getattr(probe.lib,name)(), 0, name)
        self.assertEqual(probe.lib.legacy_bytes(), probe.metadata['legacy_data_bytes'])
        self.assertEqual(probe.lib.original_bytes(), probe.metadata['navigation_data_bytes_before'])
        self.assertEqual(probe.lib.active_bytes(), probe.metadata['navigation_data_bytes_after'])
        # Same metatile512 is secondary water in Emerald and primary land in
        # FRLG;640 selects a different bank again. Blocked water stays false.
        self.assertEqual([probe.lib.water_cell(0,x,0) for x in range(5)], [1,1,0,0,0])
        self.assertEqual([probe.lib.water_cell(65535,x,0) for x in range(3)], [0,1,1])
        self.assertEqual(probe.lib.water_cell(65535,1,1), 0)
        self.assertEqual(probe.lib.water_cell(1,0,0), -1)
        self.assertEqual(set(layer.outputs), {NAVIGATION_PATH,HEADER_PATH})
        self.assertEqual(before, {path: hashlib.sha256((root/path).read_bytes()).hexdigest()
                                  for path in layer.expected})
        result = layer.outputs[NAVIGATION_PATH].decode()
        self.assertIn('{2, (MAP_GROUP(MAP_RETAINED)<<8)|MAP_NUM(MAP_RETAINED), 4, 2}', result)
        self.assertIn('{43690,48059,0,1,2,3,4,5,6,7}', result)
        self.assertTrue(result.startswith('// Untouched historical prefix.'))
        self.assertTrue(result.endswith('// Untouched historical suffix.\n'))
        self.assertTrue(probe.metadata['migration_only'])
        self.assertTrue(probe.metadata['native_rom_validation_pending'])

    def test_order_is_deterministic_and_reapplication_rejected(self):
        root, layer, records = self.fixture()
        first = stage_navigation_prune(layer, records)
        output = copy.deepcopy(layer.outputs)
        with self.assertRaisesRegex(ValueError, 'already installed'):
            stage_navigation_prune(layer, records)
        layer.outputs.clear()
        second = stage_navigation_prune(layer, list(reversed(records)))
        self.assertEqual(first, second)
        self.assertEqual(output, layer.outputs)

    def test_inventory_mismatch_and_missing_grids_fail_without_staging(self):
        for change in [dict(packed_id=123),dict(id='MAP_WRONG'),dict(dimensions=[9,3]),
                       dict(layout='LAYOUT_WRONG'),dict(banks=['Wrong','Wrong']),
                       dict(map_sha256='0'*64),dict(blockdata_sha256='0'*64),dict(map='Missing')]:
            with self.subTest(change=change):
                _, layer, records = self.fixture()
                records[0].update(change)
                with self.assertRaises(ValueError):
                    stage_navigation_prune(layer, records)
                self.assertFalse(layer.outputs)
        for records in ([], [dict(map='Emerald')]*2, ['Emerald']):
            _, layer, _ = self.fixture()
            with self.assertRaises(ValueError):
                stage_navigation_prune(layer, records)
            self.assertFalse(layer.outputs)

    def test_malformed_or_overlapping_navigation_is_rejected(self):
        for old, new in [('65535,65535','65536,65535'),
                         ('{16, (MAP_GROUP(MAP_EMERALD)', '{7, (MAP_GROUP(MAP_EMERALD)'),
                         ('{16, (MAP_GROUP(MAP_EMERALD)', '{999, (MAP_GROUP(MAP_EMERALD)'),
                         ('MAP_RETAINED','MAP_UNKNOWN'),
                         ('4, 2},','0, 2},'),
                         ('65535,65535','bogus(),65535')]:
            with self.subTest(new=new):
                root, layer, records = self.fixture()
                header = (root/NAVIGATION_PATH).read_text().replace(old,new)
                layer.parent(NAVIGATION_PATH,header.encode())
                with self.assertRaises(ValueError):
                    stage_navigation_prune(layer, records)
                self.assertFalse(layer.outputs)

    def test_terrain_change_during_read_is_rejected(self):
        root, layer, records = self.fixture()
        original = OverlaySource.water
        changed = False
        def water(source,name,x,y):
            nonlocal changed
            answer = original(source,name,x,y)
            if not changed:
                changed = True
                layer.outputs['Emerald.bin'] = b'changed while reading'
            return answer
        with patch.object(OverlaySource,'water',water):
            with self.assertRaisesRegex(ValueError,'changed while auditing'):
                stage_navigation_prune(layer, records)
        self.assertEqual(set(layer.outputs), {'Emerald.bin'})

    @unittest.skipUnless(shutil.which('gcc') or shutil.which('cc'), 'Native host compiler required')
    def test_wide_rows_and_more_than_65535_runs_use_native_wider_indices(self):
        helper = native_fixtures.NativeInventoryTests()
        self.addCleanup(helper.doCleanups)
        root, layer = helper.fixture({'Wide': ('emerald',256,257,[0x1001]*(256*257)),
                                      'Retained': ('emerald',1,1,[0x1000])})
        pixels = [(y*257+x)&65535 for y in range(257) for x in range(256)] + [0x1234]
        layer.parent(NAVIGATION_PATH, ('''
struct JourneyWorldTileGrid { u32 first; u16 map, width, height; };
static const u16 sWorldNavigationPixels[] = {'''+','.join(map(str,pixels))+'''};
static const struct JourneyWorldTileGrid sWorldTileGrids[] = {
{0, (MAP_GROUP(MAP_WIDE)<<8)|MAP_NUM(MAP_WIDE), 256, 257},
{65792, (MAP_GROUP(MAP_RETAINED)<<8)|MAP_NUM(MAP_RETAINED), 1, 1},
};
''').encode())
        probe = Probe(Source(root),layer,[dict(map='Wide')])
        self.addCleanup(probe.close)
        self.assertEqual(probe.metadata['gps_row_index_bytes'],4)
        self.assertEqual(probe.metadata['gps_run_end_bytes'],2)
        self.assertEqual(probe.lib.every_retired_cell(),0)
        self.assertEqual(probe.lib.all_clamps_and_invalid_coordinates(),0)
        self.assertEqual(probe.lib.legacy_bytes(),probe.metadata['legacy_data_bytes'])


@unittest.skipUnless(shutil.which('gcc') or shutil.which('cc'), 'Native host compiler required')
class Revision171LegacyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Path(__file__).resolve().parents[2]
        cls.source_path = cls.repo / '.local/generated-area-review-src'
        if not (cls.source_path/NAVIGATION_PATH).exists():
            raise unittest.SkipTest('Immutable revision171 source is not available locally')
        # Read and verify the full prepared171 contract, then stage only in
        # memory. Neither the source tree nor any ROM/ELF is modified.
        from candidate_layer import Layer
        from restore_generated_area_review import LAYERS, verify_prefix
        cls.parent = verify_prefix(cls.source_path, complete=True)
        inventory = json.loads((cls.repo/'docs/design/atlas-surf-layout/parent-inventory.json').read_bytes())
        cls.records = inventory['coasts']['retired_maps']
        cls.layer = Layer(cls.source_path,'atlas-legacy-test',LAYERS)
        cls.probe = Probe(Source(cls.source_path),cls.layer,cls.records)

    @classmethod
    def tearDownClass(cls):
        cls.probe.close()

    def test_all_actual_legacy_cells_and_65536_map_identities(self):
        self.assertEqual(self.probe.lib.every_retired_cell(),0)
        self.assertEqual(self.probe.lib.every_16_bit_id(),0)
        self.assertEqual(self.probe.lib.all_clamps_and_invalid_coordinates(),0)

    def test_every_preserved_grid_and_compiled_byte_budget(self):
        self.assertEqual(self.probe.lib.every_retained_grid(),0)
        metadata = self.probe.metadata
        self.assertEqual(self.probe.lib.legacy_bytes(),metadata['legacy_data_bytes'])
        self.assertEqual(self.probe.lib.original_bytes(),metadata['navigation_data_bytes_before'])
        self.assertEqual(self.probe.lib.active_bytes(),metadata['navigation_data_bytes_after'])
        self.assertGreater(metadata['data_bytes_freed'],0)
        # Every byte outside these two array initializers is preserved too,
        # including the older anchors/projections and all declarations.
        def outside_arrays(header):
            for name in ('sWorldNavigationPixels','sWorldTileGrids'):
                header = re.sub(r'(\b'+name+r'\s*\[\s*\]\s*=\s*\{).*?(\};)',
                                r'\1\2',header,flags=re.S)
            return header
        self.assertEqual(outside_arrays(self.probe.original),
                         outside_arrays(self.layer.outputs[NAVIGATION_PATH].decode()))

    def test_parent_contract_is_still_byte_identical(self):
        from restore_generated_area_review import verify_prefix
        self.assertEqual(self.parent,verify_prefix(self.source_path,complete=True))


if __name__ == '__main__':
    unittest.main()
