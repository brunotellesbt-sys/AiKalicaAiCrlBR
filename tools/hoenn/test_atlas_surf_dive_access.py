"""A Dive approach crosses the actual glyph margin and never a native coast."""
import gzip
import json
from pathlib import Path
import unittest
from atlas_surf_dive_access import attach_accesses
from atlas_surf_geometry import rasterize
from atlas_surf_truth import read_atlas


ROOT=Path(__file__).resolve().parents[2]


@unittest.skipUnless((ROOT/'.local/generated-area-review-src/src/data/journey_world_map.h').exists(),
                     'Native171 atlas source required')
class ActualDiveAccessTests(unittest.TestCase):
    def test_all_fixed_glyph_approaches_connect_and_origens_avoids_land_below(self):
        truth=read_atlas(ROOT/'.local/generated-area-review-src')
        plan=json.loads(gzip.decompress((ROOT/'docs/design/atlas-surf-layout/whole-scenery-native-exclusive-source.json.gz').read_bytes()))
        rows=attach_accesses(truth,plan['dive_features']['reservations'],truth.blue_pixels-{(96,40)})
        water=rasterize(truth.blue_pixels-{(96,40)})
        self.assertEqual(len(rows),5)
        for row in rows:
            proof=row['native_water_evidence']['authenticated_approach'];site=row['dive_site']
            path=list(map(tuple,proof['path_global_tiles']))
            self.assertIn(path[-1],water)
            self.assertLessEqual(len(path),24)
            self.assertTrue(all(abs(a[0]-b[0])+abs(a[1]-b[1])==1 for a,b in zip(path,path[1:])))
            allowed={tuple(r['atlas']) for r in proof['glyph_pixels']}
            for x,y in proof['painted_cells']:
                self.assertTrue((x//8,y//8) in allowed or truth.pixel((x//8,y//8)) in (1,2))
            if site['name']=='Origens':
                self.assertEqual(truth.pixel((site['atlas'][0],site['atlas'][1]+1)),4)
                self.assertLess(path[-1][1],path[0][1])
        self.assertTrue(all('authenticated_approach' not in row['evidence']
                            for row in plan['dive_features']['reservations']))


if __name__=='__main__':unittest.main()
