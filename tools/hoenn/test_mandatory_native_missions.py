"""Mandatory story regression evidence on the compiled regional candidate."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'mods/hoenn/mandatory-native-validation'
def read(path): return json.loads((DIR / path).read_text())

class MandatoryNativeMissions(unittest.TestCase):
    def setUp(self):
        self.replay = read('preparation/reproduction.json')
        self.prep = read('preparation/preparation.json')

    def native(self, path):
        r = read(path)
        self.assertTrue(r['passed'])
        self.assertEqual(r['rom_sha256'], self.replay['rom_sha256'])
        return r

    def test_overlay_replays_after_early_tools_and_checks_seven_files(self):
        self.assertTrue(self.replay['passed']); self.assertTrue(self.replay['deterministic_replay']); self.assertTrue(self.replay['idempotent'])
        self.assertEqual(self.replay['files'], 7)
        previous = json.loads((ROOT / 'mods/hoenn/early-story-tools-validation/preparation/reproduction.json').read_text())
        self.assertEqual(self.replay['baseline_rom_sha256'], previous['rom_sha256'])

    def test_all_seven_original_episodes_have_regional_checkpoints(self):
        expected = {'mt_moon': (True, 1), 'cerulean_rocket': (True, 2), 'fuji_rescue': (True, 4),
            'petalburg_woods': (False, 1), 'rusturf_recovery': (False, 1),
            'steven_letter': (False, 2), 'oceanic_museum': (False, 2)}
        self.assertEqual({q['key']: (q['kanto'], q['badges']) for q in self.prep['quests']}, expected)
        self.assertTrue(self.prep['existing_boss_thresholds_preserved']); self.assertTrue(self.prep['roads_not_closed'])
        audit = read('campaign-dependencies.json')
        self.assertEqual(audit['rom_sha256'], self.replay['rom_sha256'])
        self.assertEqual(audit['policy']['required_original_episodes'], self.prep['quests'])
        self.assertTrue(audit['policy']['leagues_check_pending_story'])

    def test_every_required_battle_flag_and_scene_is_checked_for_all_badge_subsets(self):
        r = self.native('matrix/campaign-matrix.json')
        self.assertEqual(r['gate_cases'], 11008); self.assertEqual(r['permission_cases'], 44)
        self.assertEqual(r['native_story_quests_required'], 7)
        for q in self.prep['quests']:
            names = q['trainers'] + q['flags'] + [v for v, _ in q['variables']]
            for name in names:
                row = next(c for c in r['checks'] if c['scenario'] == q['key'] + ':' + name)
                self.assertEqual(row['badge_subsets'], 256); self.assertEqual(row['pending_event'], q['event'])
                self.assertEqual(row['threshold'], q['badges'])
        self.assertTrue(r['other_region_badges_cannot_bypass_gate']); self.assertTrue(r['giovanni_and_space_center_required'])

    def test_actual_gym_doors_block_and_reopen_for_each_mission(self):
        r = self.native('native/mandatory-missions.json')
        self.assertEqual(len(r['gym_doors']), 7)
        self.assertTrue(all(c['physical_block'] and c['opens_after_completion'] for c in r['gym_doors']))

    def test_league_guards_require_missions_even_with_sixteen_badges_and_old_entry_flag(self):
        r = self.native('native/mandatory-missions.json')
        self.assertEqual(len(r['league_guards']), 7); self.assertEqual(r['league_badge_subset_cases'], 512)
        for c in r['league_guards']:
            self.assertEqual((c['own_badges'], c['other_badges']), (8, 8))
            for key in ['physical_guard', 'old_elite_entry_flag_cannot_bypass', 'native_save_roundtrip', 'opens_after_completion']:
                self.assertTrue(c[key])

    def test_devon_theft_can_start_with_any_first_badge_and_late_roxanne_keeps_completion(self):
        r = self.native('native/mandatory-missions.json')
        self.assertEqual({c['first_badge'] for c in r['devon_first_badge_cases']}, set(range(1, 9)))
        self.assertTrue(all(c['theft_started'] and c['no_synthetic_recovery'] and c['late_revisit_keeps_state'] for c in r['devon_first_badge_cases']))
        self.assertEqual(r['roxanne_postbattle_preserved_states'], [4, 7])

    def test_baseline_bypasses_are_reproduced_and_real_steven_interaction_requires_letter(self):
        old = read('baseline/baseline.json')
        self.assertEqual(old['rom_sha256'], self.replay['baseline_rom_sha256'])
        self.assertTrue(old['expected_bypass_reproduced']); self.assertTrue(old['physical_league_entry_allowed'])
        self.assertTrue(old['fuji_rescue_missing']); self.assertTrue(old['steven_accepts_missing_letter'])
        self.assertTrue(self.native('native/mandatory-missions.json')['actual_steven_interaction_requires_and_consumes_letter'])

    def test_early_tools_levels_and_original_story_battle_scripts_are_preserved(self):
        preserved = self.prep['preserved_native_sha256']
        for path in ['src/journey_gym_scaling.c', 'src/journey_wild.c', 'src/journey_family.c',
            'data/maps/PokemonTower_6F_Frlg/scripts.inc', 'data/maps/PokemonTower_7F_Frlg/scripts.inc',
            'data/maps/PetalburgWoods/scripts.inc', 'data/maps/RusturfTunnel/scripts.inc',
            'data/maps/SlateportCity_OceanicMuseum_2F/scripts.inc']:
            self.assertIn(path, preserved)
        prior = json.loads((ROOT / 'mods/hoenn/early-story-tools-validation/preparation/preparation.json').read_text())
        self.assertEqual(preserved['src/journey_family.c'], prior['prepared_sha256']['src/journey_family.c'])

    def test_english_and_limits_of_runtime_evidence_are_explicit(self):
        r = self.native('english-audit.json')
        self.assertEqual(r['portuguese_marker_matches'], 0); self.assertEqual(r['mandatory_mission_additional_lines'], 38)
        self.assertLessEqual(r['maximum_normal_font_line_pixels'], r['normal_font_limit_pixels'])
        r = self.native('native/mandatory-missions.json')
        self.assertTrue(r['completion_badges_travel_and_postbattle_entries_are_fixtures'])
        self.assertFalse(r['original_quest_battles_played']); self.assertFalse(r['full_campaign_playthrough'])

if __name__ == '__main__': unittest.main()
