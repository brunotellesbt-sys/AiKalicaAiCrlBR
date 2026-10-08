"""Native evidence for the standalone eight-participant Singles PWT."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / 'mods/hoenn/pwt-validation'

def report(path):
    return json.loads((VALIDATION / path).read_text())

class PWTRequirements(unittest.TestCase):
    def native(self, path):
        r = report(path)
        self.assertTrue(r['passed'])
        self.assertEqual(r['rom_sha256'], report('reproduction.json')['rom_sha256'])
        return r

    def test_separate_overlay_preserves_existing_dome_and_gym_rules(self):
        r = report('reproduction.json')
        self.assertEqual(r['baseline_rom_sha256'], json.loads((ROOT / 'mods/hoenn/family-postgame-validation/reproduction.json').read_text())['rom_sha256'])
        self.assertTrue(r['deterministic_replay']); self.assertTrue(r['idempotent'])
        self.assertEqual(r['files'], 19)
        p = report('preparation.json')
        self.assertEqual((p['participants'], p['rounds'], p['team_size'], p['level']), (8, 3, 3, 50))
        self.assertFalse(p['doubles_enabled'])
        self.assertTrue(p['save_layout_unchanged']); self.assertTrue(p['existing_dome_retained'])
        for path in ['src/battle_dome.c', 'src/journey_gym_scaling.c', 'data/maps/BattleFrontier_BattleDomeLobby/scripts.inc']:
            self.assertIn(path, p['preserved_native_sha256'])

    def test_three_complete_native_tournaments_have_nine_victories(self):
        r = self.native('native/pwt.json')
        self.assertEqual(r['native_battle_victories'], 9)
        self.assertEqual({t['pool'] for t in r['tournaments']}, {0, 1, 2})
        for t in r['tournaments']:
            self.assertEqual(len(t['leaves']), 8)
            self.assertEqual(len(set(t['leaves'])), 8)
            self.assertEqual(t['leaves'].count(255), 1)
            allowed = set(range(8)) if t['pool'] == 0 else set(range(8, 16)) if t['pool'] == 1 else set(range(18))
            self.assertLessEqual(set(t['leaves']) - {255}, allowed)
            self.assertEqual([w['round'] for w in t['wins']], [0, 1, 2])
            self.assertTrue(all(w['outcome'] == 1 and w['attacks'] > 0 for w in t['wins']))
            self.assertEqual(t['reward_bp'], 3)
            for key in ['original_party_byte_identical', 'flags_and_money_unchanged', 'native_flash_save_reload']:
                self.assertTrue(t[key])
        self.assertTrue(r['no_bag_items']); self.assertTrue(r['levels_normalized_to_50'])
        self.assertTrue(r['physical_receptionist_interaction'])
        self.assertTrue(r['battle_stats_and_travel_are_fixtures'])
        self.assertFalse(r['balance_validated']); self.assertFalse(r['full_campaign_playthrough'])

    def test_defeat_forfeit_retirement_and_cancel_restore_original_party(self):
        r = self.native('native/pwt.json')
        self.assertEqual(r['native_loss']['outcome'], 2)
        self.assertTrue(r['native_forfeit']['forfeit'])
        self.assertNotEqual(r['native_forfeit']['outcome'], 1)
        for key in ['selection_cancel_restores_party', 'between_round_retirement_restores_party', 'defeat_restores_party_without_whiteout', 'battle_bond_and_hidden_slot_restored']:
            self.assertTrue(r[key])
        self.assertTrue(any(w['ash_seen'] for t in r['tournaments'] for w in t['wins']))

    def test_all_rosters_have_three_distinct_mons_items_and_real_moves(self):
        r = self.native('native/pwt.json')
        self.assertEqual(len(r['native_roster_teams']), 18)
        self.assertEqual({t['index'] for t in r['native_roster_teams']}, set(range(18)))
        self.assertEqual(len({t['trainer'] for t in r['native_roster_teams']}), 18)
        for t in r['native_roster_teams']:
            self.assertEqual(len(t['mons']), 3)
            self.assertEqual({m['level'] for m in t['mons']}, {50})
            self.assertEqual(len({m['species'] for m in t['mons']}), 3)
            self.assertEqual(len({m['item'] for m in t['mons']}), 3)
            self.assertTrue(all(m['move'] for m in t['mons']))
        self.assertEqual({c['case'] for c in r['entry_guards']}, {'slot_out_of_range', 'same_slot', 'same_species', 'same_national_forms', 'same_item', 'egg', 'banned_mewtwo'})
        self.assertTrue(all(c['refused'] and c['party_unchanged'] for c in r['entry_guards']))

    def test_real_guide_counter_walk_and_door_connect_the_module(self):
        r = self.native('access/pwt-access.json')
        for key in ['native_guide_interaction', 'physical_counter_walk', 'native_selection_cancel', 'physical_exit_door_returns_to_dome']:
            self.assertTrue(r[key])
        self.assertTrue(r['initial_dome_warp_is_fixture'])
        self.assertFalse(r['full_frontier_journey_validated'])

    def test_catalog_destinations_and_story_gates_remain_valid(self):
        r = self.native('catalog.json')
        self.assertEqual(r['base_species_count'], 1025); self.assertEqual(r['missing_assets'], [])
        r = self.native('map-destinations.json')
        self.assertEqual((r['maps'], r['warps'], r['connections']), (1048, 2802, 372))
        self.assertEqual(r['errors'], [])
        r = self.native('campaign-matrix.json')
        self.assertEqual((r['gate_cases'], r['permission_cases']), (4096, 36))
        self.assertTrue(r['giovanni_and_space_center_required'])

if __name__ == '__main__':
    unittest.main()
