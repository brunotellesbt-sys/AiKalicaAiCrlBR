"""Keep the tested TESTE battery private until publication preflight passes."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import publish_coastal_ecology as publisher
from verify_coastal_ecology_update import verify_proof


class StagedReviewSave(unittest.TestCase):
    def test_missing_or_short_staged_save_is_rejected_before_packaging(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);save=root/'test.sav'
            for content in (None,b'short'):
                if content is not None:save.write_bytes(content)
                with patch.object(publisher,'require_final_contract'), \
                     patch.object(publisher,'package') as package:
                    with self.assertRaisesRegex(AssertionError,'staged review save'):
                        publisher.prevalidate(root/'source',root/'validation',root/'plan',save)
                    package.assert_not_called()

    def test_test_boot_and_review_proofs_bind_the_same_staged_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            save=Path(directory)/'test.sav';save.write_bytes(b's'*131072)
            sha=hashlib.sha256(save.read_bytes()).hexdigest()
            cold=dict(passed=True,fresh_rom_boot_to_title=True,fresh_rom_title_to_new_game=True,
                no_assert_screen=True,controllers_only=True,no_game_memory_writes=True,
                bundled_save_continue_to_field=True,bundled_save_sha256=sha)
            checks=dict(trainer_approach_result=0,random_wild_attempts=200,save_sha256=sha)
            for key in ('native_flash_save_exported','no_random_encounters','no_fishing_encounters',
                        'no_sweet_scent_encounters','no_rock_smash_encounters',
                        'no_automatic_approach_after_600_frames'):checks[key]=True
            review=dict(passed=True,fixture_wild_encounters_disabled=False,checks=checks)
            for kind,report in [('cold-boot',cold),('review-mode',review)]:
                verify_proof(report,save.parent,kind,'test',save,{},{})
            save.write_bytes(b'x'*131072)
            for kind,report in [('cold-boot',cold),('review-mode',review)]:
                with self.assertRaises(AssertionError):
                    verify_proof(report,save.parent,kind,'test',save,{},{})

    def test_only_prevalidated_unchanged_bytes_are_installed(self):
        for mutate in ('none','relative_cli','after_preflight','during_package'):
            with self.subTest(mutate=mutate),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);validation=root/'validation';before=validation/'baseline'
                before.mkdir(parents=True)
                old=dict(validation_scope='generated-world-audit',parent_rom_sha256='old',
                    historical_validation={},previous_validation={},variants=[],proofs=[])
                (before/'versions.json').write_text(json.dumps(old))
                (before/'review.json').write_text(json.dumps(dict(sha256='old-test')))
                (before/'test.sav').write_bytes(b'o'*131072)
                save=validation/'test.sav';tested=b's'*131072;save.write_bytes(tested)
                public=root/'roms/rom-de-teste';public.mkdir(parents=True)
                destination=public/'Pokemon-Journey-TESTE.sav';destination.write_bytes(b'o'*131072)
                output=root/'versions'
                def prevalidate(*args):
                    self.assertTrue(all(Path(path).is_absolute() for path in args))
                    sha=hashlib.sha256(tested).hexdigest()
                    if mutate=='after_preflight':save.write_bytes(b'x'*131072)
                    return old,[],sha
                def package(source,where):
                    where.mkdir(parents=True)
                    if mutate=='during_package':save.write_bytes(b'x'*131072)
                    return dict(variants=[],proofs=[])
                with patch.object(publisher,'ROOT',root), \
                     patch.object(publisher,'prevalidate',side_effect=prevalidate), \
                     patch.object(publisher,'preserve_history'), \
                     patch.object(publisher,'package',side_effect=package), \
                     patch.object(publisher,'package_review'), \
                     patch.object(publisher,'verify'),patch.object(publisher,'build_archive'):
                    if mutate not in ('none','relative_cli'):
                        with self.assertRaisesRegex(AssertionError,'save changed'):
                            publisher.publish(root/'source',validation,output,root/'plan',save)
                        self.assertEqual(destination.read_bytes(),b'o'*131072)
                    else:
                        paths=[root/'source',validation,output,root/'plan',save]
                        if mutate=='relative_cli':paths=[Path(os.path.relpath(path)) for path in paths]
                        info=publisher.publish(*paths)
                        self.assertEqual(destination.read_bytes(),tested)
                        self.assertEqual(info['previous_port_validation']['manifest'],
                            'validation/baseline/versions.json')


if __name__=='__main__':unittest.main()
