"""Reject source-network gaps that a plausible map/GPS diagram cannot prove."""
import copy
import unittest

from atlas_surf_reachability import audit, elevation_step


class Terrain:
    behavior_names = {0: 'MB_NORMAL', 1: 'MB_OCEAN_WATER', 2: 'MB_NON_ANIMATED_DOOR',
                      3: 'MB_DEEP_WATER', 4: 'MB_NO_SURFACING', 5: 'MB_IMPASSABLE_EAST'}

    def __init__(self):
        self.maps, self.layouts, self.tiles, self.by_id, self.inputs = {}, {}, {}, {}, {}

    def add(self, name, width=3, height=3, word=0x1001):
        self.maps[name] = dict(id='MAP_' + name.upper(), layout=name, map_type='MAP_TYPE_OCEAN_ROUTE',
                               connections=[], warp_events=[])
        self.by_id['MAP_' + name.upper()] = name
        self.layouts[name] = dict(width=width, height=height, primary_tileset='General',
                                  secondary_tileset='Sea', layout_version='frlg')
        self.tiles[name] = [word] * (width * height)

    def layout(self, name):
        return self.layouts[name]

    def word(self, name, x, y):
        row = self.layout(name)
        if not 0 <= x < row['width'] or not 0 <= y < row['height']:
            raise ValueError('outside actual terrain')
        return self.tiles[name][y * row['width'] + x]

    def set(self, name, x, y, word):
        self.tiles[name][y * self.layout(name)['width'] + x] = word

    def behavior(self, name, word):
        return word & 1023

    def water(self, name, x, y):
        word = self.word(name, x, y)
        return not word & 0xC00 and self.behavior(name, word) in (1, 3, 4)

    def connect(self, first, second, direction='right', offset=0, reciprocal=True):
        reverse = dict(left='right', right='left', up='down', down='up')
        self.maps[first]['connections'].append(dict(direction=direction, offset=offset,
                                                   map=self.maps[second]['id']))
        if reciprocal:
            self.maps[second]['connections'].append(dict(direction=reverse[direction], offset=-offset,
                                                        map=self.maps[first]['id']))


