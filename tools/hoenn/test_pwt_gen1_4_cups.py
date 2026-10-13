"""Keep complete generation-cup evidence tied to the shipped Gen 1–4 ROMs."""
import hashlib,json,unittest
from pathlib import Path
from pwt_catalog import load,eligible
ROOT=Path(__file__).resolve().parents[2]
class CompleteGenerationCups(unittest.TestCase):
    def test_eight_complete_native_cups_match_the_current_roms_and_participant_pools(self):
        rows=load()
        for difficulty in ['Normal','Hard']:
            rom=ROOT/'roms'/f'Pokemon-Journey-Gen1-4-{difficulty}.gba'
            sha=hashlib.sha256(rom.read_bytes()).hexdigest()
            for generation in range(1,5):
                with self.subTest(difficulty=difficulty,generation=generation):
                    path=ROOT/'mods/hoenn/pwt-gen1-4-validation'/f'{difficulty}-gen{generation}'/'pwt-generation-cup.json'
                    report=json.loads(path.read_text())
                    self.assertEqual(report['rom_sha256'],sha)
                    self.assertTrue(report['passed'] and report['complete_tournament_playthrough'])
                    self.assertEqual(report['version_generation_cap'],4)
                    self.assertEqual(report['difficulty'],difficulty)
                    self.assertEqual(report['cup_generation'],generation)
                    self.assertEqual(report['entrants'],len(eligible(rows,4,generation))+1)
                    self.assertTrue(report['champion'] and report['returned_to_lobby'])
                    self.assertEqual(report['bp_reward'],10)
                    self.assertTrue(report['party_restored_byte_exact'])
                    self.assertTrue(report['both_entrances_complete_at_ready_prompt'])
                    self.assertTrue(report['helper_and_travel_fixtures'])
                    self.assertTrue(report['player_battle_stats_boosted_for_flow_test'])
                    self.assertFalse(report['competitive_balance_test'])
                    battles=report['actual_battles']
                    self.assertEqual({b['stage'] for b in battles},{0,1})
                    allowed={r['id']:r['name'] for r in eligible(rows,4,generation)}
                    for battle in battles:
                        self.assertEqual(battle['outcome'],1)
                        self.assertEqual(battle['level'],50)
                        self.assertEqual(battle['player_team_size'],6)
                        self.assertEqual(battle['enemy_team_size'],6)
                        self.assertEqual(battle['opponent_name'],allowed[battle['opponent_catalog_id']])
if __name__=='__main__':unittest.main()
