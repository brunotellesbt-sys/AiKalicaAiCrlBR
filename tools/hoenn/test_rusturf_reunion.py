"""Regression contracts for the native HM-free Rusturf reunion."""
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'mods/hoenn/rusturf-reunion-validation'
def read(name): return json.loads((DIR / name).read_text())

class RusturfReunion(unittest.TestCase):
    def native(self, name):
        r = read(name)
        self.assertTrue(r['passed'])
        self.assertEqual(r['rom_sha256'], read('preparation/reproduction.json')['rom_sha256'])
        return r

    def test_replay_and_idempotence_after_sixteen_badge_candidate(self):
        r = read('preparation/reproduction.json')
        self.assertTrue(r['passed']); self.assertTrue(r['idempotent']); self.assertTrue(r['deterministic_replay'])
        self.assertEqual(r['files'], 1)
        prior = json.loads((ROOT / 'mods/hoenn/sixteen-badge-league-validation/preparation/reproduction.json').read_text())
        self.assertEqual(r['baseline_rom_sha256'], prior['rom_sha256'])

    def test_baseline_reunion_cannot_start_with_removed_rocks(self):
        r = read('baseline/baseline.json')
        self.assertTrue(r['passed']); self.assertTrue(r['baseline_unreachable_reproduced'])
        self.assertEqual(r['rom_sha256'], read('preparation/reproduction.json')['baseline_rom_sha256'])
        self.assertEqual({c['approach'] for c in r['cases']}, {1, 3})
        self.assertTrue(all(c['original_rock_smash_scene_unreachable'] for c in r['cases']))

    def test_both_physical_approaches_complete_original_scene_without_hms(self):
        r = self.native('native/rusturf-reunion.json')
        self.assertEqual({c['approach'] for c in r['cases']}, {1, 3})
        for c in r['cases']:
            self.assertTrue(c['scene_triggered_by_walking']); self.assertTrue(c['original_couple_exit'])
            self.assertTrue(c['no_moves_or_badges'])
            self.assertEqual(c['tm_strength_quantity'], 1)

    def test_rescue_and_couple_presence_are_required(self):
        r = self.native('native/rusturf-reunion.json')
        self.assertTrue(all(c['pre_rescue_does_not_complete'] and c['hidden_couple_does_not_start_scene'] for c in r['cases']))
        p = read('preparation/preparation.json')
        for e in p['edits'][:3]:
            self.assertIn('FLAG_RECOVERED_DEVON_GOODS', e['after'])
            self.assertIn('FLAG_HIDE_RUSTURF_TUNNEL_WANDA', e['after'])
            # Immediate coordinate scripts only queue the existing frame scene.
            self.assertIn('setvar VAR_RUSTURF_TUNNEL_STATE, 4', e['after'])
            self.assertNotIn('goto RusturfTunnel_EventScript_ClearTunnelScene', e['after'])

    def test_continue_and_revisit_do_not_repeat_reward(self):
        r = self.native('native/rusturf-reunion.json')
        self.assertTrue(all(c['native_continue'] and c['revisit_no_duplicate'] for c in r['cases']))

    def test_gym_mission_checkpoints_and_levels_are_preserved(self):
        r = self.native('matrix/campaign-matrix.json')
        prior = json.loads((ROOT / 'mods/hoenn/sixteen-badge-league-validation/matrix/campaign-matrix.json').read_text())
        self.assertEqual(r['checks'], prior['checks'])
        self.assertEqual(r['gate_cases'], 11008); self.assertEqual(r['permission_cases'], 44)
        p = read('preparation/preparation.json')
        self.assertTrue(p['regional_gym_and_league_rules_preserved'])
        preserved = p['preserved_native_sha256']
        for name in ['src/journey_campaign_gates.c', 'src/journey_gym_scaling.c', 'src/journey_wild.c', 'src/journey_family.c', 'data/maps/RusturfTunnel/map.json']:
            self.assertIn(name, preserved)

    def test_english_and_fixture_limits(self):
        r = self.native('english-audit.json')
        self.assertEqual(r['rusturf_reunion_lines'], 4)
        self.assertEqual(r['portuguese_marker_matches'], 0)
        self.assertLessEqual(r['maximum_normal_font_line_pixels'], r['normal_font_limit_pixels'])
        r = self.native('native/rusturf-reunion.json')
        self.assertTrue(r['initial_location_rescue_and_party_are_fixtures'])
        self.assertFalse(r['full_campaign_playthrough'])

if __name__ == '__main__': unittest.main()
