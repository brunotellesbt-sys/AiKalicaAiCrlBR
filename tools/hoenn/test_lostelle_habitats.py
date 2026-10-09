"""Unique story/wild family habitats and complete native catalog regression."""
import csv
import json
from pathlib import Path
import unittest
from prepare_ecology import LAND_RATES

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'mods/hoenn/lostelle-habitat-validation'

class LostelleHabitats(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prep = json.loads((DIR / 'preparation/preparation.json').read_text())
        cls.old = json.loads((ROOT / 'mods/hoenn/integration-validation/ecology-preparation.json').read_text())
        cls.native = json.loads((DIR / 'lostelle-habitats.json').read_text())
        cls.wild = json.loads((DIR / 'wild.json').read_text())
        cls.replay = json.loads((DIR / 'preparation/reproduction.json').read_text())

    def test_story_and_random_hypno_share_one_habitat(self):
        for root, section in [(96, 'MAPSEC_BERRY_FOREST'), (451, 'MAPSEC_MT_PYRE')]:
            owned = [h['section'] for h in self.prep['locations_data'] if any(f['root'] == root for f in h['families'])]
            self.assertEqual(owned, [section])
        self.assertTrue(self.prep['original_hypno_rescue_script_preserved'])
        self.assertIn('data/maps/ThreeIsland_BerryForest_Frlg/scripts.inc', self.prep['preserved_native_sha256'])

    def test_other_families_counts_and_full_catalog_are_preserved(self):
        before = {f['root']: (h['section'], f) for h in self.old['locations_data'] for f in h['families']}
        after = {f['root']: (h['section'], f) for h in self.prep['locations_data'] for f in h['families']}
        self.assertEqual(len(after), 444); self.assertEqual(before.keys(), after.keys())
        for root in before:
            self.assertEqual(before[root][1], after[root][1])
            if root not in [96, 451]: self.assertEqual(before[root][0], after[root][0])
        self.assertEqual([h['family_count'] for h in self.old['locations_data']],
                         [h['family_count'] for h in self.prep['locations_data']])

    def test_aquatic_and_unaffected_pools_are_identical(self):
        maps = {m for h in self.prep['locations_data'] if h['section'] in ['MAPSEC_BERRY_FOREST', 'MAPSEC_MT_PYRE'] for m in h['maps']}
        old = {(p['map'], p['area']): p for p in self.old['pools']}
        for p in self.prep['pools']:
            if p['map'] not in maps or p['area'] in [1, 3]: self.assertEqual(p, old[p['map'], p['area']])

    def test_native_dex_membership_all_maps_and_three_evolution_phases(self):
        self.assertTrue(self.native['passed'])
        self.assertEqual(self.native['rom_sha256'], self.replay['rom_sha256'])
        expected = 2 * sum(len(h['maps']) for h in self.prep['locations_data'])
        self.assertEqual(len(self.native['dex_membership']), expected)
        target_maps = {m for h in self.prep['locations_data'] if h['section'] in ['MAPSEC_BERRY_FOREST', 'MAPSEC_MT_PYRE'] for m in h['maps']}
        self.assertEqual(len(self.native['phase_cases']), 3 * len(target_maps))
        for c in self.native['phase_cases']:
            root = c['root']; self.assertEqual(c['observed'], [root] if c['phase'] == 0 else [root, root + 1] if c['phase'] == 1 else [root + 1])

    def test_complete_native_habitat_and_wild_level_regression(self):
        r = self.wild; self.assertTrue(r['passed'])
        self.assertEqual(r['rom_sha256'], self.replay['rom_sha256'])
        self.assertEqual(len(r['catalog_habitats']), 135)
        for h in r['catalog_habitats']:
            self.assertTrue(h['observed']); self.assertLessEqual(set(h['observed']), set(self.prep['map_species'][h['map']]))
        self.assertTrue(r['national_dex_from_initial_pokedex']); self.assertTrue(r['aquatic_branches_verified'])
        self.assertEqual(r['phase_cases'], 6); self.assertEqual(len(r['level_cases']), 5)

    def test_documented_species_match_native_habitats(self):
        with (ROOT / 'mods/hoenn/pokemon-locations.csv').open() as stream:
            rows = {int(r['internal_id']): r for r in csv.DictReader(stream)}
        for species, habitat in [(96, 'Berry Forest'), (97, 'Berry Forest'), (451, 'Mt Pyre'), (452, 'Mt Pyre')]:
            self.assertEqual(rows[species]['habitat'], habitat)
        self.assertEqual(len([r for r in rows.values() if r['category'] == 'comum']), 920)

    def test_rarer_families_keep_lower_land_chances(self):
        for habitat in self.prep['locations_data']:
            if habitat['section'] not in ['MAPSEC_BERRY_FOREST', 'MAPSEC_MT_PYRE']: continue
            for pool in self.prep['pools']:
                if pool['map'] not in habitat['maps'] or pool['area'] != 0: continue
                chances = {f['root']: sum(p for r, p in zip(pool['roots'], LAND_RATES) if r == f['root']) for f in habitat['families']}
                self.assertEqual(sum(chances.values()), 100)
                for a in habitat['families']:
                    for b in habitat['families']:
                        if a['weight'] < b['weight']: self.assertLessEqual(chances[a['root']], chances[b['root']])

    def test_overlay_replay_and_english_are_verified(self):
        self.assertTrue(self.replay['passed']); self.assertTrue(self.replay['deterministic_replay']); self.assertTrue(self.replay['idempotent'])
        english = json.loads((DIR / 'english-audit.json').read_text())
        self.assertTrue(english['passed']); self.assertEqual(english['rom_sha256'], self.replay['rom_sha256'])
        self.assertEqual(set(self.prep['prepared_sha256']), {'src/data/wild_encounters.json', 'include/journey_wild_data.h', 'include/journey_habitat_data.h'})

if __name__ == '__main__': unittest.main()
