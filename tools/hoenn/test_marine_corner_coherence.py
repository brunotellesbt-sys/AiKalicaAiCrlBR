"""Check the connectivity guard against splits, openings and real detours."""
import unittest

from marine_corner_coherence import component_integrity
from validate_sevii_route_boundaries_source import Inputs


class Toy(Inputs):
    def __init__(self, blocked=(), detour=False):
        self.maps = {'A': dict(id='A', layout='A', connections=[])}
        self.layouts = {'A': dict(width=3, height=2)}
        self.by_id = {'A': 'A'}
        self.water = {1}
        self.cells = {'A': [0x1001]*6}
        for pos in blocked:
            self.cells['A'][pos] = 0x1402
        if detour:
            self.maps['A']['connections'] = [dict(direction='down', offset=0, map='B')]
            self.maps['B'] = dict(id='B', layout='B', connections=[dict(direction='up', offset=0, map='A')])
            self.layouts['B'] = dict(width=3, height=2)
            self.by_id['B'] = 'B'
            self.cells['B'] = [0x1001]*6

    def grid(self, name): return self.cells[name]
    def behavior(self, name, block): return block & 1023


class ConnectivityTests(unittest.TestCase):
    def test_rejects_a_barrier_that_splits_a_waterway(self):
        with self.assertRaisesRegex(AssertionError, 'component split'):
            component_integrity(Toy(), Toy(blocked=(1, 4)), {'A'})

    def test_accepts_local_split_with_existing_neighbor_detour(self):
        report = component_integrity(Toy(detour=True), Toy(blocked=(1, 4), detour=True), {'A'})
        for row in report['global_component_checks']:
            self.assertEqual((row['before_components'], row['after_components']), (1, 1))
            self.assertEqual(row['changed_map_component_sizes'][0]['after'], [2, 2])

    def test_rejects_an_unexpected_opening(self):
        with self.assertRaisesRegex(AssertionError, 'Unexpected passable opening'):
            component_integrity(Toy(blocked=(1,)), Toy(), {'A'})


if __name__ == '__main__':
    unittest.main()
