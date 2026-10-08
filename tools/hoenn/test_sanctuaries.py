"""Check recorded native sanctuary evidence against the integration candidate."""
import json
from pathlib import Path
import unittest

VALIDATION = Path(__file__).resolve().parents[2] / 'mods/hoenn/integration-validation'


def report(name):
    return json.loads((VALIDATION / (name + '.json')).read_text())


class SanctuaryRequirements(unittest.TestCase):
    def test_all_special_species_have_unique_altar_flags(self):
        prep = report('sanctuaries-preparation')
        catalog = json.loads((VALIDATION.parents[2] / 'tools/hoenn/catalog_metadata.json').read_text())
        captures = prep['captures']
        self.assertEqual(len(captures), 105)
        self.assertEqual({c['id'] for c in captures}, set(catalog['special_species']))
        self.assertEqual(len({c['flag_id'] for c in captures}), 105)
        self.assertEqual(len({(c['map'], tuple(c['position'])) for c in captures}), 105)

    def test_all_native_reports_certify_the_same_candidate(self):
        names = ['connected-world', 'family', 'birth-rules', 'wild',
                 'native-catalog', 'sanctuaries', 'sanctuary-capture']
        candidate = report('native-catalog')['rom_sha256']
        for name in names:
            with self.subTest(report=name):
                data = report(name)
                self.assertEqual(data['rom_sha256'], candidate)
                if name != 'connected-world':
                    self.assertTrue(data['passed'])

    def test_every_remote_site_has_a_native_entry_and_return(self):
        prep = report('sanctuaries-preparation')
        native = report('sanctuaries')
        self.assertEqual({s['theme'] for s in prep['sites']},
                         {s['site'] for s in native['sites']})
        self.assertEqual(len(native['sites']), 14)
        self.assertEqual(sum(s['access'] == 'surf' for s in native['sites']), 9)
        self.assertEqual(sum(s['access'] == 'dive' for s in native['sites']), 5)
        self.assertEqual(sum(s['interaction_cells'] for s in native['sites']), 105)
        self.assertTrue(all(s['native_entry_and_return'] for s in native['sites']))
        self.assertEqual(native['gate_cases'], 6)

    def test_real_capture_requires_sixteen_badges_and_persists(self):
        capture = report('sanctuary-capture')
        self.assertEqual(capture['national_dex'], 1025)
        for check in ['locked_with_15_badges', 'unlocked_with_16_before_leagues',
                      'real_escape_and_retry', 'real_master_ball_capture',
                      'capture_persists_on_map_reload',
                      'native_flash_save_restores_catch_flag']:
            with self.subTest(check=check):
                self.assertTrue(capture[check])


if __name__ == '__main__':
    unittest.main()
