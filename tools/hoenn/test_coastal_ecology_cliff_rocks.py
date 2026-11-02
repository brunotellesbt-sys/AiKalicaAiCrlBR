"""Complete clipped cliff-foot objects without closing existing Surf lanes."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from coastal_ecology_cliff_rocks import (
    ANCHORS, BROKEN, COMPLETE, DONOR_ANCHORS, DONOR_MAP, FINISHED, repair)
from audit_coastal_complete_objects import audit


class CliffFeet(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        source = Path(temporary.name)

        def write(path, raw):
            target = source / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)

        layouts = []
        for name, anchors in {**ANCHORS, DONOR_MAP: DONOR_ANCHORS}.items():
            width = max(x for x, _ in anchors) + 3
            height = max(y for _, y in anchors) + 3
            path = f'data/layouts/{name}/map.bin'
            layouts.append(dict(id=name, width=width, height=height,
                                layout_version='frlg', primary_tileset='gTileset_General_Frlg',
                                blockdata_filepath=path))
            values = [0x112B] * (width * height)
            for x, y in anchors:
                for i, mid in enumerate(COMPLETE if name == DONOR_MAP else BROKEN):
                    # Exercise different elevation/collision bits on each
                    # quadrant; all must survive the graphical correction.
                    values[(y + i // 2) * width + x + i % 2] = ((i + 1) << 12) | ((i % 2) << 10) | mid
            if name == 'OneIsland_Frlg':
                values[16 * width + 8] = 0x1123
            write(path, struct.pack('<' + 'H' * len(values), *values))
            write(f'data/maps/{name}/map.json', json.dumps(dict(layout=name,
                object_events=[], warp_events=[], coord_events=[], bg_events=[])).encode())
        write('data/layouts/layouts.json', json.dumps(dict(layouts=layouts)).encode())

        class Layer:
            def __init__(self):
                self.source = source
                self.outputs = {}
                self.expected = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in source.rglob('*') if p.is_file()}

            def stage(self, path, raw):
                self.outputs[path] = raw

        return Layer()

    def test_removes_only_orphan_tops_preserving_physical_flags_and_complete_rocks(self):
        layer = self.fixture()
        report = repair(layer)
        self.assertEqual(report['replaced_top_cells'], 32)
        self.assertEqual(len(layer.outputs), 9)
        donor_path = f'data/layouts/{DONOR_MAP}/map.bin'
        self.assertNotIn(donor_path, layer.outputs)
        self.assertEqual(len(report['preserved_complete_native_rocks']), 2)
        for row in report['maps']:
            before = (layer.source / row['file']).read_bytes()
            after = layer.outputs[row['file']]
            first = struct.unpack('<' + 'H' * (len(before) // 2), before)
            final = struct.unpack('<' + 'H' * (len(after) // 2), after)
            self.assertTrue(all(a & ~1023 == b & ~1023 for a, b in zip(first, final)))
            self.assertTrue(all(a == b or (a & 1023, b & 1023) in ((0x108, 0x123), (0x109, 0x123))
                                for a, b in zip(first, final)))
        self.assertTrue(all(tuple(w & 1023 for w in row['after']) == FINISHED
                            for row in report['fragments']))
        self.assertEqual(repair(layer)['replaced_top_cells'], 0)

    def test_rejects_unexpected_native_rock_bottoms_instead_of_deleting_whole_objects(self):
        layer = self.fixture()
        path = 'data/layouts/OneIsland_Frlg/map.bin'
        raw = bytearray((layer.source / path).read_bytes())
        width = 18
        struct.pack_into('<H', raw, ((16 + 1) * width + 6) * 2, 0x0518)
        (layer.source / path).write_bytes(raw)
        layer.expected[path] = hashlib.sha256(raw).hexdigest()
        with self.assertRaises(AssertionError):
            repair(layer)
        self.assertEqual(layer.outputs, {})

    def test_refuses_to_replace_an_event_on_the_cliff_foot(self):
        layer = self.fixture()
        path = 'data/maps/OneIsland_Frlg/map.json'
        body = json.loads((layer.source / path).read_text())
        body['warp_events'] = [dict(x=6, y=16)]
        raw = json.dumps(body).encode()
        (layer.source / path).write_bytes(raw)
        layer.expected[path] = hashlib.sha256(raw).hexdigest()
        with self.assertRaises(AssertionError):
            repair(layer)
        self.assertEqual(layer.outputs, {})

    def test_object_census_finds_cut_cliff_rocks_and_preserves_the_native_variant(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source, upstream = base / 'source', base / 'upstream'
            path = 'data/layouts/Cliff/map.bin'
            mapping = dict(id='MAP_CLIFF', layout='Cliff', map_type='MAP_TYPE_ROUTE',
                           connections=[])
            layouts = dict(layouts=[dict(id='Cliff', width=2, height=2,
                primary_tileset='gTileset_General_Frlg', blockdata_filepath=path,
                border_filepath='data/layouts/Cliff/border.bin')])
            originals = {
                'data/layouts/layouts.json': json.dumps(layouts).encode(),
                'data/maps/Cliff/map.json': json.dumps(mapping).encode(),
                path: struct.pack('<4H', *COMPLETE),
                'data/layouts/Cliff/border.bin': bytes(8),
            }
            for root in (source, upstream):
                for name, raw in originals.items():
                    target = root / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(raw)
            (source / '.source-acquired.json').write_text(json.dumps(dict(commit='native',
                sha256={name: hashlib.sha256(raw).hexdigest() for name, raw in originals.items()})))
            (source / 'pokeemerald.gba').write_bytes(b'fixture')
            (source / path).write_bytes(struct.pack('<4H', *BROKEN))
            broken = audit(source, upstream)['boulders']
            self.assertEqual(len(broken['unresolved_patterns']), 1)
            self.assertEqual(broken['unresolved_patterns'][0]['anchor'], [0, 0])
            (source / path).write_bytes(struct.pack('<4H', *FINISHED))
            self.assertEqual(audit(source, upstream)['boulders']['unresolved_patterns'], [])
            (source / path).write_bytes(originals[path])
            complete = audit(source, upstream)['boulders']
            self.assertEqual(complete['unresolved_patterns'], [])
            self.assertEqual(len(complete['native_variant_art']), 1)


if __name__ == '__main__':
    unittest.main()
