"""Native exclusions require actual complete terrain, not GPS or a label."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from atlas_surf_classification import (classify_registered_native,
    regional_art_evidence, registered_water)
from atlas_surf_truth import AtlasTruth


def atlas(points):
    values = [1]*(224*112)
    for x,y in points:
        values[y*224+x] = 2
    return AtlasTruth(tuple(values),tuple(range(16)),{},'fixture')


class Terrain:
    def __init__(self,width=8,height=8,word=0x1111):
        self.maps = {'Coast':dict(id='MAP_COAST',connections=[])}
        self.by_id = {'MAP_COAST':'Coast'}
        self.width,self.height,self.tileword = width,height,word
        self.cells = [(x,y) for y in range(height) for x in range(width)]
        self.reads = []

    def layout(self,name):
        return dict(width=self.width,height=self.height)

    def water_components(self,name):
        return {p:0 for p in self.cells},[self.cells]

    def word(self,name,x,y):
        return self.tileword

    def water(self,name,x,y):
        return (x,y) in self.cells

    def read(self,name):
        self.reads.append(name)
        return b'fixture source atlas, no player GPS'

    def assert_unchanged(self):
        return 1


class PhysicalNativeClassification(unittest.TestCase):
    def setUp(self):
        self.source = Terrain()
        self.registration = dict(native_map='Coast',native_tile=[0,2],
            global_tile=[8,10],direction='left',component=0,
            local_rect=[0,0,8,8],atlas_evidence={'kind':'explicit test registration'})
        self.truth = atlas([(1,1)])

    def classify(self, registrations=None):
        with patch('atlas_surf_classification.decode_atlas',return_value=self.truth):
            return classify_registered_native(self.source,registrations or [self.registration])

    def test_full_six_by_six_native_water_core_excludes_exactly_one_pixel(self):
        report = self.classify()
        self.assertEqual(report['native_pixels'],[[1,1]])
        self.assertEqual(report['counts']['generated'],0)
        self.assertEqual(len(report['native_witnesses'][0]['witnesses']),36)
        self.assertFalse(report['old_player_gps_used'])
        self.assertFalse(report['registration_geography_independently_certified'])
        self.assertFalse(report['final_release_validated'])
        self.assertNotIn('src/data/journey_world_position.h',self.source.reads)

    def test_half_native_pixel_remains_generated_and_reports_the_missing_cells(self):
        self.registration['local_rect'] = [0,0,4,8]
        report = self.classify()
        self.assertEqual(report['native_pixels'],[])
        self.assertEqual(report['generated_pixels'],[[1,1]])
        partial = report['partial_native_pixel_coverage'][0]
        self.assertEqual(partial['native_cells'],18)
        self.assertEqual(len(partial['missing_global_cells']),18)
        self.assertTrue(report['partial_pixels_require_exclusive_game_tile_ownership'])

    def test_water_at_native_land_height_cannot_silently_certify_a_surf_core(self):
        self.source.tileword = 0x3111
        report = self.classify()
        self.assertEqual(report['native_pixels'],[])
        self.assertEqual(len(report['incompatible_native_water_heights']),1)

    def test_single_water_witness_cannot_exclude_the_whole_pixel(self):
        self.source.cells = [(1,1)]
        self.registration = dict(map='Coast',origin=[8,8],components=[0],
                                 registration_evidence='single physical tile, deliberately insufficient')
        report = self.classify()
        self.assertEqual(report['native_pixels'],[])
        self.assertEqual(report['partial_native_pixel_coverage'][0]['native_cells'],1)

    def test_registration_needs_source_evidence(self):
        self.registration.pop('atlas_evidence')
        with self.assertRaisesRegex(ValueError,'explicit authored evidence'):
            self.classify()

    def test_interface_witness_must_be_on_its_actual_named_side(self):
        self.registration['direction'] = 'right'
        with self.assertRaisesRegex(ValueError,'stated native boundary'):
            self.classify()

    def test_interface_witness_must_be_on_its_component(self):
        self.registration['component'] = 1
        with self.assertRaisesRegex(ValueError,'Unknown native water component'):
            self.classify()

    def test_patch_cannot_claim_terrain_outside_the_original_map(self):
        self.registration['local_rect'][2] = 9
        with self.assertRaisesRegex(ValueError,'exceeds original terrain'):
            self.classify()

    def test_registered_frames_do_not_impose_a_global_embedding_on_all_native_maps(self):
        first = dict(self.registration,name='first')
        second = dict(self.registration,name='another-local-interface',global_tile=[80,10])
        water,rows,seams = registered_water(self.source,[first,second])
        self.assertEqual(len(rows),2)
        self.assertEqual(len(water),128)
        self.assertEqual(seams,[])

    def test_two_different_native_cells_cannot_own_the_same_global_cell(self):
        first = dict(self.registration,name='first')
        second = dict(self.registration,name='second',global_tile=[9,10])
        with self.assertRaisesRegex(ValueError,'reservations overlap'):
            registered_water(self.source,[first,second])

    def test_duplicate_evidence_for_the_same_physical_cell_is_not_a_second_ocean(self):
        water,rows,seams = registered_water(self.source,[dict(self.registration,name='first'),
                                                      dict(self.registration,name='second')])
        self.assertEqual(len(water),64)


class AuthenticatedRegionalProvenance(unittest.TestCase):
    def test_regional_blue_provenance_is_bound_to_the_original_asset_hash(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root/'web/atlas/hoenn.png'
            path.parent.mkdir(parents=True)
            im = Image.new('RGB',(32,32),(112,184,232))
            im.putpixel((1,1),(48,104,176))
            im.save(path)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            source = Terrain()
            source.js = lambda name: dict(panels={'hoenn':[0,0,32,32]},
                asset_sha256={'web/atlas/hoenn.png':digest})
            with patch('atlas_surf_classification.decode_atlas',return_value=atlas([(1,1)])):
                report = regional_art_evidence(source,root)
                self.assertEqual(report['surviving_native_art_blue_pixels'],[[1,1]])
                self.assertFalse(report['physical_native_ownership_proven'])
                path.write_bytes(path.read_bytes()+b'changed')
                with self.assertRaisesRegex(ValueError,'authenticated parent'):
                    regional_art_evidence(source,root)


if __name__ == '__main__':
    unittest.main()
