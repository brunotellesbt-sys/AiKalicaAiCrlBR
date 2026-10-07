"""Add real bidirectional sea map connections to the reviewed LeafGreen source."""
import hashlib
import json
from pathlib import Path
import struct

PORTS = ['VermilionCity'] + [name + '_Harbor' for name in
         ['OneIsland', 'TwoIsland', 'ThreeIsland', 'FourIsland', 'FiveIsland',
          'SixIsland', 'SevenIsland', 'BirthIsland', 'NavelRock']]
WATER = 0x11D9  # General ocean at water elevation 1; walking cannot enter it.
WIDTH, HEIGHT = 48, 24


def prepare(source):
    source = Path(source)
    marker = source / '.sea-routes-prepared'
    if marker.exists():
        report = json.loads(marker.read_text())
        if report['water_block'] != WATER:
            raise ValueError('Different sea-route revision; use a freshly prepared source')
        include_scripts(source, report['routes'])
        return report
    if not (source / '.unova-prepared').exists():
        raise ValueError('Prepare tools/regions first, with the reviewed catalog.')
    groups_path = source / 'data/maps/map_groups.json'
    layouts_path = source / 'data/layouts/layouts.json'
    groups = json.loads(groups_path.read_text())
    layouts = json.loads(layouts_path.read_text())
    by_id = {r['id']: r for r in layouts['layouts']}
    originals = {}

    def write(relative, data):
        p = source / relative
        originals[str(relative)] = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data if isinstance(data, bytes) else data.encode())

    def write_json(relative, value):
        write(relative, json.dumps(value, indent=2) + '\n')

    harbor = by_id['LAYOUT_ISLAND_HARBOR']
    blocks = list(struct.unpack('<' + 'H' * (harbor['width'] * harbor['height']),
                              (source / harbor['blockdata_filepath']).read_bytes()))
    # Open a side of the existing pier, away from the sailor and ship.
    for y in range(5, harbor['height']):
        for x in range(3, 7):
            blocks[y * harbor['width'] + x] = WATER
    write(harbor['blockdata_filepath'], struct.pack('<' + 'H' * len(blocks), *blocks))

    groups['group_order'].append('JourneySeaRoutes')
    groups['JourneySeaRoutes'] = []
    routes = []
    for i, port in enumerate(PORTS):
        name = f'JourneySeaRoute{i:02d}'
        map_id = f'MAP_JOURNEY_SEA_ROUTE_{i:02d}'
        layout_id = f'LAYOUT_JOURNEY_SEA_ROUTE_{i:02d}'
        path = f'data/maps/{port}/map.json'
        origin = json.loads((source / path).read_text())
        offset = 0 if i == 0 else -15
        links = list(origin.get('connections') or [])
        if any(c['direction'] == 'down' for c in links):
            raise ValueError('Occupied southern connection: ' + port)
        links.append({'map': map_id, 'offset': offset, 'direction': 'down'})
        origin['connections'] = links
        write_json(path, origin)
        if i == 0:
            city_layout = by_id[origin['layout']]
            raw = (source / city_layout['blockdata_filepath']).read_bytes()
            city_blocks = list(struct.unpack('<' + 'H' * (len(raw) // 2), raw))
            # Widen the water channel beyond the decorative coastal rocks.
            for y in range(31, city_layout['height']):
                for x in [33, 34]:
                    city_blocks[y * city_layout['width'] + x] = WATER
            write(city_layout['blockdata_filepath'], struct.pack('<' + 'H' * len(city_blocks), *city_blocks))

        connections = [{'map': origin['id'], 'offset': -offset, 'direction': 'up'}]
        for direction, neighbor in [('left', i - 1), ('right', i + 1)]:
            if 0 <= neighbor < len(PORTS):
                connections.append({'map': f'MAP_JOURNEY_SEA_ROUTE_{neighbor:02d}',
                                    'offset': 0, 'direction': direction})
        data = dict(id=map_id, name=name, layout=layout_id, music='MUS_SURF',
                    region_map_section=origin['region_map_section'], requires_flash=False,
                    weather='WEATHER_SUNNY', map_type='MAP_TYPE_ROUTE', allow_cycling=False,
                    allow_escaping=False, allow_running=False, show_map_name=False,
                    floor_number=0, battle_scene='MAP_BATTLE_SCENE_NORMAL', connections=connections,
                    object_events=[], warp_events=[], coord_events=[], bg_events=[])
        write_json(f'data/maps/{name}/map.json', data)
        write(f'data/maps/{name}/scripts.inc', name + '_MapScripts::\n\t.byte 0\n')
        base = f'data/layouts/{name}'
        write(base + '/map.bin', struct.pack('<H', WATER) * (WIDTH * HEIGHT))
        # Closed visual border; map connections replace it at legitimate seams.
        write(base + '/border.bin', struct.pack('<H', WATER | 0x400) * 4)
        layouts['layouts'].append(dict(id=layout_id, name=name + '_Layout', width=WIDTH,
            height=HEIGHT, border_width=2, border_height=2,
            primary_tileset='gTileset_General', secondary_tileset='gTileset_IslandHarbor',
            border_filepath=base + '/border.bin', blockdata_filepath=base + '/map.bin'))
        groups['JourneySeaRoutes'].append(name)
        routes.append(dict(name=name, port=port, width=WIDTH, height=HEIGHT,
                           origin_offset=offset, connections=connections))

    write_json('data/maps/map_groups.json', groups)
    write_json('data/layouts/layouts.json', layouts)
    originals['data/event_scripts.s'] = hashlib.sha256((source / 'data/event_scripts.s').read_bytes()).hexdigest()
    report = dict(routes=routes, water_block=WATER, original_hashes=originals,
                  hoenn_integrated=False, aquatic_hms_preserved=['Surf', 'Waterfall'],
                  missing_aquatic_field_moves=['Dive', 'Whirlpool'])
    include_scripts(source, routes)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report


def include_scripts(source, routes):
    p = source / 'data/event_scripts.s'; text = p.read_text()
    for route in routes:
        line = '\t.include "data/maps/' + route['name'] + '/scripts.inc"\n'
        if line not in text: text += '\n' + line
    p.write_text(text)
