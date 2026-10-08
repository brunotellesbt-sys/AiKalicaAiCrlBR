"""Catalog coverage and unique habitats required by the connected journey."""
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[2]

class HabitatRequirements(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text())
        cls.plan = json.loads((ROOT/'mods/hoenn/integration-validation/habitats-preparation.json').read_text())

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
        self.assertEqual(sum(a['family_count']==5 for a in locations), 88)
        self.assertEqual(sum(a['family_count']==4 for a in locations), 1)

    def test_native_encounters_and_national_dex_on_audited_rom(self):
        runtime = json.loads((ROOT/'mods/hoenn/integration-validation/wild.json').read_text())
        audit = json.loads((ROOT/'mods/hoenn/integration-validation/native-catalog.json').read_text())
        self.assertTrue(runtime['passed'])
        self.assertEqual(runtime['rom_sha256'], audit['rom_sha256'])
        self.assertTrue(runtime['national_dex_from_initial_pokedex'])
        self.assertEqual(len(runtime['catalog_habitats']), len(self.plan['locations_data']))
        permitted = {a['maps'][0]: {s['id'] for f in a['families'] for s in f['species']}
                     for a in self.plan['locations_data']}
        for area in runtime['catalog_habitats']:
            self.assertTrue(area['observed'])
            self.assertLessEqual(set(area['observed']), permitted[area['map']])

    def test_rare_family_slots_do_not_exceed_common_families(self):
        for area in self.plan['locations_data']:
            for chances in area['slot_chances'].values():
                self.assertEqual(sum(chances.values()), 100)
                for rare in area['families']:
                    for common in area['families']:
                        if rare['rarity'] > common['rarity']:
                            self.assertLessEqual(chances[rare['name']], chances[common['name']], area['section'])

if __name__ == '__main__':
    unittest.main()
