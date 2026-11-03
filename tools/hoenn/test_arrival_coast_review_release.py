"""Arrival/coast publication must reject unobserved or stale evidence."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import arrival_coast_review_contract as contract
import publish_arrival_coast_review as publisher
from verify_arrival_coast_review_update import required_keys, require_final_contract, verify_elf_binding


class ArrivalCoastRelease(unittest.TestCase):
    def test_each_of_five_editions_requires_actual_cold_boot_and_review(self):
        info=dict(variants=[dict(file='Pokemon-Journey-'+name+'.gba') for name in
            ('Gen1-4-Normal','Gen1-4-Hard','Gen1-9-Normal','Gen1-9-Hard')])
        keys=required_keys(info)
        self.assertEqual(len(keys),13)
        self.assertEqual({kind for target,kind in keys if target=='common'},
            {'arrival-coast-source','arrival-coast-landing','arrival-coast-photos'})
        for target in {'test',*[r['file'] for r in info['variants']]}:
            self.assertIn((target,'cold-boot'),keys)
            self.assertIn((target,'review-mode'),keys)

    def test_unreviewed_or_unobserved_contract_cannot_publish(self):
        for hashes,native in (({},True),({'input':'hash'},False)):
            with self.subTest(hashes=hashes,native=native), \
                 patch.object(contract,'PREPARED_SHA256',hashes), \
                 patch.object(contract,'NATIVE_CONTRACT_FINALIZED',native), \
                 patch.object(publisher,'package') as package:
                with self.assertRaises(AssertionError):
                    publisher.prevalidate(Path('/unused'),Path('/unused'),Path('/unused'))
                package.assert_not_called()

    def test_mixed_native_elf_is_rejected(self):
        source=dict(elf_sha256='a'*64)
        photos=dict(elf_sha256='a'*64)
        rows=[('arrival-coast-source',source),('arrival-coast-photos',photos)]
        verify_elf_binding(rows)
        photos['elf_sha256']='b'*64
        with self.assertRaises(AssertionError):verify_elf_binding(rows)

    def test_missing_or_short_staged_battery_stops_before_packaging(self):
        with tempfile.TemporaryDirectory(prefix='arrival-save-') as directory:
            root=Path(directory);save=root/'test.sav'
            for content in (None,b'short'):
                if content is not None:save.write_bytes(content)
                with patch.object(publisher,'require_final_contract'), \
                     patch.object(publisher,'package') as package:
                    with self.assertRaisesRegex(AssertionError,'staged review save'):
                        publisher.prevalidate(root,root,root/'plan',save)
                    package.assert_not_called()


if __name__=='__main__':unittest.main()
