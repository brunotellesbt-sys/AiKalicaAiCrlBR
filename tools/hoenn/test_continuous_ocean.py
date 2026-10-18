"""Require actual Surf, MAP and palette evidence for the yellow atlas requests."""
import json, unittest
from pathlib import Path
from verify_versions import verify

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'mods/hoenn/continuous-ocean-validation'


class ContinuousOcean(unittest.TestCase):
    def test_all_six_requests_have_real_connections_and_visible_map_pixels(self):
        r = json.loads((OUT / 'source.json').read_text())
        self.assertEqual(len(r['annotations']), 6)
        self.assertEqual(sum(a['new_map'] for a in r['annotations']), 5)
        self.assertTrue(r['original_inputs_verified'] and r['idempotent'])
        self.assertTrue(r['all_new_outer_limits_closed'] and r['all_native_events_preserved'])
        self.assertTrue(r['eight_animation_frames_identical'] and r['canonical_water_pixels_and_indices_identical'])
        self.assertEqual(r['gps']['maximum_seam_delta'], 0)
        self.assertLessEqual(r['gps']['maximum_neighbor_pixel_step'], 2)
        chart = json.loads((OUT / 'chart/world-route-chart.json').read_text())
        self.assertEqual(chart['new_passage_count'], 10)
        self.assertTrue(chart['compiled_atlas_pixels_match_source'] and chart['compiled_zoom_pixels_match_source'])
        self.assertTrue(chart['cursor_tracks_controller_movement_on_reopen'] and chart['cursor_stays_within_authored_corridors'])
        tested = {c['map'] for c in chart['new_surf_passages']}
        self.assertTrue(set(r['new_maps']) <= tested)
        coast = json.loads((OUT / 'connectivity/coast-connectivity.json').read_text())
        self.assertTrue(set(r['new_maps']) <= set(coast['reachable_maps']))

    def test_caves_beaches_and_pr90_ports_are_functional_on_the_combined_build(self):
        source=json.loads((OUT/'source.json').read_text())
        self.assertEqual(source['bounded_route_count'],65)
        self.assertTrue(source['pr90_static_art_pixel_identical'])
        caves=json.loads((OUT/'validation/coastal-cave-access.json').read_text())
        islands=json.loads((OUT/'validation/beach-trainers.json').read_text())
        links=json.loads((OUT/'validation/all-surf-links.json').read_text())
        for proof in [caves,islands,links]:
            self.assertTrue(proof['passed']);self.assertEqual(proof['rom_sha256'],source['rom_sha256'])
        self.assertEqual(len(caves['caves']),15)
        self.assertTrue(all(c['controller_entry_and_return'] for c in caves['caves']))
        self.assertEqual(len(islands['islands']),9)
        self.assertTrue(all(i['won_native_battle'] and i['private_defeated_flag'] for i in islands['islands']))
        self.assertTrue(islands['save_continue_retains_all_private_flags'])
        self.assertEqual(links['crossings'],2*len(links['links'])+len(links['native_current_links']))
        self.assertTrue(links['all_usable_outdoor_surf_connections_covered'])

    def test_every_shipped_edition_keeps_surf_colors_and_all_seven_islands_accessible(self):
        release = verify(ROOT / 'mods/hoenn/versions')
        while release['validation_scope'] in ['extra-gyms','ever-grande-market','dewford-competitive-shop']:
            from verify_fuchsia_update import previous_release
            release=previous_release(release)
        if release['validation_scope']=='surf-review':
            from verify_fuchsia_update import previous_release
            release=previous_release(release)
        self.assertEqual(release['validation_scope'], 'annotated-world-links')
        for row in release['variants']:
            folder = OUT / row['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba')
            seams = json.loads((folder / 'ocean-seams.json').read_text())
            surf = json.loads((folder / 'sevii-surf-connections.json').read_text())
            video = json.loads((folder / 'continuous-ocean.json').read_text())
            for proof in [seams, surf, video]:
                self.assertTrue(proof['passed']); self.assertEqual(proof['rom_sha256'], row['sha256'])
            self.assertEqual(seams['crossings'], 26)
            self.assertEqual(len(surf['islands']), 7)
            self.assertEqual(surf['active_screen_fade_frames'], 0)
            self.assertTrue(video['all_seam_ocean_colors_identical'])
            self.assertTrue(video['no_midroute_warps_or_coordinate_writes'] and video['native_surf_and_disembark'])
            moss=json.loads((folder/'mossdeep-harbor.json').read_text());dew=json.loads((folder/'dewford-island-harbor.json').read_text())
            self.assertEqual(moss['rom_sha256'],row['sha256']);self.assertEqual(dew['rom_sha256'],row['sha256'])
            self.assertTrue(moss['controller_entry_and_exit'] and dew['ship_channel_surfed'])


if __name__ == '__main__':
    unittest.main()
