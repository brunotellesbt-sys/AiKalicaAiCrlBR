"""Experimental native Rota 127–Rota 21 seam on the pinned multiregion base.

This is NOT the complete custom-game migration: it preserves native map events,
opens only event-free ocean channels and fixes cross-tileset camera transitions.
"""
import hashlib
import json
from pathlib import Path
import struct

PIN = 'e05c82865d38a6638173fd30b2c830d1250aa50d'
SEA = 'JourneyHoennCrossing'
WIDTH, HEIGHT = 48, 24
HOENN_WATER, KANTO_WATER = 0x1170, 0x112B


def prepare(source):
    source = Path(source)
    acquired = json.loads((source / '.source-acquired.json').read_text())
    if acquired['commit'] != PIN: raise ValueError('Unexpected multiregion base')
    marker = source / '.journey-hoenn-crossing'
    if marker.exists():
        report = json.loads(marker.read_text())
        if report.get('prototype_revision') != 4:
            raise ValueError('Older crossing prototype; prepare a fresh source')
        for path, digest in report['prepared_sha256'].items():
            if hashlib.sha256((source / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Modified prepared file: ' + path)
        return report
    hashes = {}

    def write(path, value):
        destination = source / path
        old = destination.read_bytes() if destination.exists() else None
        if old is not None and path in acquired['sha256']:
            if hashlib.sha256(old).hexdigest() != acquired['sha256'][path]:
                raise ValueError('Pre-existing modification: ' + path)
        hashes[path] = hashlib.sha256(old).hexdigest() if old is not None else None
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(value if isinstance(value, bytes) else value.encode())

    def write_json(path, value): write(path, json.dumps(value, indent=2) + '\n')
    def replace(path, old, new):
        text = (source / path).read_text()
        if text.count(old) != 1: raise ValueError('Unexpected source anchor: ' + path)
        write(path, text.replace(old, new))

    groups = json.loads((source / 'data/maps/map_groups.json').read_text())
    layouts = json.loads((source / 'data/layouts/layouts.json').read_text())
    by_id = {layout['id']: layout for layout in layouts['layouts']}
    ports = [('Route127', 'right', 30, HOENN_WATER, 73, 80, 30, 54),
             ('Route21_South_Frlg', 'left', 10, KANTO_WATER, 0, 7, 10, 34)]
    preserved_events = {}
    for name, direction, offset, water, x0, x1, y0, y1 in ports:
        path = f'data/maps/{name}/map.json'
        map_data = json.loads((source / path).read_text())
        preserved_events[name] = {key: hashlib.sha256(json.dumps(map_data.get(key, []), sort_keys=True).encode()).hexdigest()
                                 for key in ['object_events', 'warp_events', 'coord_events', 'bg_events']}
        if any(c['direction'] == direction for c in map_data.get('connections') or []):
            raise ValueError('Occupied map edge: ' + name)
        for key in ['object_events', 'warp_events', 'coord_events', 'bg_events']:
            if any(x0 <= e.get('x', -1) < x1 and y0 <= e.get('y', -1) < y1 for e in map_data.get(key, [])):
                raise ValueError('Channel intersects a map event: ' + name)
        map_data['connections'].append(dict(map='MAP_JOURNEY_HOENN_CROSSING', offset=offset, direction=direction))
        write_json(path, map_data)
        layout = by_id[map_data['layout']]
        raw = (source / layout['blockdata_filepath']).read_bytes()
        blocks = list(struct.unpack('<' + 'H' * (len(raw) // 2), raw))
        for y in range(y0, y1):
            for x in range(x0, x1): blocks[y * layout['width'] + x] = water
        write(layout['blockdata_filepath'], struct.pack('<' + 'H' * len(blocks), *blocks))

    connections = [dict(map='MAP_ROUTE127', direction='left', offset=-30),
                   dict(map='MAP_ROUTE21_SOUTH', direction='right', offset=-10)]
    data = dict(id='MAP_JOURNEY_HOENN_CROSSING', name=SEA, layout='LAYOUT_JOURNEY_HOENN_CROSSING',
        music='MUS_SURF', region='REGION_HOENN', region_map_section='MAPSEC_ROUTE_127',
        requires_flash=False, weather='WEATHER_SUNNY', map_type='MAP_TYPE_OCEAN_ROUTE',
        allow_cycling=False, allow_escaping=False, allow_running=False, show_map_name=False,
        battle_scene='MAP_BATTLE_SCENE_NORMAL', connections=connections,
        object_events=[], warp_events=[], coord_events=[], bg_events=[])
    write_json(f'data/maps/{SEA}/map.json', data)
    write(f'data/maps/{SEA}/scripts.inc', f'{SEA}_MapScripts::\n\t.byte 0\n')
    groups['group_order'].append('JourneyHoennSea'); groups['JourneyHoennSea'] = [SEA]
    write_json('data/maps/map_groups.json', groups)
    base = f'data/layouts/{SEA}'
    write(base + '/map.bin', struct.pack('<H', HOENN_WATER) * WIDTH * HEIGHT)
    write(base + '/border.bin', struct.pack('<H', HOENN_WATER | 0x400) * 4)
    layouts['layouts'].append(dict(id=data['layout'], name=SEA + '_Layout', width=WIDTH, height=HEIGHT,
        primary_tileset='gTileset_General', secondary_tileset='gTileset_Mossdeep',
        border_filepath=base + '/border.bin', blockdata_filepath=base + '/map.bin', layout_version='emerald'))
    write_json('data/layouts/layouts.json', layouts)
    path = 'data/event_scripts.s'
    write(path, (source / path).read_text() + f'\n\t.include "data/maps/{SEA}/scripts.inc"\n')

    # The native camera only refreshes the secondary tileset. A cross-region
    # sea seam also changes primary gfx, palettes and animated water tiles.
    replace('src/overworld.c', 'void LoadMapFromCameraTransition(u8 mapGroup, u8 mapNum)\n{',
            'void LoadMapFromCameraTransition(u8 mapGroup, u8 mapNum)\n{\n    const struct Tileset *oldPrimary = gMapHeader.mapLayout->primaryTileset;\n    bool32 oldFrlgFormat = gMapHeader.mapLayout->isFrlg;')
    # Apply both substitutions in one write so original-hash checking remains
    # strict rather than treating the first deliberate patch as user edits.
    path = 'src/overworld.c'; text = (source / path).read_text()
    anchor = '    CopySecondaryTilesetToVramUsingHeap(gMapHeader.mapLayout);\n'
    if text.count(anchor) != 1: raise ValueError('Ambiguous camera graphics reload')
    patch = '''    if (oldPrimary != gMapHeader.mapLayout->primaryTileset)
    {
        CopyPrimaryTilesetToVram(gMapHeader.mapLayout);
        LoadMapTilesetPalettes(gMapHeader.mapLayout);
        InitTilesetAnimations();
    }
'''
    (source / path).write_text(text.replace(anchor, patch + anchor))
    text = (source / path).read_text()
    anchor = '    ApplyCurrentWarp();\n    LoadCurrentMapData();\n    LoadObjEventTemplatesFromHeader();'
    if text.count(anchor) != 1: raise ValueError('Ambiguous camera map load')
    patch = '''    ApplyCurrentWarp();
    LoadCurrentMapData();
    if (oldFrlgFormat != gMapHeader.mapLayout->isFrlg)
    {
        u32 i;
        u16 water = gMapHeader.mapLayout->isFrlg ? 0x112B : 0x1170;
        // The saved camera window also contains metatile IDs from the old
        // format. Both sides of this seam are an event-free ocean apron.
        for (i = 0; i < ARRAY_COUNT(gSaveBlock1Ptr->mapView); i++)
            gSaveBlock1Ptr->mapView[i] = water;
    }
    LoadObjEventTemplatesFromHeader();'''
    (source / path).write_text(text.replace(anchor, patch))

    # Connection previews are rendered in the CURRENT map's format. The only
    # foreign-format connection is this sea bridge, whose seven-tile apron is
    # guaranteed event-free ocean by the checks above. Convert its ocean ID.
    replace('src/fieldmap.c', '        CpuCopy16(src, dest, width * 2);', '''        if (connectedMapHeader->mapLayout->isFrlg != gMapHeader.mapLayout->isFrlg)
        {
            int j;
            u16 water = gMapHeader.mapLayout->isFrlg ? 0x112B : 0x1170;
            for (j = 0; j < width; j++)
                dest[j] = water;
        }
        else
            CpuCopy16(src, dest, width * 2);''')
    # Refresh the entire hardware tilemap after advancing its circular offset.
    # Reloading gfx alone leaves old-region tile indices in the visible area.
    path = 'src/field_camera.c'
    text = (source / path).read_text()
    anchor = '        CameraMove(deltaX, deltaY);'
    redraw = '        RedrawMapSlicesForCameraUpdate(&sFieldCameraOffset, deltaX * 2, deltaY * 2);'
    if text.count(anchor) != 2 or text.count(redraw) != 2:
        raise ValueError('Unexpected camera update hooks')
    text = text.replace(anchor, '        bool32 oldFrlgFormat = gMapHeader.mapLayout->isFrlg;\n' + anchor)
    text = text.replace(redraw, redraw + '\n        if (oldFrlgFormat != gMapHeader.mapLayout->isFrlg)\n            DrawWholeMapView();')
    write(path, text)
    report = dict(status='experimental_crossing_not_complete_migration', prototype_revision=4, source_commit=PIN,
        maps=[p[0] for p in ports], bridge=SEA, bridge_connections=connections,
        original_sha256=hashes, preserved_event_sha256=preserved_events,
        prepared_sha256={path: hashlib.sha256((source / path).read_bytes()).hexdigest() for path in hashes},
        custom_journey_migrated=False, full_story_validated=False)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args(); print(json.dumps(prepare(args.source), indent=2))
