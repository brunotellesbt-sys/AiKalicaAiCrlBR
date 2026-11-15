"""Native ownership requires exact source terrain; native width can be narrow."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from atlas_surf_classification import (classify_registered_native,
    regional_art_evidence, registered_water, census_native_bounds, _raster_cell)
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
        self.inputs = {}

    def layout(self,name):
        return dict(width=self.width,height=self.height)

    def water_components(self,name):
        return {p:0 for p in self.cells},[self.cells]

    def word(self,name,x,y):
        return self.tileword

    def water(self,name,x,y):
        return (x,y) in self.cells

    def behavior(self,name,word):
        return 1

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
        self.assertEqual(len(report['native_witnesses'][0]['witnesses']),64)
        self.assertFalse(report['old_player_gps_used'])
        self.assertFalse(report['registration_geography_independently_certified'])
        self.assertFalse(report['final_release_validated'])
        self.assertNotIn('src/data/journey_world_position.h',self.source.reads)

    def test_partial_native_pixel_has_mixed_ownership_and_reports_missing_cells(self):
        self.registration['local_rect'] = [0,0,4,8]
        report = self.classify()
        self.assertEqual(report['native_pixels'],[[1,1]])
        self.assertTrue(report['native_pixel_list_is_witness_inventory_not_full_pixel_exclusion'])
        partial = report['partial_native_pixel_coverage'][0]
        self.assertEqual(partial['native_cells'],18)
        self.assertEqual(len(partial['missing_global_cells']),18)
        self.assertTrue(report['partial_pixels_require_exclusive_game_tile_ownership'])

    def test_native_height_three_water_is_preserved_but_requires_movement_proof(self):
        self.source.tileword = 0x3111
        report = self.classify()
        self.assertEqual(report['native_pixels'],[[1,1]])
        self.assertEqual(len(report['native_water_heights_require_runtime_proof']),1)
        self.assertFalse(report['global_scc_return_proven'])

    def test_single_water_witness_does_not_claim_full_generated_pixel_exclusion(self):
        self.source.cells = [(1,1)]
        self.registration = dict(map='Coast',origin=[8,8],components=[0],
                                 registration_evidence='single physical tile, deliberately insufficient')
        report = self.classify()
        self.assertEqual(report['native_pixels'],[[1,1]])
        self.assertTrue(report['native_pixel_list_is_witness_inventory_not_full_pixel_exclusion'])
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


class NativeBoundsCensus(unittest.TestCase):
    def setUp(self):
        self.source = Terrain()
        self.truth = atlas([(1,1),(2,1)])
        self.registration = dict(native_map='Coast',native_tile=[0,2],
            global_tile=[8,10],direction='left',component=0,
            local_rect=[0,0,8,8],atlas_evidence={'test_fixture':True})
        self.report = dict(registrations=[self.registration],adapter_plan=dict(native_bounds=[
            dict(native_map='Coast',component=0,origin=[8,8],
                 local_rect=[0,0,8,8],global_rect=[8,8,16,16])]))

    def census(self):
        with patch('atlas_surf_classification.decode_atlas',return_value=self.truth), \
             patch('atlas_surf_classification._authenticate_registration',return_value={'fixture':True}):
            return census_native_bounds(self.source,self.report)

    def test_native_full_core_and_connector_have_separate_precise_accounting(self):
        result = self.census()
        self.assertEqual(result['fully_native_core_pixels'],[[1,1]])
        self.assertEqual(result['native_core_water_cell_count'],36)
        self.assertEqual(len(result['remove_generated_global_cells']),42)
        self.assertIn([15,10],result['remove_generated_global_cells'])
        self.assertFalse(result['native_scale_8_assumed'])
        self.assertFalse(result['global_scc_return_proven'])
        self.assertFalse(result['six_by_six_native_core_required_for_witness'])

    def test_native_dry_cell_is_still_excluded_from_generated_water(self):
        self.source.cells.remove((2,2))
        result = self.census()
        self.assertEqual(result['native_core_water_cell_count'],35)
        self.assertEqual(result['native_core_nonwater_or_other_component_cell_count'],1)
        self.assertIn([10,10],result['remove_generated_global_cells'])
        self.assertEqual(result['partially_native_core_pixels'],[[1,1]])

    def test_source_coordinate_translation_is_checked_before_any_ownership_claim(self):
        self.report['adapter_plan']['native_bounds'][0]['global_rect'][0] += 1
        with self.assertRaisesRegex(ValueError,'rectangle translation is inconsistent'):
            self.census()

    def test_a_narrow_native_component_remains_a_real_source_witness(self):
        self.source.cells = [(0,y) for y in range(8)]
        result = self.census()
        self.assertEqual(result['native_core_water_cell_count'],0)
        self.assertEqual(result['fully_native_core_pixels'],[])
        self.assertEqual(result['native_candidate_pixels'],[[1,1]])
        self.assertFalse(result['physical_classification_complete'])

    def test_generated_join_never_appears_without_a_four_neighbor(self):
        self.assertTrue(_raster_cell((15,10),{(1,1),(2,1)}))
        self.assertTrue(_raster_cell((16,10),{(1,1),(2,1)}))
        self.assertFalse(_raster_cell((15,10),{(1,1)}))
        self.assertFalse(_raster_cell((15,15),{(1,1),(2,2)}))


if __name__ == '__main__':
    unittest.main()
