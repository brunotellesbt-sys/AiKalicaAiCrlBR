"""Native enums, banks, disconnected pools, offsets and portal guards.

These small sources deliberately differ from the game's metatile IDs and
enum numbering. They catch a guessed parser or a universal-bank shortcut.
"""
import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from atlas_surf_source import Source
from atlas_surf_adapters import edge_pairs, inventory as adapter_inventory
from atlas_surf_coasts import stage_route114_closure
from atlas_surf_pois import _portal, current_ports
from test_atlas_surf_layer import Overlay


class NativeInventoryTests(unittest.TestCase):
    def fixture(self, maps=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        overlay = Overlay(root)
        specs = maps or {'Old': ('emerald', 3, 1, [0x1001, 0x1200, 0x1280]),
                         'Native': ('frlg', 3, 1, [0x1001, 0x1280, 0x1401])}
        overlay.parent('data/maps/map_groups.json', dict(group_order=['Group'], Group=list(specs)))
        layouts = []
        for name, (version, width, height, words) in specs.items():
            layouts.append(dict(id='LAYOUT_'+name, width=width, height=height,
                                layout_version=version, primary_tileset='Primary',
                                secondary_tileset='Secondary', blockdata_filepath=name+'.bin'))
            overlay.parent(name+'.bin', struct.pack('<'+'H'*len(words), *words))
            overlay.parent(f'data/maps/{name}/map.json', dict(id='MAP_'+name.upper(), layout='LAYOUT_'+name,
                           object_events=[], warp_events=[], coord_events=[], bg_events=[], connections=[]))
        overlay.parent('data/layouts/layouts.json', dict(layouts=layouts))
        overlay.parent('src/data/tilesets/headers.h',
                       b'const struct Tileset Primary = { .metatileAttributes = PrimaryAttrs };\n'
                       b'const struct Tileset Secondary = { .metatileAttributes = SecondaryAttrs };\n')
        # Same IDs have different meanings in the two banks. FRLG's cutoff
        # is 640, while Emerald's is 512; its attributes use 4 vs 2 bytes.
        overlay.parent('src/data/tilesets/metatiles.h',
                       b'const u16 PrimaryAttrs[] = INCBIN_U16("primary.bin");\n'
                       b'const u16 SecondaryAttrs[] = INCBIN_U16("secondary.bin");\n')
        primary = [0]*640
        primary[1] = 0x81
        secondary = [0]*384
        secondary[0] = 0x85
        overlay.parent('primary.bin', struct.pack('<640H', *primary))
        overlay.parent('secondary.bin', struct.pack('<384H', *secondary))
        overlay.parent('include/constants/metatile_behaviors.h',
                       b'enum { MB_LAND, MB_RESERVED = 0x80, MB_WATER, MB_OTHER = 0x84, MB_FISH, MB_COUNT };\n')
        overlay.parent('src/metatile_behavior.c',
                       b'#define TILE_FLAG_SURFABLE (1 << 2)\n'
                       b'#define TILE_FLAG_HAS_ENCOUNTERS (1 << 5)\n'
                       b'static const u8 sTileBitAttributes[MB_COUNT] = {\n'
                       b' [MB_WATER] = TILE_FLAG_SURFABLE,\n'
                       b' [MB_FISH] = TILE_FLAG_SURFABLE | TILE_FLAG_HAS_ENCOUNTERS,\n};\n')
        return root, overlay

    def test_implicit_enum_values_flags_and_bank_cutoffs(self):
        root, _ = self.fixture()
        source = Source(root)
        self.assertEqual(source.behavior_flags['values'][0x81], 4)
        self.assertEqual(source.behavior_flags['values'][0x85], 36)
        self.assertEqual([source.water('Old', x, 0) for x in range(3)], [True, True, False])
        # Change only the FRLG attribute files: the source must interpret
        # the native width and bank split instead of borrowing Emerald's.
        primary, secondary = [0]*640, [0]*384
        primary[1], secondary[0] = 0x81, 0x85
        (root/'primary.bin').write_bytes(struct.pack('<640I', *primary))
        (root/'secondary.bin').write_bytes(struct.pack('<384I', *secondary))
        source = Source(root)
        self.assertEqual([source.water('Native', x, 0) for x in range(3)], [True, True, False])

    def test_height_components_and_blocked_water_remain_distinct(self):
        root, _ = self.fixture({'Old': ('emerald', 5, 1, [0x1001, 0x3001, 0x0001, 0x1001, 0x1C01])})
        source = Source(root)
        labels, components = source.water_components('Old')
        self.assertNotEqual(labels[0, 0], labels[1, 0])
        self.assertEqual(labels[1, 0], labels[3, 0])
        self.assertNotIn((4, 0), labels)
        self.assertEqual(sorted(map(len, components)), [1, 3])

    def test_source_mutation_and_unsafe_paths_fail_closed(self):
        root, _ = self.fixture()
        source = Source(root)
        source.words('Old')
        (root/'Old.bin').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'changed while planning'):
            source.assert_unchanged()
        for path in ('../Old.bin', '/etc/passwd', 'data\\map.json'):
            with self.assertRaisesRegex(ValueError, 'Unsafe source path'):
                source.read(path)

    def test_missing_behavior_initializer_does_not_become_empty_table(self):
        root, _ = self.fixture()
        (root/'src/metatile_behavior.c').write_text('#define TILE_FLAG_SURFABLE 4\n')
        with self.assertRaisesRegex(ValueError, 'initializer missing'):
            _ = Source(root).behavior_flags

    def test_offset_pairs_keep_height_mismatch_for_review(self):
        root, _ = self.fixture({'Old': ('emerald', 2, 4, [0x1001]*8),
                                'Native': ('emerald', 2, 3, [0x3001]*6)})
        source = Source(root)
        interface = dict(retired_map='Old', native_map='Native', direction='right', offset=2,
                         reciprocal=True)
        pairs = list(edge_pairs(source, interface))
        self.assertEqual([row['native_tile'] for row in pairs], [[0, 0], [0, 1]])
        self.assertEqual([row['retired_tile'] for row in pairs], [[1, 2], [1, 3]])
        self.assertFalse(any(row['height_compatible'] for row in pairs))
        report = adapter_inventory(source, dict(native_interfaces=[interface]))
        self.assertEqual(len(report['adapters']), 1)
        self.assertEqual(report['currently_height_compatible_components'], 0)
        self.assertTrue(report['adapters'][0]['boundary_height_review_required'])
        interface['offset'] = -1
        self.assertEqual([r['native_tile'] for r in edge_pairs(source, interface)], [[0, 1], [0, 2]])

    def test_unreciprocated_wet_interface_is_rejected(self):
        root, _ = self.fixture({'Old': ('emerald', 1, 1, [0x1001]),
                                'Native': ('emerald', 1, 1, [0x1001])})
        interface = dict(retired_map='Old', native_map='Native', direction='right', offset=0,
                         reciprocal=False)
        with self.assertRaisesRegex(ValueError, 'Unreciprocated wet coast'):
            adapter_inventory(Source(root), dict(native_interfaces=[interface]))

    def test_portal_uses_actual_height_zero_and_rejects_missing_return(self):
        root, overlay = self.fixture({'Old': ('emerald', 1, 1, [0x3000]),
                                     'Cave': ('emerald', 1, 1, [0x0000])})
        for name, target in [('Old', 'Cave'), ('Cave', 'Old')]:
            path = f'data/maps/{name}/map.json'
            mapping = json.loads((root/path).read_bytes())
            mapping['warp_events'] = [dict(x=0, y=0, elevation=0, dest_map='MAP_'+target.upper(), dest_warp_id=0)]
            overlay.parent(path, mapping)
        source = Source(root)
        anchors = {'Cave': dict(atlas=[9, 7])}
        portal = _portal(source, 'Old', 0, 'Cave', 0, anchors)
        self.assertEqual(portal['interior_warp_tile']['height'], 0)
        self.assertEqual(portal['fixed_atlas'], [9, 7])
        source.maps['Cave']['warp_events'][0]['dest_warp_id'] = 1
        with self.assertRaisesRegex(ValueError, 'reciprocal'):
            _portal(source, 'Old', 0, 'Cave', 0, anchors)

    def test_route114_closure_preserves_every_other_cell_and_events(self):
        root, layer = self.fixture({'Route114': ('emerald', 2, 20, [0x1170]*40)})
        layouts = json.loads((root/'data/layouts/layouts.json').read_bytes())
        layouts['layouts'][0]['primary_tileset'] = 'gTileset_General'
        layer.parent('data/layouts/layouts.json', layouts)
        before = {p: hashlib.sha256((root/p).read_bytes()).hexdigest() for p in layer.expected}
        report = stage_route114_closure(layer)
        self.assertEqual(set(layer.outputs), {'Route114.bin'})
        original = struct.unpack('<40H', (root/'Route114.bin').read_bytes())
        result = struct.unpack('<40H', layer.outputs['Route114.bin'])
        self.assertEqual([i for i, pair in enumerate(zip(original, result)) if pair[0] != pair[1]], [34, 36])
        self.assertEqual(result[34], 0x15F9)
        self.assertEqual(result[32:34], original[32:34])
        self.assertFalse(report['native_validated'])
        self.assertEqual(before, {p: hashlib.sha256((root/p).read_bytes()).hexdigest() for p in layer.expected})
        # A modified mouth cannot be silently accepted as a known baseline.
        layer.outputs.clear()
        layer.parent('Route114.bin', struct.pack('<40H', *([0x15F9]*40)))
        with self.assertRaisesRegex(ValueError, 'expected native water'):
            stage_route114_closure(layer)

    def test_port_metadata_translation_is_once_and_does_not_mutate_parent(self):
        name = 'OneIsland_TreasureBeach_Frlg'
        root, overlay = self.fixture({name: ('emerald', 11, 1, [0x1C00]*9+[0x3000, 0x1001])})
        port = dict(island='One', town='OneIsland', interior='Terminal', map=name,
                    boarding=dict(dry=[name, 1, 0], water=[name, 2, 0]))
        overlay.parent('.journey-sevii-integrated-piers', dict(harbors=dict(ports=[port])))
        overlay.parent('.journey-sevii-route-boundaries',
                       dict(boundaries=dict(approach=dict(map=name, original_terrain_offset=[8, 0]))))
        original = copy.deepcopy(port)
        source = Source(root)
        for _ in range(2):
            record = current_ports(source)[0]
            self.assertEqual(record['boarding']['dry'], [name, 9, 0])
            self.assertEqual(record['boarding']['water'], [name, 10, 0])
            self.assertFalse(record['current_ferry_arrivals_repointed'])
        self.assertEqual(source.js('.journey-sevii-integrated-piers')['harbors']['ports'][0], original)
        source.assert_unchanged()


if __name__ == '__main__':
    unittest.main()
