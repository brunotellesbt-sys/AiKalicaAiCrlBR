"""Layer-165 evidence must remain bound to its own TESTE and battery save."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import verify_generated_world_update as previous


ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / 'mods/hoenn/coastal-ecology-validation/baseline'
VERSIONS = ROOT / 'mods/hoenn/versions'


class CoastalEcologyHistoricalRelease(unittest.TestCase):
    def release(self):
        return json.loads((BASELINE/'versions.json').read_bytes())

    def review(self):
        return json.loads((BASELINE/'review.json').read_bytes())

    def test_layer165_uses_its_pinned_metadata_without_reading_current_roms(self):
        with patch.object(previous, 'verify_review',
                          side_effect=AssertionError('Historical check read current TESTE')):
            previous.verify_update(VERSIONS, self.release(), historical_review=self.review(),
                                   historical_save=BASELINE/'test.sav')

    def test_layer165_rejects_a_review_identity_from_another_normal_rom(self):
        review = self.review()
        review['base_normal_sha256'] = '0'*64
        with self.assertRaises(AssertionError):
            previous.verify_update(VERSIONS, self.release(), historical_review=review,
                                   historical_save=BASELINE/'test.sav')

    def test_layer165_requires_the_save_tested_in_its_boot_evidence(self):
        with tempfile.TemporaryDirectory(prefix='coastal-history-', dir='/tmp') as temporary:
            wrong = Path(temporary)/'other.sav'
            wrong.write_bytes(bytes(131072))
            with self.assertRaises(AssertionError):
                previous.verify_update(VERSIONS, self.release(), historical_review=self.review(),
                                       historical_save=wrong)


if __name__ == '__main__':
    unittest.main()
