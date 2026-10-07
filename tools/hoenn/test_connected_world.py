"""Offline checks for the integration candidate; do not certify its campaigns."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / 'mods/hoenn/integration-validation'


class ConnectedWorldTests(unittest.TestCase):
    def test_square_cartography_and_provenance(self):
        data = json.loads((ROOT / 'web/world-layout.json').read_text())
        self.assertEqual(data['width'], data['height'])
        self.assertEqual(data['cinnabar_south_endpoint'], 'MAPSEC_ROUTE_114')
        self.assertFalse(data['full_story_validated'])
        for path, key in [('web/world-layout.svg', 'svg_sha256'), ('tools/hoenn/world_layout.py', 'generator_sha256'),
                          ('web/world-map.json', 'atlas_sha256')]:
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), data[key])

    def test_eastern_rows_and_route131(self):
        east = json.loads((VALIDATION / 'eastern-ocean-preparation.json').read_text())
        self.assertEqual(east['cells'][:4], [[0, 0], [1, 0], [2, 0], [3, 0]])
        self.assertEqual(east['cells'][4:8], [[1, 1], [2, 1], [1, 2], [2, 2]])
        self.assertTrue(any(c['map'] == 'MAP_JOURNEYPACIFIDLOGSEA' and c['direction'] == 'down'
                            for c in east['connections']['Route131']))
        self.assertTrue(any(c['map'] == 'MAP_JOURNEYWORLDSEA06' and c['direction'] == 'right'
                            for c in east['connections']['JourneyPacifidlogSea']))

    def test_western_river_preserves_special_events(self):
        west = json.loads((VALIDATION / 'western-ocean-preparation.json').read_text())
        self.assertEqual(west['channels']['Route114'], [0, 12, 10, 24])
        self.assertTrue(west['superseded_crossing_disconnected'])
        # Both native Route114–Route115 land entrance and the new lake
        # entrance exist in distinct spans; all event hashes are retained.
        links = west['connections']['Route114']
        self.assertTrue(any(c['map'] == 'MAP_ROUTE115' and c['offset'] == 40 for c in links))
        self.assertTrue(any(c['map'] == 'MAP_JOURNEYWESTRIVER' and c['offset'] == 10 for c in links))
        self.assertEqual(set(west['preserved_event_sha256']['Route114']),
                         {'object_events', 'warp_events', 'coord_events', 'bg_events'})

    def test_story_and_badge_banks_have_no_id_collision(self):
        state = json.loads((VALIDATION / 'regional-state-preparation.json').read_text())
        allocated = [f['allocated'] for f in state['frlg_flags'].values()]
        self.assertEqual(len(allocated), 763)
        self.assertEqual(len(set(allocated)), len(allocated))
        self.assertTrue(all(3160 <= f < state['flags_count'] for f in allocated))
        self.assertTrue(set(allocated).isdisjoint(state['kanto_badges']))
        self.assertNotIn(state['kanto_champion'], allocated)
        self.assertTrue(state['requires_new_save'])

    def test_reproduction_and_runtime_checks_are_recorded(self):
        reproduction = json.loads((VALIDATION / 'world-reproduction.json').read_text())
        runtime = json.loads((VALIDATION / 'connected-world.json').read_text())
        self.assertTrue(reproduction['passed']); self.assertTrue(reproduction['idempotence'])
        self.assertEqual(reproduction['prepared_files'], 131)
        seams = [r for r in runtime['checks'] if r['check'] == 'physical_surf_seam']
        self.assertEqual(len(seams), 80)
        self.assertTrue(all(r['passed'] for r in runtime['checks']))
        self.assertTrue(any(r['check'] == 'regional_flags_and_native_save_roundtrip' for r in runtime['checks']))
        self.assertFalse(runtime['full_story_validated'])


if __name__ == '__main__': unittest.main()