class PhysicalReachability(unittest.TestCase):
    def fixture(self):
        source = Terrain()
        source.add('A')
        source.add('B')
        source.connect('A', 'B')
        plan = dict(chunks=[dict(name='A', origin=[0, 0], connections=[]),
                            dict(name='B', origin=[3, 0], connections=[])])
        requirements = dict(complete=True, ports=[], caves=[], dives=[], adapters=[], native_pixels=[])
        return source, plan, requirements

    def run_audit(self, fixture):
        source, plan, requirements = fixture
        return audit(source, plan=plan, requirements=requirements)

    def test_actual_cardinal_terrain_forms_one_scc(self):
        result = self.run_audit(self.fixture())
        self.assertTrue(result['passed'], result)
        self.assertEqual(result['generated_water_sccs'], 1)
        self.assertEqual(result['generated_water_cells'], 18)
        self.assertFalse(result['compiled_rom_validated'])
        self.assertFalse(result['gps_used_for_edges'])

    def test_high_water_cannot_join_height_one_by_metadata(self):
        source, plan, requirements = self.fixture()
        source.tiles['B'] = [0x3001] * 9
        result = audit(source, plan=plan, requirements=requirements)
        self.assertFalse(result['passed'])
        self.assertEqual(result['generated_water_sccs'], 2)

    def test_bridge_fifteen_keeps_elevation_transition_zero_can_change_it(self):
        self.assertEqual(elevation_step(1, 0x1001, 0xF001), 1)
        self.assertIsNone(elevation_step(1, 0xF001, 0x3001))
        self.assertEqual(elevation_step(1, 0x1001, 0x0000), 0)
        self.assertEqual(elevation_step(0, 0x0000, 0x3000), 3)

    def test_one_way_connection_is_not_a_roundtrip(self):
        source, plan, requirements = self.fixture()
        source.maps['B']['connections'].clear()
        result = audit(source, plan=plan, requirements=requirements)
        self.assertFalse(result['passed'])
        self.assertIn('nonreciprocal-connection', {row['kind'] for row in result['errors']})

    def test_wrong_reciprocal_offset_and_nonoverlapping_offsets_fail(self):
        for offset in (1, 20):
            source, plan, requirements = self.fixture()
            source.maps['B']['connections'][0]['offset'] = offset
            result = audit(source, plan=plan, requirements=requirements)
            self.assertFalse(result['passed'])
        source, plan, requirements = self.fixture()
        source.maps['A']['connections'][0]['offset'] = 20
        source.maps['B']['connections'][0]['offset'] = -20
        self.assertEqual(audit(source, plan=plan, requirements=requirements)['generated_water_sccs'], 2)

    def test_plan_edges_gps_and_identical_atlas_coordinates_cannot_invent_connection(self):
        source, plan, requirements = self.fixture()
        for name in source.maps:
            source.maps[name]['connections'].clear()
        plan['chunks'][0].update(connections=[dict(map='MAP_B', direction='right', offset=0)], gps=[9, 9])
        plan['chunks'][1].update(origin=plan['chunks'][0]['origin'], gps=[9, 9])
        result = audit(source, plan=plan, requirements=requirements)
        self.assertFalse(result['passed'])
        self.assertEqual(result['generated_water_sccs'], 2)

    def test_port_requires_dry_height_three_and_return_to_surf(self):
        source, plan, requirements = self.fixture()
        source.set('A', 0, 0, 0x3000)
        requirements['ports'] = [dict(key='Pier', dry=['A', 0, 0], water=['A', 1, 0])]
        self.assertTrue(audit(source, plan=plan, requirements=requirements)['passed'])
        source.set('A', 0, 0, 0x0000)
        self.assertFalse(audit(source, plan=plan, requirements=requirements)['passed'])

    def test_passable_cave_interior_height_zero_is_valid_and_warps_are_directed(self):
        source, plan, requirements = self.fixture()
        source.add('Cave', 2, 2, 0x0000)
        source.set('A', 0, 0, 0x3002)
        source.set('Cave', 0, 0, 0x0002)
        source.maps['A']['warp_events'] = [dict(x=0, y=0, dest_map='MAP_CAVE', dest_warp_id='0')]
        source.maps['Cave']['warp_events'] = [dict(x=0, y=0, dest_map='MAP_A', dest_warp_id='0')]
        requirements['caves'] = [dict(key='Cave', surface='A', surface_warp=0,
                                       interior='Cave', interior_warp=0)]
        result = audit(source, plan=plan, requirements=requirements)
        self.assertTrue(result['passed'], result)
        source.maps['Cave']['warp_events'][0]['dest_map'] = 'MAP_B'
        self.assertFalse(audit(source, plan=plan, requirements=requirements)['passed'])

    def test_dive_keeps_coordinates_and_needs_reciprocal_native_links(self):
        source, plan, requirements = self.fixture()
        source.add('Depth', 3, 3, 0x0000)
        source.maps['Depth']['map_type'] = 'MAP_TYPE_UNDERWATER'
        source.set('A', 1, 1, 0x1003)
        source.maps['A']['connections'].append(dict(direction='dive', map='MAP_DEPTH', offset=0))
        source.maps['Depth']['connections'].append(dict(direction='emerge', map='MAP_A', offset=0))
        requirements['dives'] = [dict(key='Deep', surface='A', depth='Depth', points=[[1, 1]])]
        self.assertTrue(audit(source, plan=plan, requirements=requirements)['passed'])
        source.set('Depth', 1, 1, 0x0C00)
        result = audit(source, plan=plan, requirements=requirements)
        self.assertFalse(result['passed'])
        self.assertIn('dive-terrain-blocked', {row['kind'] for row in result['errors']})
        source.set('Depth', 1, 1, 0x0000)
        source.maps['Depth']['connections'][0]['offset'] = 1
        self.assertFalse(audit(source, plan=plan, requirements=requirements)['passed'])

    def test_native_pixel_requires_physical_coordinate_binding_not_gps(self):
        source, plan, requirements = self.fixture()
        requirements['native_pixels'] = [dict(key='Ink', point=['B', 1, 1],
                                              atlas=[0, 0], authenticated=True)]
        self.assertTrue(audit(source, plan=plan, requirements=requirements)['passed'])
        requirements['native_pixels'][0]['atlas'] = [99, 50]
        self.assertFalse(audit(source, plan=plan, requirements=requirements)['passed'])

    def test_reciprocal_offset_with_wrong_affine_distance_still_fails(self):
        source, plan, requirements = self.fixture()
        source.maps['A']['connections'][0]['offset'] = 1
        source.maps['B']['connections'][0]['offset'] = -1
        result = audit(source, plan=plan, requirements=requirements)
        self.assertIn('nonaffine-physical-connection', {row['kind'] for row in result['errors']})

    def test_blocking_whole_chunk_cannot_disappear_from_coverage(self):
        source, plan, requirements = self.fixture()
        source.tiles['B'] = [0x1C01] * 9
        result = audit(source, plan=plan, requirements=requirements)
        self.assertIn('generated-chunk-has-no-physical-water', {row['kind'] for row in result['errors']})

    def test_no_surfacing_floor_cannot_be_given_an_emerge_edge(self):
        source, plan, requirements = self.fixture()
        source.add('Depth', 3, 3, 0x0000)
        source.maps['Depth']['map_type'] = 'MAP_TYPE_UNDERWATER'
        source.set('A', 1, 1, 0x1003)
        source.set('Depth', 1, 1, 0x1004)
        source.maps['A']['connections'].append(dict(direction='dive', map='MAP_DEPTH', offset=0))
        source.maps['Depth']['connections'].append(dict(direction='emerge', map='MAP_A', offset=0))
        requirements['dives'] = [dict(key='Deep', surface='A', depth='Depth', points=[[1, 1]])]
        result = audit(source, plan=plan, requirements=requirements)
        self.assertIn('emerge-behavior-blocked', {row['kind'] for row in result['errors']})

    def test_warp_event_elevation_cannot_override_terrain_elevation(self):
        source, plan, requirements = self.fixture()
        source.add('Cave', 2, 2, 0x3000)
        source.set('A', 0, 0, 0x3002)
        source.set('Cave', 0, 0, 0x3002)
        source.maps['A']['warp_events'] = [dict(x=0, y=0, elevation=1, dest_map='MAP_CAVE', dest_warp_id='0')]
        source.maps['Cave']['warp_events'] = [dict(x=0, y=0, elevation=3, dest_map='MAP_A', dest_warp_id='0')]
        requirements['caves'] = [dict(key='Cave', surface='A', surface_warp=0,
                                       interior='Cave', interior_warp=0)]
        result = audit(source, plan=plan, requirements=requirements)
        self.assertFalse(result['passed'])

    def test_collision_and_bank_mismatch_are_real_not_just_route_ink(self):
        source, plan, requirements = self.fixture()
        for y in range(3):
            source.set('B', 0, y, 0x1C01)
        self.assertFalse(audit(source, plan=plan, requirements=requirements)['passed'])
        source, plan, requirements = self.fixture()
        source.layouts['B']['secondary_tileset'] = 'UnrelatedBank'
        result = audit(source, plan=plan, requirements=requirements)
        self.assertFalse(result['passed'])
        self.assertIn('bank-translation-unproven', {row['kind'] for row in result['pending']})

    def test_missing_final_destinations_and_unauthenticated_native_pixels_stay_pending(self):
        source, plan, requirements = self.fixture()
        requirements['ports'] = [dict(key='unassigned')]
        requirements['native_pixels'] = [dict(key='pixel', point=['A', 1, 1], atlas=[4, 5])]
        result = audit(source, plan=plan, requirements=requirements)
        self.assertFalse(result['passed'])
        self.assertEqual({row['kind'] for row in result['pending']},
                         {'final-port-mapping-missing', 'native-pixel-not-authenticated'})
        with self.assertRaises(AssertionError):
            audit(source, plan=plan, requirements=requirements, strict=True)

    def test_state_budget_is_enforced(self):
        source, plan, requirements = self.fixture()
        with self.assertRaisesRegex(ValueError, 'budget exceeded'):
            audit(source, plan=plan, requirements=requirements, max_states=3)


if __name__ == '__main__':
    unittest.main()
