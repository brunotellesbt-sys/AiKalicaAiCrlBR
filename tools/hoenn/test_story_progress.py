"""Native added-mission wins and the explicit cross-region story connection."""
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / 'mods/hoenn/story-progress-validation'

def report(name): return json.loads((VALIDATION / name).read_text())

class ConnectedStoryProgress(unittest.TestCase):
    def native(self):
        r = report('team-missions.json')
        self.assertTrue(r['passed'])
        self.assertEqual(r['rom_sha256'], json.loads((ROOT / 'mods/hoenn/frontier-travel-validation/reproduction.json').read_text())['rom_sha256'])
        return r

    def test_stories_are_connected_with_separate_badges_and_leagues(self):
        r = report('campaign-dependencies.json')
        self.assertEqual(r['rom_sha256'], json.loads((ROOT / 'mods/hoenn/frontier-travel-validation/reproduction.json').read_text())['rom_sha256'])
        p = r['policy']
        self.assertTrue(p['connected_campaigns']); self.assertFalse(p['independent_campaigns'])
        for key in ['independent_leagues', 'independent_badge_counts', 'independent_regional_mission_tracking']:
            self.assertTrue(p[key])
        link = p['mandatory_cross_region_prerequisite']
        self.assertFalse(link['optional'])
        self.assertEqual((link['kanto_badges'], link['hoenn_badges']), (6, 7))
        self.assertIn('Silph', link['required'])
        self.assertEqual(len(r['bosses']), 6)
        self.assertEqual(len(r['regular_gym_replacements']), 1)
        self.assertIn('Blue', r['regular_gym_replacements'][0]['boss'])
        for league in r['league_guards'].values():
            self.assertEqual(league['required_badges'], list(range(1, 9)))
            self.assertFalse(league['other_region_badges_count'])
        self.assertFalse(r['full_campaign_runtime_validated'])

    def test_28_added_trainers_are_won_in_real_native_battles(self):
        r = self.native()
        self.assertEqual((r['native_victories'], r['kanto_victories'], r['hoenn_victories']), (28, 19, 9))
        self.assertEqual(len(r['wins']), 28)
        self.assertEqual({w['trainer'] for w in r['wins']}, set(range(1478, 1506)))
        for win in r['wins']:
            self.assertEqual(win['outcome'], 1)
            self.assertGreater(win['attacks'], 0)
            self.assertTrue(win['native_defeated_flag'])
            self.assertTrue(win['other_region_event_unchanged'])
        self.assertTrue(r['badges_unchanged']); self.assertTrue(r['independent_regional_mission_tracking'])
        self.assertTrue(r['hidden_and_battle_bond_retained'])
        self.assertTrue(any(w['ash_seen'] for w in r['wins']))
        self.assertTrue(r['initial_badges_prior_events_travel_script_entry_and_battle_stats_are_fixtures'])
        self.assertFalse(r['balance_validated']); self.assertFalse(r['full_campaign_playthrough'])

    def test_missions_advance_in_sequence_and_survive_native_continue(self):
        r = self.native()
        self.assertEqual([m['mission'] for m in r['missions']], ['pewter', 'vermilion', 'rock_tunnel', 'western_sea', 'kanto_incursions', 'hoenn_rocket'])
        self.assertEqual([m['wins'] for m in r['missions']], [3, 3, 4, 5, 4, 9])
        self.assertEqual([m['next_event'] for m in r['missions']], [8, 9, 10, 11, 0, 0])
        self.assertTrue(all(m['native_save_reload_continue'] for m in r['missions']))
        for visit in r['defeated_npc_revisits']:
            self.assertTrue(visit['dialogue_only']); self.assertTrue(visit['no_new_battle'])
        self.assertEqual({v['trainer'] for v in r['defeated_npc_revisits']}, {1480, 1505})

    def test_unwon_gym_doors_open_only_after_their_own_missions(self):
        r = self.native()
        self.assertEqual([(d['city'], d['blocked']) for d in r['doors']], [('CinnabarIsland_Frlg', True), ('FortreeCity', True), ('CinnabarIsland_Frlg', False), ('FortreeCity', True), ('FortreeCity', False)])
        self.assertTrue(all(d['physical_door'] for d in r['doors']))

    def test_real_silph_victory_unlocks_the_mandatory_hoenn_alliance(self):
        r = report('silph/silph-connection.json')
        self.assertEqual(r['rom_sha256'], self.native()['rom_sha256'])
        for key in ['passed', 'five_kanto_badges_denied_without_battle',
                    'physical_silph_coordinate_trigger', 'native_card_key_pickup',
                    'native_card_key_door_opened', 'silph_completion_from_native_scene',
                    'checked_in_kanto_and_hoenn', 'native_save_reload_continue',
                    'badges_unchanged', 'unwon_kanto_gym_opened']:
            self.assertTrue(r[key], key)
        win = r['native_giovanni_win']
        self.assertEqual((win['trainer'], win['outcome']), (1103, 1))
        self.assertGreater(win['attacks'], 0)
        self.assertTrue(win['native_defeated_flag'])
        self.assertEqual((r['hoenn_event_before'], r['hoenn_event_after']), (13, 6))
        self.assertFalse(r['alliance_before']); self.assertTrue(r['alliance_after'])
        self.assertTrue(r['earlier_missions_badges_space_center_travel_and_battle_stats_are_fixtures'])
        self.assertFalse(r['balance_validated']); self.assertFalse(r['full_campaign_playthrough'])

if __name__ == '__main__': unittest.main()
