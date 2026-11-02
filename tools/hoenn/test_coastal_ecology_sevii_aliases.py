"""Keep native coast aliases bounded to complete compatible private banks."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from coastal_ecology_sevii_aliases import LAYOUT_PATH, TARGET_MAPS, repair


class NativeSeviiAliases(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        source = Path(temporary.name)

        def write(path, raw):
            target = source / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)

        names = ('JourneyRoot',) + TARGET_MAPS + ('SixIsland_RuinValley_Frlg', 'DisconnectedCoast')
        layouts = []
        for name in names:
            family = '67' if name == 'BirthIsland_Exterior_Frlg' else '123'
            layouts.append(dict(id=name, width=2, height=2, layout_version='frlg',
                primary_tileset='gTileset_General_Frlg',
                secondary_tileset='gTileset_SeviiIslands' + family,
                blockdata_filepath=f'data/layouts/{name}/map.bin',
                border_filepath=f'data/layouts/{name}/border.bin', unrelated='preserved'))
            values = (2, 2, 2, 2) if name in ('JourneyRoot', 'SixIsland_RuinValley_Frlg') else (0x1001, 0x1280, 0x3002, 0x3002)
            write(layouts[-1]['blockdata_filepath'], struct.pack('<4H', *values))
            write(layouts[-1]['border_filepath'], struct.pack('<4H', 2, 2, 2, 2))
            connections = [dict(map='MAP_' + other, direction='right', offset=0)
                           for other in TARGET_MAPS + ('SixIsland_RuinValley_Frlg',)] if name == 'JourneyRoot' else []
            write(f'data/maps/{name}/map.json', json.dumps(dict(id='MAP_' + name,
                layout=name, map_type='MAP_TYPE_ROUTE', connections=connections)).encode())
        write(LAYOUT_PATH, json.dumps(dict(layouts=layouts)).encode())
        write('.journey-sevii-integrated-piers', json.dumps(dict(ocean_seams=dict(
            target_maps=['JourneyRoot']))).encode())
        headers, definitions, doors = [], [], []
        for native, private in [('gTileset_General_Frlg', 'gTileset_JourneySeviiSea')] + [
                ('gTileset_SeviiIslands' + family, 'gTileset_JourneySeviiSea' + family)
                for family in ('123', '45', '67')]:
            for symbol in (native, private):
                meta = symbol.replace('gTileset_', 'gMetatiles_')
                headers.append('const struct Tileset ' + symbol + ' = { .metatiles = '
                    + meta + ', .metatileAttributes = NativeAttributes, .callback = NativeAnimation, };')
                definitions.append('const u16 ' + meta + '[] = INCBIN_U16("' + symbol + '.bin");')
                words = [0x41D0 if symbol == native else 0x41C6, 0, 0, 0, 9, 10, 11, 12,
                         0x61C6, 0x61C7, 0x61C7, 0x61C6, 13, 14, 15, 16] + [0] * 8
                write(symbol + '.bin', struct.pack('<24H', *words))
            doors.append('if (tileset == &' + private + ')\n        return &' + native + ';')
        write('src/data/tilesets/headers.h', '\n'.join(headers).encode())
        write('src/data/tilesets/metatiles.h', '\n'.join(definitions).encode())
        write('src/field_door.c', '\n'.join(doors).encode())

        class Layer:
            def __init__(self):
                self.source, self.outputs = source, {}

            def stage(self, path, raw):
                self.outputs[path] = raw.encode() if isinstance(raw, str) else raw

        return Layer()

    def test_aliases_only_two_fields_without_mutating_shared_banks_or_geometry(self):
        layer = self.fixture()
        before = {p.relative_to(layer.source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in layer.source.rglob('*') if p.is_file()}
        report = repair(layer)
        self.assertEqual(set(layer.outputs), {LAYOUT_PATH})
        self.assertEqual(report['target_maps'], list(TARGET_MAPS))
        old = {row['id']: row for row in json.loads((layer.source / LAYOUT_PATH).read_bytes())['layouts']}
        new = {row['id']: row for row in json.loads(layer.outputs[LAYOUT_PATH])['layouts']}
        for name in old:
            changed = {key for key in old[name] if old[name][key] != new[name][key]}
            self.assertEqual(changed, {'primary_tileset', 'secondary_tileset'} if name in TARGET_MAPS else set())
        self.assertEqual(new['BirthIsland_Exterior_Frlg']['secondary_tileset'], 'gTileset_JourneySeviiSea67')
        self.assertEqual(before, {p.relative_to(layer.source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in layer.source.rglob('*') if p.is_file()})

    def test_rejects_private_bank_with_a_changed_upper_object_word(self):
        layer = self.fixture()
        path = layer.source / 'gTileset_JourneySeviiSea67.bin'
        raw = bytearray(path.read_bytes())
        struct.pack_into('<H', raw, 8, 999)
        path.write_bytes(raw)
        with self.assertRaises(AssertionError):
            repair(layer)
        self.assertEqual(layer.outputs, {})

    def test_rejects_unreviewed_new_connected_water_map(self):
        layer = self.fixture()
        (layer.source / 'data/layouts/SixIsland_RuinValley_Frlg/map.bin').write_bytes(struct.pack('<4H', 0x1001, 0, 0, 0))
        with self.assertRaisesRegex(AssertionError, 'Native marine closure changed'):
            repair(layer)
        self.assertEqual(layer.outputs, {})

    def test_includes_native_border_water_in_the_connected_census(self):
        layer = self.fixture()
        (layer.source / 'data/layouts/SixIsland_RuinValley_Frlg/border.bin').write_bytes(struct.pack('<4H', 0x1001, 2, 2, 2))
        with self.assertRaisesRegex(AssertionError, 'Native marine closure changed'):
            repair(layer)
        self.assertEqual(layer.outputs, {})

    def test_rejects_layout_shared_with_an_unreviewed_map(self):
        layer = self.fixture()
        path = layer.source / 'data/maps/DisconnectedCoast/map.json'
        mapping = json.loads(path.read_bytes())
        mapping['layout'] = TARGET_MAPS[0]
        path.write_text(json.dumps(mapping))
        with self.assertRaises(AssertionError):
            repair(layer)
        self.assertEqual(layer.outputs, {})


if __name__ == '__main__':
    unittest.main()
