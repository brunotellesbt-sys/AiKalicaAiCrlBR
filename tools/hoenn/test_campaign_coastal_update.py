"""Check the current release and preserve the earlier coastal/tournament proof."""
import hashlib,json,unittest
from pathlib import Path
from verify_versions import verify
ROOT=Path(__file__).resolve().parents[2]
class CoastalRelease(unittest.TestCase):
 def test_current_roms_have_fresh_focused_evidence(self):
  r=verify(ROOT/'mods/hoenn/versions');self.assertEqual(len(r['variants']),4)
  if r['validation_scope']=='sevii-surf-connections':
   self.assertFalse(r['previous_sootopolis_validation']['retested_on_current_rom'])
   r=json.loads((ROOT/r['previous_sootopolis_validation']['manifest']).read_text())
  if r['validation_scope']=='sootopolis-harbor':
   self.assertFalse(r['previous_validation']['retested_on_current_rom'])
   r=json.loads((ROOT/r['previous_validation']['manifest']).read_text())
  self.assertEqual(r['validation_scope'],'campaign-coastal-update')
  self.assertFalse(r['full_campaign_playthrough']);self.assertFalse(r['historical_validation']['retested_on_current_rom'])
  self.assertNotEqual(r['parent_rom_sha256'],r['historical_validation']['parent_rom_sha256'])
 def test_live_levels_follow_mean_inside_both_regions(self):
  r=json.loads((ROOT/'mods/hoenn/coastal-update-validation/common/levels/live-levels.json').read_text())
  self.assertEqual(r['actual_mossdeep_battle_levels'][-1],23)
  for c in r['checks']:
   lo=max(1,c['mean']-(1 if c['leader'] else 5));hi=min(100,c['mean']+(5 if c['leader'] else 2))
   self.assertTrue(all(lo<=level<=hi for level in c['enemy_levels']))
   if c['leader']:self.assertEqual(c['enemy_levels'][-1],min(100,c['mean']+5))
 def test_visible_actors_walk_from_the_correct_spawn(self):
  r=json.loads((ROOT/'mods/hoenn/coastal-update-validation/common/ports/ports-and-actors.json').read_text())
  self.assertEqual(len(r['crossover_visible_approaches']),2)
  for a in r['crossover_visible_approaches']:
   self.assertTrue(a['visible']);self.assertGreaterEqual(sum(abs(x-y) for x,y in zip(a['initial'],a['player'])),7);self.assertEqual(sum(abs(x-y) for x,y in zip(a['after_approach'],a['player'])),1)
  self.assertEqual(len(r['ports']),21)
  self.assertTrue(all(p['world_ferry_captains']==1 for p in r['ports'] if p['map']!='JourneyRoute12Shipyard'))
if __name__=='__main__':unittest.main()
