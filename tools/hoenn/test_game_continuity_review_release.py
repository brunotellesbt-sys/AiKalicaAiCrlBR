"""Stop stale or incomplete game-continuity evidence before public mutations."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import game_continuity_review_contract as contract
import publish_game_continuity_review as publisher
from verify_game_continuity_review_update import required_keys,verify_elf_binding


class GameContinuityRelease(unittest.TestCase):
    def fixtures(self, root):
        names = ('Gen1-4-Normal','Gen1-4-Hard','Gen1-9-Normal','Gen1-9-Hard','TESTE')
        editions = [dict(edition=name,sha256=hashlib.sha256(name.encode()).hexdigest()) for name in names]
        raw_sha = 'f'*64
        frozen = dict(parent_rom_sha256=raw_sha,editions=editions)
        info = dict(parent_rom_sha256=raw_sha,variants=[dict(file='Pokemon-Journey-'+row['edition']+'.gba',
            sha256=row['sha256']) for row in editions if row['edition'] != 'TESTE'])
        identities = {'common':raw_sha,'test':editions[-1]['sha256'],
                      **{row['file']:row['sha256'] for row in info['variants']}}
        rows = []
        for index,(target,kind) in enumerate(sorted(required_keys(info))):
            name = str(index)+'.json'
            (root/name).write_text(json.dumps(dict(passed=True,kind=kind,rom_sha256=identities[target])))
            rows.append(dict(target=target,kind=kind,file=name))
        frozen_path,plan_path = root/'frozen.json',root/'plan.json'
        frozen_path.write_text(json.dumps(frozen))
        plan_path.write_text(json.dumps(dict(proofs=rows)))
        return frozen_path,plan_path,info,editions[-1],rows

    def test_all_five_editions_require_fresh_review_and_cold_boot(self):
        info = dict(variants=[dict(file='Pokemon-Journey-'+name+'.gba') for name in
            ('Gen1-4-Normal','Gen1-4-Hard','Gen1-9-Normal','Gen1-9-Hard')])
        keys = required_keys(info)
        self.assertEqual(len(keys),13)
        self.assertEqual({kind for target,kind in keys if target == 'common'},
                         {'game-continuity-source','game-continuity-campaign','game-continuity-coasts'})
        for target in {'test',*[row['file'] for row in info['variants']]}:
            self.assertIn((target,'review-mode'),keys)
            self.assertIn((target,'cold-boot'),keys)

    def test_unpinned_or_unobserved_contract_never_reaches_packaging(self):
        for hashes,native in (({},True),({'input':'hash'},False)):
            with self.subTest(hashes=hashes,native=native), \
                 patch.object(contract,'PREPARED_SHA256',hashes), \
                 patch.object(contract,'NATIVE_CONTRACT_FINALIZED',native), \
                 patch.object(publisher,'package') as package:
                with self.assertRaises(AssertionError):
                    publisher.prevalidate(Path('/unused'),Path('/unused'),Path('/unused'))
                package.assert_not_called()

    def test_mixed_native_elf_cannot_be_bound_to_one_source_proof(self):
        source = dict(elf_sha256='a'*64)
        campaign = dict(elf_sha256='a'*64)
        rows = [('game-continuity-source',source),('game-continuity-campaign',campaign)]
        verify_elf_binding(rows)
        campaign['elf_sha256'] = 'b'*64
        with self.assertRaises(AssertionError):
            verify_elf_binding(rows)
        with self.assertRaises(AssertionError):
            verify_elf_binding(rows+[('game-continuity-source',source)])

    def test_missing_or_short_tested_battery_stops_before_packaging(self):
        with tempfile.TemporaryDirectory(prefix='game-continuity-save-',dir='/tmp') as directory:
            root = Path(directory)
            save = root/'test.sav'
            for content in (None,b'short'):
                if content is not None:
                    save.write_bytes(content)
                with patch.object(publisher,'require_final_contract'), \
                     patch.object(publisher,'package') as package:
                    with self.assertRaisesRegex(AssertionError,'staged review save'):
                        publisher.prevalidate(root,root,root/'plan',save)
                    package.assert_not_called()

    def test_missing_or_stale_native_run_cannot_materialize_a_complete_plan(self):
        for remove in (True,False):
            with self.subTest(remove=remove), tempfile.TemporaryDirectory(prefix='game-continuity-plan-') as directory:
                root = Path(directory)
                frozen,_,_,_,rows = self.fixtures(root)
                output = root/'selected.json'
                self.assertEqual(len(publisher.write_plan(root,frozen,output)['proofs']),13)
                output.unlink()
                source = root/rows[-1]['file']
                if remove:
                    source.unlink()
                else:
                    report = json.loads(source.read_bytes())
                    report['rom_sha256'] = contract.PARENT_ROM_SHA256
                    source.write_text(json.dumps(report))
                with self.assertRaisesRegex(AssertionError,'incomplete'):
                    publisher.write_plan(root,frozen,output)
                self.assertFalse(output.exists())

    def test_strict_observations_are_checked_in_exported_folder_before_publication(self):
        with tempfile.TemporaryDirectory(prefix='game-continuity-export-') as directory:
            root = Path(directory)
            _,plan,info,test,rows = self.fixtures(root)
            prior = Path(__file__).resolve().parents[2]/'mods/hoenn/game-continuity-review-validation/baseline'
            (root/'baseline').mkdir()
            for name in ('versions.json','review.json','test.sav'):
                shutil.copyfile(prior/name,root/'baseline'/name)
            save = root/'tested.sav'
            save.write_bytes(bytes(131072))
            # This file is present in the original observations but omitted
            # from the recursive attachment manifest, like the eight missing
            # forest-animation pictures found during layer 167 publication.
            picture = root/'required-native-frame.png'
            picture.write_bytes(b'picture supplied by the native runner')
            checked_folders = []
            def strict(report,directory,*args):
                checked_folders.append(Path(directory))
                assert (Path(directory)/picture.name).is_file(), 'Native picture omitted by export'
            with patch.object(publisher,'require_final_contract'), \
                 patch('verify_arrival_coast_review_update.verify_update'), \
                 patch.object(publisher,'package',return_value=info), \
                 patch.object(publisher,'package_review',return_value=test), \
                 patch.object(publisher,'verify_proof',side_effect=strict):
                with self.assertRaisesRegex(AssertionError,'omitted by export'):
                    publisher.prevalidate(root,root,plan,save)
            self.assertEqual(len(checked_folders),1)
            self.assertNotEqual(checked_folders[0],root)


if __name__ == '__main__':
    unittest.main()
