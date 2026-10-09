"""Evidence that ordinary cave entrances no longer require winning a League."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'mods/hoenn/cave-access-validation'
def read(path): return json.loads((DIR / path).read_text())

class CaveAccess(unittest.TestCase):
    def native(self, path):
        r = read(path); self.assertTrue(r['passed'])
        self.assertEqual(r['rom_sha256'], read('reproduction.json')['rom_sha256'])
        return r

    def test_strict_overlay_preserves_rewards_encounters_and_regional_rules(self):
        p, r = read('preparation.json'), read('reproduction.json')
        self.assertEqual(set(p['prepared_sha256']), {
            'data/maps/Route103/scripts.inc', 'data/maps/Route114_FossilManiacsTunnel/scripts.inc'})
        self.assertEqual(r['files'], 2)
        for key in ['passed', 'deterministic_replay', 'idempotent']: self.assertTrue(r[key])
        for key in ['altering_cave_open_before_league', 'desert_underpass_open_before_league',
                    'fossil_rewards_and_landmark_script_preserved', 'map_layouts_and_warps_unchanged',
                    'gym_missions_scaling_and_special_capture_gate_preserved', 'cave_in_dialogue_updated']:
            self.assertTrue(p[key])
        self.assertFalse(p['new_flags_allocated'])
        for path in ['data/maps/DesertUnderpass/scripts.inc', 'src/journey_special.c',
                     'src/journey_wild.c', 'include/journey_habitat_data.h', 'src/field_player_avatar.c']:
            self.assertIn(path, p['preserved_native_sha256'])

    def test_baseline_reproduces_both_closed_doors_without_league_flags(self):
        r = read('baseline/cave-access.json')
        self.assertTrue(r['passed']); self.assertFalse(r['candidate'])
        self.assertEqual(r['rom_sha256'], read('reproduction.json')['baseline_rom_sha256'])
        self.assertEqual({row['cave'] for row in r['rows']}, {'AlteringCave', 'DesertUnderpass'})
        for row in r['rows']: self.assertTrue(row['native_closed_door_reproduced'])

    def test_native_entry_return_reentry_and_four_continues(self):
        r = self.native('native/cave-access.json'); self.assertTrue(r['candidate'])
        for row in r['rows']: self.assertTrue(row['native_entry_exit_and_reentry'])
        self.assertEqual([t['destination'][0] for t in r['transitions']], [
            'AlteringCave', 'Route103', 'AlteringCave', 'Route103', 'DesertUnderpass',
            'Route114_FossilManiacsTunnel', 'DesertUnderpass', 'Route114_FossilManiacsTunnel'])
        self.assertEqual(len(r['save_continue']), 4)
        for saved in r['save_continue']:
            self.assertEqual(saved['before'], saved['after'])
            self.assertEqual(saved['after']['kanto_badges'], 0)
            self.assertEqual(saved['after']['hoenn_badges'], 0)
            self.assertFalse(saved['after']['kanto_champion'])
            self.assertFalse(saved['after']['hoenn_champion'])
            self.assertFalse(saved['after']['special_capture_unlocked'])
        self.assertEqual([s['after']['underpass_discovered'] for s in r['save_continue']], [False, False, True, True])
        self.assertTrue(r['native_underpass_landmark'])
        self.assertTrue(r['no_internal_warps_during_each_cave_route'])
        self.assertTrue(r['initial_badges_story_party_and_two_approach_positions_are_fixtures'])
        self.assertFalse(r['full_campaign_playthrough']); self.assertFalse(r['balance_validated'])

    def test_aquatic_access_and_six_continues_still_pass_on_new_candidate(self):
        r = self.native('sootopolis/sootopolis-access.json')
        self.assertTrue(r['native_dive_and_resurface'])
        self.assertEqual(len(r['save_continue']), 6)
        for saved in r['save_continue']: self.assertEqual(saved['before'], saved['after'])

    def test_all_badge_subsets_and_archie_permissions_keep_regional_missions(self):
        r = self.native('missions/campaign-matrix.json')
        self.assertEqual((r['gate_cases'], r['permission_cases']), (5120, 44))
        for key in ['all_regional_badge_subsets', 'native_aqua_episodes_required',
                    'other_region_badges_cannot_bypass_gate', 'giovanni_and_space_center_required']:
            self.assertTrue(r[key])

if __name__ == '__main__': unittest.main()
