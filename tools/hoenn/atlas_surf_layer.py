"""Materialize affine ocean chunks without modifying their frozen parent.

This is the geometry writer, not a release preparer. A source with these
chunks still needs native coast adapters, event relocation, ecology, save
migration and independent native evidence before it can replace a ROM.
"""
import copy
import hashlib
import json
import re
import struct

from badge_story_layer import read


def _json(layer, path):
    return json.loads(read(layer, path))


def _sample(layer, maps, layouts, name, cell):
    mapping = maps[name]
    layout = layouts[mapping['layout']]
    x, y = cell
    if not (type(x) is int and type(y) is int and
            0 <= x < layout['width'] and 0 <= y < layout['height']):
        raise ValueError(('Donor cell outside its original layout', name, cell))
    blob = read(layer, layout['blockdata_filepath'])
    if len(blob) != 2 * layout['width'] * layout['height']:
        raise ValueError(('Invalid donor blockdata', name))
    return struct.unpack_from('<H', blob, 2 * (y * layout['width'] + x))[0]


def stage_geometry(layer, plan, donors):
    """Stage chunks with explicit, bank-specific native donor witnesses.

    ``donors`` maps EVERY new chunk name to ``map``, ``water_tile`` and
    ``reef_tile``. Metatile IDs are read from those coordinates, never copied
    between banks. This function does not certify a donor's visual quality.
    Old map/group IDs, events, layouts, atlas arrays and GPS grids stay intact.
    The caller must validate the plan independently before applying it.
    """
    if plan['scale'] != 8 or plan['corridor_width'] != 6:
        raise ValueError('Unreviewed physical atlas scale')
    chunks = plan['chunks']
    if not chunks or set(donors) != {row['name'] for row in chunks}:
        raise ValueError('Every chunk requires one explicit donor specification')
    group_data = _json(layer, 'data/maps/map_groups.json')
    layout_data = _json(layer, 'data/layouts/layouts.json')
    layouts = {row['id']: row for row in layout_data['layouts']}
    # Donor inputs belong to the verified parent; a newly staged map must not
    # silently become another chunk's provenance.
    donor_maps = {spec['map']: _json(layer, f"data/maps/{spec['map']}/map.json")
                  for spec in donors.values()}
    original_groups = copy.deepcopy(group_data)
    original_layouts = copy.deepcopy(layout_data)
    existing_names = {name for group in group_data['group_order'] for name in group_data[group]}
    existing_ids = set(layouts)
    bound = copy.deepcopy(plan)
    ids = {row['id']: row for row in bound['chunks']}
    if len(ids) != len(chunks):
        raise ValueError('Duplicate chunk map ID')
    records, scripts = [], []
    for chunk in bound['chunks']:
        name = chunk['name']
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', name):
            raise ValueError(('Unsafe map name', name))
        if name in existing_names or chunk['id'] != 'MAP_' + name.upper():
            raise ValueError(('Refusing to replace an existing map or inconsistent ID', name))
        layout_id = 'LAYOUT_' + name.upper()
        if layout_id in existing_ids:
            raise ValueError(('Refusing to replace an existing layout', layout_id))
        group = chunk['group']
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', group):
            raise ValueError(('Unsafe group name', group))
        if group not in group_data['group_order']:
            if group in group_data:
                raise ValueError(('Unexpected existing group key', group))
            group_data['group_order'].append(group)
            group_data[group] = []
        number = len(group_data[group])
        if number != chunk['number'] or number >= 100:
            raise ValueError(('Map number does not match append-only WarpData-safe group', name, number))
        index = group_data['group_order'].index(group)
        if index > 127:
            raise ValueError('Persisted WarpData mapGroup cannot exceed signed 127')
        group_data[group].append(name)
        chunk['group_index'] = index
        w, h = chunk['width'], chunk['height']
        if any(type(v) is not int or not 1 <= v <= 127 for v in (w, h)):
            raise ValueError(('Map dimensions exceed signed native coordinates', name))
        spec = donors[name]
        donor = donor_maps[spec['map']]
        layout = copy.deepcopy(layouts[donor['layout']])
        water = _sample(layer, donor_maps, layouts, spec['map'], spec['water_tile'])
        reef = _sample(layer, donor_maps, layouts, spec['map'], spec['reef_tile'])
        if water & 0xC00 or water >> 12 != 1 or not reef & 0xC00:
            raise ValueError(('Donors must provide passable Surf height and a blocked complete reef', name))
        values = [reef] * (w * h)
        occupied = set()
        for y, left, right in chunk['water_runs']:
            if not (0 <= y < h and 0 <= left < right <= w):
                raise ValueError(('Water outside generated map', name))
            for x in range(left, right):
                at = y * w + x
                if at in occupied:
                    raise ValueError(('Duplicate water cell', name, x, y))
                occupied.add(at)
                values[at] = water
        if not occupied and not (chunk.get('reserved_terrain') is True
                                 and chunk.get('kind') in ('stamp','cave','adapter','dive','port')
                                 and chunk.get('evidence')):
            raise ValueError(('Empty generated ocean', name))
        for connection in chunk['connections']:
            if connection['map'] not in ids or connection['direction'] not in ('up', 'down', 'left', 'right'):
                raise ValueError(('Unresolved geometry connection', name, connection))
        folder = f'data/layouts/{name}'
        layout.update(id=layout_id, name=name + '_Layout', width=w, height=h,
                      blockdata_filepath=folder + '/map.bin', border_filepath=folder + '/border.bin',
                      border_width=2, border_height=2)
        layout_data['layouts'].append(layout)
        mapping = copy.deepcopy(donor)
        # Donor scenery/events are not copied as decoration: their real
        # placements must be relocated by the integration stage separately.
        mapping.update(id=chunk['id'], name=name, layout=layout_id,
                       map_type='MAP_TYPE_OCEAN_ROUTE', music='MUS_SURF',
                       connections=copy.deepcopy(chunk['connections']),
                       object_events=[], warp_events=[], coord_events=[], bg_events=[],
                       allow_cycling=False, allow_running=False, show_map_name=False)
        for field in ('shared_scripts_map', 'shared_events_map'):
            mapping.pop(field, None)
        blockdata = struct.pack('<' + 'H' * len(values), *values)
        layer.stage(f'data/maps/{name}/map.json', json.dumps(mapping, indent=2) + '\n')
        layer.stage(layout['blockdata_filepath'], blockdata)
        layer.stage(layout['border_filepath'], struct.pack('<4H', *([reef] * 4)))
        scripts.append(name + '_MapScripts::\n\t.byte 0\n')
        records.append(dict(map=name, map_id=chunk['id'], group_index=index, number=number,
                            layout=layout_id, donor=copy.deepcopy(spec),
                            donor_banks=[layout['primary_tileset'], layout['secondary_tileset']],
                            water_word=water, reef_word=reef,
                            blockdata_sha256=hashlib.sha256(blockdata).hexdigest()))
    for group in original_groups['group_order']:
        if group_data[group] != original_groups[group]:
            raise ValueError(('Historical native IDs changed', group))
    if layout_data['layouts'][:len(original_layouts['layouts'])] != original_layouts['layouts']:
        raise ValueError('Historical layouts changed')
    layer.stage('data/maps/map_groups.json', json.dumps(group_data, indent=2) + '\n')
    layer.stage('data/layouts/layouts.json', json.dumps(layout_data, indent=2) + '\n')
    script_path = 'data/maps/JourneyAtlasSeas.inc'
    layer.stage(script_path, ''.join(scripts))
    event_path = 'data/event_scripts.s'
    event_text = read(layer, event_path).decode()
    include = f'\t.include "{script_path}"\n'
    if script_path in event_text:
        raise ValueError('Atlas chunk script table already included')
    layer.stage(event_path, event_text + '\n' + include)
    return bound, dict(kind='atlas-affine-chunk-materialization', chunks=records,
                       historical_ids_and_layouts_unchanged=True,
                       native_adapters_and_events_integrated=False,
                       source_certified=False, native_certified=False)
