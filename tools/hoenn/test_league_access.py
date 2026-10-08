"""Evidence for early National Dex, independent leagues and real Elite battles."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / 'mods/hoenn/league-validation'


def report(name):
    return json.loads((VALIDATION / (name + '.json')).read_text())


class LeagueAccessRequirements(unittest.TestCase):
    def native(self, name):
        result = report(name)
        self.assertTrue(result['passed'])
        self.assertEqual(result['rom_sha256'], report('reproduction')['rom_sha256'])
        return result

    def test_both_regressions_reproduce_on_the_previous_candidate(self):
        baseline = report('league-baseline')
        self.assertTrue(baseline['baseline_regressions_reproduced'])
        self.assertTrue(baseline['eight_kanto_badges_blocked_with_national_dex'])
        self.assertTrue(baseline['hoenn_champion_leaks_into_kanto'])
        reproduction = report('reproduction')
        self.assertEqual(baseline['rom_sha256'], reproduction['baseline_rom_sha256'])
        previous = json.loads((ROOT/'mods/hoenn/aftermath-validation/reproduction.json').read_text())
        self.assertEqual(previous['rom_sha256'], reproduction['baseline_rom_sha256'])
        self.assertTrue(reproduction['deterministic_replay'])
        self.assertTrue(reproduction['idempotent'])
        self.assertEqual(reproduction['files'],4)
        prep = report('preparation')
        self.assertTrue(prep['save_layout_unchanged'])
        self.assertTrue(prep['hoenn_guard_preserved'])
        self.assertEqual(prep['kanto_champion_flag'],0x1AC2)

    def test_each_missing_badge_blocks_only_its_own_league(self):
        native = self.native('league-access')
        self.assertEqual(native['kanto_badge_subsets'],256)
        for region in ('Kanto','Hoenn'):
            cases = [c for c in native['physical_entry_cases'] if c['region']==region]
            self.assertEqual(len(cases),10)
            self.assertEqual({c['own_mask'] for c in cases},{0,255}|{255^(1<<i) for i in range(8)})
            for case in cases:
                self.assertEqual(case['entered'],case['own_mask']==255)
                self.assertEqual(case['other_mask'],0 if case['entered'] else 255)
        for name in ('early_national_dex_does_not_block_first_league','champion_flags_independent',
                     'game_clear_flags_independent','native_flash_save_reload','completion_scripts_executed'):
            self.assertTrue(native[name],name)
        self.assertFalse(native['full_elite_four_victory'])

    def test_real_first_elite_victories_open_the_next_room(self):
        for region in ('kanto','hoenn'):
            with self.subTest(region=region):
                native = self.native(region+'-elite-battle')
                for name in ('real_first_elite_victory','ash_after_ko','party_identity_preserved',
                             'ash_reverted_after_battle','native_progression_door','native_flash_save_reload'):
                    self.assertTrue(native[name],name)
                self.assertGreater(native['attacks'],0)
                self.assertFalse(native['full_league_victory'])
                if region=='kanto':
                    self.assertTrue(native['other_region_champion_does_not_select_kanto_rematch'])
                for suffix in ('first-elite-room','elite-ash-battle','elite-next-room'):
                    self.assertGreater((VALIDATION/(region+'-'+suffix+'.png')).stat().st_size,1000)

    def test_regional_missions_remain_gated_and_catalog_complete(self):
        matrix = self.native('campaign-matrix')
        self.assertEqual(matrix['gate_cases'],4096)
        self.assertTrue(matrix['giovanni_and_space_center_required'])
        catalog = self.native('catalog')
        self.assertEqual(catalog['enabled_mega_forms'],97)
        self.assertEqual(catalog['incomplete_assets'],[])
        self.assertFalse(catalog['stones_distributed'])
        maps = self.native('map-destinations')
        self.assertEqual(maps['errors'],[])
        self.assertEqual(maps['maps'],1046)

    def test_boats_and_western_surf_crossings_survive_the_new_flag_bank(self):
        travel = report('travel/connected-world')
        self.assertEqual(travel['rom_sha256'],report('reproduction')['rom_sha256'])
        ferry = next(c for c in travel['checks'] if c['check']=='early_ticketed_interregional_ferry')
        self.assertTrue(ferry['passed'])
        self.assertEqual(ferry['ports_tested'],9)
        self.assertEqual(len(ferry['trips']),16)
        for name in ('zero_badges','mission_flags_unchanged','native_flash_save_roundtrip',
                     'regional_format_switches','full_key_pocket_retry'):
            self.assertTrue(ferry[name],name)
        crossings = [c for c in travel['checks'] if c['check']=='physical_surf_seam']
        self.assertEqual(len(crossings),18)
        self.assertTrue(all(c['passed'] for c in crossings))


if __name__ == '__main__':
    unittest.main()
