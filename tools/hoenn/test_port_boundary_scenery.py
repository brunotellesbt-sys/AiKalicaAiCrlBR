"""Exercise whole footprints, an authentic connected reef and route guards."""
import copy
import struct
import unittest
from pathlib import Path
from unittest.mock import patch

from port_boundary_scenery import (BEACH, FIVE, FOUR, PORT_MAPS, PURE_WATER_WORDS, REPAIRS,
    SEVEN_FRONT, SEVEN_LIMIT, SIX, SIX_BOARDING, SMALL, VISIBLE_LIMITS, census, check_water_connectivity, repair)

PROTECTION=dict(boarding={(SIX,SIX_BOARDING)},boats=set(),report=dict(boarding_water=[],boat_footprints=[]))


class Layer:
    source = Path('/tmp/port-scenery-unit-fixture')

    def __init__(self):
        self.outputs = {}

    def stage(self, path, raw):
        self.outputs[path] = raw


class FixtureTerrain:
    def __init__(self):
        self.maps, self.layouts, self.blocks = {}, {}, {}
        for name in (*PORT_MAPS, 'OneIsland_KindleRoad_Frlg'):
            width, height = {BEACH:(40, 48), FOUR:(48, 40), FIVE:(24, 20),
                             'OneIsland_Frlg':(24, 20),
                             'ThreeIsland_Port_Frlg':(45,20), SIX:(24,30),
                             'OneIsland_KindleRoad_Frlg':(24, 140)}.get(name, (24, 40))
            self.maps[name] = dict(layout=name)
            self.layouts[name] = dict(width=width, height=height,
                layout_version='frlg', primary_tileset='gTileset_JourneySeviiSea',
                blockdata_filepath=name+'.bin')
            self.blocks[name+'.bin'] = [0x112B]*(width*height)
            for x, y, direction, xx, yy in self.perimeter(name):
                self.blocks[name+'.bin'][y*width+x] = 0x1643
        for name,cells in VISIBLE_LIMITS.items():
            width=self.layout(name)['width']
            for x,y in cells:self.grid(name)[y*width+x]=0x0676 if name==SEVEN_FRONT else 0x1673
        for x,y in SEVEN_LIMIT:self.grid(SEVEN_FRONT)[y*24+x]=0x1273
        self.grid(SIX)[29*24+2]=0x1673
        self.primary = [0]*(1024*8)
        self.primary[0x273*8:0x274*8] = PURE_WATER_WORDS
        self.primary[0x276*8:0x277*8] = PURE_WATER_WORDS
        self.primary[SMALL*8:(SMALL+1)*8] = (*PURE_WATER_WORDS[:4], 0x41E2, 0x41E3, 0x41E4, 0x41E5)
        self.renderer = type('Renderer', (), {'tileset':lambda renderer, name:(None, None, self.primary)})()
        native = [(0x05CB, 0x112B, 0x05D3, 0x05D4),
                  (0x1244, 0x1245, 0x124C, 0x071A),
                  (0x1273, 0x1245, 0x1673, 0x1273),
                  (0x11CB, 0x11CC, 0x112B, 0x112B)]
        for case, words in zip(REPAIRS, native):
            width = self.layout(case['map'])['width']
            x, y = case['anchor']
            for q, word in enumerate(words):
                self.grid(case['map'])[(y+q//2)*width+x+q%2] = word
        self.grid('OneIsland_KindleRoad_Frlg')[19*24+23] = 0x1643
        self.grid(FOUR)[36*48+8] = 0x1273

    def layout(self, name):
        return self.layouts[self.maps[name]['layout']]

    def grid(self, name):
        return self.blocks[self.layout(name)['blockdata_filepath']]

    def water(self, name, word):
        return word & 1023 != 0x31A

    def perimeter(self, name):
        width, height = (self.layout(name)[key] for key in ('width', 'height'))
        for x in range(width):
            yield x, 0, 'up', x, -1
            yield x, height-1, 'down', x, height
        for y in range(height):
            yield 0, y, 'left', -1, y
            yield width-1, y, 'right', width, y

    def neighbor(self, name, x, y, direction):
        if name == BEACH and direction == 'up' and 8 <= x < 32:
            return 'OneIsland_Frlg', x-8, y+20
        if name == 'OneIsland_Frlg' and direction == 'down':
            return BEACH, x+8, y-20
        return None


class PortSceneryTests(unittest.TestCase):
    def setUp(self):
        protected=patch('port_boundary_scenery.protected_port_cells',return_value=copy.deepcopy(PROTECTION))
        protected.start();self.addCleanup(protected.stop)

    def test_atomic_whole_object_repair_preserves_openings_roof_and_other_cells(self):
        terrain, layer = FixtureTerrain(), Layer()
        original = copy.deepcopy(terrain.blocks)
        with patch('port_boundary_scenery.Terrain', return_value=terrain):
            report = repair(layer)
        self.assertEqual(report['changed_art_cells'], 9)
        self.assertEqual(report['newly_blocked_cells'], 2)
        self.assertEqual(len(layer.outputs), 6)
        self.assertFalse(report['census_after']['incomplete'])
        expected = {(case['map'], (case['anchor'][0]+q%2, case['anchor'][1]+q//2)):
                    (case['target'], case['block']) for case in REPAIRS for q in case['quarters']}
        expected.update({(name,cell):(SMALL,True) for name,cells in VISIBLE_LIMITS.items() for cell in cells})
        expected[SIX,SIX_BOARDING]=(0x273,False)
        for name in (BEACH, FOUR, FIVE, SEVEN_FRONT,SIX,'ThreeIsland_Port_Frlg'):
            width = terrain.layout(name)['width']
            path = terrain.layout(name)['blockdata_filepath']
            before = original[path]
            after = struct.unpack('<'+'H'*len(before), layer.outputs[path])
            for i, (a, b) in enumerate(zip(before, after)):
                self.assertEqual(a >> 12, b >> 12)
                target = expected.get((name, (i%width, i//width)))
                if target is None:
                    self.assertEqual(a, b)
                else:
                    self.assertEqual(b & 1023, target[0])
                    self.assertEqual(b & 0xC00,0 if (name,(i%width,i//width))==(SIX,SIX_BOARDING) else 0x400 if target[1] else a & 0xC00)
        self.assertEqual(terrain.grid(BEACH)[7*40+20], 0x112B)
        self.assertEqual(terrain.grid(FOUR)[28*48+2], 0x071A)
        self.assertEqual(report['outer_limit_census_before']['unsealed_water_cells'], 7)
        self.assertEqual(report['outer_limit_census_after']['unsealed_water_cells'], 0)
        self.assertEqual(report['visible_actual_outer_limits']['changed_art_cells'],53)
        self.assertEqual(report['outer_limit_census_after']['invisible_pure_water_limits'],0)

    def test_incomplete_neighbor_is_rejected_but_real_seam_object_is_complete(self):
        terrain = FixtureTerrain()
        terrain.grid('OneIsland_Frlg')[19*24+2:19*24+4] = [0x11CB, 0x11CC]
        terrain.grid(BEACH)[10:12] = [0x05D3, 0x05D4]
        rows = census(terrain)['objects']
        joined = [row for row in rows if row['map'] == BEACH and row['anchor'] == [10, -1]]
        self.assertEqual(len(joined), 1)
        self.assertTrue(joined[0]['complete'])
        self.assertTrue(joined[0]['connected_map_parts'])
        terrain.grid('OneIsland_Frlg')[19*24+3] = 0x112B
        self.assertFalse(next(row for row in census(terrain)['objects']
                              if row['map'] == BEACH and row['anchor'] == [10, -1])['complete'])

    def test_wrong_last_footprint_stages_nothing(self):
        terrain, layer = FixtureTerrain(), Layer()
        terrain.grid(FIVE)[14*24+6] = 0x112B
        with patch('port_boundary_scenery.Terrain', return_value=terrain):
            with self.assertRaises(AssertionError):
                repair(layer)
        self.assertEqual(layer.outputs, {})

    def test_native_submerged_variant_is_not_rewritten_as_a_broken_standard_boulder(self):
        terrain = FixtureTerrain()
        words = terrain.grid('OneIsland_Frlg')
        for q, mid in enumerate((0x112, 0x111, 0x11A, 0x119)):
            words[(1+q//2)*24+22+q%2] = 0x1000 | mid
        row = next(row for row in census(terrain)['objects']
                   if row['map'] == 'OneIsland_Frlg' and row['anchor'] == [22, 1])
        self.assertTrue(row['complete'])
        self.assertEqual(row['native_complete_variant'], [0x112, 0x111, 0x11A, 0x119])

    def test_unexpected_event_on_changed_quarter_stages_nothing(self):
        terrain, layer = FixtureTerrain(), Layer()
        terrain.maps[FIVE]['warp_events'] = [dict(x=5, y=14)]
        with patch('port_boundary_scenery.Terrain', return_value=terrain):
            with self.assertRaisesRegex(AssertionError, 'intersects an event'):
                repair(layer)
        self.assertEqual(layer.outputs, {})

    def test_new_blocked_pebbles_cannot_cut_a_preexisting_water_corridor(self):
        terrain = FixtureTerrain()
        # Interior one-tile bridge between two open water pockets. A proposed
        # pebble on its center must fail even though all outer edges survive.
        width, height = 7, 5
        terrain.layouts[FIVE].update(width=width, height=height)
        before = [0x152B]*(width*height)
        for x in range(1, 6):
            before[2*width+x] = 0x112B
        after = before.copy()
        after[2*width+3] = 0x1643
        with self.assertRaisesRegex(AssertionError, 'closes an existing Surf route'):
            check_water_connectivity(terrain, FIVE, before, after, {2*width+3})

    def test_same_water_id_with_a_cliff_upper_layer_aborts_before_staging(self):
        terrain, layer = FixtureTerrain(), Layer()
        terrain.primary[0x273*8+4] = 0x5250
        with patch('port_boundary_scenery.Terrain', return_value=terrain):
            with self.assertRaisesRegex(AssertionError, 'non-water upper artwork'):
                repair(layer)
        self.assertEqual(layer.outputs, {})


if __name__ == '__main__':
    unittest.main()
