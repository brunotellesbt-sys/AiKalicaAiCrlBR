"""Static invariants and independent BPS verification for the exported journey ROM."""
import json
from pathlib import Path
import sys
import unittest
import zlib
import struct
from prepare import ROOT
sys.path.insert(0,str(ROOT/'tools/rom_hacks'))
from remove_hm_walls import BASE, Maps, sha
from test_remove_hm_walls import apply_bps

D=ROOT/'mods/choose-starting-city'

class JourneyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads((D/'manifest.json').read_text())
        cls.ref=json.loads((D/'debug-reference.json').read_text())
        cls.rom=(D/'LeafGreen-Choose-Starting-City.gba').read_bytes()
        cls.source=(ROOT/'Pokemon - Leaf Green Version (U) (V1.1).gba').read_bytes()
        cls.config=json.loads((ROOT/'tools/journey/homes.json').read_text())

    def test_bps_independent_roundtrip_and_hashes(self):
        patch=(D/'LeafGreen-Choose-Starting-City.bps').read_bytes()
        self.assertEqual(sha(self.source),self.manifest['original_sha256'])
        self.assertEqual(sha(self.rom),self.manifest['target_sha256'])
        self.assertEqual(sha(patch),self.manifest['patch_sha256'])
        self.assertEqual(apply_bps(self.source,patch),self.rom)
        self.assertEqual(self.rom[:0xc0],self.source[:0xc0])
        self.assertEqual(len(self.rom),16*1024*1024)

    def test_curated_house_whitelist_and_progression_exclusions(self):
        homes=[h['house'] for h in self.manifest['homes']]
        self.assertEqual(homes,[house for city in self.config['cities'] for house in city['houses']])
        self.assertEqual(len(homes),16)
        self.assertTrue(all(len(c['houses'])==1 for c in self.config['cities']))
        self.assertEqual([h['index'] for h in self.manifest['homes']],list(range(1,17)))
        self.assertTrue(set(homes).isdisjoint(self.config['excluded']))
        self.assertEqual(len({h['city'] for h in self.manifest['homes']}),16)
        self.assertTrue(all(1<=h['people']<=3 and h['roles'][0]==1 for h in self.manifest['homes']))

    def test_original_map_ids_and_non_home_headers_stay_available(self):
        old=json.loads((ROOT/'mods/no-hm-walls/reference.json').read_text())
        self.assertEqual(self.ref['groups'][:len(old['groups'])],old['groups'])
        # The runtime replacement uses only the selected home. Essential story maps
        # retain their original map identity and no house replacement table entry.
        essential=['LavenderTown_VolunteerPokemonHouse','FuchsiaCity_WardensHouse','CeladonCity_Condominiums_1F','CeruleanCity_House2']
        for name in essential:
            self.assertIn(name,self.ref['map_symbols'])
            self.assertNotIn(name,[h['house'] for h in self.manifest['homes']])

    def test_combined_mod_keeps_hm_obstacle_counts(self):
        report=self.manifest['terrestrial_hm_changes']
        self.assertEqual(report['counts']['cut_tree'],55)
        self.assertEqual(report['counts']['rock_smash_rock'],97)
        self.assertEqual(report['counts']['strength_boulder'],58)
        self.assertEqual(report['counts']['flash_maps'],2)
        self.assertEqual(report['counts']['victory_road_gate_cells_opened'],8)
        self.assertEqual(report['target_sha256'],sha(self.rom))

    def test_surf_waterfall_tiles_preserved(self):
        original=json.loads((ROOT/'mods/no-hm-walls/reference.json').read_text())
        for old,new in zip(original['attribute_tables'],self.ref['attribute_tables']):
            self.assertEqual(old['symbol'],new['symbol'])
            start,other,size=old['address']-BASE,new['address']-BASE,old['count']*4
            self.assertEqual(self.source[start:start+size],self.rom[other:other+size],old['symbol'])

    def test_exported_overlay_matches_reviewed_files(self):
        for name,digest in self.manifest['overlay_hashes'].items():
            self.assertEqual(sha((ROOT/'tools/journey'/name).read_bytes()),digest,name)

if __name__=='__main__':unittest.main()
