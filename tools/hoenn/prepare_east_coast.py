"""Open three Hoenn east-coast entrances and Fuchsia's sea to the Sevii grid."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from prepare_crossing import PIN, HOENN_WATER, KANTO_WATER


def prepare(source):
    source = Path(source)
    marker = source / '.journey-east-coast'
    if marker.exists():
        report = json.loads(marker.read_text())
        for p, digest in report['prepared_sha256'].items():
            if hashlib.sha256((source / p).read_bytes()).hexdigest() != digest:
                raise ValueError('Modified east coast output: ' + p)
        if 'input_sha256' not in report:
            acquired=json.loads((source/'.source-acquired.json').read_text())
            report['input_sha256']={f'data/maps/Route{n}/map.json':acquired['sha256'][f'data/maps/Route{n}/map.json'] for n in range(124,132)}
            marker.write_text(json.dumps(report,indent=2)+'\n')
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    if acquired['commit'] != PIN: raise ValueError('Unexpected base')
    expected = dict(acquired['sha256'])
    for p in ['.journey-hoenn-crossing', '.journey-worldsea', '.journey-westsea', '.journey-region-state']:
        expected.update(json.loads((source / p).read_text())['prepared_sha256'])
    outputs, originals, maps, preserved = {}, {}, {}, {}
    groups = json.loads((source / 'data/maps/map_groups.json').read_text())
    layouts = json.loads((source / 'data/layouts/layouts.json').read_text())
    by_layout = {l['id']: l for l in layouts['layouts']}

    def stage(p, value):
        target = source / p
        digest = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
        if digest is not None and digest != expected.get(p): raise ValueError('Unreviewed modification: ' + p)
        originals[p] = digest; outputs[p] = value if isinstance(value, bytes) else value.encode()
    def stage_json(p, value): stage(p, json.dumps(value, indent=2) + '\n')
    def existing(name):
        if name in maps: return
        maps[name] = json.loads((source / f'data/maps/{name}/map.json').read_text())
        preserved[name] = {k: hashlib.sha256(json.dumps(maps[name].get(k, []), sort_keys=True).encode()).hexdigest()
                           for k in ['object_events', 'warp_events', 'coord_events', 'bg_events']}
    def connect(a, d, b, offset=0):
        opposite = dict(up='down', down='up', left='right', right='left')
        for name, direction, other, off in [(a, d, b, offset), (b, opposite[d], a, -offset)]:
            links = maps[name].get('connections') or []
            links.append(dict(map=maps[other]['id'], direction=direction, offset=off))
            maps[name]['connections'] = links
    new_maps = []
    def ocean(name, height, frlg=False):
        base = 'data/layouts/' + name
        water = KANTO_WATER if frlg else HOENN_WATER
        layout = dict(id='LAYOUT_' + name.upper(), name=name + '_Layout', width=48, height=height,
            primary_tileset='gTileset_General_Frlg' if frlg else 'gTileset_General',
            secondary_tileset='gTileset_FuchsiaCity' if frlg else 'gTileset_Mossdeep',
            border_filepath=base+'/border.bin', blockdata_filepath=base+'/map.bin',
            layout_version='frlg' if frlg else 'emerald', border_width=2, border_height=2)
        layouts['layouts'].append(layout)
        stage(base+'/map.bin', struct.pack('<H', water) * 48 * height)
        stage(base+'/border.bin', struct.pack('<H', water | 0x400) * 4)
        maps[name] = dict(id='MAP_'+name.upper(), name=name, layout=layout['id'], music='MUS_SURF',
            region='REGION_KANTO' if frlg else 'REGION_HOENN',
            region_map_section='MAPSEC_ROUTE_19' if frlg else 'MAPSEC_ROUTE_127',
            requires_flash=False, weather='WEATHER_SUNNY', map_type='MAP_TYPE_OCEAN_ROUTE',
            allow_cycling=False, allow_escaping=False, allow_running=False, show_map_name=False,
            battle_scene='MAP_BATTLE_SCENE_NORMAL', connections=[],
            object_events=[], warp_events=[], coord_events=[], bg_events=[])
        new_maps.append(name)
    channels = {'Route125': (73,80,8,32), 'Route127': (73,80,30,54),
                'Route129': (73,80,8,32), 'Route19_Frlg': (20,24,40,54)}
    for name in list(channels) + ['JourneyWorldSea00', 'JourneyWorldSea04', 'JourneyWorldSea06']:
        existing(name)
    for name, height, frlg in [('JourneyHoennNorthSea',24,False), ('JourneyHoennMiddleSea',24,False),
                               ('JourneyHoennSouthSea',24,False), ('JourneyFuchsiaSea',14,True)]:
        ocean(name, height, frlg)
    connect('Route125','right','JourneyHoennNorthSea',8)
    connect('JourneyHoennNorthSea','right','JourneyWorldSea00',-24)
    connect('Route127','right','JourneyHoennMiddleSea',30)
    connect('JourneyHoennMiddleSea','right','JourneyWorldSea04')
    connect('Route129','right','JourneyHoennSouthSea',8)
    connect('JourneyHoennSouthSea','up','JourneyWorldSea06')
    connect('Route19_Frlg','right','JourneyFuchsiaSea',40)
    connect('JourneyFuchsiaSea','right','JourneyWorldSea00')
    for name, (x0,x1,y0,y1) in channels.items():
        for key in ['object_events','warp_events','coord_events','bg_events']:
            for event in maps[name].get(key, []):
                if x0 <= event.get('x',-1) < x1 and y0 <= event.get('y',-1) < y1:
                    raise ValueError('Channel intersects event: '+name)
        layout = by_layout[maps[name]['layout']]; p = layout['blockdata_filepath']
        raw = (source/p).read_bytes(); blocks = list(struct.unpack('<'+'H'*(len(raw)//2),raw))
        water = KANTO_WATER if name.endswith('_Frlg') else HOENN_WATER
        for y in range(y0,y1):
            for x in range(x0,x1): blocks[y*layout['width']+x] = water
        stage(p,struct.pack('<'+'H'*len(blocks),*blocks))
    groups['group_order'].append('JourneyEastCoast'); groups['JourneyEastCoast'] = new_maps
    stage_json('data/maps/map_groups.json',groups); stage_json('data/layouts/layouts.json',layouts)
    scripts = (source/'data/event_scripts.s').read_text()
    for name in new_maps:
        stage(f'data/maps/{name}/scripts.inc',name+'_MapScripts::\n\t.byte 0\n')
        scripts += f'\n\t.include "data/maps/{name}/scripts.inc"\n'
    stage('data/event_scripts.s',scripts)
    for name, data in maps.items(): stage_json(f'data/maps/{name}/map.json',data)
    for p, raw in outputs.items():
        target=source/p; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(raw)
    report = dict(status='experimental_connected_east_coast_not_complete_campaign',source_commit=PIN,
        maps=new_maps,channels=channels,connections={n:m['connections'] for n,m in maps.items()},
        preserved_event_sha256=preserved,original_sha256=originals,
        input_sha256={f'data/maps/Route{n}/map.json':acquired['sha256'][f'data/maps/Route{n}/map.json'] for n in range(124,132)},
        prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()},
        native_eastern_routes_connected=[f'Route{n}' for n in range(124,132)],
        ever_grande_entrance_preserved=True,full_story_validated=False)
    marker.write_text(json.dumps(report,indent=2)+'\n'); return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--source',type=Path,required=True)
    args=parser.parse_args(); print(json.dumps(prepare(args.source),indent=2))
