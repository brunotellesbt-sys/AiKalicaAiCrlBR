"""Require current native workshop evidence in every shipped edition."""
import hashlib,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class SpecialEncounterTests(unittest.TestCase):
    def test_four_roms_have_current_native_workshop_and_capture_proofs(self):
        release=json.loads((ROOT/'mods/hoenn/versions/versions.json').read_text())
        self.assertTrue(release['special_encounters_validated'])
        proofs=[p for p in release['proofs'] if p['kind']=='special-encounters']
        self.assertEqual(len(proofs),4)
        for proof in proofs:
            with self.subTest(edition=proof['target']):
                r=json.loads((ROOT/'mods/hoenn/versions'/proof['file']).read_text())
                self.assertEqual(r['rom_sha256'],hashlib.sha256((ROOT/'roms'/proof['target']).read_bytes()).hexdigest())
                self.assertTrue(r['actual_tv_capture_and_form_ui'])
                self.assertEqual(len(r['rotom_changes']),6)
                self.assertEqual(len(r['dex_locations']),21)
                self.assertEqual(r['event_only_families'],21)
                self.assertEqual(r['form_tools_available'],54)
                cases={c['case']:c for c in r['checks']}
                self.assertTrue(cases['rotom_tv_capture']['captured_base_form'])
                self.assertEqual(len(cases['deoxys_meteorite']['four_forms']),4)
                self.assertTrue(cases['keystone_installation']['consumed_once'])
                self.assertEqual(len(cases['fossil_restoration']['recipes']),15)
    def test_event_families_have_left_both_grass_guides(self):
        for cap in (4,9):
            text=(ROOT/'docs'/f'encontros-gen1-{cap}.md').read_text()
            for label in ('Rotom','Spiritomb','Unown','Porygon','Castform Normal','Gimmighoul Chest','Omanyte','Kabuto','Aerodactyl'):
                self.assertNotIn('| '+label+' |',text)
            self.assertIn('encontros-especiais-e-formas.md',text)

if __name__=='__main__':unittest.main()
