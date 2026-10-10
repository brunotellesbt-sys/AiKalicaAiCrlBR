"""Integrity contracts for the compiled sea redesign and native traversal evidence."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
DIR=ROOT/'mods/hoenn/sea-landscapes-validation'
def read(p):return json.loads((DIR/p).read_text())
class SeaLandscapes(unittest.TestCase):
 def native(self,p):
  r=read(p);self.assertTrue(r['passed']);self.assertEqual(r['rom_sha256'],read('preparation/reproduction.json')['rom_sha256']);return r
 def test_exact_native_seafoam_mountain_and_preserved_interiors(self):
  p=read('preparation/preparation.json');mountain=p['seafoam_mountain']
  self.assertEqual(mountain['source_map'],'Route20_Frlg');self.assertTrue(mountain['tiles_copied_exactly'])
  self.assertEqual([cell for cell in mountain['cells'] if cell[:2]==[0,0]],[[0,0,0x30A9]])
  self.assertGreater(len(mountain['cells']),60)
  self.assertEqual(len(p['caves']),14)
  for cave in p['caves']:
   self.assertTrue(cave['interior_unchanged'])
   self.assertIn('data/layouts/'+cave['map']+'/map.bin',p['preserved_native_sha256'])
 def test_replay_and_water_predominance_in_all_active_seas(self):
  r=read('preparation/reproduction.json');self.assertTrue(r['deterministic_replay']);self.assertTrue(r['idempotent'])
  prior=json.loads((ROOT/'mods/hoenn/rusturf-reunion-validation/preparation/reproduction.json').read_text())
  self.assertEqual(r['baseline_rom_sha256'],prior['rom_sha256'])
  p=read('preparation/preparation.json');self.assertEqual(len(p['maps']),27)
  self.assertEqual(len({m['blockdata_sha256']for m in p['maps']}),27)
  for m in p['maps']:self.assertGreater(m['water_fraction'],.6)
 def test_all_47_npcs_visible_on_correct_native_surface(self):
  r=self.native('terrain/sea-landscapes.json');self.assertEqual(len(r['maps']),27);self.assertEqual(len(r['npcs']),47)
  self.assertTrue(all(e['native_visible']for e in r['npcs']))
  self.assertEqual(sum(not e['water']for e in r['npcs']),22)
  self.assertTrue(any('AQUA' in e['graphics'] and e['map']=='JourneyRustboroCoast'for e in r['npcs']))
  self.assertTrue(any(e['water'] and e['graphics']=='OBJ_EVENT_GFX_SWIMMER_M_WATER'for e in r['npcs']))
 def test_waterfall_required_only_for_climbing_native_river(self):
  r=self.native('terrain/sea-landscapes.json');w=r['waterfall']
  for k in ['no_move_cannot_climb','native_prompt_and_climb','native_descent','zero_badges']:self.assertTrue(w[k])
  self.assertLessEqual(w['upper_position'][1],9)
  p=read('preparation/preparation.json')['river_access']
  self.assertEqual(p['connection_offset'],-10)
  self.assertEqual([x+10 for x in p['river_edge_rows']],p['route_edge_rows'])
 def test_all_96_surf_connections_remain_native(self):
  r=read('seams/connected-world.json');self.assertEqual(r['rom_sha256'],read('preparation/reproduction.json')['rom_sha256'])
  seams=[x for x in r['checks']if x['check']=='physical_surf_seam'];self.assertEqual(len(seams),96);self.assertTrue(all(x['passed']for x in seams))
 def test_complete_continuous_west_coast_trip_and_cave_returns(self):
  r=self.native('ocean/ocean-journey.json');self.assertTrue(r['continuous_roundtrip']);self.assertTrue(r['no_midroute_warps_or_direct_trainer_scripts'])
  self.assertEqual(r['start'],r['end']);self.assertEqual(len(r['transitions']),24);self.assertEqual(len(r['save_continue']),6)
  r=self.native('sanctuaries/sanctuary-routes.json');self.assertEqual(len(r['sites']),14);self.assertEqual(len(r['altars']),105);self.assertEqual(len(r['save_continue']),33)
  for s in r['sites']:self.assertEqual(s['initial_position'],s['final_position'])
 def test_regional_mission_thresholds_and_levels_unchanged(self):
  r=self.native('matrix/campaign-matrix.json');prior=json.loads((ROOT/'mods/hoenn/rusturf-reunion-validation/matrix/campaign-matrix.json').read_text())
  self.assertEqual(r['checks'],prior['checks']);self.assertEqual(r['gate_cases'],11008);self.assertEqual(r['permission_cases'],44)
  p=read('preparation/preparation.json')['preserved_native_sha256']
  for name in ['src/journey_campaign_gates.c','src/journey_gym_scaling.c','src/journey_wild.c','src/data/trainers.party','include/constants/opponents.h']:self.assertIn(name,p)
 def test_english_and_fixture_limits(self):
  r=self.native('english-audit.json');self.assertEqual(r['portuguese_marker_matches'],0)
  for p in ['terrain/sea-landscapes.json','ocean/ocean-journey.json','sanctuaries/sanctuary-routes.json']:
   r=self.native(p);self.assertFalse(r['full_campaign_playthrough'])
if __name__=='__main__':unittest.main()
