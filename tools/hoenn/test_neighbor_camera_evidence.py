"""Reject old ROM proofs and incomplete pre-entry boulders."""
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from verify_neighbor_layout_camera import verify

BASE=Path(__file__).resolve().parents[2]/'docs/design/neighbor-layout-camera-review'

class NeighborCameraEvidence(unittest.TestCase):
    def test_another_ROM_cannot_claim_the_fixed_camera(self):
        f=json.loads(gzip.decompress((BASE/'compiled-freeze-v7.json.gz').read_bytes()));f['rom_sha256']='0'*64
        with self.assertRaisesRegex(AssertionError,'another ROM'):verify(f,BASE/'native-v7')

    def test_pre_entry_water_cannot_pass_with_a_fixed_top_level_flag(self):
        f=json.loads(gzip.decompress((BASE/'compiled-freeze-v7.json.gz').read_bytes()))
        r=json.loads((BASE/'native-v7/neighbor-camera-native.json').read_bytes());r['cases'][0]['before']['cells'][0]['metatile']=0x170
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)
            for p in (BASE/'native-v7').iterdir():
                if p.name!='neighbor-camera-native.json':(target/p.name).symlink_to(p)
            (target/'neighbor-camera-native.json').write_text(json.dumps(r))
            with self.assertRaises(AssertionError):verify(f,target)

if __name__=='__main__':unittest.main()
