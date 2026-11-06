"""Guard whole reef repairs against lost collision flags or broader edits."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from sevii_complete_scenery import (DIMENSIONS, EDGE_RESTORES, FOOTPRINTS, FOUR, KINDLE,
                                    LARGE, OBJECT_TARGETS, PARENT_MARKER, SMALL, repair)


class FixtureLayer:
    def __init__(self, source):
        self.source = Path(source)
        self.outputs, self.expected = {}, {}

    def input(self, path, raw):
        if isinstance(raw, str):
            raw = raw.encode()
        target = self.source/path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        self.expected[path] = hashlib.sha256(raw).hexdigest()

    def stage(self, path, raw):
        self.outputs[path] = raw.encode() if isinstance(raw, str) else raw


class CompleteSceneryTests(unittest.TestCase):
    def fixture(self, directory):
        layer = FixtureLayer(directory)
        layouts = []
        donor_rows = []
        for number, (name, (width, height)) in enumerate(DIMENSIONS.items()):
            footprints = FOOTPRINTS.get(name, [])
            path = f'data/layouts/{name}/map.bin'
            layouts.append(dict(id=name, width=width, height=height,
                                blockdata_filepath=path, layout_version='frlg',
                                primary_tileset='gTileset_JourneySeviiSea'))
            layer.input(f'data/maps/{name}/map.json', json.dumps(dict(layout=name,
                object_events=[dict(local_id=6, x=4, y=6)],
                connections=[dict(direction='left', offset=120, map='KEEP')],
                warp_events=[dict(dest_warp_id=3, x=7, y=4)])))
            # Non-object cells include cliff/building-like IDs and varied flags.
            words = [((i % 16) << 12) | ((i % 4) << 10) | (0x270+i % 12)
                     for i in range(width*height)]
            for x, y, expected in footprints:
                for q, mid in enumerate(expected):
                    index = (y+q//2)*width+x+q%2
                    words[index] = ((q+number+1) << 12) | ((q % 4) << 10) | mid
            if name == KINDLE:
                for q, mid in enumerate(LARGE):
                    words[(29+q//2)*width+21+q%2] = 0x400 | mid
            donors = []
            for x, y, mid in EDGE_RESTORES.get(name, []):
                words[y*width+x] = 0x1643
                donors.append(dict(tile=[x, y], before=0x1000 | mid, after=0x1643))
            if name == FOUR:
                for x, mid in [(28, 0x24C), (29, 0x24D)]:
                    words[39*width+x] = 0x1643
                    donors.append(dict(tile=[x, 39], before=0x1000 | mid, after=0x1643))
            donor_rows.append(dict(map=name, path=path, cells=donors))
            layer.input(path, struct.pack('<'+'H'*len(words), *words))
        layer.input('data/layouts/layouts.json', json.dumps(dict(layouts=layouts)))
        layer.input(PARENT_MARKER, json.dumps(dict(boundaries=dict(outer_water_changes=donor_rows))))
        return layer

    def run_repair(self, layer):
        marker_hash = hashlib.sha256((layer.source/PARENT_MARKER).read_bytes()).hexdigest()
        with patch('sevii_complete_scenery.PARENT_MARKER_SHA256', marker_hash), \
             patch('sevii_boundary_scenery_actor.repair', return_value={'actor_fixture': True}):
            return repair(layer)

    def test_finishes_entire_objects_and_preserves_collision_elevation_and_neighbors(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as directory:
            layer = self.fixture(directory)
            report = self.run_repair(layer)
            self.assertEqual(report['original_object_count'], 38)
            self.assertEqual(report['restored_native_edge_cells'], 70)
            self.assertEqual(report['changed_cells'], 147)
            self.assertEqual(report['permanent_scenery'], {'actor_fixture': True})
            self.assertEqual(len(layer.outputs), 7)
            for name, (width, height) in DIMENSIONS.items():
                footprints = FOOTPRINTS.get(name, [])
                path = f'data/layouts/{name}/map.bin'
                before = struct.unpack('<'+'H'*(width*height), (layer.source/path).read_bytes())
                after = struct.unpack('<'+'H'*(width*height), layer.outputs[path])
                targets = {(y+q//2)*width+x+q%2: OBJECT_TARGETS.get((name, x, y), (SMALL,)*4)[q]
                           for x, y, _ in footprints for q in range(4)}
                targets.update({y*width+x: mid for x, y, mid in EDGE_RESTORES.get(name, [])})
                for index, (old, new) in enumerate(zip(before, after)):
                    self.assertEqual(old & ~1023, new & ~1023)
                    if index in targets:
                        self.assertEqual(new & 1023, targets[index])
                    else:
                        self.assertEqual(old, new)
            self.assertFalse(any('/maps/' in path for path in layer.outputs))

    def test_unreviewed_pattern_aborts_before_staging_either_map(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as directory:
            layer = self.fixture(directory)
            name = list(FOOTPRINTS)[-1]
            path = f'data/layouts/{name}/map.bin'
            width, height = DIMENSIONS[name]
            words = list(struct.unpack('<'+'H'*(width*height), (layer.source/path).read_bytes()))
            words[11*width] = (words[11*width] & ~1023) | 0x274
            layer.input(path, struct.pack('<'+'H'*len(words), *words))
            with self.assertRaisesRegex(AssertionError, 'Reviewed reef footprint changed'):
                self.run_repair(layer)
            self.assertEqual(layer.outputs, {})

    def test_restore_rejects_an_unreviewed_native_donor(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as directory:
            layer = self.fixture(directory)
            marker = json.loads((layer.source/PARENT_MARKER).read_bytes())
            marker['boundaries']['outer_water_changes'][0]['cells'][0]['before'] = 0x1274
            layer.input(PARENT_MARKER, json.dumps(marker))
            with self.assertRaisesRegex(AssertionError, 'Unreviewed shoreline donor'):
                self.run_repair(layer)
            self.assertEqual(layer.outputs, {})

    def test_rejects_a_donor_marker_with_the_wrong_identity(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as directory:
            layer = self.fixture(directory)
            with self.assertRaisesRegex(AssertionError, 'Scenery donor marker changed'):
                repair(layer)
            self.assertEqual(layer.outputs, {})


if __name__ == '__main__':
    unittest.main()
