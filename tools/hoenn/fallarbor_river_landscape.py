"""Repair the river scenery with intact native banks and walkable beach land.

Called by the current PR overlay. No native events, connections or buildings
move. The Route 114 reference is pinned to the acquired source in its caller.
"""
import hashlib
import json
import struct
from pathlib import Path

WATER = 0x1170
ROCK = 0x15F9  # Existing complete one-metatile boulder, with animated water.


def repair(layer):
    s = layer.source
    layouts = {l['id']: l for l in json.loads((s/'data/layouts/layouts.json').read_text())['layouts']}
    def load(name):
        m = json.loads((s/f'data/maps/{name}/map.json').read_text())
        l = layouts[m['layout']]
        return m, l, list(struct.unpack('<'+'H'*(l['width']*l['height']), (s/l['blockdata_filepath']).read_bytes()))
    river, rl, old_river = load('JourneyWestRiver')
    route, tl, old_route = load('Route114')
    reference = (Path(__file__).parent/'templates/route114-native.bin').read_bytes()
    acquired = json.loads((s/'.source-acquired.json').read_text())
    assert hashlib.sha256(reference).hexdigest() == acquired['sha256'][tl['blockdata_filepath']]
    native = list(struct.unpack('<3200H', reference))
    assert (rl['width'],rl['height'],tl['width'],tl['height']) == (48,14,40,80)
    # The old rectangular excavation removed cliff feet and whole tree rows.
    # Restore their native geometry, then clear the actual existing lake mouth.
    bank = old_route[:]
    for y in range(10,24):
        for x in range(12):
            bank[y*40+x] = native[y*40+x]
    removed = []
    for y in range(16,19):
        for x in range(10):
            if bank[y*40+x]&1023 in [0x150,0x151,0x158,0x159,0x15A,0x15B]:
                removed.append([x,y,bank[y*40+x]])
                bank[y*40+x] = 0x1189 if y == 16 else WATER
    # Complete overhanging trees are scenery, never a route under their leaves.
    overhangs = []
    for x in range(3,7):
        assert bank[18*40+x]&1023 in [0x2CC,0x2CD]
        bank[18*40+x] |= 0x400
        overhangs.append([x,18])
    # A one-cell pond in the landing bank forced another Surf animation in the
    # middle of the dirt path. Make that entire small pocket continuous land.
    for y in range(13,16):
        for x in range(17,20):
            bank[y*40+x] = 0x3279
    layer.stage(tl['blockdata_filepath'],struct.pack('<3200H',*bank))
    # A simple complete native beach, without concave partial corners or
    # dry sand assigned water elevation. Keep both existing trainer positions.
    values = [WATER]*(48*14)
    beach = [0x11B,0x11C,0x11D,0x123,0x124,0x125,0x12B,0x12C,0x12D]
    island = []
    widths = [(11,14),(10,15),(9,16),(9,16),(9,16),(10,15),(11,14)]
    land = {(x,y+3) for y,(a,b) in enumerate(widths) for x in range(a,b+1)}
    from render_sea_maps import MapRenderer
    renderer = MapRenderer(s)
    primary = renderer.tileset(rl['primary_tileset'])[2]
    known = {tuple(primary[mid*8:(mid+1)*8]):mid for mid in beach}
    patterns = json.loads((s/'.journey-complete-beach-edges').read_text())['patterns']['emerald']
    known.update({tuple(p['words']):p['id'] for p in patterns})
    for x,y in sorted(land):
        words = list(primary[0x124*8:0x125*8])
        for q,(dx,dy) in enumerate([(-1,-1),(1,-1),(-1,1),(1,1)]):
            horizontal = (x+dx,y) not in land
            vertical = (x,y+dy) not in land
            if not horizontal and not vertical and (x+dx,y+dy) not in land:
                mid = beach[[8,6,2,0][q]]
                for lev in [0,1]:words[lev*4+q] = primary[mid*8+lev*4+3-q]^0xC00
            else:
                row = (0 if dy<0 else 2) if vertical else 1
                col = (0 if dx<0 else 2) if horizontal else 1
                mid = beach[row*3+col]
                for lev in [0,1]:words[lev*4+q] = primary[mid*8+lev*4+q]
        assert tuple(words) in known, ('Unrecognized beach quadrant',x,y)
        values[y*48+x] = 0x3000|known[tuple(words)]
        island.append([x,y])
    for event in river['object_events']:
        assert [event['x'],event['y']] in island and event['elevation']==3
    # Borders use whole boulders at every phase, including odd mouth heights.
    # Preserve the northern and southern regional connections, with a clear
    # three-row mouth into the native lake (river y6..8 -> Route 114 y16..18).
    for y in range(14):
        for x in range(48):
            closed = (x<2 or y<2 and x>=24 or y>=12 and x>=34
                      or x>=46 and y not in range(6,9))
            if closed:
                values[y*48+x] = ROCK
    layer.stage(rl['blockdata_filepath'],struct.pack('<672H',*values))
    layer.stage(rl['border_filepath'],struct.pack('<4H',*[ROCK]*4))
    assert all(bank[i]==old_route[i] for i in range(24*40,len(bank)))
    return dict(maps=['JourneyWestRiver','Route114'],island=island,
        beach_elevation=3,river_water_rows=[6,7,8],route_water_rows=[16,17,18],
        full_boulder_metatile=ROCK,restored_native_cliff_rectangle=[0,10,12,6],
        whole_native_trees_restored=True,blocked_tree_overhangs=overhangs,
        removed_complete_reefs=removed,filled_landing_pond=[17,13,3,3],
        all_events_connections_and_city_buildings_preserved=True,
        source_paths=[rl['blockdata_filepath'],rl['border_filepath'],tl['blockdata_filepath']])
