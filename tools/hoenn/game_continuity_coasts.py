"""Load compatible coastal banks before crossing into neighboring towns.

The neighboring block IDs are drawn using the current map's banks. Extended
terminal IDs therefore need the integrated bank on the ocean approach too.
No terrain, event, connection, graphics or animation callback is changed.
"""
import copy
import hashlib
import json
from pathlib import Path
import re
import struct

from badge_story_layer import read
from render_sea_maps import MapRenderer

PATH = 'data/layouts/layouts.json'
PRIMARY = 'gTileset_JourneySeviiSea'
ASSIGNMENTS = {
    'JourneySurfLink01000': (PRIMARY, 'gTileset_JourneySeviiIntegrated45'),
    'JourneySurfLink05400': (PRIMARY, 'gTileset_JourneySeviiIntegrated123'),
    'JourneySurfLink05301': (PRIMARY, 'gTileset_JourneySeviiIntegrated123'),
    'JourneySurfLink05200': (PRIMARY, 'gTileset_JourneySeviiIntegrated67'),
    'JourneySurfLink00600': (PRIMARY, 'gTileset_SeviiIslands45'),
    'JourneySurfLink00000': (PRIMARY, 'gTileset_SeviiIslands67'),
    'JourneyCinnabarSouthSea': (PRIMARY, 'gTileset_JourneyKantoSeaCinnabarIsland'),
    'JourneyLavenderApproach': (PRIMARY, 'gTileset_JourneyKantoSeaLavenderTown'),
    'JourneySurfLink02901': (PRIMARY, 'gTileset_FuchsiaCity'),
    'JourneyFuchsiaSea': (PRIMARY, 'gTileset_FuchsiaCity'),
    'JourneyTanobyDawnSea': (PRIMARY, 'gTileset_IslandHarbor_Frlg'),
    'JourneySouthwestSeviiPassage': (PRIMARY, 'gTileset_IslandHarbor_Frlg'),
    'JourneyOneTwoPassage': (PRIMARY, 'gTileset_IslandHarbor_Frlg'),
    'JourneyTwoThreePassage': (PRIMARY, 'gTileset_JourneySeviiIntegrated123'),
    'JourneyFuchsiaInlet': (PRIMARY, 'gTileset_FuchsiaCity'),
    'JourneyKantoSouthWestSea': (PRIMARY, 'gTileset_LavenderTown'),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def camera_pairs(layout, neighbor, connection):
    """Conservative visible strip: eight columns or six rows across the seam."""
    width,height = layout['width'],layout['height']
    tw,th = neighbor['width'],neighbor['height']
    direction,offset = connection['direction'],connection['offset']
    if direction in ('left','right'):
        for y in range(max(0,offset),min(height,offset+th)):
            for depth in range(min(8,width,tw)):
                yield ((depth if direction=='left' else width-1-depth,y),
                       (tw-1-depth if direction=='left' else depth,y-offset))
    else:
        assert direction in ('up','down')
        for x in range(max(0,offset),min(width,offset+tw)):
            for depth in range(min(6,height,th)):
                yield ((x,depth if direction=='up' else height-1-depth),
                       (x-offset,th-1-depth if direction=='up' else depth))


def repair(layer):
    source = Path(layer.source)
    original = read(layer,PATH)
    data = json.loads(original)
    layouts = {row['id']:row for row in data['layouts']}
    before = copy.deepcopy(layouts)
    maps = {p.parent.name:json.loads(read(layer,p.relative_to(source).as_posix()))
            for p in (source/'data/maps').glob('*/map.json')}
    by_id = {row['id']:name for name,row in maps.items()}
    renderer = MapRenderer(source)
    renderer.layouts = layouts
    attr_cache = {}
    def attribute(name,mid):
        layout = layouts[maps[name]['layout']]
        assert layout['layout_version']=='frlg'
        bank = layout['primary_tileset' if mid<640 else 'secondary_tileset']
        if bank not in attr_cache:
            body = re.search(r'const struct Tileset '+bank+r'\s*=\s*\{(.*?)\};',renderer.headers,re.S)[1]
            symbol = re.search(r'\.metatileAttributes\s*=\s*(\w+)',body)[1]
            path = re.search(r'\b'+symbol+r'\[\].*?"([^"]+)"',renderer.metas)[1]
            attr_cache[bank] = read(layer,path)
        index = mid if mid<640 else mid-640
        raw = attr_cache[bank][4*index:4*index+4]
        assert len(raw)==4,(name,bank,mid)
        return raw
    grids = {}
    def grid(name):
        if name not in grids:
            layout = layouts[maps[name]['layout']]
            raw = read(layer,layout['blockdata_filepath'])
            grids[name] = struct.unpack('<'+'H'*(len(raw)//2),raw)
        return grids[name]
    def tile(name,word):
        return renderer.render(name,values=[word],dimensions=(1,1),npcs=False)[0].tobytes()

    records = []
    for name,(primary,secondary) in ASSIGNMENTS.items():
        layout = layouts[maps[name]['layout']]
        assert layout['layout_version']=='frlg'
        old = dict(layout)
        used = sorted({word&1023 for word in grid(name)})
        old_pixels = {mid:digest(tile(name,mid)) for mid in used}
        old_attrs = {mid:attribute(name,mid) for mid in used}
        layout.update(primary_tileset=primary,secondary_tileset=secondary)
        assert layout!=old,('No-op bank assignment',name)
        assert all(layout[key]==value for key,value in old.items()
                   if key not in ('primary_tileset','secondary_tileset'))
        assert {mid:digest(tile(name,mid)) for mid in used}==old_pixels,('Own artwork changed',name)
        assert {mid:attribute(name,mid) for mid in used}==old_attrs,('Own behavior changed',name)
        records.append(dict(map=name,layout=layout['id'],before_primary=old['primary_tileset'],
            before_secondary=old['secondary_tileset'],primary=primary,secondary=secondary,
            own_used_metatiles=used,own_pixels_sha256=old_pixels,
            own_attribute_bytes={mid:raw.hex() for mid,raw in old_attrs.items()},
            blockdata_sha256=digest(read(layer,layout['blockdata_filepath'])),
            map_json_sha256=digest(read(layer,f'data/maps/{name}/map.json')),
            all_own_map_pixels_and_attributes_unchanged=True))

    seams = []
    for name,mapping in sorted(maps.items()):
        for connection in mapping.get('connections') or []:
            if connection['direction'] not in ('up','down','left','right'):
                continue
            neighbor = by_id[connection['map']]
            if name not in ASSIGNMENTS and neighbor not in ASSIGNMENTS:
                continue
            layout,other = layouts[mapping['layout']],layouts[maps[neighbor]['layout']]
            assert layout['layout_version']==other['layout_version']=='frlg'
            count = 0
            for (x,y),(xx,yy) in camera_pairs(layout,other,connection):
                for current,canonical,nx,ny in ((name,neighbor,xx,yy),(neighbor,name,x,y)):
                    width = layouts[maps[canonical]['layout']]['width']
                    word = grid(canonical)[ny*width+nx]
                    assert tile(current,word)==tile(canonical,word),(
                        'Neighbor pixels do not fit the loaded camera bank',current,canonical,nx,ny,hex(word))
                    assert attribute(current,word&1023)==attribute(canonical,word&1023),(
                        'Neighbor attributes do not fit the loaded camera bank',current,canonical,nx,ny,hex(word))
                    count += 1
            seams.append(dict(map=name,neighbor=neighbor,connection=connection,
                              compared_cells_in_both_cameras=count))
    changed = {maps[name]['layout'] for name in ASSIGNMENTS}
    assert all(layout==before[key] for key,layout in layouts.items() if key not in changed)
    after = (json.dumps(data,indent=2)+'\n').encode()
    layer.stage(PATH,after)
    return dict(kind='game-continuity-coast-bank-repair',changed_paths=[PATH],
        before_sha256=digest(original),after_sha256=digest(after),assignments=records,
        affected_cardinal_seams=seams,own_terrain_art_and_attributes_unchanged=True,
        visible_neighbor_metatile_art_and_attributes_compatible=True,
        camera_strip_columns=8,camera_strip_rows=6,
        all_other_layouts_and_all_terrain_events_connections_unchanged=True,
        graphics_palettes_callbacks_and_metatile_files_unchanged=True,
        actual_native_approach_crossing_return_and_eight_water_phases_required=True)
