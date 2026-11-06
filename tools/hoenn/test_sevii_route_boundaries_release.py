"""Reject incomplete boundary releases before changing published artifacts."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import sevii_route_boundaries_contract as contract
import publish_sevii_route_boundaries as publisher
from verify_sevii_route_boundaries_update import required_keys, verify_elf_binding

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT/'mods/hoenn/sevii-route-boundaries-validation/baseline'


class SeviiRouteBoundariesRelease(unittest.TestCase):
    def fixtures(self, root):
        names = ('Gen1-4-Normal', 'Gen1-4-Hard', 'Gen1-9-Normal', 'Gen1-9-Hard', 'TESTE')
        editions = [dict(edition=name, sha256=hashlib.sha256(name.encode()).hexdigest()) for name in names]
        raw_sha = 'f'*64
        frozen = dict(parent_rom_sha256=raw_sha, editions=editions)
        previous = json.loads((BASELINE/'versions.json').read_bytes())
        info = dict(parent_rom_sha256=raw_sha, integration_layers=previous['integration_layers']+[contract.SCOPE],
                    variants=[dict(file='Pokemon-Journey-'+row['edition']+'.gba', sha256=row['sha256'])
                              for row in editions if row['edition'] != 'TESTE'])
        identities = {'common': raw_sha, 'test': editions[-1]['sha256'],
                      **{row['file']: row['sha256'] for row in info['variants']}}
        rows = []
        for index, (target, kind) in enumerate(sorted(required_keys(info))):
            name = str(index)+'.json'
            (root/name).write_text(json.dumps(dict(passed=True, kind=kind, rom_sha256=identities[target])))
            rows.append(dict(target=target, kind=kind, file=name))
        frozen_path, plan_path = root/'frozen.json', root/'plan.json'
        frozen_path.write_text(json.dumps(frozen))
        plan_path.write_text(json.dumps(dict(proofs=rows)))
        return frozen_path, plan_path, info, editions[-1], rows

    def test_twelve_current_reports_cover_source_native_and_each_edition(self):
        with tempfile.TemporaryDirectory(prefix='sevii-boundary-plan-', dir='/tmp') as directory:
            root = Path(directory)
            frozen, _, info, _, rows = self.fixtures(root)
            self.assertEqual(len(required_keys(info)), 12)
            self.assertEqual({kind for target, kind in required_keys(info) if target == 'common'},
                             {'sevii-route-boundaries-source', 'sevii-route-boundaries-native'})
            self.assertEqual(len(publisher.write_plan(root, frozen, root/'selected.json')['proofs']), 12)
            for target, kind in required_keys(info):
                if target != 'common':
                    self.assertIn(kind, {'cold-boot', 'review-mode'})
            native = next(row for row in rows if row['kind'] == 'sevii-route-boundaries-native')
            file = root/native['file']
            report = json.loads(file.read_bytes())
            report['rom_sha256'] = contract.PARENT_ROM_SHA256
            file.write_text(json.dumps(report))
            with self.assertRaisesRegex(AssertionError, 'incomplete'):
                publisher.write_plan(root, frozen, root/'rejected.json')
            self.assertFalse((root/'rejected.json').exists())

    def test_unfinished_contract_cannot_reach_packaging(self):
        for hashes, native in (({}, True), ({'map.bin': 'a'*64}, False)):
            with self.subTest(hashes=hashes, native=native), \
                 patch.object(contract, 'PREPARED_SHA256', hashes), \
                 patch.object(contract, 'NATIVE_CONTRACT_FINALIZED', native), \
                 patch.object(publisher, 'package') as package:
                with self.assertRaises(AssertionError):
                    publisher.prevalidate('/unused', '/unused', '/unused')
                package.assert_not_called()

    def test_source_and_native_must_share_one_compiled_identity(self):
        source = dict(elf_sha256='a'*64, rom_sha256='f'*64)
        native = dict(source)
        reports = [('sevii-route-boundaries-source', source), ('sevii-route-boundaries-native', native)]
        verify_elf_binding(reports)
        for key in ('elf_sha256', 'rom_sha256'):
            with self.subTest(key=key):
                changed = dict(native, **{key: 'b'*64})
                with self.assertRaises(AssertionError):
                    verify_elf_binding([reports[0], ('sevii-route-boundaries-native', changed)])
        with self.assertRaises(AssertionError):
            verify_elf_binding(reports[:1])
        with self.assertRaises(AssertionError):
            verify_elf_binding(reports+[reports[0]])

    def test_preflight_checks_exported_observations_before_replacing_roms(self):
        with tempfile.TemporaryDirectory(prefix='sevii-boundary-export-', dir='/tmp') as directory:
            root = Path(directory)
            _, plan, info, review, _ = self.fixtures(root)
            shutil.copytree(BASELINE, root/'baseline')
            save = root/'tested.sav'
            save.write_bytes(bytes(131072))
            picture = root/'required-boundary-frame.png'
            picture.write_bytes(b'native evidence omitted from captures')
            checked = []
            def strict(report, directory, *args):
                checked.append(Path(directory))
                assert (Path(directory)/picture.name).is_file(), 'Boundary observation omitted by export'
            with patch.object(publisher, 'require_final_contract'), \
                 patch('verify_game_continuity_review_update.verify_update'), \
                 patch.object(publisher, 'package', return_value=info), \
                 patch.object(publisher, 'package_review', return_value=review), \
                 patch.object(publisher, 'verify_proof', side_effect=strict):
                with self.assertRaisesRegex(AssertionError, 'omitted by export'):
                    publisher.prevalidate(root, root, plan, save)
            self.assertEqual(len(checked), 1)
            self.assertNotEqual(checked[0], root)


if __name__ == '__main__':
    unittest.main()
