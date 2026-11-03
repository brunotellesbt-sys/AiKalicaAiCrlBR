"""Reject water or occupied arrival destinations before changing the table."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from coastal_followup_arrivals import PATH, REPAIRS, census, repair, rows


class InitialBoatArrivals(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        source = Path(temporary.name)
        names = {value for row in REPAIRS.values() for value in row[:2]}
        lines = []
        for index in range(1, 32):
            if index in REPAIRS:
                old_map, _, landing, _ = REPAIRS[index]
                truck = (10, 6)
                boat = 'TRUE'
            else:
                old_map = 'MAP_CITY_'+str(index)
                names.add(old_map)
                landing, truck, boat = (7, 5), (6, 5), 'FALSE'
            lines.append('{'+', '.join([old_map, *map(str, truck), *map(str, landing), boat])+'}')
        text = 'static const struct JourneyBirthArrival sJourneyBirthArrivals[] = {\n'+',\n'.join(lines)+'\n};\n'
        files = {PATH: text.encode()}
        layouts = []
        for index, map_id in enumerate(sorted(names)):
            name = map_id.removeprefix('MAP_')
            layout = 'LAYOUT_'+name
            path = 'data/layouts/'+name+'/map.bin'
            layouts.append(dict(id=layout, width=64, height=48, layout_version='frlg',
                primary_tileset='gTileset_General', secondary_tileset='gTileset_Coast', blockdata_filepath=path))
            files[path] = struct.pack('<3072H', *([0x3000]*3072))
            files['data/maps/'+name+'/map.json'] = json.dumps(dict(id=map_id, layout=layout,
                object_events=[], warp_events=[], coord_events=[], bg_events=[])).encode()
        files['data/layouts/layouts.json'] = json.dumps(dict(layouts=layouts)).encode()
        files['src/data/tilesets/headers.h'] = b'const struct Tileset gTileset_General = { .metatileAttributes = gGeneralAttrs };\nconst struct Tileset gTileset_Coast = { .metatileAttributes = gCoastAttrs };\n'
        files['src/data/tilesets/metatiles.h'] = b'const u32 gGeneralAttrs[] = INCBIN_U32("general.bin");\nconst u32 gCoastAttrs[] = INCBIN_U32("coast.bin");\n'
        files['general.bin'] = struct.pack('<640I', 0, 21, *([0]*638))
        files['coast.bin'] = struct.pack('<384I', *([0]*384))
        for name, raw in files.items():
            path = source/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)

        class Layer:
            def __init__(self):
                self.source = source
                self.outputs = {}
                self.expected = {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()}

            def stage(self, name, value):
                self.outputs[name] = value.encode() if isinstance(value, str) else value

        return Layer()

    def set_cell(self, layer, map_id, xy, block):
        path = 'data/layouts/'+map_id.removeprefix('MAP_')+'/map.bin'
        raw = bytearray((layer.source/path).read_bytes())
        struct.pack_into('<H', raw, (xy[1]*64+xy[0])*2, block)
        layer.outputs[path] = bytes(raw)

    def test_retargets_ten_starts_and_preserves_all_vehicle_and_other_city_fields(self):
        layer = self.fixture()
        original = rows((layer.source/PATH).read_text())
        report = repair(layer)
        final = rows(layer.outputs[PATH].decode())
        self.assertEqual(len(report['changed_rows']), 10)
        self.assertEqual(len(report['all_31_destinations']), 31)
        self.assertEqual(set(layer.outputs), {PATH})
        for before, after in zip(original, final):
            self.assertEqual(before['truck'], after['truck'])
            self.assertEqual(before['boat'], after['boat'])
            if before['index'] not in REPAIRS:
                self.assertEqual(before, after)
        self.assertEqual(repair(layer)['changed_rows'], [])

    def test_rejects_water_even_with_a_land_elevation(self):
        layer = self.fixture()
        self.set_cell(layer, 'MAP_TWO_ISLAND', (10, 12), 0x3001)
        with self.assertRaisesRegex(AssertionError, 'not on reviewed dry ground'):
            repair(layer)
        self.assertNotIn(PATH, layer.outputs)

    def test_rejects_dry_art_at_surf_elevation(self):
        layer = self.fixture()
        self.set_cell(layer, 'MAP_MOSSDEEP_CITY', (6, 25), 0x1000)
        with self.assertRaisesRegex(AssertionError, 'not on reviewed dry ground'):
            repair(layer)
        self.assertNotIn(PATH, layer.outputs)

    def test_checks_the_mother_cell_independently(self):
        layer = self.fixture()
        self.set_cell(layer, 'MAP_DEWFORD_TOWN', (14, 11), 0x3400)
        with self.assertRaisesRegex(AssertionError, 'not on reviewed dry ground'):
            repair(layer)
        self.assertNotIn(PATH, layer.outputs)

    def test_rejects_static_event_overlap_on_the_new_bridge(self):
        layer = self.fixture()
        path = 'data/maps/SIX_ISLAND/map.json'
        mapping = json.loads((layer.source/path).read_text())
        mapping['warp_events'] = [dict(x=11, y=27)]
        layer.outputs[path] = json.dumps(mapping).encode()
        with self.assertRaisesRegex(AssertionError, 'overlaps an event'):
            repair(layer)
        self.assertNotIn(PATH, layer.outputs)

    def test_census_checks_the_21_unchanged_starts_too(self):
        layer = self.fixture()
        self.set_cell(layer, 'MAP_CITY_28', (7, 5), 0x1001)
        with self.assertRaisesRegex(AssertionError, 'not on reviewed dry ground'):
            repair(layer)
        self.assertNotIn(PATH, layer.outputs)


if __name__ == '__main__':
    unittest.main()
