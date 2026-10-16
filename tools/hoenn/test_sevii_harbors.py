"""Guard seven working terminals and current, unobstructed Sevii Surf travel."""
import json,unittest
from pathlib import Path
from PIL import Image
from verify_versions import verify
from verify_sevii_harbor_update import ISLANDS

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'mods/hoenn/sevii-harbors-validation'


class SeviiHarbors(unittest.TestCase):
    def test_all_seven_terminals_and_surf_roundtrips_are_current_in_every_edition(self):
        release=verify(ROOT/'mods/hoenn/versions')
        self.assertEqual(release['validation_scope'],'sevii-harbors')
        cases=[('validation',release['parent_rom_sha256'])]
        cases += [(r['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba'),r['sha256']) for r in release['variants']]
        for edition,sha in cases:
            port=json.loads((OUT/edition/'sevii-harbors.json').read_text())
            surf=json.loads((OUT/edition/'sevii-surf-connections.json').read_text())
            world=json.loads((OUT/edition/'sevii-world-surf.json').read_text())
            self.assertEqual(port['rom_sha256'],sha);self.assertEqual(surf['rom_sha256'],sha)
            self.assertEqual(world['rom_sha256'],sha)
            self.assertEqual({t['region'] for t in world['trips']},{'KANTO','HOENN'})
            self.assertTrue(all(t['controller_roundtrip'] and t['no_midroute_warps_or_coordinate_writes'] for t in world['trips']))
            self.assertTrue(port['cinnabar_surf_under_pier_roundtrip'] and port['cinnabar_quay_walked_above'])
            self.assertEqual({p['island'] for p in port['ports']},ISLANDS)
            self.assertEqual(len(surf['islands']),7);self.assertEqual(len(surf['seams']),14)
            self.assertEqual(surf['active_screen_fade_frames'],0)
            for p in port['ports']:
                self.assertTrue(p['controller_entry_and_exit'] and p['south_surf_lane_crossed'])
                self.assertTrue(p['save_continue_inside'] and p['one_indoor_captain'] and p['old_lodge_exit_preserved'])
                self.assertEqual([t['destination'] for t in p['trips']],['JourneyPalletHarbor',p['interior']])

    def test_lanes_original_boats_atlas_and_other_ports_are_preserved(self):
        r=json.loads((OUT/'source.json').read_text());layout=json.loads((OUT/'layout.json').read_text())
        self.assertTrue(r['original_inputs_verified'] and r['idempotent']);self.assertFalse(r['differences'])
        self.assertGreater(r['unrelated_source_inputs_checked'],30000)
        for field in ['south_row_byte_identical','west_two_columns_byte_identical',
                      'surface_connections_and_dimensions_preserved','original_small_boat_graphics_preserved',
                      'varied_opposite_berths','boats_clear_of_upper_quay','bridge_extensions_three_tiles','old_boat_gap_closed',
                      'native_ferry_arrivals_preserved','all_other_port_placements_preserved',
                      'cinnabar_quay_art_pixel_identical','atlas_unchanged','shared_art_pixel_identical']:
            self.assertTrue(r[field],field)
        self.assertEqual(layout['south_water_lane'],[0,12,17,1]);self.assertEqual(layout['west_water_lane'],[0,0,2,13])
        self.assertEqual(layout['bridge_behavior'],0x71)
        self.assertEqual({p['pid'] for p in layout['ports']},set(range(2,9)))
        self.assertEqual(len({(p['pier_x'],p['outside_boat']['x'],p['medium_boat']['x'],p['medium_boat']['y']) for p in layout['ports']}),7)

    def test_sand_backed_roof_and_ship_are_shared_in_all_seven_ports(self):
        reference=Image.open(ROOT/'docs/images/lavender-harbor/JourneyRoute12Shipyard.png').convert('RGB').crop((8*48,11*48,15*48,17*48))
        inside=Image.open(ROOT/'docs/images/pallet-harbor/JourneyPalletHarbor.png').convert('RGB')
        layout=json.loads((OUT/'layout.json').read_text())
        for p in layout['ports']:
            exterior=Image.open(ROOT/f'docs/images/sevii-harbors/{p["exterior"]}.png').convert('RGB')
            room=Image.open(ROOT/f'docs/images/sevii-harbors/{p["interior"]}.png').convert('RGB')
            # Native Sevii palettes quantize the facade; the roof and its
            # exposed sand must match exactly, without blue water backing.
            self.assertEqual(exterior.crop((10*48,0,17*48,4*48)).tobytes(),
                             reference.crop((0,0,7*48,4*48)).tobytes(),p['island'])
            self.assertEqual(room.tobytes(),inside.tobytes(),p['island'])
            plank=exterior.crop((9*48,3*48,10*48,4*48)).tobytes()
            for x in (7,8,9):
                for y in range(3,7):
                    self.assertEqual(exterior.crop((x*48,y*48,(x+1)*48,(y+1)*48)).tobytes(),plank,
                                     (p['island'],x,y,'Visible end post at the upper bridge join'))


if __name__=='__main__':unittest.main()
