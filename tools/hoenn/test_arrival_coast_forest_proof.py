"""Reject regressions in the recorded native forest route and its evidence."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from PIL import Image

from verify_arrival_coast_forest_proof import verify

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'mods/hoenn/arrival-coast-review-validation/common/photos/forest'


class ForestNativeProof(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((EVIDENCE/'arrival-coast-forest-native.json').read_text())

    def rejects(self,mutate):
        report=copy.deepcopy(self.report)
        mutate(report)
        with self.assertRaises(AssertionError):verify(report,EVIDENCE)

    def test_actual_final_rom_observations_and_media_pass(self):
        self.assertTrue(verify(self.report,EVIDENCE))

    def test_source_only_or_partial_route_cannot_replace_native_proof(self):
        self.rejects(lambda r:r.update(compiled_rom=False))
        self.rejects(lambda r:r.update(walked_tiles=0))
        self.rejects(lambda r:r['states'].pop())

    def test_foreign_camera_palette_bank_and_inconsistent_addresses_fail(self):
        self.rejects(lambda r:r['loaded_banks'][4].update(primary='gTileset_General_Frlg'))
        self.rejects(lambda r:r['loaded_banks'][5].update(secondary='gTileset_LavenderTown'))
        self.rejects(lambda r:r['loaded_banks'][1].update(primary_pointer=r['loaded_banks'][1]['primary_pointer']+4))

    def test_closed_shore_or_missing_controlled_return_fails(self):
        self.rejects(lambda r:r['native_dry_landing'].update(surfing=True,elevation=1))
        self.rejects(lambda r:r['transitions'].pop(1))
        self.rejects(lambda r:r.update(native_surf_return_prompt=False))

    def test_gatehouse_warps_cannot_be_replaced_with_an_exterior_jump(self):
        self.rejects(lambda r:r['transitions'].__setitem__(3,dict(
            source=['Route15_Frlg',9,11],destination=['Route15_Frlg',16,11])))

    def test_controller_walking_through_a_tree_or_missing_blocker_fails(self):
        self.rejects(lambda r:r['dry_margin_and_forest_controller_checks'][0]['before'].update(tile=[1,2]))
        self.rejects(lambda r:r['dry_margin_and_forest_controller_checks'].pop())

    def test_still_frame_wrong_palette_and_missing_real_water_samples_fail(self):
        self.rejects(lambda r:r['native_water_animation'][0].update(
            valid_native_phases=r['native_water_animation'][1]['valid_native_phases']))
        self.rejects(lambda r:r['native_water_animation'][0]['visible_pixels'].update(palette=6))
        self.rejects(lambda r:r['native_water_animation'][0]['visible_pixels'].update(samples=[]))

    def test_tampered_capture_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'forest';shutil.copytree(EVIDENCE,target)
            row=self.report['captures'][0]
            with (target/row['file']).open('ab') as stream:stream.write(b'changed')
            with self.assertRaises(AssertionError):verify(self.report,target)

    def test_rehashed_picture_with_missing_avatar_pixels_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'forest';shutil.copytree(EVIDENCE,target)
            report=copy.deepcopy(self.report);state=report['states'][0]
            path=target/state['capture_file'];image=Image.open(path).convert('RGB')
            for x,y,*_ in state['avatar_pixels']['expected_scanout_pixels']:
                image.putpixel((x,y),(255,0,255))
            image.save(path)
            report['captures'][0]['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaises(AssertionError):verify(report,target)

    def test_rehashed_picture_with_wrong_water_pixels_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'forest';shutil.copytree(EVIDENCE,target)
            report=copy.deepcopy(self.report);row=report['native_water_animation'][0]
            path=target/row['capture_file'];image=Image.open(path).convert('RGB')
            x,y,*_=row['visible_pixels']['samples'][0]
            image.putpixel((x,y),(255,0,255));image.save(path)
            row['capture_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaises(AssertionError):verify(report,target)


if __name__=='__main__':unittest.main()
