"""Extend Treasure Beach's GPS while preserving every old logical position."""
import json
from pathlib import Path
import re

from badge_story_layer import read

PATH = 'src/data/journey_world_position.h'
IDENT = 'MAP_ONE_ISLAND_TREASURE_BEACH'


def repair(layer):
    original = read(layer,PATH).decode()
    array = re.search(r'(sWorldNavigationPixels\[\] = \{)([^}]+)',original)
    packed = list(map(int,array[2].split(',')))
    def descriptor(ident):
        pattern = r'\{(\d+), \(MAP_GROUP\('+ident+r'\)<<8\)\|MAP_NUM\('+ident+r'\), (\d+), (\d+)\}'
        match = re.search(pattern,original)
        assert match, ident
        return match,tuple(map(int,match.groups()))
    desc,(first,width,height) = descriptor(IDENT)
    assert (width,height)==(24,40)
    old = [packed[first+y*width:first+(y+1)*width] for y in range(height)]
    _,(link_first,link_width,link_height) = descriptor('MAP_JOURNEYSURFLINK05000')
    assert (link_width,link_height)==(16,13)
    top = packed[link_first+12*16+8:link_first+13*16]
    fixed = {(x+8,y):old[y][x] for y in range(40) for x in range(24)}
    fixed.update({(x,0):value for x,value in enumerate(top)})
    # The average of the minimal and maximal 2-Lipschitz extensions preserves
    # fixed pixels and bounds every adjacent step, without nearest-route snaps.
    # Solve each atlas axis independently; existing 24x40 values stay exact.
    coordinates = [(x,y,value&255,value>>8) for (x,y),value in fixed.items()]
    extended = []
    for y in range(48):
        for x in range(40):
            if (x,y) in fixed:
                extended.append(fixed[x,y]);continue
            result = []
            for axis in (2,3):
                low = max(row[axis]-2*(abs(x-row[0])+abs(y-row[1])) for row in coordinates)
                high = min(row[axis]+2*(abs(x-row[0])+abs(y-row[1])) for row in coordinates)
                assert low<=high, ('Inconsistent fixed GPS edges',x,y,axis,low,high)
                result.append(max(0,min(255,(low+high)//2)))
            extended.append(result[0]|result[1]<<8)
    steps = []
    for y in range(48):
        for x in range(40):
            a = extended[y*40+x]
            for xx,yy in ((x+1,y),(x,y+1)):
                if xx<40 and yy<48:
                    b = extended[yy*40+xx]
                    steps.append(max(abs((a&255)-(b&255)),abs((a>>8)-(b>>8))))
    assert max(steps)<=2
    assert all(extended[y*40+x+8]==old[y][x] for y in range(40) for x in range(24))
    assert extended[:8]==top
    result = original[:array.start(2)]+','.join(map(str,packed+extended))+original[array.end(2):]
    replacement = '{'+str(len(packed))+', (MAP_GROUP('+IDENT+')<<8)|MAP_NUM('+IDENT+'), 40, 48}'
    assert result.count(desc[0])==1
    result = result.replace(desc[0],replacement)
    # Keep the older sparse fallback anchors in the same logical locations.
    anchor_match = re.search(r'(sWorldAnchors\[\].*?= \{\n)(.*?)(\n\};)',result,re.S)
    rows = anchor_match[2].splitlines()
    projection = re.search(r'\{(\d+), \(MAP_GROUP\('+IDENT+r'\)<<8\)\|MAP_NUM\('+IDENT+r'\), (\d+)\}',original)
    assert projection
    anchor_first,anchor_count = map(int,projection.groups())
    for index in range(anchor_first,anchor_first+anchor_count):
        values = list(map(int,re.fullmatch(r'\{([^}]+)\},',rows[index])[1].split(',')))
        values[0]+=8;values[2]+=8
        rows[index]='{'+','.join(map(str,values))+'},'
    result = result[:anchor_match.start(2)]+'\n'.join(rows)+result[anchor_match.end(2):]
    layer.stage(PATH,result)
    world = read(layer,'src/data/journey_world_map.h')
    return dict(map='OneIsland_TreasureBeach_Frlg',old_dimensions=[24,40],dimensions=[40,48],
                original_tile_offset=[8,0],original_grid_pixels_preserved=960,
                new_grid_first=len(packed),new_grid_pixels=len(extended),
                west_connection_pixels=top,all_other_logical_grids_unchanged=True,
                maximum_adjacent_pixel_step=max(steps),
                atlas_tiles_tilemap_palette_and_route_lines_unchanged=True,
                world_header_sha256=__import__('hashlib').sha256(world).hexdigest())
