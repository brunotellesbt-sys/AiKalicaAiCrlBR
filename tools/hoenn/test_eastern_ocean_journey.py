"""Evidence for native continuous Kanto-Sevii-Hoenn travel and persistence."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'mods/hoenn/eastern-ocean-journey-validation'

class EasternOceanJourney(unittest.TestCase):
    def report(self):
        r = json.loads((DIR / 'ocean-journey.json').read_text())
        self.assertTrue(r['passed'])
        ball = json.loads((DIR / 'preparation/reproduction.json').read_text())
        self.assertEqual(r['rom_sha256'], ball['rom_sha256'])
        return r

    def test_continuous_trip_visits_all_seven_ports_and_both_hoenn_exits(self):
        r = self.report()
        self.assertTrue(r['continuous_roundtrip']); self.assertEqual(r['start'], r['end'])
        self.assertEqual(r['start'], ['VermilionCity_Frlg', 20, 20])
        goals = {leg['goal'][0] for leg in r['legs']}
        ports = {n + 'Island_Harbor_Frlg' for n in ['One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven']}
        self.assertTrue((ports | {'Route127', 'Route131', 'PacifidlogTown'}).issubset(goals))
        self.assertTrue(r['no_midroute_warps_or_direct_trainer_scripts'])
        self.assertEqual(r['position_changes'], sum(leg['position_changes'] for leg in r['legs']))
        self.assertTrue(all(leg['position_changes'] > 0 for leg in r['legs']))

    def test_native_connections_join_sevii_to_both_hoenn_routes(self):
        r = self.report()
        pairs = {(t['source'][0], t['destination'][0]) for t in r['transitions']}
        for a, b in [('VermilionCity_Frlg', 'JourneyWorldSea00'),
                     ('JourneyWorldSea06', 'JourneyPacifidlogSea'),
                     ('JourneyPacifidlogSea', 'Route131'), ('Route131', 'PacifidlogTown'),
                     ('JourneyWorldSea04', 'JourneyHoennMiddleSea'), ('JourneyHoennMiddleSea', 'Route127')]:
            self.assertIn((a, b), pairs); self.assertIn((b, a), pairs)
        for n in ['One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven']:
            port = n + 'Island_Harbor_Frlg'
            self.assertTrue(any(a == port for a, b in pairs)); self.assertTrue(any(b == port for a, b in pairs))

    def test_eight_continues_preserve_land_surf_and_independent_badges(self):
        saves = self.report()['save_continue']
        self.assertEqual(len(saves), 8)
        self.assertEqual({s['after']['mode'] for s in saves}, {1, 8})
        self.assertEqual({s['after']['frlg_format'] for s in saves}, {True, False})
        for saved in saves:
            self.assertEqual(saved['before'], saved['after'])
            self.assertEqual(saved['after']['kanto_badges'], 0); self.assertEqual(saved['after']['hoenn_badges'], 0)
            self.assertFalse(saved['after']['special_capture_unlocked'])
            self.assertTrue((DIR / (saved['label'] + '-after-continue.png')).is_file())

    def test_alternate_layout_patch_preserves_events_and_english_text(self):
        r = self.report()
        prep = json.loads((DIR / 'preparation/preparation.json').read_text())
        replay = json.loads((DIR / 'preparation/reproduction.json').read_text())
        failure = json.loads((DIR / 'baseline/failure.json').read_text())
        self.assertFalse(failure['journey_completed'])
        self.assertEqual(failure['rom_sha256'], replay['baseline_rom_sha256'])
        self.assertNotEqual(failure['rom_sha256'], r['rom_sha256'])
        self.assertTrue(replay['deterministic_replay']); self.assertTrue(replay['idempotent'])
        self.assertEqual(set(prep['prepared_sha256']), {'data/layouts/Route131_SkyPillar/map.bin'})
        self.assertTrue(prep['all_events_and_map_connections_preserved'])
        self.assertTrue(prep['native_layout_switch_and_sky_pillar_entrance_preserved'])
        self.assertGreater(len(prep['modified_tiles']), 0)
        for x, y, before, after in prep['modified_tiles']:
            self.assertTrue(48 <= x < 60 and 33 <= y < 40); self.assertNotEqual(before, after)
        saved = next(s for s in r['save_continue'] if s['label'] == 'route131-alternate-layout-surf')
        self.assertEqual(saved['after']['mode'], 8)
        sky = json.loads((DIR / 'sky-pillar/sky-pillar-access.json').read_text())
        self.assertEqual(sky['rom_sha256'], r['rom_sha256'])
        self.assertTrue(sky['native_full_tower_walk_return_and_reentry'])
        self.assertTrue(sky['native_early_awakening_trigger_refused'])
        english = json.loads((DIR / 'english-audit.json').read_text())
        self.assertEqual(english['rom_sha256'], r['rom_sha256'])
        self.assertEqual(english['portuguese_marker_matches'], 0)

    def test_native_battles_and_balance_limits_are_reported_separately(self):
        r = self.report()
        for b in r['native_trainer_battles']:
            self.assertEqual(b['outcome'], 1); self.assertTrue(b['native_defeated_flag']); self.assertGreater(b['attacks'], 0)
        self.assertGreaterEqual(len(r['surf_prompts']), 8)
        self.assertTrue(r['initial_party_position_and_prior_story_states_are_fixtures'])
        self.assertTrue(r['trainer_stats_and_healing_are_fixtures']); self.assertTrue(r['wild_encounters_disabled'])
        self.assertFalse(r['balance_validated']); self.assertFalse(r['full_campaign_playthrough'])

if __name__ == '__main__': unittest.main()
