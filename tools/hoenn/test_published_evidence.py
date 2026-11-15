"""Keep archived evidence usable without certifying candidate ROM bytes."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock

import published_evidence as evidence
from verify_fuchsia_update import harbor_baseline
from verify_versions import verify


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class HistoricalEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.current = self.root/'mods/hoenn/versions'
        self.current.mkdir(parents=True)
        self.addCleanup(mock.patch.stopall)
        mock.patch.object(evidence, 'ROOT', self.root).start()
        mock.patch.object(evidence, 'CURRENT', self.current).start()
        evidence.baseline.cache_clear()
        evidence.evidence_rom.cache_clear()
        self.addCleanup(evidence.baseline.cache_clear)
        self.addCleanup(evidence.evidence_rom.cache_clear)

        self.archive = self.root/'mods/hoenn/validation-baselines/pr79'
        self.archive.mkdir(parents=True)
        self.name = 'Pokemon-Journey-Gen1-4-Normal.gba'
        parent = bytes(range(256))
        compressed = gzip.compress(parent, mtime=0)
        (self.archive/'parent.gba.gz').write_bytes(compressed)
        variant = bytearray(parent)
        variant[192:196] = struct.pack('<HBB', 493, 0, 0)
        variant[0xA0:0xAC] = b'JOURNEY G4 N'
        variant[0xBD] = (-sum(variant[0xA0:0xBD])-0x19)&255
        self.archived_variant = bytes(variant)
        report = json.dumps({'rom_sha256': digest(parent), 'passed': True}).encode()
        (self.archive/'battle.json').write_bytes(report)
        self.old = dict(
            validated=True, parent_rom_sha256=digest(parent), build_rules_offset=192,
            variants=[dict(file=self.name, max_national=493,
                           perfect_trainer_ivs=False, sha256=digest(variant))],
            proofs=[dict(kind='battle-interactions', file='battle.json',
                         target='common', sha256=digest(report))])
        old_reference = self.write_manifest(self.archive/'versions.json', self.old)
        old_reference.update(parent_rom_sha256=digest(parent),
                             compressed_parent_sha256=digest(compressed))

        harbor = dict(validated=True, validation_scope='sevii-surf-connections',
                      integration_layers=['original'], parent_rom_sha256='harbor',
                      variants=[], proofs=[])
        harbor_reference = self.write_manifest(self.root/'harbor/versions.json', harbor)
        self.prior = dict(
            validated=True, validation_scope='generated-area-review',
            integration_layers=['original', 'generated-area-review'],
            parent_rom_sha256='parent-171', variants=[], proofs=[],
            historical_validation=old_reference,
            previous_port_validation=harbor_reference)
        self.prior_path = self.root/'mods/hoenn/atlas-surf-layout-validation/baseline/versions.json'
        prior_reference = self.write_manifest(self.prior_path, self.prior)
        self.candidate = dict(
            candidate=True, validated=False, final_release_validated=False,
            validation_scope='atlas-surf-layout-candidate', proofs=[],
            integration_layers=self.prior['integration_layers']+['atlas-surf-layout'],
            parent_rom_sha256='parent-172', variants=[],
            previous_port_validation=prior_reference)
        self.save_candidate()

    def write_manifest(self, path, info):
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = (json.dumps(info, indent=2)+'\n').encode()
        path.write_bytes(raw)
        return dict(manifest=path.relative_to(self.root).as_posix(),
                    manifest_sha256=digest(raw), retested_on_current_rom=False)

    def save_candidate(self):
        self.write_manifest(self.current/'versions.json', self.candidate)

    def test_candidate_resolves_archive_and_rom_identity_without_claiming_new_proof(self):
        before = copy.deepcopy(self.candidate)
        candidate_rom = b'candidate 172 bytes are different'
        (self.root/'roms').mkdir()
        (self.root/'roms'/self.name).write_bytes(candidate_rom)

        directory, release = evidence.evidence_release('battle-interactions')
        self.assertEqual(directory, self.archive)
        self.assertEqual(release, self.old)
        raw = evidence.evidence_rom(directory, self.name)
        self.assertEqual(raw, self.archived_variant)
        self.assertNotEqual(raw, candidate_rom)
        report = json.loads((directory/release['proofs'][0]['file']).read_bytes())
        self.assertEqual(report['rom_sha256'], release['parent_rom_sha256'])
        self.assertEqual(self.candidate, before)
        self.assertEqual(json.loads((self.current/'versions.json').read_bytes()), before)
        self.assertNotIn('candidate', release)

    def test_harbor_reader_traverses_pinned_layers_without_mutating_candidate(self):
        before = copy.deepcopy(self.candidate)
        release = harbor_baseline(self.candidate)
        self.assertEqual(release['validation_scope'], 'sevii-surf-connections')
        self.assertEqual(self.candidate, before)
        self.assertEqual(evidence.resolve_previous_release(self.candidate), self.prior)

    def test_candidate_still_fails_the_default_final_release_gate(self):
        with self.assertRaisesRegex(AssertionError, 'Unvalidated release'):
            verify(self.current)

    def test_missing_candidate_pin_or_proof_list_is_an_error(self):
        for key in ('previous_port_validation', 'proofs'):
            with self.subTest(key=key):
                info = copy.deepcopy(self.candidate)
                del info[key]
                with self.assertRaises(KeyError):
                    evidence.release_baseline(info)

    def test_candidate_cannot_import_historical_proofs_or_approval_flags(self):
        changes = [('proofs', copy.deepcopy(self.old['proofs'])),
                   ('validated', True), ('candidate', False),
                   ('final_release_validated', True)]
        for key, value in changes:
            with self.subTest(key=key):
                self.candidate[key] = value
                self.save_candidate()
                with self.assertRaises(AssertionError):
                    evidence.evidence_release('battle-interactions')
                self.candidate[key] = [] if key == 'proofs' else key == 'candidate'

    def test_pinned_manifest_hash_and_false_retest_flag_are_required(self):
        reference = self.candidate['previous_port_validation']
        for key, value in [('manifest_sha256', '0'*64),
                           ('retested_on_current_rom', True),
                           ('retested_on_current_rom', 0)]:
            with self.subTest(key=key, value=value):
                changed = copy.deepcopy(reference)
                changed[key] = value
                with self.assertRaises(AssertionError):
                    evidence.pinned_release(changed)
        self.prior_path.write_text(self.prior_path.read_text()+' ')
        with self.assertRaisesRegex(AssertionError, 'hash mismatch'):
            evidence.release_baseline(self.candidate)

    def test_absolute_parent_and_symlink_manifest_paths_are_rejected(self):
        reference = self.candidate['previous_port_validation']
        outside = self.root.parent/(self.root.name+'-outside.json')
        outside.write_bytes(self.prior_path.read_bytes())
        self.addCleanup(outside.unlink)
        (self.root/'escape.json').symlink_to(outside)
        for path in (str(self.prior_path), '../'+outside.name, 'escape.json'):
            with self.subTest(path=path):
                changed = dict(reference, manifest=path)
                with self.assertRaises(AssertionError):
                    evidence.pinned_release(changed)

    def test_ancestor_must_be_validated_and_preserve_the_layer_prefix(self):
        for key, value in [('validated', False),
                           ('integration_layers', ['wrong', 'generated-area-review']),
                           ('integration_layers', self.candidate['integration_layers'])]:
            with self.subTest(key=key, value=value):
                info = copy.deepcopy(self.prior)
                info[key] = value
                changed = copy.deepcopy(self.candidate)
                changed['previous_port_validation'] = self.write_manifest(self.prior_path, info)
                with self.assertRaises(AssertionError):
                    evidence.resolve_previous_release(changed)

    def test_candidate_cannot_skip_171_even_with_an_authenticated_older_manifest(self):
        self.candidate['previous_port_validation'] = self.prior['previous_port_validation']
        with self.assertRaises(AssertionError):
            evidence.release_baseline(self.candidate)

    def test_archived_parent_and_archive_hash_cannot_be_substituted(self):
        for key in ('parent_rom_sha256', 'compressed_parent_sha256'):
            with self.subTest(key=key):
                prior = copy.deepcopy(self.prior)
                prior['historical_validation'][key] = '0'*64
                self.candidate['previous_port_validation'] = self.write_manifest(self.prior_path, prior)
                self.save_candidate()
                with self.assertRaises(AssertionError):
                    evidence.evidence_release('battle-interactions')

    def test_missing_historical_proof_is_not_supplied_by_candidate_bytes(self):
        with self.assertRaisesRegex(AssertionError, 'unrecorded-proof'):
            evidence.evidence_release('unrecorded-proof')


if __name__ == '__main__':
    unittest.main()
