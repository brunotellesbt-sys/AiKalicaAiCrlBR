"""Regressions for unused native maps and the isolated host-C oracle."""
from pathlib import Path
import shutil
from types import SimpleNamespace
import unittest

from atlas_surf_regional_projection import NativeCOracle, NativeProjection
from atlas_surf_source import Source


class MapIdentityTests(unittest.TestCase):
    def test_unused_map_and_constant_fail_explicitly(self):
        projection = NativeProjection.__new__(NativeProjection)
        projection.inputs = SimpleNamespace(
            maps={'Unused': {'id': 'MAP_UNUSED'}}, identities={},
            by_id={'MAP_UNUSED': 'Unused'})
        for name in ('Unused', 'MAP_UNUSED'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'no compiled identity'):
                projection._map_name(name)


class Revision171OracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path(__file__).resolve().parents[2] / '.local/generated-area-review-src'
        if not (source / '.journey-generated-area-review').is_file():
            raise unittest.SkipTest('Immutable revision171 source is not available')
        if not (shutil.which('cc') or shutil.which('gcc')):
            raise unittest.SkipTest('Host C compiler is not available')
        cls.projection = NativeProjection(Source(source))

    def test_unused_maps_are_omitted_and_native_cases_match(self):
        projection = self.projection
        unused = set(projection.inputs.maps) - set(projection.inputs.identities)
        self.assertIn('Route19_UnusedHouse_Frlg', unused)
        code = NativeCOracle(projection).code()
        for name in unused:
            constant = projection.inputs.maps[name]['id']
            self.assertNotIn('#define ' + constant + ' ', code)
        self.assertIn('#define MAP_TYPE_UNKNOWN ', code)
        cases = [
            ('Route121', 0, 0), ('Route121', 55, 1),
            ('Route126', 52, 57), ('SlateportCity', 10, 10),
            ('SSTidalCorridor', 1, 1, {'sstidal': {'location': 'SS_TIDAL_LOCATION_SLATEPORT'}}),
        ]
        report = NativeCOracle(projection).compare(cases)
        self.assertEqual(report['cases'], len(cases))
        self.assertEqual(report['mismatches'], 0)
        self.assertFalse(report['arm_build'])
        self.assertFalse(report['source_written'])


if __name__ == '__main__':
    unittest.main()
