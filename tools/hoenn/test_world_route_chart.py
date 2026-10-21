"""Require actual new Surf crossings and a moving native MAP cursor."""
from verify_fuchsia_update import harbor_baseline
import json
import unittest
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'mods/hoenn/world-route-chart-validation'


class WorldRouteChart(unittest.TestCase):
    def test_current_rom_crosses_every_new_passage_and_reopens_map_at_real_position(self):
        release=json.loads((ROOT/'mods/hoenn/versions/versions.json').read_text())
        release=harbor_baseline(release)
        r=json.loads((OUT/'world-route-chart.json').read_text())
        self.assertTrue(r['passed'])
        self.assertEqual(r['rom_sha256'],release['parent_rom_sha256'])
        self.assertTrue(r['compiled_zoom_pixels_match_source'])
        self.assertTrue(r['cursor_tracks_controller_movement_on_reopen'])
        self.assertTrue(r['cursor_stays_within_authored_corridors'])
        self.assertEqual(r['new_passage_count'],3)
        for p in r['new_surf_passages']:
            self.assertTrue(p['no_midroute_coordinate_writes'])
            self.assertGreater(len({tuple(s['marker']) for s in p['cursor_samples'] if s['map']==p['map']}),1)
            self.assertTrue(all(s['cursor_matches_compiled_tile_position'] and s['return_preserves_position'] for s in p['cursor_samples']))
            self.assertTrue(all(c['outbound_and_return'] and c['surf_preserved'] for c in p['controller_crossings']))

    def test_chart_has_no_printed_names_and_all_links_are_real_and_orthogonal(self):
        layout=json.loads((OUT/'layout.json').read_text())
        index=json.loads((ROOT/'docs/images/navigation/world-routes.json').read_text())
        proof=json.loads((OUT/'world-route-chart.json').read_text())
        release=json.loads((ROOT/'mods/hoenn/versions/versions.json').read_text())
        while release.get('validation_scope') in ['sevii-integrated-piers','dewford-coast-safety','extra-gyms','ever-grande-market','dewford-competitive-shop']:
            from verify_fuchsia_update import previous_release
            release=previous_release(release)
        if release.get('validation_scope')=='annotated-world-links':
            layout=json.loads((ROOT/'mods/hoenn/continuous-ocean-validation/layout/annotated-world-links.json').read_text())['chart']
            proof=json.loads((ROOT/'mods/hoenn/continuous-ocean-validation/chart/world-route-chart.json').read_text())
        if release.get('validation_scope')=='surf-review':
            layout=json.loads((ROOT/'mods/hoenn/surf-review-validation/source.json').read_text())['chart']
            proof=json.loads((ROOT/'mods/hoenn/surf-review-validation/native/surf-review.json').read_text())
        self.assertFalse(index['labels_printed_on_map'])
        self.assertEqual(index['routes'],layout['routes'])
        self.assertEqual(proof['actual_connection_edges'],len(layout['routes']))
        self.assertTrue(proof['all_edges_match_native_map_connections'])
        self.assertGreaterEqual(len(layout['green_rectifications']),8)
        for edge in layout['routes']:
            self.assertTrue(edge['actual_connection'])
            self.assertTrue(all(a[0]==b[0] or a[1]==b[1] for a,b in zip(edge['polyline'],edge['polyline'][1:])))
        self.assertEqual(len({p['map'] for p in layout['passages']}),10 if release.get('validation_scope') in ['annotated-world-links','surf-review'] else 3)
        definitions={d['map']:d for d in index['definitions']}
        for passage in layout['passages']:
            self.assertEqual(definitions[passage['map']]['name'],passage['name'])
            self.assertEqual(definitions[passage['map']]['definition'],passage['definition'])

    def test_routes_are_visibly_drawn_at_the_red_annotations(self):
        im=Image.open(ROOT/'docs/images/navigation/world-map-current.png').convert('RGB')
        proof=json.loads((OUT/'world-route-chart.json').read_text())
        expected=[(101,65),(101,69),(101,73),(175,43),(181,46),(190,50),
                  (176,101),(176,106),(185,109),(168,105)]
        self.assertTrue(proof['authored_corridors_visible'])
        self.assertEqual(proof['visible_route_samples'],[list(p) for p in expected])
        for x,y in expected:
            self.assertEqual(im.getpixel((6*x+3,6*y+3)),(48,104,176),(x,y,'Route missing from annotated location'))


if __name__=='__main__':unittest.main()
