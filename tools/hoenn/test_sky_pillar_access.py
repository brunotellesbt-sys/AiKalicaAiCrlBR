"""Evidence for an explorable tower without premature climate progression."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'mods/hoenn/sky-pillar-validation'
def read(path): return json.loads((DIR / path).read_text())

class SkyPillarAccess(unittest.TestCase):
    def native(self, path):
        r = read(path); self.assertTrue(r['passed'])
        self.assertEqual(r['rom_sha256'], read('reproduction.json')['rom_sha256'])
        return r

    def test_strict_overlay_preserves_climate_scenes_and_capture_gate(self):
        p, r = read('preparation.json'), read('reproduction.json')
        self.assertEqual(set(p['prepared_sha256']), {'src/journey_campaign_gates.c',
            'data/maps/SkyPillar_Outside/scripts.inc', 'data/maps/SkyPillar_Top/scripts.inc'})
        self.assertEqual(r['files'], 3)
        for key in ['passed', 'deterministic_replay', 'idempotent']: self.assertTrue(r[key])
        for key in ['tower_door_open_before_wallace', 'awakening_requires_native_sootopolis_clash',
                    'awakening_requires_archie_silph_space_center_and_regional_missions',
                    'original_awakening_body_and_peace_scene_preserved', 'capture_still_requires_sixteen_badges',
                    'native_clean_and_cracked_layout_scripts_preserved']:
            self.assertTrue(p[key])
        self.assertFalse(p['new_flags_allocated'])
        for path in ['src/journey_special.c', 'data/maps/SootopolisCity/scripts.inc',
                     'data/maps/SeafloorCavern_Room9/scripts.inc']:
            self.assertIn(path, p['preserved_native_sha256'])

    def test_baseline_closed_door_and_native_tower_visit_with_three_continues(self):
        b = read('baseline/sky-pillar-access.json')
        self.assertTrue(b['passed']); self.assertTrue(b['native_closed_door_reproduced'])
        self.assertEqual(b['rom_sha256'], read('reproduction.json')['baseline_rom_sha256'])
        r = self.native('native/sky-pillar-access.json')
        for key in ['native_full_tower_walk_return_and_reentry', 'native_clean_summit_layout',
                    'native_early_awakening_trigger_refused', 'no_internal_warps_after_initial_placement']:
            self.assertTrue(r[key])
        visited = {t['destination'][0] for t in r['transitions']}
        self.assertTrue({f'SkyPillar_{i}F' for i in range(1, 6)} | {'SkyPillar_Top', 'SkyPillar_Outside'} <= visited)
        self.assertEqual(len(r['save_continue']), 3)
        for saved in r['save_continue']:
            self.assertEqual(saved['before'], saved['after'])
            for key in ['sky_state', 'sootopolis_state', 'cry_done', 'kanto_badges', 'hoenn_badges']:
                self.assertEqual(saved['after'][key], 0)
            for key in ['weather_crisis', 'archie_completed', 'special_capture_unlocked']:
                self.assertFalse(saved['after'][key])

    def test_awakening_checks_all_badge_subsets_and_each_prior_mission(self):
        r = self.native('permissions/rayquaza-permission.json')
        self.assertEqual(r['cases'], 4352)
        self.assertEqual(r['regional_badge_threshold'], 7)
        self.assertTrue(r['other_region_badges_do_not_bypass'])
        self.assertTrue(r['initial_badges_and_event_flags_are_fixtures'])
        expected = {'archie', 'giovanni', 'space-center', 'shelly', 'matt', 'submarine',
                    'institute', 'regional-mission', 'weather-clear', 'already-awakened'}
        self.assertTrue(expected <= {c['scenario'] for c in r['checks'] if not c['ready']})

    def test_native_alliance_awakening_peace_and_final_gym_still_work(self):
        r = self.native('aftermath/archie-aftermath.json')
        for key in ['real_giovanni_archie_shelly_battle', 'native_victory', 'original_kyogre_scene_completed',
                    'original_rayquaza_awakening', 'original_rayquaza_peace_scene',
                    'physical_gym_blocked_during_climate_crisis', 'physical_gym_open_after_victory',
                    'awakening_alone_keeps_gym_gate', 'regional_badges_unchanged', 'native_save_preserves_completion']:
            self.assertTrue(r[key])
        self.assertTrue(r['prerequisites_are_initial_state_fixtures'])
        self.assertFalse(r['full_campaign_playthrough'])

    def test_previous_cave_access_and_all_regional_gates_still_pass(self):
        caves = self.native('caves/cave-access.json')
        for row in caves['rows']: self.assertTrue(row['native_entry_exit_and_reentry'])
        for saved in caves['save_continue']: self.assertEqual(saved['before'], saved['after'])
        r = self.native('missions/campaign-matrix.json')
        self.assertEqual((r['gate_cases'], r['permission_cases']), (5120, 44))

if __name__ == '__main__': unittest.main()
