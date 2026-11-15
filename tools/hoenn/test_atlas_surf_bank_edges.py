"""Actual-helper tests for bank pointers, full attributes and both cameras."""
import ast
import hashlib
import inspect
import struct
import unittest

import atlas_surf_physical
from atlas_surf_bank_edges import Banks,CompiledMarineView,audit_edges,rgb555_palette
from sevii_boundary_camera import C_HELPERS


def physical_helper():
    tree=ast.parse(inspect.getsource(atlas_surf_physical.stage))
    return next(node.value.value for node in ast.walk(tree) if isinstance(node,ast.Assign)
                and any(isinstance(target,ast.Name) and target.id=='word' for target in node.targets))


class Fixture:
    def __init__(self):
        self.inputs={};self.identities={'A':10240,'B':10241,'LegacyA':3072,'LegacyB':3328}
        self.maps={name:dict(id='MAP_'+name.upper(),map_type='MAP_TYPE_OCEAN_ROUTE',connections=[])
                   for name in self.identities}
        self.maps['LegacyA']['id']='MAP_JOURNEYSURFLINK00000'
        self.maps['LegacyB']['id']='MAP_JOURNEYSURFLINK03002'
        self.maps['A']['connections']=[dict(map='MAP_B',direction='right',offset=0)]
        self.maps['B']['connections']=[dict(map='MAP_A',direction='left',offset=0)]
        self.by_id={r['id']:name for name,r in self.maps.items()}
        self.layouts={name:dict(width=2,height=2,primary_tileset='BankA',secondary_tileset='BankA',layout_version='frlg') for name in self.maps}
        self.layouts['B'].update(primary_tileset='BankB',secondary_tileset='BankB')
        self.words={name:[0x112B]*4 for name in self.maps}
        self.files={
            'src/fieldmap.c':(C_HELPERS+'\n'+physical_helper()+'''
u32 GetNumMetatilesInPrimary(const struct MapLayout *p){return p->isFrlg?NUM_METATILES_IN_PRIMARY_FRLG:NUM_METATILES_IN_PRIMARY;}
u32 GetNumPalsInPrimary(const struct MapLayout *p){return p->isFrlg?NUM_PALS_IN_PRIMARY_FRLG:NUM_PALS_IN_PRIMARY;}
''').encode(),
            'include/fieldmap.h':b'''#define NUM_METATILES_IN_PRIMARY_FRLG 640
#define NUM_METATILES_IN_PRIMARY 512
#define NUM_PALS_IN_PRIMARY_FRLG 7
#define NUM_PALS_IN_PRIMARY 6
#define NUM_TILES_PER_METATILE 8
''',
            'include/global.fieldmap.h':b'#define MAPGRID_METATILE_ID_MASK 0x3FF\n#define MAPGRID_COLLISION_MASK 0xC00\n',
            'include/constants/global.h':b'enum Connection {CONNECTION_INVALID=-1,CONNECTION_NONE,CONNECTION_SOUTH,CONNECTION_NORTH,CONNECTION_WEST,CONNECTION_EAST,CONNECTION_DIVE,CONNECTION_EMERGE};',
            'include/constants/map_types.h':b'enum MapType {MAP_TYPE_NONE,MAP_TYPE_TOWN,MAP_TYPE_CITY,MAP_TYPE_ROUTE,MAP_TYPE_OCEAN_ROUTE};',
            'src/tileset_anims.c':b'void AnimA(void){}\nvoid AnimB(void){}',
            'tilesA.png':b'same indexed graphics','tilesB.png':b'same indexed graphics',
            'attrsA.bin':bytes(1024*4),'attrsB.bin':bytes(1024*4),
            'metasA.bin':struct.pack('<'+('H'*8192),*([1]*8192)),
            'metasB.bin':struct.pack('<'+('H'*8192),*([1]*8192)),
        }
        self.files['src/data/tilesets/headers.h']='\n'.join(
            f'const struct Tileset Bank{key}={{.tiles=Tiles{key},.palettes=Pal{key},.metatiles=Metas{key},.metatileAttributes=Attrs{key},.callback=AnimA}};'
            for key in ('A','B')).encode()
        self.files['src/data/tilesets/metatiles.h']='\n'.join(
            f'const u16 Metas{k}[]=INCBIN_U16("metas{k}.bin");\nconst u16 Attrs{k}[]=INCBIN_U16("attrs{k}.bin");' for k in ('A','B')).encode()
        self.files['src/data/tilesets/graphics.h']=('''const u32 TilesA[]=INCBIN_U32("tilesA.4bpp.smol");
#define TilesB TilesA
'''+ '\n'.join(f'const u16 Pal{k}[][16]={{'+','.join(['0']*256)+'};' for k in ('A','B'))).encode()

    def read(self,path):
        if path not in self.files:raise FileNotFoundError(path)
        raw=self.files[path];digest=hashlib.sha256(raw).hexdigest()
        if path in self.inputs and self.inputs[path]!=digest:raise ValueError('Fixture changed during audit')
        self.inputs[path]=digest;return raw
    def layout(self,name):return self.layouts[name]
    def word(self,name,x,y):return self.words[name][y*2+x]
    def assert_unchanged(self):
        for name,value in self.inputs.items():assert hashlib.sha256(self.files[name]).hexdigest()==value


