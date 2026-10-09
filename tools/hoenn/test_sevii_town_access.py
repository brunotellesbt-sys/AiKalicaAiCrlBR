"""Native island access, real nurse recovery and Continue evidence."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'mods/hoenn/sevii-town-validation'

class SeviiTownAccess(unittest.TestCase):
    def report(self):
        r = json.loads((DIR / 'sevii-town-access.json').read_text())
        self.assertTrue(r['passed'])
        prior = json.loads((ROOT / 'mods/hoenn/eastern-ocean-journey-validation/preparation/reproduction.json').read_text())
        self.assertEqual(r['rom_sha256'], prior['rom_sha256'])
        return r

    def test_seven_towns_centers_and_harbors_reached_through_native_travel(self):
        r = self.report()
        self.assertTrue(r['continuous_roundtrip']); self.assertEqual(r['start'], r['end'])
        self.assertTrue(r['no_midroute_warps_or_direct_npc_scripts'])
        visited = set(r['visited_maps'])
        for n in ['One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven']:
            for suffix in ['_Frlg', '_Harbor_Frlg', '_PokemonCenter_1F_Frlg']:
                self.assertIn(n + 'Island' + suffix, visited)
        self.assertIn('ThreeIsland_Port_Frlg', visited)
        self.assertEqual(r['position_changes'], sum(l['position_changes'] for l in r['legs']))
        self.assertTrue(all(l['position_changes'] > 0 for l in r['legs']))

    def test_every_nurse_restores_damaged_pokemon_by_interaction(self):
        healing = self.report()['healing']
        self.assertEqual(len(healing), 7)
        self.assertEqual({h['island'] for h in healing}, {'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven'})
        for h in healing:
            self.assertEqual(h['hp_before'], 1); self.assertEqual(h['hp_after'], h['max_hp'])
            self.assertGreater(h['hp_after'], 1)
            self.assertTrue(h['native_nurse_interaction']); self.assertTrue(h['initial_damage_is_fixture'])
            self.assertTrue((DIR / (h['island'].lower() + '-native-healing.png')).is_file())

    def test_fourteen_continues_preserve_foot_surf_and_regional_badges(self):
        saved = self.report()['save_continue']
        self.assertEqual(len(saved), 14)
        self.assertEqual(sum(s['after']['mode'] == 1 for s in saved), 7)
        self.assertEqual(sum(s['after']['mode'] == 8 for s in saved), 7)
        for s in saved:
            self.assertEqual(s['before'], s['after'])
            self.assertEqual(s['after']['kanto_badges'], 0); self.assertEqual(s['after']['hoenn_badges'], 0)
            self.assertFalse(s['after']['special_capture_unlocked'])
            self.assertTrue((DIR / (s['label'] + '-after-continue.png')).is_file())

    def test_tileset_pointer_change_keeps_western_journey_working(self):
        r = self.report()
        west = json.loads((DIR / 'west/ocean-journey.json').read_text())
        self.assertTrue(west['passed']); self.assertEqual(west['rom_sha256'], r['rom_sha256'])
        self.assertEqual(len(west['transitions']), 24); self.assertEqual(len(west['save_continue']), 6)
        for saved in west['save_continue']: self.assertEqual(saved['before'], saved['after'])

    def test_remaining_campaign_work_is_explicit(self):
        r = self.report()
        self.assertTrue(r['initial_party_position_and_prior_story_states_are_fixtures'])
        self.assertTrue(r['wild_encounters_disabled'])
        self.assertFalse(r['full_campaign_playthrough']); self.assertFalse(r['balance_validated'])
        self.assertEqual(r['native_trainer_battles'], [])

if __name__ == '__main__': unittest.main()
