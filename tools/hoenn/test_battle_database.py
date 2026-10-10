"""Release proofs for the external Gen 9 database and actual native learning."""
import hashlib,json,unittest
from audit_battle_database import decode_database,compare_database
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'mods/hoenn/playable-validation'
REFERENCE=ROOT/'tools/hoenn/data/scarlet-violet-database.json'
class BattleDatabase(unittest.TestCase):
 def test_official_reference_covers_every_base_species_and_retains_custom_rules(self):
  ref=json.loads(REFERENCE.read_text());catalog=json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text())
  self.assertTrue({str(i) for i in catalog['canonical_species'].values()}<=set(ref['species']))
  self.assertEqual(ref['provenance']['commit'],'942cda71d14bf0618bd57991708a2e2734b6daba')
  for sid,wanted in [('35',[19,19]),('39',[1,19]),('122',[15,19]),('183',[12,19]),('280',[15,19]),('303',[9,19]),('700',[19,19])]:self.assertEqual(ref['species'][sid]['types'],wanted)
  self.assertEqual(ref['moves']['15']['type'],13);self.assertEqual(ref['moves']['70']['type'],6)
 def test_compiled_rom_matches_reference_and_new_layer_reproduces(self):
  r=json.loads((EVIDENCE/'battle-database.json').read_text());replay=json.loads((EVIDENCE/'battle-database-preparation/reproduction.json').read_text())
  self.assertTrue(r['passed']);self.assertEqual(r['differences'],[])
  self.assertEqual(r['reference_sha256'],hashlib.sha256(REFERENCE.read_bytes()).hexdigest())
  self.assertGreaterEqual(r['species_checked'],1395);self.assertEqual(r['moves_checked'],847)
  self.assertGreaterEqual(r['fairy_species_checked'],89)
  self.assertTrue(replay['passed'] and replay['deterministic_replay'] and replay['idempotent'])
  self.assertEqual(replay['rom_sha256'],'2643c27c4cac5386c541c7f4cda568f57f83b5d93e9eb8c88eb8b0a406f5bf45')
 def test_native_creation_learning_fairy_and_save(self):
  r=json.loads((EVIDENCE/'learnsets/learnsets.json').read_text())
  self.assertTrue(r['passed'] and r['native_save_preserves_moves'])
  self.assertEqual(r['base_species'],1025);self.assertEqual(r['native_creation_cases'],5125)
  self.assertGreater(r['native_level_up_moves'],500)
  self.assertEqual(len(r['fairy_matchups']),12)
  self.assertEqual(next(c['modifier'] for c in r['fairy_matchups'] if c['attacker']==17 and c['defender']==19),0)
 def test_exported_bytes_match_and_wrong_pp_or_type_are_detected(self):
  proof=json.loads((EVIDENCE/'battle-database.json').read_text());layout=proof['compiled_layout']
  raw=(ROOT/'mods/hoenn/playable/Pokemon-Journey-World-Alpha-1.gba').read_bytes()
  self.assertTrue(compare_database(decode_database(raw,layout))['passed'])
  for mid,offset in [(33,layout['abi'][8]),(585,layout['abi'][7])]:
   altered=bytearray(raw);at=layout['symbols']['gMovesInfo']+mid*layout['abi'][6]+offset;altered[at]^=1
   failures=compare_database(decode_database(altered,layout))
   self.assertFalse(failures['passed']);self.assertTrue(any(d['kind']=='move' and d['id']==mid for d in failures['differences']))
 def test_both_leagues_finish_and_resume_without_enemy_mutations(self):
  for region in ['kanto','hoenn']:
   r=json.loads((EVIDENCE/f'full-league-{region}/{region}-league-completion.json').read_text())
   self.assertTrue(r['passed'] and r['native_hall_of_fame'] and r['native_credits_finished'])
   self.assertTrue(r['native_continue_menu'] and r['return_to_selected_home'] and r['native_flash_save_reload'])
   self.assertEqual(len(r['wins']),5)
   self.assertTrue(r['enemy_levels_not_written'] and r['other_region_uncompleted'])
   self.assertFalse(r['full_campaign_playthrough'])
if __name__=='__main__':unittest.main()
