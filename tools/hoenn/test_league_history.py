"""Regression evidence for two regional championships sharing one native archive."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
VALIDATION=ROOT/'mods/hoenn/history-validation'

def report(path):return json.loads((VALIDATION/path).read_text())

class SharedLeagueHistoryRequirements(unittest.TestCase):
    def native(self,path):
        r=report(path)
        self.assertTrue(r['passed'])
        self.assertEqual(r['rom_sha256'],report('reproduction.json')['rom_sha256'])
        return r

    def test_strict_layer_replays_after_home_completion(self):
        r=report('reproduction.json')
        previous=json.loads((ROOT/'mods/hoenn/completion-validation/reproduction.json').read_text())
        self.assertEqual(r['baseline_rom_sha256'],previous['rom_sha256'])
        self.assertTrue(r['deterministic_replay']);self.assertTrue(r['idempotent'])
        self.assertEqual(r['files'],4)
        p=report('preparation.json')
        self.assertEqual(p['shared_archive_capacity'],50)
        self.assertTrue(p['save_layout_unchanged'])
        self.assertTrue(p['regional_clear_and_champion_flags_independent'])

    def test_previous_candidate_loses_first_region_history(self):
        r=report('baseline/history-baseline.json')
        self.assertTrue(r['passed']);self.assertTrue(r['baseline_erases_first_record'])
        self.assertEqual(r['rom_sha256'],report('reproduction.json')['baseline_rom_sha256'])
        self.assertEqual([a['records'] for a in r['archives']],[1,1])

    def test_ten_battles_in_one_save_in_both_region_orders(self):
        ids={'kanto':[1164,1165,1166,1167,1194],'hoenn':[261,262,263,264,335]}
        for first in ['kanto','hoenn']:
            with self.subTest(first=first):
                r=self.native(first+'-first/'+first+'-first-history.json')
                self.assertTrue(r['same_native_save']);self.assertTrue(r['ten_native_battle_victories'])
                self.assertTrue(r['both_champion_flags_persist']);self.assertTrue(r['shared_archive_preserved'])
                self.assertEqual(r['sequences'][0]['region'],first)
                self.assertEqual([a['records'] for a in r['archives']],[1,2])
                self.assertEqual(r['archives'][0]['records_sha256'][0],r['archives'][1]['records_sha256'][0])
                for i,seq in enumerate(r['sequences']):
                    self.assertEqual([w['trainer'] for w in seq['wins']],ids[seq['region']])
                    self.assertTrue(all(w['attacks']>0 for w in seq['wins']))
                    for key in ['native_hall_of_fame','native_credits_finished','native_continue_menu',
                                'return_to_selected_home','team_identity_and_hidden_slot_preserved','native_flash_save_reload']:
                        self.assertTrue(seq[key],key)
                    self.assertEqual(seq['other_region_uncompleted'],i==0)
                self.assertFalse(r['full_campaign_playthrough'])

    def test_both_native_screens_roll_over_at_fifty_teams(self):
        r=self.native('capacity/hall-capacity.json')
        self.assertEqual(r['shared_capacity'],50)
        self.assertEqual({c['region'] for c in r['cases']},{'hoenn','kanto'})
        for c in r['cases']:
            self.assertEqual(c['records'],50)
            for key in ['oldest_only_removed','remaining_records_byte_identical','new_team_identity_preserved',
                        'native_credits_and_continue','native_flash_reload']:
                self.assertTrue(c[key],key)
        self.assertTrue(r['archive_and_champion_states_are_fixtures'])
        self.assertFalse(r['pc_viewer_validated'])

    def test_lorelei_rematch_uses_own_regional_championship(self):
        r=self.native('rematch/kanto-elite-rematch.json')
        self.assertEqual(r['first_trainer_id'],1470)
        self.assertTrue(r['own_kanto_champion_selects_rematch'])
        self.assertTrue(r['real_first_elite_victory']);self.assertTrue(r['native_progression_door'])
        self.assertTrue(r['native_flash_save_reload']);self.assertTrue(r['badge_and_champion_states_are_fixtures'])
        self.assertFalse(r['full_league_victory'])

    def test_story_gates_and_catalog_remain_valid(self):
        r=self.native('campaign-matrix.json')
        self.assertEqual(r['gate_cases'],4096);self.assertEqual(r['permission_cases'],36)
        self.assertTrue(r['giovanni_and_space_center_required'])
        r=self.native('catalog.json')
        self.assertEqual(r['base_species_count'],1025);self.assertEqual(r['missing_assets'],[])
        megas=self.native('megas.json');self.assertEqual(megas['enabled_mega_forms'],97)

if __name__=='__main__':unittest.main()
