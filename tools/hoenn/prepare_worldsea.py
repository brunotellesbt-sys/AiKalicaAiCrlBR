"""Extend the experimental native crossing with an eastern Sevii ocean grid.

No replacement of the released ROM. Ports retain every original event. The
western Cinnabar/Hoenn endpoint is deliberately pending geographic confirmation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from prepare_crossing import PIN, HOENN_WATER, KANTO_WATER

WIDTH, HEIGHT = 64, 48
PORTS = ['VermilionCity_Frlg'] + [n + '_Harbor_Frlg' for n in
    ['OneIsland', 'TwoIsland', 'ThreeIsland', 'FourIsland', 'FiveIsland',
     'SixIsland', 'SevenIsland', 'BirthIsland', 'NavelRock']]
CELLS = [(0, 0), (1, 0), (2, 0), (3, 0), (1, 1), (2, 1),
         (1, 2), (2, 2), (3, 1), (3, 2)]
OPPOSITE = dict(up='down', down='up', left='right', right='left')


def prepare(source):
    source = Path(source)
    crossing = json.loads((source / '.journey-hoenn-crossing').read_text())
    if crossing['source_commit'] != PIN or crossing['prototype_revision'] != 4:
        raise ValueError('Prepare the reviewed native crossing revision 4 first')
    marker = source / '.journey-worldsea'
    if marker.exists():
        report = json.loads(marker.read_text())
        if report['revision'] != 1:
            raise ValueError('Unexpected ocean revision')
        for path, digest in report['prepared_sha256'].items():
            if hashlib.sha256((source / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Modified ocean output: ' + path)
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    expected = acquired['sha256'] | crossing['prepared_sha256']
    originals, output = {}, {}

    def stage(path, data):
        target = source / path
        if path not in originals:
            digest = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
            if digest is not None and digest != expected.get(path):
                raise ValueError('Unreviewed modification: ' + path)
            originals[path] = digest
        output[path] = data if isinstance(data, bytes) else data.encode()

    def stage_json(path, data): stage(path, json.dumps(data, indent=2) + '\n')

    groups = json.loads((source / 'data/maps/map_groups.json').read_text())
    layouts = json.loads((source / 'data/layouts/layouts.json').read_text())
    by_layout = {l['id']: l for l in layouts['layouts']}
    maps, preserved = {}, {}
    geometry = []

    def ocean(name, width, height, frlg=True, cell=None):
        ident = 'MAP_' + name.upper()
        base = 'data/layouts/' + name
        water = KANTO_WATER if frlg else HOENN_WATER
        layout = dict(id='LAYOUT_' + name.upper(), name=name + '_Layout', width=width, height=height,
            primary_tileset='gTileset_General_Frlg' if frlg else 'gTileset_General',
            secondary_tileset='gTileset_IslandHarbor_Frlg' if frlg else 'gTileset_Pacifidlog',
            border_filepath=base + '/border.bin', blockdata_filepath=base + '/map.bin',
            layout_version='frlg' if frlg else 'emerald', border_width=2, border_height=2)
        layouts['layouts'].append(layout)
        stage(base + '/map.bin', struct.pack('<H', water) * width * height)
        stage(base + '/border.bin', struct.pack('<H', water | 0x400) * 4)
        maps[name] = dict(id=ident, name=name, layout=layout['id'], music='MUS_SURF',
            region='REGION_KANTO' if frlg else 'REGION_HOENN',
            region_map_section='MAPSEC_SIX_ISLAND' if frlg else 'MAPSEC_ROUTE_131',
            requires_flash=False, weather='WEATHER_SUNNY', map_type='MAP_TYPE_OCEAN_ROUTE',
            allow_cycling=False, allow_escaping=False, allow_running=False,
            show_map_name=False, battle_scene='MAP_BATTLE_SCENE_NORMAL',
            connections=[], object_events=[], warp_events=[], coord_events=[], bg_events=[])
        geometry.append(dict(name=name, width=width, height=height, cell=cell))
        return name

    def existing(name):
        if name not in maps:
            maps[name] = json.loads((source / f'data/maps/{name}/map.json').read_text())
            preserved[name] = {k: hashlib.sha256(json.dumps(maps[name].get(k, []), sort_keys=True).encode()).hexdigest()
                               for k in ['object_events', 'warp_events', 'coord_events', 'bg_events']}
        return maps[name]

    def connect(a, direction, b, offset=0):
        # Multiple parallel connections are allowed only for disjoint spans;
        # lower hubs use a 16-tile lane beside the 17-tile harbor at x=24.
        for name, d, other, o in [(a, direction, b, offset), (b, OPPOSITE[direction], a, -offset)]:
            links = maps[name].get('connections') or []
            links.append(dict(map=maps[other]['id'], direction=d, offset=o))
            maps[name]['connections'] = links

    def open_channel(name, x0, x1, y0, y1, water):
        data = maps[name]
        for key in ['object_events', 'warp_events', 'coord_events', 'bg_events']:
            for event in data.get(key, []):
                if x0 <= event.get('x', -1) < x1 and y0 <= event.get('y', -1) < y1:
                    raise ValueError('Channel intersects event: ' + name)
        layout = by_layout[data['layout']]
        path = layout['blockdata_filepath']
        raw = output.get(path, (source / path).read_bytes())
        blocks = list(struct.unpack('<' + 'H' * (len(raw) // 2), raw))
        if not (0 <= x0 < x1 <= layout['width'] and 0 <= y0 < y1 <= layout['height']):
            raise ValueError('Out of bounds channel: ' + name)
        for y in range(y0, y1):
            for x in range(x0, x1): blocks[y * layout['width'] + x] = water
        stage(path, struct.pack('<' + 'H' * len(blocks), *blocks))

    hubs = {}
    for i, (port, cell) in enumerate(zip(PORTS, CELLS)):
        name = ocean(f'JourneyWorldSea{i:02d}', WIDTH, HEIGHT, cell=list(cell))
        hubs[cell] = name
        existing(port)
        maps[name]['region_map_section'] = maps[port]['region_map_section']
        if any(c['direction'] == 'down' for c in maps[port].get('connections') or []):
            raise ValueError('Occupied southern port: ' + port)
        connect(name, 'up', port, 0 if i == 0 else 24)
        if i == 0:
            open_channel(port, 33, 35, 31, 40, KANTO_WATER)
        else:
            # Native FRLG harbor shares one layout. No sailor or ship is moved.
            open_channel(port, 3, 7, 5, 13, KANTO_WATER)

    for (col, row), name in hubs.items():
        if (col + 1, row) in hubs:
            connect(name, 'right', hubs[col + 1, row])
        if (col, row + 1) in hubs:
            lane = ocean(f'JourneyWorldLane{col}{row}', 16, 48)
            connect(name, 'down', lane)
            connect(lane, 'down', hubs[col, row + 1])

    # Pacifidlog's right-hand route keeps its native links to the town and
    # Route130. Only an event-free southern ocean edge is opened.
    route = existing('Route131')
    if any(c['direction'] == 'down' for c in route['connections']):
        raise ValueError('Occupied Route131 southern edge')
    open_channel('Route131', 48, 60, 33, 40, HOENN_WATER)
    lane = ocean('JourneyPacifidlogSea', 12, 48, frlg=False)
    connect('Route131', 'down', lane, 48)
    connect(lane, 'right', hubs[1, 2])

    new_maps = [g['name'] for g in geometry]
    groups['group_order'].append('JourneyWorldOcean')
    groups['JourneyWorldOcean'] = new_maps
    stage_json('data/maps/map_groups.json', groups)
    stage_json('data/layouts/layouts.json', layouts)
    for name, data in maps.items(): stage_json(f'data/maps/{name}/map.json', data)
    scripts = (source / 'data/event_scripts.s').read_text()
    for name in new_maps:
        stage(f'data/maps/{name}/scripts.inc', name + '_MapScripts::\n\t.byte 0\n')
        scripts += f'\n\t.include "data/maps/{name}/scripts.inc"\n'
    stage('data/event_scripts.s', scripts)
    # Preflight all source guards before writing anything.
    for path, raw in output.items():
        target = source / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    report = dict(status='experimental_ocean_grid_not_complete_campaign', revision=1,
        source_commit=PIN, routes=geometry, ports=PORTS, cells=CELLS,
        connections={name: maps[name]['connections'] for name in new_maps + PORTS + ['Route131']},
        preserved_event_sha256=preserved, original_sha256=originals,
        prepared_sha256={p: hashlib.sha256(raw).hexdigest() for p, raw in output.items()},
        route131_endpoint='proposed_pending_user_confirmation',
        cinnabar_south_endpoint='pending_geographic_confirmation',
        released_rom_changed=False, full_story_validated=False)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source), indent=2))
