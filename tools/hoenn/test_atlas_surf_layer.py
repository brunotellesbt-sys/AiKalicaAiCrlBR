"""Guard historical identities and donor-bank provenance during materialization."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from atlas_surf_geometry import plan_geometry
from atlas_surf_layer import stage_geometry


class Overlay:
    def __init__(self, root):
        self.source, self.outputs, self.expected = root, {}, {}

    def parent(self, name, value):
        path = self.source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value if isinstance(value, bytes) else json.dumps(value).encode())
        self.expected[name] = hashlib.sha256(path.read_bytes()).hexdigest()

    def stage(self, name, value):
        self.outputs[name] = value if isinstance(value, bytes) else value.encode()


class GeometryWriterTests(unittest.TestCase):
    def fixture(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        layer = Overlay(Path(temp.name))
        layer.parent('data/maps/map_groups.json', dict(group_order=['Native'], Native=['OldCoast']))
        layout = dict(id='LAYOUT_OLD', name='OldCoast', width=2, height=1,
                      primary_tileset='NativePrimary', secondary_tileset='NativeSecondary',
                      layout_version='frlg', blockdata_filepath='old.bin', border_filepath='old-border.bin')
        layer.parent('data/layouts/layouts.json', dict(layouts=[layout]))
        original = dict(id='MAP_OLD_COAST', name='OldCoast', layout='LAYOUT_OLD',
                        object_events=[dict(local_id=7)], warp_events=[dict(dest_map='MAP_OLD_COAST')],
                        coord_events=[], bg_events=[], connections=[])
        layer.parent('data/maps/OldCoast/map.json', original)
        layer.parent('old.bin', struct.pack('<2H', 0x112B, 0x1643))
        layer.parent('data/event_scripts.s', b'original_scripts::\n')
        return layer, original

    def test_append_only_ids_original_events_and_frozen_inputs(self):
        layer, original = self.fixture()
        before = {p.relative_to(layer.source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in layer.source.rglob('*') if p.is_file()}
        plan = plan_geometry([(3, 3), (4, 3)])
        donors = {c['name']: dict(map='OldCoast', water_tile=[0, 0], reef_tile=[1, 0])
                  for c in plan['chunks']}
        bound, result = stage_geometry(layer, plan, donors)
        groups = json.loads(layer.outputs['data/maps/map_groups.json'])
        self.assertEqual(groups['Native'], ['OldCoast'])
        self.assertEqual(bound['chunks'][0]['group_index'], 1)
        self.assertNotIn('data/maps/OldCoast/map.json', layer.outputs)
        self.assertFalse(result['native_adapters_and_events_integrated'])
        for chunk in bound['chunks']:
            mapping = json.loads(layer.outputs[f"data/maps/{chunk['name']}/map.json"])
            self.assertEqual(mapping['object_events'], [])
            self.assertEqual(mapping['warp_events'], [])
            layouts = json.loads(layer.outputs['data/layouts/layouts.json'])['layouts']
            row = next(l for l in layouts if l['id'] == mapping['layout'])
            self.assertEqual(row['primary_tileset'], 'NativePrimary')
            self.assertEqual(row['secondary_tileset'], 'NativeSecondary')
        self.assertEqual(before, {p.relative_to(layer.source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in layer.source.rglob('*') if p.is_file()})

    def test_bad_bank_donor_or_existing_map_is_rejected(self):
        layer, _ = self.fixture()
        plan = plan_geometry([(3, 3)])
        donors = {c['name']: dict(map='OldCoast', water_tile=[1, 0], reef_tile=[0, 0])
                  for c in plan['chunks']}
        with self.assertRaises(ValueError):
            stage_geometry(layer, plan, donors)
        bad = copy.deepcopy(plan)
        bad['chunks'][0].update(name='OldCoast', id='MAP_OLDCOAST')
        with self.assertRaises(ValueError):
            stage_geometry(layer, bad, {'OldCoast': next(iter(donors.values()))})

    def test_signed_map_group_capacity_is_enforced(self):
        layer, _ = self.fixture()
        groups = dict(group_order=['Native'] + [f'Empty{i}' for i in range(127)], Native=['OldCoast'])
        groups.update({name: [] for name in groups['group_order'][1:]})
        layer.parent('data/maps/map_groups.json', groups)
        plan = plan_geometry([(3, 3)])
        donors = {c['name']: dict(map='OldCoast', water_tile=[0, 0], reef_tile=[1, 0])
                  for c in plan['chunks']}
        with self.assertRaisesRegex(ValueError, 'signed 127'):
            stage_geometry(layer, plan, donors)


if __name__ == '__main__':
    unittest.main()
