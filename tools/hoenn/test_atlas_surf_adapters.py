"""Coast integration guards: native offsets, banks, terrain and height3."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from atlas_surf_adapters import plan_adapters, stage_bindings
from atlas_surf_source import CARDINAL, OPPOSITE


class Terrain:
    def __init__(self, height=1):
        self.height = height
        self.maps = {'Native': {'id':'MAP_NATIVE'}, 'Donor':{'id':'MAP_DONOR'}}
    def layout(self, name):
        return dict(width=12,height=12,primary_tileset='NativePrimary',
                    secondary_tileset='NativeSecondary',layout_version='frlg')
    def anchors(self):
        return {'Native':dict(atlas=[10,10],section='NATIVE',label='NATIVE')}
    def word(self, name, x, y):
        if (x,y) == (11,11): return 0x1643
        return ((self.height if name == 'Native' else 1)<<12)|0x12B
    def water(self, name, x, y):
        return not self.word(name,x,y)&0xC00
    def water_components(self,name):
        cells = [(x,y) for y in range(12) for x in range(12) if self.water(name,x,y)]
        return dict.fromkeys(cells,0), [cells]


class Truth:
    array_sha256 = {'tiles':'frozen'}
    def pixel(self, point): return 2


def fixture(direction='right', height=1):
    source = Terrain(height)
    dx,dy = CARDINAL[direction]
    anchor = {'left':[0,5], 'right':[11,5], 'up':[5,0], 'down':[5,11]}[direction]
    native = [([anchor[0],v] if dx else [v,anchor[1]]) for v in range(1,10)]
    row = dict(native_map='Native',component=0,
               source_wet_edge_witnesses=[dict(native_tile=p,retired_tile=[0,p[1]],
                    direction=OPPOSITE[direction],offset=0,retired_map='Retired',
                    words=[0x112B,source.word('Native',*p)],height_compatible=height==1)
                    for p in native])
    origin = [84-anchor[0],84-anchor[1]]
    mouth = [([anchor[0],v] if dx else [v,anchor[1]]) for v in range(2,8)]
    water = {(x+origin[0]+distance*dx,y+origin[1]+distance*dy)
             for x,y in mouth for distance in range(1,18)}
    left,top = min(x for x,y in water),min(y for x,y in water)
    right,bottom = max(x for x,y in water)+1,max(y for x,y in water)+1
    runs=[]
    for y in range(top,bottom):
        xs=sorted(x-left for x,yy in water if yy==y)
        runs.append([y-top,xs[0],xs[-1]+1])
    plan=dict(scale=8,corridor_width=6,chunks=[dict(origin=[left,top],width=right-left,
              height=bottom-top,water_runs=runs)])
    reg=dict(native_map='Native',component=0,native_tile=anchor,global_tile=[84,84],
             direction=direction,local_rect=[0,0,12,12],
             donor=dict(map='Donor',water_tile=[0,0],reef_tile=[11,11]),
             atlas_evidence=dict(art_sha256={'tiles':'frozen'},
                  fixed_anchor=dict(map='Native',atlas=[10,10]),
                  geographic_basis='test registered coast',native_coast_basis='real boundary',
                  art_samples=[dict(atlas=[10,10],palette_index=2)]))
    return source,dict(adapters=[row]),plan,[reg],Truth()


class AdapterTests(unittest.TestCase):
    def test_raster_junction_padding_needs_an_independent_native_edge_witness(self):
        args=list(fixture());chunk=args[2]['chunks'][0]
        chunk['height']+=1
        chunk['water_runs'].append([6,0,1])
        result=plan_adapters(*args)
        proof=result['bindings'][0]['source_wet_mouth']
        self.assertEqual(len(proof),7)
        self.assertIn([11,8],[w['native_tile'] for w in proof])
        args[1]['adapters'][0]['source_wet_edge_witnesses']=[w for w in args[1]['adapters'][0]['source_wet_edge_witnesses'] if w['native_tile']!=[11,8]]
        with self.assertRaisesRegex(ValueError,'Unregistered native water opening'):
            plan_adapters(*args)

    def test_four_headings_have_real_reciprocal_offsets_and_straight_water(self):
        for direction in CARDINAL:
            with self.subTest(direction=direction):
                result=plan_adapters(*fixture(direction))
                binding=result['bindings'][0]; reservation=result['reservations'][0]
                self.assertEqual(binding['native_connection']['direction'],direction)
                self.assertEqual(binding['adapter_connection']['direction'],OPPOSITE[direction])
                self.assertEqual(binding['native_connection']['offset'],-binding['adapter_connection']['offset'])
                self.assertEqual(len(binding['source_wet_mouth']),6)
                self.assertTrue(result['complete_component_coverage'])
                self.assertEqual(reservation['banks'],['NativePrimary','NativeSecondary','frlg'])
                self.assertEqual(reservation['word_overrides'],[])

    def test_native_height3_uses_new_adapter_transition_without_normalizing_native(self):
        source,inventory,plan,regs,truth=fixture(height=3)
        before=source.word('Native',11,5)
        result=plan_adapters(source,inventory,plan,regs,truth)
        reservation=result['reservations'][0]; binding=result['bindings'][0]
        self.assertEqual(binding['native_heights'],[3])
        self.assertEqual(binding['adapter_height'],3)
        self.assertEqual({r['word']>>12 for r in reservation['word_overrides']},{0,3})
        self.assertEqual(source.word('Native',11,5),before)
        self.assertTrue(binding['transition_height_zero_only_in_new_adapter'])

    def test_unproven_or_stale_coast_registration_cannot_pass(self):
        for modification in ('gps','hash','sample','anchor','offedge'):
            args=list(fixture()); regs=args[3]
            if modification=='gps': regs[0]['atlas_evidence']['sole_basis']='old-gps'
            elif modification=='hash': regs[0]['atlas_evidence']['art_sha256']={'tiles':'changed'}
            elif modification=='sample': regs[0]['atlas_evidence']['art_samples'][0]['palette_index']=1
            elif modification=='anchor': regs[0]['atlas_evidence']['fixed_anchor']['atlas']=[11,10]
            else: regs[0]['native_tile']=[10,5]
            with self.subTest(modification=modification),self.assertRaises(ValueError):
                plan_adapters(*args)

    def test_missing_component_and_duplicate_placements_are_rejected(self):
        args=list(fixture()); args[1]['adapters'].append(dict(native_map='Other',component=1))
        with self.assertRaises(ValueError):plan_adapters(*args)
        args=list(fixture()); args[3].append(copy.deepcopy(args[3][0]))
        with self.assertRaises(ValueError):plan_adapters(*args)

    def test_gap_before_outer_route_and_foreign_banks_fail_closed(self):
        args=list(fixture()); args[2]['chunks'][0]['water_runs'][2][1]=2
        with self.assertRaises(ValueError):plan_adapters(*args)
        args=list(fixture())
        real=args[0].layout
        args[0].layout=lambda n: {**real(n),'secondary_tileset':'Foreign'} if n=='Donor' else real(n)
        with self.assertRaises(ValueError):plan_adapters(*args)

    def test_native_events_and_blockdata_survive_link_staging(self):
        args=fixture(height=3); result=plan_adapters(*args)
        reservation=result['reservations'][0]; binding=result['bindings'][0]
        with tempfile.TemporaryDirectory() as temp:
            class Layer:
                source=Path(temp)
                outputs={}
                expected={}
                def stage(self,name,content):
                    self.outputs[name]=content.encode() if isinstance(content,str) else content
            layer=Layer()
            native=dict(id='MAP_NATIVE',layout='NATIVE',connections=[dict(map='MAP_RETIRED',direction='right',offset=-2)],
                        object_events=[dict(x=2,y=3,script='KEEP')],warp_events=[dict(x=4,y=5)],
                        coord_events=[],bg_events=[])
            files={'data/maps/Native/map.json':json.dumps(native),
                   'data/maps/Retired/map.json':json.dumps(dict(id='MAP_RETIRED')),
                   f"data/maps/{reservation['name']}/map.json":json.dumps(dict(id=binding['adapter_id'],layout='ADAPTER',connections=[])),
                   'data/layouts/layouts.json':json.dumps(dict(layouts=[dict(id='ADAPTER',width=reservation['width'],height=reservation['height'],blockdata_filepath='adapter.bin')])),
                   'native.bin':b'preserved'}
            width,height=reservation['width'],reservation['height']; words=[0x1643]*(width*height)
            for y,left,right in reservation['water_runs']:
                for x in range(left,right):words[y*width+x]=0x112B
            files['adapter.bin']=struct.pack('<'+'H'*len(words),*words)
            for name,value in files.items():
                path=layer.source/name;path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(value.encode() if isinstance(value,str) else value)
                layer.expected[name]=hashlib.sha256(path.read_bytes()).hexdigest()
            report=stage_bindings(layer,result,retired_maps=['Retired'])
            staged=json.loads(layer.outputs['data/maps/Native/map.json'])
            for key in ('object_events','warp_events','coord_events','bg_events'):
                self.assertEqual(staged[key],native[key])
            self.assertEqual(staged['connections'],[binding['native_connection']])
            self.assertNotIn('native.bin',layer.outputs)
            self.assertEqual((layer.source/'native.bin').read_bytes(),b'preserved')
            self.assertTrue(report['native_blockdata_not_modified'])
            changed=struct.unpack('<'+'H'*len(words),layer.outputs['adapter.bin'])
            self.assertEqual({value>>12 for value in changed if not value&0xC00},{0,1,3})


if __name__=='__main__':unittest.main()
