"""Continue Route114's western lake to Cinnabar and Hoenn's western coast.

Layer on the pinned eastern-ocean candidate. Keep all native map events and
connections; disconnect the superseded Route21/Route127 prototype crossing.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from prepare_crossing import PIN, HOENN_WATER, KANTO_WATER


def prepare(source):
    source = Path(source)
    east = json.loads((source / '.journey-worldsea').read_text())
    crossing = json.loads((source / '.journey-hoenn-crossing').read_text())
    original = json.loads((source / '.source-acquired.json').read_text())
    if east['source_commit'] != PIN or east['revision'] != 1:
        raise ValueError('Prepare the eastern ocean revision 1 first')
    marker = source / '.journey-westsea'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            if hashlib.sha256((source / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Modified western ocean output: ' + path)
        return report
    expected = original['sha256'] | crossing['prepared_sha256'] | east['prepared_sha256']
    outputs, originals = {}, {}

    def stage(path, data):
        target = source / path
        if path not in originals:
            digest = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
            if digest is not None and digest != expected.get(path):
                raise ValueError('Unreviewed modification: ' + path)
            originals[path] = digest
        outputs[path] = data if isinstance(data, bytes) else data.encode()

    def stage_json(path, data): stage(path, json.dumps(data, indent=2) + '\n')
    layouts = json.loads((source / 'data/layouts/layouts.json').read_text())
    by_layout = {l['id']: l for l in layouts['layouts']}
    groups = json.loads((source / 'data/maps/map_groups.json').read_text())
    maps, preserved, new_maps = {}, {}, []

    def existing(name):
        data = json.loads((source / f'data/maps/{name}/map.json').read_text())
        maps[name] = data
        preserved[name] = {k: hashlib.sha256(json.dumps(data.get(k, []), sort_keys=True).encode()).hexdigest()
                           for k in ['object_events', 'warp_events', 'coord_events', 'bg_events']}

    def ocean(name, width, height, frlg=False):
        water = KANTO_WATER if frlg else HOENN_WATER
        base = 'data/layouts/' + name
        layout = dict(id='LAYOUT_' + name.upper(), name=name + '_Layout', width=width, height=height,
            primary_tileset='gTileset_General_Frlg' if frlg else 'gTileset_General',
            secondary_tileset='gTileset_CinnabarIsland' if frlg else 'gTileset_Fallarbor',
            border_filepath=base + '/border.bin', blockdata_filepath=base + '/map.bin',
            layout_version='frlg' if frlg else 'emerald', border_width=2, border_height=2)
        layouts['layouts'].append(layout)
        stage(base + '/map.bin', struct.pack('<H', water) * width * height)
        stage(base + '/border.bin', struct.pack('<H', water | 0x400) * 4)
        maps[name] = dict(id='MAP_' + name.upper(), name=name, layout=layout['id'], music='MUS_SURF',
            region='REGION_KANTO' if frlg else 'REGION_HOENN',
            region_map_section='MAPSEC_CINNABAR_ISLAND' if frlg else 'MAPSEC_ROUTE_114',
            requires_flash=False, weather='WEATHER_SUNNY', map_type='MAP_TYPE_OCEAN_ROUTE',
            allow_cycling=False, allow_escaping=False, allow_running=False, show_map_name=False,
            battle_scene='MAP_BATTLE_SCENE_NORMAL', connections=[],
            object_events=[], warp_events=[], coord_events=[], bg_events=[])
        new_maps.append(name)

    def connect(a, direction, b, offset=0):
        opposite = dict(up='down', down='up', left='right', right='left')
        for name, d, other, o in [(a, direction, b, offset), (b, opposite[direction], a, -offset)]:
            links = maps[name].get('connections') or []
            links.append(dict(map=maps[other]['id'], direction=d, offset=o))
            maps[name]['connections'] = links

    def open_channel(name, bounds, water):
        x0, x1, y0, y1 = bounds
        for key in ['object_events', 'warp_events', 'coord_events', 'bg_events']:
            if any(x0 <= e.get('x', -1) < x1 and y0 <= e.get('y', -1) < y1 for e in maps[name].get(key, [])):
                raise ValueError('Channel intersects event: ' + name)
        layout = by_layout[maps[name]['layout']]
        path = layout['blockdata_filepath']
        raw = (source / path).read_bytes()
        blocks = list(struct.unpack('<' + 'H' * (len(raw) // 2), raw))
        if not (0 <= x0 < x1 <= layout['width'] and 0 <= y0 < y1 <= layout['height']):
            raise ValueError('Out of bounds channel')
        for y in range(y0, y1):
            for x in range(x0, x1): blocks[y * layout['width'] + x] = water
        stage(path, struct.pack('<' + 'H' * len(blocks), *blocks))

    for name in ['CinnabarIsland_Frlg', 'Route114', 'Route115', 'Route105', 'Route127', 'Route21_South_Frlg']:
        existing(name)
    for name in ['Route127', 'Route21_South_Frlg']:
        maps[name]['connections'] = [c for c in maps[name]['connections'] if c['map'] != 'MAP_JOURNEY_HOENN_CROSSING']
    maps_path = 'data/maps/JourneyHoennCrossing/map.json'
    old_bridge = json.loads((source / maps_path).read_text())
    old_bridge['connections'] = []
    stage_json(maps_path, old_bridge)
    ocean('JourneyCinnabarSouthSea', 24, 48, frlg=True)
    ocean('JourneyWestRiver', 48, 14)
    ocean('JourneyRustboroCoast', 48, 80)
    ocean('JourneyRustboroGate', 12, 24)
    ocean('JourneyDewfordCoast', 48, 80)
    ocean('JourneyDewfordGate', 12, 24)
    connect('CinnabarIsland_Frlg', 'down', 'JourneyCinnabarSouthSea')
    connect('JourneyCinnabarSouthSea', 'down', 'JourneyWestRiver')
    # Route114's pre-existing left link starts at y40; this new lake link
    # spans y10..23, avoiding the secret base at y27 and hidden item at y30.
    connect('JourneyWestRiver', 'right', 'Route114', -10)
    connect('JourneyWestRiver', 'down', 'JourneyRustboroCoast')
    connect('JourneyRustboroCoast', 'right', 'JourneyRustboroGate', 24)
    connect('JourneyRustboroGate', 'right', 'Route115', -24)
    connect('JourneyRustboroCoast', 'down', 'JourneyDewfordCoast')
    connect('JourneyDewfordCoast', 'right', 'JourneyDewfordGate', 30)
    connect('JourneyDewfordGate', 'right', 'Route105', -30)
    channels = {'CinnabarIsland_Frlg': (8, 16, 14, 20), 'Route114': (0, 12, 10, 24),
                'Route115': (0, 7, 24, 48), 'Route105': (0, 7, 30, 54)}
    for name, bounds in channels.items():
        open_channel(name, bounds, KANTO_WATER if name.endswith('_Frlg') else HOENN_WATER)
    groups['group_order'].append('JourneyWesternOcean')
    groups['JourneyWesternOcean'] = new_maps
    stage_json('data/maps/map_groups.json', groups)
    stage_json('data/layouts/layouts.json', layouts)
    scripts = (source / 'data/event_scripts.s').read_text()
    for name in new_maps:
        stage(f'data/maps/{name}/scripts.inc', name + '_MapScripts::\n\t.byte 0\n')
        scripts += f'\n\t.include "data/maps/{name}/scripts.inc"\n'
    stage('data/event_scripts.s', scripts)
    for name, data in maps.items(): stage_json(f'data/maps/{name}/map.json', data)
    for path, raw in outputs.items():
        target = source / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
    report = dict(status='experimental_western_ocean_not_complete_campaign', revision=1, source_commit=PIN,
        channels=channels, maps=new_maps,
        connections={name: data['connections'] for name, data in maps.items() if name not in ['Route127', 'Route21_South_Frlg']},
        preserved_event_sha256=preserved, original_sha256=originals,
        prepared_sha256={p: hashlib.sha256(raw).hexdigest() for p, raw in outputs.items()},
        superseded_crossing_disconnected=True, released_rom_changed=False, full_story_validated=False)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source), indent=2))
