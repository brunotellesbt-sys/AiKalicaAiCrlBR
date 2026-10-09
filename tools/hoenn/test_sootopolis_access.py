"""Native route evidence for both Sootopolis shores and its ocean return."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'mods/hoenn/sootopolis-validation'

class SootopolisAccess(unittest.TestCase):
    def report(self, path):
        r = json.loads((DIR / path).read_text())
        self.assertTrue(r['passed'])
        expected = json.loads((ROOT / 'mods/hoenn/water-continue-validation/reproduction.json').read_text())
        self.assertEqual(r['rom_sha256'], expected['rom_sha256'])
        return r

    def test_native_path_visits_both_shores_and_returns_to_route126(self):
        r = self.report('native/sootopolis-access.json')
        self.assertTrue(r['native_dive_and_resurface'])
        self.assertTrue(r['native_walking_and_surf'])
        self.assertTrue(r['no_internal_warps_after_initial_ocean_fixture'])
        self.assertTrue(r['no_trainer_battle_required'])
        self.assertGreater(r['position_changes'], 100)
        self.assertEqual([t['destination'][0] for t in r['transitions']], [
            'Underwater_SootopolisCity', 'SootopolisCity_House1', 'SootopolisCity',
            'SootopolisCity_PokemonCenter_1F', 'SootopolisCity', 'Underwater_Route126'])
        self.assertGreaterEqual(len(r['surf_prompts']), 2)

    def test_six_continues_keep_water_modes_badges_and_pending_story(self):
        r = self.report('native/sootopolis-access.json')
        saves = r['save_continue']
        self.assertEqual([s['before']['avatar_mode'] for s in saves], [16, 8, 1, 1, 16, 8])
        self.assertEqual([s['before']['map'] for s in saves], [
            'Underwater_SootopolisCity', 'SootopolisCity', 'SootopolisCity_House1',
            'SootopolisCity_PokemonCenter_1F', 'Underwater_Route126', 'Route126'])
        for saved in saves:
            self.assertEqual(saved['before'], saved['after'])
            self.assertEqual(saved['after']['kanto_badges'], 0)
            self.assertEqual(saved['after']['hoenn_badges'], 0)
            self.assertFalse(saved['after']['kyogre_escaped'])
        self.assertEqual(saves[-1]['after']['position'], [45, 66])

    def test_shared_walker_still_completes_seafloor_with_pending_boss(self):
        r = self.report('seafloor/seafloor-route.json')
        self.assertTrue(r['native_dive_out_and_return_to_route128'])
        self.assertTrue(r['native_boss_trigger_refuses_missing_missions'])
        self.assertTrue(r['no_internal_position_warps_or_event_entries'])
        self.assertTrue(r['return_surf_prompts'])
        for saved in r['water_save_continues']:
            self.assertEqual(saved['before'], saved['after'])
            self.assertFalse(saved['after']['archie_permission'])

    def test_reports_keep_fixtures_and_campaign_limits_explicit(self):
        r = self.report('native/sootopolis-access.json')
        self.assertTrue(r['initial_story_badges_origin_party_ocean_are_fixtures'])
        self.assertTrue(r['wild_encounters_disabled'])
        self.assertFalse(r['full_campaign_playthrough'])
        self.assertFalse(r['balance_validated'])
        for saved in r['save_continue']:
            self.assertTrue((DIR / 'native' / (saved['label'] + '-after-continue.png')).is_file())

if __name__ == '__main__': unittest.main()
