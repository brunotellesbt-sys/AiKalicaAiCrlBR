"""Validate imported competitive references and supported tournament spreads."""
import hashlib,json
from pathlib import Path
import unittest
from import_pwt_builds import stable_symbols
HERE=Path(__file__).resolve().parent

class PWTBuildReferenceTests(unittest.TestCase):
    def test_historical_spelling_aliases_are_resolved_deterministically(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'moves.h'
            path.write_text('#define MOVE_SOFTBOILED MOVE_SOFT_BOILED\n#define MOVE_SOLARBEAM MOVE_SOLAR_BEAM\n')
            a=stable_symbols(Path(directory),'MOVE','moves.h')
            path.write_text('\n'.join(reversed(path.read_text().splitlines()))+'\n')
            self.assertEqual(stable_symbols(Path(directory),'MOVE','moves.h'),a)
            self.assertEqual(a['softboiled'],'MOVE_SOFT_BOILED')
            self.assertEqual(a['solarbeam'],'MOVE_SOLAR_BEAM')
    def test_reference_is_pinned_and_player_move_policy_is_explicit(self):
        data=json.loads((HERE/'data/pwt-builds.json').read_text())
        original=json.loads((HERE/'data/competitive-profiles.json').read_text())
        self.assertEqual(len(data['reference_commit']),40)
        self.assertEqual(set(data['reference_sha256']),set(original['reference_sha256']))
        self.assertTrue(data['player_moves_preserved'])
        self.assertTrue(data['ou_prioritized'])

    def test_spreads_have_legal_budget_and_frozen_provenance(self):
        data=json.loads((HERE/'data/pwt-builds.json').read_text())
        self.assertGreater(len(data['records']),1000)
        self.assertTrue(any(r['zero_speed'] for r in data['records']))
        for row in data['records']:
            with self.subTest(species=row['species'],set=row['set']):
                self.assertEqual(sum(row['evs']),510)
                self.assertTrue(all(0<=ev<=252 for ev in row['evs']))
                self.assertEqual(len(row['moves']),4)
                self.assertTrue(all(len(group)<=6 for group in row['moves']))
                self.assertTrue(row['nature'].startswith('NATURE_'))
                self.assertTrue(row['source'] and row['set'])

    def test_portraits_and_walking_sheets_match_acquisition_hashes(self):
        directory=HERE/'data/pwt';references=json.loads((directory/'sources.json').read_text())
        for record in references['portraits']:
            if 'converted' in record:
                self.assertEqual(hashlib.sha256((directory/record['converted']).read_bytes()).hexdigest(),record['converted_sha256'])
        walking=json.loads((directory/'walking/sources.json').read_text())['walking']
        for record in walking:
            if record['status']=='acquired':
                self.assertEqual(hashlib.sha256((directory/'walking'/record['converted']).read_bytes()).hexdigest(),record['converted_sha256'])

if __name__=='__main__':unittest.main()
