"""Exact event coverage, incoming travel and preserved save identities."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from atlas_surf_retirement import audit,stage,RetirementBlocked,EVENT_FIELDS


class FakeLayer:
    def __init__(self,source,files):
        self.source=source;self.outputs={};self.expected={}
        for path,value in files.items():
            raw=value.encode() if isinstance(value,str) else (json.dumps(value)+"\n").encode()
            target=source/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            self.expected[path]=hashlib.sha256(raw).hexdigest()
    def stage(self,path,value):self.outputs[path]=value.encode() if isinstance(value,str) else value


def fixture():
    actor=dict(x=5,y=6,elevation=1,script='TrainerScript',flag='FLAG_TRAINER',
               graphics_id='GFX_SWIMMER',trainer_type='TRAINER_TYPE_NORMAL')
    warp=dict(x=8,y=9,elevation=3,dest_map='MAP_CAVE',dest_warp_id='1')
    moved_actor={**actor,'x':2,'y':3};moved_warp={**warp,'x':4,'y':5}
    maps={
        'Old':dict(id='MAP_OLD',layout='OLD_LAYOUT',music='MUS_OLD',connections=[dict(map='MAP_OLD',direction='up',offset=0)],
                   object_events=[actor],warp_events=[warp],coord_events=[],bg_events=[]),
        'New':dict(id='MAP_NEW',layout='NEW_LAYOUT',connections=[],object_events=[moved_actor],warp_events=[moved_warp],coord_events=[],bg_events=[]),
        'Cave':dict(id='MAP_CAVE',layout='CAVE_LAYOUT',connections=[],object_events=[],warp_events=[
            dict(x=0,y=0,dest_map='MAP_CAVE',dest_warp_id='0'),dict(x=1,y=1,dest_map='MAP_NEW',dest_warp_id='0')],coord_events=[],bg_events=[])}
    files={f'data/maps/{name}/map.json':value for name,value in maps.items()}
    files['data/maps/map_groups.json']=dict(group_order=['Parent','Atlas'],Parent=['Old','Cave'],Atlas=['New'])
    files['data/layouts/layouts.json']=dict(layouts=[dict(id=name,width=20,height=20) for name in ['OLD_LAYOUT','NEW_LAYOUT','CAVE_LAYOUT']])
    files['data/scripts/old.inc']='Old_MapScripts::\n\t.byte 0\n'
    records=[dict(source_map='Old',field='object_events',source_index=0,source_tile=[5,6],target_map='New',target_index=0,target_tile=[2,3]),
             dict(source_map='Old',field='warp_events',source_index=0,source_tile=[8,9],target_map='New',target_index=0,target_tile=[4,5])]
    retired=[dict(map='Old',id='MAP_OLD',packed_id=0,layout='OLD_LAYOUT',events={field:maps['Old'][field] for field in EVENT_FIELDS})]
    return files,retired,records


class RetirementTests(unittest.TestCase):
    def run_fixture(self,action,mutate=None,**kwargs):
        files,retired,records=fixture()
        if mutate:mutate(files,retired,records)
        with tempfile.TemporaryDirectory() as directory:
            layer=FakeLayer(Path(directory),files)
            result=action(layer,retired,records,**kwargs)
            return result,dict(layer.outputs),files

    def test_retirement_only_changes_active_arrays_and_keeps_ids_layout_scripts(self):
        report,outputs,files=self.run_fixture(stage)
        self.assertEqual(set(outputs),{'data/maps/Old/map.json'})
        old=json.loads(outputs['data/maps/Old/map.json'])
        self.assertEqual(old['id'],'MAP_OLD');self.assertEqual(old['layout'],'OLD_LAYOUT')
        self.assertEqual(old['music'],'MUS_OLD');self.assertEqual(old['connections'],[])
        for field in EVENT_FIELDS:self.assertEqual(old[field],[])
        self.assertEqual(report['expected_event_count'],2)
        self.assertTrue(report['source_staged'])
        self.assertFalse(report['save_migration_applied'])
        table=report['legacy_dest_warp_table'][0]
        self.assertEqual((table['old_packed_id'],table['old_warp_id']),(0,0))
        self.assertEqual((table['new_packed_id'],table['new_warp_id']),(256,0))
        self.assertEqual(table['old_event']['dest_warp_id'],'1')

    def test_missing_event_coverage_never_clears_any_old_event(self):
        files,retired,records=fixture();records.pop()
        with tempfile.TemporaryDirectory() as directory:
            layer=FakeLayer(Path(directory),files)
            with self.assertRaisesRegex(ValueError,'exact complete relocation coverage'):
                stage(layer,retired,records)
            self.assertEqual(layer.outputs,{})

    def test_duplicate_and_invented_events_are_rejected(self):
        for index in (0,99):
            def mutate(files,retired,records):
                row=copy.deepcopy(records[0]);row['source_index']=index;records.append(row)
            with self.assertRaisesRegex(ValueError,'Duplicate or invented'):
                self.run_fixture(stage,mutate)

    def test_trainer_script_or_flag_change_is_not_a_relocation(self):
        def mutate(files,retired,records):files['data/maps/New/map.json']['object_events'][0]['flag']='0'
        with self.assertRaisesRegex(ValueError,'identity was altered'):
            self.run_fixture(stage,mutate)

    def test_numeric_native_local_id_override_is_accepted_only_when_identity_is_equal(self):
        def same(files,retired,records):files['data/maps/New/map.json']['object_events'][0]['native_local_id']=1
        report,_,_=self.run_fixture(stage,same)
        self.assertEqual(report['relocated_events'][0]['source_native_local_id'],1)
        def changed(files,retired,records):files['data/maps/New/map.json']['object_events'][0]['native_local_id']=2
        with self.assertRaisesRegex(ValueError,'Native object local ID changed'):
            self.run_fixture(stage,changed)

    def test_changed_parent_inventory_is_rejected_before_staging(self):
        def mutate(files,retired,records):retired[0]['events']['object_events']=[]
        with self.assertRaisesRegex(ValueError,'Parent event inventory changed'):
            self.run_fixture(stage,mutate)

    def test_old_numeric_identity_is_append_only(self):
        def mutate(files,retired,records):files['data/maps/map_groups.json']['Parent'].reverse()
        with self.assertRaisesRegex(ValueError,'numeric identity changed'):
            self.run_fixture(stage,mutate)

    def test_remaining_native_warp_blocks_retirement_without_partial_outputs(self):
        files,retired,records=fixture()
        files['data/maps/Cave/map.json']['warp_events'][1]['dest_map']='MAP_OLD'
        with tempfile.TemporaryDirectory() as directory:
            layer=FakeLayer(Path(directory),files)
            with self.assertRaises(RetirementBlocked) as error:stage(layer,retired,records)
            self.assertEqual(len(error.exception.report['incoming_warps']),1)
            self.assertEqual(layer.outputs,{})

    def test_remaining_native_connection_blocks_retirement(self):
        def mutate(files,retired,records):files['data/maps/Cave/map.json']['connections']=[dict(map='MAP_OLD',direction='up',offset=0)]
        with self.assertRaises(RetirementBlocked) as error:self.run_fixture(stage,mutate)
        self.assertEqual(error.exception.report['incoming_connections'][0]['map'],'Cave')

    def test_portal_cannot_silently_change_interior(self):
        def mutate(files,retired,records):files['data/maps/New/map.json']['warp_events'][0]['dest_warp_id']='0'
        with self.assertRaisesRegex(ValueError,'silently changed its interior'):
            self.run_fixture(stage,mutate)

    def test_code_references_are_reported_and_optional_release_gate_is_strict(self):
        def mutate(files,retired,records):
            files['src/warp.c']='// MAP_OLD is only a comment here.\nvoid Travel(void) { SetWarp(MAP_OLD); }\n'
        report,_,_=self.run_fixture(stage,mutate)
        unresolved=report['code_references']['unresolved']
        self.assertEqual(len(unresolved),1)
        self.assertEqual(unresolved[0]['locations'][0]['line'],2)
        self.assertFalse(report['code_reference_audit_complete'])
        with self.assertRaises(RetirementBlocked):self.run_fixture(stage,mutate,require_code_resolution=True)

    def test_code_resolution_is_bound_to_exact_file_bytes(self):
        code='const int oldMap = MAP_OLD;\n'
        def mutate(files,retired,records):files['src/legacy.c']=code
        policy=[dict(path='src/legacy.c',symbol='MAP_OLD',file_sha256=hashlib.sha256(code.encode()).hexdigest(),
                     kind='migration-table',evidence='Immutable old identity is consumed only by migration version2.')]
        report,_,_=self.run_fixture(stage,mutate,code_reference_resolutions=policy,require_code_resolution=True)
        self.assertTrue(report['code_reference_audit_complete'])
        policy[0]['file_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'resolution is stale'):
            self.run_fixture(stage,mutate,code_reference_resolutions=policy)

    def test_audit_is_read_only_even_when_travel_still_enters_old_mesh(self):
        def mutate(files,retired,records):files['data/maps/Cave/map.json']['connections']=[dict(map='MAP_OLD',direction='down',offset=0)]
        report,outputs,_=self.run_fixture(audit,mutate)
        self.assertEqual(outputs,{})
        self.assertEqual(len(report['incoming_connections']),1)
        self.assertFalse(report['source_staged'])


if __name__=='__main__':unittest.main()
