"""Evidence for shared Kanto sprites restoring Dive as Surf on Continue."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'mods/hoenn/water-continue-validation'
def read(path): return json.loads((DIR / path).read_text())

class WaterContinue(unittest.TestCase):
    def native(self, path):
        r = read(path); self.assertTrue(r['passed'])
        self.assertEqual(r['rom_sha256'], read('reproduction.json')['rom_sha256'])
        return r

    def test_strict_overlay_changes_only_avatar_inference_without_save_or_art_changes(self):
        p, r = read('preparation.json'), read('reproduction.json')
        for key in ['passed', 'deterministic_replay', 'idempotent']: self.assertTrue(r[key])
        self.assertEqual(r['files'], 1)
        self.assertEqual(set(p['prepared_sha256']), {'src/field_player_avatar.c'})
        for key in ['map_type_restores_underwater_before_shared_sprite_lookup',
                    'original_avatar_graphics_tables_retained', 'land_and_surface_lookup_retained',
                    'native_dive_surf_and_boss_missions_retained', 'badge_scaling_and_save_layout_unchanged']:
            self.assertTrue(p[key], key)
        self.assertFalse(p['new_flags_allocated']); self.assertFalse(p['full_campaign_validated'])
        self.assertIn('src/overworld.c', p['preserved_native_sha256'])

    def test_baseline_reproduces_wrong_mode_only_for_both_kanto_underwater_avatars(self):
        b = read('baseline/water-continue.json')
        self.assertTrue(b['passed']); self.assertFalse(b['candidate'])
        self.assertEqual(b['rom_sha256'], read('reproduction.json')['baseline_rom_sha256'])
        self.assertEqual(b['wrong_mode_cases'], ['kanto-0-underwater', 'kanto-1-underwater'])
        self.assertEqual(len(b['rows']), 16)
        for row in b['rows']:
            if row['label'] in b['wrong_mode_cases']:
                self.assertEqual((row['before']['mode'], row['after']['mode']), (16, 8))
                self.assertEqual(row['before']['position'], row['after']['position'])
                self.assertEqual(row['before']['map'], row['after']['map'])
            else: self.assertTrue(row['mode_preserved'])

    def test_all_four_avatars_keep_foot_surf_dive_and_resurfaced_modes_after_continue(self):
        r = self.native('native/water-continue.json')
        self.assertTrue(r['candidate']); self.assertEqual(r['wrong_mode_cases'], [])
        self.assertEqual(len(r['rows']), 16)
        expected = {f'{region}-{gender}-{state}' for region in ['kanto', 'hoenn'] for gender in [0, 1]
                    for state in ['foot', 'surf', 'underwater', 'resurfaced']}
        self.assertEqual({row['label'] for row in r['rows']}, expected)
        for row in r['rows']:
            self.assertTrue(row['mode_preserved'])
            self.assertEqual(row['before'], row['after'])
            self.assertEqual(row['after']['kanto_badges'], 0)
            self.assertEqual(row['after']['hoenn_badges'], 0)
        self.assertTrue(r['native_dive_and_resurface'])
        self.assertTrue(r['origins_genders_badges_travel_and_known_moves_are_fixtures'])
        self.assertFalse(r['full_campaign_playthrough']); self.assertFalse(r['balance_validated'])

    def test_native_seafloor_return_passages_lead_back_to_route128(self):
        r = self.native('route/seafloor-route.json')
        self.assertTrue(r['native_dive_out_and_return_to_route128'])
        self.assertGreater(r['return_walked_steps'], 40)
        self.assertTrue(r['no_internal_position_warps_or_event_entries'])
        destinations = {t['destination'][0] for t in r['return_map_transitions']}
        self.assertTrue({'SeafloorCavern_Entrance', 'Underwater_Route128'} <= destinations)
        self.assertTrue(r['return_surf_prompts'])
        self.assertTrue(r['in_battle_status_recovery_is_fixture'])

    def test_underwater_and_surface_continue_keep_position_mode_and_story_on_return(self):
        r = self.native('route/seafloor-route.json'); saves = r['water_save_continues']
        self.assertEqual([s['before']['map'] for s in saves], [
            'Underwater_SeafloorCavern', 'Underwater_Route128', 'Route128'])
        self.assertEqual([s['before']['avatar_mode'] for s in saves], [16, 16, 8])
        for saved in saves:
            self.assertEqual(saved['before'], saved['after'])
            self.assertEqual(saved['after']['kanto_badges'], 0)
            self.assertEqual(saved['after']['hoenn_badges'], 0)
            self.assertFalse(saved['after']['kyogre_escaped'])
            self.assertFalse(saved['after']['archie_permission'])
        self.assertEqual(saves[-1]['after']['position'], r['dive_point'])

    def test_regional_missions_and_archie_permissions_still_match_all_badge_subsets(self):
        r = self.native('missions/campaign-matrix.json')
        self.assertEqual((r['gate_cases'], r['permission_cases']), (5120, 44))
        for key in ['all_regional_badge_subsets', 'native_aqua_episodes_required',
                    'other_region_badges_cannot_bypass_gate', 'giovanni_and_space_center_required']:
            self.assertTrue(r[key], key)

if __name__ == '__main__': unittest.main()
