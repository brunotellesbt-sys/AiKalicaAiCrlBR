"""Block only Pallet's wet cliff lip while composing with complete-tree fixes."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from coastal_ecology_pallet_shore import CELLS, MAP, repair


class PalletWetLip(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        source = Path(temporary.name)
        values = [0x3001] * 780
        for x, y, value in CELLS:
            values[y * 26 + x] = value
        values[25 * 26 + 18] = 0xF305
        files = {
            'data/layouts/layouts.json': json.dumps(dict(layouts=[dict(id='Pallet',
                width=26, height=30, layout_version='frlg', primary_tileset='gTileset_General_Frlg',
                secondary_tileset='gTileset_PalletTown', blockdata_filepath='data/layouts/Pallet/map.bin')])).encode(),
            f'data/maps/{MAP}/map.json': json.dumps(dict(layout='Pallet', object_events=[],
                warp_events=[], coord_events=[], bg_events=[])).encode(),
            'data/layouts/Pallet/map.bin': struct.pack('<780H', *values),
        }
        for name, raw in files.items():
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)

        class Layer:
            def __init__(self):
                self.source = source
                self.outputs = {}
                self.expected = {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()}

            def stage(self, path, raw):
                self.outputs[path] = raw

        return Layer()

    def test_only_eight_collision_bits_change_and_existing_tree_overlay_survives(self):
        layer = self.fixture()
        path = 'data/layouts/Pallet/map.bin'
        before = list(struct.unpack('<780H', (layer.source / path).read_bytes()))
        before[0] = 0x340E  # An independent previously staged complete-tree cell.
        layer.outputs[path] = struct.pack('<780H', *before)
        report = repair(layer)
        after = struct.unpack('<780H', layer.outputs[path])
        self.assertEqual(len(report['changed_cells']), 8)
        self.assertEqual(sum(a != b for a, b in zip(before, after)), 8)
        self.assertTrue(all(a == b or a ^ b == 0x400 for a, b in zip(before, after)))
        self.assertEqual(after[0], 0x340E)
        self.assertEqual(after[25 * 26 + 18], 0xF305)
        self.assertEqual(repair(layer)['changed_cells'], [])

    def test_refuses_a_different_height_instead_of_moving_the_shore(self):
        layer = self.fixture()
        path = 'data/layouts/Pallet/map.bin'
        raw = bytearray((layer.source / path).read_bytes())
        struct.pack_into('<H', raw, (17 * 26 + 15) * 2, 0x1302)
        (layer.source / path).write_bytes(raw)
        layer.expected[path] = hashlib.sha256(raw).hexdigest()
        with self.assertRaises(AssertionError):
            repair(layer)
        self.assertEqual(layer.outputs, {})

    def test_refuses_to_block_a_map_event(self):
        layer = self.fixture()
        path = f'data/maps/{MAP}/map.json'
        mapping = json.loads((layer.source / path).read_text())
        mapping['coord_events'] = [dict(x=15, y=17)]
        raw = json.dumps(mapping).encode()
        (layer.source / path).write_bytes(raw)
        layer.expected[path] = hashlib.sha256(raw).hexdigest()
        with self.assertRaises(AssertionError):
            repair(layer)
        self.assertEqual(layer.outputs, {})


if __name__ == '__main__':
    unittest.main()
