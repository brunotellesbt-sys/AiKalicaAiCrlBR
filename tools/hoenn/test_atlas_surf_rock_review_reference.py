"""Compact download references must authenticate the external review files."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from verify_atlas_surf_checkpoint import verify_rocks103_evidence


class RockReviewReference(unittest.TestCase):
    def fixture(self,root):
        base=root/'docs/design/native-rock-fragments-review';base.mkdir(parents=True)
        summary=dict(source_repairs=103,maps=20,complete_large_boulders_preserved=462,suspect_pieces_after=0,
            final_release_validated=False,native_ROM_validation_complete=False)
        (base/'summary.json').write_text(json.dumps(summary));(base/'capture.png').write_bytes(b'unchanged-capture')
        def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
        (base/'SHA256SUMS').write_text(''.join(sha(base/n)+'  '+n+'\n' for n in ['summary.json','capture.png']))
        reference=dict(scope='native-General-103-rock-fragments',final_release_validated=False,
            native_ROM_validation_complete=False,
            summary=dict(file=(base/'summary.json').relative_to(root).as_posix(),sha256=sha(base/'summary.json')),
            evidence_manifest=dict(file=(base/'SHA256SUMS').relative_to(root).as_posix(),sha256=sha(base/'SHA256SUMS')))
        target=root/'docs/design/atlas-surf-layout/rocks103-checkpoint.json';target.parent.mkdir(parents=True)
        target.write_text(json.dumps(reference));return base,target,reference

    def test_all_external_review_bytes_are_authenticated(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);base,_,_=self.fixture(root);self.assertIsNotNone(verify_rocks103_evidence(root))
            (base/'capture.png').write_bytes(b'changed-capture')
            with self.assertRaisesRegex(AssertionError,'Changed rock review evidence'):verify_rocks103_evidence(root)

    def test_external_manifest_cannot_escape_its_review_directory(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);base,target,reference=self.fixture(root)
            manifest=base/'SHA256SUMS';manifest.write_text('0'*64+'  ../escape\n')
            reference['evidence_manifest']['sha256']=hashlib.sha256(manifest.read_bytes()).hexdigest()
            target.write_text(json.dumps(reference))
            with self.assertRaises(AssertionError):verify_rocks103_evidence(root)


if __name__=='__main__':unittest.main()
