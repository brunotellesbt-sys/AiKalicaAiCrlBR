"""Keep the recorded beach occlusion distinguishable from a visible sprite."""
import copy
import json
from pathlib import Path
import unittest

from verify_sevii_integrated_piers_update import verify_visibility_captures


ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / 'mods/hoenn/sevii-integrated-validation/baseline/dewford-beach-visibility.json'


class NativeBeachVisibility(unittest.TestCase):
    def test_recorded_avatar_can_be_hidden_despite_enabled_sprite_flags(self):
        report = json.loads(BASELINE.read_text())
        self.assertFalse(report['passed'])
        self.assertTrue(report['bug_reproduced'])
        self.assertEqual(report['rom_sha256'],
                         '5e0cecc8d2143334795a752e9bb1f70343671f34a29dbd2af3a78e3bff05ef50')
        verify_visibility_captures(report, BASELINE.parent)
        samples = {row['label']: row for row in report['samples']}
        for label in ['east-beach-corner-avatar', 'east-side-of-bridge-footing']:
            with self.subTest(label=label):
                self.assertTrue(samples[label]['sprite_enabled'])
                self.assertTrue(samples[label]['object_enabled'])
                self.assertEqual(samples[label]['lower_body_pixels'], 0)
        self.assertGreater(samples['ordinary-sand-visible-reference']['lower_body_pixels'], 8)

    def test_reported_visibility_must_match_the_actual_native_capture(self):
        report = json.loads(BASELINE.read_text())
        altered = copy.deepcopy(report)
        sample = next(row for row in altered['samples'] if row['label'] == 'east-beach-corner-avatar')
        sample['lower_body_pixels'] = 24
        with self.assertRaises(AssertionError):
            verify_visibility_captures(altered, BASELINE.parent)


if __name__ == '__main__':
    unittest.main()
