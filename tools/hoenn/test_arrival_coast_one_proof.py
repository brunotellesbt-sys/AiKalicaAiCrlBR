"""Reject missing coastal geometry, animation and native picture evidence."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from PIL import Image

from verify_arrival_coast_one_proof import verify

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT/'mods/hoenn/arrival-coast-review-validation/common/photos/one'


class OneNativeProof(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((EVIDENCE/'arrival-coast-one-native.json').read_bytes())

    def rejects(self, mutate):
        report = copy.deepcopy(self.report)
        mutate(report)
        with self.assertRaises(AssertionError):
            verify(report, EVIDENCE)

    def test_actual_final_native_observations_pass(self):
        self.assertTrue(verify(self.report, EVIDENCE))

    def test_incomplete_upper_water_or_wrong_loaded_camera_is_rejected(self):
        self.rejects(lambda r: r['compiled_upper_water'].update(upper_words_changed=29))
        self.rejects(lambda r: r['loaded_camera_banks'][0].update(primary='gTileset_General_Frlg'))
        self.rejects(lambda r: r['animation_cycles'][0]['rows'].pop())
        self.rejects(lambda r: r['animation_cycles'][0]['rows'][0]['visible_pixels'].update(palette=6))
        self.rejects(lambda r: r['animation_cycles'][0]['rows'][0].update(valid_native_phases={'current':[], 'sand':[]}))

    def test_missing_cliff_object_quarter_or_controlled_return_is_rejected(self):
        self.rejects(lambda r: r['west_cliff']['compiled_cells'].pop())
        self.rejects(lambda r: r['west_cliff']['blocked_north'][0]['after'].update(tile=[0,7]))
        self.rejects(lambda r: r['west_cliff']['boundary_rock']['pixels'].update(matching_scanout_pixels=97))
        self.rejects(lambda r: r['west_cliff'].update(roundtrip_connections=[]))
        self.rejects(lambda r: r['orphan_and_boulder']['retained_complete_cross_map_boulder'].pop())
        self.rejects(lambda r: r['orphan_and_boulder']['removed_orphan_cells_traversed_by_native_surf'][0].update(surfing=False))

    def test_rehashed_partial_rock_picture_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)/'one'
            shutil.copytree(EVIDENCE, target)
            report = copy.deepcopy(self.report)
            rock = report['west_cliff']['boundary_rock']
            path = target/rock['capture_file']
            picture = Image.open(path).convert('RGB')
            for x,y,*_ in rock['pixels']['expected_scanout_pixels']:
                picture.putpixel((x,y),(255,0,255))
            picture.save(path)
            for row in report['captures']:
                if row['file'] == rock['capture_file']:
                    row['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaises(AssertionError):
                verify(report,target)

    def test_rehashed_wrong_water_picture_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)/'one'
            shutil.copytree(EVIDENCE,target)
            report = copy.deepcopy(self.report)
            phase = report['animation_cycles'][0]['rows'][0]
            path = target/phase['capture_file']
            picture = Image.open(path).convert('RGB')
            x,y,*_ = phase['visible_pixels']['samples'][0]
            picture.putpixel((x,y),(255,0,255))
            picture.save(path)
            phase['capture_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            for row in report['captures']:
                if row['file'] == phase['capture_file']:
                    row['sha256'] = phase['capture_sha256']
            with self.assertRaises(AssertionError):
                verify(report,target)


if __name__ == '__main__':
    unittest.main()
