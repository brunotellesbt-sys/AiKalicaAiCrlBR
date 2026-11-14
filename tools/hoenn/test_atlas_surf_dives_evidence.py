"""Reject false Dive exports, mutable queries, altered images and promotion."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from verify_atlas_surf_dives_native import verify


DIRECTORY=Path(__file__).resolve().parents[2]/'docs/design/atlas-surf-layout/diagnostic-dives-native'


class DiveEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.report=json.loads((DIRECTORY/'dives-native.json').read_text())

    def test_current_exported_native_trips_and_pixels_verify(self):
        result=verify(self.report,DIRECTORY)
        self.assertEqual(result['sites'],5)
        self.assertEqual(result['captures'],40)
        self.assertFalse(result['current_source_bound'])
        self.assertFalse(result['final_release_validated'])

    def test_wrong_destination_or_mode_is_rejected(self):
        for mode in ('coords','avatar'):
            report=deepcopy(self.report)
            if mode=='coords':report['cases'][0]['descent']['after']['tile'][0]+=1
            else:report['cases'][0]['emerge']['after']['mode']=16
            with self.assertRaises(AssertionError):verify(report,DIRECTORY)

    def test_mutable_query_or_promotion_is_rejected(self):
        for mode in ('query','release'):
            report=deepcopy(self.report)
            if mode=='query':report['queries'][0]['function']='TrySetDiveWarp'
            else:report['final_release_validated']=True
            with self.assertRaises(AssertionError):verify(report,DIRECTORY)

    def test_capture_hash_or_floor_height_claim_is_rejected(self):
        for mode in ('hash','floor'):
            report=deepcopy(self.report)
            if mode=='hash':report['captures'][0]['sha256']='0'*64
            else:report['cases'][0]['sanctuary']['tile_elevation']=3
            with self.assertRaises(AssertionError):verify(report,DIRECTORY)


if __name__=='__main__':
    unittest.main()
