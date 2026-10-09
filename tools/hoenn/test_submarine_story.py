"""Evidence from native Maxie/Stern/theft/hideout traversal on the current ROM."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / 'mods/hoenn'

class SubmarineStory(unittest.TestCase):
    def report(self):
        report = json.loads((REPORTS / 'submarine-story-validation/submarine-story.json').read_text())
        candidate = json.loads((REPORTS / 'aqua-episodes-validation/reproduction.json').read_text())
        self.assertTrue(report['passed'])
        self.assertEqual(report['rom_sha256'], candidate['rom_sha256'])
        return report

    def test_native_awakening_interview_theft_and_matt_complete_in_sequence(self):
        r = self.report()
        for key in ['native_maxie_victory_schedules_interview', 'native_stern_interview_enters_harbor',
                    'native_theft_opens_hideout', 'native_matt_victory_and_submarine_departure']:
            self.assertTrue(r[key], key)
        self.assertEqual(r['wins'][0]['trainer'], 601)
        self.assertEqual(r['wins'][4]['trainer'], 30)
        self.assertEqual(r['wins'][5]['trainer'], 2) # Original grunt on the way out.

    def test_directional_walk_uses_all_three_floors_and_original_teleports(self):
        r = self.report()
        self.assertTrue(r['native_surf_entrance'])
        self.assertTrue(r['no_hideout_position_or_event_entry_injections'])
        self.assertGreater(r['hideout_walked_steps'], 100)
        transitions = r['original_hideout_transitions']
        maps = {end[0] for t in transitions for end in (t['source'], t['destination'])}
        self.assertEqual(maps, {'AquaHideout_1F', 'AquaHideout_B1F', 'AquaHideout_B2F'})
        self.assertGreaterEqual(len(transitions), 8)
        self.assertTrue(any(t['source'][0] == t['destination'][0] for t in transitions))
        for i in range(1, len(transitions) + 1):
            self.assertTrue((REPORTS / f'submarine-story-validation/hideout-transition-{i}.png').is_file())

    def test_native_single_and_two_trainer_double_victories(self):
        r = self.report()
        trainers = set()
        doubles = []
        for win in r['wins']:
            trainers.add(win['trainer'])
            self.assertEqual(win['outcome'], 1)
            self.assertGreater(win['attacks'], 0)
            self.assertTrue(win['native_defeated_flag'])
            if win['second_trainer'] is not None:
                self.assertTrue(win['double_battle'])
                self.assertTrue(win['second_native_defeated_flag'])
                trainers.add(win['second_trainer'])
                doubles.append(win)
        self.assertEqual(trainers, {601, 27, 3, 192, 28, 193, 30, 2})
        self.assertEqual(len(doubles), 2)

    def test_native_continue_preserves_progress_and_documents_fixture_limits(self):
        r = self.report()
        self.assertTrue(r['native_save_continue_after_maxie_theft_and_matt'])
        self.assertTrue(r['regional_badges_and_kanto_missions_unchanged'])
        self.assertTrue(r['prior_episodes_badges_intercity_travel_initial_surf_and_battle_stats_are_fixtures'])
        self.assertTrue(r['healing_between_battles_is_fixture'])
        self.assertFalse(r['full_campaign_playthrough'])
        self.assertFalse(r['balance_validated'])

    def test_original_exit_teleport_and_stairs_lead_back_to_surf(self):
        r = self.report()
        self.assertGreater(r['return_walked_steps'], 40)
        self.assertEqual(r['original_return_transitions'], [
            {'source': ['AquaHideout_B2F', 32, 21], 'destination': ['AquaHideout_B1F', 31, 4]},
            {'source': ['AquaHideout_B1F', 29, 2], 'destination': ['AquaHideout_1F', 22, 2]},
        ])
        self.assertEqual(r['native_surf_prompts_on_return'], [['AquaHideout_1F', 13, 12]])
        self.assertTrue(r['no_hideout_position_or_event_entry_injections'])

    def test_native_lilycove_exit_and_continue_preserve_surf_and_regional_progress(self):
        r = self.report()
        self.assertTrue(r['native_return_to_lilycove'])
        self.assertTrue(r['native_continue_in_surf_after_return'])
        self.assertTrue(r['regional_badges_and_kanto_missions_unchanged'])
        for name in ['native-surf-prompt-return', 'native-return-to-lilycove-after-matt',
                     'native-lilycove-return-after-continue', 'hideout-transition-9', 'hideout-transition-10']:
            self.assertTrue((REPORTS / f'submarine-story-validation/{name}.png').is_file())

if __name__ == '__main__':
    unittest.main()
