"""Protect native underwater floors, full cave arches and return approaches."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from generated_world_underwater import NAMES, repair


class UnderwaterTerrain(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        source = Path(temporary.name)
        layouts = []
        def write(path, data):
            target = source/path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        for name in [*NAMES, 'Underwater_Route128']:
            width, height = (48, 30)
            values = [0x3254]*(width*height)
            if name == 'Underwater_Route128':
                for y, row in [(25,[0x0665,0x0666,0x0667]),(26,[0x066D,0x326E,0x066F])]:
                    values[y*width+37:y*width+40] = row
            else:
                for y in range(height):
                    for x in range(width):
                        if x in (0,width-1) or y in (0,height-1):
                            values[y*width+x] = 0x361E
                values[9*width+38] = 0x3666
                values[10*width+38] = 0x326E
            path = f'data/layouts/{name}/map.bin'
            layouts.append(dict(id=name,width=width,height=height,
                                primary_tileset='gTileset_General',
                                secondary_tileset='gTileset_Underwater',
                                blockdata_filepath=path))
            write(path, struct.pack('<'+'H'*len(values),*values))
            write(f'data/maps/{name}/map.json', json.dumps(dict(
                layout=name,map_type='MAP_TYPE_UNDERWATER',
                warp_events=[dict(x=38,y=10)])).encode())
        write('data/layouts/layouts.json', json.dumps(dict(layouts=layouts)).encode())
        attributes = [0x1000]*512
        write('data/tilesets/secondary/underwater/metatile_attributes.bin',
              struct.pack('<512H',*attributes))
        class Layer:
            def __init__(self):
                self.source = source
                self.outputs = {}
                self.expected = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in source.rglob('*') if p.is_file()}
            def stage(self,path,raw):
                self.outputs[path] = raw
        return Layer()

    def test_floor_art_preserves_behavior_and_entrance_has_all_six_pieces(self):
        layer = self.fixture()
        report = repair(layer)
        self.assertEqual(len(layer.outputs),5)
        for row in report['maps']:
            words = struct.unpack('<1440H', layer.outputs[f'data/layouts/{row["map"]}/map.bin'])
            self.assertEqual(words[5*48+5],0x3216)
            self.assertEqual(words[9*48+37:9*48+40],(0x3665,0x3666,0x3667))
            self.assertEqual(words[10*48+37:10*48+40],(0x366D,0x326E,0x366F))
            self.assertTrue(all(not words[11*48+x]&0xC00 for x in range(36,41)))
            self.assertTrue(all(word>>12==3 for word in words))

    def test_rejects_floor_with_a_different_gameplay_behavior(self):
        layer = self.fixture()
        path = 'data/tilesets/secondary/underwater/metatile_attributes.bin'
        raw = bytearray((layer.source/path).read_bytes())
        struct.pack_into('<H',raw,(0x216-512)*2,0x1012)
        (layer.source/path).write_bytes(raw)
        layer.expected[path] = hashlib.sha256(raw).hexdigest()
        with self.assertRaises(AssertionError):
            repair(layer)


if __name__ == '__main__':
    unittest.main()
