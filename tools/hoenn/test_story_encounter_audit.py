"""Shared script references, cycles and dynamic encounter limits."""
import json
from pathlib import Path
import tempfile
import unittest
from audit_story_encounters import audit

class StoryEncounterAudit(unittest.TestCase):
    def fixture(self, source):
        (source / 'data/scripts').mkdir(parents=True)
        (source / 'src').mkdir()
        (source / '.journey-ecology').write_text(json.dumps({'locations_data': [dict(section='MAPSEC_BERRY_FOREST', families=[dict(root=96, name='SPECIES_DROWZEE', species=[dict(name='SPECIES_HYPNO')])])]}))
        for name, section in [('Forest', 'MAPSEC_BERRY_FOREST'), ('Other', 'MAPSEC_OTHER')]:
            path = source / 'data/maps' / name; path.mkdir(parents=True)
            (path / 'map.json').write_text(json.dumps(dict(id='MAP_' + name.upper(), region_map_section=section, object_events=[dict(script='Entry')], coord_events=[], bg_events=[])))
            (path / 'scripts.inc').write_text(name + '_MapScripts::\n\t.byte 0\n')
        (source / 'data/scripts/shared.inc').write_text('Entry::\n\tcall Shared\n\tend\nShared::\n\tsetwildbattle SPECIES_HYPNO, 30\n\tgoto Entry\nDead::\n\tsetwildbattle SPECIES_MEW, 5\n\tend\n')

    def test_shared_encounter_is_resolved_for_each_map_without_infinite_cycle(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp); self.fixture(source); r = audit(source)
            self.assertEqual(len(r['records']), 2)
            self.assertEqual({x['map'] for x in r['records']}, {'Forest', 'Other'})
            self.assertEqual([x['map'] for x in r['ordinary_habitat_mismatches']], ['Other'])
            self.assertTrue(all(x['script_chain'] == ['Entry', 'Shared'] for x in r['records']))

    def test_unreferenced_and_commented_encounters_are_not_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp); self.fixture(source)
            p = source / 'data/scripts/shared.inc'; p.write_text(p.read_text().replace('setwildbattle SPECIES_HYPNO, 30', '@ setwildbattle SPECIES_HYPNO, 30'))
            self.assertEqual(audit(source)['records'], [])

    def test_variable_selected_species_remains_unresolved(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp); self.fixture(source)
            p = source / 'data/scripts/shared.inc'; p.write_text(p.read_text().replace('SPECIES_HYPNO', 'VAR_0x8004'))
            r = audit(source); self.assertEqual(len(r['dynamic_species']), 2)
            self.assertEqual(r['records'], []); self.assertFalse(r['full_fixed_encounter_coverage'])

    def test_latest_overlay_changes_the_comparison_habitat(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp); self.fixture(source)
            p = source / '.journey-ecology'; r = json.loads(p.read_text()); r['locations_data'][0]['section'] = 'MAPSEC_OTHER'
            (source / '.journey-tower-habitats').write_text(json.dumps(r))
            self.assertEqual([x['map'] for x in audit(source)['ordinary_habitat_mismatches']], ['Forest'])

    def test_source_selected_sudowoodo_callback_is_included(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp); self.fixture(source)
            p = source / 'data/maps/Forest'; p.rename(source / 'data/maps/BattleFrontier_OutsideEast')
            (source / 'src/item_use.c').write_text('ScriptContext_SetupScript(BattleFrontier_OutsideEast_EventScript_WaterSudowoodo);')
            with (source / 'data/scripts/shared.inc').open('a') as stream:
                stream.write('BattleFrontier_OutsideEast_EventScript_WaterSudowoodo::\n\tsetwildbattle SPECIES_SUDOWOODO, 40\n\tend\n')
            r = audit(source); self.assertTrue(any(x['species'] == 'SPECIES_SUDOWOODO' for x in r['records']))
            self.assertIn('src/item_use.c', r['input_sha256'])

if __name__ == '__main__': unittest.main()
