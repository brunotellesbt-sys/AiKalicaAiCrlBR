"""Contracts for the sixteen badge League correction and unchanged gym gates."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'mods/hoenn/sixteen-badge-league-validation'
def read(name): return json.loads((DIR / name).read_text())

class SixteenBadgeLeagues(unittest.TestCase):
    def native(self, name):
        report = read(name)
        self.assertTrue(report['passed'])
        self.assertEqual(report['rom_sha256'], read('preparation/reproduction.json')['rom_sha256'])
        return report

    def test_replay_is_deterministic_and_follows_merged_mission_candidate(self):
        r = read('preparation/reproduction.json')
        for key in ('passed', 'idempotent', 'deterministic_replay'): self.assertTrue(r[key])
        self.assertEqual(r['files'], 3)
        prior = json.loads((ROOT / 'mods/hoenn/mandatory-native-validation/preparation/reproduction.json').read_text())
        self.assertEqual(r['baseline_rom_sha256'], prior['rom_sha256'])

    def test_native_permissions_require_both_complete_badge_banks(self):
        r = self.native('native/sixteen-badge-leagues.json')
        self.assertEqual(r['required_badges'], dict(kanto=8, hoenn=8))
        self.assertEqual(r['permission_cases'], 2048)
        self.assertTrue(r['badges_are_only_league_permission'])
        self.assertTrue(r['gym_story_requirement_is_preserved'])

    def test_physical_guards_save_load_and_old_elite_flag(self):
        r = self.native('native/sixteen-badge-leagues.json')
        self.assertEqual(len(r['physical_cases']), 8)
        for region in ('Kanto', 'Hoenn'):
            cases = [c for c in r['physical_cases'] if c['region'] == region]
            self.assertEqual({(c['own_badges'], c['other_badges'], c['old_elite_entry_flag']) for c in cases},
                {(8, 0, False), (8, 7, False), (8, 7, True), (7, 8, True)})
            for c in cases:
                for key in ('physical_denial', 'native_save_roundtrip', 'physical_entry_after_sixteen'): self.assertTrue(c[key])

    def test_prior_regional_only_permission_bug_reproduced(self):
        r = read('baseline/baseline.json')
        self.assertTrue(r['expected_old_rule_reproduced'])
        self.assertEqual(r['rom_sha256'], read('preparation/reproduction.json')['baseline_rom_sha256'])
        self.assertEqual([(c['kanto'], c['hoenn'], c['allowed']) for c in r['cases']],
            [(8, 0, [1, 0]), (0, 8, [0, 1]), (8, 7, [1, 0]), (7, 8, [0, 1])])

    def test_all_regional_mission_checkpoints_match_prior_native_matrix(self):
        r = self.native('matrix/campaign-matrix.json')
        prior = json.loads((ROOT / 'mods/hoenn/mandatory-native-validation/matrix/campaign-matrix.json').read_text())
        self.assertEqual(r['checks'], prior['checks'])
        self.assertEqual(r['gate_cases'], 11008); self.assertEqual(r['permission_cases'], 44)
        self.assertEqual(r['native_story_quests_required'], 7)
        self.assertTrue(r['other_region_badges_cannot_bypass_gate'])
        self.assertTrue(r['giovanni_and_space_center_required'])

    def test_campaign_code_levels_and_story_scripts_preserved(self):
        r = read('preparation/preparation.json')
        self.assertTrue(r['campaign_logic_outside_league_permissions_preserved'])
        self.assertTrue(r['regional_champions_remain_separate'])
        self.assertEqual(len(r['preserved_native_sha256']), 8)
        prior = json.loads((ROOT / 'mods/hoenn/mandatory-native-validation/preparation/preparation.json').read_text())
        for path in ('src/journey_gym_scaling.c', 'src/journey_wild.c', 'src/journey_family.c'):
            self.assertEqual(r['preserved_native_sha256'][path], prior['preserved_native_sha256'][path])

    def test_league_dialogue_is_english_and_never_dispatches_gym_guide(self):
        r = self.native('english-audit.json')
        self.assertEqual(r['sixteen_badge_league_lines'], 4)
        self.assertEqual(r['portuguese_marker_matches'], 0)
        self.assertLessEqual(r['maximum_normal_font_line_pixels'], r['normal_font_limit_pixels'])
        p = read('preparation/preparation.json')
        self.assertTrue(p['league_messages_are_not_gym_messages'])
        for e in p['edits']:
            if e['path'].endswith('scripts.inc'):
                self.assertNotIn('Journey_GymGuide_Dispatch', e['after'])
        self.assertTrue(self.native('native/sixteen-badge-leagues.json')['gym_story_requirement_not_reused_as_league_dialogue'])

    def test_audit_distinguishes_local_checks_from_final_league_entrance(self):
        r = read('campaign-dependencies.json')
        self.assertEqual(r['rom_sha256'], read('preparation/reproduction.json')['rom_sha256'])
        self.assertTrue(r['policy']['both_leagues_require_sixteen_badges'])
        self.assertFalse(r['policy']['leagues_check_pending_story'])
        for c in r['league_guards'].values(): self.assertEqual(c['final_entrance_required_badges'], dict(kanto=8, hoenn=8))
        self.assertTrue(r['policy']['independent_regional_mission_tracking'])
        self.assertFalse(r['full_campaign_runtime_validated'])
        self.assertFalse(self.native('native/sixteen-badge-leagues.json')['full_campaign_playthrough'])

if __name__ == '__main__': unittest.main()
