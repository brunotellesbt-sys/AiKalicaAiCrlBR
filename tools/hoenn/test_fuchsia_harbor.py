"""Bind the new Fuchsia terminal and its physical validation to shipped ROMs."""
import hashlib
import json
import unittest
from pathlib import Path
from verify_versions import verify
from verify_fuchsia_update import previous_release

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'mods/hoenn/fuchsia-harbor-validation'


class FuchsiaHarbor(unittest.TestCase):
    def test_every_edition_walks_the_quay_and_uses_the_indoor_captain(self):
        release=verify(ROOT/'mods/hoenn/versions')
        while release.get('validation_scope') in ('ever-grande-market','surf-review','annotated-world-links','island-harbors','sevii-harbors','three-harbor-terminals'):release=previous_release(release)
        self.assertEqual(release['validation_scope'],'fuchsia-harbor')
        targets=[('validation',release['parent_rom_sha256'])]
        targets += [(r['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba'),r['sha256']) for r in release['variants']]
        for name,sha in targets:
            r=json.loads((OUT/name/'fuchsia-harbor.json').read_text())
            self.assertTrue(r['passed']);self.assertEqual(r['rom_sha256'],sha)
            self.assertTrue(r['quay_walked_without_surf'] and r['controller_entry_and_exit'])
            self.assertTrue(r['one_indoor_captain'] and r['outside_captain_removed'])
            self.assertTrue(r['medium_boat_hull_blocked_over_water'] and r['ship_hull_blocked_over_water'])
            self.assertTrue(r['save_continue_inside_terminal'] and r['old_lodge_exit_walked'])
            self.assertEqual([t['destination'] for t in r['trips']],['JourneyPalletHarbor','JourneyFuchsiaHarbor'])

    def test_only_fuchsia_changes_and_shared_city_art_stays_identical(self):
        r=json.loads((OUT/'source.json').read_text())
        self.assertTrue(r['original_inputs_verified'] and r['idempotent'])
        self.assertFalse(r['differences']);self.assertGreater(r['unrelated_source_inputs_checked'],30000)
        self.assertTrue(r['atlas_unchanged'] and r['other_ports_unchanged'])
        self.assertTrue(r['existing_trainers_preserved'] and r['other_fuchsia_maps_pixel_identical'])
        self.assertIn('FuchsiaCity_Frlg',r['compared_maps'])

    def test_old_reports_keep_their_original_rom_hashes(self):
        release=json.loads((ROOT/'mods/hoenn/versions/versions.json').read_text())
        while release.get('validation_scope') in ('ever-grande-market','surf-review','annotated-world-links','island-harbors','sevii-harbors','three-harbor-terminals'):release=previous_release(release)
        old=previous_release(release)
        self.assertNotEqual(old['parent_rom_sha256'],release['parent_rom_sha256'])
        self.assertEqual(old['integration_layers']+['fuchsia-harbor'],release['integration_layers'])
        for proof in old['proofs']:
            raw=(ROOT/'mods/hoenn/versions'/proof['file']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),proof['sha256'])


if __name__=='__main__':unittest.main()
