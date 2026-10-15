"""Require actual new Surf crossings and a moving native MAP cursor."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'mods/hoenn/world-route-chart-validation'


class WorldRouteChart(unittest.TestCase):
    def test_current_rom_crosses_every_new_passage_and_reopens_map_at_real_position(self):
        release=json.loads((ROOT/'mods/hoenn/versions/versions.json').read_text())
        r=json.loads((OUT/'world-route-chart.json').read_text())
        self.assertTrue(r['passed'])
        self.assertEqual(r['rom_sha256'],release['parent_rom_sha256'])
        self.assertTrue(r['compiled_zoom_pixels_match_source'])
        self.assertTrue(r['cursor_tracks_controller_movement_on_reopen'])
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
        self.assertFalse(index['labels_printed_on_map'])
        self.assertEqual(index['routes'],layout['routes'])
        self.assertEqual(proof['actual_connection_edges'],len(layout['routes']))
        self.assertTrue(proof['all_edges_match_native_map_connections'])
        self.assertGreaterEqual(len(layout['green_rectifications']),8)
        for edge in layout['routes']:
            self.assertTrue(edge['actual_connection'])
            self.assertTrue(all(a[0]==b[0] or a[1]==b[1] for a,b in zip(edge['polyline'],edge['polyline'][1:])))
        self.assertEqual(len({p['map'] for p in layout['passages']}),3)
        definitions={d['map']:d for d in index['definitions']}
        for passage in layout['passages']:
            self.assertEqual(definitions[passage['map']]['name'],passage['name'])
            self.assertEqual(definitions[passage['map']]['definition'],passage['definition'])


if __name__=='__main__':unittest.main()
