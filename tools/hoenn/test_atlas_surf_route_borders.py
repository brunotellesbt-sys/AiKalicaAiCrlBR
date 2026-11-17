"""A thin boundary must preserve old play and isolate the new background."""
from collections import deque
import struct
import unittest

from atlas_surf_route_borders import plan,_neighbor


WATER=0x112b
REEF=0x1643


class Terrain:
    def __init__(self,host=False):
        self.data={'Sea':[REEF]*49};self.data['Sea'][3*7+3]=WATER
        self.maps={'Sea':dict(id='MAP_SEA',connections=[])};self.by_id={'MAP_SEA':'Sea'}
        if host:
            self.data['Host']=[WATER]*21;self.maps['Host']=dict(id='MAP_HOST',connections=[])
            self.by_id['MAP_HOST']='Host';self.maps['Sea']['connections']=[dict(direction='right',map='MAP_HOST',offset=0)]
        self.behavior_flags=dict(values=b'\x01',surf_flag=1)
    def layout(self,name):return dict(width=7 if name=='Sea' else 3,height=7,
        primary_tileset='Primary',secondary_tileset='Secondary',blockdata_filepath=name+'.bin')
    def word(self,name,x,y):return self.data[name][y*self.layout(name)['width']+x]
    def words(self,name):return self.data[name]
    def read(self,path):return struct.pack('<'+'H'*len(self.data[path[:-4]]),*self.data[path[:-4]])
    def behavior(self,name,word):return 0
    def assert_unchanged(self):return True


def metadata(kind='ordinary'):
    row=dict(name='Sea',kind=kind,width=7,height=7)
    if kind=='stamp':row.update(source_rect=[0,0,2,2],stamp_offset=[0,0])
    return dict(geometry_plan=dict(chunks=[row]),geometry=dict(chunks=[dict(map='Sea',
        donor_banks=['Primary','Secondary'],water_word=WATER,reef_word=REEF)]))


class ThinReefTests(unittest.TestCase):
    def test_existing_route_survives_but_background_cannot_be_reached(self):
        terrain=Terrain();changes,report=plan(terrain,metadata());self.assertEqual(len(changes),1)
        words=struct.unpack('<49H',changes[0]['raw'])
        self.assertEqual(words[3*7+3],WATER)
        for x,y in [(2,3),(4,3),(3,2),(3,4)]:self.assertEqual(words[y*7+x],REEF)
        self.assertEqual(words[0],WATER);self.assertEqual(report['background_water_cells'],44)
        seen={(3,3)};todo=deque(seen)
        while todo:
            x,y=todo.popleft()
            for xx,yy in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                if 0<=xx<7 and 0<=yy<7 and not words[yy*7+xx]&0xc00 and (xx,yy) not in seen:
                    seen.add((xx,yy));todo.append((xx,yy))
        self.assertEqual(seen,{(3,3)})

    def test_native_shore_connection_gets_a_continuous_blocking_line(self):
        terrain=Terrain(host=True);changes,_=plan(terrain,metadata());words=struct.unpack('<49H',changes[0]['raw'])
        self.assertTrue(all(words[y*7+6]==REEF for y in range(7)))
        self.assertTrue(all(words[y*7+5]==WATER for y in range(7) if y!=3))

    def test_native_core_is_not_erased_even_if_it_uses_the_reef_metatile(self):
        terrain=Terrain();changes,_=plan(terrain,metadata('stamp'));words=struct.unpack('<49H',changes[0]['raw'])
        for y in range(2):
            for x in range(2):self.assertEqual(words[y*7+x],REEF)

    def test_first_bounded_connection_wins_even_when_its_tile_is_blocked(self):
        terrain=Terrain(host=True);terrain.maps['BlockedHost']=dict(id='MAP_BLOCKED',connections=[])
        terrain.by_id['MAP_BLOCKED']='BlockedHost';terrain.data['BlockedHost']=[REEF]*21
        terrain.maps['Sea']['connections'].insert(0,dict(direction='right',map='MAP_BLOCKED',offset=0))
        self.assertEqual(_neighbor(terrain,'Sea',6,3,1,0),('BlockedHost',0,3))
        changes,_=plan(terrain,metadata());self.assertEqual(struct.unpack('<49H',changes[0]['raw'])[3*7+6],WATER)

    def test_wrong_bank_cannot_be_treated_as_a_universal_reef_id(self):
        terrain=Terrain();m=metadata();m['geometry']['chunks'][0]['donor_banks']=['Other','Bank']
        with self.assertRaisesRegex(ValueError,'bank'):plan(terrain,m)


if __name__=='__main__':unittest.main()