class BankEdgesTests(unittest.TestCase):
    def test_equal_pointer_alias_full_words_and_palettes_allow_both_cameras(self):
        source=Fixture();report=audit_edges(source,scope=['A','B'])
        self.assertEqual(report['authenticated_bank_pairs'],[['A','B'],['B','A']])
        self.assertEqual(report['unproven_edges'],[])
        self.assertTrue(report['actual_helpers_host_compiled'])

    def test_primary_general_assets_can_live_in_real_graphics_translation_unit(self):
        source=Fixture();line=b'const u32 TilesA[]=INCBIN_U32("tilesA.4bpp.smol");'
        source.files['src/data/tilesets/graphics.h']=source.files['src/data/tilesets/graphics.h'].replace(line,b'')
        source.files['src/graphics.c']=line
        report=audit_edges(source,scope=['A','B'])
        self.assertEqual(report['authenticated_bank_pairs'],[['A','B'],['B','A']])
        self.assertIn('src/graphics.c',report['input_sha256'])

    def test_equal_graphic_bytes_in_distinct_symbols_never_grant_pointer_identity(self):
        source=Fixture();source.files['src/data/tilesets/graphics.h']=source.files['src/data/tilesets/graphics.h'].replace(
            b'#define TilesB TilesA',b'const u32 TilesB[]=INCBIN_U32("tilesB.4bpp.smol");')
        report=audit_edges(source,scope=['A','B'])
        self.assertFalse(report['authenticated_bank_pairs'])
        failures=report['unproven_edges'][0]['failures']
        self.assertTrue(all(r['reason']=='tiles-pointer-symbols-differ' for r in failures))
        self.assertTrue(all(r['source_bytes_equal'] for r in failures))

    def test_high_attribute_bits_and_eighth_word_are_compared(self):
        for field,offset in [('attrsB.bin',299*4+3),('metasB.bin',299*16+14)]:
            source=Fixture();raw=bytearray(source.files[field]);raw[offset]=2;source.files[field]=bytes(raw)
            with self.subTest(field=field):
                report=audit_edges(source,scope=['A','B'])
                self.assertFalse(report['authenticated_bank_pairs'])
                self.assertIn('full-metatile-attributes-differ' if field.startswith('attrs') else 'eight-metatile-words-differ',
                              report['summary']['face_failure_reasons'])

    def test_callback_pointer_difference_is_rejected(self):
        source=Fixture();source.files['src/data/tilesets/headers.h']=source.files['src/data/tilesets/headers.h'].replace(
            b'.metatileAttributes=AttrsB,.callback=AnimA',b'.metatileAttributes=AttrsB,.callback=AnimB')
        result=CompiledMarineView(source).check('A','B',0x112B)
        self.assertFalse(result['compatible']);self.assertEqual(result['reason'],'animation-callback-pointers-differ')

    def test_rgb555_quantization_not_rgb24(self):
        def palette(red):return ('JASC-PAL\n0100\n16\n'+(f'{red} 0 0\n'*16)).encode()
        self.assertEqual(rgb555_palette(palette(0)),rgb555_palette(palette(7)))
        self.assertNotEqual(rgb555_palette(palette(0)),rgb555_palette(palette(8)))
        source=Fixture();source.files['src/data/tilesets/graphics.h']=source.files['src/data/tilesets/graphics.h'].replace(
            b'const u16 PalB[][16]={0,',b'const u16 PalB[][16]={1,')
        result=CompiledMarineView(source).check('A','B',0x112B)
        self.assertFalse(result['compatible']);self.assertEqual(result['reason'],'palette-rgb555-differs')

    def test_cross_format_actual_allowlist_preserves_collision_and_height(self):
        source=Fixture();source.layouts['B']['layout_version']='emerald'
        compiled=CompiledMarineView(source)
        for word,target in [(0x312B,0x3170),(0x1643,0x15F9),(0x0114,0x0123)]:
            result=compiled.check('A','B',word)
            self.assertTrue(result['compatible']);self.assertEqual(result['translated_word'],target)
        self.assertFalse(compiled.check('A','B',0x3200)['compatible'])

    def test_halo_failure_does_not_become_a_false_movement_certificate(self):
        source=Fixture();source.words['A'][0]=0x3200
        source.layouts['B']['layout_version']='emerald'
        report=audit_edges(source,scope=['A','B'])
        self.assertEqual(report['authenticated_bank_pairs'],[['A','B'],['B','A']])
        self.assertTrue(report['edges'][0]['both_cameras_face_compatible'])
        self.assertFalse(report['edges'][0]['seven_tile_visual_report_compatible'])
        self.assertTrue(report['edges'][0]['halo_failures'])

    def test_one_good_seam_cannot_whitelist_another_bad_seam_between_same_maps(self):
        source=Fixture();source.layouts['B']['layout_version']='emerald'
        source.words['A'][0]=0x3200
        source.maps['A']['connections'].append(dict(map='MAP_B',direction='up',offset=0))
        source.maps['B']['connections'].append(dict(map='MAP_A',direction='down',offset=0))
        report=audit_edges(source,scope=['A','B'])
        self.assertTrue(any(r['both_cameras_face_compatible'] for r in report['edges']))
        self.assertTrue(any(r['face_failures'] for r in report['edges']))
        self.assertEqual(report['authenticated_bank_pairs'],[])
        self.assertTrue(all(not r['pair_authenticated_across_all_connections'] for r in report['edges']))


if __name__=='__main__':unittest.main()
