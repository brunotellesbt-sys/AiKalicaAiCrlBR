"""Shipyard evidence: native travel, indoor doors, ferries and continuous geometry."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
DIR=ROOT/'mods/hoenn/route12-shipyard-validation'
def read(name):return json.loads((DIR/name).read_text())
class Route12Shipyard(unittest.TestCase):
 def test_replay_and_story_preservation(self):
  p=read('preparation/preparation.json');r=read('preparation/reproduction.json')
  self.assertTrue(r['passed'] and r['deterministic_replay'] and r['idempotent'])
  self.assertTrue(p['compact_platform'] and p['sailors_lodge'] and p['boats_docked_against_piers'])
  self.assertEqual(p['grassy_house_border_tiles'],1)
  self.assertEqual(p['sandy_grass_border_tiles'],1)
  self.assertTrue(p['northwest_berth'] and p['central_water_holes_filled'] and p['irregular_house_island'])
  self.assertEqual(p['soil_extension_max_tiles'],2)
  self.assertEqual((p['boat_count'],p['larger_boats']),(7,3))
  self.assertTrue(p['fuchsia_unchanged'] and p['snorlax_and_route12_events_preserved'])
  for f in ['src/journey_campaign_gates.c','src/journey_gym_scaling.c','data/maps/Route12_Frlg/scripts.inc','data/maps/JourneyFuchsiaSea/map.json']:
   self.assertIn(f,p['preserved_native_sha256'])
 def test_native_foot_surf_doors_and_continue(self):
  r=read('native/route12-shipyard.json')
  for flag in ['passed','continuous_roundtrip','foot_access_from_existing_route12_walkway','save_continue_on_pier','no_midroute_warps','sailors_lodge_native_entry_and_exit','vermilion_old_exit_physically_closed']:
   self.assertTrue(r[flag],flag)
  self.assertEqual(r['rom_sha256'],read('preparation/reproduction.json')['rom_sha256'])
  self.assertTrue(any(x['map']=='TwoIsland_Harbor_Frlg' for x in r['legs']))
  self.assertTrue(any(x['map']=='JourneyEverGrandeBackSouthSea' for x in r['legs']))
  self.assertFalse(r['full_campaign_playthrough'])
 def test_real_captain_menus_and_return(self):
  r=read('ferry/route12-ferry.json')
  self.assertTrue(r['passed'] and r['actual_captain_interactions'] and r['actual_menu_choices'] and r['return_save_continue'])
  self.assertEqual(r['rom_sha256'],read('preparation/reproduction.json')['rom_sha256'])
 def test_rectangle_alignment_without_overlapping_maps(self):
  meta=json.loads((ROOT/'mods/hoenn/route12-shipyard-gallery/metadata.json').read_text());rects={r['map']:r for r in meta['rectangles']}
  a,b,c= [rects[n] for n in ['Route12_Frlg','JourneyRoute12Shipyard','JourneyWorldSea02']]
  self.assertEqual(a['x']+a['width'],b['x']);self.assertEqual(a['y']+60,b['y'])
  self.assertEqual(b['y']+b['height'],c['y']);self.assertEqual(b['x'],c['x']+1)
  for a in rects.values():
   for b in rects.values():
    if a['map']>=b['map']:continue
    self.assertTrue(min(a['x']+a['width'],b['x']+b['width'])<=max(a['x'],b['x']) or min(a['y']+a['height'],b['y']+b['height'])<=max(a['y'],b['y']),(a,b))
  self.assertEqual(meta['rom_sha256'],read('preparation/reproduction.json')['rom_sha256'])
if __name__=='__main__':unittest.main()
