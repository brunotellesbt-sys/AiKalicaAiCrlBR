"""Replace Lavender Port's cottage with Pallet's terminal and indoor ferry."""
import argparse
import copy
import json
import re
import struct
from pathlib import Path

from candidate_layer import Layer
from import_native_pier import import_pier
from prepare_world_route_chart import PRIOR, LAYER as PREVIOUS
from render_sea_maps import MapRenderer

LAYER = 'lavender-harbor'
PRIOR = PRIOR + [PREVIOUS]
EXTERIOR = 'JourneyRoute12Shipyard'
HARBOR = 'JourneyLavenderHarbor'
MAP = 'MAP_JOURNEY_LAVENDER_HARBOR'
DOOR = (11, 40)
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
    r = MapRenderer(s)
    ids, files = import_pier(s, exterior['secondary_tileset'],
                            donor=donor['secondary_tileset'],
                            mids=sorted({v & 1023 for v in house}))
    # Pallet's terminal stands over water; Lavender's stands on sand. Replace
    # only the transparent roof backing, keeping the native roof foreground.
    metatiles = next(p for p in files if p.endswith('/metatiles.bin'))
    words = bytearray(files[metatiles])
    sand = r.tileset(exterior['primary_tileset'])[2][0x115*8:0x115*8+4]
    for value in house[:7]:
        struct.pack_into('<4H',words,(ids[value & 1023]-640)*16,*sand)
    files[metatiles] = bytes(words)
    for path, raw in files.items():
        layer.stage(path, raw)
    # Clear the former cottage, then move the terminal two tiles left and
    # down from its first preview. Keep the surrounding island and piers.
    grass = original[37*w+9]
    for y in range(36, 39):
        for x in range(10, 15):
            blocks[y*w+x] = grass
    for y in range(6):
        for x in range(7):
            value = house[y*7+x]
            blocks[(35+y)*w+8+x] = (value & ~1023) | ids[value & 1023]
    sand_cells = []
    for y in range(34,41):
        for x in range(8,17):
            if blocks[y*w+x] == grass:
                blocks[y*w+x] = 0x3115
                sand_cells.append([x,y])
    # Keep the old exterior warp index so old saves in the lodge can exit.
    warp = city['warp_events'][0]
    assert warp['dest_map'] == 'MAP_JOURNEYROUTE12SAILORSLODGE'
    warp.update(x=DOOR[0], y=DOOR[1], dest_map=MAP, dest_warp_id='0')
    outside_captains = [o for o in city['object_events'] if o['script']=='Journey_FerryPort0']
    assert len(outside_captains) == 1
    city['object_events'] = [o for o in city['object_events'] if o not in outside_captains]
    layer.stage(exterior['blockdata_filepath'], struct.pack('<'+'H'*len(blocks), *blocks))
    layer.stage(f'data/maps/{EXTERIOR}/map.json', json.dumps(city, indent=2)+'\n')

    interior, native_layout, inside = load('JourneyPalletHarbor')
    interior, layout = copy.deepcopy(interior), copy.deepcopy(native_layout)
    layout.update(id='LAYOUT_JOURNEY_LAVENDER_HARBOR', name=HARBOR+'_Layout',
                  blockdata_filepath=f'data/layouts/{HARBOR}/map.bin',
                  border_filepath=f'data/layouts/{HARBOR}/border.bin')
    data['layouts'].append(layout)
    interior.update(id=MAP, name=HARBOR, layout=layout['id'],
                    region_map_section=city['region_map_section'])
    captain = next(o for o in interior['object_events'] if o['script']=='Journey_FerryPort18')
    captain['script'] = 'Journey_FerryPort0'
    for warp in interior['warp_events']:
        warp.update(dest_map=city['id'], dest_warp_id='0')
    layer.stage(layout['blockdata_filepath'], (s/native_layout['blockdata_filepath']).read_bytes())
    layer.stage(layout['border_filepath'], (s/native_layout['border_filepath']).read_bytes())
    layer.stage(f'data/maps/{HARBOR}/map.json', json.dumps(interior, indent=2)+'\n')
    layer.stage(f'data/maps/{HARBOR}/scripts.inc', HARBOR+'_MapScripts::\n\t.byte 0\n')
    layer.stage('data/layouts/layouts.json', json.dumps(data, indent=2)+'\n')
    groups = json.loads((s/'data/maps/map_groups.json').read_text())
    group = next(k for k in groups['group_order'] if 'JourneyPalletHarbor' in groups[k])
    groups[group].append(HARBOR)
    layer.stage('data/maps/map_groups.json', json.dumps(groups, indent=2)+'\n')
    layer.stage('data/event_scripts.s', (s/'data/event_scripts.s').read_text()
                +f'\n\t.include "data/maps/{HARBOR}/scripts.inc"\n')
    path = 'data/scripts/journey_campaign_gates.inc'
    text = (s/path).read_text()
    a = text.index('LavenderNetwork_Destination0::\n')
    b = text.index('\n\n', a)
    destination = text[a:b].replace(city['id']+')', MAP+')')
    for var, value in [('0x8009', ARRIVAL[0]), ('0x800A', ARRIVAL[1])]:
        destination, count = re.subn(r'(setvar VAR_'+var+r', )\d+', lambda m:m[1]+str(value), destination)
        assert count == 1
    layer.stage(path, text[:a]+destination+text[b:])
    ship = next(o for o in interior['object_events'] if o['graphics_id']=='OBJ_EVENT_GFX_SS_TIDAL')
    hull = json.loads((s/'.journey-pallet-harbor').read_text())['hull']
    changed = [[i%w, i//w] for i,(a,b) in enumerate(zip(original,blocks)) if a!=b]
    return layer.finish(exterior=EXTERIOR, interior=HARBOR, terminal=[8,35,7,6],
                        terminal_shift_from_first_preview=[-2,2],
                        roof_background='native_sand',remaining_grass_replaced_with_sand=sand_cells,
                        door=list(DOOR), world_port_id=0, captain=list(CAPTAIN), arrival=list(ARRIVAL),
                        ship=[ship['x'],ship['y']], ship_sprite_size=list(r.sprite(ship['graphics_id'],0).size),
                        hull=hull, changed_terrain=changed, copied_from='JourneyPalletHarbor',
                        outside_captain_removed=True, existing_piers_and_boats_preserved=True,
                        surface_connections_preserved=True, old_lodge_exit_preserved=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().source), indent=2))
