"""Check identities, shared gyms and the two edition-specific entrant pools."""
import unittest
from pwt_catalog import eligible, load

class TournamentCatalogTests(unittest.TestCase):
    def test_shared_gym_leaders_have_independent_teams(self):
        rows = {row['key']: row for row in load()}
        for pair in [('TATE','LIZA'),('CILAN','CHILI'),('CHILI','CRESS'),
                     ('DRAYDEN','IRIS'),('BEA','ALLISTER'),('GORDIE','MELONY'),
                     ('OPAL','BEDE'),('PIERS','MARNIE'),('WALLACE','JUAN'),
                     ('KOGA','JANINE'),('GIOVANNI','BLUE')]:
            with self.subTest(pair=pair):
                a,b = [rows[key] for key in pair]
                self.assertNotEqual(a['id'],b['id'])
                self.assertNotEqual(a['species'],b['species'])
                self.assertEqual(len(a['species']),6)
                self.assertEqual(len(b['species']),6)

    def test_global_pools_include_every_eligible_identity_once(self):
        rows = load()
        for cap in (4,9):
            pool = eligible(rows,cap)
            self.assertEqual(len({r['id'] for r in pool}),len(pool))
            self.assertEqual({r['id'] for r in pool},
                             {r['id'] for r in rows if r['generations']==[0] or min(r['generations'])<=cap})
            self.assertTrue({'ASH','EREN','LUFFY'} <= {r['key'] for r in pool})
            for gen in range(1,cap+1):
                cup = eligible(rows,cap,gen)
                self.assertTrue(all(r['generations']==[0] or gen in r['generations'] for r in cup))
                self.assertTrue({'ASH','EREN','LUFFY'} <= {r['key'] for r in cup})

    def test_additions_preserve_the_reference_party(self):
        for row in load():
            with self.subTest(trainer=row['name']):
                self.assertEqual(row['species'][:len(row['original'])],row['original'])
                self.assertEqual(row['species'][len(row['original']):],row['additions'])
                self.assertTrue(row['source_game'])

if __name__ == '__main__':
    unittest.main()
