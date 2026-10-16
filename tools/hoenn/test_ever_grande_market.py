"""Current-ROM native proofs cover gifts, shopping and the restored city marker."""
import json
import unittest
from pathlib import Path
from verify_versions import verify

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'mods/hoenn/ever-grande-market-validation'

class EverGrandeMarket(unittest.TestCase):
    def test_each_edition_walks_homes_and_buys_at_the_stall(self):
        release=verify(ROOT/'mods/hoenn/versions')
        self.assertEqual(release['validation_scope'],'ever-grande-market')
        expected={r['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba'):r['sha256'] for r in release['variants']}
        expected['TESTE']=json.loads((ROOT/'roms/rom-de-teste/review.json').read_text())['sha256']
        for edition,sha in expected.items():
            with self.subTest(edition=edition):
                r=json.loads((OUT/edition/'ever-grande-market.json').read_text())
                self.assertEqual(r['rom_sha256'],sha)
                self.assertEqual([g['item'] for g in r['gifts']],['ITEM_FULL_RESTORE','ITEM_MAX_REVIVE'])
                self.assertTrue(all(g['bag_full_preserves_gift'] and g['repeat_talk_no_duplicate'] and g['controller_entry_and_exit'] for g in r['gifts']))
                self.assertTrue(r['market_actual_purchase'] and r['insufficient_money_rejected'])
                self.assertEqual(r['market_price'],200000)
                self.assertTrue(r['stock_specific_price_reset'] and r['save_continue_preserves_gifts_and_purchase'])
                self.assertTrue(r['compiled_atlas_and_zoom_match_source'] and r['sootopolis_city_red'])

    def test_unrelated_terrain_is_preserved_and_overlay_replays(self):
        r=json.loads((OUT/'source.json').read_text())
        self.assertTrue(r['independent_replay'] and r['idempotent'])
        self.assertGreater(r['unrelated_files_preserved'],30000)
        self.assertTrue(r['all_surf_maps_unchanged'] and r['original_city_events_and_connections_preserved'])

if __name__=='__main__':unittest.main()
