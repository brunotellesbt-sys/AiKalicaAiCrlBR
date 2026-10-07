"""Offline integrity checks for the map preview, independent of the ROM build."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class AtlasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'web/world-map.json').read_text())
        cls.points = {p['id']: p for p in cls.data['points']}

    def test_native_map_images_match_provenance(self):
        self.assertEqual(len(self.data['panels']), 5)
        for name, digest in self.data['output_sha256'].items():
            image = (ROOT / 'web/atlas' / name).read_bytes()
            self.assertEqual(image[:8], b'\x89PNG\r\n\x1a\n')
            self.assertEqual(hashlib.sha256(image).hexdigest(), digest)

    def test_all_places_have_valid_panel_coordinates(self):
        panels = {p['id']: p for p in self.data['panels']}
        self.assertEqual(len(self.points), 38)
        self.assertEqual(len(self.points), len(self.data['points']))
        for p in self.points.values():
            panel = panels[p['panel']]
            self.assertLessEqual(panel['x'], p['x'])
            self.assertLessEqual(p['x'], panel['x'] + panel['width'])
            self.assertLessEqual(panel['y'], p['y'])
            self.assertLessEqual(p['y'], panel['y'] + panel['height'])

    def test_surf_links_match_shipped_map_graph(self):
        routes = json.loads((ROOT / 'mods/sea-routes/routes.json').read_text())['routes']
        ports = sorted((p for p in self.points.values() if p['port_index'] is not None), key=lambda p: p['port_index'])
        self.assertEqual([p['map'] for p in ports], [r['port'] for r in routes])
        links = [l for l in self.data['links'] if l['status'] == 'playable']
        self.assertEqual(len(links), len(routes) - 1)
        for i, link in enumerate(links):
            self.assertEqual((link['source'], link['target']), (ports[i]['id'], ports[i + 1]['id']))
            self.assertEqual(link['maps'], [routes[i]['name'], routes[i + 1]['name']])
            self.assertTrue(any(c['map'] == 'MAP_JOURNEY_SEA_ROUTE_' + f'{i + 1:02d}' and c['direction'] == 'right' for c in routes[i]['connections']))
        manifest = json.loads((ROOT / 'mods/sea-routes/manifest.json').read_text())
        self.assertEqual(self.data['sea_rom_sha256'], manifest['target_sha256'])

    def test_hoenn_is_explicitly_pending(self):
        self.assertFalse(self.data['hoenn_story_integrated'])
        hoenn = [p for p in self.points.values() if p['panel'] == 'hoenn']
        self.assertEqual(len(hoenn), 17)
        self.assertTrue(all(p['status'] == 'planned' for p in hoenn))
        for link in self.data['links']:
            self.assertIn(link['source'], self.points); self.assertIn(link['target'], self.points)
            if 'hoenn' in [self.points[link[k]]['panel'] for k in ['source', 'target']]:
                self.assertEqual(link['status'], 'planned')
        pending = [l for l in self.data['links'] if l['status'] == 'planned']
        self.assertEqual({l['mode'] for l in pending}, {'Surf', 'Barco com ticket'})
        surf = next(l for l in pending if l['mode'] == 'Surf')
        self.assertEqual((surf['source'], surf['target']), ('MAPSEC_ROUTE_21', 'MAPSEC_ROUTE_127'))

    def test_recorded_browser_validation_matches_atlas(self):
        report = json.loads((ROOT / 'mods/hoenn/validation/atlas-browser.json').read_text())
        self.assertTrue(report['passed'])
        self.assertEqual(report['page_errors'], [])
        self.assertEqual(len(report['checks']), 7)
        self.assertEqual(report['data_sha256'], hashlib.sha256((ROOT / 'web/world-map.json').read_bytes()).hexdigest())
        self.assertEqual(self.data['generator_sha256'], hashlib.sha256((ROOT / 'tools/hoenn/world_atlas.py').read_bytes()).hexdigest())


if __name__ == '__main__': unittest.main()
