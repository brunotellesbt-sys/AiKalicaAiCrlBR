"""Move Fuchsia's ferry office onto the western bay with a Slateport terminal."""
import argparse
import copy
import json
import re
import struct
from pathlib import Path

from candidate_layer import Layer
from import_native_pier import import_pier
from prepare_lavender_harbor import PRIOR, LAYER as PREVIOUS
from render_sea_maps import MapRenderer

LAYER = 'fuchsia-harbor'
PRIOR = PRIOR + [PREVIOUS]
EXTERIOR = 'Route19_Frlg'
HARBOR = 'JourneyFuchsiaHarbor'
MAP = 'MAP_JOURNEY_FUCHSIA_HARBOR'
TERMINAL = (1, 10, 7, 6)
DOOR = (4, 15)
ARRIVAL = (16, 13)
CAPTAIN = (16, 12)


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

    city, exterior, blocks = load(EXTERIOR)
    original = blocks.copy()
    w = exterior['width']
    _, donor, pallet = load('PalletTown_Frlg')
    house = [pallet[(18+y)*donor['width']+15+x] for y in range(6) for x in range(7)]
    ids, files = import_pier(s, exterior['secondary_tileset'],
                            donor=donor['secondary_tileset'],
                            mids=sorted({v & 1023 for v in house}))
    for path, raw in files.items():
        layer.stage(path, raw)
    # Recover the native beach and its upper cliff rim behind the old cottage.
    for y in range(9, 12):
        for x in range(9, 14):
            blocks[y*w+x] = 0x3115
    # The two clipped boulder tops replaced a straight bank. Complete the
    # existing cliff instead of carving its mountain away for the new roof.
    removed_rock = [[x,9,blocks[9*w+x]] for x in (5,6)]
    assert [v & 1023 for _,_,v in removed_rock] == [0x108,0x109]
    for x in (5,6):
        blocks[9*w+x] = 0x1123
    tx, ty, tw, th = TERMINAL
    for y in range(th):
        for x in range(tw):
            value = house[y*tw+x]
            blocks[(ty+y)*w+tx+x] = (value & ~1023) | ids[value & 1023]
    # Keep the original L-shaped pier. Only its two westernmost cells under
    # the new terminal wall are replaced. A wooden apron connects the door.
    quay = []
    for x in range(1,9):
        blocks[16*w+x] = 0x3340 if x == 1 else 0x3342 if x == 8 else 0x3341
        quay.append([x,16])
    for x in (7,8):
        blocks[18*w+x] = original[17*w+x]
        quay.append([x,18])
    captain = next(o for o in city['object_events'] if o['script']=='Journey_FerryPort20')
    city['object_events'].remove(captain)
    boat = next(o for o in city['object_events'] if o['graphics_id']=='OBJ_EVENT_GFX_MR_BRINEYS_BOAT')
    boat.update(graphics_id='OBJ_EVENT_GFX_SEAGALLOP', x=4, y=19,
                movement_type='MOVEMENT_TYPE_FACE_LEFT')
    # Remove only the old boat's invisible hull, then block every opaque pixel
    # of the medium boat over water, including the stern and bow.
    for y in (16,17):
        for x in (4,5,6):
            if blocks[y*w+x] & 1023 == 0x12B:
                blocks[y*w+x] &= ~0x400
    r = MapRenderer(s)
    sprite = r.sprite(boat['graphics_id'], 0)
    ox, oy = boat['x']*16+8-sprite.width//2, boat['y']*16+16-sprite.height
    outside_hull = sorted({((ox+x)//16,(oy+y)//16)
        for y in range(sprite.height) for x in range(sprite.width)
        if sprite.getpixel((x,y))[3]})
    for x,y in outside_hull:
        if blocks[y*w+x] & 1023 in (0x1D2,0x1D9,0x1E2):
            blocks[y*w+x] = 0x112B  # Native ocean-pattern filler beneath the hull.
        assert blocks[y*w+x] >> 12 == 1, ('Boat overlaps quay/land',x,y)
        blocks[y*w+x] |= 0x400
    # No existing trainer may be covered by either the building or the ship.
    occupied = {(x,y) for y in range(ty,ty+th) for x in range(tx,tx+tw)} | set(outside_hull)
    assert all((o['x'],o['y']) not in occupied for o in city['object_events'] if o is not boat)
    old_warp = city['warp_events'][0]
    assert old_warp['dest_map']=='MAP_JOURNEYROUTE19PORTLODGE'
    old_warp.update(x=DOOR[0],y=DOOR[1],dest_map=MAP,dest_warp_id='0')
    layer.stage(exterior['blockdata_filepath'], struct.pack('<'+'H'*len(blocks),*blocks))
    layer.stage(f'data/maps/{EXTERIOR}/map.json',json.dumps(city,indent=2)+'\n')
    # Reuse the permanent S.S. Tidal and the indoor transport menu from Pallet.
    interior, native_layout, inside = load('JourneyPalletHarbor')
    interior, layout = copy.deepcopy(interior), copy.deepcopy(native_layout)
    layout.update(id='LAYOUT_JOURNEY_FUCHSIA_HARBOR',name=HARBOR+'_Layout',
                  blockdata_filepath=f'data/layouts/{HARBOR}/map.bin',
                  border_filepath=f'data/layouts/{HARBOR}/border.bin')
    data['layouts'].append(layout)
    interior.update(id=MAP,name=HARBOR,layout=layout['id'],region_map_section=city['region_map_section'])
    inside_captain = next(o for o in interior['object_events'] if o['script']=='Journey_FerryPort18')
    inside_captain['script']='Journey_FerryPort20'
    for warp in interior['warp_events']:
        warp.update(dest_map=city['id'],dest_warp_id='0')
    layer.stage(layout['blockdata_filepath'],(s/native_layout['blockdata_filepath']).read_bytes())
    layer.stage(layout['border_filepath'],(s/native_layout['border_filepath']).read_bytes())
    layer.stage(f'data/maps/{HARBOR}/map.json',json.dumps(interior,indent=2)+'\n')
    layer.stage(f'data/maps/{HARBOR}/scripts.inc',HARBOR+'_MapScripts::\n\t.byte 0\n')
    # Saves inside the retired cottage leave through the relocated exterior
    # warp index zero; its old NPC no longer duplicates the working captain.
    lodge, _, _ = load('JourneyRoute19PortLodge')
    assert lodge['warp_events'][0]['dest_warp_id']=='0'
    lodge['object_events']=[]
    layer.stage('data/maps/JourneyRoute19PortLodge/map.json',json.dumps(lodge,indent=2)+'\n')
    layer.stage('data/layouts/layouts.json',json.dumps(data,indent=2)+'\n')
    groups=json.loads((s/'data/maps/map_groups.json').read_text())
    group=next(k for k in groups['group_order'] if 'JourneyLavenderHarbor' in groups[k])
    groups[group].append(HARBOR)
    layer.stage('data/maps/map_groups.json',json.dumps(groups,indent=2)+'\n')
    layer.stage('data/event_scripts.s',(s/'data/event_scripts.s').read_text()+f'\n\t.include "data/maps/{HARBOR}/scripts.inc"\n')
    path='data/scripts/journey_campaign_gates.inc'
    text=(s/path).read_text()
    a=text.index('LavenderNetwork_Destination20::\n');b=text.index('\n\n',a)
    destination=text[a:b].replace('MAP_ROUTE19)',MAP+')')
    for var,value in [('0x8009',ARRIVAL[0]),('0x800A',ARRIVAL[1])]:
        destination,count=re.subn(r'(setvar VAR_'+var+r', )\d+',lambda m:m[1]+str(value),destination)
        assert count==1
    layer.stage(path,text[:a]+destination+text[b:])
    changed=[[i%w,i//w] for i,(a,b) in enumerate(zip(original,blocks)) if a!=b]
    return layer.finish(exterior=EXTERIOR,interior=HARBOR,terminal=list(TERMINAL),door=list(DOOR),
        quay=quay,world_port_id=20,captain=list(CAPTAIN),arrival=list(ARRIVAL),
        outside_boat=boat,outside_boat_sprite_size=list(sprite.size),outside_hull=[list(c) for c in outside_hull],
        inside_ship_sprite_size=[96,40],hull=json.loads((s/'.journey-pallet-harbor').read_text())['hull'],
        removed_clipped_rock=removed_rock,changed_terrain=changed,
        one_indoor_captain=True,outside_captain_removed=True,existing_trainers_preserved=True,
        shore_and_mountains_preserved=True,old_lodge_exit_preserved=True,
        copied_from='PalletTown_Frlg / JourneyPalletHarbor',surface_connections_preserved=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    print(json.dumps(prepare(p.parse_args().source),indent=2))
