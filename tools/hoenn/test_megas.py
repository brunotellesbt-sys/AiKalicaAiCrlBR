"""Mega battle evidence; catalogue completeness remains a separate release gate."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / 'mods/hoenn/mega-validation'


def report(name):
    return json.loads((VALIDATION / (name + '.json')).read_text())


class MegaRequirements(unittest.TestCase):
    def test_every_registered_mega_has_an_enabled_form_link(self):
        catalog = report('catalog')
        self.assertEqual(catalog['missing_mega_targets'], [])
        self.assertEqual(catalog['enabled_mega_forms'], 97)
        self.assertEqual(len({link['target_id'] for link in catalog['links']}), 97)
        self.assertEqual(catalog['rom_sha256'], report('reproduction')['rom_sha256'])
        self.assertEqual(report('reproduction')['baseline_rom_sha256'], json.loads(
            (ROOT / 'mods/hoenn/abilities-validation/reproduction.json').read_text())['rom_sha256'])
        self.assertFalse(catalog['stones_distributed'])

    def test_missing_mega_z_art_is_fixed_with_pinned_assets(self):
        baseline = report('base-catalog')
        catalog = report('catalog')
        self.assertFalse(baseline['passed'])
        self.assertTrue(catalog['passed'])
        self.assertFalse(catalog['all_sprites_rendered'])
        self.assertEqual(baseline['incomplete_assets'], [dict(
            id=1558, species='SPECIES_GARCHOMP_MEGA_Z',
            missing=['back', 'front', 'palette', 'shiny_palette'])])
        self.assertEqual(catalog['incomplete_assets'], [])
        self.assertTrue(report('reproduction')['deterministic_replay'])
        self.assertTrue(report('reproduction')['idempotent'])

    def test_native_trigger_and_reversion_in_five_real_battles(self):
        for name in ['charizard-x', 'charizard-y', 'rayquaza', 'greninja', 'garchomp-z']:
            with self.subTest(case=name):
                native = report(name)
                self.assertTrue(native['passed'])
                self.assertEqual(native['rom_sha256'], report('catalog')['rom_sha256'])
                self.assertEqual(native['fixture_met_level'], 5)
                for check in ['real_brock_battle', 'native_start_button', 'transformed',
                              'rendered_at_action_menu', 'restored_base_species',
                              'items_added_only_in_test_fixture']:
                    self.assertTrue(native[check], check)

    def test_no_mega_without_ring_or_matching_stone(self):
        for name in ['no-ring', 'wrong-stone']:
            with self.subTest(case=name):
                native = report(name)
                self.assertTrue(native['passed'])
                self.assertEqual(native['rom_sha256'], report('catalog')['rom_sha256'])
                self.assertEqual(native['fixture_met_level'], 5)
                self.assertFalse(native['transformed'])
                self.assertFalse(native['rendered_at_action_menu'])
                self.assertTrue(native['real_brock_battle'])
                self.assertTrue(native['restored_base_species'])


    def test_all_enabled_battle_pictures_decode_without_buffer_overrun(self):
        codec = report('sprite-codec')
        self.assertTrue(codec['passed'])
        self.assertEqual(codec['rom_sha256'], report('catalog')['rom_sha256'])
        self.assertEqual(codec['species'], 1571)
        self.assertEqual(codec['pictures'], len(codec['checks']))
        self.assertEqual(codec['pictures'], 3323)
        self.assertTrue(codec['native_decoder_matches_original_pixels'])
        self.assertTrue(codec['buffer_bounds_verified'])
        self.assertFalse(codec['all_battle_animations_validated'])
        assets = {}
        for check in codec['checks']:
            assets.setdefault(check['species'], set()).add(check['asset'])
            self.assertGreater(check['bytes'], 0)
            self.assertEqual(len(check['sha256']), 64)
        self.assertEqual(len(assets), codec['species'])
        for kinds in assets.values():
            self.assertTrue({'front', 'back'} <= kinds)
        for link in report('catalog')['links']:
            self.assertIn(link['target_id'], assets)

    def test_art_assets_match_the_pinned_upstream_manifest(self):
        import hashlib
        directory = ROOT / 'mods/hoenn/assets/mega-garchomp-z'
        manifest = json.loads((directory / 'provenance.json').read_text())
        for name, digest in manifest['files'].items():
            data = (directory / name).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), digest['sha256'])
            blob = b'blob ' + str(len(data)).encode() + b'\0' + data
            self.assertEqual(hashlib.sha1(blob).hexdigest(), digest['git_blob'])

    def test_one_mega_per_battle_survives_switch_and_faint(self):
        for name in ['mega-switch', 'mega-faint']:
            native = report(name)
            self.assertTrue(native['passed'])
            self.assertEqual(native['rom_sha256'], report('catalog')['rom_sha256'])
            for check in ['native_party_menu', 'real_switch', 'second_mega_blocked',
                          'original_species_restored']:
                self.assertTrue(native[check], check)
        self.assertTrue(report('mega-faint')['fainted_after_transformation'])

    def test_ash_form_survives_switch_and_reverts_after_faint_battle(self):
        for name in ['ash-switch', 'ash-faint']:
            native = report(name)
            self.assertTrue(native['passed'])
            self.assertEqual(native['rom_sha256'], report('catalog')['rom_sha256'])
            for check in ['native_party_menu', 'real_switch', 'original_species_restored']:
                self.assertTrue(native[check], check)
        self.assertTrue(report('ash-switch')['ash_persists_after_return'])
        self.assertTrue(report('ash-faint')['fainted_after_transformation'])

    def test_mission_gates_cover_every_badge_subset_without_cross_region_bypass(self):
        native = report('campaign-matrix')
        self.assertTrue(native['passed'])
        self.assertEqual(native['rom_sha256'], report('catalog')['rom_sha256'])
        self.assertEqual(native['gate_cases'], 15 * 256)
        self.assertEqual(native['permission_cases'], 36)
        for check in native['checks']:
            self.assertEqual(check['badge_subsets'], 256)
        for check in ['native_gate_decisions', 'all_regional_badge_subsets',
                      'other_region_badges_cannot_bypass_gate',
                      'giovanni_and_space_center_required', 'flags_are_initial_state_fixtures']:
            self.assertTrue(native[check], check)
        self.assertFalse(native['full_campaign_playthrough'])
        thresholds = {c['scenario']: c['threshold'] for c in native['checks']}
        self.assertEqual(thresholds['silph'], 6)
        self.assertEqual(thresholds['space_center'], 7)
        self.assertEqual(thresholds['archie'], 7)
        for name in ['pewter', 'vermilion', 'rock_tunnel', 'western_sea', 'kanto_incursions', 'hoenn_rocket']:
            self.assertEqual(thresholds[name], 4)

    def test_hidden_ability_regressions_use_the_final_art_candidate(self):
        for name, expected in [('abilities-slot-0', False), ('abilities-slot-1', False),
                               ('abilities-slot-2', True), ('abilities-event', True),
                               ('abilities-froakie', False)]:
            native = report(name)
            self.assertTrue(native['passed'])
            self.assertEqual(native['rom_sha256'], report('catalog')['rom_sha256'])
            self.assertEqual(native['ash_after_ko'], expected)
            self.assertEqual(native['fixture_met_level'], 5)
            self.assertTrue(native['native_save_preserves_slot'])
            self.assertTrue(native['normal_species_and_ability_restored'])
        hidden = report('abilities-slot-2')
        self.assertEqual(hidden['wild_samples'], 200)
        self.assertEqual(hidden['inheritance_samples'], 100)

    def test_native_normal_and_shiny_palettes_cover_every_enabled_species(self):
        palettes = report('palette-loader')
        self.assertTrue(palettes['passed'])
        self.assertEqual(palettes['rom_sha256'], report('catalog')['rom_sha256'])
        self.assertEqual(palettes['species'], report('sprite-codec')['species'])
        self.assertEqual(palettes['palettes'], len(palettes['checks']))
        for check in ['native_palette_loader_matches_build', 'adjacent_colors_preserved',
                      'all_picture_indices_fit_palettes']:
            self.assertTrue(palettes[check], check)
        assets = {}
        for check in palettes['checks']:
            assets.setdefault(check['species'], set()).add(check['asset'])
            self.assertLess(check['highest_picture_color'], check['original_colors'])
        for kinds in assets.values():
            self.assertTrue({'normal', 'shiny'} <= kinds)
        self.assertFalse(palettes['all_battle_animations_validated'])

if __name__ == '__main__':
    unittest.main()
