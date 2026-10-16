"""Bind Lavender's replacement terminal to its artwork and native ROM evidence."""
import json
import unittest
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'mods/hoenn/lavender-harbor-validation'


class LavenderHarbor(unittest.TestCase):
    def test_terminal_keeps_pallet_artwork_with_sand_behind_roof(self):
        pallet = Image.open(ROOT/'docs/images/pallet-harbor/PalletTown_Frlg.png').convert('RGB')
        lavender = Image.open(ROOT/'docs/images/lavender-harbor/JourneyRoute12Shipyard.png').convert('RGB')
        old = pallet.crop((15*48,6*48,22*48,12*48))
        new = lavender.crop((8*48,11*48,15*48,17*48))
        # Only exposed blue roof backing changes; the building stays intact.
        for i,(a,b) in enumerate(zip(old.getdata(),new.getdata())):
            if i//old.width<24 and a in {(74,123,222),(74,148,222)}:
                self.assertGreater(b[0],b[2])
            else:
                self.assertEqual(a,b)
        self.assertEqual((ROOT/'docs/images/pallet-harbor/JourneyPalletHarbor.png').read_bytes(),
                         (ROOT/'docs/images/lavender-harbor/JourneyLavenderHarbor.png').read_bytes())

    def test_replacement_stays_inside_central_platform(self):
        layout = json.loads((OUT/'layout.json').read_text())
        self.assertTrue(all(8<=x<16 and 35<=y<41 for x,y in layout['changed_terrain']))
        self.assertEqual(layout['terminal'],[8,35,7,6])
        self.assertEqual(layout['terminal_shift_from_first_preview'],[-2,2])
        self.assertEqual(layout['world_port_id'],0)
        self.assertEqual(layout['door'],[11,40])
        self.assertEqual(layout['ship_sprite_size'],[96,40])
        self.assertEqual(layout['roof_background'],'native_sand')
        self.assertTrue(layout['remaining_grass_replaced_with_sand'])
        for field in ['outside_captain_removed','existing_piers_and_boats_preserved',
                      'surface_connections_preserved','old_lodge_exit_preserved']:
            self.assertTrue(layout[field])

    def test_every_edition_walks_doors_and_sails_to_pallet_and_back(self):
        release = json.loads((ROOT/'mods/hoenn/versions/versions.json').read_text())
        self.assertTrue(release['lavender_harbor_validated'])
        self.assertEqual(release['integration_layers'][-1],'lavender-harbor')
        cases=[('validation',release['parent_rom_sha256'])]
        cases += [(r['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba'),r['sha256'])
                  for r in release['variants']]
        for edition,sha in cases:
            report=json.loads((OUT/edition/'lavender-harbor.json').read_text())
            self.assertTrue(report['passed'])
            self.assertEqual(report['rom_sha256'],sha)
            for field in ['controller_entry_and_exit','captain_interacted_physically',
                          'outside_captain_removed','one_indoor_captain','ship_hull_blocked_over_water',
                          'network_arrivals_inside_terminal','save_continue_inside_terminal','returned_to_original_pier',
                          'old_lodge_exit_walked']:
                self.assertTrue(report[field],(edition,field))
            self.assertEqual([t['destination'] for t in report['trips']],
                             ['JourneyPalletHarbor','JourneyLavenderHarbor'])


if __name__ == '__main__':
    unittest.main()
