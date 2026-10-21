"""Require physical proof for the three terminals at the user's exact bounds."""
import hashlib,json,unittest
from pathlib import Path
from verify_versions import verify
from verify_three_harbor_update import BOXES
from verify_fuchsia_update import previous_release

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'mods/hoenn/three-harbor-validation'


class ThreeHarborTerminals(unittest.TestCase):
    def test_every_edition_enters_and_sails_from_all_three_terminals(self):
        release=verify(ROOT/'mods/hoenn/versions')
        while release.get('validation_scope') in ('sevii-integrated-piers','dewford-coast-safety','extra-gyms','ever-grande-market','dewford-competitive-shop','surf-review','annotated-world-links','island-harbors','sevii-harbors'):release=previous_release(release)
        self.assertEqual(release['validation_scope'],'three-harbor-terminals')
        cases=[('validation',release['parent_rom_sha256'])]
        cases += [(r['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba'),r['sha256']) for r in release['variants']]
        for name,sha in cases:
            r=json.loads((OUT/name/'three-harbors.json').read_text())
            self.assertTrue(r['passed']);self.assertEqual(r['rom_sha256'],sha)
            self.assertEqual({p['pid'] for p in r['ports']},set(BOXES))
            for p in r['ports']:
                self.assertEqual(p['terminal'],BOXES[p['pid']])
                self.assertTrue(p['controller_entry_and_exit'] and p['one_indoor_captain'])
                self.assertTrue(p['save_continue_inside'] and p['network_arrival_inside'])
                self.assertTrue(p['medium_boat_hull_blocked_over_water'] and p['inside_ship_hull_blocked_over_water'])
                self.assertEqual([t['destination'] for t in p['trips']],['JourneyPalletHarbor',p['interior']])

    def test_legacy_house_and_briney_service_remain_accessible(self):
        r=json.loads((OUT/'validation/three-harbors.json').read_text())
        cases={p['pid']:p for p in r['ports']}
        self.assertTrue(cases[19]['legacy_exit_preserved'])
        self.assertTrue(cases[12]['briney_local_service_preserved'])
        self.assertEqual(cases[12]['door'],[16,50])
        self.assertEqual(cases[21]['pier_extension'],[[x,y] for y in range(12,16) for x in (64,65)])
        self.assertTrue((OUT/'validation/Petalburg-Briney-exit.png').exists())

    def test_independent_replay_preserves_other_ports_and_shared_art(self):
        r=json.loads((OUT/'source.json').read_text())
        self.assertTrue(r['original_inputs_verified'] and r['idempotent'])
        self.assertFalse(r['differences']);self.assertGreater(r['unrelated_source_inputs_checked'],30000)
        self.assertTrue(r['atlas_unchanged'] and r['vermilion_and_pacifidlog_preserved'])
        self.assertTrue(r['all_other_ports_preserved'] and r['shared_art_pixel_identical'])
        self.assertGreaterEqual(len(r['compared_maps']),10)


if __name__=='__main__':unittest.main()
