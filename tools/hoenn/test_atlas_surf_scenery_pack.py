"""Whole objects must fit real route geometry without cutting travel channels."""
from copy import deepcopy
from types import SimpleNamespace
import unittest

from atlas_surf_dives import OLD_SURFACES,patch_specs
from atlas_surf_geometry import rasterize
from atlas_surf_scenery import _json_digest
from atlas_surf_scenery_pack import (fixed_dive_reservations,pack_scenery,pack_grouped_scenery,
                                    preserve_native_water_collars)
from test_atlas_surf_scenery import stamp_fixture


class Inputs:
    def anchors(self):return {'OldSea':dict(atlas=[12,12],label='OLD SEA')}
    def assert_unchanged(self):return 0


class WholeSceneryPackingTests(unittest.TestCase):
    def setUp(self):
        self.truth=SimpleNamespace(indices=[1]*(224*112))
        self.pixels={(x,12) for x in range(4,23)}

    def stamp(self,key):
        stamp=stamp_fixture();stamp.update(key=key,kind='land-scenery',events=[])
        stamp['stamp_sha256']=_json_digest({k:v for k,v in stamp.items() if k!='stamp_sha256'})
        return stamp

    def test_complete_objects_stay_adjacent_without_blocking_route_or_overlapping(self):
        stamps=[self.stamp(f'OldSea:{i:03}') for i in range(4)]
        original=deepcopy(stamps)
        plan=pack_scenery(Inputs(),self.truth,dict(stamps=stamps),self.pixels)
        self.assertTrue(plan['complete']);self.assertEqual(plan['placed_native_stamps'],4)
        self.assertEqual(stamps,original)
        water=rasterize(self.pixels)
        rects=[]
        for row in plan['reservations']:
            self.assertEqual(row['route_water_obstructed'],[])
            x,y=row['global_anchor']
            self.assertNotIn((x,y),water)
            self.assertTrue(any((x+dx,y+dy) in water for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))))
            self.assertFalse(row['evidence']['authored_decoration_region']['original_player_gps_used'])
            ox,oy=row['origin'];r=(ox,oy,ox+row['width'],oy+row['height'])
            for a,b,c,d in rects:
                self.assertFalse(max(ox,a)<min(r[2],c) and max(oy,b)<min(r[3],d))
            rects.append(r)

    def test_no_fit_is_explicit_and_does_not_invent_a_channel_or_cut_an_object(self):
        stamp=self.stamp('OldSea:000')
        existing=[dict(name='Occupied',origin=[0,0],width=200,height=200)]
        plan=pack_scenery(Inputs(),self.truth,dict(stamps=[stamp]),self.pixels,existing=existing)
        self.assertFalse(plan['complete']);self.assertEqual(plan['reservations'],[])
        self.assertEqual(plan['unplaced_stamps'][0]['stamp'],stamp['key'])
        self.assertFalse(plan['art_changed'])

    def test_native_continent_cannot_be_overwritten_by_decorative_relocation(self):
        self.truth.indices=[3]*(224*112)
        plan=pack_scenery(Inputs(),self.truth,dict(stamps=[self.stamp('OldSea:000')]),self.pixels)
        self.assertFalse(plan['complete'])
        self.assertGreater(plan['rejected_candidate_counts']['non_ocean_art'],0)

    def test_cave_without_fixed_icon_registration_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'fixed icon'):
            pack_scenery(Inputs(),self.truth,dict(stamps=[stamp_fixture()]),self.pixels)

    def test_fixed_dive_replacement_is_exactly_the_five_event_free_native_features(self):
        stamps=[]
        for site in patch_specs():
            stamp=dict(key=site['name'],stamp_sha256='authenticated',
                       parent_map=OLD_SURFACES[site['name']],source_anchor=site['portal'],
                       source_rect=[0,0,5,5],words=[0x114f]*25,kind='water-decoration',events=[],
                       native_water_runs=[[y,0,5] for y in range(5)],bank_signature='emerald')
            stamps.append(stamp)
        plan=fixed_dive_reservations(dict(stamps=stamps),set())
        self.assertEqual(len(plan['replaced_stamps']),5)
        self.assertEqual(sum(sum(b-a for y,a,b in r['additional_water_runs'])
                             for r in plan['reservations']),75)
        altered=deepcopy(stamps);altered[0]['events']=[dict(script='PreserveMe')]
        with self.assertRaisesRegex(ValueError,'complete original stamp'):
            fixed_dive_reservations(dict(stamps=altered),set())

    def test_same_owner_shares_outer_margin_while_all_native_cores_remain_whole(self):
        stamps=[self.stamp(f'OldSea:{i:03}') for i in range(7)]
        plan=pack_grouped_scenery(Inputs(),self.truth,dict(stamps=stamps),self.pixels)
        self.assertTrue(plan['complete']);self.assertEqual(plan['placed_native_stamps'],7)
        self.assertLess(plan['grouped_decorative_maps'],7)
        native=[r for r in plan['placements']]
        self.assertEqual({r['stamp'] for r in native},{s['key'] for s in stamps})
        for row in native:
            x,y,w,h=row['component_global_rect']
            self.assertEqual([w,h],[3,3])
            self.assertEqual(row['stamp_offset'],[x-row['origin'][0],y-row['origin'][1]])
            self.assertGreaterEqual(row['stamp_offset'][0],9)
            self.assertGreaterEqual(row['stamp_offset'][1],9)
        self.assertFalse(plan['source_routing_proven'])

    def test_blocked_whole_reef_can_border_water_without_a_fictitious_wet_core(self):
        stamp=self.stamp('OldSea:000');stamp.update(words=[0x15f9]*9,native_water_runs=[],
                                                   core_cells=[[x,y] for y in range(3) for x in range(3)])
        stamp['stamp_sha256']=_json_digest({k:v for k,v in stamp.items() if k!='stamp_sha256'})
        plan=pack_grouped_scenery(Inputs(),self.truth,dict(stamps=[stamp]),self.pixels)
        self.assertTrue(plan['complete'])
        self.assertEqual(plan['placements'][0]['source_rect'],[2,4,3,3])
        self.assertEqual(stamp['words'],[0x15f9]*9)

    def test_native_water_fringe_requires_each_real_source_cell_and_keeps_full_word(self):
        stamp=self.stamp('OldSea:000')
        plan=pack_grouped_scenery(Inputs(),self.truth,dict(stamps=[stamp]),self.pixels)
        class FringeInputs(Inputs):
            def layout(self,name):return dict(width=10,height=10)
            def water(self,name,x,y):return (x,y)!=(1,3)
            def word(self,name,x,y):return 0x0170 if x==1 else 0x1170
        result=preserve_native_water_collars(FringeInputs(),dict(stamps=[stamp]),plan)
        witness=result['native_water_collar_witnesses'][0]
        self.assertEqual(len(witness['cells']),15)
        self.assertNotIn([1,3],[c['source_tile'] for c in witness['cells']])
        self.assertIn(0x0170,[c['word'] for c in witness['cells']])
        self.assertEqual(plan.get('native_water_collar_cells'),None)


if __name__=='__main__':unittest.main()
