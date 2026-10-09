"""Native Shelly/Matt completion and regional free-order gym requirements."""
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'mods/hoenn/aqua-episodes-validation'
def read(path): return json.loads((DIR / path).read_text())

class MandatoryAquaEpisodes(unittest.TestCase):
    def native(self, path):
        r = read(path); self.assertTrue(r['passed'])
        self.assertEqual(r['rom_sha256'], read('reproduction.json')['rom_sha256'])
        return r

    def test_strict_overlay_retains_native_quests_roads_and_level_scaling(self):
        r = read('reproduction.json'); p = read('preparation.json')
        for key in ['passed', 'deterministic_replay', 'idempotent']: self.assertTrue(r[key])
        self.assertEqual(r['files'], 2)
        self.assertEqual(r['baseline_rom_sha256'], json.loads((ROOT / 'mods/hoenn/story-puzzles-validation/reproduction.json').read_text())['rom_sha256'])
        self.assertEqual(set(p['prepared_sha256']), {'src/journey_campaign_gates.c', 'data/scripts/journey_campaign_gates.inc'})
        self.assertEqual([(e['boss'], e['badges'], e['event']) for e in p['events']], [('Shelly', 4, 15), ('Matt', 6, 16)])
        for key in ['only_unwon_gyms_blocked', 'guide_explains_team_and_location', 'roads_unchanged', 'native_castform_gift_retained', 'native_submarine_theft_escape_retained', 'archie_and_space_center_require_both_episodes', 'independent_kanto_badges_and_league_retained', 'save_layout_unchanged']:
            self.assertTrue(p[key], key)
        self.assertIn('src/journey_gym_scaling.c', p['preserved_native_sha256'])
        self.assertFalse(p['new_flags_allocated']); self.assertFalse(p['full_campaign_validated'])

    def test_old_candidate_allowed_skipping_both_episodes(self):
        r = read('baseline/aqua-episodes-baseline.json')
        self.assertTrue(r['passed']); self.assertTrue(r['shelly_and_matt_can_be_skipped'])
        self.assertTrue(r['archie_permission_without_either_episode'])
        self.assertEqual(r['rom_sha256'], read('reproduction.json')['baseline_rom_sha256'])
        self.assertTrue(all(not d['blocked'] and d['physical_door'] for d in r['native_gym_doors']))

    def test_real_npc_battles_preserve_castform_submarine_and_native_save(self):
        r = self.native('native/aqua-episodes.json')
        self.assertEqual([w['trainer'] for w in r['wins']], [32, 30])
        for win in r['wins']:
            self.assertEqual(win['outcome'], 1); self.assertGreater(win['attacks'], 0)
            self.assertTrue(win['native_defeated_flag'])
        self.assertEqual([d['blocked'] for d in r['doors']], [True, False, True, False])
        self.assertTrue(all(d['physical_door'] for d in r['doors']))
        for key in ['native_npc_interactions', 'shelly_at_four_badges', 'matt_at_six_badges', 'original_castform_received', 'original_submarine_departed', 'wins_do_not_award_badges', 'kanto_missions_and_badges_unchanged', 'native_save_reload_continue', 'magma_space_center_and_silph_still_required']:
            self.assertTrue(r[key], key)
        self.assertTrue(r['travel_badges_earlier_missions_later_scenes_and_battle_stats_are_fixtures'])
        self.assertFalse(r['balance_validated']); self.assertFalse(r['full_campaign_playthrough'])

    def test_every_badge_subset_requires_native_victory_and_scene_completion(self):
        r = self.native('matrix/campaign-matrix.json')
        self.assertEqual((r['gate_cases'], r['permission_cases']), (5120, 44))
        self.assertTrue(r['all_regional_badge_subsets']); self.assertTrue(r['native_aqua_episodes_required'])
        self.assertTrue(r['other_region_badges_cannot_bypass_gate']); self.assertTrue(r['giovanni_and_space_center_required'])
        expected = {'shelly_battle': (4, 15), 'institute_completion': (4, 15), 'matt_battle': (6, 16), 'submarine_escape': (6, 16)}
        for key, values in expected.items():
            check = next(c for c in r['checks'] if c['scenario'] == key)
            self.assertEqual((check['threshold'], check['pending_event']), values)
            self.assertEqual(check['badge_subsets'], 256)
        self.assertTrue(r['flags_are_initial_state_fixtures']); self.assertFalse(r['full_campaign_playthrough'])

if __name__ == '__main__': unittest.main()
