"""The video cape closes as a complete object across the real map seam."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from coastal_ecology_kindle_cliff import CHANGES, ROAD, TOWN, TREASURE, repair


class KindleCliff(unittest.TestCase):
    def fixture(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        source = Path(temp.name)
        def write(path, data):
            target = source/path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        layouts = []
        for name, cells in CHANGES.items():
            height = {TOWN:20, ROAD:140, TREASURE:40}[name]
            path = f'data/layouts/{name}/map.bin'
            layouts.append(dict(id=name,width=24,height=height,
                layout_version='frlg',blockdata_filepath=path))
            words = [0x0471]*(24*height)
            for x,y,before,_ in cells: words[y*24+x] = before
            write(path,struct.pack('<'+'H'*len(words),*words))
            write(f'data/maps/{name}/map.json',json.dumps(dict(layout=name)).encode())
        write('data/layouts/layouts.json',json.dumps(dict(layouts=layouts)).encode())
        class Layer:
            def __init__(self):
                self.source,self.outputs=source,{}
                self.expected={p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in source.rglob('*') if p.is_file()}
            def stage(self,path,data): self.outputs[path]=data
        return Layer()

    def test_closes_both_corners_face_and_water_toe_without_other_edits(self):
        layer=self.fixture()
        report=repair(layer)
        self.assertEqual(report['changed_cells'],26)
        self.assertEqual(len(layer.outputs),3)
        for name,cells in CHANGES.items():
            path=f'data/layouts/{name}/map.bin'
            before=(layer.source/path).read_bytes()
            after=layer.outputs[path]
            actual={i//2 for i in range(0,len(before),2) if before[i:i+2]!=after[i:i+2]}
            self.assertEqual(actual,{y*24+x for x,y,_,_ in cells})
            words=struct.unpack('<'+'H'*(len(after)//2),after)
            for x,y,_,expected in cells:self.assertEqual(words[y*24+x],expected)
        road=struct.unpack('<3360H',layer.outputs[f'data/layouts/{ROAD}/map.bin'])
        self.assertTrue(all(road[139*24+x]>>12==1 for x in range(8)))
        self.assertTrue(all(road[138*24+x]&0x400 for x in range(7)))

    def test_rejects_changed_input_before_staging_either_half(self):
        layer=self.fixture()
        path=f'data/layouts/{ROAD}/map.bin'
        data=bytearray((layer.source/path).read_bytes())
        struct.pack_into('<H',data,(138*24+6)*2,0x0471)
        (layer.source/path).write_bytes(data)
        layer.expected[path]=hashlib.sha256(data).hexdigest()
        with self.assertRaisesRegex(AssertionError,'Unreviewed Kindle cape input'):
            repair(layer)
        self.assertEqual(layer.outputs,{})


if __name__=='__main__':unittest.main()
