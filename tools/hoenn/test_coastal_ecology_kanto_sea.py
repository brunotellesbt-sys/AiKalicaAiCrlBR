"""Keep the marine aliases bounded to lower animated-water palette words."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from coastal_ecology_kanto_sea import EXPECTED_WORDS, FAMILIES, PRESERVED_FRESHWATER, TARGET_MAPS, repair
from coastal_ecology_ocean import normalize


class KantoSea(unittest.TestCase):
    def fixture(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        source=Path(temporary.name)
        def write(path,data):
            target=source/path;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data if isinstance(data,bytes) else data.encode())
        headers,definitions,aliases=[],[],[]
        for native,private in [('General_Frlg','JourneySeviiSea'),('SeviiIslands123','JourneySeviiSea123')]:
            for name in (native,private):
                headers.append('const struct Tileset gTileset_'+name+' = { .metatiles = gMeta_'+name+', .metatileAttributes = gAttributes, .callback = NativeAnimation, };')
                definitions.append('const u16 gMeta_'+name+'[] = INCBIN_U16("'+name+'.bin");')
                write(name+'.bin',struct.pack('<8H',0x41C6,0x41C7,0x41C7,0x41C6,0,0,0,0))
            aliases.append('    if (tileset == &gTileset_'+private+')\n        return &gTileset_'+native+';\n')
        for family in FAMILIES:
            headers.append('const struct Tileset gTileset_'+family+' = { .metatiles = gMeta_'+family+', .metatileAttributes = gAttributes, .callback = NativeAnimation, };')
            path='data/tilesets/'+family+'/metatiles.bin'
            definitions.append('const u16 gMeta_'+family+'[] = INCBIN_U16("'+path+'");')
            count=EXPECTED_WORDS[family];words=[]
            while count:
                n=min(count,4);words.extend([0x61C6]*n+[0x41C7]*(4-n)+[0x61C6]*4);count-=n
            write(path,struct.pack('<'+'H'*len(words),*words))
        write('src/data/tilesets/headers.h','\n'.join(headers))
        write('src/data/tilesets/metatiles.h','\n'.join(definitions))
        write('src/field_door.c','static const struct Tileset *JourneySeviiDoorTileset(const struct Tileset *tileset)\n{\n'+''.join(aliases)+'    return tileset;\n}\n')
        write('include/tilesets.h','#ifndef TILESETS_H\n#define TILESETS_H\n#endif\n')
        rows=[]
        for name in TARGET_MAPS+PRESERVED_FRESHWATER:
            family=('SeviiIslands123' if name=='NavelRock_Exterior_Frlg' else
                    'CinnabarIsland' if name.startswith(('Cinnabar','Route20')) else
                    'PalletTown' if name.startswith(('Pallet','Route21')) else
                    'VermilionCity' if name.startswith(('Vermilion','Route11')) else
                    'LavenderTown')
            path='data/layouts/'+name+'/map.bin'
            rows.append(dict(id=name,width=1,height=1,layout_version='frlg',
                primary_tileset='gTileset_General_Frlg',secondary_tileset='gTileset_'+family,
                blockdata_filepath=path))
            write(path,b'\x2b\x11')
            write('data/maps/'+name+'/map.json',json.dumps(dict(layout=name)))
        write('data/layouts/layouts.json',json.dumps(dict(layouts=rows)))
        class Layer:
            def __init__(self):
                self.source,self.outputs=source,{}
                self.expected={p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in source.rglob('*') if p.is_file()}
            def stage(self,path,data):self.outputs[path]=data.encode() if isinstance(data,str) else data
        return Layer()

    def test_native_object_upper_layers_and_nonwater_palettes_are_preserved(self):
        # Two complete metatiles: eligible lower water plus unchanged flips,
        # object layers, another water palette and adjacent non-water art.
        before=[0x61C6,0x65C7,0x69C6,0x6DC7,0x61C6,0x65C7,0x69C6,0x6DC7,
                0x41C6,0x41C7,0x61C5,0x61C8,0x6000,0x7000,0x8000,0x9000]
        packed=struct.pack('<16H',*before)
        after,changes=normalize(packed)
        words=struct.unpack('<16H',after)
        self.assertEqual(words[:4],tuple(w^0x2000 for w in before[:4]))
        self.assertEqual(words[4:],tuple(before[4:]))
        self.assertEqual([r['word_index'] for r in changes],[0,1,2,3])
        self.assertEqual(normalize(after),(after,[]))

    def test_marine_scope_excludes_native_freshwater_and_limits_private_tables(self):
        self.assertEqual(len(TARGET_MAPS),15)
        self.assertEqual(len(set(TARGET_MAPS)),15)
        self.assertTrue(set(TARGET_MAPS).isdisjoint(PRESERVED_FRESHWATER))
        self.assertIn('NavelRock_Exterior_Frlg',TARGET_MAPS)
        self.assertIn('VermilionCity_Frlg',TARGET_MAPS)
        self.assertEqual(set(EXPECTED_WORDS),set(FAMILIES))
        self.assertEqual(sum(EXPECTED_WORDS.values()),160)

    def test_replay_stages_nine_paths_and_preserves_every_native_input(self):
        layer=self.fixture();report=repair(layer)
        self.assertEqual(len(layer.outputs),9)
        self.assertEqual(report['lower_water_words_changed'],160)
        self.assertEqual(len(report['layout_assignments']),15)
        before=json.loads((layer.source/'data/layouts/layouts.json').read_text())
        after=json.loads(layer.outputs['data/layouts/layouts.json'])
        for old,new in zip(before['layouts'],after['layouts']):
            if old['id'] in PRESERVED_FRESHWATER:self.assertEqual(old,new)
            else:self.assertEqual(new['primary_tileset'],'gTileset_JourneySeviiSea')
        for path,expected in layer.expected.items():
            self.assertEqual(hashlib.sha256((layer.source/path).read_bytes()).hexdigest(),expected)

    def test_new_native_palette_usage_requires_review_before_any_output_is_staged(self):
        layer=self.fixture();path='data/tilesets/CinnabarIsland/metatiles.bin'
        words=bytearray((layer.source/path).read_bytes());struct.pack_into('<H',words,0,0x41C6)
        (layer.source/path).write_bytes(words);layer.expected[path]=hashlib.sha256(words).hexdigest()
        with self.assertRaises(AssertionError):repair(layer)
        self.assertEqual(layer.outputs,{})


if __name__=='__main__':unittest.main()
