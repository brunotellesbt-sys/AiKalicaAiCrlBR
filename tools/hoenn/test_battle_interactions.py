"""Require reproducible mechanics coverage bound to the exact tested ROM edition; historical evidence is labeled explicitly."""
import hashlib
import json
import unittest
from pathlib import Path
from verify_battle_interactions import verify_report
from published_evidence import evidence_release,evidence_rom

ROOT=Path(__file__).resolve().parents[2]
REPORTS=ROOT/'mods/hoenn/battle-interactions-validation'

class NativeBattleInteractions(unittest.TestCase):
    def test_all_four_editions_have_matching_native_mechanics_results(self):
        directory,manifest=evidence_release('battle-interactions')
        baseline=None
        for row in manifest['variants']:
            with self.subTest(edition=row['file']):
                sha=hashlib.sha256(evidence_rom(directory,row['file'])).hexdigest()
                self.assertEqual(sha,row['sha256'])
                edition=row['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba')
                report=json.loads((REPORTS/edition/'battle-interactions.json').read_text())
                verify_report(report,sha,row['max_national'],row['perfect_trainer_ivs'])
                if baseline is None:baseline=report['checks']
                else:self.assertEqual(report['checks'],baseline)

    def test_status_item_and_pp_corner_cases_have_observed_results(self):
        report=json.loads((REPORTS/'Gen1-9-Hard/battle-interactions.json').read_text())
        rows={(r['group'],r['case']):r for r in report['checks']}
        for key,expected in {
            ('ability_resolution','mold-ABILITY_SHIELD'):26,
            ('ability_resolution','mold-NONE-ground-immunity'):4096,
            ('leppa','EARTH_POWER-RIPEN-False-pp'):10,
            ('leppa','TACKLE-RIPEN-False-pp'):20,
            ('leppa','TACKLE-NONE-True-pp'):0,
            ('berry_heal','SITRUS_BERRY-scheduled-heal-RIPEN-50-False'):-50,
            ('mental_herb','disableTimer-cleared'):0,
            ('survival','STURDY-NONE-100'):99,
            ('survival','STURDY-NONE-99'):1000,
            ('type_chart','DRAGON-FAIRY'):0,
            ('type_chart','FAIRY-DRAGON'):8192,
            ('ai_hazards','SPIKES-HEAVY_DUTY_BOOTS-NONE-plain'):0,
            ('ai_hazards','TOXIC_SPIKES-HEAVY_DUTY_BOOTS-NONE-plain'):0,
            ('ai_hazards','SPIKES-HEAVY_DUTY_BOOTS-NONE-magic-room'):12,
            ('ai_hazards','SPIKES-HEAVY_DUTY_BOOTS-KLUTZ-plain'):12,
            ('turn_order','True-TACKLE-TACKLE-NONE-NONE'):1,
            ('turn_order','True-TACKLE-QUICK_ATTACK-NONE-NONE'):0xffffffff,
        }.items():
            with self.subTest(case=key):self.assertEqual(rows[key]['actual'],expected)

    def test_boots_regression_was_reproduced_on_the_previous_rom(self):
        before=json.loads((REPORTS/'regression-before-fix/boots-spikes.json').read_text())
        self.assertFalse(before['passed'])
        self.assertEqual(before['actual'],12)
        self.assertEqual(before['expected'],0)
        directory,manifest=evidence_release('battle-interactions')
        self.assertNotEqual(before['rom_sha256'],manifest['parent_rom_sha256'])

    def test_release_seal_includes_the_new_evidence(self):
        directory,manifest=evidence_release('battle-interactions')
        self.assertTrue(manifest['battle_interactions_validated'])
        proofs=[p for p in manifest['proofs'] if p['kind']=='battle-interactions']
        self.assertEqual(len(proofs),5)
        for proof in proofs:
            self.assertEqual(hashlib.sha256((directory/proof['file']).read_bytes()).hexdigest(),proof['sha256'])

if __name__=='__main__':unittest.main()
