"""Negative controls for complete objects, seam deduplication and Surf clearance."""
import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path

from generated_world_marine import repair


class RecordingLayer:
    def __init__(self, source):
        self.source = source
        self.outputs = {}
        self.expected = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in source.rglob('*') if p.is_file()}

    def stage(self, path, raw):
        self.outputs[path] = raw


class MarineCompleteObjects(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.source = Path(self.directory.name)
        self.layouts = []
        self.values = {}
        self.add_map('ThreeIsland_Frlg', 24, 24)
        a = self.values['ThreeIsland_Frlg']
        for y, row in [(20, [0x041E, 0x041F] * 3),
                       (21, [0x0414, 0x0415, 0x0414, 0x0415, 0x0414, 0x0417]),
                       (22, [0x041C, 0x041D, 0x041C, 0x041D, 0x041C, 0x041F])]:
            a[y * 24:y * 24 + 6] = row
        self.add_map('SixIsland_Frlg', 24, 30)
        a = self.values['SixIsland_Frlg']
        a[3 * 24 + 2:3 * 24 + 4] = [0x300E, 0x300F]
        a[4 * 24 + 2:4 * 24 + 4] = [0x041E, 0x041F]
        self.add_map('VictoryRoad_B2F', 26, 16)
        a = self.values['VictoryRoad_B2F']
        a[14 * 26 + 23:14 * 26 + 25] = [0x0550, 0x0551]
        a[15 * 26 + 23:15 * 26 + 25] = [0x0558, 0x0559]

    def add_map(self, name, width, height, connections=None):
        layout = dict(id='LAYOUT_' + name, width=width, height=height,
                      primary_tileset='gTileset_General',
                      blockdata_filepath=f'data/layouts/{name}/map.bin')
        self.layouts.append(layout)
        self.values[name] = [0x3001] * (width * height)
        path = self.source / f'data/maps/{name}/map.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dict(id='MAP_' + name, layout=layout['id'],
                                       map_type='MAP_TYPE_OCEAN_ROUTE',
                                       connections=connections)))

    def run_repair(self):
        path = self.source / 'data/layouts/layouts.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dict(layouts=self.layouts)))
        for name, values in self.values.items():
            path = self.source / f'data/layouts/{name}/map.bin'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(struct.pack('<' + 'H' * len(values), *values))
        layer = RecordingLayer(self.source)
        result = repair(layer)
        return layer, result

    def test_split_object_is_repaired_once_with_exact_height_and_collision(self):
        self.add_map('RockLeft', 2, 4, [dict(direction='right', map='MAP_RockRight', offset=0)])
        self.add_map('RockRight', 2, 4, [dict(direction='left', map='MAP_RockLeft', offset=0)])
        self.values['RockLeft'][3] = 0x0550
        self.values['RockRight'][2] = 0x15F9
        self.values['RockLeft'][5] = 0x15F9
        self.values['RockRight'][4] = 0x0559
        layer, result = self.run_repair()
        self.assertEqual(len(result['rocks']), 1)
        rock = result['rocks'][0]
        self.assertEqual(rock['after'], [0x0550, 0x1551, 0x1558, 0x0559])
        self.assertTrue(all((a & ~1023) == (b & ~1023)
                            for a, b in zip(rock['before'], rock['after'])))
        self.assertIn('data/layouts/RockLeft/map.bin', layer.outputs)
        self.assertIn('data/layouts/RockRight/map.bin', layer.outputs)

    def test_tall_native_rock_is_not_mistaken_for_broken_two_by_two(self):
        self.add_map('SlateportCity', 4, 4)
        a = self.values['SlateportCity']
        a[0:2], a[4:6] = [0x0552, 0x0553], [0x0558, 0x0559]
        layer, result = self.run_repair()
        self.assertEqual(result['rocks'], [])
        self.assertNotIn('data/layouts/SlateportCity/map.bin', layer.outputs)

    def test_open_water_below_half_rock_remains_traversable(self):
        self.add_map('Route126', 80, 80)
        a = self.values['Route126']
        a[77 * 80 + 46:77 * 80 + 48] = [0x0550, 0x15F9]
        a[78 * 80 + 46:78 * 80 + 48] = [0x1170, 0x1170]
        _, result = self.run_repair()
        self.assertEqual(result['rocks'][0]['after'], [0x05F9, 0x15F9, 0x1170, 0x1170])

    def test_complete_tree_heads_leave_entry_and_lower_forest_untouched(self):
        _, result = self.run_repair()
        tree = result['forest']
        self.assertEqual(tree['after'][0:2], [[0x3001] * 6] * 2)
        self.assertEqual(tree['after'][2], [0x300E, 0x300F] * 3)
        self.assertEqual(tree['after'][3], [0x041E, 0x041F] * 3)
        self.assertEqual(tree['before'][4], tree['after'][4])


if __name__ == '__main__':
    unittest.main()
