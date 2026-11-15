"""Only blocked obsolete faces or the explicit lagoon exception may close."""
import json
import unittest

from atlas_surf_coasts import stage_closed_native_connections
from atlas_surf_source import Source
import test_atlas_surf_source_inventory as source_fixtures


class ClosedCoastTests(unittest.TestCase):
    fixture=source_fixtures.NativeInventoryTests.fixture

    def setup_link(self,blocked):
        root,layer=self.fixture({'Old':('emerald',2,1,[0x1001]*2),
                                 'Native':('emerald',2,1,[0x1401 if blocked else 0x1001,0x3000])})
        path='data/maps/Native/map.json';mapping=json.loads((root/path).read_text())
        mapping['connections']=[dict(direction='left',offset=0,map='MAP_OLD')]
        mapping['object_events']=[dict(x=1,y=0,script='PreserveMe')]
        layer.parent(path,mapping)
        return root,layer,mapping

    def test_blocked_face_disconnects_without_terrain_or_event_changes(self):
        root,layer,original=self.setup_link(True);source=Source(root)
        report=stage_closed_native_connections(layer,source,['Old'],route114_closure={})
        updated=json.loads(layer.outputs['data/maps/Native/map.json'])
        self.assertEqual(updated['connections'],[])
        self.assertEqual(updated['object_events'],original['object_events'])
        self.assertEqual(set(layer.outputs),{'data/maps/Native/map.json'})
        self.assertEqual(len(report['removed']),1)
        self.assertEqual(json.loads((root/'data/maps/Native/map.json').read_text()),original)

    def test_live_wet_interface_cannot_disappear(self):
        root,layer,_=self.setup_link(False)
        with self.assertRaisesRegex(ValueError,'unreplaced traversable pair'):
            stage_closed_native_connections(layer,Source(root),['Old'],route114_closure={})
        self.assertEqual(layer.outputs,{})


if __name__=='__main__':unittest.main()
