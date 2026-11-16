"""Keep the ferry service and native objects while freeing the harbor paths."""
from copy import deepcopy
import json
import hashlib
import struct
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest

from atlas_surf_object_ids import validate_object_ids
from atlas_surf_pacifidlog_captain import stage as move_captain
from atlas_surf_slateport_rocks import stage as finish_rocks
from candidate_layer import Layer


class HarborFixTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/'.source-acquired.json').write_text(json.dumps(dict(sha256={})))
        self.layer=Layer(self.root,'fixture',[])

    def write(self,name,value):
        path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(value if isinstance(value,bytes) else (json.dumps(value)+'\n').encode())
        self.layer.expected[name]=hashlib.sha256(path.read_bytes()).hexdigest()

    def test_captain_retains_service_and_ids_and_boat_does_not_inherit_his_id(self):
        captain=dict(x=11,y=27,graphics_id='OBJ_EVENT_GFX_SAILOR',script='Journey_FerryPort11',
                     local_id='LOCALID_JOURNEY_BIRTH_CAPTAIN_31',flag='0',elevation=3,movement_type='MOVEMENT_TYPE_FACE_DOWN')
        boat=dict(x=12,y=29,graphics_id='OBJ_EVENT_GFX_MR_BRINEYS_BOAT',script='JourneyCompactPort_Boat')
        town=dict(id='MAP_PACIFIDLOG_TOWN',object_events=[dict(x=i,y=10,script='resident') for i in range(3)]+[captain,boat],
                  warp_events=[dict(x=12,y=24,dest_map='MAP_PACIFIDLOG_TOWN_HOUSE3'),
                               dict(x=16,y=13,dest_map='MAP_PACIFIDLOG_TOWN_HOUSE1')])
        house=dict(id='MAP_PACIFIDLOG_TOWN_HOUSE3',object_events=[dict(x=3,y=5,script='girl'),dict(x=4,y=2,script='trader')],
                   warp_events=[dict(x=4,y=8,dest_map='MAP_PACIFIDLOG_TOWN')])
        before=deepcopy((town,house))
        for name,value in [('PacifidlogTown',town),('PacifidlogTown_House3',house)]:self.write(f'data/maps/{name}/map.json',value)
        inputs=SimpleNamespace(word=lambda n,x,y:0x3001,water=lambda n,x,y:False)
        r=move_captain(self.layer,inputs)
        after=[json.loads(self.layer.outputs[f'data/maps/{n}/map.json']) for n in ('PacifidlogTown','PacifidlogTown_House3')]
        self.assertEqual(validate_object_ids(after[0]['object_events']),[1,2,3,5])
        self.assertEqual(validate_object_ids(after[1]['object_events']),[1,2,4])
        moved=after[1]['object_events'][-1]
        self.assertEqual((moved['script'],moved['local_id'],moved['flag']),
                         (captain['script'],captain['local_id'],captain['flag']))
        self.assertEqual((moved['x'],moved['y']),(7,6));self.assertEqual(r['port_number'],11)
        for old,new in zip(before,after):self.assertEqual(old['warp_events'],new['warp_events'])
        self.assertEqual(after[0]['object_events'][-1],dict(boat,native_local_id=5))
        self.assertEqual(after[1]['object_events'][:2],house['object_events'])

    def test_boulder_slices_become_complete_cliff_without_changing_collision_or_water(self):
        values=[0x1170]*2400
        for x,y in ((36,6),(38,15)):values[y*40+x]=0x564;values[(y+1)*40+x]=0x56c
        values[17*40+35:17*40+37]=[0x55a,0x55b]
        values[57*40+3:57*40+5]=[0x552,0x553]
        for x,y,pattern in [(1,58,[0x550,0x551,0x558,0x559]),(37,57,[0x1552,0x1553,0x1558,0x1559])]:
            for q,v in enumerate(pattern):values[(y+q//2)*40+x+q%2]=v
        values[59*40+38:59*40+40]=[0x1550,0x1551]
        original=values.copy();path='data/layouts/SlateportCity/map.bin'
        self.write(path,struct.pack('<2400H',*values))
        layout=dict(width=40,height=60,primary_tileset='gTileset_General',secondary_tileset='gTileset_Slateport',layout_version='emerald',blockdata_filepath=path)
        def word(name,x,y):
            if name=='Route109':return {(38,0):0x1558,(39,0):0x1559}.get((x,y),0x1170)
            return {(36,5):0x1190,(34,17):0x1189,(6,58):0x112c}.get((x,y),values[y*40+x])
        inputs=SimpleNamespace(layout=lambda n:layout,word=word,
            maps={'SlateportCity':dict(connections=[dict(direction='down',map='MAP_ROUTE109',offset=0)]),'Route109':{}},
            by_id={'MAP_ROUTE109':'Route109'})
        r=finish_rocks(self.layer,inputs);actual=struct.unpack('<2400H',self.layer.outputs[path])
        changed={i for i,(a,b) in enumerate(zip(original,actual)) if a!=b}
        self.assertEqual(changed,{y*40+x for x,y in ((36,6),(36,7),(38,15),(38,16),(35,17),(36,17),(3,57),(4,57))})
        for i in changed:
            self.assertEqual(original[i]&~1023,actual[i]&~1023)
            self.assertEqual(actual[i]&1023,0x12c if i//40==57 else 0x189 if i//40==17 else 0x190)
        self.assertEqual(len(r['complete_visible_slices_removed']),2)
        self.assertEqual(len(r['before_census']['orphan_pieces']),8)
        self.assertEqual(r['after_census']['orphan_pieces'],[])
        self.assertEqual(len(r['after_census']['complete_objects']),3)


if __name__=='__main__':unittest.main()
