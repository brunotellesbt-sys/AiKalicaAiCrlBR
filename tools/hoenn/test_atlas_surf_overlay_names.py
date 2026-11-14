"""Audit staged native terrain and labels without materializing or changing art."""
import json
import unittest

from atlas_surf_geometry import plan_geometry
from atlas_surf_layer import stage_geometry
from atlas_surf_names import stage as stage_names
from atlas_surf_overlay import OverlaySource
from atlas_surf_truth import ART_ARRAYS,decode_atlas
import test_atlas_surf_source_inventory as fixtures


class OverlayAndNamesTests(unittest.TestCase):
    fixture=fixtures.NativeInventoryTests.fixture

    def test_staged_maps_and_banks_are_visible_without_writing_parent(self):
        root,layer=self.fixture({'Old':('emerald',2,1,[0x1001,0x1401])})
        layer.parent('data/event_scripts.s',b'original::\n')
        plan=plan_geometry([(3,3)])
        donors={row['name']:dict(map='Old',water_tile=[0,0],reef_tile=[1,0]) for row in plan['chunks']}
        plan,_=stage_geometry(layer,plan,donors)
        view=OverlaySource(layer);name=plan['chunks'][0]['name']
        self.assertIn(name,view.maps)
        self.assertTrue(view.water(name,1,1))
        self.assertFalse(view.water(name,0,0))
        self.assertFalse((root/f'data/maps/{name}/map.json').exists())
        view.assert_unchanged()
        layer.outputs[f'data/maps/{name}/map.json']+=b' '
        with self.assertRaisesRegex(ValueError,'changed while auditing'):view.assert_unchanged()

    def test_names_preserve_old_registry_and_all_four_art_arrays(self):
        root,layer=self.fixture({'Old':('emerald',2,1,[0x1001,0x1401])})
        layer.parent('data/event_scripts.s',b'original::\n')
        path='data/maps/Old/map.json'
        mapping=json.loads((root/path).read_text());mapping['region_map_section']='MAPSEC_TEST';layer.parent(path,mapping)
        old='    {(MAP_GROUP(MAP_OLD)<<8)|MAP_NUM(MAP_OLD), MAPSEC_TEST, 10, 10, COMPOUND_STRING("OLD COAST")},\n'
        header='\n'.join('static unsigned short '+key+'[] = {'+','.join(map(str,values))+'};'
                         for key,values in zip(ART_ARRAYS,([0x11]*32,[0]*1024,list(range(16)),[0])))
        header+='\nstatic const struct Point sWorldPoints[] = {\n'+old+'};\n'
        layer.parent('src/data/journey_world_map.h',header.encode())
        plan=plan_geometry([(3,3)])
        plan,_=stage_geometry(layer,plan,{c['name']:dict(map='Old',water_tile=[0,0],reef_tile=[1,0]) for c in plan['chunks']})
        report=stage_names(layer,plan,{c['name']:'Old' for c in plan['chunks']})
        updated=layer.outputs['src/data/journey_world_map.h'].decode()
        self.assertIn(old,updated)
        self.assertEqual(dict(decode_atlas(header).array_sha256),dict(decode_atlas(updated).array_sha256))
        self.assertEqual(report['points'][0]['label'],'OLD COAST')
        self.assertEqual(report['points'][0]['atlas'],[3,3])
        self.assertFalse(report['native_validated'])
        self.assertTrue(report['labels_are_not_player_location_proof'])
        self.assertEqual((root/'src/data/journey_world_map.h').read_text(),header)

    def test_overlay_does_not_compile_a_different_enum_from_disk(self):
        root,layer=self.fixture()
        view=OverlaySource(layer)
        layer.outputs['include/constants/metatile_behaviors.h']=b'enum{CHANGED};'
        with self.assertRaisesRegex(ValueError,'isolated native compiler snapshot'):
            _=view.behavior_flags


if __name__=='__main__':
    unittest.main()
