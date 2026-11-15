"""Exercise the complete staged source against immutable native revision171."""
import gzip
import json
from pathlib import Path
import unittest

from atlas_surf_overlay import OverlaySource
from atlas_surf_source import Source
from atlas_surf_truth import decode_atlas
from prepare_atlas_surf_layout import ROOT,compose


@unittest.skipUnless((ROOT/'.local/generated-area-review-src/.journey-generated-area-review').is_file(),
                     'Immutable revision171 source is not installed')
class RealStagedLayoutTests(unittest.TestCase):
    def test_all_whole_words_events_dive_banks_and_native_exclusions_survive_composition(self):
        parent=Source(ROOT/'.local/generated-area-review-src')
        layer,report=compose(parent.source);candidate=OverlaySource(layer)
        inventory=json.loads(gzip.decompress((ROOT/'docs/design/atlas-surf-layout/parent-scenery-extraction.json.gz').read_bytes()))
        placements=json.loads(gzip.decompress((ROOT/'docs/design/atlas-surf-layout/whole-scenery-native-exclusive-source.json.gz').read_bytes()))
        stamps={s['key']:s for s in inventory['stamps']}
        for row in placements['placements']:
            stamp=stamps[row['stamp']];layout=candidate.layout(row['name'])
            words=candidate.words(row['name']);sx,sy=row['stamp_offset'];w,h=stamp['source_rect'][2:]
            actual=[words[(sy+y)*layout['width']+sx+x] for y in range(h) for x in range(w)]
            self.assertEqual(actual,stamp['words'],stamp['key'])
        self.assertEqual(len(placements['placements']),374)
        self.assertEqual(len(report['objects']['relocated_events']),74)
        for row in report['objects']['relocated_object_ids']:
            old=parent.maps[row['source_map']]['object_events'][row['source_index']]
            new=candidate.maps[row['target_map']]['object_events'][row['target_index']]
            self.assertEqual(new['native_local_id'],old.get('native_local_id',row['source_index']+1))
        for chunk in report['geometry_plan']['chunks']:
            x,y=chunk['origin'];r,b=x+chunk['width'],y+chunk['height']
            self.assertLessEqual((chunk['width']+15)*(chunk['height']+14),10240)
            for native in report['geometry_plan']['native_regions']:
                a,d,c,e=native['global_rect']
                self.assertFalse(max(x,a)<min(r,c) and max(y,d)<min(b,e))
            if chunk['kind']=='dive':
                layout=candidate.layout(chunk['name'])
                self.assertEqual([layout['primary_tileset'],layout['secondary_tileset']],
                                 ['gTileset_General','gTileset_Mossdeep'])
        old_art=decode_atlas(parent.read('src/data/journey_world_map.h').decode())
        new_art=decode_atlas(candidate.read('src/data/journey_world_map.h').decode())
        self.assertEqual(dict(old_art.array_sha256),dict(new_art.array_sha256))
        self.assertFalse(report['release_eligible']);self.assertFalse(report['native_validated'])
        self.assertFalse(report['NATIVE_CONTRACT_FINALIZED'])
        self.assertTrue(report['pending_obligations'])
        parent.assert_unchanged();candidate.assert_unchanged()


if __name__=='__main__':unittest.main()
