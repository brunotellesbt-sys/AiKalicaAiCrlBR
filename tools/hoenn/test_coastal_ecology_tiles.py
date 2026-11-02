"""Protect complete pine replacements and existing movement/event footprints."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from coastal_ecology_tiles import ANCHORS, BROKEN, COMPLETE, repair


class TreeRepair(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        source = Path(temporary.name)
        def write(name, raw):
            target = source/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        layouts = []
        for name, width, height in [('PalletTown_Frlg',26,30),('ViridianCity_Frlg',16,26)]:
            path = f'data/layouts/{name}/map.bin'
            layouts.append(dict(id=name,width=width,height=height,
                                primary_tileset='gTileset_General_Frlg',blockdata_filepath=path))
            values = [0x3001]*(width*height)
            for x,y in ANCHORS if name.startswith('Pallet') else [(12,23)]:
                for i,mid in enumerate(BROKEN if name.startswith('Pallet') else COMPLETE):
                    values[(y+i//2)*width+x+i%2] = 0x3400|mid
            write(path,struct.pack('<'+'H'*len(values),*values))
            write(f'data/maps/{name}/map.json',json.dumps(dict(layout=name,
                object_events=[],warp_events=[],coord_events=[],bg_events=[])).encode())
        write('data/layouts/layouts.json',json.dumps(dict(layouts=layouts)).encode())
        class Layer:
            def __init__(self):
                self.source=source
                self.outputs={}
                self.expected={p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in source.rglob('*') if p.is_file()}
            def stage(self,path,raw):
                self.outputs[path]=raw
        return Layer()

    def test_reconstructs_full_objects_and_preserves_all_physical_bits(self):
        layer=self.fixture()
        report=repair(layer)
        self.assertEqual(set(layer.outputs),{'data/layouts/PalletTown_Frlg/map.bin'})
        self.assertEqual(len(report['trees']),30)
        self.assertEqual(len(report['changed_cells']),60)
        before=struct.unpack('<780H',(layer.source/report['file']).read_bytes())
        after=struct.unpack('<780H',layer.outputs[report['file']])
        self.assertTrue(all(a&~1023==b&~1023 for a,b in zip(before,after)))
        footprint={(x+dx,y+dy) for x,y in ANCHORS for dy in range(3) for dx in range(2)}
        self.assertTrue(all(a==b for i,(a,b) in enumerate(zip(before,after)) if (i%26,i//26) not in footprint))
        for row in report['trees']:
            self.assertEqual(tuple(value&1023 for value in row['after']),COMPLETE)
        self.assertEqual(repair(layer)['changed_cells'],[])

    def test_rejects_a_different_bank_instead_of_reusing_universal_ids(self):
        layer=self.fixture()
        path='data/layouts/layouts.json'
        body=json.loads((layer.source/path).read_text())
        body['layouts'][1]['primary_tileset']='gTileset_General'
        raw=json.dumps(body).encode()
        (layer.source/path).write_bytes(raw)
        layer.expected[path]=hashlib.sha256(raw).hexdigest()
        with self.assertRaises(AssertionError):
            repair(layer)
        self.assertEqual(layer.outputs,{})

    def test_refuses_to_overwrite_an_event_inside_the_tree_footprint(self):
        layer=self.fixture()
        path='data/maps/PalletTown_Frlg/map.json'
        body=json.loads((layer.source/path).read_text())
        body['warp_events']=[dict(x=24,y=1)]
        raw=json.dumps(body).encode()
        (layer.source/path).write_bytes(raw)
        layer.expected[path]=hashlib.sha256(raw).hexdigest()
        with self.assertRaises(AssertionError):
            repair(layer)
        self.assertEqual(layer.outputs,{})


if __name__=='__main__':
    unittest.main()
