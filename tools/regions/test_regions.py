"""Verify the complete release and the exclusion of forbidden battle mechanics."""
import hashlib,json,struct,sys,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/unova'))
import test_catalog as unova_tests
from extract import lz77

class RegionsTests(unova_tests.CatalogTests):
    output=ROOT/'mods/all-regions'
    rom_name='LeafGreen-Journey-AllRegions'

    def test_complete_donor_inventory(self):
        rows=self.catalog['catalog'];ids={r['species_id'] for r in rows}
        self.assertEqual(len(rows),1482);self.assertEqual(len(ids),len(rows))
        self.assertEqual({r['national_dex'] for r in rows},set(range(1,1026)))
        self.assertEqual(sum(r['mega'] for r in rows),48)
        self.assertEqual(self.catalog['missing_base_species'],[])
        self.assertEqual(len(self.catalog['missing_base_species_from_uploads']),47)
        self.assertFalse(any('_GMAX' in r['species'] or 'ETERNAMAX' in r['species'] for r in rows))
        active={i for i in range(self.abi['species_count']) if self.rom[self.base+i*self.abi['species_size']]}
        self.assertEqual(active,ids)
        self.assertIn('SPECIES_DIANCIE_MEGA',{r['species'] for r in rows})

    def test_original_uploaded_patch_verified(self):
        sources=self.catalog['sources']
        self.assertEqual({s['tag'] for s in sources},{'sun','swsh','xy','scarlet'})
        self.assertTrue(all(len(s['sha256'])==64 for s in sources))
        inv=json.loads((self.output/'donor-inventory.json').read_text())
        for source in sources:self.assertTrue(inv['donor_inventories'][source['tag']])

    def test_all_donor_graphics_referenced_in_rom(self):
        with zipfile.ZipFile(self.output/'donor-assets.zip') as z:
            self.assertEqual(hashlib.sha256((self.output/'donor-assets.zip').read_bytes()).hexdigest(),self.manifest['donor_asset_sha256'])
            for r in self.catalog['catalog']:
                p=self.offset(r)
                for kind in ['front','back']:
                    ptr=struct.unpack_from('<I',self.rom,p+self.abi['species_'+kind])[0]
                    if r.get('native_graphics'):
                        off=ptr-0x08000000
                        self.assertTrue(0<=off<len(self.rom)-16)
                        self.assertIn(self.rom[off],[1,2,3,4,5,6]) # native SMOL format
                    else:
                        actual,_=lz77(self.rom,ptr)
                        self.assertGreaterEqual(len(actual),2048,r['species'])
                        expected,_=lz77(z.read(f'{r["donor_id"]}/{kind}.4bpp.lz'),0x08000000)
                        self.assertEqual(actual,expected,(r['species'],kind))
                ptr=struct.unpack_from('<I',self.rom,p+self.abi['species_palette'])[0]-0x08000000
                self.assertTrue(0<=ptr<=len(self.rom)-32)
                if not r.get('native_graphics'):self.assertEqual(self.rom[ptr:ptr+32],z.read(f'{r["donor_id"]}/palette.gbapal'),r['species'])

    def test_recorded_emulator_validation_matches_release(self):
        report=json.loads((self.output/'validation/results.json').read_text());rows=report['checks']
        self.assertEqual(report['rom_sha256'],self.manifest['target_sha256']);self.assertTrue(all(r['passed'] for r in rows))
        self.assertEqual(sum(r['check']=='native-pokemon-creation' for r in rows),1482)
        self.assertEqual(sum(r['check']=='native-mega-evolution-and-reversion' for r in rows),48)
        self.assertEqual(sum(r['check']=='compiled-gym-party-levels' for r in rows),392)
        self.assertEqual(sum(r['check']=='excluded-battle-mechanic-unavailable' for r in rows),8)

    def test_form_and_evolution_targets_reference_active_species(self):
        active={r['species_id'] for r in self.catalog['catalog']}
        for r in self.catalog['catalog']:
            p=self.offset(r)
            for key,stride,target_offset,terminator in [('species_form_ids',2,0,0xFFFF),('species_form_changes',self.abi['form_change_size'],2,0),('species_evolutions',self.abi['evolution_size'],4,0xFFFF)]:
                ptr=struct.unpack_from('<I',self.rom,p+self.abi[key])[0]
                if not ptr:continue
                for n in range(256):
                    off=ptr-0x08000000+n*stride
                    method=struct.unpack_from('<H',self.rom,off)[0]
                    if method==terminator:break
                    target=struct.unpack_from('<H',self.rom,off+target_offset)[0]
                    if key=='species_form_changes' and target==0:
                        # Native FAINT/END_BATTLE restore the remembered party species.
                        self.assertIn(method,[5,self.abi['end_battle_method']])
                    else:self.assertTrue(target in active,(r['species'],key,target))
                else:self.fail('Unterminated table '+r['species'])

    def test_regional_variants_have_correct_native_types(self):
        byname={r['species']:r for r in self.catalog['catalog']}
        for name,types in [('SPECIES_SYLVEON',[19,19]),('SPECIES_DIANCIE_MEGA',[6,19]),('SPECIES_ZORUA_HISUI',[1,8])]:
            p=self.offset(byname[name]);self.assertEqual(list(self.rom[p+6:p+8]),types)

if __name__=='__main__':unittest.main()
