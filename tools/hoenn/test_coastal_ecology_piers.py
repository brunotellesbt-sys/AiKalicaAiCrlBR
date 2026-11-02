"""Keep the video regression bounded to water heights, with safe failure."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from coastal_ecology_piers import AFFECTED_MAP, EXPECTED_CELLS, repair
from integrated_sevii_harbors import CONFIG


class SafePierWater(unittest.TestCase):
    def fixture(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        source = Path(temp.name)
        def write(path, value):
            path = source/path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
        names = sorted({cfg['map'] for cfg in CONFIG.values()}
                       | {cfg['front_map'] for cfg in CONFIG.values() if 'front_map' in cfg})
        layouts = []
        for name in names:
            path = f'data/layouts/{name}/map.bin'
            layouts.append(dict(id=name, width=24, height=40, layout_version='frlg',
                                primary_tileset='gTileset_Primary', secondary_tileset='gTileset_Secondary',
                                blockdata_filepath=path))
            words = [0x3000]*(24*40)
            if name == AFFECTED_MAP:
                # Ocean, plus separate blocked water, dry transition floor and
                # multi-level tile which must never enter this repair's scope.
                words[200:200+EXPECTED_CELLS] = [0x001]*EXPECTED_CELLS
                words[100], words[101], words[102], words[103] = 0x0401, 0x0000, 0xF001, 0x1001
            write(path, struct.pack('<'+'H'*len(words), *words))
            write(f'data/maps/{name}/map.json', json.dumps(dict(id='MAP_'+name.upper(),layout=name)).encode())
        write('data/layouts/layouts.json', json.dumps(dict(layouts=layouts)).encode())
        write('src/data/tilesets/headers.h', b'''const struct Tileset gTileset_Primary = { .metatileAttributes = gAttrsPrimary, };
const struct Tileset gTileset_Secondary = { .metatileAttributes = gAttrsSecondary, };''')
        write('src/data/tilesets/metatiles.h', b'''const u32 gAttrsPrimary[] = INCBIN_U32("primary.bin");
const u32 gAttrsSecondary[] = INCBIN_U32("secondary.bin");''')
        write('primary.bin', struct.pack('<II',0,21))
        write('secondary.bin', struct.pack('<I',0))
        class Layer:
            def __init__(self):
                self.source=source
                self.outputs={}
                self.expected={p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in source.rglob('*') if p.is_file()}
            def stage(self,path,value):
                self.outputs[path]=value
        return Layer()

    def test_changes_only_the_65_open_water_elevations(self):
        layer=self.fixture()
        result=repair(layer)
        path=f'data/layouts/{AFFECTED_MAP}/map.bin'
        self.assertEqual(set(layer.outputs),{path})
        self.assertEqual(result['normalized_water_cells'],EXPECTED_CELLS)
        before=struct.unpack('<960H',(layer.source/path).read_bytes())
        after=struct.unpack('<960H',layer.outputs[path])
        self.assertEqual([i for i,(a,b) in enumerate(zip(before,after)) if a!=b],list(range(200,265)))
        self.assertTrue(all(a&0x0FFF==b&0x0FFF for a,b in zip(before,after)))
        self.assertTrue(all(after[i]==0x1001 for i in range(200,265)))
        self.assertEqual(after[100:104],before[100:104])
        self.assertEqual(repair(layer)['normalized_water_cells'],0)

    def test_rejects_unreviewed_transition_water_on_another_island(self):
        layer=self.fixture()
        path='data/layouts/TwoIsland_Frlg/map.bin'
        data=bytearray((layer.source/path).read_bytes())
        struct.pack_into('<H',data,0,1)
        layer.outputs[path]=bytes(data)
        with self.assertRaisesRegex(AssertionError,'Unexpected transition-height'):
            repair(layer)

    def test_rejects_a_different_patch_size_instead_of_silently_broadening_scope(self):
        layer=self.fixture()
        path=f'data/layouts/{AFFECTED_MAP}/map.bin'
        data=bytearray((layer.source/path).read_bytes())
        struct.pack_into('<H',data,200*2,0x1001)
        layer.outputs[path]=bytes(data)
        with self.assertRaises(AssertionError):
            repair(layer)


if __name__=='__main__':
    unittest.main()
