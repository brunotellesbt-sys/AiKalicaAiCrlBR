"""Catalog coverage and unique habitats required by the connected journey."""
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[2]

class HabitatRequirements(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text())
        cls.plan = json.loads((ROOT/'mods/hoenn/integration-validation/ecology-preparation.json').read_text())

    def test_every_ordinary_national_species_has_one_habitat(self):
        canonical = {int(i) for i in self.catalog['canonical_species'].values()}
        special = set(self.catalog['special_species'])
        found = []
        for area in self.plan['locations_data']:
            found.extend(s['id'] for f in area['families'] for s in f['species'] if s['id'] in canonical)
        self.assertEqual(set(found), canonical-special)
        self.assertEqual(len(found), len(set(found)))
        self.assertEqual(len(found), 920)

    def test_no_legendary_mythical_or_ultra_beast_in_ordinary_habitats(self):
        species = self.catalog['species']
        for area in self.plan['locations_data']:
            for family in area['families']:
                for mon in family['species']:
                    self.assertFalse(species[str(mon['id'])]['special'], mon['name'])

    def test_fixed_balanced_family_counts_without_duplicates(self):
        locations = self.plan['locations_data']
        roots = [f['root'] for a in locations for f in a['families']]
        self.assertEqual(len(roots), len(set(roots)))
        self.assertEqual(len(roots), 444)
        self.assertEqual(sum(a['family_count']==5 for a in locations), 18)
        self.assertEqual(sum(a['family_count']==4 for a in locations), 79)
        self.assertEqual(sum(a['family_count']==1 for a in locations), 38)
        self.assertEqual(self.plan['type_ids']['TYPE_WATER'], 12)
        self.assertEqual(self.plan['type_ids']['TYPE_GRASS'], 13)

    def test_native_encounters_and_national_dex_on_audited_rom(self):
        runtime = json.loads((ROOT/'mods/hoenn/integration-validation/wild.json').read_text())
        audit = json.loads((ROOT/'mods/hoenn/integration-validation/native-catalog.json').read_text())
        self.assertTrue(runtime['passed'])
        self.assertEqual(runtime['rom_sha256'], audit['rom_sha256'])
        self.assertTrue(runtime['national_dex_from_initial_pokedex'])
        self.assertEqual(len(runtime['catalog_habitats']), len(self.plan['locations_data']))
        permitted = {m:set(ids) for m,ids in self.plan['map_species'].items()}
        for area in runtime['catalog_habitats']:
            self.assertTrue(area['observed'])
            self.assertLessEqual(set(area['observed']), permitted[area['map']])

    def test_aquatic_pools_have_only_water_families(self):
        family_by_root = {f['root']:f for area in self.plan['locations_data'] for f in area['families']}
        for pool in self.plan['pools']:
            if pool['area'] in [1,3]:
                for root in pool['roots']:
                    self.assertIn(self.plan['type_ids']['TYPE_WATER'], family_by_root[root]['types'])
        # These checks catch the previous enum offset error directly.
        self.assertIn(self.plan['type_ids']['TYPE_GRASS'], self.catalog['species']['1']['types'])
        self.assertIn(self.plan['type_ids']['TYPE_FIRE'], self.catalog['species']['4']['types'])
        self.assertIn(self.plan['type_ids']['TYPE_WATER'], self.catalog['species']['7']['types'])

if __name__ == '__main__':
    unittest.main()
