"""Preserve scene/scripts while eliminating the seven retired ferry targets."""
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from atlas_surf_ports import stage
from test_atlas_surf_layer import Overlay


class PortArrivalTests(unittest.TestCase):
    def fixture(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        layer=Overlay(Path(temp.name));ports=[];maps={};identities={}
        c=['static const s8 sSeag[][4] = {','[SEAGALLOP_OTHER] = {1,2,3,4},']
        scripts=['UnchangedNPC::\n\tmsgbox SameMessage, MSGBOX_DEFAULT\n\tend']
        for i,island in enumerate(('One','Two','Three','Four','Five','Six','Seven'),2):
            old=island+'Island_Harbor_Frlg';new='Town'+island
            old_id='MAP_OLD_'+island.upper();new_id='MAP_TOWN_'+island.upper()
            maps[old]=dict(id=old_id);maps[new]=dict(id=new_id);identities[new]=(4<<8)|i
            ports.append(dict(island=island,boarding=dict(dry=[new,i,6]),dry_terrain=dict(height=3),water_terrain=dict(height=1)))
            c.append(f'[SEAGALLOP_{island.upper()}_ISLAND] = {{MAP_GROUP({old_id}), MAP_NUM({old_id}), 0x08, 0x05}},')
            scripts.append(f'Journey_Ferry_Destination{i}::\n\tmsgbox SameMessage, MSGBOX_DEFAULT\n\twarp {old_id}, 8, 5\n\twaitstate\n\tend')
        c.append('};\nvoid Scene(void) { PreserveNativeFerry(); }')
        layer.parent('src/seagallop.c','\n'.join(c).encode())
        layer.parent('data/scripts/journey_campaign_gates.inc','\n'.join(scripts).encode())
        return layer,SimpleNamespace(maps=maps,identities=identities),ports

    def test_only_authentic_seven_arrivals_change(self):
        layer,inputs,ports=self.fixture()
        with patch('atlas_surf_ports.current_ports',return_value=ports):result=stage(layer,inputs)
        self.assertEqual(len(result['arrivals']),7)
        c=layer.outputs['src/seagallop.c'].decode();scripts=layer.outputs['data/scripts/journey_campaign_gates.inc'].decode()
        self.assertIn('[SEAGALLOP_OTHER] = {1,2,3,4},',c)
        self.assertIn('void Scene(void) { PreserveNativeFerry(); }',c)
        self.assertIn('UnchangedNPC::\n\tmsgbox SameMessage, MSGBOX_DEFAULT\n\tend',scripts)
        self.assertEqual(scripts.count('SameMessage'),8)
        self.assertEqual(scripts.count('\twaitstate'),7)
        for i,port in enumerate(ports,2):
            self.assertIn(f'\twarp MAP_TOWN_{port["island"].upper()}, {i}, 6',scripts)
            self.assertNotIn('MAP_OLD_'+port['island'].upper(),c+scripts)
        self.assertFalse(result['native_validated'])

    def test_incomplete_piers_and_signed_overflow_rejected(self):
        layer,inputs,ports=self.fixture()
        with patch('atlas_surf_ports.current_ports',return_value=ports[:6]):
            with self.assertRaisesRegex(ValueError,'all seven'):stage(layer,inputs)
        inputs.identities['TownOne']=128<<8
        with patch('atlas_surf_ports.current_ports',return_value=ports):
            with self.assertRaisesRegex(ValueError,'signed byte'):stage(layer,inputs)
        self.assertFalse(layer.outputs)

    def test_parent_drift_does_not_silently_retarget_something_else(self):
        layer,inputs,ports=self.fixture()
        p='src/seagallop.c'
        layer.parent(p,(layer.source/p).read_bytes().replace(b'0x08, 0x05',b'0x09, 0x05',1))
        with patch('atlas_surf_ports.current_ports',return_value=ports):
            with self.assertRaisesRegex(ValueError,'row changed'):stage(layer,inputs)


if __name__=='__main__':
    unittest.main()
