"""Replace Birth Island's orphan roof with the native low wooden landing.

The fifteen roof cells return to native water. Two metal side pieces become
plain wood; the unique warp metatile keeps its behavior/height and receives
the native center-plank artwork. Navel Rock's complete vessel is untouched.
"""
import hashlib
import json
import re
import struct

from badge_story_layer import read


MAP = 'BirthIsland_Exterior_Frlg'
BANK = 'gTileset_JourneySeviiSea67'


def _bank_path(layer, bank, field):
    headers = read(layer, 'src/data/tilesets/headers.h').decode()
    definitions = read(layer, 'src/data/tilesets/metatiles.h').decode()
    body = re.search(r'const struct Tileset ' + re.escape(bank) + r'\s*=\s*\{(.*?)\};', headers, re.S)[1]
    symbol = re.search(r'\.' + field + r'\s*=\s*(\w+)', body)[1]
    return re.search(r'\b' + symbol + r'\[\].*?"([^"]+)"', definitions)[1]


def repair(layer):
    layouts = json.loads(read(layer, 'data/layouts/layouts.json'))['layouts']
    mapspec = read(layer, f'data/maps/{MAP}/map.json')
    mapping = json.loads(mapspec)
    layout = next(row for row in layouts if row['id'] == mapping['layout'])
    assert (layout['width'], layout['height'], layout['layout_version']) == (30, 30, 'frlg')
    assert layout['primary_tileset'] == 'gTileset_JourneySeviiSea'
    assert layout['secondary_tileset'] == BANK
    path = layout['blockdata_filepath']
    before = read(layer, path)
    values = list(struct.unpack('<900H', before))
    roof = ((0x6E8, 0x6E9, 0x6E9, 0x6E9, 0x6EA),
            (0x6F0, 0x6F1, 0x6F1, 0x6F1, 0x6F2),
            (0x6F8, 0x6F9, 0x6F9, 0x6F9, 0x6FA))
    changes = []
    water = values[25*30+12]
    assert water == 0x112B
    for dy, row in enumerate(roof):
        for dx, expected in enumerate(row):
            x, y = 13+dx, 25+dy
            at = y*30+x
            assert values[at] == expected, ('Birth roof footprint changed', x, y)
            changes.append(dict(cell=[x, y], before=values[at], after=water))
            values[at] = water
    for x, old, donor_x in ((14, 0x32E3, 14), (16, 0x32E5, 16)):
        at = 24*30+x
        wood = values[23*30+donor_x]
        assert values[at] == old and wood == (0x31C5 if x == 14 else 0x31C7)
        assert values[at] & ~1023 == wood & ~1023
        changes.append(dict(cell=[x, 24], before=values[at], after=wood))
        values[at] = wood
    assert values[24*30+15] == 0x32E4
    # This metatile has exactly one reference across every map and border in
    # its bank. Its definition is therefore private to this existing warp.
    references = []
    for row in layouts:
        if row['secondary_tileset'] != BANK:
            continue
        for key in ('blockdata_filepath', 'border_filepath'):
            raw = read(layer, row[key])
            for i, (word,) in enumerate(struct.iter_unpack('<H', raw)):
                if word & 1023 == 0x2E4:
                    references.append((row[key], i))
    assert references == [(path, 24*30+15)], ('Warp graphic is no longer private', references)
    meta_path = _bank_path(layer, BANK, 'metatiles')
    primary_path = _bank_path(layer, layout['primary_tileset'], 'metatiles')
    attr_path = _bank_path(layer, BANK, 'metatileAttributes')
    attrs = read(layer, attr_path)
    assert struct.unpack_from('<I', attrs, (0x2E4-640)*4)[0] & 511 == 0x65
    meta_before = read(layer, meta_path)
    meta = bytearray(meta_before)
    wood_words = read(layer, primary_path)[0x1C6*16:(0x1C6+1)*16]
    assert len(wood_words) == 16
    at = (0x2E4-640)*16
    assert bytes(meta[at:at+16]).hex() == '67526852775278520000000083558355'
    meta[at:at+16] = wood_words
    blockdata = struct.pack('<900H', *values)
    layer.stage(path, blockdata)
    layer.stage(meta_path, bytes(meta))
    assert read(layer, attr_path) == attrs and read(layer, f'data/maps/{MAP}/map.json') == mapspec
    return dict(kind='birth-native-wooden-landing', map=MAP, changed_cells=changes,
                cells_changed=len(changes), private_warp_metatile=0x2E4,
                private_metatile_reference=[path, 15, 24],
                native_wood_donor=dict(map=MAP, cell=[15, 23], metatile=0x1C6,
                                       bank=layout['primary_tileset']),
                metadata_path=meta_path, attributes_sha256=hashlib.sha256(attrs).hexdigest(),
                before_sha256=hashlib.sha256(before).hexdigest(),
                after_sha256=hashlib.sha256(blockdata).hexdigest(),
                events_height_collision_and_warp_behavior_preserved=True,
                navel_rock_unchanged=True, native_return_and_visibility_validated=False)
