"""Evidence for removing the obsolete Seafloor entrance guard dependency."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / 'mods/hoenn/seafloor-access-validation'
def read(path): return json.loads((REPORTS / path).read_text())

class SeafloorAccess(unittest.TestCase):
    def test_strict_single_map_overlay_preserves_story_permissions_and_save(self):
        p, r = read('preparation.json'), read('reproduction.json')
        for key in ['passed', 'deterministic_replay', 'idempotent']: self.assertTrue(r[key])
        self.assertEqual(r['files'], 1)
        self.assertEqual(set(p['prepared_sha256']), {'data/maps/SeafloorCavern_Entrance/map.json'})
        self.assertEqual((p['guard']['before'], p['guard']['after']), ([10, 2], [11, 3]))
        for key in ['guard_dialogue_visibility_and_steven_event_retained', 'only_guard_coordinates_changed',
                    'native_dive_surf_and_boss_missions_retained', 'badge_scaling_and_save_layout_unchanged']:
            self.assertTrue(p[key], key)
        self.assertIn('src/journey_campaign_gates.c', p['preserved_native_sha256'])
        self.assertIn('data/maps/SeafloorCavern_Room9/scripts.inc', p['preserved_native_sha256'])
        self.assertFalse(p['new_flags_allocated']); self.assertFalse(p['full_campaign_validated'])

    def native(self):
        r = read('native/seafloor-route.json')
        self.assertTrue(r['passed'])
        self.assertEqual(r['rom_sha256'], read('reproduction.json')['rom_sha256'])
        return r

    def test_baseline_real_dive_and_resurface_still_leave_guard_blocking(self):
        b = read('baseline/seafloor-baseline.json')
        self.assertTrue(b['passed'])
        self.assertEqual(b['rom_sha256'], read('reproduction.json')['baseline_rom_sha256'])
        self.assertTrue(b['native_zero_badge_dive']); self.assertTrue(b['native_resurface_into_cavern'])
        self.assertTrue(b['native_entrance_guard_blocks_passage'])
        self.assertTrue(b['guard_visibility_not_faked'])
        self.assertEqual(b['position'], [10, 3])

    def test_native_water_access_and_walk_reach_archie_without_land_hms(self):
        r = self.native()
        self.assertTrue(r['native_zero_badge_dive']); self.assertTrue(r['native_resurface_into_cavern'])
        self.assertTrue(r['reaches_archie_without_strength_rock_smash_flash_or_acro'])
        self.assertTrue(r['no_internal_position_warps_or_event_entries'])
        self.assertTrue(r['relocated_grunt_visible_and_native_dialogue_retained'])
        self.assertGreater(r['walked_steps'], 100)
        self.assertTrue(r['surf_prompts'])
        destinations = {t['destination'][0] for t in r['original_map_transitions']}
        self.assertTrue({'Underwater_SeafloorCavern', 'SeafloorCavern_Room1',
                         'SeafloorCavern_Room8', 'SeafloorCavern_Room9'} <= destinations)
        for win in r['wins']:
            self.assertEqual(win['outcome'], 1); self.assertGreater(win['attacks'], 0)
            self.assertTrue(win['native_defeated_flag'])
            if win['second_trainer'] is not None:
                self.assertTrue(win['double_battle']); self.assertTrue(win['second_native_defeated_flag'])
        shelly = next(w for w in r['wins'] if w['trainer'] == 33)
        self.assertEqual(shelly['second_trainer'], 567)

    def test_boss_permission_and_continue_preserve_required_missions_and_zero_badges(self):
        r = self.native()
        self.assertTrue(r['native_boss_trigger_refuses_missing_missions'])
        self.assertTrue(r['native_save_continue_preserves_zero_badges'])
        self.assertTrue(r['starting_ocean_party_stats_healing_are_fixtures'])
        self.assertTrue(r['wild_encounters_disabled'])
        self.assertFalse(r['full_campaign_playthrough']); self.assertFalse(r['balance_validated'])

    def test_all_badge_subsets_keep_aqua_episodes_giovanni_and_space_center_required(self):
        r = read('matrix/campaign-matrix.json')
        self.assertTrue(r['passed'])
        self.assertEqual(r['rom_sha256'], read('reproduction.json')['rom_sha256'])
        self.assertEqual((r['gate_cases'], r['permission_cases']), (5120, 44))
        for key in ['all_regional_badge_subsets', 'native_aqua_episodes_required',
                    'other_region_badges_cannot_bypass_gate', 'giovanni_and_space_center_required']:
            self.assertTrue(r[key], key)

if __name__ == '__main__': unittest.main()
