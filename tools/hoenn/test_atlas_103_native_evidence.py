"""Reject stale ROM identity and forged pixels in the exported rock evidence."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image

from verify_atlas_103_rocks_native import verify

ROOT=Path(__file__).resolve().parents[2]
FROZEN=ROOT/'docs/design/native-rock-fragments-review/compiled-freeze-v6.json.gz'
NATIVE=FROZEN.parent/'native-v6'


class NativeRockEvidence(unittest.TestCase):
    def test_previous_ROM_cannot_reuse_the_current_native_pass(self):
        frozen=json.loads(gzip.decompress(FROZEN.read_bytes()))
        frozen['rom_sha256']='0'*64
        with self.assertRaisesRegex(AssertionError,'belongs to another ROM'):verify(frozen,NATIVE)

    def test_changed_observed_pixel_is_rejected_even_with_refreshed_capture_hashes(self):
        frozen=json.loads(gzip.decompress(FROZEN.read_bytes()))
        report=json.loads(gzip.decompress((NATIVE/'rocks103-native.json.gz').read_bytes()))
        phase=report['cases'][0]['animation_observations'][0];filename=phase['capture']['file']
        sample=phase['pixels']['cells'][0]['samples'][0];x,y=sample[:2]
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)
            for p in NATIVE.glob('*.png'):
                if p.name!=filename:(target/p.name).symlink_to(p)
            im=Image.open(NATIVE/filename).convert('RGB');old=im.getpixel((x,y));im.putpixel((x,y),tuple((v+128)%256 for v in old));im.save(target/filename)
            new_hash=hashlib.sha256((target/filename).read_bytes()).hexdigest()
            for row in report['captures']:
                if row['file']==filename:row['sha256']=new_hash
            phase['capture']['sha256']=new_hash
            (target/'rocks103-native.json.gz').write_bytes(gzip.compress(json.dumps(report).encode()))
            with self.assertRaisesRegex(AssertionError,'pixels differ'):verify(frozen,target)


if __name__=='__main__':unittest.main()
