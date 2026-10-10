"""Native matrix regression for order-independent regional leader parties."""
import hashlib,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class AdaptiveGyms(unittest.TestCase):
 def test_native_matrix_has_every_leader_rank_and_player_size(self):
  r=json.loads((ROOT/'mods/hoenn/playable-validation/adaptive-gym-teams/adaptive-gym-teams.json').read_text())
  self.assertTrue(r['passed'] and r['enemy_party_not_written'])
  self.assertEqual(r['leaders'],16);self.assertEqual(r['cases'],768)
  self.assertEqual(r['egg_cases'],128);self.assertGreater(r['move_cases'],3000)
  self.assertEqual(r['rom_sha256'],hashlib.sha256((ROOT/'mods/hoenn/playable/Pokemon-Journey-World-Alpha-1.gba').read_bytes()).hexdigest())
  self.assertEqual(len({(c['leader'],c['rank'],c['player_count']) for c in r['checks']}),768)
  for c in r['checks']:
   rank=c['rank'];players=c['player_count']
   count=6 if rank>=5 else rank+1+(players>rank+1)
   self.assertEqual(c['enemy_count'],count)
   self.assertEqual(c['levels'][-1],[14,21,28,35,42,48,54,60][rank-1])
   self.assertEqual(c['species'][-1],c['ace'])
  self.assertTrue(r['regional_badge_banks_independent'] and r['signature_preserved_across_party_sizes'])
 def test_actual_mossdeep_battle_stays_double_with_even_or_odd_teams(self):
  for name,count,double in [('double',2,True),('odd',3,True)]:
   r=json.loads((ROOT/f'mods/hoenn/playable-validation/mossdeep-{name}/mossdeep-entry.json').read_text())
   self.assertTrue(r['passed'] and r['native_gym_script'])
   self.assertEqual(r['player_count'],count);self.assertEqual(r['leader_count'],count);self.assertEqual(r['double_battle'],double)
if __name__=='__main__':unittest.main()
