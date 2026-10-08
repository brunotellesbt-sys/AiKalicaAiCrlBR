"""Native complete League sequences and persistent selected-home destinations."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
VALIDATION=ROOT/'mods/hoenn/completion-validation'
def report(name):return json.loads((VALIDATION/(name+'.json')).read_text())
class LeagueCompletionRequirements(unittest.TestCase):
 def native(self,name):
  r=report(name);self.assertTrue(r['passed']);self.assertEqual(r['rom_sha256'],report('reproduction')['rom_sha256']);return r
 def test_replay_uses_the_previous_league_candidate(self):
  r=report('reproduction');previous=json.loads((ROOT/'mods/hoenn/league-validation/reproduction.json').read_text())
  self.assertEqual(r['baseline_rom_sha256'],previous['rom_sha256'])
  self.assertTrue(r['deterministic_replay']);self.assertTrue(r['idempotent']);self.assertEqual(r['files'],4)
  prep=report('preparation');self.assertTrue(prep['save_layout_unchanged']);self.assertTrue(prep['no_home_preserves_original_fallback'])
  self.assertTrue(prep['badges_and_champion_flags_unchanged'])
  self.assertEqual(set(prep['prepared_sha256']),{'include/overworld.h','include/journey_family.h','src/journey_family.c','src/post_battle_event_funcs.c'})
 def test_both_five_battle_sequences_resume_the_native_save(self):
  for region,ids,home in [('kanto',[1164,1165,1166,1167,1194],'Mauville'),('hoenn',[261,262,263,264,335],'Vermilion')]:
   with self.subTest(region=region):
    r=self.native(region+'-league-completion')
    self.assertEqual([w['trainer'] for w in r['wins']],ids)
    self.assertTrue(all(w['attacks']>0 for w in r['wins']))
    for check in ['native_hall_of_fame','native_credits_finished','native_continue_menu','return_to_selected_home',
                  'team_identity_and_hidden_slot_preserved','other_region_uncompleted','native_flash_save_reload']:
     self.assertTrue(r[check],check)
    self.assertEqual(r['selected_home'],home)
    self.assertTrue(r['healing_between_battles_is_fixture']);self.assertFalse(r['full_campaign_playthrough'])
    for name in ['continue-menu','credits-start','home-after-credits']:
     self.assertGreater((VALIDATION/(region+'-'+name+'.png')).stat().st_size,1000)
 def test_all_houses_and_both_genders_have_persistent_destinations(self):
  r=self.native('home-resume');cases=r['cases']
  self.assertEqual(len(cases),62)
  self.assertEqual({(c['index'],c['gender']) for c in cases},{(i,g) for i in range(1,32) for g in [0,1]})
  self.assertTrue(all(c['native_flash_save_reload'] for c in cases))
  female=next(c for c in cases if c['index']==17 and c['gender']==1)
  male=next(c for c in cases if c['index']==17 and c['gender']==0)
  self.assertEqual(female['map'],'LittlerootTown_MaysHouse_2F');self.assertEqual(male['map'],'LittlerootTown_BrendansHouse_2F')
  self.assertTrue(r['flags_unchanged']);self.assertTrue(r['invalid_home_leaves_destination_unchanged'])
  self.assertFalse(r['full_credit_sequences'])
 def test_campaigns_and_league_doors_remain_independent(self):
  matrix=self.native('campaign-matrix');self.assertEqual(matrix['gate_cases'],4096)
  self.assertTrue(matrix['giovanni_and_space_center_required'])
  doors=self.native('league-access');self.assertEqual(doors['kanto_badge_subsets'],256)
  self.assertEqual(len(doors['physical_entry_cases']),20)
  self.assertTrue(doors['champion_flags_independent'])
  catalog=self.native('catalog');self.assertEqual(catalog['enabled_mega_forms'],97);self.assertFalse(catalog['stones_distributed'])
if __name__=='__main__':unittest.main()
