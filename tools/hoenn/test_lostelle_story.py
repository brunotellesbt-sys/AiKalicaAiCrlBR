"""Native Sevii rescue, regional persistence, scaled Hypno and real rewards."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'mods/hoenn/lostelle-story-validation'

class LostelleStory(unittest.TestCase):
    def report(self):
        r = json.loads((DIR / 'lostelle-story.json').read_text())
        self.assertTrue(r['passed'])
        prior = json.loads((ROOT / 'mods/hoenn/lostelle-habitat-validation/preparation/reproduction.json').read_text())
        self.assertEqual(r['rom_sha256'], prior['rom_sha256'])
        return r

    def test_four_consecutive_bikers_and_route_trainers_win_natively(self):
        r = self.report(); trainers = [b for b in r['battles'] if b['kind'] == 'trainer']
        self.assertEqual([b['trainer'] for b in trainers[:4]], [1263, 1264, 1265, 1477])
        self.assertTrue(all(b['map'] == 'ThreeIsland_Frlg' for b in trainers[:4]))
        self.assertTrue(any(b['map'] == 'ThreeIsland_BondBridge_Frlg' for b in trainers[4:]))
        for b in trainers:
            self.assertEqual(b['outcome'], 1); self.assertTrue(b['native_defeated_flag'])
            self.assertGreater(b['attacks'], 0)

    def test_story_gives_and_consumes_meteorite_and_rewards_once(self):
        r = self.report(); initial, rescue, delivered, opened = [r[k] for k in ['initial', 'rescue', 'delivered', 'games_opened']]
        self.assertEqual(initial['meteorite'], 0); self.assertEqual(rescue['meteorite'], 1)
        self.assertEqual(delivered['meteorite'], 0)
        self.assertEqual(rescue['iapapa'], initial['iapapa'] + 1)
        self.assertTrue(delivered['moon_reward_received'])
        self.assertEqual(delivered['moon_stone'], initial['moon_stone'] + 1)
        self.assertEqual(opened['moon_stone'], delivered['moon_stone'])
        self.assertEqual(opened['two_scene'], 4); self.assertEqual(opened['one_scene'], 2)
        final = r['save_continue'][-1]['after']
        self.assertEqual(final['moon_stone'], opened['moon_stone']); self.assertEqual(final['meteorite'], 0)

    def test_hypno_scales_to_party_mean_and_native_escort_returns_child(self):
        r = self.report(); wild = [b for b in r['battles'] if b['kind'] == 'scripted_wild']
        self.assertEqual(len(wild), 1); b = wild[0]
        self.assertEqual(b['opponent_species'], 97); self.assertEqual(b['outcome'], 1)
        mean = r['wild_party_mean']
        self.assertGreaterEqual(b['opponent_level'], max(1, mean - 5))
        self.assertLessEqual(b['opponent_level'], min(100, mean + 2))
        self.assertEqual(b['map'], 'ThreeIsland_BerryForest_Frlg')
        self.assertEqual(r['rescue']['map'], 'TwoIsland_JoyfulGameCorner_Frlg')
        self.assertTrue(r['rescue']['rescued']); self.assertTrue(r['rescue']['forest_lostelle_hidden'])
        self.assertTrue(r['original_lostelle_escort_warp']); self.assertTrue(r['rescued_child_revisit_has_no_second_battle'])

    def test_eight_continues_keep_items_quests_and_regional_badges(self):
        saves = self.report()['save_continue']; self.assertEqual(len(saves), 8)
        for s in saves:
            self.assertEqual(s['before'], s['after'])
            self.assertEqual(s['after']['kanto_badges'], 0); self.assertEqual(s['after']['hoenn_badges'], 0)
            self.assertTrue((DIR / (s['label'] + '-after-continue.png')).is_file())
        self.assertEqual(saves[0]['after']['one_scene'], 1)
        self.assertEqual(saves[1]['after']['three_scene'], 2)
        self.assertEqual(saves[2]['after']['three_scene'], 4)
        self.assertTrue(saves[-1]['after']['rescued']); self.assertEqual(saves[-1]['after']['mode'], 8)

    def test_complete_journey_uses_ordinary_travel_and_returns_to_start(self):
        r = self.report()
        self.assertEqual(r['start'], r['end']); self.assertTrue(r['no_midroute_fixture_warps_or_direct_npc_scripts'])
        self.assertTrue({'ThreeIsland_BondBridge_Frlg', 'ThreeIsland_BerryForest_Frlg', 'TwoIsland_JoyfulGameCorner_Frlg'}.issubset(r['visited_maps']))
        self.assertEqual(r['position_changes'], sum(l['position_changes'] for l in r['legs']))
        self.assertTrue(all(l['position_changes'] > 0 for l in r['legs']))

    def test_fixture_and_campaign_limits_are_explicit(self):
        r = self.report()
        self.assertTrue(r['initial_party_position_and_prior_story_states_are_fixtures'])
        self.assertTrue(r['boosted_battle_stats_and_pp_are_fixtures'])
        self.assertTrue(r['random_wild_encounters_disabled'])
        self.assertFalse(r['full_campaign_playthrough']); self.assertFalse(r['balance_validated'])

if __name__ == '__main__': unittest.main()
