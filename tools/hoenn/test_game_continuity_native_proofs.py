"""Reject the reproduced softlocks, incomplete camera evidence and lost saves."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from PIL import Image

from publish_coastal_closures import copy_current_proof
from verify_game_continuity_campaign import verify as campaign
from verify_game_continuity_coasts import verify as coasts

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'mods/hoenn/game-continuity-review-validation/common'


class GameNativeProofs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.campaign=json.loads((BASE/'campaign/game-continuity-campaign.json').read_bytes())
        cls.coasts=json.loads((BASE/'coasts/game-continuity-coasts.json').read_bytes())

    def rejects(self,name,mutate):
        report=copy.deepcopy(getattr(self,name));mutate(report)
        with self.assertRaises(AssertionError):
            (campaign if name=='campaign' else coasts)(report,BASE/name)

    def test_real_native_campaign_and_sixteen_cameras_pass(self):
        campaign(self.campaign,BASE/'campaign');coasts(self.coasts,BASE/'coasts')

    def test_hidden_shelly_and_fake_battle_or_reward_fail(self):
        self.rejects('campaign',lambda r:r.update(shelly_visibility_before=0))
        self.rejects('campaign',lambda r:r.update(shelly_object_id_before=16))
        self.rejects('campaign',lambda r:r['native_battle'].update(outcome=2))
        self.rejects('campaign',lambda r:r.update(gift_species=[382,382,382,25]))

    def test_post_route119_softlock_and_save_regression_fail(self):
        self.rejects('campaign',lambda r:r['gym_ready'].update(pending_event=15))
        self.rejects('campaign',lambda r:r['cold_continue']['runs'][1].update(weather_state=1))
        self.rejects('campaign',lambda r:r['cold_continue']['runs'][1].update(shelly_instances=1))

    def test_wrong_loaded_bank_missing_return_or_animation_fail(self):
        self.rejects('coasts',lambda r:r['cases'].pop())
        self.rejects('coasts',lambda r:r['cases'][0]['before_bank'].update(secondary='gTileset_JourneySeviiSea45'))
        self.rejects('coasts',lambda r:r['cases'][0]['returned'].update(surfing=False))
        self.rejects('coasts',lambda r:r['cases'][0]['phases'].pop())
        self.rejects('coasts',lambda r:r['cases'][0]['phases'][0]['camera'].update(canonical_neighbor_rom_bg_words_checked=False))

    def test_rehashed_wrong_terminal_picture_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'coasts';shutil.copytree(BASE/'coasts',target)
            report=copy.deepcopy(self.coasts);case=report['cases'][0]
            image_path=target/case['before_capture']['file']
            image=Image.open(image_path).convert('RGB')
            samples=[p for p in case['before_pixels']['samples'] if p[5]!=case['map'] and p[6]>=640]
            self.assertTrue(samples)
            x,y,*_=samples[0];image.putpixel((x,y),(255,0,255));image.save(image_path)
            sha=hashlib.sha256(image_path.read_bytes()).hexdigest()
            case['before_capture']['sha256']=sha
            next(row for row in report['captures'] if row['file']==image_path.name)['sha256']=sha
            with self.assertRaises(AssertionError):coasts(report,target)

    def test_proof_copy_keeps_actual_battery_and_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'proof.json'
            copy_current_proof(BASE/'campaign/game-continuity-campaign.json',target)
            campaign(json.loads(target.read_bytes()),target.parent)
            battery=target.parent/self.campaign['battery_file']
            self.assertEqual(battery.read_bytes(),(BASE/'campaign'/battery.name).read_bytes())
            battery.write_bytes(b'x'*131072)
            with self.assertRaises(AssertionError):campaign(self.campaign,target.parent)


if __name__=='__main__':unittest.main()
