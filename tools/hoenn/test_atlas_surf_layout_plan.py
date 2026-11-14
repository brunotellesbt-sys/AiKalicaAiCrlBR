"""Adversarial checks for the independent atlas plan audit, without the planner."""
import copy
import unittest

from validate_atlas_surf_layout_plan import position, validate_plan


def plan_fixture():
    # Three horizontal atlas pixels form 22x6 tiles, split at global x=32.
    # These runs are handwritten and do not call either raster implementation.
    first = dict(name='A', id='MAP_A', group='Atlas0', number=0,
                 origin=[24, 24], width=8, height=8,
                 water_runs=[[y, 1, 8] for y in range(1, 7)],
                 connections=[dict(direction='right', map='MAP_B', offset=0)])
    second = dict(name='B', id='MAP_B', group='Atlas0', number=1,
                  origin=[32, 24], width=16, height=8,
                  water_runs=[[y, 0, 15] for y in range(1, 7)],
                  connections=[dict(direction='left', map='MAP_A', offset=0)])
    return dict(scale=8, corridor_width=6, chunk_tiles=32, chunks=[first, second])


class IndependentAtlasPlanAudit(unittest.TestCase):
    def setUp(self):
        self.plan = plan_fixture()
        self.routes = [[3, 3], [4, 3], [5, 3]]

    def audit(self, **kwargs):
        return validate_plan(self.plan, route_pixels=self.routes, **kwargs)

    def test_valid_physical_seam_has_file_scope_and_exact_coverage(self):
        report = self.audit(native_pixels=[[10, 10]], icon_pixels=[[11, 10]])
        self.assertTrue(report['passed'])
        self.assertEqual(report['physical_water_cells'], 132)
        self.assertEqual(report['directed_seams'], 2)
        self.assertEqual(report['generated_water_components'], 1)
        self.assertGreater(report['straight_eight_tile_distance_checks'], 0)
        for label in ('source_validated', 'compiled_rom_validated', 'native_controls_validated'):
            self.assertIs(report[label], False)

    def test_north_travel_never_drift_east_and_eight_steps_are_one_pixel(self):
        chunk = dict(origin=[25, 17])
        for x in range(16):
            for y in range(8, 24):
                before = position(chunk, x, y)
                after = position(chunk, x, y-8)
                self.assertEqual(after, (before[0], before[1]-1))

    def test_reference_uses_floor_for_negative_border_coordinates(self):
        self.assertEqual(position(dict(origin=[0, 0]), -1, -1), (-1, -1))

    def test_missing_seam_is_not_hidden_by_overlapping_gps(self):
        self.plan['chunks'][1]['connections'] = []
        with self.assertRaisesRegex(AssertionError, 'physical seams'):
            self.audit()

    def test_seam_cannot_fold_the_world_with_arbitrary_offset(self):
        self.plan['chunks'][0]['connections'][0]['offset'] = 2
        with self.assertRaisesRegex(AssertionError, 'folds or moves'):
            self.audit()

    def test_water_in_an_unclassified_ocean_pixel_is_rejected(self):
        self.plan['chunks'][1]['water_runs'].append([7, 0, 15])
        with self.assertRaisesRegex(AssertionError, 'Physical raster differs'):
            self.audit()

    def test_missing_connector_cell_is_rejected(self):
        self.plan['chunks'][0]['water_runs'][0][2] -= 1
        with self.assertRaisesRegex(AssertionError, 'Physical raster differs'):
            self.audit()

    def test_water_cannot_belong_to_two_generated_maps(self):
        duplicate = copy.deepcopy(self.plan['chunks'][0])
        duplicate.update(name='C', id='MAP_C', number=2)
        self.plan['chunks'].append(duplicate)
        with self.assertRaisesRegex(AssertionError, 'overlap in physical water'):
            self.audit()

    def test_duplicate_water_runs_are_rejected(self):
        self.plan['chunks'][0]['water_runs'].append([1, 2, 4])
        with self.assertRaisesRegex(AssertionError, 'Overlapping water runs'):
            self.audit()

    def test_native_route_cannot_also_be_generated(self):
        with self.assertRaisesRegex(AssertionError, 'classifications overlap'):
            self.audit(native_pixels=[[4, 3]])

    def test_signed_warp_map_number_cannot_overflow(self):
        self.plan['chunks'][1]['number'] = 128
        with self.assertRaisesRegex(AssertionError, 'WarpData-safe'):
            self.audit()

    def test_old_per_cell_interpolation_is_outside_contract(self):
        self.plan['chunks'][0]['gps_interpolation'] = [[137, 55], [157, 44]]
        with self.assertRaisesRegex(AssertionError, 'affine contract'):
            self.audit()

    def test_scale_and_width_cannot_be_weakened_to_match_a_bad_plan(self):
        self.plan['scale'] = 4
        with self.assertRaisesRegex(AssertionError, 'physical scale'):
            self.audit()

    def test_declared_access_has_separate_accounting(self):
        # The third pixel is an explicit access, never an unreported exception.
        self.routes.pop()
        report = self.audit(access_pixels=[[5, 3]])
        self.assertEqual(report['atlas_route_pixels'], 2)
        self.assertEqual(report['access_pixels'], 1)


if __name__ == '__main__':
    unittest.main()
