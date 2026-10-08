"""Evidence for the climate mission and real native double/tag battles."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / 'mods/hoenn/aftermath-validation'


def report(name):
    return json.loads((VALIDATION / (name + '.json')).read_text())


class StoryAftermathRequirements(unittest.TestCase):
    def native(self, name):
        evidence = report(name)
        self.assertTrue(evidence['passed'])
        self.assertEqual(evidence['rom_sha256'], report('reproduction')['rom_sha256'])
        return evidence

    def test_overlay_replays_from_the_mega_candidate_and_preserves_native_scenes(self):
        reproduction = report('reproduction')
        previous = json.loads((ROOT / 'mods/hoenn/mega-validation/reproduction.json').read_text())
        self.assertEqual(reproduction['baseline_rom_sha256'], previous['rom_sha256'])
        self.assertTrue(reproduction['passed'])
        self.assertTrue(reproduction['deterministic_replay'])
        self.assertTrue(reproduction['idempotent'])
        self.assertEqual(reproduction['files'], 3)
        catalog = self.native('catalog')
        self.assertEqual(catalog['enabled_mega_forms'], 97)
        self.assertEqual(catalog['missing_mega_targets'], [])
        self.assertEqual(catalog['incomplete_assets'], [])
        self.assertFalse(catalog['stones_distributed'])
        prep = report('preparation')
        self.assertEqual(prep['gate'], 14)
        self.assertEqual(prep['hoenn_badge_threshold'], 7)
        self.assertFalse(prep['new_flags_allocated'])
        self.assertFalse(prep['full_campaign_validated'])
        for check in ['kanto_gates_unchanged', 'native_rayquaza_scene_preserved',
                      'rayquaza_capture_not_required', 'no_new_roadblocks',
                      'homes_accessible_during_crisis']:
            self.assertTrue(prep[check], check)
        self.assertEqual(set(prep['prepared_sha256']), {
            'src/journey_campaign_gates.c', 'data/scripts/journey_campaign_gates.inc',
            'data/maps/SootopolisCity/scripts.inc'})
        self.assertEqual(set(prep['preserved_native_sha256']), {
            'data/maps/SeafloorCavern_Room9/scripts.inc', 'data/maps/SkyPillar_Top/scripts.inc',
            'data/maps/MossdeepCity_SpaceCenter_2F/scripts.inc'})

    def test_battle_bond_and_partner_mega_coexist_in_real_double_battles(self):
        for case, slot, ash in [('hidden', 2, True), ('event', 0, True),
                                 ('torrent', 0, False), ('protean', 1, False)]:
            with self.subTest(case=case):
                native = self.native('double-' + case)
                self.assertEqual(native['ability_slot'], slot)
                self.assertEqual(native['ash_after_ko'], ash)
                self.assertEqual(native['simultaneous_forms'], ash)
                self.assertEqual(native['rendered_at_action_menu'], ash)
                self.assertTrue(all(native['player_move_selections']))
                for check in ['real_tate_liza_double_battle', 'partner_mega',
                              'both_original_species_restored', 'original_ability_slot_restored',
                              'real_hoenn_badge_awarded', 'kanto_badges_unchanged',
                              'native_save_preserves_slot_and_badge', 'mega_items_added_only_in_fixture']:
                    self.assertTrue(native[check], check)

    def test_real_steven_victory_survives_the_rival_call(self):
        native = self.native('maxie-aftermath')
        for check in ['real_steven_maxie_tabitha_battle', 'native_victory_and_aftermath',
                      'native_space_center_invasion', 'ash_after_ko',
                      'six_owned_pokemon_and_personalities_restored', 'hidden_slot_preserved',
                      'native_rival_call_consumes_legacy_flag', 'completion_state_remains_three',
                      'archie_permission_survives_call', 'remaining_gym_stays_gated_by_archie',
                      'regional_badges_unchanged', 'native_save_preserves_completion']:
            self.assertTrue(native[check], check)
        self.assertTrue(native['party_selection_screen_validated'])
        self.assertTrue(native['prerequisites_are_initial_state_fixtures'])
        self.assertFalse(native['full_campaign_playthrough'])

    def test_real_archie_victory_and_rayquaza_scene_unlock_the_last_arbitrary_gym(self):
        native = self.native('archie-aftermath')
        for check in ['real_giovanni_archie_shelly_battle', 'native_victory', 'ash_after_ko',
                      'ai_partner_present', 'original_kyogre_scene_completed', 'actual_route128_arrival',
                      'canonical_quest_completion_flag', 'original_rayquaza_awakening',
                      'original_rayquaza_peace_scene', 'awakening_alone_keeps_gym_gate',
                      'physical_gym_blocked_before_victory', 'physical_gym_open_after_victory',
                      'physical_gym_blocked_during_climate_crisis', 'native_guide_weather_mission',
                      'six_owned_pokemon_restored', 'owned_personalities_and_trainer_ids_preserved',
                      'hidden_slot_preserved', 'regional_badges_unchanged', 'native_save_preserves_completion',
                      'family_house_accessible_during_crisis']:
            self.assertTrue(native[check], check)
        self.assertGreater(native['player_attacks'], 0)
        self.assertTrue(native['prerequisites_are_initial_state_fixtures'])
        self.assertFalse(native['full_campaign_playthrough'])

    def test_climate_gate_respects_all_badge_subsets_and_both_regions(self):
        native = self.native('campaign-matrix')
        self.assertEqual(native['gate_cases'], 16 * 256)
        self.assertEqual(native['permission_cases'], 36)
        weather = next(c for c in native['checks'] if c['scenario'] == 'weather_crisis')
        self.assertEqual(weather, dict(region='hoenn', scenario='weather_crisis',
                                      badge_subsets=256, threshold=7, pending_event=14))
        self.assertTrue(native['other_region_badges_cannot_bypass_gate'])
        self.assertTrue(native['flags_are_initial_state_fixtures'])
        self.assertFalse(native['full_campaign_playthrough'])


if __name__ == '__main__':
    unittest.main()
