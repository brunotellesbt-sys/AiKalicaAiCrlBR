"""A camera seam must settle before the walker indexes its new layout."""
import ast
from pathlib import Path
import unittest


class NativeCoordinateObservation(unittest.TestCase):
    def observer(self, positions):
        tree = ast.parse(Path(__file__).with_name('native_water_walk.py').read_text())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'settled_position')
        state = {'frame': 0}
        context = dict(by_location={(1, 2): 'new'}, location=lambda: (1, 2),
                       position=lambda: positions[min(state['frame'], len(positions)-1)],
                       blocks={'new': (8, 6, ())})
        def step(frames):
            state['frame'] += frames
        context['step'] = step
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<walker>', 'exec'), context)
        return context['settled_position'], state

    def test_outgoing_coordinates_are_never_used_in_the_smaller_new_map(self):
        observe, state = self.observer([(94, 38), (94, 38), (2, 0)])
        self.assertEqual(observe(), ('new', 2, 0))
        self.assertEqual(state['frame'], 2)

    def test_valid_coordinates_do_not_advance_the_game(self):
        observe, state = self.observer([(7, 5)])
        self.assertEqual(observe(), ('new', 7, 5))
        self.assertEqual(state['frame'], 0)

    def test_persistent_invalid_coordinates_fail_instead_of_hiding_a_game_bug(self):
        observe, _ = self.observer([(-1, 2)])
        with self.assertRaisesRegex(AssertionError, 'did not settle'):
            observe(limit=3)

    def test_in_range_outgoing_coordinates_are_not_reported_as_surf_on_land(self):
        tree = ast.parse(Path(__file__).with_name('native_water_walk.py').read_text())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'walk')
        positions = iter([('new', 5, 5), ('new', 1, 1)])
        observations, frames = [], []
        context = dict(walked=0, blocked=set(), by_location={0:'old'},
                       location=lambda:0, position=lambda:(5,5), field=lambda:False,
                       settled_position=lambda:next(positions), step=lambda count:frames.append(count),
                       transitions=[], walk_transition_pictures=False,
                       walk_observer=lambda before,after:observations.append((before,after)))
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<walker>', 'exec'), context)
        context['walk'](('new',1,1))
        self.assertEqual(frames,[30])
        self.assertEqual(observations,[(('old',5,5),('new',1,1))])


if __name__ == '__main__':
    unittest.main()
