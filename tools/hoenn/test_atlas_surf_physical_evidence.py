"""Reject promotion, altered captures, false headings and hidden loading gaps."""
import copy
import json
from pathlib import Path
import unittest

from verify_atlas_surf_physical_native import verify


DIRECTORY=Path(__file__).resolve().parents[2]/'docs/design/atlas-surf-layout/diagnostic-physical-native'


class PhysicalEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.report=json.loads((DIRECTORY/'physical-native.json').read_text())

    def test_exported_frames_pixels_and_hashes_verify(self):
        result=verify(self.report,DIRECTORY)
        self.assertTrue(result['passed'])
        self.assertFalse(result['final_release_validated'])
        self.assertFalse(result['current_source_bound'])

    def test_long_pause_or_query_during_timing_is_rejected(self):
        for mode in ('pause','query'):
            report=copy.deepcopy(self.report)
            seam=report['seams'][0]
            if mode=='pause':
                seam['consistent_coordinates_frame']=seam['map_published_frame']+300
                seam['inconsistent_coordinate_frames']=300
            else:
                report['queries'][0]['frame']=seam['start_frame']+1
            with self.assertRaises(AssertionError):
                verify(report,DIRECTORY)

    def test_direction_drift_or_release_promotion_is_rejected(self):
        for mode in ('direction','release'):
            report=copy.deepcopy(self.report)
            if mode=='direction':
                next(row for row in report['route'] if row['phase']=='north-eight-tiles')['global_after'][0]+=1
            else:report['final_release_validated']=True
            with self.assertRaises(AssertionError):
                verify(report,DIRECTORY)

    def test_changed_capture_hash_or_pixel_witness_is_rejected(self):
        for mode in ('hash','pixel'):
            report=copy.deepcopy(self.report)
            if mode=='hash':report['captures'][0]['sha256']='0'*64
            else:
                row=next(row for row in report['observations'] if row['case']=='diagonal-real-terrain-without-direct-connection')
                row['pixels']['cells'][0]['samples'][0][2:5]=[248,0,248]
            with self.assertRaises(AssertionError):
                verify(report,DIRECTORY)


if __name__=='__main__':
    unittest.main()
