"""Verify the released binary catalog, graphics, Fairy types and patch."""
import hashlib
import json
from pathlib import Path
import struct
import unittest
import zipfile
import zlib

from bps import apply
from extract import lz77, TYPES

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'mods/unova-catalog'
FAIRY = {35:('FAIRY','FAIRY'),36:('FAIRY','FAIRY'),39:('NORMAL','FAIRY'),40:('NORMAL','FAIRY'),122:('PSYCHIC','FAIRY'),173:('FAIRY','FAIRY'),174:('NORMAL','FAIRY'),175:('FAIRY','FAIRY'),176:('FAIRY','FLYING'),183:('WATER','FAIRY'),184:('WATER','FAIRY'),209:('FAIRY','FAIRY'),210:('FAIRY','FAIRY'),280:('PSYCHIC','FAIRY'),281:('PSYCHIC','FAIRY'),282:('PSYCHIC','FAIRY'),298:('NORMAL','FAIRY'),303:('STEEL','FAIRY'),439:('PSYCHIC','FAIRY'),468:('FAIRY','FLYING'),546:('GRASS','FAIRY'),547:('GRASS','FAIRY')}

class CatalogTests(unittest.TestCase):
    output = OUT
    rom_name = "LeafGreen-Journey-Unova"
    @classmethod
    def setUpClass(cls):
        cls.rom = (cls.output/(cls.rom_name+'.gba')).read_bytes()
        cls.manifest = json.loads((cls.output/'manifest.json').read_text())
        cls.catalog = json.loads((cls.output/'catalog.json').read_text())
        cls.ref = json.loads((cls.output/'debug-reference.json').read_text())
        cls.abi = cls.ref['layout']; cls.base = cls.ref['symbols']['gSpeciesInfo']-0x08000000

    def offset(self,row): return self.base+row['species_id']*self.abi['species_size']

    def test_patch_integrity_and_roundtrip(self):
        original = (ROOT/'Pokemon - Leaf Green Version (U) (V1.1).gba').read_bytes()
        patch = (self.output/(self.rom_name+'.bps')).read_bytes()
        for data,key in [(original,'original_sha256'),(patch,'patch_sha256'),(self.rom,'target_sha256')]:
            self.assertEqual(hashlib.sha256(data).hexdigest(),self.manifest[key])
        self.assertEqual(apply(patch,original),self.rom)
        self.assertEqual(self.rom[:0xC0],original[:0xC0])
        self.assertEqual(len(self.rom),32*1024*1024)

    def test_complete_donor_inventory(self):
        rows = self.catalog['catalog']
        self.assertEqual(len(rows),859)
        self.assertEqual(len({r['species_id'] for r in rows}),859)
        self.assertEqual({r['national_dex'] for r in rows},set(range(1,650)))
        self.assertEqual(sum(r['mega'] for r in rows),47)
        self.assertEqual(self.catalog['missing_base_species'],list(range(650,1026)))
        self.assertEqual(self.catalog['missing_mega_species'],['Diancie'])
        active = {i for i in range(self.abi['species_count']) if self.rom[self.base+i*self.abi['species_size']]}
        self.assertEqual(active,{r['species_id'] for r in rows})
        egg = self.base+self.abi['species_count']*self.abi['species_size']
        self.assertGreater(struct.unpack_from('<I',self.rom,egg+self.abi['species_front'])[0],0x08000000)

    def test_original_uploaded_patch_verified(self):
        patch = (self.output/'donor/unova_emerald_2_0_3.bps').read_bytes()
        report = json.loads((self.output/'donor-patch.json').read_text())
        self.assertEqual(hashlib.sha256(patch).hexdigest(),report['patch_sha256'])
        self.assertEqual(patch[:4],b'BPS1')
        source,target,checksum = struct.unpack('<III',patch[-12:])
        self.assertEqual(source,0x1f1c08fb)
        self.assertEqual(target,0x416153b8)
        self.assertEqual(checksum,zlib.crc32(patch[:-4]))

    def test_donor_stats_and_native_typings(self):
        for r in self.catalog['catalog']:
            p = self.offset(r)
            self.assertEqual(list(self.rom[p:p+6]),r['stats'],r['species'])
            types = list(self.rom[p+6:p+8])
            if r['species'] in self.manifest['imported']['corrected_fairy_species']:
                self.assertEqual(types,[TYPES.index(t)+1 for t in FAIRY[r['national_dex']]],r['species'])
            else: self.assertEqual(types,[TYPES.index(t)+1 for t in r['types']],r['species'])

    def test_all_donor_graphics_referenced_in_rom(self):
        with zipfile.ZipFile(self.output/'donor-assets.zip') as archive:
            self.assertEqual(hashlib.sha256((self.output/'donor-assets.zip').read_bytes()).hexdigest(),self.manifest['donor_asset_sha256'])
            for r in self.catalog['catalog']:
                p = self.offset(r)
                for kind in ['front','back']:
                    ptr = struct.unpack_from('<I',self.rom,p+self.abi['species_'+kind])[0]
                    actual,_ = lz77(self.rom,ptr)
                    expected,_ = lz77(archive.read(f'{r["donor_id"]}/{kind}.4bpp.lz'),0x08000000)
                    self.assertEqual(actual,expected,(r['species'],kind))
                ptr = struct.unpack_from('<I',self.rom,p+self.abi['species_palette'])[0]-0x08000000
                self.assertEqual(self.rom[ptr:ptr+32],archive.read(f'{r["donor_id"]}/palette.gbapal'),r['species'])

    def test_inherited_journey_and_no_new_encounters(self):
        self.assertEqual(len(self.manifest['homes']),16)
        self.assertEqual(len(self.manifest['open_world']['trainers']),49)
        self.assertEqual(self.manifest['open_world']['league_requires_badges'],8)
        self.assertEqual(self.manifest['open_world']['viridian_leader'],'BLUE')
        self.assertEqual(self.manifest['terrestrial_hm_changes']['counts'],{'strength_boulder':58,'rock_smash_rock':97,'flash_maps':2,'cut_tree':55,'victory_road_gate_cells_opened':8})
        prior = json.loads((ROOT/'mods/choose-starting-city/manifest.json').read_text())['wild_world']
        for key in ['pools','families','fire_red_exclusive_wild_species']:
            self.assertEqual(self.manifest['wild_world'][key],prior[key])

    def test_recorded_emulator_validation_matches_release(self):
        report = json.loads((self.output/'validation/results.json').read_text())
        self.assertEqual(report['rom_sha256'],self.manifest['target_sha256'])
        rows = report['checks']
        self.assertTrue(all(r['passed'] for r in rows))
        self.assertEqual(sum(r['check']=='native-pokemon-creation' for r in rows),859)
        self.assertEqual(sum(r['check']=='native-mega-evolution-and-reversion' for r in rows),47)
        self.assertEqual(sum(r['check']=='compiled-gym-party-levels' for r in rows),392)

if __name__ == '__main__': unittest.main()
