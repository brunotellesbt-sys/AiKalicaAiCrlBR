"""Continuous western ocean travel and regressions on the English candidate."""
from collections import Counter
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'mods/hoenn/ocean-journey-validation'
def read(path): return json.loads((DIR / path).read_text())

class OceanJourney(unittest.TestCase):
    def native(self, path):
        r = read(path); self.assertTrue(r['passed'])
        expected = json.loads((ROOT / 'mods/hoenn/english-text-validation/ball/reproduction.json').read_text())
        self.assertEqual(r['rom_sha256'], expected['rom_sha256'])
        return r

    def test_continuous_return_visits_lake_and_both_hoenn_towns(self):
        r = self.native('native/ocean-journey.json')
        self.assertTrue(r['continuous_roundtrip']); self.assertEqual(r['start'], r['end'])
        self.assertEqual(r['start'], ['CinnabarIsland_Frlg', 11, 12])
        self.assertEqual(len(r['legs']), 18); self.assertGreater(r['position_changes'], 1200)
        goals = {leg['goal'][0] for leg in r['legs']}
        self.assertTrue({'Route114', 'RustboroCity', 'DewfordTown', 'CinnabarIsland_Frlg'}.issubset(goals))
        self.assertTrue(r['no_midroute_warps_or_direct_trainer_scripts'])

    def test_twenty_four_map_connections_have_reciprocal_native_traversals(self):
        r = self.native('native/ocean-journey.json'); crossings = r['transitions']
        self.assertEqual(len(crossings), 24)
        counts = Counter((t['source'][0], t['destination'][0]) for t in crossings)
        for (a, b), count in counts.items(): self.assertEqual(count, counts[b, a])
        visited = {n for a, b in counts for n in [a, b]}
        self.assertEqual(visited, set(r['maps'])); self.assertEqual(len(visited), 13)
        for a, b in [('JourneyWestRiver', 'Route114'), ('JourneyRustboroGate', 'Route115'),
                     ('JourneyDewfordGate', 'Route105'), ('Route106', 'DewfordTown')]:
            self.assertEqual(counts[a, b], 1)

    def test_six_continues_preserve_modes_formats_and_separate_badge_banks(self):
        r = self.native('native/ocean-journey.json'); saves = r['save_continue']
        self.assertEqual(len(saves), 6)
        self.assertEqual(Counter(s['after']['mode'] for s in saves), {1: 3, 8: 3})
        self.assertEqual(Counter(s['after']['frlg_format'] for s in saves), {True: 2, False: 4})
        for saved in saves:
            self.assertEqual(saved['before'], saved['after'])
            self.assertEqual(saved['after']['kanto_badges'], 0); self.assertEqual(saved['after']['hoenn_badges'], 0)
            self.assertFalse(saved['after']['special_capture_unlocked'])
            self.assertTrue((DIR / 'native' / (saved['label'] + '-after-continue.png')).is_file())

    def test_native_surf_prompts_and_sight_line_battles(self):
        r = self.native('native/ocean-journey.json')
        self.assertGreaterEqual(len(r['surf_prompts']), 6)
        self.assertEqual({b['trainer'] for b in r['native_trainer_battles']}, {1534, 441, 339, 153, 151})
        for battle in r['native_trainer_battles']:
            self.assertEqual(battle['outcome'], 1); self.assertTrue(battle['native_defeated_flag'])
            self.assertGreater(battle['attacks'], 0)

    def test_elevation_changes_do_not_break_sanctuaries_or_sky_pillar(self):
        r = self.native('sanctuaries/sanctuary-routes.json')
        self.assertEqual(len(r['sites']), 14); self.assertEqual(len(r['altars']), 105)
        self.assertEqual(len(r['save_continue']), 33)
        for saved in r['save_continue']: self.assertEqual(saved['before'], saved['after'])
        sky = self.native('sky-pillar/sky-pillar-access.json')
        self.assertTrue(sky['native_full_tower_walk_return_and_reentry'])
        self.assertTrue(sky['native_early_awakening_trigger_refused'])
        self.assertEqual(len(sky['save_continue']), 3)

    def test_campaign_and_balance_limits_are_explicit(self):
        r = self.native('native/ocean-journey.json')
        self.assertTrue(r['initial_party_position_and_prior_story_states_are_fixtures'])
        self.assertTrue(r['trainer_stats_and_healing_are_fixtures']); self.assertTrue(r['wild_encounters_disabled'])
        self.assertFalse(r['full_campaign_playthrough']); self.assertFalse(r['balance_validated'])

if __name__ == '__main__': unittest.main()
