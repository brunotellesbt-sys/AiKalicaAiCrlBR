"""Extend the private sea banks to their connected native Sevii coasts.

Only the two bank references in ten existing layouts change. The private
banks already preserve their complete native objects, attributes, graphics,
palettes, callbacks and door aliases; this closes the remaining sea seams.
"""
from collections import deque
import hashlib
import json
from pathlib import Path
import struct

from integrated_ocean_seams import _field, _header, _table_path


TARGET_MAPS = (
    'BirthIsland_Exterior_Frlg',
    'FiveIsland_Meadow_Frlg',
    'FiveIsland_MemorialPillar_Frlg',
    'FiveIsland_ResortGorgeous_Frlg',
    'FiveIsland_WaterLabyrinth_Frlg',
    'OneIsland_KindleRoad_Frlg',
    'SevenIsland_TanobyRuins_Frlg',
    'SixIsland_GreenPath_Frlg',
    'SixIsland_OutcastIsland_Frlg',
    'ThreeIsland_BondBridge_Frlg',
)
LAYOUT_PATH = 'data/layouts/layouts.json'


def water_word(word):
    return ((word & 1023 in (454, 455) and word >> 12 == 6)
            or 464 <= word & 1023 < 468)


def repair(layer):
    source = Path(layer.source)

    def raw(path):
        return layer.outputs[path] if path in layer.outputs else (source / path).read_bytes()

    before = raw(LAYOUT_PATH)
    data = json.loads(before)
    layouts = {row['id']: row for row in data['layouts']}
    original = json.loads(before)
    originals = {row['id']: row for row in original['layouts']}
    maps = {path.parent.name: json.loads(raw(path.relative_to(source).as_posix()))
            for path in (source / 'data/maps').glob('*/map.json')}
    by_id = {row['id']: name for name, row in maps.items()}
    inherited = json.loads((source / '.journey-sevii-integrated-piers').read_text())['ocean_seams']
    routes = {name: [name] for name in inherited['target_maps']}
    queue = deque(routes)
    while queue:
        name = queue.popleft()
        for edge in maps[name].get('connections') or []:
            if edge['direction'] not in ('left', 'right', 'up', 'down'):
                continue
            other = by_id[edge['map']]
            if other not in routes:
                routes[other] = routes[name] + [other]
                queue.append(other)

    headers = raw('src/data/tilesets/headers.h').decode()
    definitions = raw('src/data/tilesets/metatiles.h').decode()
    tables = {}

    def table(symbol):
        if symbol not in tables:
            body = _header(headers, symbol)
            path = _table_path(definitions, _field(body, 'metatiles'))
            blob = raw(path)
            tables[symbol] = struct.unpack('<' + 'H' * (len(blob) // 2), blob)
        return tables[symbol]

    # Discover using every map and border cell of connected native outdoors.
    # This excludes inland Ruin Valley and ocean links already using palette 4.
    discovered = {}
    for name in sorted(routes):
        mapping = maps[name]
        layout = layouts[mapping['layout']]
        if (layout['primary_tileset'] != 'gTileset_General_Frlg'
                or layout['secondary_tileset'] not in (
                    'gTileset_SeviiIslands123', 'gTileset_SeviiIslands45',
                    'gTileset_SeviiIslands67')
                or mapping['map_type'] not in ('MAP_TYPE_ROUTE', 'MAP_TYPE_TOWN',
                                             'MAP_TYPE_CITY', 'MAP_TYPE_OCEAN_ROUTE')):
            continue
        assert layout['layout_version'] == 'frlg', name
        blob = raw(layout['blockdata_filepath'])
        values = struct.unpack('<' + 'H' * (len(blob) // 2), blob)
        assert len(values) == layout['width'] * layout['height'], name
        border_blob = raw(layout['border_filepath'])
        border_values = struct.unpack('<' + 'H' * (len(border_blob) // 2), border_blob)
        map_metatiles = {value & 1023 for value in values}
        affected = []
        for mid in sorted({value & 1023 for value in values + border_values}):
            symbol = layout['primary_tileset'] if mid < 640 else layout['secondary_tileset']
            index = mid if mid < 640 else mid - 640
            words = table(symbol)[index * 8:(index + 1) * 8]
            if any(water_word(word) for word in words[:4]):
                affected.append(dict(metatile=mid, native_lower_words=list(words[:4])))
        if affected:
            # Keep the prepared marker's map-cell metadata stable. Border
            # cells participate in closure discovery and rejection above;
            # their separate review must not rewrite a frozen marker.
            discovered[name] = dict(affected_metatiles=[row for row in affected
                if row['metatile'] in map_metatiles],
                blockdata_sha256=hashlib.sha256(blob).hexdigest(),
                surface_connection_path=routes[name])
    assert set(discovered) == set(TARGET_MAPS), ('Native marine closure changed', sorted(discovered))

    # Birth Island uses the complete native 67 bank too. Compare every bank
    # field and every object layer, instead of assuming map-name compatibility.
    bank_checks = []
    for native, private in [('gTileset_General_Frlg', 'gTileset_JourneySeviiSea')] + [
            ('gTileset_SeviiIslands' + family, 'gTileset_JourneySeviiSea' + family)
            for family in ('123', '45', '67')]:
        old, new = _header(headers, native), _header(headers, private)
        old_meta, new_meta = _field(old, 'metatiles'), _field(new, 'metatiles')
        assert old == new.replace(new_meta, old_meta), (native, private)
        old_words, new_words = table(native), table(private)
        assert len(old_words) == len(new_words)
        assert all(a == b or (i % 8 < 4 and water_word(a))
                   for i, (a, b) in enumerate(zip(old_words, new_words))), private
        bank_checks.append(dict(original=native, private=private,
            complete_objects_upper_layers_and_attributes_preserved=True,
            graphics_palettes_animation_callbacks_and_header_fields_preserved=True))
    doors = raw('src/field_door.c').decode()
    for row in bank_checks:
        assert ('if (tileset == &' + row['private'] + ')\n        return &'
                + row['original'] + ';') in doors, row

    assignments = []
    for name in TARGET_MAPS:
        layout = layouts[maps[name]['layout']]
        old = dict(layout)
        layout['primary_tileset'] = 'gTileset_JourneySeviiSea'
        layout['secondary_tileset'] = old['secondary_tileset'].replace(
            'gTileset_SeviiIslands', 'gTileset_JourneySeviiSea')
        assignments.append(dict(map=name, layout=layout['id'],
            original_primary=old['primary_tileset'], original_secondary=old['secondary_tileset'],
            primary=layout['primary_tileset'], secondary=layout['secondary_tileset'],
            **discovered[name]))
    target_layouts = {row['layout'] for row in assignments}
    assert len(target_layouts) == len(TARGET_MAPS)
    assert {name for name, row in maps.items() if row['layout'] in target_layouts} == set(TARGET_MAPS)
    for identity, layout in layouts.items():
        old = originals[identity]
        changed = {key for key in old.keys() | layout.keys() if old.get(key) != layout.get(key)}
        assert changed == ({'primary_tileset', 'secondary_tileset'} if identity in target_layouts else set()), identity
    layer.stage(LAYOUT_PATH, json.dumps(data, indent=2) + '\n')
    return dict(kind='coastal-ecology-sevii-bank-aliases', target_maps=list(TARGET_MAPS),
        layout_assignments=assignments, bank_compatibility=bank_checks,
        changed_paths=[LAYOUT_PATH], only_primary_and_secondary_layout_fields_changed=True,
        all_other_layouts_geometry_events_shared_banks_and_save_abi_preserved=True,
        original_shared_tilesets_unchanged=True, native_door_aliases_preserved=True,
        connected_marine_native_layout_census_complete=True)
