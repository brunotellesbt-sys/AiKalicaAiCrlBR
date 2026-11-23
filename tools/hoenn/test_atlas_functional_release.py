"""An optimistic flag or refreshed report cannot replace the reviewed bytes."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from verify_atlas_functional_release import check_identity,verify_tree


class FunctionalEvidenceGuards(unittest.TestCase):
    def test_passed_report_still_needs_the_same_rom_elf_and_marker(self):
        frozen=dict(rom_sha256='1'*64,elf_sha256='2'*64,marker_sha256='3'*64)
        artifacts={'pokeemerald.gba':'1'*64,'pokeemerald.elf':'2'*64,'.journey-atlas-surf-layout':'3'*64}
        check_identity(dict(passed=True,artifact_sha256=artifacts),frozen)
        for name in artifacts:
            wrong=deepcopy(artifacts);wrong[name]='0'*64
            with self.assertRaisesRegex(AssertionError,'mixed native artifact'):
                check_identity(dict(passed=True,artifact_sha256=wrong),frozen)

    def test_rehashed_capture_or_new_attachment_cannot_replace_the_pinned_index(self):
        digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);capture=root/'capture.png';capture.write_bytes(b'native capture')
            index=root/'index.json';index.write_text(json.dumps({'capture.png':digest(capture)}))
            pinned=digest(index);verify_tree(root,'index.json',pinned)
            capture.write_bytes(b'different native capture')
            with self.assertRaisesRegex(AssertionError,'Changed native attachment'):
                verify_tree(root,'index.json',pinned)
            index.write_text(json.dumps({'capture.png':digest(capture)}))
            with self.assertRaisesRegex(AssertionError,'index changed'):
                verify_tree(root,'index.json',pinned)
            pinned=digest(index);(root/'unreviewed.png').write_bytes(b'unreviewed')
            with self.assertRaisesRegex(AssertionError,'Unindexed'):
                verify_tree(root,'index.json',pinned)
