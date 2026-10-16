"""Guard the requested Pallet geometry and bind physical proof to every ROM."""
import json
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'mods/hoenn/pallet-harbor-validation'


class PalletHarbor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layout = json.loads((OUT/'layout.json').read_text())
        cls.manifest = json.loads((ROOT/'mods/hoenn/versions/versions.json').read_text())

    def test_every_edition_has_fresh_controller_evidence(self):
        self.assertTrue(self.manifest['pallet_harbor_validated'])
        self.assertIn('pallet-harbor', self.manifest['integration_layers'])
        for row in self.manifest['variants']:
            edition = row['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba')
            report = json.loads((OUT/edition/'pallet-harbor.json').read_text())
            self.assertEqual(report['rom_sha256'], row['sha256'])
            self.assertTrue(report['passed'])
            for field in ['original_bridge_preserved', 'outside_boat_shifted_right',
                          'bridge_walked_without_surf', 'controller_entry_and_exit',
                          'ship_hull_blocked_over_water', 'interior_captain_interacted_physically',
                          'outside_captain_removed', 'bridges_joined_and_walked',
                          'complete_trees_checked', 'route21_surf_roundtrip',
                          'merged_bay_surfed', 'south_bridge_walked', 'eastern_corridor_walked',
                          'bridge_crossed_by_surf_below', 'upper_corner_corrected']:
                self.assertTrue(report[field], (edition, field))
            self.assertEqual(report['ship_sprite_size'], [96, 40])
            self.assertEqual(report['route21_atlas_seam_delta'], 0)
            self.assertEqual([t['destination'] for t in report['trips']],
                             ['JourneyLavenderHarbor', 'JourneyPalletHarbor'])

    def test_bridge_connection_boat_shift_and_network_id(self):
        self.assertEqual([[x,y] for x,y,_ in self.layout['preserved_bridge']],
                         [[x,y] for y in (17,18) for x in range(9,13)])
        self.assertEqual([self.layout['outside_boat'][k] for k in ('x','y')], [10,20])
        self.assertEqual(self.layout['boat_shift'], [1,0])
        self.assertEqual(self.layout['world_port_id'], 18)
        self.assertTrue(self.layout['bridge_unchanged'] and self.layout['outside_captain_removed'])
        self.assertEqual(self.layout['bridge_join'], [[x,y] for y in (17,18) for x in (13,14)])
        self.assertEqual(self.layout['maximum_seam_delta'], 0)
        self.assertLessEqual(self.layout['maximum_neighbor_pixel_step'], 2)

    def test_water_above_is_reduced_and_grassy_divider_is_removed(self):
        # Three-times native rendering starts at tile (0,12).
        im = Image.open(ROOT/'docs/images/pallet-harbor/PalletTown_Frlg.png').convert('RGB')
        above = im.crop((720,240,1008,264))  # Upper half of (15..20,17).
        rim = im.crop((720,264,1008,288))
        merged = im.crop((528,432,624,624))  # (11..12,21..24), below the boat.
        self.assertTrue(all(g>b for r,g,b in above.getdata()), 'Extra water row above terminal')
        self.assertTrue(any(r>g and r>b for r,g,b in rim.getdata()), 'Missing upper cliff rim')
        self.assertTrue(all(b>g for r,g,b in merged.getdata()), 'Land still separates the two seas')

    def test_independent_layer_reproduction_matches_outputs(self):
        proof = json.loads((OUT/'validation/reproduction.json').read_text())
        self.assertTrue(proof['passed'] and proof['original_inputs_verified'] and proof['idempotent'])
        self.assertEqual(proof['prepared_sha256'], self.layout['prepared_sha256'])
        self.assertEqual(set(proof['byte_identical_outputs']), set(self.layout['prepared_sha256']))
        common = json.loads((OUT/'validation/pallet-harbor.json').read_text())
        self.assertEqual(common['rom_sha256'], self.manifest['parent_rom_sha256'])

    def test_south_access_has_visible_wood_matching_the_quay(self):
        im = Image.open(ROOT/'docs/images/pallet-harbor/PalletTown_Frlg.png').convert('RGB')
        deck = im.crop((18*48,13*48,19*48,14*48))
        quay = im.crop((19*48,12*48,20*48,13*48))
        self.assertEqual(deck.tobytes(), quay.tobytes(), 'South access is invisible or does not match the wooden quay')


if __name__ == '__main__':
    unittest.main()
