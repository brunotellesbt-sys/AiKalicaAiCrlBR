"""Build a walkable lakeside terminal and move Sootopolis's world port indoors."""
import argparse
import copy
import io
import json
import re
import struct
from pathlib import Path

from PIL import Image

from candidate_layer import Layer
from import_native_pier import import_pier
from prepare_navigated_sea_atlas import PRIOR, LAYER as PREVIOUS
from render_sea_maps import MapRenderer

LAYER = 'sootopolis-harbor'
PRIOR = PRIOR + [PREVIOUS]
HARBOR = 'JourneySootopolisHarbor'
MAP = 'MAP_JOURNEY_SOOTOPOLIS_HARBOR'
DOOR = (23, 44)
CAPTAIN = (8, 11)
ARRIVAL = (8, 12)


def prepare(source):
    layer = Layer(source, LAYER, PRIOR)
    if old := layer.existing():
        return old
    s = layer.source
    data = json.loads((s / 'data/layouts/layouts.json').read_text())
    layouts = {l['id']: l for l in data['layouts']}

    def load(name):
        m = json.loads((s / f'data/maps/{name}/map.json').read_text())
        l = layouts[m['layout']]
        raw = (s / l['blockdata_filepath']).read_bytes()
        return m, l, list(struct.unpack('<' + 'H' * (len(raw) // 2), raw))

    city, exterior, blocks = load('SootopolisCity')
    baseline = blocks.copy()
    _, donor, donor_blocks = load('SlateportCity')
    width = exterior['width']
    # A complete native Slateport terminal, including its original door behavior.
    house = [donor_blocks[(7+y)*donor['width']+25+x]
             for y in range(6) for x in range(7)]
    renderer = MapRenderer(s)
    _, palettes, _ = renderer.tileset(donor['secondary_tileset'])
    _, primary_palettes, _ = renderer.tileset('gTileset_General')
    # Recolor only the imported terminal; Slateport and other Sootopolis tiles
    # keep their original palettes. Warm roof shades become maritime blue.
    blue = {}
    for bank in range(13):
        blue[bank] = [(115, 189, 246) if g > r + 8 and g > b + 8 else
                      (b, g, r) if r > g + 25 and r > b + 35 else (r, g, b)
                      for r, g, b in (primary_palettes if bank < 6 else palettes)[bank]]
    for index in (1, 2, 3, 4):
        blue[2][index] = (115, 189, 246)  # Water replaces the donor's grass corners.
    ids, files = import_pier(s, exterior['secondary_tileset'], emerald=True,
                            donor=donor['secondary_tileset'], donor_emerald=True,
                            mids=sorted({v & 1023 for v in house}), donor_palettes=blue)
    for path, raw in files.items():
        layer.stage(path, raw)
    # Match the lake behind the wooden platform's supporting fringe as well.
    _, dock_palettes, _ = renderer.tileset('gTileset_Pacifidlog')
    dock_colors = {bank: [(115, 189, 246) if b > r+20 and b > g+10 else (r, g, b)
                          for r, g, b in (primary_palettes if bank < 6 else dock_palettes)[bank]]
                   for bank in range(13)}
    pier, files = import_pier(s, exterior['secondary_tileset'], emerald=True,
                             donor='gTileset_Pacifidlog', donor_emerald=True,
                             mids=[0x220, 0x221, 0x224, 0x228, 0x229, 0x22C],
                             overrides=layer.outputs, donor_palettes=dock_colors)
    for path, raw in files.items():
        layer.stage(path, raw)

    # Remove the old ferry objects only; native story NPCs and their local IDs
    # remain intact. Restore the blocked water under the old submarine.
    old_boats = [o for o in city['object_events']
                 if o['graphics_id'] == 'OBJ_EVENT_GFX_JOURNEY_SUBMARINE']
    for boat in old_boats:
        for y in (boat['y']-1, boat['y']):
            for x in range(boat['x']-1, boat['x']+2):
                blocks[y*width+x] &= ~0x400
    city['object_events'] = [o for o in city['object_events']
                            if o['graphics_id'] != 'OBJ_EVENT_GFX_JOURNEY_SUBMARINE'
                            and o['script'] != 'Journey_FerryPort17']
    assert old_boats
    # Keep the central legendary scene and the gym island untouched. The
    # terminal occupies water west of Groudon; the bridge meets existing grass.
    for y in range(6):
        for x in range(7):
            at = (39+y)*width+20+x
            assert baseline[at] >> 12 == 1, (20+x, 39+y)
            original = house[y*7+x]
            blocks[at] = (original & ~1023) | ids[original & 1023]
    bridge = []
    for y in (45, 46):
        for x in range(16, 27):
            # All deck cells are on elevation 3, with zero collision, including
            # the shore cell. This prevents the one-tile water gap in the concept.
            mid = 0x220 if x == 16 else 0x224 if x == 26 else 0x221
            blocks[y*width+x] = 0x3000 | pier[mid]
            bridge.append([x, y])
    for x in range(19, 27):
        blocks[47*width+x] = 0x1400 | pier[0x22C if x == 26 else 0x229]
    assert baseline[45*width+16] >> 12 == 3
    door_index = len(city['warp_events'])
    city['warp_events'].append(dict(x=DOOR[0], y=DOOR[1], elevation=3,
                                   dest_map=MAP, dest_warp_id='0'))
    layer.stage(exterior['blockdata_filepath'], struct.pack('<'+'H'*len(blocks), *blocks))
    # The native crisis switches layouts on entry. Apply only the same small
    # harbor footprint there, preserving the legendary battle's own terrain.
    crisis = layouts['LAYOUT_SOOTOPOLIS_CITY_LEGENDS_BATTLE']
    raw = (s/crisis['blockdata_filepath']).read_bytes()
    crisis_blocks = list(struct.unpack('<'+'H'*(len(raw)//2), raw))
    assert crisis['width'] == width and len(crisis_blocks) == len(blocks)
    for i, (before, after) in enumerate(zip(baseline, blocks)):
        if before != after:
            crisis_blocks[i] = after
    layer.stage(crisis['blockdata_filepath'], struct.pack('<'+'H'*len(crisis_blocks), *crisis_blocks))
    layer.stage('data/maps/SootopolisCity/map.json', json.dumps(city, indent=2)+'\n')

    interior, native_layout, inside = load('SlateportCity_Harbor')
    interior = copy.deepcopy(interior)
    layout = copy.deepcopy(native_layout)
    layout.update(id='LAYOUT_JOURNEY_SOOTOPOLIS_HARBOR', name=HARBOR+'_Layout',
                  blockdata_filepath=f'data/layouts/{HARBOR}/map.bin',
                  border_filepath=f'data/layouts/{HARBOR}/border.bin')
    data['layouts'].append(layout)
    interior.update(id=MAP, name=HARBOR, layout=layout['id'],
                    region_map_section=city['region_map_section'],
                    music=city['music'], connections=None, coord_events=[], bg_events=[],
                    allow_cycling=False)

    def npc(x, y, graphics, script, elevation=3):
        return dict(graphics_id=graphics, x=x, y=y, elevation=elevation,
                    movement_type='MOVEMENT_TYPE_FACE_DOWN', movement_range_x=0,
                    movement_range_y=0, trainer_type='TRAINER_TYPE_NONE',
                    trainer_sight_or_berry_tree_id='0', script=script, flag='0')

    interior['object_events'] = [
        npc(*CAPTAIN, 'OBJ_EVENT_GFX_SAILOR', 'Journey_FerryPort17'),
        npc(8, 9, 'OBJ_EVENT_GFX_JOURNEY_SUBMARINE', 'JourneyCompactPort_Boat', 1),
    ]
    interior['warp_events'] = [dict(x=x, y=14, elevation=0,
                                   dest_map=city['id'], dest_warp_id=str(door_index))
                               for x in (11, 12)]
    # Double the existing indexed sprite without introducing extra colors or
    # changing its nine-frame ordering; use the engine's native 64x64 OAM.
    path = 'graphics/object_events/pics/journey/submarine.png'
    sheet = Image.open(s/path)
    assert sheet.size == (32, 288) and sheet.mode == 'P'
    enlarged = sheet.resize((64, 576), Image.Resampling.NEAREST)
    stream = io.BytesIO()
    enlarged.save(stream, format='PNG')
    layer.stage(path, stream.getvalue())
    path = 'src/data/object_events/object_event_pic_tables.h'
    text = (s/path).read_text()
    old = 'overworld_ascending_frames(gObjectEventPic_JourneySubmarine,4,4)'
    assert text.count(old) == 1
    layer.stage(path, text.replace(old, 'overworld_ascending_frames(gObjectEventPic_JourneySubmarine,8,8)'))
    path = 'src/data/object_events/object_event_graphics_info.h'
    text = (s/path).read_text()
    pattern = r'(const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_JourneySubmarine=\{)(.*?)(\};)'
    match = re.search(pattern, text)
    assert match
    body = match[2].replace('.size=512', '.size=2048').replace('.width=32', '.width=64')
    body = body.replace('.height=32', '.height=64').replace('_32x32', '_64x64')
    layer.stage(path, text[:match.start(2)]+body+text[match.end(2):])
    # Clear the old ship collision and cargo stacks in this private layout.
    for y in range(6, 10):
        for x in range(5, 24):
            inside[y*layout['width']+x] &= ~0x400
    for y in range(11, 15):
        for x in range(18, 24):
            inside[y*layout['width']+x] = 0x3202
    hull = [[x, y] for y in range(6, 10) for x in range(6, 11)]
    for x, y in hull:
        at = y*layout['width']+x
        assert inside[at] >> 12 == 1
        inside[at] |= 0x400
    layer.stage(layout['blockdata_filepath'], struct.pack('<'+'H'*len(inside), *inside))
    layer.stage(layout['border_filepath'], (s/native_layout['border_filepath']).read_bytes())
    layer.stage(f'data/maps/{HARBOR}/map.json', json.dumps(interior, indent=2)+'\n')
    layer.stage(f'data/maps/{HARBOR}/scripts.inc', HARBOR+'_MapScripts::\n\t.byte 0\n')
    layer.stage('data/layouts/layouts.json', json.dumps(data, indent=2)+'\n')
    groups = json.loads((s/'data/maps/map_groups.json').read_text())
    group = next(k for k in groups['group_order'] if 'JourneyMossdeepSailorsLodge' in groups[k])
    groups[group].append(HARBOR)
    layer.stage('data/maps/map_groups.json', json.dumps(groups, indent=2)+'\n')
    layer.stage('data/event_scripts.s', (s/'data/event_scripts.s').read_text()
                + f'\n\t.include "data/maps/{HARBOR}/scripts.inc"\n')
    # Stable destination 17 preserves every existing network menu and exclusion
    # of the current port. Only its landing map and coordinates move indoors.
    path = 'data/scripts/journey_campaign_gates.inc'
    script = (s/path).read_text()
    a = script.index('LavenderNetwork_Destination17::\n')
    b = script.index('\n\n', a)
    destination = script[a:b].replace('MAP_SOOTOPOLIS_CITY)', MAP+')')
    for var, value in [('0x8009', ARRIVAL[0]), ('0x800A', ARRIVAL[1])]:
        destination, count = re.subn(r'(setvar VAR_'+var+r', )\d+',
                                    lambda m: m[1]+str(value), destination)
        assert count == 1
    layer.stage(path, script[:a]+destination+script[b:])
    # A new game starting in Sootopolis also lands in the terminal. Its mother
    # stands clear of the permanent captain, and no second boat is spawned.
    path = 'include/journey_birth_arrivals.h'
    text, count = re.subn(r'\{MAP_SOOTOPOLIS_CITY, \d+, \d+, \d+, \d+, TRUE\}',
                         '{'+MAP+', 8, 9, 11, 12, TRUE}', (s/path).read_text())
    assert count == 1
    layer.stage(path, text)
    path = 'src/journey_birth.c'
    text = (s/path).read_text()
    old = '&& index != 29 && index != 31)'
    assert text.count(old) == 1
    layer.stage(path, text.replace(old, '&& index != 29 && index != 30 && index != 31)'))
    return layer.finish(exterior='SootopolisCity', interior=HARBOR,
                        door=list(DOOR), bridge=bridge, shore=[16, 45],
                        terminal=[20, 39, 7, 6], captain=list(CAPTAIN),
                        arrival=list(ARRIVAL), submarine=[8, 9], hull=hull,
                        submarine_sprite_size=[64, 64], submarine_scale=2,
                        world_port_id=17, native_story_objects_preserved=True,
                        crisis_layout_supported=True, bridge_extended_left_tiles=1,
                        outside_captain_removed=True, private_interior_layout=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().source), indent=2))
