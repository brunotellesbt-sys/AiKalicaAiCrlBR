"""Exported ecology must preserve both games and all intended progression phases."""
import json
from pathlib import Path
import unittest

class WildWorldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((Path(__file__).resolve().parents[2]/'mods/choose-starting-city/manifest.json').read_text())['wild_world']

    def test_all_fire_red_exclusives_have_native_habitats(self):
        r=self.report
        available={s for chain in r['families'].values() for s in chain}
        self.assertTrue(set(r['fire_red_exclusive_wild_species'])<=available)
        placements={'SPECIES_SCYTHER':'SAFARI_ZONE','SPECIES_ELEKID':'POWER_PLANT','SPECIES_SHELLDER':'VERMILION','SPECIES_GROWLITHE':'POKEMON_MANSION','SPECIES_WOOPER':'ISLAND'}
        for species,habitat in placements.items():
            self.assertTrue(any(species in p['families'] and habitat in p['map'] for p in r['pools']),(species,habitat))

    def test_phase_and_limits(self):
        self.assertEqual(self.report['level_range'],[-5,2])
        self.assertEqual(self.report['phases'],{'0-2 badges':[1],'3-5 badges':[1,2],'6-8 badges':[2,3]})
        self.assertTrue(all(1<=len(p['families'])<=24 for p in self.report['pools']))
        self.assertGreater(len(self.report['pools']),200)
        self.assertEqual(self.report['families']['SPECIES_ODDISH'],['SPECIES_ODDISH','SPECIES_GLOOM','SPECIES_VILEPLUME'])
        self.assertEqual(self.report['families']['SPECIES_UNOWN'],['SPECIES_UNOWN']*3)
