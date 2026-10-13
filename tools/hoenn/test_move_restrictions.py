"""Bind native move-effect regression reports to the current release ROM."""
import hashlib,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class NativeMoveRestrictions(unittest.TestCase):
    def test_history_pp_and_status_regressions_match_the_release(self):
        manifest=json.loads((ROOT/'mods/hoenn/versions/versions.json').read_text())
        for kind in ['move-restrictions','pwt-encore']:
            report=json.loads((ROOT/f'mods/hoenn/pwt-gen1-4-validation/{kind}.json').read_text())
            self.assertTrue(report['passed'])
            self.assertEqual(report['rom_sha256'],manifest['parent_rom_sha256'])
        cases=report # Encore report assertions are independent of case count.
        self.assertTrue(cases['no_history_fails_without_crashing'])
        self.assertTrue(cases['valid_encore_preserved'])
        report=json.loads((ROOT/'mods/hoenn/pwt-gen1-4-validation/move-restrictions.json').read_text())
        self.assertEqual(report['cases'],len(report['checks']))
        self.assertGreaterEqual(report['cases'],60)
        names={c['case'] for c in report['checks']}
        self.assertTrue({'Cmd_disablelastusedattack','Cmd_copymovepermanently','Cmd_mimicattackcopy',
            'BS_TryInstruct','copycat_case','mefirst_case','encore_plus_torment','all_pp_exhausted',
            'choice_item_combination','move_pp_pressure','spread_move_two_pressure_opponents',
            'struggle_has_no_pp_cost','normal_switch','ai_stab_recording'}<=names)
        for row in report['checks']:
            if row['case'] in ['spite_pp','move_pp_pressure','spread_move_two_pressure_opponents']:
                self.assertLessEqual(row['after'],row['before'])
                self.assertGreaterEqual(row['after'],0)
    def test_struggle_is_observed_in_a_real_gen1_cup(self):
        path=ROOT/'mods/hoenn/pwt-gen1-4-validation/Normal-gen1/pwt-generation-cup.json'
        report=json.loads(path.read_text())
        self.assertTrue(report['exhausted_pp_for_struggle_fixture'])
        self.assertTrue(report['native_struggle_observed'])
        self.assertTrue(report['complete_tournament_playthrough'])
if __name__=='__main__':unittest.main()
