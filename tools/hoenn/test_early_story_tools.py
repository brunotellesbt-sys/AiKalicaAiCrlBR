"""Regression contracts for early ownership and preserved story events."""
import csv
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'mods/hoenn/early-story-tools-validation'
def read(path): return json.loads((DIR / path).read_text())

class EarlyStoryTools(unittest.TestCase):
    def setUp(self):
        self.replay = read('preparation/reproduction.json')
        self.prep = read('preparation/preparation.json')

    def native(self, region):
        r = read(region + '/early-story-tools.json')
        self.assertTrue(r['passed'])
        self.assertEqual(r['rom_sha256'], self.replay['rom_sha256'])
        return r

    def test_source_replay_is_ordered_idempotent_and_complete(self):
        for key in ['passed', 'deterministic_replay', 'idempotent']: self.assertTrue(self.replay[key])
        self.assertEqual(self.replay['files'], 7)
        previous = json.loads((ROOT / 'mods/hoenn/tower-habitat-validation/preparation/reproduction.json').read_text())
        self.assertEqual(self.replay['baseline_rom_sha256'], previous['rom_sha256'])
        self.assertEqual(len(self.prep['prepared_sha256']), 7)
        self.assertFalse(self.prep['new_save_fields'])

    def test_native_mother_gifts_work_in_both_regions_without_badges(self):
        for region in ['kanto', 'hoenn']:
            r = self.native(region)
            self.assertEqual(r['region'].lower(), region)
            for key in ['real_city_choice_and_mother_input', 'mother_only', 'zero_badges',
                        'original_quest_flags_preserved_by_mother', 'poke_flute_not_given_at_start']:
                self.assertTrue(r[key])
            self.assertEqual(r['all_selected_homes_native_special'], list(range(1, 32)))

    def test_full_pocket_partial_retries_pc_storage_and_save(self):
        for region in ['kanto', 'hoenn']:
            r = self.native(region)
            for key in ['pc_ownership_prevents_duplicates', 'full_bag_and_partial_retries', 'native_save_roundtrip']:
                self.assertTrue(r[key])

    def test_original_family_healing_starter_and_doors_still_work(self):
        for region in ['kanto', 'hoenn']:
            r = read(region + '-family/family.json')
            self.assertTrue(r['passed'])
            for key in ['original_mother_heal', 'family_gifts_once', 'native_save_roundtrip', 'actual_stairs_and_door']:
                self.assertTrue(r[key])
            self.assertEqual(r['starter_level'], 5)

    def test_original_owners_finish_events_with_bag_pc_or_missing_tool(self):
        for region in ['kanto', 'hoenn']:
            cases = self.native(region)['original_item_giver_continuations']
            self.assertEqual(len(cases), 9)
            for location in ['Route104_PrettyPetalFlowerShop', 'RocketHideout_B4F_Frlg', 'Route120']:
                rows = [c for c in cases if c['map'] == location]
                self.assertEqual({c['storage'] for c in rows}, {'bag', 'pc', 'missing'})
            self.assertTrue(all(c['original_receipt_flag_set'] and not c['duplicate'] for c in cases))
            self.assertTrue(self.native(region)['silph_scope_pickup_full_bag_retry'])

    def test_flute_remains_first_badge_reward_for_all_sixteen_gyms(self):
        r = read('first-badge-and-west-sea.json')
        self.assertEqual(r['rom_sha256'], self.replay['rom_sha256'])
        c = next(c for c in r['checks'] if c['check'] == 'first_badge_flute_native_rewards')
        self.assertEqual(len(set(c['gyms'])), 16)
        for key in ['passed', 'no_reward_before_badges', 'repeated_reward_no_duplicate',
                    'full_bag_retry', 'hoenn_reward_recognized_by_fuji', 'other_region_badges_unchanged']:
            self.assertTrue(c[key])
        self.assertTrue(c['battle_victory_simulated'])

    def test_fixed_encounters_wild_habitats_and_level_logic_preserved(self):
        preserved = self.prep['preserved_native_sha256']
        for path in ['data/maps/Route12_Frlg/scripts.inc', 'data/maps/Route16_Frlg/scripts.inc',
            'data/scripts/kecleon.inc', 'data/maps/PokemonTower_6F_Frlg/scripts.inc',
            'data/maps/BattleFrontier_OutsideEast/scripts.inc', 'src/data/wild_encounters.json',
            'include/journey_wild_data.h', 'include/journey_habitat_data.h', 'src/journey_wild.c']:
            self.assertIn(path, preserved)
        previous = json.loads((ROOT / 'mods/hoenn/tower-habitat-validation/preparation/preparation.json').read_text())
        for path in ['src/data/wild_encounters.json', 'include/journey_wild_data.h', 'include/journey_habitat_data.h']:
            self.assertEqual(preserved[path], previous['prepared_sha256'][path])

    def test_english_audit_preserves_translations_and_measures_added_dialogue(self):
        r = read('english-audit.json')
        self.assertTrue(r['passed']); self.assertEqual(r['rom_sha256'], self.replay['rom_sha256'])
        self.assertEqual(r['translated_literals'], 97); self.assertEqual(r['portuguese_marker_matches'], 0)
        self.assertEqual(r['early_story_tools_additional_lines'], 10)
        self.assertLessEqual(r['maximum_normal_font_line_pixels'], r['normal_font_limit_pixels'])
        self.assertTrue(all(f['translation_layer_non_text_bytes_unchanged'] for f in r['text_files']))
        changed = {f['path'] for f in r['text_files'] if not f['non_text_bytes_unchanged']}
        self.assertEqual(changed, {'src/journey_family.c', 'data/scripts/journey_family.inc'})

    def test_current_guide_covers_catalog_and_explicit_story_exceptions(self):
        guide = (ROOT / 'mods/hoenn/POKEMON-LOCATIONS.md').read_text()
        self.assertIn('Encontros fixos ligados à história são exceções', guide)
        self.assertIn('Silph Scope, Devon Scope e Wailmer Pail', guide)
        with (ROOT / 'mods/hoenn/pokemon-locations.csv').open() as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len([r for r in rows if r['category'] == 'comum']), 920)
        self.assertEqual(len([r for r in rows if r['category'] not in ['comum', 'forma regional']]), 105)

    def test_western_crossing_regression_and_validation_limits(self):
        r = read('first-badge-and-west-sea.json')
        seams = [c for c in r['checks'] if c['check'] == 'physical_surf_seam']
        self.assertEqual(len(seams), 18); self.assertTrue(all(c['passed'] for c in seams))
        for region in ['kanto', 'hoenn']:
            r = self.native(region)
            self.assertFalse(r['full_campaign_playthrough']); self.assertFalse(r['original_boss_battles_played'])
            self.assertIn('owner scene states and entries', r['fixtures'])

if __name__ == '__main__': unittest.main()
