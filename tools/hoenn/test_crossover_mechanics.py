"""Check the PWT and battle evidence recorded on the eight-encounter ROMs."""
import gzip
import hashlib
import json
from io import BytesIO
from pathlib import Path
import unittest

from PIL import Image

from verify_battle_interactions import verify_report
from verify_versions import VARIANTS

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / 'docs/design/revisao-integral-2026-11-26'
ROM_MANIFEST = ROOT / 'mods/hoenn/crossover-badges/validation.json'
PWT_BASE = ROOT / 'mods/hoenn/pwt-complete-rosters'
REJECTIONS = {
    'five_selected', 'same_slot_twice', 'missing_slot', 'only_five_owned',
    'unavailable_generation', 'egg', 'duplicate_held_item', 'same_species_twice',
    'frontier_banned_species', 'already_active',
}


class CrossoverMechanics(unittest.TestCase):
    def test_five_native_profiles(self):
        release = json.loads(ROM_MANIFEST.read_bytes())
        previous = json.loads((PWT_BASE / 'validation.json').read_bytes())
        editions = set(VARIANTS) | {'Pokemon-Journey-TESTE.gba'}
        self.assertEqual(set(release['editions']), editions)
        for name in sorted(editions):
            with self.subTest(edition=name):
                stem = Path(name).stem
                national, hard = VARIANTS.get(name, (1025, False))
                cap = 4 if national == 493 else 9
                sha = release['editions'][name]['rom_sha256']
                report = json.loads(gzip.decompress((REPORTS / (stem + '-mecanicas.json.gz')).read_bytes()))
                self.assertEqual(report['elf_sha256'], release['elf_sha256'])
                self.assertEqual(report['marker_sha256'], release['source_marker_sha256'])
                verify_report(report['battle'], sha, national, hard)

                registration = report['registration']
                self.assertEqual((registration['rom_sha256'], registration['version_generation_cap']), (sha, cap))
                self.assertTrue(registration['passed'] and registration['invalid_registration_native'])
                self.assertTrue(registration['reward_stage_is_explicit_fixture'])
                checks = {row['case']: row for row in registration['checks']}
                self.assertEqual(len(checks), len(registration['checks']))
                self.assertEqual(set(checks), REJECTIONS | {'global_reward', 'generation_reward'})
                for case in REJECTIONS:
                    self.assertTrue(checks[case]['rejected'] and checks[case]['party_unchanged'], case)
                for case, reward in [('global_reward', 25), ('generation_reward', 10)]:
                    self.assertEqual(checks[case]['bp'], reward)
                    self.assertTrue(checks[case]['once_only'] and checks[case]['party_restored_byte_exact'])

                # Compare eligibility and both observed transformations to the reviewed roster layer.
                archive = (PWT_BASE / (stem + '-evidence.json.gz')).read_bytes()
                self.assertEqual(hashlib.sha256(archive).hexdigest(), previous['editions'][name]['evidence_sha256'])
                prior_mega = json.loads(gzip.decompress(archive))['mega']
                mega = report['mega']
                self.assertEqual(mega['rom_sha256'], sha)
                self.assertEqual(mega, {**prior_mega, 'rom_sha256': sha})
                capture = (REPORTS / (stem + '-raichu.png')).read_bytes()
                self.assertEqual(hashlib.sha256(capture).hexdigest(), report['screenshot_sha256'])
                with Image.open(BytesIO(capture)) as picture:
                    self.assertEqual((picture.format, picture.size), ('PNG', (240, 160)))
                    picture.verify()
