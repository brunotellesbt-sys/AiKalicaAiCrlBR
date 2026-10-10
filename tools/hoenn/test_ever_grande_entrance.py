"""Evidence for the reef opening and the actual Vermilion ocean endpoint."""
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'mods/hoenn/ever-grande-entrance-validation'

def read(name):
    return json.loads((DIR / name).read_text())

class EverGrandeEntrance(unittest.TestCase):
    def test_only_the_lower_reef_changes_and_layer_replays(self):
        p = read('preparation/preparation.json')
        r = read('preparation/reproduction.json')
        self.assertTrue(r['passed'] and r['deterministic_replay'] and r['idempotent'])
        self.assertEqual(len(p['prepared_sha256']), 3)
        self.assertIn('data/layouts/EverGrandeCity/map.bin', p['prepared_sha256'])
        self.assertEqual(len(p['changed_tiles']), 31)
        self.assertTrue(all(t['after'] == 0x1170 and t['y'] >= 70 and 22 <= t['x'] < 32 for t in p['changed_tiles']))
        self.assertTrue(p['waterfall_and_upper_pool_preserved'] and p['map_events_and_league_gates_preserved'])
    def test_controller_roundtrip_reaches_waterfall_base_from_east(self):
        r = read('native/ever-grande-entrance.json')
        self.assertTrue(r['passed'] and r['continuous_roundtrip'] and r['no_midroute_warps'])
        self.assertTrue(r['save_continue_at_waterfall_base'])
        self.assertEqual(r['rom_sha256'], read('preparation/reproduction.json')['rom_sha256'])
        self.assertIn({'map': 'EverGrandeCity', 'position': [20, 68]}, r['legs'])
        self.assertIn({'map': 'VermilionCity_Frlg', 'position': [20, 20]}, r['legs'])
        self.assertIn({'map': 'JourneyFuchsiaSea', 'position': [10, 10]}, r['legs'])
        self.assertTrue(any(t['source'][0] == 'JourneyEverGrandeBackSouthSea' and t['destination'][0] == 'EverGrandeCity' for t in r['transitions']))
        self.assertEqual(r['legs'][-1], {'map': 'FuchsiaCity_Frlg', 'position': [20, 20]})
        self.assertFalse(r['full_campaign_playthrough'])
    def test_actual_map_places_vermilion_directly_above_the_ocean(self):
        p = json.loads((ROOT / 'mods/hoenn/ever-grande-entrance-gallery/metadata.json').read_text())
        rects = {r['map']: r for r in p['rectangles']}
        a, b = rects['VermilionCity_Frlg'], rects['JourneyWorldSea00']
        self.assertEqual(a['y'] + a['height'], b['y'])
        self.assertEqual(a['x'], b['x'])
        self.assertTrue(p['source_metatiles'] and p['includes_vermilion'])
        self.assertEqual(p['rom_sha256'], read('preparation/reproduction.json')['rom_sha256'])
        self.assertFalse(p['full_world_map'])
        f, route, canal = rects['FuchsiaCity_Frlg'], rects['Route19_Frlg'], rects['JourneyFuchsiaSea']
        self.assertEqual(f['y'] + f['height'], route['y'])
        self.assertEqual(route['x'] + route['width'], canal['x'])
        self.assertEqual(route['y'] + 40, canal['y'])
        self.assertEqual(canal['y'] + canal['height'], 0)
        for a in rects.values():
            for b in rects.values():
                if a['map'] >= b['map']: continue
                self.assertTrue(min(a['x']+a['width'], b['x']+b['width']) <= max(a['x'], b['x']) or min(a['y']+a['height'], b['y']+b['height']) <= max(a['y'], b['y']), (a,b))

if __name__ == '__main__':
    unittest.main()
