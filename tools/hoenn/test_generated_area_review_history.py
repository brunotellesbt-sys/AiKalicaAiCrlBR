"""Preserve the exact layer-170 review identity, battery and media provenance."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import verify_coast_scenery_review_update as previous
from generated_area_review_contract import BASELINE_SHA256, HISTORICAL_COMMIT, SCOPE
from publish_badge_story import archive_plan, historical_media
from publish_coastal_closures import report_dependencies
from verify_generated_area_review_update import baseline

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT/'mods/hoenn/generated-area-review-validation/baseline'
VERSIONS = ROOT/'mods/hoenn/versions'


class GeneratedAreaReviewHistory(unittest.TestCase):
    def release(self):
        return json.loads((BASELINE/'versions.json').read_bytes())

    def review(self):
        return json.loads((BASELINE/'review.json').read_bytes())

    def test_parent_baseline_rejects_every_changed_file(self):
        for name in BASELINE_SHA256:
            with self.subTest(file=name):
                raw = (BASELINE/name).read_bytes()
                baseline(name, raw)
                with self.assertRaises(AssertionError):
                    baseline(name, raw+b'changed')

    def test_historical_parent_keeps_its_test_rom_and_save(self):
        with patch('verify_sevii_route_boundaries_update.verify_review', side_effect=AssertionError('Read current TESTE')):
            previous.verify_update(VERSIONS, self.release(), historical_review=self.review(),
                                   historical_save=BASELINE/'test.sav')
        review = self.review()
        review['base_normal_sha256'] = '0'*64
        with self.assertRaises(AssertionError):
            previous.review_identity(VERSIONS, self.release(), historical_review=review,
                                     historical_save=BASELINE/'test.sav')
        with self.assertRaisesRegex(AssertionError, 'pinned save'):
            previous.review_identity(VERSIONS, self.release(), historical_review=self.review())
        with tempfile.TemporaryDirectory(prefix='generated-area-history-', dir='/tmp') as directory:
            wrong = Path(directory)/'other.sav'
            wrong.write_bytes(bytes(131072))
            with self.assertRaises(AssertionError):
                previous.verify_update(VERSIONS, self.release(), historical_review=self.review(),
                                       historical_save=wrong)

    def test_parent_native_media_remain_bound_to_their_archived_commit(self):
        release = self.release()
        proof = next(row for row in release['proofs'] if row['kind'] == 'coast-scenery-review-native')
        report = Path(proof['file'])
        dependencies = report_dependencies(VERSIONS/report, expected_sha=proof['sha256'])
        captures = {(report.parent/relative).as_posix(): sha for relative, (_, sha) in dependencies.items()
                    if relative.suffix == '.png'}
        self.assertTrue(captures)
        entries, media = archive_plan(release, VERSIONS, include_roms=False, current_scope=SCOPE)
        for name, sha in captures.items():
            self.assertNotIn(name, entries)
            self.assertEqual(media[name]['sha256'], sha)
            self.assertIn('coast-scenery-review', media[name]['required_by_historical_scopes'])
        selected = next(iter(captures))
        registry = historical_media({selected: media[selected]}, commit=HISTORICAL_COMMIT)
        self.assertIn('/blob/'+HISTORICAL_COMMIT+'/', registry[0]['url'])


if __name__ == '__main__':
    unittest.main()
