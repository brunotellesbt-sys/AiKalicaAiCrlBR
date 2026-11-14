"""Exercise emitted lookup C against an independent rectangle oracle.

These are host C tests, not claims of emulated-ROM performance or artwork.
"""
import ctypes
from copy import deepcopy
import json
from pathlib import Path
import random
import shutil
import subprocess
import tempfile
import unittest

from atlas_surf_runtime import bind_groups, render_runtime, stage


def fixture():
    # Nonuniform and signed rectangles exercise row-bin edges, skinny maps,
    # missing group slots, and maps crossing several 32-tile spatial rows.
    chunks = []
    for row in range(9):
        for col in range(13):
            i = len(chunks)
            chunks.append(dict(name=f'Sea{i}', id=f'MAP_SEA{i}', group_index=90 + i // 60,
                               group=f'Seas{i // 60}', number=(i % 60) + (2 if i // 60 else 0),
                               origin=[col * 39 - 51, row * 43 - 66],
                               width=5 + (i * 17) % 30, height=3 + (i * 11) % 35))
    chunks.append(dict(name='LongSea', id='MAP_LONG_SEA', group_index=95, group='LongSeas',
                       number=99, origin=[-130, -100], width=23, height=500))
    return dict(scale=8, chunks=chunks)


@unittest.skipUnless(shutil.which('gcc'), 'Host GCC is required for generated-C equivalence')
class GeneratedRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='atlas-runtime-test-')
        cls.path = Path(cls.temp.name)
        cls.plan = fixture()
        code, cls.metadata = render_runtime(cls.plan)
        (cls.path / 'runtime.h').write_text(code)
        (cls.path / 'probe.c').write_text('''
#include <stdint.h>
#include <stddef.h>
typedef uint8_t bool8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int16_t s16;
typedef int32_t s32;
#define TRUE 1
#define FALSE 0
#define ARRAY_COUNT(a) (sizeof(a)/sizeof((a)[0]))
#include "runtime.h"
int by_id(unsigned group, unsigned number) {
    const struct JourneyAtlasChunk *c = JourneyAtlasChunk(group, number);
    return c ? (int)(c - sAtlasChunks) : -1;
}
int at_world(int x, int y) {
    const struct JourneyAtlasChunk *c = JourneyAtlasWorldChunk(x, y);
    return c ? (int)(c - sAtlasChunks) : -1;
}
int position(unsigned group, unsigned number, short x, short y, unsigned short *out) {
    return JourneyAtlasPosition(group, number, x, y, out);
}
int group_present(unsigned group) { return JourneyAtlasGroup(group); }
int floor8(int value) { return JourneyAtlasFloor8(value); }
int floor32(int value) { return JourneyAtlasFloor32(value); }
''')
        subprocess.run(['gcc', '-std=gnu89', '-shared', '-fPIC', '-O2', '-Wall', '-Wextra', '-Werror',
                        str(cls.path / 'probe.c'), '-o', str(cls.path / 'runtime.so')], check=True,
                       capture_output=True, text=True)
        cls.lib = ctypes.CDLL(str(cls.path / 'runtime.so'))
        for name in ('by_id', 'at_world'):
            getattr(cls.lib, name).argtypes = [ctypes.c_int, ctypes.c_int]
            getattr(cls.lib, name).restype = ctypes.c_int
        cls.lib.position.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_int16, ctypes.c_int16,
                                     ctypes.POINTER(ctypes.c_uint16)]
        cls.lib.position.restype = ctypes.c_int
        cls.lib.group_present.argtypes = [ctypes.c_uint]
        for name in ('floor8', 'floor32'):
            getattr(cls.lib, name).argtypes = [ctypes.c_int32]
            getattr(cls.lib, name).restype = ctypes.c_int32

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_every_16_bit_map_id_matches_direct_oracle(self):
        expected = {(c['group_index'], c['number']): i for i, c in enumerate(self.plan['chunks'])}
        for group in range(256):
            for number in range(256):
                self.assertEqual(self.lib.by_id(group, number), expected.get((group, number), -1),
                                 (group, number))
        self.assertEqual(self.lib.by_id(65535, 0), -1)
        self.assertEqual(self.lib.by_id(90, 65535), -1)
        for group in range(256):
            self.assertEqual(bool(self.lib.group_present(group)),
                             any(c['group_index'] == group for c in self.plan['chunks']))

    def test_spatial_lookup_all_cells_and_outside_match_raster_oracle(self):
        # Build the expected answer independently from raw rectangle bounds;
        # none of the generator's row-index or search helpers are imported.
        oracle = {}
        for i, chunk in enumerate(self.plan['chunks']):
            x0, y0 = chunk['origin']
            for y in range(y0, y0 + chunk['height']):
                for x in range(x0, x0 + chunk['width']):
                    self.assertNotIn((x, y), oracle)
                    oracle[x, y] = i
        for y in range(-110, 412):
            for x in range(-140, 460):
                self.assertEqual(self.lib.at_world(x, y), oracle.get((x, y), -1), (x, y))
        for xy in [(-2**31, 0), (2**31 - 1, 0), (0, -2**31), (0, 2**31 - 1)]:
            self.assertEqual(self.lib.at_world(*xy), -1)

    def test_floor_is_mathematical_for_all_signed_16_bit_values(self):
        for value in range(-32768, 32768):
            self.assertEqual(self.lib.floor8(value), value // 8)
            self.assertEqual(self.lib.floor32(value), value // 32)
        for value in [-2**31, -2**31 + 1, 2**31 - 2, 2**31 - 1]:
            self.assertEqual(self.lib.floor8(value), value // 8)
            self.assertEqual(self.lib.floor32(value), value // 32)

    def test_position_has_no_perpendicular_drift_and_exact_scale(self):
        rng = random.Random(172)
        for chunk in self.plan['chunks']:
            for _ in range(20):
                x = rng.randrange(-3, chunk['width'] + 3)
                y = rng.randrange(-3, chunk['height'] + 3)
                for dx, dy in [(0, 0), (1, 0), (0, 1), (-1, 0), (0, -1),
                               (8, 0), (0, 8), (-8, 0), (0, -8)]:
                    px = (chunk['origin'][0] + x + dx) // 8
                    py = (chunk['origin'][1] + y + dy) // 8
                    result = ctypes.c_uint16(0xBEEF)
                    found = self.lib.position(chunk['group_index'], chunk['number'],
                                              x + dx, y + dy, ctypes.byref(result))
                    if 0 <= px <= 255 and 0 <= py <= 255:
                        self.assertTrue(found)
                        self.assertEqual(result.value, px | py << 8)
                    else:
                        self.assertFalse(found)
                        self.assertEqual(result.value, 0xBEEF)
        result = ctypes.c_uint16(0xBEEF)
        self.assertFalse(self.lib.position(0, 0, 1, 1, ctypes.byref(result)))
        self.assertEqual(result.value, 0xBEEF)

    def test_tables_are_compact_and_index_not_cell_sized(self):
        total_area = sum(c['width'] * c['height'] for c in self.plan['chunks'])
        self.assertLess(self.metadata['table_bytes'], total_area // 2)
        self.assertFalse(self.metadata['per_cell_gps_table'])
        self.assertEqual(self.metadata['spatial_row_tiles'], 32)
        self.assertLess(self.metadata['maximum_row_maps'], len(self.plan['chunks']) // 2)


class RuntimePlanValidationTests(unittest.TestCase):
    def test_bad_ids_and_ambiguous_rectangles_rejected(self):
        for change in [dict(number=100), dict(group_index=256), dict(width=0),
                       dict(origin=[32760, 0], width=20)]:
            plan = fixture()
            plan['chunks'][0].update(change)
            with self.assertRaises(ValueError):
                render_runtime(plan)
        plan = fixture()
        plan['chunks'][1]['group_index'] = plan['chunks'][0]['group_index']
        plan['chunks'][1]['number'] = plan['chunks'][0]['number']
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            render_runtime(plan)
        plan = fixture()
        plan['chunks'][1]['origin'] = plan['chunks'][0]['origin'][:]
        with self.assertRaisesRegex(ValueError, 'Overlapping'):
            render_runtime(plan)
        plan = fixture()
        plan['scale'] = 4
        with self.assertRaisesRegex(ValueError, 'eight'):
            render_runtime(plan)

    def test_named_groups_bind_to_actual_registry_and_slots(self):
        plan = dict(scale=8, chunks=[dict(name='SeaA', group='Atlas', number=0,
                                        origin=[800, 400], width=20, height=10)])
        groups = dict(group_order=['Native', 'Atlas'], Native=['Old'], Atlas=['SeaA'])
        bound = bind_groups(plan, groups)
        self.assertEqual(bound['chunks'][0]['group_index'], 1)
        self.assertNotIn('group_index', plan['chunks'][0])
        groups['Atlas'] = ['Other']
        with self.assertRaisesRegex(ValueError, 'disagrees'):
            bind_groups(plan, groups)

    def test_stage_preserves_native_fallback_and_movement_functions(self):
        plan = dict(scale=8, chunks=[dict(name='SeaA', group='Atlas', number=0,
                                        origin=[800, 400], width=20, height=10)])
        world = '''#include "global.h"
u16 JourneyWorldMapPosition(void)
{
    s16 x, y;
    x -= MAP_OFFSET; y -= MAP_OFFSET;
    return NativePosition(x, y);
}
'''
        movement = '''u16 MapGridGetCollisionAt(s16 x, s16 y) { return NativeCollision(x, y); }
u16 MapGridGetElevationAt(s16 x, s16 y) { return NativeHeight(x, y); }
u16 GetMapBorderIdAt(s16 x, s16 y) { return NativeBorder(x, y); }
'''
        field = '''#include "global.h"
static bool8 JourneyMarineViewGroup(u16 group)
{
    return LegacyGroup(group);
}
static bool8 JourneyMarineCornerMetatile(s32 x, s32 y, u16 *result)
{
    const struct MapHeader *current = &gMapHeader;
    if (!JourneyMarineViewMap(current) || current->connections == NULL)
        return FALSE;
    return LegacyDrawing(x, y, result);
}
''' + movement

        class FakeLayer:
            def __init__(self):
                self.outputs = {
                    'data/maps/map_groups.json': json.dumps(dict(
                        group_order=['Native', 'Atlas'], Native=['Old'], Atlas=['SeaA'])).encode(),
                    'src/journey_world_map.c': world.encode(), 'src/fieldmap.c': field.encode()}

            def stage(self, path, content):
                self.outputs[path] = content.encode() if isinstance(content, str) else content

        layer = FakeLayer()
        result = stage(layer, plan)
        actual_field = layer.outputs['src/fieldmap.c'].decode()
        actual_world = layer.outputs['src/journey_world_map.c'].decode()
        self.assertIn(movement, actual_field)
        self.assertIn('return LegacyDrawing(x, y, result);', actual_field)
        self.assertIn('return NativePosition(x, y);', actual_world)
        self.assertLess(actual_world.index('JourneyAtlasPosition('), actual_world.index('NativePosition('))
        self.assertIn('JourneyMarineViewCompatible(layout, layout->map[', actual_field)
        self.assertTrue(result['native_rom_validation_pending'])
        with self.assertRaisesRegex(ValueError, 'already installed'):
            stage(layer, plan)


if __name__ == '__main__':
    unittest.main()
