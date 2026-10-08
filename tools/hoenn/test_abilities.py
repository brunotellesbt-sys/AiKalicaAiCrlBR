"""Recorded native evidence for the ability candidate, separate from the map baseline."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / 'mods/hoenn/abilities-validation'


def report(name):
    return json.loads((VALIDATION / (name + '.json')).read_text())


class AbilityRequirements(unittest.TestCase):
    def test_overlay_replays_from_validated_map_baseline(self):
        reproduction = report('reproduction')
        baseline = json.loads((ROOT / 'mods/hoenn/integration-validation/connected-world.json').read_text())
        self.assertTrue(reproduction['passed'])
        self.assertTrue(reproduction['deterministic_replay'])
        self.assertTrue(reproduction['idempotent'])
        self.assertEqual(reproduction['baseline_rom_sha256'], baseline['rom_sha256'])
        prep = report('preparation')
        self.assertEqual(prep['battle_bond_generation'], 7)
        self.assertEqual(prep['wild_hidden_percent'], 5)
        self.assertEqual(prep['hidden_slot'], 2)
        self.assertTrue(prep['no_gift_or_trainer_ability_roll'])

    def test_hidden_slot_transforms_but_normal_slots_do_not(self):
        candidate = report('reproduction')['rom_sha256']
        for slot in range(3):
            with self.subTest(slot=slot):
                native = report('abilities-slot-' + str(slot))
                self.assertTrue(native['passed'])
                self.assertEqual(native['rom_sha256'], candidate)
                self.assertEqual(native['ability_slot'], slot)
                self.assertEqual(native['ash_after_ko'], slot == 2)
                self.assertTrue(native['real_brock_battle'])
                self.assertTrue(native['normal_species_and_ability_restored'])
                self.assertTrue(native['native_save_preserves_slot'])
        native = report('abilities-slot-2')
        self.assertTrue(native['ash_rendered_at_action_menu'])
        self.assertEqual(native['wild_samples'], 200)
        self.assertGreater(native['wild_hidden_observed'], 0)
        self.assertLess(native['wild_hidden_observed'], native['wild_samples'])
        self.assertEqual(native['inheritance_samples'], 100)
        self.assertGreater(native['hidden_inherited'], 0)
        self.assertLess(native['hidden_inherited'], native['inheritance_samples'])

    def test_event_form_preserved_and_pre_evolution_cannot_transform(self):
        candidate = report('reproduction')['rom_sha256']
        for name, transforms in [('abilities-event', True), ('abilities-froakie', False)]:
            with self.subTest(name=name):
                native = report(name)
                self.assertTrue(native['passed'])
                self.assertEqual(native['rom_sha256'], candidate)
                self.assertEqual(native['ash_after_ko'], transforms)
                self.assertTrue(native['normal_species_and_ability_restored'])
                self.assertTrue(native['native_save_preserves_slot'])

    def test_special_capture_survives_ability_migration(self):
        capture = report('sanctuary-capture')
        self.assertTrue(capture['passed'])
        self.assertEqual(capture['rom_sha256'], report('reproduction')['rom_sha256'])
        for key in ['locked_with_15_badges', 'unlocked_with_16_before_leagues',
                    'real_escape_and_retry', 'real_master_ball_capture',
                    'native_flash_save_restores_catch_flag']:
            self.assertTrue(capture[key], key)


if __name__ == '__main__':
    unittest.main()
