"""Keep layer 168 evidence bound to its own review identity and tested save."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import verify_game_continuity_review_update as previous
from publish_badge_story import archive_plan, historical_media
from publish_coastal_closures import report_dependencies
from sevii_route_boundaries_contract import BASELINE_SHA256, HISTORICAL_COMMIT, SCOPE
from verify_sevii_route_boundaries_update import baseline

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT/'mods/hoenn/sevii-route-boundaries-validation/baseline'
VERSIONS = ROOT/'mods/hoenn/versions'


class SeviiRouteBoundariesHistoricalRelease(unittest.TestCase):
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

    def test_parent_never_reads_current_test_rom_during_historical_verification(self):
        with patch.object(previous, 'verify_review', side_effect=AssertionError('Read current TESTE')):
            previous.verify_update(VERSIONS, self.release(), historical_review=self.review(),
                                   historical_save=BASELINE/'test.sav')

    def test_parent_rejects_review_from_another_normal_edition(self):
        review = self.review()
        review['base_normal_sha256'] = '0'*64
        with self.assertRaises(AssertionError):
            previous.verify_update(VERSIONS, self.release(), historical_review=review,
                                   historical_save=BASELINE/'test.sav')

    def test_parent_requires_the_save_used_by_its_boot_proof(self):
        with tempfile.TemporaryDirectory(prefix='sevii-boundary-history-', dir='/tmp') as directory:
            wrong = Path(directory)/'other.sav'
            wrong.write_bytes(bytes(131072))
            with self.assertRaises(AssertionError):
                previous.verify_update(VERSIONS, self.release(), historical_review=self.review(),
                                       historical_save=wrong)

    def test_parent_camera_captures_keep_their_exact_archived_provenance(self):
        release = self.release()
        proof = next(row for row in release['proofs'] if row['kind'] == 'game-continuity-coasts')
        report = Path(proof['file'])
        dependencies = report_dependencies(VERSIONS/report, expected_sha=proof['sha256'])
        captures = {(report.parent/relative).as_posix(): sha for relative, (_, sha) in dependencies.items()
                    if relative.suffix == '.png'}
        self.assertTrue(captures)
        entries, media = archive_plan(release, VERSIONS, include_roms=False, current_scope=SCOPE)
        for name, sha in captures.items():
            self.assertNotIn(name, entries)
            self.assertEqual(media[name]['sha256'], sha)
            self.assertIn('game-continuity-review', media[name]['required_by_historical_scopes'])
        selected = next(iter(captures))
        registry = historical_media({selected: media[selected]}, commit=HISTORICAL_COMMIT)
        self.assertEqual(registry[0]['repository_file'], 'mods/hoenn/versions/'+selected)
        self.assertIn('/blob/'+HISTORICAL_COMMIT+'/', registry[0]['url'])


if __name__ == '__main__':
    unittest.main()
