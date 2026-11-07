"""Reject incomplete generated area publication before replacing public bytes."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import generated_area_review_contract as contract
import publish_generated_area_review as publisher
from verify_generated_area_review_update import required_keys, verify_elf_binding

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT/'mods/hoenn/generated-area-review-validation/baseline'


class GeneratedAreaReviewRelease(unittest.TestCase):
    def fixtures(self, root):
        names = ('Gen1-4-Normal', 'Gen1-4-Hard', 'Gen1-9-Normal', 'Gen1-9-Hard', 'TESTE')
        editions = [dict(edition=name, sha256=hashlib.sha256(name.encode()).hexdigest()) for name in names]
        info = dict(parent_rom_sha256='f'*64, integration_layers=['previous']*170+[contract.SCOPE],
                    variants=[dict(file='Pokemon-Journey-'+row['edition']+'.gba', sha256=row['sha256'])
                              for row in editions if row['edition'] != 'TESTE'])
        identities = {'common': info['parent_rom_sha256'], 'test': editions[-1]['sha256'],
                      **{row['file']: row['sha256'] for row in info['variants']}}
        rows = []
        for index, (target, kind) in enumerate(sorted(required_keys(info))):
            name = str(index)+'.json'
            (root/name).write_text(json.dumps(dict(passed=True, kind=kind, rom_sha256=identities[target])))
            rows.append(dict(target=target, kind=kind, file=name))
        frozen, plan = root/'frozen.json', root/'plan.json'
        frozen.write_text(json.dumps(dict(parent_rom_sha256=info['parent_rom_sha256'], editions=editions)))
        plan.write_text(json.dumps(dict(proofs=rows)))
        return frozen, plan, info, editions[-1], rows

    def test_plan_requires_two_common_and_ten_edition_proofs(self):
        with tempfile.TemporaryDirectory(prefix='generated-area-plan-', dir='/tmp') as directory:
            root = Path(directory)
            frozen, _, info, _, rows = self.fixtures(root)
            keys = required_keys(info)
            self.assertEqual(len(keys), 12)
            self.assertEqual({kind for target, kind in keys if target == 'common'},
                             {'generated-area-review-source', 'generated-area-review-native'})
            self.assertEqual(len(publisher.write_plan(root, frozen, root/'selected.json')['proofs']), 12)
            native = next(row for row in rows if row['kind'] == 'generated-area-review-native')
            path = root/native['file']
            report = json.loads(path.read_bytes())
            report['rom_sha256'] = contract.PARENT_ROM_SHA256
            path.write_text(json.dumps(report))
            with self.assertRaisesRegex(AssertionError, 'incomplete'):
                publisher.write_plan(root, frozen, root/'rejected.json')
            self.assertFalse((root/'rejected.json').exists())

    def test_duplicate_current_report_cannot_choose_a_preferred_copy(self):
        with tempfile.TemporaryDirectory(prefix='generated-area-duplicate-', dir='/tmp') as directory:
            root = Path(directory)
            frozen, _, _, _, rows = self.fixtures(root)
            shutil.copyfile(root/rows[0]['file'], root/'duplicate.json')
            with self.assertRaisesRegex(AssertionError, 'Ambiguous'):
                publisher.write_plan(root, frozen, root/'selected.json')

    def test_unfinished_contract_cannot_reach_packaging(self):
        for hashes, native in (({}, True), ({'map.bin': 'a'*64}, False)):
            with self.subTest(hashes=hashes, native=native), \
                 patch.object(contract, 'PREPARED_SHA256', hashes), \
                 patch.object(contract, 'NATIVE_CONTRACT_FINALIZED', native), \
                 patch.object(publisher, 'package') as package:
                with self.assertRaises(AssertionError):
                    publisher.prevalidate('/unused', '/unused', '/unused')
                package.assert_not_called()

    def test_common_proofs_require_the_same_rom_and_elf_once_each(self):
        source = dict(elf_sha256='a'*64, rom_sha256='f'*64)
        reports = [('generated-area-review-source', source), ('generated-area-review-native', dict(source))]
        verify_elf_binding(reports)
        for key in ('elf_sha256', 'rom_sha256'):
            with self.subTest(key=key), self.assertRaises(AssertionError):
                verify_elf_binding([reports[0], (reports[1][0], dict(source, **{key: 'b'*64}))])
        for invalid in (reports[:1], reports+[reports[0]]):
            with self.assertRaises(AssertionError):
                verify_elf_binding(invalid)

    def test_preflight_verifies_the_exported_dependency_graph(self):
        with tempfile.TemporaryDirectory(prefix='generated-area-export-', dir='/tmp') as directory:
            root = Path(directory)
            _, plan, info, review, _ = self.fixtures(root)
            shutil.copytree(BASELINE, root/'baseline')
            previous = json.loads((BASELINE/'versions.json').read_bytes())
            info['integration_layers'] = previous['integration_layers']+[contract.SCOPE]
            save = root/'tested.sav'
            save.write_bytes(bytes(131072))
            checked = []
            def strict(report, directory, *args):
                checked.append(Path(directory))
                assert (Path(directory)/'required-native-frame.png').is_file(), 'Native attachment omitted by export'
            with patch.object(publisher, 'require_final_contract'), \
                 patch('verify_coast_scenery_review_update.verify_update'), \
                 patch.object(publisher, 'package', return_value=info), \
                 patch.object(publisher, 'package_review', return_value=review), \
                 patch.object(publisher, 'verify_proof', side_effect=strict):
                with self.assertRaisesRegex(AssertionError, 'omitted by export'):
                    publisher.prevalidate(root, root, plan, save)
            self.assertEqual(len(checked), 1)
            self.assertNotEqual(checked[0], root)


if __name__ == '__main__':
    unittest.main()
