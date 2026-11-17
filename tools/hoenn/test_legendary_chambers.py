"""Portable regression controls from the actual 105-room preparation."""
import base64
import copy
import gzip
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from atlas_legendary_chambers import stretch
from audit_legendary_chambers import audit


class IndividualLegendaryRooms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=Path(__file__).parent/'data/legendary-chambers-source-fixture.json.gz'
        fixture=json.loads(gzip.decompress(path.read_bytes()))
        cls.temp=tempfile.TemporaryDirectory(prefix='individual-legend-rooms-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.reference=Path(cls.temp.name)
        for name,encoded in fixture['reference'].items():
            path=cls.reference/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(base64.b64decode(encoded))
        cls.current={n:base64.b64decode(raw) for n,raw in fixture['current'].items()}
        cls.report=fixture['report']

    def setUp(self):
        self.layer=SimpleNamespace(source=self.reference,outputs=dict(self.current))
        self.plan=copy.deepcopy(self.report)

    def mutate_json(self,name,change):
        value=json.loads(self.layer.outputs[name])
        change(value)
        self.layer.outputs[name]=json.dumps(value).encode()

    def test_all105_own_rooms_keep_native_IDs_capture_scripts_and_single_Dex_location(self):
        result=audit(self.layer,self.reference,self.plan)
        self.assertTrue(result['passed'])
        self.assertEqual((result['rooms'],result['parents']),(105,48))
        self.assertEqual(result['unique_native_geometries'],37)
        self.assertFalse(result['native_gameplay_validated'])

    def test_wrong_reciprocal_parent_warp_is_rejected(self):
        name=self.plan['rooms'][0]['room']
        self.mutate_json(f'data/maps/{name}/map.json',lambda m:m['warp_events'][0].update(dest_warp_id='0'))
        with self.assertRaisesRegex(ValueError,'own entrance'):
            audit(self.layer,self.reference,self.plan)

    def test_changed_capture_flag_or_statue_is_rejected(self):
        room=self.plan['rooms'][0]['room'];path=f'data/maps/{room}/map.json'
        for change in (dict(flag='FLAG_TEMP_1'),dict(graphics_id='OBJ_EVENT_GFX_STATUE')):
            with self.subTest(change=change):
                self.layer.outputs=dict(self.current)
                self.mutate_json(path,lambda m:m['object_events'][0].update(change))
                with self.assertRaisesRegex(ValueError,'identity, sprite or flag'):
                    audit(self.layer,self.reference,self.plan)

    def test_native_actor_array_cannot_be_reordered(self):
        path='data/maps/GraniteCave_1F/map.json'
        self.mutate_json(path,lambda m:m['object_events'].append(m['object_events'].pop(0)))
        with self.assertRaisesRegex(ValueError,'campaign actor'):
            audit(self.layer,self.reference,self.plan)

    def test_rehashed_cut_scenery_does_not_pass_whole_template_check(self):
        room=self.plan['rooms'][0]
        path=f'data/layouts/{room["room"]}/map.bin'
        raw=bytearray(self.layer.outputs[path]);raw[0]^=1
        self.layer.outputs[path]=bytes(raw)
        room['blockdata_sha256']=hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ValueError,'native scenery'):
            audit(self.layer,self.reference,self.plan)

    def test_foreign_bank_and_duplicate_Dex_rows_are_rejected(self):
        room=self.plan['rooms'][0]
        path='data/layouts/layouts.json'
        def foreign(doc):
            next(l for l in doc['layouts'] if l['id']=='LAYOUT_'+room['room'].upper())['secondary_tileset']='gTileset_Cave'
        self.mutate_json(path,foreign)
        with self.assertRaisesRegex(ValueError,'foreign native graphics'):
            audit(self.layer,self.reference,self.plan)
        self.layer.outputs=dict(self.current)
        path='src/data/journey_world_dex_locations.h'
        self.layer.outputs[path]+=b'\n{SPECIES_ARTICUNO,MAP_JOURNEYSANCTUARYTEMPESTADES,123,57,1,0},\n'
        with self.assertRaisesRegex(ValueError,'stale or duplicate'):
            audit(self.layer,self.reference,self.plan)

    def test_old_map_numbers_and_all_four_atlas_arrays_are_immutable(self):
        path='data/maps/map_groups.json'
        def reorder(doc):
            group=doc['group_order'][0]
            doc[group][0],doc[group][1]=doc[group][1],doc[group][0]
        self.mutate_json(path,reorder)
        with self.assertRaisesRegex(ValueError,'map numbers'):
            audit(self.layer,self.reference,self.plan)
        for symbol in ('sWorldTiles','sWorldTilemap','sWorldPalette','sWorldDetailPixels'):
            with self.subTest(symbol=symbol):
                self.layer.outputs=dict(self.current)
                path='src/data/journey_world_map.h'
                raw=self.layer.outputs[path]
                at=raw.index(b'{',raw.index(symbol.encode()))+1
                self.layer.outputs[path]=raw[:at]+b'1,'+raw[at:]
                with self.assertRaisesRegex(ValueError,'artwork changed'):
                    audit(self.layer,self.reference,self.plan)

    def test_stretch_rejects_a_composite_corner(self):
        with self.assertRaisesRegex(ValueError,'split native scenery'):
            stretch([1,2,3,4],2,2,1,2,None,0)
        with self.assertRaisesRegex(ValueError,'split native scenery'):
            stretch([1,2,3,4],2,2,None,0,1,2)
