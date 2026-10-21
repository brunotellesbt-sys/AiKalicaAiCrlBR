"""Reject relabelled ROM evidence, blocked Surf returns and covered native pixels.

Use --validation with a real integrated-piers validator output. Those native
checks are skipped until that output exists; baseline preservation still runs.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

from publish_sevii_integrated_piers import copy_proof, preserve_history
from verify_sevii_integrated_piers_update import (
    ROOT, current_report, verify_captures, verify_integrated_piers,
    verify_dewford, verify_native_avatar_pixels, verify_reboarding_baseline,
    verify_visibility_captures,
)


BASELINE = ROOT / 'mods/hoenn/sevii-integrated-validation/baseline'
OLD_SHA = '5e0cecc8d2143334795a752e9bb1f70343671f34a29dbd2af3a78e3bff05ef50'
NATIVE = ROOT / 'mods/hoenn/sevii-integrated-validation/Gen1-9-Normal'


def reference(path):
    return dict(file=path.relative_to(ROOT).as_posix(),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def reboarding_reference():
    directory = BASELINE / 'sevii-reboarding'
    result = reference(directory / 'blocked-surf-return-reproduced.json')
    result['captures'] = [reference(path) for path in sorted(directory.glob('*.png'))]
    return result


class HistoricalEvidence(unittest.TestCase):
    def test_original_seven_blocked_returns_remain_expected_failures(self):
        pinned = reboarding_reference()
        self.assertEqual(pinned['sha256'],
                         '59ff93961ac4d1d63f5b635f1a5576fff68ca8b6f222c3b422ac230bf50424b4')
        report = verify_reboarding_baseline(pinned, OLD_SHA)
        self.assertFalse(report['passed'])
        self.assertEqual(len(report['ports']), 7)

    def test_expected_failure_cannot_seal_a_current_release(self):
        raw = (BASELINE / 'sevii-reboarding/blocked-surf-return-reproduced.json').read_bytes()
        with self.assertRaisesRegex(AssertionError, 'Failed evidence'):
            current_report(raw, OLD_SHA, ('test', 'integrated-piers'))

    def test_stale_passed_native_report_is_rejected(self):
        raw = (ROOT / 'mods/hoenn/dewford-coast-validation/Gen1-9-Normal/dewford-coast.json').read_bytes()
        report = json.loads(raw)
        current_report(raw, report['rom_sha256'], ('old', 'dewford-coast'))
        with self.assertRaisesRegex(AssertionError, 'Stale evidence'):
            current_report(raw, '0' * 64, ('new', 'dewford-coast'))

    def test_baseline_capture_hash_cannot_be_relabelled(self):
        pinned = reboarding_reference()
        pinned['captures'][0]['sha256'] = '0' * 64
        with self.assertRaises(AssertionError):
            verify_reboarding_baseline(pinned, OLD_SHA)

    def test_publisher_preserves_native_report_and_capture_bytes(self):
        source = BASELINE / 'dewford-beach-visibility.json'
        report = json.loads(source.read_bytes())
        with tempfile.TemporaryDirectory(prefix='sevii-evidence-', dir='/tmp') as directory:
            destination = Path(directory) / 'dewford-beach-visibility.json'
            sha = copy_proof(source, destination)
            self.assertEqual(destination.read_bytes(), source.read_bytes())
            self.assertEqual(sha, hashlib.sha256(source.read_bytes()).hexdigest())
            verify_visibility_captures(report, destination.parent)
            for capture in report['captures']:
                self.assertEqual((destination.parent / capture['file']).read_bytes(),
                                 (source.parent / capture['file']).read_bytes())

    def test_modified_png_fails_despite_unchanged_report(self):
        source = BASELINE / 'dewford-beach-visibility.json'
        report = json.loads(source.read_bytes())
        with tempfile.TemporaryDirectory(prefix='sevii-corrupt-', dir='/tmp') as directory:
            destination = Path(directory) / source.name
            copy_proof(source, destination)
            capture = destination.parent / report['captures'][0]['file']
            capture.write_bytes(capture.read_bytes() + b'changed')
            with self.assertRaises(AssertionError):
                verify_visibility_captures(report, destination.parent)

    def test_invalid_capture_does_not_replace_an_existing_report(self):
        original = BASELINE / 'dewford-beach-visibility.json'
        with tempfile.TemporaryDirectory(prefix='sevii-publish-', dir='/tmp') as directory:
            root = Path(directory)
            source, target = root / 'source/report.json', root / 'target/report.json'
            copy_proof(original, source)
            copy_proof(original, target)
            altered = json.loads(source.read_bytes())
            altered['captures'][0]['sha256'] = '0' * 64
            source.write_text(json.dumps(altered))
            before = target.read_bytes()
            with self.assertRaises(AssertionError):
                copy_proof(source, target)
            self.assertEqual(target.read_bytes(), before)

    def test_isolated_output_preserves_all_historical_proof_hashes(self):
        old = json.loads((BASELINE / 'versions.json').read_bytes())
        with tempfile.TemporaryDirectory(prefix='sevii-history-', dir='/tmp') as directory:
            output = Path(directory)
            preserve_history(old, output)
            self.assertTrue((output / 'START-HERE.md').is_file())
            for proof in old['proofs']:
                self.assertEqual(hashlib.sha256((output / proof['file']).read_bytes()).hexdigest(),
                                 proof['sha256'])

    def test_original_dewford_video_schema_is_verified_without_json_relabelling(self):
        source = ROOT / 'mods/hoenn/dewford-coast-validation/Gen1-9-Normal/dewford-coast.json'
        report = json.loads(source.read_bytes())
        self.assertIn('video', report)
        self.assertNotIn('video_file', report)
        verify_dewford(report, source.parent)
        with tempfile.TemporaryDirectory(prefix='sevii-video-', dir='/tmp') as directory:
            destination = Path(directory) / source.name
            copy_proof(source, destination)
            self.assertEqual(source.read_bytes(), destination.read_bytes())
            verify_dewford(report, destination.parent)

    def test_changed_recording_hash_is_rejected(self):
        source = ROOT / 'mods/hoenn/dewford-coast-validation/Gen1-9-Normal/dewford-coast.json'
        report = json.loads(source.read_bytes())
        report['video_sha256'] = '0' * 64
        with self.assertRaises(AssertionError):
            verify_dewford(report, source.parent)


class CurrentNativeEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = NATIVE / 'integrated-piers.json'
        if not path.exists():
            raise unittest.SkipTest('Run native integrated-piers validator, then pass --validation with its output')
        cls.raw = path.read_bytes()
        cls.report = json.loads(cls.raw)
        cls.images = verify_captures(cls.report['captures'], NATIVE)

    def test_all_seven_current_piers_and_actual_png_pixels_pass(self):
        current_report(self.raw, self.report['rom_sha256'], ('native', 'integrated-piers'))
        verify_integrated_piers(self.report, NATIVE)

    def test_enabled_sprite_flags_cannot_replace_opaque_obj_pixels(self):
        altered = copy.deepcopy(self.report)
        del altered['ports'][0]['reboarded_state']['native_avatar_pixels']['expected_scanout_pixels']
        with self.assertRaises(KeyError):
            verify_integrated_piers(altered, NATIVE)

    def test_blocked_surf_return_is_rejected(self):
        altered = copy.deepcopy(self.report)
        altered['ports'][0]['surf_departure_and_reboard'] = False
        with self.assertRaisesRegex(AssertionError, 'surf_departure_and_reboard'):
            verify_integrated_piers(altered, NATIVE)

    def test_reboard_must_finish_on_foot_at_the_original_pier(self):
        altered = copy.deepcopy(self.report)
        altered['ports'][0]['reboarded_state']['surfing'] = True
        with self.assertRaises(AssertionError):
            verify_integrated_piers(altered, NATIVE)

    def test_previous_rom_hash_is_rejected_even_for_a_passed_report(self):
        altered = copy.deepcopy(self.report)
        altered['rom_sha256'] = OLD_SHA
        with self.assertRaisesRegex(AssertionError, 'Stale evidence'):
            current_report(json.dumps(altered), self.report['rom_sha256'], ('native', 'integrated-piers'))

    def test_covered_avatar_pixels_are_rejected_even_when_counters_claim_visible(self):
        state = self.report['ports'][0]['reboarded_state']
        proof = state['native_avatar_pixels']
        image = self.images[state['capture_file']].copy()
        for x, y, red, green, blue, band, unique in proof['expected_scanout_pixels']:
            if band == 2:
                image.putpixel((x, y), tuple(255 - value for value in [red, green, blue]))
        with self.assertRaises(AssertionError):
            verify_native_avatar_pixels(proof, image)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validation', type=Path, default=NATIVE)
    options, remaining = parser.parse_known_args()
    NATIVE = options.validation.resolve()
    unittest.main(argv=[sys.argv[0], *remaining])
