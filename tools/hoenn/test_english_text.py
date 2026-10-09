"""English dialogue and capture persistence on the current native candidate."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'mods/hoenn/english-text-validation'
def read(path): return json.loads((DIR / path).read_text())

class EnglishGame(unittest.TestCase):
    def native(self, path):
        r = read(path); self.assertTrue(r['passed'])
        self.assertEqual(r['rom_sha256'], read('ball/reproduction.json')['rom_sha256'])
        return r

    def test_ordered_replay_checks_seven_source_files(self):
        text, ball = read('text/reproduction.json'), read('ball/reproduction.json')
        for r in [text, ball]:
            self.assertTrue(r['passed']); self.assertTrue(r['deterministic_replay']); self.assertTrue(r['idempotent'])
        self.assertEqual(text['files'], 6); self.assertEqual(ball['files'], 1)
        self.assertEqual(text['rom_sha256'], ball['baseline_rom_sha256'])
        self.assertEqual(text['baseline_rom_sha256'], json.loads(
            (ROOT / 'mods/hoenn/sky-pillar-validation/reproduction.json').read_text())['rom_sha256'])

    def test_english_translation_keeps_logic_and_fits_normal_font(self):
        r = self.native('english-audit.json')
        self.assertEqual(r['game_language'], 'English'); self.assertEqual(r['translated_literals'], 97)
        self.assertEqual(len(r['text_files']), 6)
        self.assertTrue(all(f['non_text_bytes_unchanged'] for f in r['text_files']))
        self.assertGreater(r['scanned_manifest_source_files'], 3000)
        self.assertGreater(r['scanned_quoted_literals'], 100000)
        self.assertEqual(r['portuguese_marker_matches'], 0)
        self.assertEqual(r['checked_dialogue_lines'], 160)
        self.assertLessEqual(r['maximum_normal_font_line_pixels'], r['normal_font_limit_pixels'])
        self.assertFalse(r['every_dialogue_visually_reviewed'])

    def test_native_starting_homes_keep_gifts_and_national_dex(self):
        regions = set()
        for city in [1, 17]:
            r = self.native(f'home-{city}/english-dialogue.json'); regions.add(r['region'])
            for key in ['native_city_choice_and_arrival', 'all_three_water_hms_given',
                        'native_starter_menu', 'national_dex_enabled']:
                self.assertTrue(r[key])
            self.assertEqual(r['starter_level'], 5)
            for image in ['english-family-gift-dialogue', 'english-professor-first-page', 'english-starter-menu']:
                self.assertTrue((DIR / f'home-{city}' / (image + '.png')).is_file())
        self.assertEqual(regions, {'Kanto', 'Hoenn'})

    def test_mythical_legendary_and_ultra_beast_capture_with_retries(self):
        for dex, access in [(1025, 'surf'), (249, 'dive'), (793, 'surf')]:
            r = self.native(f'capture-{dex}/special-capture-continue.json')
            self.assertEqual(r['national_dex'], dex); self.assertEqual(r['access'], access)
            for key in ['locked_with_15_badges', 'unlocked_with_16_before_leagues',
                        'real_escape_and_retry', 'real_knockout_and_retry', 'real_master_ball_capture',
                        'native_surface_entry_return_and_reentry', 'no_internal_warps_or_script_entries',
                        'captured_npc_absent_after_continue_and_reentry', 'no_duplicate_after_continue']:
                self.assertTrue(r[key], (dex, key))
            self.assertEqual([r['escape_outcome'], r['knockout_outcome'], r['capture_outcome']], [4, 1, 7])
            self.assertGreater(r['knockout_attacks'], 0)
            self.assertEqual(len(r['transitions']), 3)

    def test_seven_continues_preserve_the_captured_individual_and_altar(self):
        saves = []
        for dex in [1025, 249, 793]:
            r = self.native(f'capture-{dex}/special-capture-continue.json')
            saves.extend(r['save_continue'])
            for saved in r['save_continue']:
                self.assertEqual(saved['before'], saved['after'])
                state = saved['after']
                self.assertTrue(state['capture_flag']); self.assertTrue(state['caught_dex'])
                self.assertEqual(state['captured_species'], r['species_id'])
                self.assertEqual(state['party_count'], 2)
                self.assertEqual(state['league_clear'], [False, False])
                self.assertEqual([state['kanto_badges'], state['hoenn_badges']], [8, 8])
        self.assertEqual(len(saves), 7)
        self.assertEqual(sorted(s['after']['mode'] for s in saves), [1, 1, 1, 8, 8, 8, 16])

    def test_pwt_registration_still_enforces_six_member_singles(self):
        r = self.native('pwt/pwt-six.json')
        self.assertEqual(r['team_size'], 6); self.assertEqual(len(r['guards']), 7)
        self.assertTrue(r['reversed_order_preserved']); self.assertTrue(r['original_party_restored'])
        self.assertTrue(all(g['refused'] and g['party_unchanged'] for g in r['guards']))

    def test_fixtures_and_campaign_limits_remain_explicit(self):
        for dex in [1025, 249, 793]:
            r = self.native(f'capture-{dex}/special-capture-continue.json')
            self.assertTrue(r['party_badges_ball_and_initial_surface_position_are_fixtures'])
            self.assertTrue(r['knockout_attack_boost_is_fixture'])
            self.assertFalse(r['full_campaign_playthrough']); self.assertFalse(r['balance_validated'])
            self.assertFalse(r['all_special_species_captures_validated'])

if __name__ == '__main__': unittest.main()
