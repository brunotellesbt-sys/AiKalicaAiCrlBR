"""Stage one sea pattern without changing Sevii water or shoreline semantics.

The original fast-water tiles have static diagonal waves. Generated ocean
links use the globally animated ocean at graphics 454/455. Private metatile
tables give both behaviors the latter art while retaining every attribute,
block, shoreline overlay, palette, graphics bank and animation callback.
"""
import hashlib
import json
import re
import struct
from pathlib import Path

from PIL import Image


PRIMARY = 'gTileset_JourneySeviiSea'
TARGET_MAPS = sorted([
    'OneIsland_Frlg', 'OneIsland_TreasureBeach_Frlg', 'TwoIsland_Frlg',
    'TwoIsland_CapeBrink_Frlg', 'ThreeIsland_Frlg', 'ThreeIsland_Port_Frlg',
    'FourIsland_Frlg', 'FiveIsland_Frlg', 'SixIsland_Frlg',
    'SixIsland_WaterPath_Frlg', 'SevenIsland_Frlg',
    'SevenIsland_TrainerTower_Frlg', 'SevenIsland_SevaultCanyon_Entrance_Frlg',
    'SevenIsland_SevaultCanyon_Frlg', 'JourneySurfLink01000',
    'JourneySurfLink05100', 'JourneySurfLink05200', 'JourneySurfLink05301',
])
FAMILIES = ['123', '45', '67']


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _header(headers, symbol):
    return re.search(r'const struct Tileset ' + re.escape(symbol)
                     + r'\s*=\s*\{(.*?)\};', headers, re.S)[1]


def _field(body, field):
    return re.search(r'\.' + field + r'\s*=\s*(\w+)', body)[1]


def _table_path(definitions, symbol):
    return re.search(r'\b' + re.escape(symbol) + r'\[\].*?"([^"]+)"', definitions)[1]


