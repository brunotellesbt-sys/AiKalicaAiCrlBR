"""Bind previous unboosted cups to their preserved tested ROMs."""
import hashlib,json,unittest
from pathlib import Path
from verify_pwt_balance import verify_report
from published_evidence import evidence_release,evidence_rom
ROOT=Path(__file__).resolve().parents[2]
class PWTBalanceTests(unittest.TestCase):
    def test_completed_edition_pool_combinations_match_tested_roms_and_are_unboosted(self):
        count=0
        directory,release=evidence_release('pwt-unboosted-0')
        for cap in (4,9):
            for difficulty in ('Normal','Hard'):
                edition=f'Gen1-{cap}-{difficulty}'
                sha=hashlib.sha256(evidence_rom(directory,f'Pokemon-Journey-{edition}.gba')).hexdigest()
                pools=release['pwt_balance_tested_pools'][f'Pokemon-Journey-{edition}.gba']
                self.assertTrue(pools)
                for pool in pools:
                    path=ROOT/'mods/hoenn/pwt-balance-validation'/edition/f'cup-{pool}'/'pwt-unboosted.json'
                    report=json.loads(path.read_text())
                    with self.subTest(edition=edition,pool=pool):
                        verify_report(report,sha,cap,difficulty=='Hard',pool)
                    count+=1
        self.assertGreaterEqual(count,4)
    def test_nonlevel_reference_and_native_regressions_match_validation_release(self):
        directory,release=evidence_release('nonlevel-moves')
        proof=next(p for p in release['proofs'] if p['kind']=='nonlevel-moves')
        r=json.loads((directory/proof['file']).read_text())
        self.assertEqual(r['rom_sha256'],release['parent_rom_sha256'])
        self.assertEqual(r['species_and_forms_checked'],1571)
        self.assertEqual(r['independently_checked_tables'],3142)
        self.assertEqual(r['egg_capacity'],22)
        self.assertTrue(r['form_moves_not_tms'] and r['tm_tutor_and_egg_lists_separate'])
        self.assertEqual(r['reference_sha256'],hashlib.sha256((ROOT/'tools/hoenn/data/nonlevel-moves.json').read_bytes()).hexdigest())
        self.assertFalse(r['differences'])

if __name__=='__main__':unittest.main()
