"""Bind all four final ROMs to their controller and reproduction evidence."""
import hashlib
import json
import unittest
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'mods/hoenn/sootopolis-harbor-validation'


class SootopolisHarbor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT/'mods/hoenn/versions/versions.json').read_text())
        cls.report = json.loads((OUT/'validation/sootopolis-harbor.json').read_text())

    def test_controller_evidence_belongs_to_this_rom(self):
        self.assertEqual(self.manifest['validation_scope'], 'sootopolis-harbor')
        self.assertTrue(self.manifest['validated'])
        for row in self.manifest['variants']:
            raw = (ROOT/'mods/hoenn/versions'/row['file']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row['sha256'])
            edition = row['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba')
            report = json.loads((OUT/edition/'sootopolis-harbor.json').read_text())
            self.assertEqual(report['rom_sha256'], row['sha256'])
            self.assertTrue(report['passed'])
            self.assertEqual(raw[0xBD], (-sum(raw[0xA0:0xBD])-0x19) & 255)
        self.assertEqual(self.report['rom_sha256'], self.manifest['parent_rom_sha256'])
        self.assertTrue(self.report['passed'])

    def test_both_layouts_have_real_walkable_access(self):
        for field in ['bridge_walked_without_surf', 'controller_entry_and_exit',
                      'crisis_layout_controller_access', 'returned_to_original_land',
                      'shore_end_uses_native_grass', 'extra_bottom_bridge_row_removed',
                      'bridge_end_stays_in_original_tile']:
            self.assertTrue(self.report[field], field)
        self.assertEqual(self.report['submarine_sprite_size'], [64, 64])
        self.assertTrue(self.report['submarine_hull_blocked_over_water'])

    def test_physical_captains_reach_the_existing_network_and_return(self):
        self.assertTrue(self.report['captain_interacted_physically'])
        self.assertEqual([t['destination'] for t in self.report['trips']],
                         ['SlateportCity_Harbor', 'JourneySootopolisHarbor'])
        self.assertTrue(all(t['native_animation_observations'] >= 5 for t in self.report['trips']))
        self.assertFalse(self.report['full_campaign_playthrough'])

    def test_shore_end_keeps_wood_and_grass_without_blue_water_pixels(self):
        # The published exterior is a 3x native rendering, cropped at (14,33).
        # Check both marked end cells (16,45) and (16,46), including foreground:
        # a grass background alone failed to remove the old baked-in water.
        image = Image.open(ROOT/'docs/images/sootopolis-harbor/SootopolisCity.png').convert('RGB')
        end = set(image.crop((96, 576, 144, 672)).getdata())
        grass = set(image.crop((336, 144, 384, 192)).getdata())
        self.assertTrue(end & grass, 'No native grass at the original bridge end')
        self.assertTrue(end - grass, 'The wooden end was removed')
        self.assertFalse([(r, g, b) for r, g, b in end if b >= r+10 and b >= g+8],
                         'Water or foam pixels remain beside the wooden end')

    def test_overlay_outputs_reproduce_and_repeat(self):
        proof = json.loads((OUT/'validation/reproduction.json').read_text())
        layer = json.loads((OUT/'layout.json').read_text())
        self.assertTrue(proof['passed'] and proof['original_inputs_verified'] and proof['idempotent'])
        self.assertEqual(set(proof['byte_identical_outputs']), set(layer['prepared_sha256']))
        self.assertEqual(layer['bridge_extended_left_tiles'], 1)
        self.assertTrue(layer['shore_end_water_pixels_removed'])
        self.assertIn([16, 45], layer['bridge'])


if __name__ == '__main__':
    unittest.main()
