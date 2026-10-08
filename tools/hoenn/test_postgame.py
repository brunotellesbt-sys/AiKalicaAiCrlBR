"""Native PC history and complete League repeat visits after both championships."""
import json
import struct
import zlib
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
VALIDATION=ROOT/'mods/hoenn/postgame-validation'

def report(path):return json.loads((VALIDATION/path).read_text())

class PostgameRequirements(unittest.TestCase):
    def native(self,path,baseline=False):
        r=report(path);self.assertTrue(r['passed'])
        self.assertEqual(r['rom_sha256'],report('reproduction.json')['baseline_rom_sha256' if baseline else 'rom_sha256']);return r

    def test_display_overlay_is_one_strict_file_after_shared_history(self):
        r=report('reproduction.json')
        previous=json.loads((ROOT/'mods/hoenn/history-validation/reproduction.json').read_text())
        self.assertEqual(r['baseline_rom_sha256'],previous['rom_sha256'])
        self.assertTrue(r['deterministic_replay']);self.assertTrue(r['idempotent']);self.assertEqual(r['files'],1)
        p=report('preparation.json')
        self.assertEqual(set(p['prepared_sha256']),{'src/hall_of_fame_frlg.c'})
        for key in ['dex_numbers_above_999','three_digit_style_below_1000_preserved',
                    'unknown_species_question_marks_preserved','save_layout_unchanged','species_and_battle_rules_unchanged']:
            self.assertTrue(p[key],key)

    def test_both_complete_league_repeat_visits_in_both_orders(self):
        first_ids={'kanto':[1164,1165,1166,1167,1194],'hoenn':[261,262,263,264,335]}
        repeat_ids={'kanto':[1470,1471,1472,1473,1476],'hoenn':first_ids['hoenn']}
        for first in ['kanto','hoenn']:
            with self.subTest(first=first):
                r=self.native(first+'-first/'+first+'-first-rematches.json')
                self.assertTrue(r['complete_rematches']);self.assertTrue(r['same_native_save'])
                self.assertTrue(r['champion_coverage_moves_are_fixture'])
                self.assertEqual(r['native_battle_victories'],20)
                order=[first,'hoenn' if first=='kanto' else 'kanto']*2
                self.assertEqual([seq['region'] for seq in r['sequences']],order)
                self.assertEqual([a['records'] for a in r['archives']],[1,2,3,4])
                for i,seq in enumerate(r['sequences']):
                    expected=(repeat_ids if i>=2 else first_ids)[seq['region']]
                    self.assertEqual([w['trainer'] for w in seq['wins']],expected)
                    self.assertTrue(all(w['attacks']>0 for w in seq['wins']))
                    for key in ['native_hall_of_fame','native_credits_finished','native_continue_menu',
                                'return_to_selected_home','team_identity_and_hidden_slot_preserved','native_flash_save_reload']:
                        self.assertTrue(seq[key],key)
                    self.assertEqual(seq['other_region_uncompleted'],i==0)
                    if i:
                        previous=r['archives'][i-1]['records_sha256']
                        self.assertEqual(r['archives'][i]['records_sha256'][:len(previous)],previous)
                self.assertFalse(r['full_campaign_playthrough'])

    def test_both_pc_interfaces_navigate_the_entire_shared_archive(self):
        r=self.native('pc/hall-pc.json')
        self.assertEqual({(c['region'],c['records']) for c in r['cases']},
                         {(region,n) for region in ['kanto','hoenn'] for n in [1,50]})
        for c in r['cases']:
            self.assertEqual(c['pages_visited'],c['records']);self.assertEqual(c['mons_navigated'],6)
            for key in ['newest_and_oldest_correct','mon_boundaries_respected','menu_return_and_logoff',
                        'archive_unchanged','native_flash_save_reload']:
                self.assertTrue(c[key],key)
            self.assertEqual(c['exit'],'B' if c['records']==1 else 'A_at_oldest')
        self.assertTrue(r['archive_and_championships_are_fixtures'])
        self.assertTrue(r['native_pc_menu_and_navigation']);self.assertTrue(r['physical_pc_interaction']);self.assertTrue(r['national_dex_enabled'])

    def test_native_pc_screenshots_include_recent_generation_species(self):
        r=self.native('pc/hall-pc.json')
        catalog=json.loads((ROOT/'mods/hoenn/history-validation/catalog.json').read_text())
        expected=[catalog['canonical_species'][str(n)] for n in [1,25,252,387,658,1025]]
        for c in r['cases']:
            self.assertEqual(c['viewed_species'],expected)
            for image in ['pc-menu','newest-team','oldest-team','returned-menu','field-after-pc','dex-1025']:
                path=VALIDATION/'pc'/f"{c['region']}-{c['records']}-{image}.png"
                self.assertGreater(path.stat().st_size,1000)

    def test_before_after_changes_only_the_four_digit_kanto_label(self):
        self.native('baseline-pc/hall-pc.json',baseline=True)
        self.native('pc/hall-pc.json')
        def pixels(path):
            raw=path.read_bytes();at=8;data=b''
            while at<len(raw):
                size=struct.unpack('>I',raw[at:at+4])[0]
                if raw[at+4:at+8]==b'IDAT':data+=raw[at+8:at+8+size]
                at+=size+12
            decoded=zlib.decompress(data)
            self.assertEqual(len(decoded),721*160)
            self.assertTrue(all(decoded[y*721]==0 for y in range(160)))
            return [decoded[y*721+1:(y+1)*721] for y in range(160)]
        for count in [1,50]:
            for region in ['kanto','hoenn']:
                for image in ['newest-team','dex-1025']:
                    before=pixels(VALIDATION/'baseline-pc'/f'{region}-{count}-{image}.png')
                    after=pixels(VALIDATION/'pc'/f'{region}-{count}-{image}.png')
                    changes=[(x,y) for y in range(160) for x in range(240)
                             if before[y][x*3:x*3+3]!=after[y][x*3:x*3+3]]
                    if region=='kanto' and image=='dex-1025':
                        self.assertGreater(len(changes),0)
                        self.assertTrue(all(50<=x<=80 and 120<=y<=136 for x,y in changes))
                    else:self.assertEqual(changes,[])

    def test_native_hall_of_fame_still_saves_and_rolls_over(self):
        r=self.native('capacity/hall-capacity.json')
        self.assertEqual(r['shared_capacity'],50)
        self.assertEqual({c['region'] for c in r['cases']},{'kanto','hoenn'})
        self.assertTrue(all(c['oldest_only_removed'] and c['remaining_records_byte_identical']
                            and c['native_credits_and_continue'] and c['native_flash_reload'] for c in r['cases']))

if __name__=='__main__':unittest.main()
