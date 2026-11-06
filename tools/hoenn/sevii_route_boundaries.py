"""Close unconnected marine limits with complete native reef metatiles.

Only water cells on outer map edges are candidates. A real connecting span,
dry land, geology, events and every existing passage remain intact.
"""
import json
from pathlib import Path
import re
import struct

from badge_story_layer import read
from generated_world_marine import PRIMARY_FAMILIES
from render_sea_maps import MapRenderer

CARDINAL = {'left', 'right', 'up', 'down'}
SEVII_TOWNS = {name+'Island_Frlg' for name in ('One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven')}


class Terrain:
    def __init__(self, source, layer=None):
        self.source, self.layer = Path(source), layer
        self.read = lambda p: read(layer, p) if layer else (self.source/p).read_bytes()
        self.layout_data = json.loads(self.read('data/layouts/layouts.json'))
        self.layouts = {r['id']:r for r in self.layout_data['layouts']}
        self.maps = {p.parent.name:json.loads(self.read(p.relative_to(self.source).as_posix()))
                     for p in (self.source/'data/maps').glob('*/map.json')}
        self.by_id = {row['id']:name for name,row in self.maps.items()}
        self.blocks, self.originals = {}, {}
        enum = (self.source/'include/constants/metatile_behaviors.h').read_text()
        enum = re.sub(r'/\*.*?\*/|//[^\n]*', '', enum, flags=re.S)
        body = enum.split('enum {',1)[1].split('}',1)[0]
        assert '=' not in body, 'Resolve explicitly assigned native behavior enums first'
        self.behavior_ids = {name:i for i,name in enumerate(re.findall(r'\b(?:MB_\w+|NUM_METATILE_BEHAVIORS)\b',body))}
        flags = (self.source/'src/metatile_behavior.c').read_text()
        self.water_behaviors = {self.behavior_ids[name] for name,expr in
            re.findall(r'\[(MB_\w+)\]\s*=\s*([^,\n]+)',flags) if 'TILE_FLAG_SURFABLE' in expr}
        self.renderer = MapRenderer(self.source)
        self.attrs = {}

    def layout(self, name):
        return self.layouts[self.maps[name]['layout']]

    def grid(self, name):
        path = self.layout(name)['blockdata_filepath']
        if path not in self.blocks:
            raw = self.read(path)
            self.originals[path] = raw
            self.blocks[path] = list(struct.unpack('<'+'H'*(len(raw)//2),raw))
        return self.blocks[path]

    def behavior(self, name, word):
        layout = self.layout(name)
        frlg = layout['layout_version']=='frlg'
        cutoff,size = (640,4) if frlg else (512,2)
        mid = word&1023
        bank = layout['primary_tileset' if mid<cutoff else 'secondary_tileset']
        if (bank,size) not in self.attrs:
            body = re.search(r'const struct Tileset '+re.escape(bank)+r'\s*=\s*\{(.*?)\};',self.renderer.headers,re.S)[1]
            symbol = re.search(r'\.metatileAttributes\s*=\s*(\w+)',body)[1]
            path = re.search(r'\b'+symbol+r'\[\].*?"([^"]+)"',self.renderer.metas)[1]
            raw = self.read(path)
            self.attrs[bank,size] = [int.from_bytes(raw[i:i+size],'little') for i in range(0,len(raw),size)]
        return self.attrs[bank,size][mid if mid<cutoff else mid-cutoff]&(511 if frlg else 255)

    def water(self, name, word):
        return self.behavior(name,word) in self.water_behaviors

    def neighbor(self, name, x, y, direction):
        """Return an actual connected target cell, regardless of its terrain."""
        layout = self.layout(name)
        for connection in self.maps[name].get('connections') or []:
            if connection['direction']!=direction:
                continue
            other = self.by_id[connection['map']]
            target = self.layout(other)
            offset = connection['offset']
            xx = x-offset if direction in ('up','down') else x+target['width'] if direction=='left' else x-layout['width']
            yy = y-offset if direction in ('left','right') else y+target['height'] if direction=='up' else y-layout['height']
            if 0<=xx<target['width'] and 0<=yy<target['height']:
                return other,xx,yy
        return None

    def perimeter(self, name):
        width,height = (self.layout(name)[key] for key in ('width','height'))
        for x in range(width):
            yield x,0,'up',x,-1
            yield x,height-1,'down',x,height
        for y in range(height):
            yield 0,y,'left',-1,y
            yield width-1,y,'right',width,y


def selected_maps(terrain):
    return sorted(name for name,mapping in terrain.maps.items()
        if terrain.layout(name)['primary_tileset'] in PRIMARY_FAMILIES
        and (mapping['map_type']=='MAP_TYPE_OCEAN_ROUTE' and (name.startswith('Journey') or 'Island_Harbor' in name)
             or name in SEVII_TOWNS
             or name.startswith('OneIsland_') and mapping['map_type']=='MAP_TYPE_ROUTE'
             or name=='ThreeIsland_Port_Frlg'))


def repair(layer):
    # Geography is prepared first, then this pass closes only its genuine
    # outer limits; new Surf openings are protected by actual connections.
    from sevii_south_approach import repair as south_approach
    approach = south_approach(layer)
    from sevii_save_geometry import repair as save_geometry
    migration = save_geometry(layer)
    from sevii_south_projection import repair as south_projection
    projection = south_projection(layer)
    terrain = Terrain(layer.source,layer)
    inspected = selected_maps(terrain)
    changes, borders = [], []
    for name in inspected:
        layout = terrain.layout(name)
        words = terrain.grid(name)
        width = layout['width']
        small = PRIMARY_FAMILIES[layout['primary_tileset']][1]
        events = {(e['x'],e['y']) for key in ('object_events','warp_events','coord_events','bg_events')
                  for e in terrain.maps[name].get(key,[]) }
        openings = {(x,y) for x,y,direction,xx,yy in terrain.perimeter(name)
                    if terrain.neighbor(name,xx,yy,direction) is not None}
        cells = {}
        for x,y,direction,xx,yy in terrain.perimeter(name):
            # A corner can be an opening on either incident side.
            if (x,y) in openings:
                continue
            at = y*width+x
            before = words[at]
            if before&1023==small or not terrain.water(name,before):
                continue
            assert (x,y) not in events, ('Event occupies an unconnected outer water edge',name,x,y)
            # One complete native reef; no boulder quadrants, copied pixels,
            # inherited land height or invisible out-of-map collision.
            after = 0x1400|small
            cells[at] = dict(tile=[x,y],before=before,after=after)
            words[at] = after
        if cells:
            changes.append(dict(map=name,path=layout['blockdata_filepath'],cells=list(cells.values())))
        frlg = layout['layout_version']=='frlg'
        path = 'data/layouts/JourneyMarineLimits/'+('frlg' if frlg else 'emerald')+'-border.bin'
        raw = struct.pack('<4H',*([0x1400|small]*4))
        layer.stage(path,raw)
        old = {key:layout.get(key) for key in ('border_filepath','border_width','border_height')}
        layout.update(border_filepath=path,border_width=2,border_height=2)
        borders.append(dict(map=name,before=old,path=path,block=0x1400|small))
    for path,words in terrain.blocks.items():
        raw = struct.pack('<'+'H'*len(words),*words)
        if raw!=terrain.originals[path]:
            layer.stage(path,raw)
    layer.stage('data/layouts/layouts.json',json.dumps(terrain.layout_data,indent=2)+'\n')
    return dict(kind='sevii-route-boundaries-repair',approach=approach,migration=migration,
                projection=projection,inspected_maps=inspected,
                outer_water_changes=changes,borders=borders,
                existing_connection_spans_preserved=True,complete_native_small_reef_metatiles=True,
                dry_land_geology_buildings_and_events_preserved=True)
