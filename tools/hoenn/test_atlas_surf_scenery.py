"""Whole-object, real-water and reciprocal event relocation regression tests."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from atlas_surf_scenery import (bind_native_water, check_placements, component_inventory,
                                placement, stage_placements, _json_digest)
from test_atlas_surf_object_ids import backend_fixture

WATER, LAND, REEF = 0x1170, 0x3001, 0x15F9


def stamp_fixture(*, actor=False):
    event = dict(x=3,y=5,elevation=3,dest_map="MAP_CAVE",dest_warp_id="1")
    events=[dict(field="warp_events",source_index=0,event=event,offset=[1,1])]
    if actor:
        events.append(dict(field="object_events",source_index=1,
                           event=dict(x=3,y=5,graphics_id="OBJ_TRAINER",script="Trainer",flag="0"),offset=[1,1]))
    value=dict(key="OldSea:000",parent_map="OldSea",parent_map_id="MAP_OLDSEA",
               source_rect=[2,4,3,3],source_anchor=[3,5],anchor_offset=[1,1],
               bank_signature="nativebank",banks=["Primary","Secondary"],layout_version="emerald",
               pure_water_word=WATER,words=[WATER]*3+[WATER,LAND,WATER]+[WATER]*3,
               native_water_runs=[[0,0,3],[1,0,1],[1,2,3],[2,0,3]],
               words_sha256="fixture",core_cells=[[1,1]],has_dry_terrain=True,
               touches_parent_edge=False,kind="portal-scenery",events=events,
               sprite_sources_authenticated=True,placement_assigned=False,native_validated=False)
    value["stamp_sha256"]=_json_digest(value)
    return value


class FakeLayer:
    def __init__(self,source,files):
        self.source=source;self.outputs={};self.expected={}
        for name,value in files.items():
            path=source/name;path.parent.mkdir(parents=True,exist_ok=True)
            blob=value if isinstance(value,bytes) else (json.dumps(value)+"\n").encode()
            path.write_bytes(blob);self.expected[name]=hashlib.sha256(blob).hexdigest()
    def stage(self,name,value):
        self.outputs[name]=value.encode() if isinstance(value,str) else value


class FakeInputs:
    def __init__(self,maps):
        self.maps=maps;self.by_id={value["id"]:name for name,value in maps.items()}
    def assert_unchanged(self):return len(self.maps)


class WholeSceneryTests(unittest.TestCase):
    def test_water_behavior_does_not_erase_shore_overlay(self):
        words=[WATER]*25
        words[2*5+2]=0x112B  # Different native art, even when its behavior is Surf.
        components,boundaries=component_inventory(words,5,5,WATER,{})
        self.assertEqual(len(components),1)
        self.assertEqual(components[0]["cells"],{(2,2)})
        self.assertEqual(boundaries,[])

    def test_diagonal_quarters_stay_whole_and_boundary_is_separate(self):
        words=[WATER]*49
        words[2*7+2]=LAND;words[3*7+3]=REEF
        words[0]=REEF
        components,boundaries=component_inventory(words,7,7,WATER,{})
        self.assertEqual(components[0]["cells"],{(2,2),(3,3)})
        self.assertEqual(boundaries,[{(0,0)}])

    def test_boundary_with_an_event_is_never_discarded_as_reef(self):
        words=[WATER]*9;words[0]=REEF
        components,boundaries=component_inventory(words,3,3,WATER,{"bg_events":[dict(x=0,y=0)]})
        self.assertEqual(len(components),1);self.assertEqual(boundaries,[])

    def test_native_mask_does_not_call_dry_threshold_water(self):
        stamp=stamp_fixture();row=placement(stamp,[100,100],name="New",halo=9)
        result=bind_native_water(row,stamp,{(100,100),(101,100),(98,100)})
        water={(result['origin'][0]+x,result['origin'][1]+y)
               for y,start,end in result['water_runs'] for x in range(start,end)}
        self.assertNotIn((100,100),water)
        self.assertIn((101,100),water)
        self.assertEqual(result['route_water_obstructed'],[[100,100]])
        self.assertEqual(result['width'],21)

    def test_corrupt_stamp_and_cropped_component_are_rejected(self):
        stamp=stamp_fixture();row=placement(stamp,[100,100],name="New",halo=0)
        altered=copy.deepcopy(stamp);altered['words'][4]=WATER
        with self.assertRaisesRegex(ValueError,"content changed"):
            check_placements([altered],[row])
        row['width']=2
        with self.assertRaisesRegex(ValueError,"dimensions or bank"):
            check_placements([stamp],[row])

    def test_main_corridor_conflict_requires_explicit_review(self):
        stamp=stamp_fixture();row=placement(stamp,[100,100],name="New",halo=0)
        with self.assertRaisesRegex(ValueError,"six-tile corridor"):
            check_placements([stamp],[row],core_corridor={(100,100)})
        result=check_placements([stamp],[row],core_corridor={(100,100)},allow_corridor_overrides={(100,100)})
        self.assertEqual(result['explicit_corridor_override_cells'],[[100,100]])

    def test_halo_rectangles_cannot_overlap(self):
        stamp=stamp_fixture();other=copy.deepcopy(stamp);other['key']='OldSea:001'
        other['stamp_sha256']=_json_digest({k:v for k,v in other.items() if k!='stamp_sha256'})
        a=placement(stamp,[100,100],name='A');b=placement(other,[110,100],name='B')
        with self.assertRaisesRegex(ValueError,'rectangles overlap'):
            check_placements([stamp,other],[a,b])

    def run_stage(self,*,foreign=False,actor=False,approved=(),numeric_id=None,target_objects=()):
        stamp=stamp_fixture(actor=actor)
        if actor and numeric_id is not None:
            stamp['events'][1]['event']['native_local_id']=numeric_id
            stamp['stamp_sha256']=_json_digest({key:value for key,value in stamp.items() if key!='stamp_sha256'})
        row=placement(stamp,[100,100],name="New",halo=1)
        old_objects=[dict(x=0,y=0)]
        if actor:old_objects.append(stamp['events'][1]['event'])
        maps={"OldSea":dict(id="MAP_OLDSEA",warp_events=[stamp['events'][0]['event']],object_events=old_objects),
              "Cave":dict(id="MAP_CAVE",warp_events=[dict(x=1,y=1,dest_map="MAP_CAVE",dest_warp_id="0"),
                                                      dict(x=3,y=4,dest_map="MAP_OLDSEA",dest_warp_id="0")],object_events=[])}
        target=dict(id="MAP_NEW",layout="LAYOUT_NEW",warp_events=[],object_events=list(target_objects))
        layout=dict(id="LAYOUT_NEW",width=5,height=5,primary_tileset="Foreign" if foreign else "Primary",
                    secondary_tileset="Secondary",layout_version="emerald",blockdata_filepath="new.bin")
        files={f"data/maps/{name}/map.json":value for name,value in maps.items()}
        files.update({"data/maps/New/map.json":target,"data/layouts/layouts.json":dict(layouts=[layout]),
                      "new.bin":struct.pack('<25H',*([REEF]*25))})
        if actor:files['tools/mapjson/mapjson.cpp']=backend_fixture().encode()
        with tempfile.TemporaryDirectory() as directory:
            layer=FakeLayer(Path(directory),files)
            result=stage_placements(layer,FakeInputs(maps),dict(stamps=[stamp]),[row],allow_local_id_reindex=approved)
            new=json.loads(layer.outputs['data/maps/New/map.json'])
            cave=json.loads(layer.outputs['data/maps/Cave/map.json'])
            words=struct.unpack('<25H',layer.outputs['new.bin'])
        return result,new,cave,words

    def test_native_bank_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'different native banks'):
            self.run_stage(foreign=True)

    def test_grouped_whole_objects_accumulate_in_one_native_map_without_overwrite(self):
        stamps=[];placements=[]
        for i,left in enumerate((1,6)):
            stamp=stamp_fixture();stamp.update(key=f'OldSea:{i:03}',events=[],kind='land-scenery')
            stamp['words'][4]=LAND+i
            stamp['stamp_sha256']=_json_digest({k:v for k,v in stamp.items() if k!='stamp_sha256'})
            row=placement(stamp,[100+left+1,102],name='New',halo=1)
            row.update(origin=[100,100],width=10,height=5,stamp_offset=[left,1],
                       shared_reservation=True,component_global_rect=[100+left,101,3,3])
            stamps.append(stamp);placements.append(row)
        layout=dict(id='LAYOUT_NEW',width=10,height=5,primary_tileset='Primary',
                    secondary_tileset='Secondary',layout_version='emerald',blockdata_filepath='new.bin')
        maps={'OldSea':dict(id='MAP_OLDSEA',warp_events=[],object_events=[])}
        files={'data/maps/OldSea/map.json':maps['OldSea'],
               'data/maps/New/map.json':dict(id='MAP_NEW',layout='LAYOUT_NEW',warp_events=[],object_events=[]),
               'data/layouts/layouts.json':dict(layouts=[layout]),'new.bin':struct.pack('<50H',*([REEF]*50))}
        with tempfile.TemporaryDirectory() as directory:
            layer=FakeLayer(Path(directory),files)
            stage_placements(layer,FakeInputs(maps),dict(stamps=stamps),placements)
            words=struct.unpack('<50H',layer.outputs['new.bin'])
            self.assertEqual(words[22],LAND)
            self.assertEqual(words[27],LAND+1)
            self.assertEqual(words[0],REEF)
        overlapping=copy.deepcopy(placements);overlapping[1]['stamp_offset']=[2,1]
        overlapping[1]['component_global_rect']=[102,101,3,3]
        with self.assertRaisesRegex(ValueError,'cores overlap'):
            check_placements(stamps,overlapping)

    def test_whole_terrain_and_nonzero_reciprocal_warp_are_relocated(self):
        result,new,cave,words=self.run_stage()
        self.assertEqual(new['warp_events'][0]['dest_warp_id'],'1')
        self.assertEqual([new['warp_events'][0]['x'],new['warp_events'][0]['y']],[2,2])
        self.assertEqual(cave['warp_events'][1]['dest_map'],'MAP_NEW')
        self.assertEqual(cave['warp_events'][1]['dest_warp_id'],'0')
        self.assertEqual(words[12],LAND)
        self.assertEqual(words[0],REEF)  # Camera halo stays in the reserved bank.
        self.assertEqual(len(result['incoming_warps_repointed']),1)

    def test_object_numeric_id_survives_array_reordering_without_allowlist(self):
        result,new,_,_=self.run_stage(actor=True)
        self.assertEqual(new['object_events'][0]['script'],'Trainer')
        self.assertEqual(new['object_events'][0]['native_local_id'],2)
        self.assertEqual(result['relocated_events'][1]['source_index'],1)
        self.assertEqual(result['relocated_events'][1]['source_local_id'],2)
        self.assertEqual(result['relocated_events'][1]['target_local_id'],2)
        self.assertTrue(result['native_object_id_backend']['object_clone_and_macro_share_ids'])
        self.assertTrue(result['object_numeric_ids_preserved'])

    def test_explicit_source_id_and_deprecated_allowlist_cannot_renumber(self):
        result,new,_,_=self.run_stage(actor=True,numeric_id=240,approved=[('OldSea',1)])
        self.assertEqual(new['object_events'][0]['native_local_id'],240)
        self.assertTrue(result['deprecated_local_id_reindex_allowlist_ignored'])
        self.assertEqual(result['relocated_object_ids'][0]['native_local_id'],240)

    def test_grouping_conflicting_native_object_ids_requires_another_map(self):
        with self.assertRaisesRegex(ValueError,'local-ID collision'):
            self.run_stage(actor=True,target_objects=[dict(native_local_id=2)])


if __name__=='__main__':unittest.main()
