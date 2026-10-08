"""Regression evidence for the selected family's Hoenn champion rewards."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / 'mods/hoenn/family-postgame-validation'

def report(path):
    return json.loads((VALIDATION / path).read_text())

class FamilyPostgameRequirements(unittest.TestCase):
    def native(self, path, baseline=False):
        r = report(path)
        self.assertTrue(r['passed'])
        self.assertEqual(r['rom_sha256'], report('reproduction.json')['baseline_rom_sha256' if baseline else 'rom_sha256'])
        return r

    def test_strict_overlay_follows_display_fix(self):
        r = report('reproduction.json')
        self.assertEqual(r['baseline_rom_sha256'], json.loads((ROOT / 'mods/hoenn/postgame-validation/reproduction.json').read_text())['rom_sha256'])
        self.assertTrue(r['deterministic_replay'])
        self.assertTrue(r['idempotent'])
        self.assertEqual(r['files'], 6)
        p = report('preparation.json')
        self.assertTrue(p['save_layout_unchanged'])
        self.assertTrue(p['hoenn_championship_required'])

    def test_all_homes_require_own_hoenn_championship_in_either_region(self):
        r = self.native('native/family-postgame.json')
        cases = r['helper_cases']
        self.assertEqual(len(cases), 248)
        self.assertEqual({c['index'] for c in cases}, set(range(1, 32)))
        self.assertEqual({c['current_region'] for c in cases}, {'kanto', 'hoenn'})
        self.assertEqual({(c['kanto_clear'], c['hoenn_clear']) for c in cases}, {(False, False), (False, True), (True, False), (True, True)})
        for c in cases:
            self.assertEqual(c['pending'], 3 if c['hoenn_clear'] else 0)
        for key in ['invalid_homes_no_reward', 'full_key_pocket_retries_without_losing_reward',
                    'existing_ticket_repairs_receipt_without_duplicate']:
            self.assertTrue(r[key])

    def test_native_mothers_complete_both_news_choices_and_save(self):
        r = self.native('native/family-postgame.json')
        self.assertEqual(len(r['dialogues']), 6)
        self.assertEqual({c['index'] for c in r['dialogues']}, {1, 2, 17, 20, 31})
        self.assertEqual({c['gender'] for c in r['dialogues'] if c['index'] == 17}, {0, 1})
        self.assertEqual({c['color'] for c in r['dialogues']}, {0, 1})
        for c in r['dialogues']:
            self.assertEqual(c['ticket_quantity'], 1)
            for key in ['news_completed', 'repeat_no_duplicate', 'native_flash_save_reload']:
                self.assertTrue(c[key])
            self.assertTrue((VALIDATION / 'native' / f"family-{c['index']:02d}-{c['gender']}-news-choice.png").exists())
        self.assertTrue(r['championship_and_warps_are_fixtures'])
        self.assertFalse(r['full_campaign_playthrough'])

    def test_old_native_roamers_no_longer_bypass_sanctuaries(self):
        old = self.native('baseline/family-postgame-baseline.json', baseline=True)
        new = self.native('native/family-postgame.json')
        self.assertTrue(old['forced_active_latias'])
        self.assertGreater(old['native_roamer_encounters'], 0)
        self.assertEqual(old['native_roamer_attempts'], 100)
        self.assertEqual(new['native_roamer_attempts'], 100)
        self.assertEqual(new['native_roamer_encounters'], 0)
        self.assertEqual(new['completed_campaign_roamer_attempts'], 100)
        self.assertEqual(new['completed_campaign_roamer_encounters'], 0)
        self.assertTrue(new['all_sixteen_badges_set_for_final_roamer_check'])
        captures = json.loads((ROOT / 'mods/hoenn/integration-validation/sanctuaries-preparation.json').read_text())['captures']
        self.assertTrue({243, 244, 245, 380, 381}.issubset({c['national_dex'] for c in captures}))

    def test_story_gate_and_catalog_regressions(self):
        r = self.native('campaign-matrix.json')
        self.assertEqual(r['gate_cases'], 4096)
        self.assertEqual(r['permission_cases'], 36)
        self.assertTrue(r['giovanni_and_space_center_required'])
        r = self.native('catalog.json')
        self.assertEqual(r['base_species_count'], 1025)
        self.assertEqual(r['missing_assets'], [])

if __name__ == '__main__':
    unittest.main()
