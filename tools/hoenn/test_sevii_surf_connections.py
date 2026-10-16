"""Require current, native seven-island Surf evidence in every shipped edition."""
from verify_fuchsia_update import harbor_baseline
import hashlib,json,unittest
from pathlib import Path
from verify_versions import verify
from verify_sevii_update import ISLANDS

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'mods/hoenn/sevii-surf-validation'

class SeviiSurfConnections(unittest.TestCase):
    def test_all_four_editions_reach_native_land_and_return_without_fades(self):
        release=harbor_baseline(verify(ROOT/'mods/hoenn/versions'));self.assertEqual(release['validation_scope'],'sevii-surf-connections')
        for row in release['variants']:
            name=row['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba');r=json.loads((OUT/name/'sevii-surf-connections.json').read_text())
            self.assertEqual(r['rom_sha256'],row['sha256']);self.assertEqual({i['map'] for i in r['islands']},ISLANDS)
            self.assertEqual(len(r['seams']),14);self.assertEqual(r['active_screen_fade_frames'],0)
            self.assertTrue(r['native_disembark'] and r['controller_roundtrip'] and r['save_continue_preserves_location'])

    def test_port_source_and_old_port_evidence_are_preserved(self):
        r=json.loads((OUT/'scope/sevii-source-scope.json').read_text())
        self.assertTrue(r['port_buildings_boats_captains_and_warps_unchanged'] and r['native_sevii_land_unchanged'])
        self.assertTrue(r['birth_and_navel_arrival_layout_preserved'])
        self.assertGreater(r['unchanged_source_inputs_checked'],30000)
        self.assertTrue(any('SootopolisCity' in p for p in r['preserved_port_paths']))
        self.assertTrue(any('PalletTown' in p for p in r['preserved_port_paths']))
        self.assertFalse(any('sootopolis' in p.lower() or 'pallet' in p.lower() for p in r['changed_source_files']))
        release=harbor_baseline(json.loads((ROOT/'mods/hoenn/versions/versions.json').read_text()));reference=release['previous_sootopolis_validation']
        self.assertFalse(reference['retested_on_current_rom'])
        self.assertEqual(hashlib.sha256((ROOT/reference['manifest']).read_bytes()).hexdigest(),reference['manifest_sha256'])

    def test_reproduced_source_matches_compiled_gps_scope(self):
        scope=json.loads((OUT/'scope/sevii-source-scope.json').read_text());replay=json.loads((OUT/'reproduction.json').read_text())
        self.assertEqual(set(scope['overlay_output_files']),set(replay['byte_identical_outputs']))
        self.assertEqual(replay['reproduced_layers'],scope['new_layers'])
        self.assertEqual(scope['maximum_seam_delta'],0);self.assertLessEqual(scope['maximum_neighbor_pixel_step'],2)
        self.assertTrue(replay['original_inputs_verified'] and replay['idempotent']);self.assertFalse(replay['differences'])

if __name__=='__main__':unittest.main()