def _retarget(blob, canonical):
    old = list(struct.unpack('<' + 'H' * (len(blob) // 2), blob))
    new, changes = old.copy(), []
    for at, word in enumerate(old):
        if 464 <= word & 1023 < 468:
            # Those four graphics contain water only; no object/body graphic
            # is eligible. Preserve every upper layer word, including corners.
            assert at % 8 < 4, (at, word)
            new[at] = canonical[at % 8]
            changes.append(dict(word_index=at, before=word, after=new[at]))
    assert all(old[i] == new[i] for i in range(len(old)) if i % 8 >= 4)
    return struct.pack('<' + 'H' * len(new), *new), changes


def repair(layer):
    """Stage only; compose after harbor geometry/movement and Six terrain."""
    source, touched = layer.source, set()

    def raw(path):
        return layer.outputs[path] if path in layer.outputs else (source / path).read_bytes()

    def stage(path, content):
        layer.stage(path, content)
        touched.add(path)

    headers_path, definitions_path = 'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h'
    headers, definitions = raw(headers_path).decode(), raw(definitions_path).decode()
    primary_body = _header(headers, 'gTileset_General_Frlg')
    primary_path = _table_path(definitions, _field(primary_body, 'metatiles'))
    canonical = list(struct.unpack_from('<4H', raw(primary_path), 0x12B * 16))
    assert canonical == [0x41C6, 0x41C7, 0x41C7, 0x41C6]
    tables, aliases = [], []

    def table(old_symbol, new_symbol=None):
        nonlocal headers, definitions
        body = _header(headers, old_symbol)
        old_meta = _field(body, 'metatiles')
        old_path = _table_path(definitions, old_meta)
        before = raw(old_path)
        after, changes = _retarget(before, canonical)
        assert changes, old_symbol
        if new_symbol:
            new_meta = new_symbol.replace('gTileset_', 'gMetatiles_')
            path = str(Path(old_path).with_name('journey_sevii_sea_metatiles.bin'))
            assert new_symbol not in headers and new_meta not in definitions
            new_body = body.replace('.metatiles = ' + old_meta + ',', '.metatiles = ' + new_meta + ',')
            assert body == new_body.replace(new_meta, old_meta)
            headers += '\nconst struct Tileset ' + new_symbol + ' =\n{' + new_body + '};\n'
            definitions += '\nconst u16 ' + new_meta + '[] = INCBIN_U16("' + path + '");\n'
            aliases.append(dict(original=old_symbol, private=new_symbol))
        else:
            new_meta, path, new_symbol = old_meta, old_path, old_symbol
        stage(path, after)
        attrs = _field(body, 'metatileAttributes')
        tables.append(dict(original_tileset=old_symbol, tileset=new_symbol,
                           original_metatile_symbol=old_meta, metatile_symbol=new_meta,
                           original_path=old_path, path=path, attributes_symbol=attrs,
                           original_sha256=_sha(before), prepared_sha256=_sha(after),
                           words_changed=changes, native_body_words_unchanged=True,
                           attributes_unchanged=True))

    table('gTileset_General_Frlg', PRIMARY)
    for family in FAMILIES:
        table('gTileset_SeviiIslands' + family, 'gTileset_JourneySeviiSea' + family)
        table('gTileset_JourneySeviiIntegrated' + family)
    stage(headers_path, headers)
    stage(definitions_path, definitions)

    layout_data = json.loads(raw('data/layouts/layouts.json'))
    layouts = {row['id']: row for row in layout_data['layouts']}
    maps = {path.parent.name: json.loads(raw(path.relative_to(source).as_posix()))
            for path in (source / 'data/maps').glob('*/map.json')}
    by_id = {row['id']: name for name, row in maps.items()}
    assignment = []
    for name in TARGET_MAPS:
        layout = layouts[maps[name]['layout']]
        assert layout['layout_version'] == 'frlg'
        assert layout['primary_tileset'] == 'gTileset_General_Frlg'
        old_secondary = layout['secondary_tileset']
        if old_secondary.startswith('gTileset_SeviiIslands'):
            layout['secondary_tileset'] = old_secondary.replace('gTileset_SeviiIslands', 'gTileset_JourneySeviiSea')
        else:
            assert old_secondary.startswith('gTileset_JourneySeviiIntegrated'), (name, old_secondary)
        layout['primary_tileset'] = PRIMARY
        assignment.append(dict(map=name, layout=layout['id'],
                               original_primary='gTileset_General_Frlg',
                               original_secondary=old_secondary,
                               primary=PRIMARY, secondary=layout['secondary_tileset']))
    stage('data/layouts/layouts.json', json.dumps(layout_data, indent=2) + '\n')

    # Exact pointer comparisons otherwise discard the native door graphics
    # for a private bank, despite the door metatile itself being unchanged.
    door_path = 'src/field_door.c'
    doors = raw(door_path).decode()
    compare = '(gfx->tileset == gMapHeader.mapLayout->primaryTileset || gfx->tileset == gMapHeader.mapLayout->secondaryTileset)'
    assert doors.count(compare) == 1
    door_aliases = aliases + [dict(original='gTileset_SeviiIslands' + family,
                                  private='gTileset_JourneySeviiIntegrated' + family)
                              for family in FAMILIES]
    function = '''static const struct Tileset *JourneySeviiDoorTileset(const struct Tileset *tileset)
{
'''
    for alias in door_aliases:
        function += '    if (tileset == &' + alias['private'] + ')\n        return &' + alias['original'] + ';\n'
    function += '    return tileset;\n}\n\n'
    anchor = 'static const struct DoorGraphics *GetDoorGraphics(const struct DoorGraphics *gfx, u16 metatileNum)\n'
    assert doors.count(anchor) == 1
    doors = doors.replace(anchor, function + anchor)
    doors = doors.replace(compare, '(gfx->tileset == JourneySeviiDoorTileset(gMapHeader.mapLayout->primaryTileset) || gfx->tileset == JourneySeviiDoorTileset(gMapHeader.mapLayout->secondaryTileset))')
    stage(door_path, doors)
    path = 'include/tilesets.h'
    declarations = raw(path).decode()
    new_declarations = ''.join('extern const struct Tileset ' + row['private'] + ';\n'
                               for row in door_aliases)
    assert all(('extern const struct Tileset ' + row['private'] + ';') not in declarations
               for row in door_aliases)
    stage(path, declarations.replace('\n#endif', '\n' + new_declarations + '\n#endif'))

    pairs = {}
    for name in TARGET_MAPS:
        for edge in maps[name].get('connections') or []:
            if edge['direction'] not in ['left', 'right', 'up', 'down']:
                continue
            other = by_id[edge['map']]
            key = tuple(sorted([name, other]))
            pairs.setdefault(key, dict(maps=list(key), source=name, destination=other,
                                       direction=edge['direction'], offset=edge['offset']))
    assert len(pairs) == 26
    return dict(changed_paths=sorted(touched), target_maps=TARGET_MAPS,
                layout_assignments=assignment, tables=tables, aliases=aliases,
                door_aliases=door_aliases, native_door_animation_aliases_preserved=True,
                surface_seams=[pairs[key] for key in sorted(pairs)], expected_surface_seams=26,
                canonical_words=canonical, canonical_graphics=[454, 455],
                old_static_graphics=[464, 465, 466, 467],
                native_body_words_unchanged=True, all_attributes_unchanged=True,
                all_blockdata_and_map_events_unchanged=True,
                native_ocean_and_fast_water_behaviors_preserved=True,
                surf_dive_encounter_semantics_preserved=True,
                original_shared_tilesets_unchanged=True,
                primary_graphics_palettes_and_animation_callback_shared=True)


def validate_compiled(lib, symbols, source, metadata):
    """Read the final ROM tables and aliases; do not modify emulator state."""
    source = Path(source)
    definitions = (source / 'src/data/tilesets/metatiles.h').read_text()
    records = []
    for row in metadata['tables']:
        expected = (source / row['path']).read_bytes()
        address = symbols[row['metatile_symbol']]
        compiled = bytes(lib.read8(address + i) for i in range(len(expected)))
        assert compiled == expected, ('Compiled sea table differs', row['path'])
        bank = symbols[row['tileset']]
        assert lib.read32(bank + 12) == address
        assert lib.read32(bank + 16) == symbols[row['attributes_symbol']]
        attr_address = symbols[row['attributes_symbol']]
        attributes = (source / _table_path(definitions, row['attributes_symbol'])).read_bytes()
        assert bytes(lib.read8(attr_address + i) for i in range(len(attributes))) == attributes
        for change in row['words_changed']:
            assert change['word_index'] % 8 < 4
            assert lib.read16(address + 2 * change['word_index']) == change['after']
        records.append(dict(tileset=row['tileset'], compiled_words=len(expected) // 2,
                            canonical_water_words=len(row['words_changed']),
                            metatiles_sha256=_sha(compiled), attributes_sha256=_sha(attributes),
                            compiled_attribute_bytes=len(attributes), attributes_pointer_preserved=True))
    for row in metadata['aliases']:
        old, new = symbols[row['original']], symbols[row['private']]
        # Every header byte except the metatile pointer must be identical.
        assert all(lib.read8(old + i) == lib.read8(new + i)
                   for i in range(24) if i not in range(12, 16)), row
    primary_attrs = lib.read32(symbols[PRIMARY] + 16)
    assert lib.read32(primary_attrs + 4 * 0x12B) & 511 == 0x15
    assert lib.read32(primary_attrs + 4 * 0x273) & 511 == 0x2C
    return dict(compiled_metatile_tables=records, compiled_tables_match_source=True,
                compiled_attributes_shared=True, native_body_words_unchanged=True,
                graphics_palettes_and_callbacks_identical=True,
                ocean_fast_water_surf_dive_encounter_attributes_preserved=True)


def audit_source(source, baseline, metadata):
    """Independently constrain the sea change to water underlay words only.

    The surrounding integration audit replays harbor imports independently;
    this check also verifies their reversible before-table hashes so no
    additional private object word can be hidden among the water changes.
    """
    source, baseline = Path(source), Path(baseline)
    headers = (source / 'src/data/tilesets/headers.h').read_text()
    definitions = (source / 'src/data/tilesets/metatiles.h').read_text()
    old_headers = (baseline / 'src/data/tilesets/headers.h').read_text()
    old_definitions = (baseline / 'src/data/tilesets/metatiles.h').read_text()
    checked_words = body_words = 0
    for row in metadata['tables']:
        after = (source / row['path']).read_bytes()
        assert _sha(after) == row['prepared_sha256']
        before = bytearray(after)
        positions = set()
        for change in row['words_changed']:
            at = change['word_index']
            assert at not in positions and at % 8 < 4
            positions.add(at)
            assert 464 <= change['before'] & 1023 < 468
            assert change['after'] == metadata['canonical_words'][at % 8]
            assert struct.unpack_from('<H', after, 2 * at)[0] == change['after']
            struct.pack_into('<H', before, 2 * at, change['before'])
        assert _sha(before) == row['original_sha256']
        if row['original_tileset'] != row['tileset']:
            assert (baseline / row['original_path']).read_bytes() == before
            assert (source / row['original_path']).read_bytes() == before
            old_body = _header(old_headers, row['original_tileset'])
            new_body = _header(headers, row['tileset'])
            assert new_body.replace(row['metatile_symbol'], row['original_metatile_symbol']) == old_body
            attrs_path = _table_path(old_definitions, row['attributes_symbol'])
            assert (source / attrs_path).read_bytes() == (baseline / attrs_path).read_bytes()
        expected, changes = _retarget(bytes(before), metadata['canonical_words'])
        assert expected == after and changes == row['words_changed']
        assert _field(_header(headers, row['tileset']), 'metatileAttributes') == row['attributes_symbol']
        assert _table_path(definitions, row['metatile_symbol']) == row['path']
        checked_words += len(after) // 2
        body_words += len(after) // 4
    assert set(metadata['target_maps']) == set(TARGET_MAPS)
    assert len(metadata['surface_seams']) == metadata['expected_surface_seams'] == 26
    return dict(passed=True, water_table_words_checked=checked_words,
                native_upper_body_words_preserved=body_words,
                only_graphics_464_to_467_water_underlays_retargeted=True,
                all_native_attributes_and_behavior_tables_unchanged=True,
                original_shared_banks_unchanged=True,
                original_primary_palette_graphics_and_callback_reused=True,
                exact_private_before_tables_reconstructed=True)


def _animation_frames(source):
    frames = []
    for phase in range(8):
        image = Image.open(Path(source) / f'data/tilesets/primary/general_frlg/anim/water_current_landwatersedge/{phase}.png')
        pixels = []
        for tile in [38, 39]:
            x, y = tile % (image.width // 8) * 8, tile // (image.width // 8) * 8
            pixels.extend(image.getpixel((x + xx, y + yy)) | image.getpixel((x + xx + 1, y + yy)) << 4
                          for yy in range(8) for xx in range(0, 8, 2))
        frames.append(bytes(pixels))
    return frames


def validate_loaded(lib, symbols, source, metadata, map_name):
    """Check loaded water art/animation and map buffer without state writes."""
    source = Path(source)
    header = json.loads((source / f'data/maps/{map_name}/map.json').read_text())
    layouts = {row['id']: row for row in json.loads((source / 'data/layouts/layouts.json').read_text())['layouts']}
    layout = layouts[header['layout']]
    assert layout['layout_version'] == 'frlg', map_name
    loaded_layout = lib.read32(symbols['gMapHeader'])
    primary, secondary = lib.read32(loaded_layout + 16), lib.read32(loaded_layout + 20)
    assert primary == symbols[layout['primary_tileset']], map_name
    assert secondary == symbols[layout['secondary_tileset']], map_name
    canonical = [lib.read16(lib.read32(primary + 12) + 0x12B * 16 + 2 * i) for i in range(4)]
    assert canonical == metadata['canonical_words'], (map_name, canonical)
    table_rows = {row['tileset']: row for row in metadata['tables']}
    checked = []
    width, height = layout['width'], layout['height']
    blob = (source / layout['blockdata_filepath']).read_bytes()
    values = struct.unpack('<' + 'H' * (len(blob) // 2), blob)
    buffer_width = lib.read32(symbols['gBackupMapLayout'])
    buffer = lib.read32(symbols['gBackupMapLayout'] + 8)
    for bank_name, bank, offset in [(layout['primary_tileset'], primary, 0),
                                    (layout['secondary_tileset'], secondary, 640)]:
        row = table_rows.get(bank_name)
        if not row:
            continue
        mids = {change['word_index'] // 8 + offset for change in row['words_changed']}
        for cell, value in enumerate(values):
            if value & 1023 not in mids:
                continue
            x, y = cell % width, cell // width
            actual = lib.read16(buffer + 2 * ((y + 7) * buffer_width + x + 7))
            assert actual == value, (map_name, x, y, actual, value)
            checked.append([x, y, value])
    vram = bytes(lib.read8(0x06000000 + 454 * 32 + i) for i in range(64))
    frames = _animation_frames(source)
    assert vram in frames, ('Loaded canonical water animation differs', map_name, _sha(vram))
    palette = [lib.read16(0x05000000 + (64 + i) * 2) for i in [3, 4, 5, 7]]
    return dict(map=map_name, primary=layout['primary_tileset'], secondary=layout['secondary_tileset'],
                canonical_lower_words=canonical, loaded_underlay_cells_checked=len(checked),
                loaded_underlay_cells_sha256=_sha(json.dumps(checked).encode()),
                vram_water_sha256=_sha(vram), valid_animation_phases=[i for i, frame in enumerate(frames) if frame == vram],
                native_ocean_palette=palette, loaded_graphics_and_palette_verified=True,
                native_map_buffer_unchanged=True, native_body_words_unchanged=True)
