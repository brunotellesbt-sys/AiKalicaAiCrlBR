"""Corruption checks for candidate integrity; no final native gameplay claim."""
import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

import verify_atlas_surf_checkpoint as check


class CandidateMetadataTests(unittest.TestCase):
    def test_final_seal_and_missing_or_stale_proofs_are_rejected(self):
        good = dict(candidate=True, validated=False, final_release_validated=False,
                    validation_scope=check.SCOPE, proofs=[])
        check.candidate_flags(good, proofs=True)
        for key, value in [('validated', True), ('candidate', False),
                           ('final_release_validated', True), ('proofs', [{'sha256': 'old'}])]:
            with self.subTest(key=key), self.assertRaises(AssertionError):
                check.candidate_flags(dict(good, **{key: value}), proofs=True)
        del good['proofs']
        with self.assertRaises(KeyError):
            check.candidate_flags(good, proofs=True)

    def test_history_pin_and_baseline_bytes_are_both_checked(self):
        baseline = check.ROOT / check.BASELINE
        old = check.read_json(baseline)
        info = dict(integration_layers=old['integration_layers'] + ['atlas-surf-layout'],
                    previous_port_validation=dict(manifest=check.BASELINE,
                         manifest_sha256=check.BASELINE_SHA256, retested_on_current_rom=False))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / check.BASELINE
            target.parent.mkdir(parents=True)
            target.write_bytes(baseline.read_bytes())
            check.verify_history(root, info)
            forged = copy.deepcopy(info)
            forged['previous_port_validation']['manifest_sha256'] = '0' * 64
            with self.assertRaises(AssertionError):
                check.verify_history(root, forged)
            target.write_bytes(target.read_bytes() + b' ')
            with self.assertRaises(AssertionError):
                check.verify_history(root, info)

    def test_cold_boot_cannot_be_stale_or_only_claim_freshness_at_top(self):
        report = dict(rom_sha256='current', passed=True, controllers_only=True,
                      no_game_memory_writes=True, fresh_rom_boot_to_title=True,
                      fresh_rom_title_to_new_game=True, no_assert_screen=True,
                      runs=[dict(battery=False, frames=1, fresh_rom_boot_to_title=True,
                                 fresh_rom_title_to_new_game=True)])
        check.verify_cold_report(report, 'current')
        for key, value in [('rom_sha256', 'stale'), ('no_game_memory_writes', False),
                           ('controllers_only', False), ('runs', [dict(battery=True)])]:
            with self.subTest(key=key), self.assertRaises(AssertionError):
                check.verify_cold_report(dict(report, **{key: value}), 'current')

    def test_missing_or_changed_proof_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            info = dict(variants=[], native_cold_boot={})
            review = dict(sha256='current')
            with self.assertRaises(AssertionError):
                check.verify_boots(root, info, review, dict(cold_boot={}))
            path = check.PROOF / 'candidate-cold-boot/TESTE-continued-after-save/cold-boot.json'
            (root / path).parent.mkdir(parents=True)
            (root / path).write_text('{}')
            info['native_cold_boot'] = {'TESTE': dict(report=path.as_posix(), sha256='0' * 64)}
            with self.assertRaises(AssertionError):
                check.verify_boots(root, info, review, dict(cold_boot=info['native_cold_boot']))

    def test_if_candidate_skips_only_another_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / 'mods/hoenn/versions/versions.json'
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps(dict(validation_scope='generated-area-review')))
            self.assertIsNone(check.verify(root, if_candidate=True))
            target.write_text(json.dumps(dict(validation_scope=check.SCOPE)))
            with self.assertRaises(KeyError):
                check.verify(root, if_candidate=True)


class BinaryProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.directory = Path(cls.tmp.name)
        parent = bytearray(check.ROM_BYTES)
        cls.at = 1024
        parent[cls.at:cls.at + 4] = struct.pack('<HBB', 1025, 1, 0)
        cls.info = dict(build_rules_offset=cls.at, parent_header_hex=parent[0xA0:0xBE].hex(),
                        parent_rules_hex=parent[cls.at:cls.at + 4].hex(),
                        parent_rom_sha256=check.digest(parent), variants=[])
        for index, (name, (cap, hard)) in enumerate(check.VARIANTS.items()):
            raw = bytearray(parent)
            raw[0xA0:0xAC] = ('CHECKPOINT%02d' % index).encode()
            raw[cls.at:cls.at + 4] = struct.pack('<HBB', cap, hard, 0)
            raw[0xBD] = (-sum(raw[0xA0:0xBD]) - 0x19) & 255
            (cls.directory / name).write_bytes(raw)
            positions = list(range(0xA0, 0xBE)) + list(range(cls.at, cls.at + 4))
            cls.info['variants'].append(dict(file=name, max_national=cap, perfect_trainer_ivs=hard,
                 bytes=len(raw), sha256=check.digest(raw),
                 patched_byte_offsets=[i for i in positions if raw[i] != parent[i]]))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_profiles_restore_the_same_parent(self):
        restored = check.verify_profiles(self.directory, self.info)
        self.assertEqual(check.digest(restored), self.info['parent_rom_sha256'])

    def test_changed_binary_rejected_even_with_refreshed_edition_hash(self):
        info = copy.deepcopy(self.info)
        row = info['variants'][0]
        path = self.directory / row['file']
        original = path.read_bytes()
        try:
            corrupt = bytearray(original)
            corrupt[2000] ^= 1
            path.write_bytes(corrupt)
            row['sha256'] = check.digest(corrupt)
            with self.assertRaisesRegex(AssertionError, 'Unapproved binary'):
                check.verify_profiles(self.directory, info)
        finally:
            path.write_bytes(original)

    def test_patch_metadata_and_generation_cap_checked(self):
        for field, value in [('patched_byte_offsets', []), ('max_national', 1), ('bytes', 1)]:
            info = copy.deepcopy(self.info)
            info['variants'][0][field] = value
            with self.subTest(field=field), self.assertRaises(AssertionError):
                check.verify_profiles(self.directory, info)


class ArchiveTests(unittest.TestCase):
    def test_archive_must_contain_current_documents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / 'mods/hoenn/versions'
            directory.mkdir(parents=True)
            names = list(check.CONTINUITY_FILES) + ['Aqui/README.md', 'Aqui/ERROS-PARA-PROXIMA-IA.md', 'roms/README.md', 'roms/CANDIDATA-172.json',
                'roms/rom-de-teste/LEIA-ME.md', 'roms/rom-de-teste/review.json',
                'roms/rom-de-teste/SHA256SUMS', 'roms/rom-de-teste/Pokemon-Journey-TESTE.sav']
            for name in names:
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_text(name)
            for name in ('versions.json', 'SHA256SUMS'):
                (directory / name).write_text(name)
            archive = directory / 'Pokemon-Journey-Four-Editions.zip'
            with zipfile.ZipFile(archive, 'w') as bundle:
                for name in names:
                    bundle.write(root / name, name)
                for name in ('versions.json', 'SHA256SUMS'):
                    bundle.write(directory / name, name)
                bundle.writestr('CANDIDATA-EM-VALIDACAO.txt', 'pending')
            summary = dict(archive_bytes=archive.stat().st_size,
                           archive_sha256=check.digest(archive.read_bytes()))
            check.verify_archive(root, directory, dict(variants=[]), summary)
            for name in (check.CONTINUITY_FILES[0], 'Aqui/README.md', 'Aqui/ERROS-PARA-PROXIMA-IA.md'):
                path = root / name
                original = path.read_bytes()
                path.write_text('updated continuity')
                try:
                    with self.subTest(name=name), self.assertRaisesRegex(AssertionError, 'Stale archive entry'):
                        check.verify_archive(root, directory, dict(variants=[]), summary)
                finally:
                    path.write_bytes(original)


if __name__ == '__main__':
    unittest.main()
