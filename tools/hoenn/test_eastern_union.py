"""Guard compiled evidence against folded seams, lost ports and GBA buffer overflow."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
DIR=ROOT/'mods/hoenn/eastern-union-validation'
def read(path):return json.loads((DIR/path).read_text())
class EasternUnion(unittest.TestCase):
 def native(self,path):
  r=read(path);self.assertTrue(r['passed']);self.assertEqual(r['rom_sha256'],read('preparation/reproduction.json')['rom_sha256']);return r
 def test_reproducible_compiled_layer(self):
  r=read('preparation/reproduction.json');self.assertTrue(r['deterministic_replay']);self.assertTrue(r['idempotent'])
  self.assertEqual(r['baseline_rom_sha256'],json.loads((ROOT/'mods/hoenn/sea-landscapes-validation/preparation/reproduction.json').read_text())['rom_sha256'])
 def test_no_overlapping_rectangles_or_folded_edges(self):
  p=read('preparation/preparation.json');rect={r['map']:r for r in p['rectangles']}
  for a in rect.values():
   for b in rect.values():
    if a['map']>=b['map']:continue
    self.assertTrue(min(a['x']+a['width'],b['x']+b['width'])<=max(a['x'],b['x']) or min(a['y']+a['height'],b['y']+b['height'])<=max(a['y'],b['y']),(a,b))
  for c in p['connections']:
   a,b=rect[c['source']],rect[c['destination']]
   if c['direction']=='right':self.assertEqual(a['x']+a['width'],b['x']);self.assertEqual(c['offset'],b['y']-a['y'])
   else:self.assertEqual(a['y']+a['height'],b['y']);self.assertEqual(c['offset'],b['x']-a['x'])
 def test_full_eastern_rectangle_and_port_space(self):
  rect=read('preparation/preparation.json')['rectangles']
  # Ocean, native Ever Grande and the six retained ports tile the entire union.
  for y in range(240):
   intervals=sorted((max(80,r['x']),min(446,r['x']+r['width'])) for r in rect if r['y']<=y<r['y']+r['height'] and r['x']<446 and r['x']+r['width']>80)
   end=80
   for start,stop in intervals:self.assertLessEqual(start,end,(y,start,end));end=max(end,stop)
   self.assertEqual(end,446,y)
  self.assertEqual(len([r for r in rect if 'Harbor' in r['map']]),6)
 def test_native_capacity_and_preserved_story(self):
  p=read('preparation/preparation.json')
  for r in p['terrain']:
   self.assertLessEqual((r['width']+15)*(r['height']+14),10240);self.assertLessEqual(r['width'],127);self.assertLessEqual(r['height'],127)
  self.assertIn('src/fieldmap.c',p['prepared_sha256']);self.assertTrue(p['incoming_connection_upper_bound_exclusive'])
  self.assertTrue(p['route131_south_spur_removed']);self.assertTrue(p['no_added_transition_warps'])
  for f in ['data/layouts/EverGrandeCity/map.bin','src/journey_campaign_gates.c','src/journey_gym_scaling.c','src/data/trainers.party']:self.assertIn(f,p['preserved_native_sha256'])
  self.assertEqual(len([f for f in p['preserved_native_sha256'] if 'JourneySanctuary' in f and f.endswith('/map.bin')]),14)
 def test_native_surf_and_continuous_trip_behind_ever_grande(self):
  r=self.native('native/eastern-union.json');self.assertGreater(len(r['surf_seams']),100);self.assertTrue(all(s['surf_preserved'] for s in r['surf_seams']))
  self.assertTrue(r['continuous_roundtrip']);self.assertTrue(r['no_midroute_warps']);self.assertEqual(len(r['save_continue']),2)
  maps={x['map'] for x in r['legs']}
  self.assertTrue({'JourneyEverGrandeBackSea','JourneyEverGrandeBackSouthSea','JourneyWorldSea06','JourneyWorldSea04'}<=maps)
  self.assertFalse(r['full_campaign_playthrough'])
 def test_caves_npcs_waterfall_and_regional_gates(self):
  r=self.native('sanctuaries/sanctuary-routes.json');self.assertEqual(len(r['sites']),14);self.assertEqual(len(r['altars']),105);self.assertEqual(len(r['save_continue']),33)
  r=self.native('terrain/sea-landscapes.json');self.assertEqual(len(r['npcs']),47);self.assertTrue(r['waterfall']['native_prompt_and_climb'])
  r=self.native('leagues/sixteen-badge-leagues.json');self.assertEqual(r['permission_cases'],2048);self.assertEqual(len(r['physical_cases']),8)
  self.assertTrue(all(c['physical_denial'] and c['physical_entry_after_sixteen'] for c in r['physical_cases']))
  r=self.native('western-ocean/ocean-journey.json');self.assertEqual(len(r['transitions']),24);self.assertEqual(len(r['save_continue']),6)
  r=self.native('matrix/campaign-matrix.json');self.assertEqual(r['gate_cases'],11008);self.assertEqual(r['permission_cases'],44)
  self.assertEqual(r['checks'],json.loads((ROOT/'mods/hoenn/sea-landscapes-validation/matrix/campaign-matrix.json').read_text())['checks'])
 def test_render_and_english_match_compiled_rom(self):
  self.native('english-audit.json')
  r=json.loads((ROOT/'mods/hoenn/eastern-union-gallery/metadata.json').read_text());self.assertTrue(r['source_metatiles']);self.assertEqual(r['rom_sha256'],read('preparation/reproduction.json')['rom_sha256'])

if __name__=='__main__':unittest.main()
