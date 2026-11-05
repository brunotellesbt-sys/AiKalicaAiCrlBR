"""Preserve layer 167's own TESTE identity and controller-tested battery."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import verify_arrival_coast_review_update as previous
from game_continuity_review_contract import BASELINE_SHA256
from verify_game_continuity_review_update import baseline

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT/'mods/hoenn/game-continuity-review-validation/baseline'
VERSIONS = ROOT/'mods/hoenn/versions'


class GameContinuityHistoricalRelease(unittest.TestCase):
    def release(self):
        return json.loads((BASELINE/'versions.json').read_bytes())

    def review(self):
        return json.loads((BASELINE/'review.json').read_bytes())

    def test_parent_baseline_files_reject_any_byte_change(self):
        for name in BASELINE_SHA256:
            with self.subTest(file=name):
                raw = (BASELINE/name).read_bytes()
                baseline(name,raw)
                with self.assertRaises(AssertionError):
                    baseline(name,raw+b'changed')

    def test_parent_uses_pinned_metadata_without_reading_current_test_rom(self):
        with patch.object(previous,'verify_review',side_effect=AssertionError('Historical check read current TESTE')):
            previous.verify_update(VERSIONS,self.release(),historical_review=self.review(),
                                   historical_save=BASELINE/'test.sav')

    def test_parent_rejects_another_normal_rom_identity(self):
        review = self.review()
        review['base_normal_sha256'] = '0'*64
        with self.assertRaises(AssertionError):
            previous.verify_update(VERSIONS,self.release(),historical_review=review,
                                   historical_save=BASELINE/'test.sav')

    def test_parent_requires_the_battery_its_boot_proof_tested(self):
        with tempfile.TemporaryDirectory(prefix='game-continuity-history-',dir='/tmp') as directory:
            wrong = Path(directory)/'other.sav'
            wrong.write_bytes(bytes(131072))
            with self.assertRaises(AssertionError):
                previous.verify_update(VERSIONS,self.release(),historical_review=self.review(),
                                       historical_save=wrong)


if __name__ == '__main__':
    unittest.main()
