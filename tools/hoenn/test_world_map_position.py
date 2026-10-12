"""Check native projection evidence and preserve the approved atlas bytes."""
import hashlib,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'mods/hoenn/playable-validation/world-map-position'
class WorldMapPosition(unittest.TestCase):
 def test_real_mossdeep_crossing_and_every_shared_projection_edge(self):
  r=json.loads((OUT/'world-map-position.json').read_text())
  self.assertTrue(r['passed'] and r['short_trip_has_no_midroute_fixture_warp'] and r['recenter_uses_real_position'])
  self.assertEqual(r['rom_sha256'],hashlib.sha256((ROOT/'mods/hoenn/playable/Pokemon-Journey-World-Alpha-1.gba').read_bytes()).hexdigest())
  self.assertGreaterEqual(len(r['connections']),570)
  self.assertLessEqual(r['maximum_neighbor_pixel_step'],2)
  rom=(ROOT/'mods/hoenn/playable/Pokemon-Journey-World-Alpha-1.gba').read_bytes()
  at=r['compiled_anchor_offset'];size=r['compiled_anchor_bytes']
  self.assertEqual(hashlib.sha256(rom[at:at+size]).hexdigest(),r['compiled_anchor_sha256'])
  self.assertTrue(any('Harbor' in c['source'] for c in r['connections']))
  for c in r['connections']:
   self.assertTrue(c['samples'])
   self.assertGreaterEqual(len(c['samples']),1)
  trip=r['mossdeep_short_controller_trip']
  self.assertEqual(trip[1]['marker'],trip[2]['marker'])
  self.assertLessEqual(max(abs(p['marker'][1]-trip[0]['marker'][1]) for p in trip),1)
  self.assertGreaterEqual(trip[-1]['marker'][0],trip[0]['marker'][0])
  self.assertGreater(r['within_route_controller_progress'][-1]['marker'][0],trip[-1]['marker'][0])
 def test_position_layer_reproduces_and_repeats(self):
  r=json.loads((OUT/'reproduction.json').read_text())
  self.assertTrue(r['passed'] and r['original_input_hashes_checked'] and r['idempotent'])
  self.assertEqual(len(r['byte_identical_prepared_files']),4)
 def test_rendered_atlas_is_byte_identical_to_previous_release(self):
  r=json.loads((OUT/'atlas-preservation.json').read_text());rom=(ROOT/'mods/hoenn/playable/Pokemon-Journey-World-Alpha-1.gba').read_bytes()
  self.assertTrue(r['passed']);self.assertEqual(r['rom_sha256'],hashlib.sha256(rom).hexdigest())
  self.assertEqual(set(r['arrays']),{'sWorldPalette','sWorldTiles','sWorldTilemap'})
  for name,a in r['arrays'].items():
   observed=rom[a['current_offset']:a['current_offset']+a['bytes']]
   self.assertEqual(hashlib.sha256(observed).hexdigest(),a['sha256'],name)
if __name__=='__main__':unittest.main()
