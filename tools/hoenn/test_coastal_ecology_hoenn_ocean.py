"""Reject real Hoenn palette seams without treating native phases as new art."""
import json
from pathlib import Path
import struct
import tempfile
import unittest

from coastal_ecology_hoenn_ocean import source_census


class NativeHoennWaterCensus(unittest.TestCase):
    def fixture(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        source = Path(directory.name)
        def write(path, value):
            target = source/path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(value if isinstance(value, bytes) else value.encode())
        write('src/data/tilesets/headers.h', '\n'.join(
            'const struct Tileset gTileset_'+bank+' = { .metatiles = gMeta_'+bank+', };'
            for bank in ('General','Mossdeep')))
        write('src/data/tilesets/metatiles.h', '\n'.join(
            'const u16 gMeta_'+bank+'[] = INCBIN_U16("'+bank+'.bin");'
            for bank in ('General','Mossdeep')))
        # Palette6 in upper object pieces is unrelated to the sea underlay.
        write('General.bin', struct.pack('<8H',0x41C6,0x41C7,0,0,0x61C6,0,0,0))
        write('Mossdeep.bin', struct.pack('<8H',0x41C7,0x41C6,0,0,0x61C7,0,0,0))
        layout = dict(id='MOSSDEEP',primary_tileset='gTileset_General',
                      secondary_tileset='gTileset_Mossdeep',blockdata_filepath='map.bin')
        write('data/layouts/layouts.json',json.dumps(dict(layouts=[layout])))
        write('data/maps/MossdeepCity/map.json',json.dumps(dict(layout='MOSSDEEP',map_type='MAP_TYPE_CITY')))
        write('map.bin',struct.pack('<2H',0x1000,0x1200))
        return source

    def test_actual_used_primary_and_secondary_water_match(self):
        result = source_census(self.fixture())
        self.assertEqual(result['map_count'],1)
        self.assertEqual({row['bank'] for row in result['water_banks']},
                         {'gTileset_General','gTileset_Mossdeep'})
        self.assertTrue(result['all_referenced_hoenn_ocean_words_use_palette4'])

    def test_lower_water_palette_seam_is_rejected(self):
        source = self.fixture()
        words = list(struct.unpack('<8H',(source/'Mossdeep.bin').read_bytes()))
        words[1] = 0x61C6
        (source/'Mossdeep.bin').write_bytes(struct.pack('<8H',*words))
        with self.assertRaisesRegex(AssertionError,'Hoenn ocean palette differs'):
            source_census(source)

    def test_unused_secondary_water_is_not_reported_as_visible(self):
        source = self.fixture()
        (source/'map.bin').write_bytes(struct.pack('<H',0x1000))
        result = source_census(source)
        self.assertEqual([row['bank'] for row in result['water_banks']],['gTileset_General'])


if __name__=='__main__':
    unittest.main()
