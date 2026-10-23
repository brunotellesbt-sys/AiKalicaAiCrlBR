"""Guard the 163 publication gate and immutable 162 historical evidence."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import verify_sevii_integrated_piers_update as historical
from publish_coastal_closures import (
    LEGACY_MEDIA, archive_entries, copy_current_proof, edition_report, publish,
    report_dependencies,
)
from verify_coastal_closures_update import (
    ALLOWED_SOURCE_FILES, BASELINE_SHA256, ROOT, verify_baseline_bytes,
    verify_shore_animation, verify_source, verify_update,
)


BASELINE = ROOT / 'mods/hoenn/coastal-closures-validation/baseline'
VERSIONS = ROOT / 'mods/hoenn/versions'


class CoastalReleaseContracts(unittest.TestCase):
    def source_contract(self):
        """A report-shaped fixture tests rejection, without claiming native proof."""
        report = dict(
            kind='coastal-closures-source', layers=['coastal-closures'],
            parent_rom_sha256='0' * 64, compiled_rom=True, preflight=False,
            changed_files=sorted(ALLOWED_SOURCE_FILES),
            allowed_changed_files=sorted(ALLOWED_SOURCE_FILES),
            source_hashes_checked=30001, independent_replay=True, idempotent=True,
            unrelated_source_files_unchanged=True, save_and_link_abi_unchanged=True,
            atlas_graphics_unchanged=True, gyms_and_campaign_unchanged=True,
            shore_animation=dict(
                native_private_secondary_reload_after_dma_refresh=True,
                secondary_reload_only_marks_pending=True,
                post_dma_refresh_only_after_all_requests_complete=True,
                post_dma_refresh_one_shot_with_private_bank_and_general_callback_guards=True,
                main_vblank_only_reviewed_post_dma_call=True,
                public_tileset_api_only_reviewed_declaration=True))
        info = dict(integration_layers=['coastal-closures'])
        old = dict(parent_rom_sha256='0' * 64)
        return report, info, old

    def test_source_scope_rejects_unrelated_files_even_if_report_calls_them_allowed(self):
        self.assertEqual(len(ALLOWED_SOURCE_FILES), 24)
        report, info, old = self.source_contract()
        verify_source(report, info, old)
        for field in ['changed_files', 'allowed_changed_files']:
            report[field].remove('src/main.c')
            report[field].append('src/battle_main.c')
        with self.assertRaises(AssertionError):
            verify_source(report, info, old)

    def test_source_scope_rejects_each_missing_post_dma_safeguard(self):
        report, info, old = self.source_contract()
        for safeguard in report['shore_animation']:
            with self.subTest(safeguard=safeguard):
                changed = copy.deepcopy(report)
                changed['shore_animation'][safeguard] = False
                with self.assertRaisesRegex(AssertionError, safeguard):
                    verify_source(changed, info, old)

    def test_source_preflight_is_not_accepted_as_compiled_evidence(self):
        report, info, old = self.source_contract()
        report.update(compiled_rom=False, preflight=True)
        with self.assertRaises(AssertionError):
            verify_source(report, info, old)

    def test_native_shore_rejects_unfinished_reload_and_stale_private_phase(self):
        path = edition_report(BASELINE.parent, 'Gen1-9-Normal', 'shore-animation')
        original = json.loads(path.read_bytes())
        for failure in ['pending-at-first-frame', 'reload-not-observed', 'stale-private-phase']:
            with self.subTest(failure=failure):
                report = copy.deepcopy(original)
                if failure == 'pending-at-first-frame':
                    report['connections'][0]['observed_crossings'][0]['private_shore_refresh_pending'] = True
                elif failure == 'reload-not-observed':
                    report['onload_samples'][0]['current_global_phase_after_native_bg_dma_verified'] = False
                else:
                    report['onload_samples'][0]['private_vram_sha256'] = '0' * 64
                with self.assertRaises(AssertionError):
                    verify_shore_animation(report, path.parent)

    def test_unfinished_native_contract_cannot_verify_or_package(self):
        with patch('verify_coastal_closures_update.CONTRACT_FINALIZED', False):
            with self.assertRaisesRegex(AssertionError, 'not finalized'):
                verify_update(Path('/tmp/nonexistent-coastal-release'), {})
            with tempfile.TemporaryDirectory(prefix='coastal-gate-', dir='/tmp') as directory:
                output = Path(directory) / 'output'
                with self.assertRaisesRegex(AssertionError, 'not finalized'):
                    publish(Path('/tmp/nonexistent-coastal-source'), BASELINE.parent, output)
                self.assertFalse(output.exists())

    def test_each_layer162_baseline_has_an_independent_immutable_identity(self):
        for name in BASELINE_SHA256:
            raw = (BASELINE / name).read_bytes()
            verify_baseline_bytes(name, raw)
            with self.assertRaisesRegex(AssertionError, 'baseline changed'):
                verify_baseline_bytes(name, raw + b'\n')

    def test_changed_baseline_prevents_packaging_before_any_output(self):
        with tempfile.TemporaryDirectory(prefix='coastal-pinned-', dir='/tmp') as directory:
            root = Path(directory)
            baseline = root / 'validation/baseline'
            baseline.mkdir(parents=True)
            info = json.loads((BASELINE / 'versions.json').read_bytes())
            info['parent_rom_sha256'] = '0' * 64
            (baseline / 'versions.json').write_text(json.dumps(info))
            with patch('verify_coastal_closures_update.CONTRACT_FINALIZED', True), \
                    patch('publish_coastal_closures.package') as package:
                with self.assertRaisesRegex(AssertionError, 'baseline changed'):
                    publish(root / 'source', baseline.parent, root / 'output')
                package.assert_not_called()
                self.assertFalse((root / 'output').exists())

    def test_layer162_manifest_and_all42_original_report_hashes_are_preserved(self):
        raw = (BASELINE / 'versions.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         'd484518546094cf6562cbf314d08fb47e291f5e3f6c66acdbcc198c59eefbd9f')
        info = json.loads(raw)
        self.assertEqual(info['validation_scope'], 'sevii-integrated-piers')
        self.assertEqual((len(info['integration_layers']), len(info['proofs'])), (162, 42))
        for proof in info['proofs']:
            self.assertEqual(hashlib.sha256((VERSIONS / proof['file']).read_bytes()).hexdigest(),
                             proof['sha256'])

    def test_historical162_verification_uses_pinned_review_and_save_without_current_roms(self):
        info = json.loads((BASELINE / 'versions.json').read_bytes())
        review = json.loads((BASELINE / 'review.json').read_bytes())
        with tempfile.TemporaryDirectory(prefix='coastal-history-', dir='/tmp') as directory:
            output = Path(directory)
            shutil.copytree(VERSIONS / 'evidence', output / 'evidence')
            self.assertFalse(any(output.glob('*.gba')))
            with patch.object(historical, 'verify_review', side_effect=AssertionError('Current review must not be read')):
                historical.verify_update(output, info, historical_review=review,
                                         historical_save=BASELINE / 'test.sav')

    def test_historical162_rejects_a_relabelled_review_identity(self):
        info = json.loads((BASELINE / 'versions.json').read_bytes())
        review = copy.deepcopy(json.loads((BASELINE / 'review.json').read_bytes()))
        review['base_normal_sha256'] = '0' * 64
        with self.assertRaises(AssertionError):
            historical.verify_update(VERSIONS, info, historical_review=review,
                                     historical_save=BASELINE / 'test.sav')

    def test_historical162_rejects_an_unrelated_battery_save(self):
        info = json.loads((BASELINE / 'versions.json').read_bytes())
        review = json.loads((BASELINE / 'review.json').read_bytes())
        with tempfile.TemporaryDirectory(prefix='coastal-save-', dir='/tmp') as directory:
            save = Path(directory) / 'wrong.sav'
            save.write_bytes(bytes(131072))
            with self.assertRaises(AssertionError):
                historical.verify_update(VERSIONS, info, historical_review=review,
                                         historical_save=save)

    def test_archive_plan_preserves_each_layer162_proof_attachment(self):
        info = json.loads((BASELINE / 'versions.json').read_bytes())
        entries = archive_entries(info, VERSIONS, include_roms=False)
        reports = {name for name in entries if name.startswith('evidence/') and name.endswith('.json')}
        self.assertEqual(len(reports), 42 + 211)
        self.assertTrue({proof['file'] for proof in info['proofs']} <= reports)
        catalog = {path.relative_to(ROOT).as_posix()
                   for path in (ROOT / 'assets/tiles').rglob('*') if path.is_file()}
        self.assertGreaterEqual(len(catalog), 608)
        self.assertTrue(catalog <= entries.keys())
        self.assertIn('docs/AJUSTES-GBA.txt', entries)
        self.assertFalse(set(LEGACY_MEDIA) & entries.keys())
        for proof in info['proofs']:
            self.assertIn(proof['file'], entries)
            report = json.loads(entries[proof['file']].read_bytes())
            rows = list(report.get('captures', [])) + list(report.get('source_review_images', []))
            if 'video_sha256' in report:
                rows.append(dict(file=report['video'], sha256=report['video_sha256']))
            for row in rows:
                name = (Path(proof['file']).parent / row['file']).as_posix()
                self.assertIn(name, entries)
                self.assertEqual(hashlib.sha256(entries[name].read_bytes()).hexdigest(), row['sha256'])

    def test_components_keep_reports_and_capture_paths_unchanged(self):
        with tempfile.TemporaryDirectory(prefix='coastal-components-', dir='/tmp') as directory:
            root = Path(directory)
            original = root / 'original'
            (original / 'ports').mkdir(parents=True)
            capture = original / 'ports/avatar.png'
            capture.write_bytes(b'original native capture bytes')
            child = original / 'ports/integrated-piers.json'
            child.write_text(json.dumps(dict(captures=[dict(file='avatar.png', sha256=hashlib.sha256(capture.read_bytes()).hexdigest())])))
            parent = original / 'affected-coast-connections.json'
            parent.write_text(json.dumps(dict(components=[dict(kind='integrated-piers', file='ports/integrated-piers.json',
                                                               sha256=hashlib.sha256(child.read_bytes()).hexdigest())])))
            output = root / 'published/affected-coast-connections.json'
            digest = copy_current_proof(parent, output)
            self.assertEqual(digest, hashlib.sha256(parent.read_bytes()).hexdigest())
            self.assertEqual(output.read_bytes(), parent.read_bytes())
            self.assertEqual((output.parent / 'ports/integrated-piers.json').read_bytes(), child.read_bytes())
            self.assertEqual((output.parent / 'ports/avatar.png').read_bytes(), capture.read_bytes())

    def test_corrupted_component_capture_prevents_any_copy(self):
        with tempfile.TemporaryDirectory(prefix='coastal-corrupt-', dir='/tmp') as directory:
            root = Path(directory)
            capture = root / 'avatar.png'
            capture.write_bytes(b'changed capture')
            child = root / 'child.json'
            child.write_text(json.dumps(dict(captures=[dict(file='avatar.png', sha256='0' * 64)])))
            parent = root / 'parent.json'
            parent.write_text(json.dumps(dict(components=[dict(file='child.json', sha256=hashlib.sha256(child.read_bytes()).hexdigest())])))
            destination = root / 'output/report.json'
            with self.assertRaisesRegex(AssertionError, 'attachment hash mismatch'):
                copy_current_proof(parent, destination)
            self.assertFalse(destination.parent.exists())

    def test_component_outside_its_report_directory_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='coastal-traversal-', dir='/tmp') as directory:
            parent = Path(directory) / 'report.json'
            parent.write_text(json.dumps(dict(components=[dict(file='../other.json', sha256='0' * 64)])))
            with self.assertRaises(AssertionError):
                report_dependencies(parent)

    def test_component_report_with_wrong_hash_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='coastal-wrong-sha-', dir='/tmp') as directory:
            root = Path(directory)
            (root / 'child.json').write_text('{}\n')
            parent = root / 'report.json'
            parent.write_text(json.dumps(dict(components=[dict(file='child.json', sha256='0' * 64)])))
            with self.assertRaisesRegex(AssertionError, 'component hash mismatch'):
                report_dependencies(parent)

    def test_component_cycle_is_rejected_before_any_copy(self):
        # A symlink reaches the same active report without a path traversal.
        with tempfile.TemporaryDirectory(prefix='coastal-cycle-', dir='/tmp') as directory:
            root = Path(directory)
            parent = root / 'report.json'
            (root / 'cycle.json').symlink_to(parent)
            parent.write_text(json.dumps(dict(components=[dict(file='cycle.json', sha256='0' * 64)])))
            with self.assertRaisesRegex(AssertionError, 'Cyclic proof component'):
                copy_current_proof(parent, root / 'output/report.json')
            self.assertFalse((root / 'output').exists())

    def test_duplicate_capture_paths_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix='coastal-duplicate-', dir='/tmp') as directory:
            root = Path(directory)
            capture = root / 'native.png'
            capture.write_bytes(b'native pixels')
            row = dict(file='native.png', sha256=hashlib.sha256(capture.read_bytes()).hexdigest())
            parent = root / 'report.json'
            parent.write_text(json.dumps(dict(captures=[row, row])))
            with self.assertRaisesRegex(AssertionError, 'Duplicate attachment path'):
                report_dependencies(parent)

    def test_shore_native_output_directory_is_supported_without_ambiguous_aliases(self):
        with tempfile.TemporaryDirectory(prefix='coastal-layout-', dir='/tmp') as directory:
            root = Path(directory)
            report = root / 'TESTE/shore/shore-animation.json'
            report.parent.mkdir(parents=True)
            report.write_text('{}\n')
            self.assertEqual(edition_report(root, 'TESTE', 'shore-animation'), report)
            (root / 'TESTE/shore-animation.json').write_bytes(report.read_bytes())
            with self.assertRaisesRegex(AssertionError, 'ambiguous current proof'):
                edition_report(root, 'TESTE', 'shore-animation')


if __name__ == '__main__':
    unittest.main()
