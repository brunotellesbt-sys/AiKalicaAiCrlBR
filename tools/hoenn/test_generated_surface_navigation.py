"""Regression checks for signed native surface connection geometry."""
import json
from pathlib import Path
import tempfile
import unittest
import struct

from validate_generated_surface_navigation import edge_pairs, middle_run, merge_reports, place_fixture


class SurfaceConnectionGeometry(unittest.TestCase):
    def test_high_coordinate_fixture_uses_s16_event_and_restores_empty_event_table(self):
        memory = {}
        class Lib:
            def read8(self, at): return memory.get(at, 255)
            def read32(self, at): return int.from_bytes(bytes(self.read8(at+i) for i in range(4)), 'little')
            def raw8(self, at, value): memory[at] = value
        lib = Lib()
        for i, value in enumerate(struct.pack('<I', 0x2000)): lib.raw8(0x1004+i,value)
        lib.raw8(0x2001,0)
        seen = []
        def script(code,frames):
            self.assertEqual(lib.read8(0x2001),1)
            at=lib.read32(0x2008)
            seen.append(struct.unpack('<hhBBBB',bytes(lib.read8(at+i) for i in range(8))))
        ns=dict(lib=lib,s={},native=lambda *args:0x1000,map_id=lambda name:(3,4),
                FIXTURE_ROM_BASE=0x9000000,script=script)
        before={at:lib.read8(at) for at in [0x2001,*range(0x2008,0x200c),*range(0x9000180,0x9000188)]}
        self.assertTrue(place_fixture(ns,'large',143,133))
        self.assertEqual(seen,[(143,133,0,255,0,0)])
        self.assertEqual(before,{at:lib.read8(at) for at in before})
        def broken_script(*args,**kwargs): raise RuntimeError('fixture failure')
        ns['script']=broken_script
        with self.assertRaises(RuntimeError):place_fixture(ns,'large',143,133)
        self.assertEqual(before,{at:lib.read8(at) for at in before})

    def test_negative_horizontal_offset_maps_the_overlap_not_the_map_origin(self):
        pairs = edge_pairs('right', -3, 8, 6, 5, 7)
        self.assertEqual(pairs, [((7,y),(0,y+3)) for y in range(4)])
        reverse = edge_pairs('left', 3, 5, 7, 8, 6)
        self.assertEqual(pairs, [(q,p) for p,q in reverse])

    def test_positive_vertical_offset_is_reversible(self):
        pairs = edge_pairs('down', 4, 10, 8, 7, 5)
        self.assertEqual(pairs, [((x,7),(x-4,0)) for x in range(4,10)])
        self.assertEqual(pairs, [(q,p) for p,q in edge_pairs('up', -4, 7,5,10,8)])

    def test_disjoint_edges_have_no_synthetic_passage(self):
        self.assertEqual(edge_pairs('right', 8,4,5,4,3), [])
        self.assertEqual(edge_pairs('down', -10,4,5,4,3), [])

    def test_middle_of_largest_contiguous_open_span(self):
        pairs=[((8,y),(0,y)) for y in [0,1,5,6,7,8,9]]
        self.assertEqual(middle_run(pairs), ((8,7),(0,7)))
        self.assertIsNone(middle_run([]))

    def test_native_shards_cannot_claim_other_rom_or_missing_cases(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            blueprint=[dict(source='A',destination='B',mode='surf'),dict(source='B',destination='A',mode='walk')]
            base=dict(rom_sha256='rom-one',planned_native_cases=blueprint,graph_passed=True)
            a=base|dict(native_cases=[dict(index=0,**blueprint[0],passed=True)])
            b=base|dict(native_cases=[dict(index=1,**blueprint[1],passed=True)])
            for name,value in [('a',a),('b',b)]: (root/name).write_text(json.dumps(value))
            with self.assertRaisesRegex(AssertionError,'Incomplete'):
                merge_reports([root/'a'],root/'out')
            with self.assertRaisesRegex(AssertionError,'Duplicate'):
                merge_reports([root/'a',root/'a'],root/'out')
            self.assertTrue(merge_reports([root/'a',root/'b'],root/'out')['passed'])
            b['rom_sha256']='rom-two';(root/'b').write_text(json.dumps(b))
            with self.assertRaisesRegex(AssertionError,'different ROMs'):
                merge_reports([root/'a',root/'b'],root/'out')


if __name__ == '__main__':
    unittest.main()
