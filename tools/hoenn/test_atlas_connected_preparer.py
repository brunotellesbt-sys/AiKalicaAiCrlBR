"""Unfinished/changed source proofs cannot authorize private materialization."""
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from atlas_surf_candidate_migration import build_tables
from prepare_atlas_connected_layout import diagnostic, prepare


class ConnectedPreparationGuards(unittest.TestCase):
    def test_failed_or_changed_source_report_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            source=dict(passed=True,errors=[],pending=[],generated_water_sccs=1)
            plain=json.dumps(source).encode();raw=gzip.compress(plain,mtime=0)
            (root/'source.json.gz').write_bytes(raw)
            review=dict(source_passed=True,generated_water_sccs=1,candidate_identity_history={'checked':True},
                        additional_native_edges_preview=True,files={'source.json.gz':dict(
                            sha256=hashlib.sha256(raw).hexdigest(),json_sha256=hashlib.sha256(plain).hexdigest())})
            (root/'review.json').write_text(json.dumps(review));self.assertEqual(diagnostic(root)[1]['source'],source)
            (root/'source.json.gz').write_bytes(gzip.compress(plain+b' ',mtime=0))
            with self.assertRaisesRegex(ValueError,'changed'):diagnostic(root)
            review['source_passed']=False;(root/'review.json').write_text(json.dumps(review))
            with self.assertRaisesRegex(ValueError,'passing'):diagnostic(root)

    def test_existing_private_source_is_preserved_before_any_source_read(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);target=root/'old-source';target.mkdir();(target/'keep').write_text('partial work')
            with self.assertRaisesRegex(ValueError,'Preserve|preserve'):
                prepare(target,root/'missing-parent',root/'missing-review',root/'missing-trips',root/'missing-ROM')
            self.assertEqual((target/'keep').read_text(),'partial work')

    def test_safe_looking_terrain_alone_cannot_create_a_save_rescue_table(self):
        with self.assertRaisesRegex(ValueError,'physical graph'):
            build_tables(None,None,None,None,physical_graph=None)


if __name__=='__main__':unittest.main()
