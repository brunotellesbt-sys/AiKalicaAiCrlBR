"""Extend Pallet's eastern bay and replace its cottage with a Slateport terminal."""
import argparse
import copy
import json
import re
import struct
from pathlib import Path

from candidate_layer import Layer
from import_native_pier import import_pier
from prepare_sootopolis_harbor import PRIOR, LAYER as PREVIOUS
from render_sea_maps import MapRenderer
from world_navigation_grid import build

LAYER = 'pallet-harbor'
PRIOR = PRIOR + [PREVIOUS]
HARBOR = 'JourneyPalletHarbor'
MAP = 'MAP_JOURNEY_PALLET_HARBOR'
DOOR = (18, 23)
CAPTAIN = (16, 12)
ARRIVAL = (16, 13)


def prepare(source):
    layer = Layer(source, LAYER, PRIOR)
    if old := layer.existing():
        return old
    s = layer.source
    data = json.loads((s/'data/layouts/layouts.json').read_text())
    layouts = {l['id']: l for l in data['layouts']}

    def load(name):
        m = json.loads((s/f'data/maps/{name}/map.json').read_text())
        l = layouts[m['layout']]
        raw = (s/l['blockdata_filepath']).read_bytes()
        return m, l, list(struct.unpack('<'+'H'*(len(raw)//2), raw))

    city, exterior, blocks = load('PalletTown_Frlg')
    old_w, old_h = exterior['width'], exterior['height']
    assert (old_w, old_h) == (24, 21)
    w = 26
    before = [tile for y in range(old_h)
              for tile in blocks[y*old_w:(y+1)*old_w]+[0x3001, 0x3001]]
    blocks = before.copy()
    boat = copy.deepcopy(next(o for o in city['object_events']
                              if o['graphics_id'] == 'OBJ_EVENT_GFX_MR_BRINEYS_BOAT'))
    bridge = [[x, y, before[y*w+x]] for y in (17, 18) for x in range(9, 13)]
    extension = [v & ~0x400 if v >> 12 == 1 else v for v in before[-w:]]
    blocks.extend(extension * 9)
    exterior.update(width=w, height=30)
    # Keep Oak's laboratory, the northern route and the southern Surf channel.
    # The final southern row keeps the old Route 21 terrain; copied boat
    # collision is cleared from the additional rows beneath the actual hull.
    for y in range(16, 25):
        for x in range(13, 23):
            blocks[y*w+x] = 0x3001 if x < 15 or y == 16 else 0x112B
    for x in range(15, 23):
        blocks[17*w+x] = 0x3001
    for y in (17, 18):
        for x in (13, 14):
            blocks[y*w+x] = before[18*w+11]
    for y in range(18, 25):
        blocks[y*w+22] = 0x112C
    for x in range(11, 23):
        blocks[25*w+x] = 0x112B
    for y in range(21, 26):
        blocks[y*w+10] = 0x112B
    for y in (19, 20):
        for x in (8, 9, 10):
            blocks[y*w+x] = 0x112B
    # Merge the old boat channel with the new bay. The narrow wooden access
    # replaces the grassy peninsula, leaving water visible on both sides.
    for y in range(19, 25):
        for x in range(11, 15):
            blocks[y*w+x] = before[18*w+11] if x >= 13 else 0x112B
    blocks[18*w+22] = 0x1124
    blocks[16*w+20] = before[16*w+20]  # Oak's relocated sign.

    _, donor, native_house = load('SlateportCity')
    house = [native_house[(7+y)*donor['width']+25+x]
             for y in range(6) for x in range(7)]
    r = MapRenderer(s)
    # Remove grass behind the donor's roof; the actual Kanto water remains
    # visible through it rather than inheriting an Emerald green backdrop.
    ids, files = import_pier(s, exterior['secondary_tileset'],
                            donor=donor['secondary_tileset'], donor_emerald=True,
                            mids=sorted({v & 1023 for v in house}),
                            transparent_colors={2: {1, 2, 3, 4}})
    for path, raw in files.items():
        layer.stage(path, raw)
    path = 'data/tilesets/secondary/pallet_town_frlg/metatiles.bin'
    assert path in layer.outputs
    words = bytearray(layer.outputs[path])
    water = r.tileset('gTileset_General_Frlg')[2][0x12B*8:0x12B*8+4]
    for original in house[:7]:
        struct.pack_into('<4H', words, (ids[original & 1023]-640)*16, *water)
    # A south-facing native cliff rim closes the bay before the unchanged
    # Route 21 seam. Flip the north rim, retaining its native water behavior.
    attrs_path = path.replace('metatiles.bin', 'metatile_attributes.bin')
    attrs = bytearray(layer.outputs[attrs_path])
    rim_ids = []
    primary = r.tileset('gTileset_General_Frlg')[2]
    for mid in (0x123, 0x124):
        rim_ids.append(640+len(words)//16)
        incoming = primary[mid*8:(mid+1)*8]
        flipped = [incoming[b+q] ^ 0x800 for b in (0, 4) for q in (2, 3, 0, 1)]
        words.extend(struct.pack('<8H', *flipped))
        attrs.extend((0x10).to_bytes(4, 'little'))  # MB_POND_WATER
    layer.stage(path, words)
    layer.stage(attrs_path, attrs)
    for x in range(11, 23):
        blocks[25*w+x] = 0x1000 | rim_ids[x == 22]
    # Put the native upper cliff at the bottom of the grass cell, keeping
    # the reduced gap above the roof rather than adding a full water row.
    grass = primary[8:16]
    upper_rim = []
    for mid in (0x123, 0x124):
        incoming = primary[mid*8:(mid+1)*8]
        upper_rim.append(640+len(words)//16)
        mixed = [grass[0], grass[1], incoming[0], incoming[1],
                 grass[4], grass[5], incoming[4], incoming[5]]
        words.extend(struct.pack('<8H', *mixed))
        attrs.extend((0).to_bytes(4, 'little'))
    for x in range(15, 23):
        blocks[17*w+x] = 0x3000 | upper_rim[x == 22]
    layer.stage(path, words)
    layer.stage(attrs_path, attrs)
    for y in range(6):
        for x in range(7):
            value = house[y*7+x]
            blocks[(18+y)*w+15+x] = (value & ~1023) | ids[value & 1023]
    # A quay reaches the new lower entrance without moving a single tile
    # of the original horizontal bridge or the small boat beneath it.
    for x in range(13, 22):
        blocks[24*w+x] = before[18*w+10] if x == 13 else before[18*w+12] if x == 21 else before[18*w+11]
    for x, y, value in bridge:
        assert blocks[y*w+x] == value
    current_boat = next(o for o in city['object_events'] if o['graphics_id'] == boat['graphics_id'])
    current_boat['x'] += 1
    boat_sprite = r.sprite(current_boat['graphics_id'], 2)
    ox, oy = current_boat['x']*16+8-boat_sprite.width//2, current_boat['y']*16+16-boat_sprite.height
    outside_hull = sorted({((ox+x)//16, (oy+y)//16)
        for y in range(boat_sprite.height) for x in range(boat_sprite.width)
        if boat_sprite.getpixel((x, y))[3]})
    for x, y in outside_hull:
        assert blocks[y*w+x] >> 12 == 1
        blocks[y*w+x] |= 0x400
    city['object_events'] = [o for o in city['object_events'] if o['script'] != 'Journey_FerryPort18']
    # Leave room for whole trees beside the bay, and complete the two
    # pre-existing clipped saplings west of the boat channel.
    trees = []
    def tree(x, y):
        cells = [0x00E, 0x00F, 0x01C, 0x01F, 0x024, 0x027]
        for dy in range(3):
            for dx in range(2):
                blocks[(y+dy)*w+x+dx] = 0x3400 | cells[dy*2+dx]
        if [x, y] not in trees:
            trees.append([x, y])
    for y in range(18, 30):
        for x in range(6):
            blocks[y*w+x] = 0x3001
    for x in (0, 2, 4):
        for y in (18, 21, 24, 27):
            tree(x, y)
    for y in (12, 15):
        tree(0, y)
    for y in range(0, 30, 3):
        tree(24, y)
    for y in range(2, 17):
        blocks[y*w+22] = 0x3001
    for y in range(2, 30):
        blocks[y*w+23] = 0x3001
    for x in range(12, 26, 2):
        tree(x, 27)
    assert [v & ~0x400 for v in blocks[-w+7:-w+11]] == [v & ~0x400 for v in extension[7:11]]
    # Move the wandering resident away from the terminal's access corridor.
    resident = next(o for o in city['object_events'] if o.get('local_id') == 'LOCALID_PALLET_FAT_MAN')
    resident.update(x=19, y=10, movement_range_x=1, movement_range_y=1)
    old_warp = next(warp for warp in city['warp_events']
                    if warp['dest_map'] == 'MAP_JOURNEYPALLETTOWNPORTLODGE')
    door_index = city['warp_events'].index(old_warp)
    old_warp.update(x=DOOR[0], y=DOOR[1], dest_map=MAP, dest_warp_id='0')
    layer.stage(exterior['blockdata_filepath'], struct.pack('<'+'H'*len(blocks), *blocks))
    layer.stage('data/maps/PalletTown_Frlg/map.json', json.dumps(city, indent=2)+'\n')
    # Saves inside the former cottage still exit through the new front door.
    old_lodge, _, _ = load('JourneyPalletTownPortLodge')
    assert old_lodge['warp_events'][0]['dest_warp_id'] == str(door_index)

    interior, native_layout, inside = load('SlateportCity_Harbor')
    interior, layout = copy.deepcopy(interior), copy.deepcopy(native_layout)
    layout.update(id='LAYOUT_JOURNEY_PALLET_HARBOR', name=HARBOR+'_Layout',
                  blockdata_filepath=f'data/layouts/{HARBOR}/map.bin',
                  border_filepath=f'data/layouts/{HARBOR}/border.bin')
    data['layouts'].append(layout)
    interior.update(id=MAP, name=HARBOR, layout=layout['id'],
                    region='REGION_KANTO', region_map_section=city['region_map_section'],
                    music=city['music'], connections=None, coord_events=[], bg_events=[])
    ship = copy.deepcopy(next(o for o in interior['object_events']
                              if o['graphics_id'] == 'OBJ_EVENT_GFX_SS_TIDAL'))
    ship.pop('local_id', None)
    captain = copy.deepcopy(next(o for o in interior['object_events']
                                 if o['script'] == 'Journey_FerryPort1'))
    captain.update(x=CAPTAIN[0], y=CAPTAIN[1], script='Journey_FerryPort18')
    interior['object_events'] = [ship, captain]
    interior['warp_events'] = [dict(x=x, y=14, elevation=0, dest_map=city['id'],
                                   dest_warp_id=str(door_index)) for x in (11, 12)]
    # Use the ship's opaque native sprite footprint for solid hull collision.
    sprite = r.sprite(ship['graphics_id'], 0)
    ox = ship['x']*16+8-sprite.width//2
    oy = ship['y']*16+16-sprite.height
    hull = [list(cell) for cell in sorted({((ox+x)//16, (oy+y)//16)
            for y in range(sprite.height) for x in range(sprite.width)
            if sprite.getpixel((x, y))[3]})]
    for x, y in hull:
        assert inside[y*layout['width']+x] >> 12 == 1
        inside[y*layout['width']+x] |= 0x400
    layer.stage(layout['blockdata_filepath'], struct.pack('<'+'H'*len(inside), *inside))
    layer.stage(layout['border_filepath'], (s/native_layout['border_filepath']).read_bytes())
    layer.stage(f'data/maps/{HARBOR}/map.json', json.dumps(interior, indent=2)+'\n')
    layer.stage(f'data/maps/{HARBOR}/scripts.inc', HARBOR+'_MapScripts::\n\t.byte 0\n')
    layer.stage('data/layouts/layouts.json', json.dumps(data, indent=2)+'\n')
    groups = json.loads((s/'data/maps/map_groups.json').read_text())
    group = next(k for k in groups['group_order'] if 'JourneySootopolisHarbor' in groups[k])
    groups[group].append(HARBOR)
    layer.stage('data/maps/map_groups.json', json.dumps(groups, indent=2)+'\n')
    layer.stage('data/event_scripts.s', (s/'data/event_scripts.s').read_text()
                +f'\n\t.include "data/maps/{HARBOR}/scripts.inc"\n')
    path = 'data/scripts/journey_campaign_gates.inc'
    text = (s/path).read_text()
    a = text.index('LavenderNetwork_Destination18::\n')
    b = text.index('\n\n', a)
    destination = text[a:b].replace('MAP_PALLET_TOWN)', MAP+')')
    for var, value in [('0x8009', ARRIVAL[0]), ('0x800A', ARRIVAL[1])]:
        destination, count = re.subn(r'(setvar VAR_'+var+r', )\d+', lambda m:m[1]+str(value), destination)
        assert count == 1
    layer.stage(path, text[:a]+destination+text[b:])
    # Extend the existing continuous atlas grid, retaining its zero-distance
    # route seams and the native cave positions introduced by later layers.
    geometry = json.loads((s/'.journey-navigated-sea-atlas').read_text())
    projection = next(p for p in geometry['projections'] if p['map'] == 'PalletTown_Frlg')
    for anchor in geometry['anchors'][projection['first']:projection['first']+projection['count']+1]:
        for axis in (1, 3):
            if anchor[axis] == old_h-1:
                anchor[axis] = exterior['height']-1
    geometry['anchors'][projection['first']][1] = exterior['height']//2
    geometry['anchors'][projection['first']][3] = exterior['height']//2
    projection.update(width=w, height=exterior['height'])
    geometry['anchors'][projection['first']][0] = w//2
    geometry['anchors'][projection['first']][2] = w//2
    for seam in geometry['seams']:
        if seam['map'] == 'PalletTown_Frlg' and seam['direction'] == 'down':
            seam['box'][1] = seam['box'][3] = exterior['height']-1
    grids, pixels, grid_proof = build(geometry)
    anchors, projections = geometry['anchors'], geometry['projections']
    position = 'struct JourneyWorldAnchor { s16 left, top, right, bottom; u8 x, y; };\nstruct JourneyWorldProjection { u32 first; u16 map, count; };\nstatic const struct JourneyWorldAnchor sWorldAnchors[] __attribute__((used)) = {\n'
    position += ''.join('{'+','.join(map(str,a))+'},\n' for a in anchors)+'};\nstatic const struct JourneyWorldProjection sWorldProjections[] = {\n'
    position += ''.join('{'+str(p['first'])+', (MAP_GROUP('+p['id']+')<<8)|MAP_NUM('+p['id']+'), '+str(p['count'])+'},\n' for p in projections)+'};\n'
    position += '\nstruct JourneyWorldTileGrid { u32 first; u16 map, width, height; };\nstatic const u16 sWorldNavigationPixels[] = {'+','.join(str(int(x)|(int(y)<<8)) for x,y in pixels)+'};\nstatic const struct JourneyWorldTileGrid sWorldTileGrids[] = {\n'
    position += ''.join('{'+str(int(grids[p['map']][0,0]))+', (MAP_GROUP('+p['id']+')<<8)|MAP_NUM('+p['id']+'), '+str(p['width'])+', '+str(p['height'])+'},\n' for p in projections)+'};\n'
    layer.stage('src/data/journey_world_position.h', position)
    return layer.finish(exterior='PalletTown_Frlg', interior=HARBOR, door=list(DOOR),
                        terminal=[15, 18, 7, 6], exterior_size=[w, exterior['height']],
                        previous_size=[old_w, old_h], preserved_bridge=bridge,
                        original_boat=boat, outside_boat=current_boat, boat_shift=[1, 0],
                        outside_captain_removed=True, bridge_unchanged=True,
                        bridge_join=[[x,y] for y in (17,18) for x in (13,14)],
                        complete_trees=trees, upper_cliff_rim=True,
                        world_port_id=18, captain=list(CAPTAIN), arrival=list(ARRIVAL),
                        ship=[ship['x'], ship['y']], ship_graphics=ship['graphics_id'],
                        ship_sprite_size=list(sprite.size), hull=hull,
                        route_seams_preserved=True, **grid_proof,
                        **{key:geometry[key] for key in ('anchors','projections','seams')})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().source), indent=2))
