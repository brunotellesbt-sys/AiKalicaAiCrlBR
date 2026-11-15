"""Whole reservations, exact route coverage and physical seam regressions."""
from copy import deepcopy
import random
import unittest

from atlas_surf_geometry import chunk_water
from atlas_surf_plan import plan_reserved_geometry


def independent_corridor(pixels):
    result=set()
    for x,y in pixels:
        for yy in range(8*y+1,8*y+7):
            for xx in range(8*x+1,8*x+7):result.add((xx,yy))
        if (x+1,y) in pixels:
            result.update((xx,yy) for xx in (8*x+7,8*x+8) for yy in range(8*y+1,8*y+7))
        if (x,y+1) in pixels:
            result.update((xx,yy) for yy in (8*y+7,8*y+8) for xx in range(8*x+1,8*x+7))
    return result


class ReservedGeometryTests(unittest.TestCase):
    def cells(self,plan):
        result={}
        for chunk in plan['chunks']:
            ox,oy=chunk['origin']
            for x,y in chunk_water(chunk):
                self.assertNotIn((ox+x,oy+y),result)
                result[ox+x,oy+y]=chunk['name']
        return result

    def assert_rectangles_and_seams(self,plan):
        lookup={row['id']:row for row in plan['chunks']}
        for i,a in enumerate(plan['chunks']):
            ax,ay=a['origin']
            self.assertLess(a['number'],100)
            self.assertLessEqual(max(a['width'],a['height']),127)
            for b in plan['chunks'][i+1:]:
                bx,by=b['origin']
                self.assertFalse(max(ax,bx)<min(ax+a['width'],bx+b['width'])
                                 and max(ay,by)<min(ay+a['height'],by+b['height']))
            for c in a['connections']:
                b=lookup[c['map']];bx,by=b['origin']
                reverse={'left':'right','right':'left','up':'down','down':'up'}[c['direction']]
                self.assertIn(dict(direction=reverse,map=a['id'],offset=-c['offset']),b['connections'])
                if c['direction']=='right':self.assertEqual(ax+a['width'],bx)
                elif c['direction']=='left':self.assertEqual(bx+b['width'],ax)
                elif c['direction']=='down':self.assertEqual(ay+a['height'],by)
                else:self.assertEqual(by+b['height'],ay)
                self.assertEqual(c['offset'],by-ay if c['direction'] in ('left','right') else bx-ax)

    def test_complete_large_reservation_crosses_storage_boundaries_without_cutting(self):
        pixels={(x,0) for x in range(12)}
        reserve=dict(name='Cave',origin=[28,-7],width=40,height=23,kind='cave',
                     evidence=dict(source='authenticated fixture'))
        plan=plan_reserved_geometry(pixels,[reserve])
        cave=next(c for c in plan['chunks'] if c['name']=='Cave')
        self.assertEqual((cave['origin'],cave['width'],cave['height']),([28,-7],40,23))
        self.assertEqual(set(self.cells(plan)),independent_corridor(pixels))
        self.assert_rectangles_and_seams(plan)
        self.assertFalse(plan['source_certified'])

    def test_sweep_random_nonoverlapping_reservations_preserves_every_tile(self):
        rng=random.Random(172)
        pixels={(x,y) for y in range(4) for x in range(16)}
        for _ in range(30):
            reserve=[]
            for i in range(4):
                reserve.append(dict(name='Object'+str(i),origin=[i*32+rng.randrange(0,8),rng.randrange(0,12)],
                                    width=rng.randrange(4,20),height=rng.randrange(4,20),
                                    kind='stamp',evidence=dict(source='fixture')))
            plan=plan_reserved_geometry(pixels,reserve)
            self.assertEqual(set(self.cells(plan)),independent_corridor(pixels))
            self.assert_rectangles_and_seams(plan)

    def test_native_dry_terrain_is_never_declared_water(self):
        pixels={(0,0),(1,0)}
        reserve=dict(name='Landing',origin=[4,0],width=4,height=8,kind='port',
                     evidence=dict(source='fixture'),reserved_water_policy='native',
                     water_runs=[[1,0,4],[2,0,4]],native_water_evidence=dict(donor='native footprint'))
        with self.assertRaisesRegex(ValueError,'obstructs the six-tile route'):
            plan_reserved_geometry(pixels,[reserve])
        reserve['route_obstruction_evidence']=dict(native_beach_endpoint=True)
        plan=plan_reserved_geometry(pixels,[reserve])
        cells=self.cells(plan)
        self.assertNotIn((5,3),cells)
        self.assertIn((5,2),cells)
        self.assertGreater(plan['route_water_replaced_by_authenticated_native_terrain'],0)
        self.assert_rectangles_and_seams(plan)

    def test_dry_reservation_stays_complete_and_has_real_face_connection(self):
        reserve=dict(name='Cave',origin=[16,0],width=8,height=8,kind='cave',evidence=dict(parent='native'),
                     reserved_water_policy='native',water_runs=[],native_water_evidence=dict(native=True))
        plan=plan_reserved_geometry([(1,0)],[reserve])
        cave=next(c for c in plan['chunks'] if c['name']=='Cave')
        self.assertFalse(cave['water_runs'])
        self.assertTrue(any(c['direction']=='left' for c in cave['connections']))
        self.assert_rectangles_and_seams(plan)

    def test_extra_water_requires_native_footprint_and_fits_reservation(self):
        row=dict(name='Dive',origin=[0,0],width=8,height=8,kind='dive',evidence=dict(icon='fixed'),
                 additional_water_runs=[[0,0,2]])
        with self.assertRaisesRegex(ValueError,'authenticated native footprint'):
            plan_reserved_geometry([(0,0)],[row])
        row['native_water_evidence']=dict(dive_icon=True)
        plan=plan_reserved_geometry([(0,0)],[row])
        self.assertEqual(plan['reserved_additional_water_tiles'],2)
        bad=deepcopy(row);bad['additional_water_runs']=[[8,0,2]]
        with self.assertRaisesRegex(ValueError,'outside'):
            plan_reserved_geometry([(0,0)],[bad])

    def test_overlaps_and_invalid_evidence_or_signed_bounds_fail_closed(self):
        row=dict(name='Native',origin=[0,0],width=8,height=8,kind='stamp',evidence=dict(parent='native'))
        with self.assertRaisesRegex(ValueError,'overlap'):
            plan_reserved_geometry([(0,0)],[row,dict(row,origin=[7,0],name='Other')])
        for change in [dict(width=128),dict(width=127,height=127),dict(kind='unknown'),dict(evidence=None),dict(origin=[32767,0])]:
            with self.assertRaises(ValueError):plan_reserved_geometry([(0,0)],[dict(row,**change)])

    def test_native_patch_is_excluded_from_rectangles_not_only_from_water(self):
        native=dict(native_map='NativeCoast',origin=[0,0],local_rect=[9,0,17,8],
                    global_rect=[9,0,17,8],evidence=dict(registered_component='source-witness'))
        plan=plan_reserved_geometry([(x,0) for x in range(4)],native_regions=[native])
        self.assertGreater(plan['route_raster_cells_owned_by_registered_native_terrain'],0)
        for row in plan['chunks']:
            x,y=row['origin'];r,b=x+row['width'],y+row['height']
            self.assertFalse(max(x,9)<min(r,17) and max(y,0)<min(b,8))
        expected=independent_corridor({(x,0) for x in range(4)})
        expected={p for p in expected if not (9<=p[0]<17 and 0<=p[1]<8)}
        actual={(row['origin'][0]+x,row['origin'][1]+y)
                for row in plan['chunks'] for y,a,b in row['water_runs'] for x in range(a,b)}
        self.assertEqual(actual,expected)

    def test_native_registration_mismatch_or_generated_overlap_is_rejected(self):
        native=dict(native_map='NativeCoast',origin=[0,0],local_rect=[8,0,16,8],
                    global_rect=[8,0,16,8],evidence=dict(registered_component='source-witness'))
        row=dict(name='Scene',origin=[7,0],width=8,height=8,kind='stamp',evidence=dict(parent='native'))
        with self.assertRaisesRegex(ValueError,'registered native terrain'):
            plan_reserved_geometry([(0,0),(1,0)],[row],native_regions=[native])
        changed=dict(native,global_rect=[9,0,17,8])
        with self.assertRaisesRegex(ValueError,'local registration'):
            plan_reserved_geometry([(0,0)],native_regions=[changed])
        overlapping=dict(native,origin=[1,0],global_rect=[9,0,17,8])
        with self.assertRaisesRegex(ValueError,'native terrain owners overlap'):
            plan_reserved_geometry([(0,0)],native_regions=[native,overlapping])
        touching=dict(native,origin=[8,0],global_rect=[16,0,24,8])
        plan_reserved_geometry([(x,0) for x in range(4)],native_regions=[native,touching])


if __name__=='__main__':
    unittest.main()
