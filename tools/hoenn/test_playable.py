"""Check released bytes and native map evidence, rather than source snippets."""
import hashlib,json,unittest,struct,zlib
from pathlib import Path
from verify_playable import verify
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'mods/hoenn/playable-validation'
def png_colors(path):
 raw=Path(path).read_bytes();at=8;data=b''
 while at<len(raw):
  size=struct.unpack_from('>I',raw,at)[0];kind=raw[at+4:at+8];chunk=raw[at+8:at+8+size];at+=size+12
  if kind==b'IHDR':w,h,depth,color,*_=struct.unpack('>IIBBBBB',chunk);assert (depth,color)==(8,2)
  elif kind==b'IDAT':data+=chunk
 data=zlib.decompress(data);previous=bytearray(w*3);colors=set();at=0
 for _ in range(h):
  filt=data[at];row=bytearray(data[at+1:at+1+w*3]);at+=w*3+1
  for i in range(len(row)):
   a=row[i-3] if i>=3 else 0;b=previous[i];c=previous[i-3] if i>=3 else 0
   predictor=a+b-c;dist=[abs(predictor-v) for v in [a,b,c]];paeth=[a,b,c][dist.index(min(dist))]
   row[i]=(row[i]+[0,a,b,(a+b)//2,paeth][filt])&255
  colors.update(tuple(row[i:i+3]) for i in range(0,len(row),3));previous=row
 return colors

class PlayableAlpha(unittest.TestCase):
 def test_exported_rom_matches_all_validation_evidence(self):
  r=verify(ROOT/'mods/hoenn/playable')
  self.assertFalse(r['full_campaign_playthrough'])
  self.assertEqual(r['layers'][-1],'coastal-world-map')
 def test_native_menu_map_returns_without_changing_location(self):
  r=json.loads((EVIDENCE/'world-map/world-map.json').read_text())
  self.assertTrue(r['pokenav_entry_and_return'] and r['native_save_menu_and_continue'])
  self.assertLessEqual(r['maximum_normal_menu_rows'],9)
  self.assertEqual({c['map'] for c in r['checks']},{'JourneyRoute12Shipyard','Route1_Frlg','LittlerootTown','SixIsland_Frlg'})
  for c in r['checks']:
   self.assertTrue(all(c[k] for k in ['controller_open','move','recenter','back','position_preserved']))
 def test_world_map_layer_reproduces_and_preserves_campaign_and_terrain(self):
  r=json.loads((EVIDENCE/'coastal-world-map-preparation/reproduction.json').read_text())
  p=json.loads((EVIDENCE/'coastal-world-map-preparation/preparation.json').read_text())
  self.assertTrue(r['passed'] and r['deterministic_replay'] and r['idempotent'])
  self.assertEqual(r['rom_sha256'],json.loads((EVIDENCE/'world-map/world-map.json').read_text())['rom_sha256'])
  for path in ['src/region_map.c','src/journey_campaign_gates.c','src/journey_gym_scaling.c','data/layouts/JourneyRoute12Shipyard/map.bin']:
   self.assertIn(path,p['preserved_native_sha256']);self.assertNotIn(path,p['prepared_sha256'])
 def test_open_coast_has_a_real_surf_and_pedestrian_roundtrip(self):
  r=json.loads((EVIDENCE/'coast/kanto-open-sea.json').read_text())
  p=json.loads((EVIDENCE/'coast-preparation/preparation.json').read_text())
  self.assertTrue(r['passed'] and r['continuous_surf_roundtrip'] and r['no_midtrip_fixture_warps'])
  self.assertTrue(r['bridge_walk_without_surf'])
  self.assertTrue(p['no_rectangle_overlaps'] and p['approved_shipyard_core_preserved'])
  self.assertTrue(p['vermilion_exit_not_restored'] and p['map_buffers_fit'])
  for rect in p['rectangles']:
   self.assertLessEqual((rect['width']+15)*(rect['height']+14),p['map_buffer_limit'])
 def test_world_art_has_one_sea_color_and_one_navigable_route_color(self):
  colors=png_colors(ROOT/'mods/hoenn/world-map-gallery/world-map-art.png')
  blue={c for c in colors if c[2]>c[0]+20 and c[2]>c[1]-30}
  self.assertEqual(blue,{(112,184,232),(48,104,176)})
 def test_browser_runs_core_and_restores_native_save_state(self):
  r=json.loads((EVIDENCE/'browser.json').read_text())
  self.assertTrue(r['passed'])
  self.assertTrue(r['actual_core_boot'] and r['corrupt_download_rejected'] and r['retry_available'])
  self.assertLessEqual(abs(r['state_saved_frame']-r['state_restore_frame']),30)
  self.assertTrue(r['mobile_no_horizontal_overflow'] and r['same_local_release_save_namespace'])
if __name__=='__main__':unittest.main()
