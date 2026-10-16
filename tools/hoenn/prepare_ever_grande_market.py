"""Add two furnished Ever Grande homes, a native market stall and city emblem."""
import argparse
import copy
import json
import re
import struct
from pathlib import Path

from PIL import Image
from candidate_layer import Layer
from import_native_pier import import_pier
from prepare_dewford_competitive_shop import PRIOR, LAYER as PREVIOUS
from prepare_world_dex_map import COLORS, decode, encode
from render_sea_maps import MapRenderer

LAYER = 'ever-grande-market'
PRIOR = PRIOR + [PREVIOUS]
ROOT = Path(__file__).resolve().parents[2]
HOUSES = [('JourneyEverGrandeHouse1', 13, 45, 'ITEM_FULL_RESTORE', 'FLAG_JOURNEY_EVER_FULL_RESTORE', 0x1B3E),
          ('JourneyEverGrandeHouse2', 20, 45, 'ITEM_MAX_REVIVE', 'FLAG_JOURNEY_EVER_MAX_REVIVE', 0x1B3F)]
PRICE = 200000


def prepare(source):
    layer = Layer(source, LAYER, PRIOR)
    if old := layer.existing():
        return old
    s = layer.source
    r = MapRenderer(s)
    def load(name):
        m = json.loads((s/f'data/maps/{name}/map.json').read_text())
        l = r.layouts[m['layout']]
        raw = (s/l['blockdata_filepath']).read_bytes()
        return m, l, list(struct.unpack('<'+'H'*(len(raw)//2), raw))
    city, layout, v = load('EverGrandeCity')
    original = v.copy()
    _, donor, house = load('OldaleTown')
    house = [house[y*donor['width']+x] for y in range(4,8) for x in range(4,8)]
    _, market, stall = load('SlateportCity')
    stall = [stall[y*market['width']+x] for y in range(41,44) for x in range(2,6)]
    # Only reserve metatiles not referenced by any layout sharing this bank.
    used = set()
    for l in r.layouts.values():
        if l['secondary_tileset'] != layout['secondary_tileset']: continue
        for k in ['blockdata_filepath','border_filepath']:
            raw = (s/l[k]).read_bytes()
            used.update(x&1023 for x in struct.unpack('<'+'H'*(len(raw)//2),raw))
    slots = [x for x in range(0x2B0,0x3E0) if x not in used]
    mids = sorted({x&1023 for x in house})
    ids, files = import_pier(s, layout['secondary_tileset'], emerald=True,
                            donor=donor['secondary_tileset'], donor_emerald=True,
                            mids=mids, metatile_slots=slots[:len(mids)])
    house_ids = ids.copy()
    house_files = files.copy()
    remaining = slots[len(mids):]
    mids = sorted({x&1023 for x in stall})
    stall_ids, files = import_pier(s, layout['secondary_tileset'], emerald=True,
                                  donor=market['secondary_tileset'], donor_emerald=True,
                                  mids=mids, metatile_slots=remaining[:len(mids)], overrides=files)
    files = house_files | files
    for p, raw in files.items(): layer.stage(p,raw)
    # Clone complete native 4x4 homes onto the flowerbeds. Keep all mountains,
    # the central three-tile path, both stairs, Center and Victory Road intact.
    def place(blocks,x,y,width,ids):
        for i,value in enumerate(blocks):
            xx,yy=x+i%width,y+i//width
            assert original[yy*40+xx]&1023 in [1, *range(0x200,0x300)], (xx,yy)
            v[yy*40+xx]=(5<<12)|(value&0xC00)|ids[value&1023]
    groups = json.loads((s/'data/maps/map_groups.json').read_text())
    groups['group_order'].append('JourneyEverGrandeHomes')
    groups['JourneyEverGrandeHomes'] = []
    scripts = []
    flags = (s/'include/constants/flags.h').read_text()
    for index,(name,x,y,item,flag,number) in enumerate(HOUSES):
        assert not re.search(r'^#define\s+FLAG_\w+\s+0x'+f'{number:X}'+r'\b',flags,re.M|re.I)
        assert number<=int(re.search(r'^#define JOURNEY_FLAGS_END\s+(0x\w+)',flags,re.M)[1],16)
        flags += f'\n#define {flag} 0x{number:X}\n'
        place(house,x,y,4,house_ids)
        exterior_warp = len(city['warp_events'])
        city['warp_events'].append(dict(x=x+1,y=y+3,elevation=0,dest_map='MAP_'+name.upper(),dest_warp_id='0'))
        inside = copy.deepcopy(load('OldaleTown_House1' if index==0 else 'MossdeepCity_House1')[0])
        inside.update(id='MAP_'+name.upper(),name=name,region_map_section=city['region_map_section'],music=city['music'])
        for warp in inside['warp_events']:
            warp.update(dest_map=city['id'],dest_warp_id=str(exterior_warp))
        inside['object_events'] = [dict(graphics_id='OBJ_EVENT_GFX_WOMAN_2' if index==0 else 'OBJ_EVENT_GFX_OLD_MAN',
            x=6 if index==0 else 7,y=4,elevation=3,movement_type='MOVEMENT_TYPE_FACE_DOWN',
            movement_range_x=0,movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',
            script=name+'_Gift',flag='0'),
            dict(graphics_id='OBJ_EVENT_GFX_GIRL_1' if index==0 else 'OBJ_EVENT_GFX_MAN_1',x=2,y=6 if index==0 else 4,elevation=3,
            movement_type='MOVEMENT_TYPE_FACE_RIGHT',movement_range_x=0,movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',
            trainer_sight_or_berry_tree_id='0',script=name+'_Neighbor',flag='0')]
        inside.update(coord_events=[],bg_events=[])
        layer.stage(f'data/maps/{name}/map.json',json.dumps(inside,indent=2)+'\n')
        label = 'FULL RESTORE' if index==0 else 'MAX REVIVE'
        scripts.append(f'''{name}_MapScripts::
\t.byte 0
{name}_Gift::
\tlock
\tfaceplayer
\tgoto_if_set {flag}, {name}_After
\tmsgbox {name}_Offer, MSGBOX_DEFAULT
\tgiveitem {item}, 1
\tgoto_if_eq VAR_RESULT, FALSE, {name}_Finish
\tsetflag {flag}
{name}_After:
\tmsgbox {name}_Thanks, MSGBOX_DEFAULT
{name}_Finish:
\trelease
\tend
{name}_Neighbor::
\tmsgbox {name}_Chat, MSGBOX_NPC
\tend
{name}_Offer:
\t.string "Welcome to EVER GRANDE!\\n"
\t.string "Take this {label} for your trip.$"
{name}_Thanks:
\t.string "Good luck on VICTORY ROAD!\\n"
\t.string "You can rest at the POKeMON CENTER.$"
{name}_Chat:
\t.string "Our little market sells MEGA STONES.\\n"
\t.string "Rare stones cost a small fortune!$"
''')
        groups['JourneyEverGrandeHomes'].append(name)
    # The stall's native canopy/poles sit on the already walkable lower lawn.
    place(stall,25,50,4,stall_ids)
    # Clear only the two small flower patches at the counter and its approach.
    for x,y in [(26,52),(27,52),(26,53),(27,53),(27,49),(28,49)]: v[y*40+x]=0x5001
    city['object_events'].append(dict(graphics_id='OBJ_EVENT_GFX_MART_EMPLOYEE',x=26,y=52,elevation=5,
        movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,movement_range_y=0,
        trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',script='JourneyEverGrande_MegaSeller',flag='0'))
    city['bg_events'].append(dict(type='sign',x=28,y=53,elevation=5,player_facing_dir='BG_EVENT_PLAYER_FACING_ANY',script='JourneyEverGrande_MarketSign'))
    v[53*40+28]=0x5403
    # Every actual mega stone in the native item table; no Orbs or Z-Crystals.
    itemdata=(s/'src/data/items.h').read_text()
    stones=[m[1] for m in re.finditer(r'\[(ITEM_\w+)\]\s*=\s*\{(.*?)\n    \},',itemdata,re.S) if '.holdEffect = HOLD_EFFECT_MEGA_STONE,' in m[2]]
    assert len(stones)>=47
    scripts.append('''JourneyEverGrande_MegaSeller::
\tlock
\tfaceplayer
\tmsgbox JourneyEverGrande_MarketWelcome, MSGBOX_DEFAULT
\tpokemart JourneyEverGrande_MegaStock
\tmsgbox JourneyEverGrande_MarketBye, MSGBOX_DEFAULT
\trelease
\tend
JourneyEverGrande_MarketSign::
\tmsgbox JourneyEverGrande_MarketWelcome, MSGBOX_SIGN
\tend
JourneyEverGrande_MarketWelcome:
\t.string "EVER GRANDE MEGA MARKET\\n"
\t.string "Rare MEGA STONES: 200,000 each!$"
JourneyEverGrande_MarketBye:
\t.string "Thank you! Visit our market again.$"
\t.align 2
JourneyEverGrande_MegaStock::
'''+''.join('\t.2byte '+item+'\n' for item in stones)+'\t.2byte ITEM_NONE\n')
    layer.stage('data/maps/JourneyEverGrandeHomes.inc','\n'.join(scripts))
    layer.stage('data/maps/map_groups.json',json.dumps(groups,indent=2)+'\n')
    layer.stage('data/event_scripts.s',(s/'data/event_scripts.s').read_text()+'\n\t.include "data/maps/JourneyEverGrandeHomes.inc"\n')
    layer.stage('include/constants/flags.h',flags)
    layer.stage('data/maps/EverGrandeCity/map.json',json.dumps(city,indent=2)+'\n')
    layer.stage(layout['blockdata_filepath'],struct.pack('<3200H',*v))
    # Use the imported house palette for the real native door animation.
    meta=next(raw for p,raw in files.items() if p.endswith('/metatiles.bin'))
    bank=struct.unpack_from('<H',meta,(house_ids[0x287]-512)*16+8)[0]>>12
    text=(s/'src/field_door.c').read_text();anchor='static const struct DoorGraphics sDoorAnimGraphicsTable[] =\n{'
    text=text.replace(anchor,'static const u8 sDoorAnimPalettes_JourneyEver[] = {'+','.join([str(bank)]*8)+'};\n'+anchor+f'\n    {{{house_ids[0x287]}, &gTileset_EverGrande, DOOR_SOUND_NORMAL, 1, sDoorAnimTiles_Oldale, sDoorAnimPalettes_JourneyEver}},')
    layer.stage('src/field_door.c',text)
    # A stock-specific price never changes item resale value or other marts.
    text=(s/'src/shop.c').read_text().replace('#include "constants/items.h"','#include "constants/items.h"\n#include "constants/hold_effects.h"')
    needle='GetItemPrice(itemId) >> IsPokeNewsActive(POKENEWS_SLATEPORT)';text=text.replace(needle,'JourneyEverGrandeShopPrice(itemId)')
    text=text.replace('GetItemPrice(tItemId) >> IsPokeNewsActive(POKENEWS_SLATEPORT)','JourneyEverGrandeShopPrice(tItemId)')
    anchor='static EWRAM_DATA struct ShopData *sShopData'
    at=text.index(anchor)
    text=text[:at]+'''extern const u16 JourneyEverGrande_MegaStock[];
static EWRAM_DATA bool8 sJourneyEverGrandeMarket = FALSE;
u32 JourneyEverGrandeShopPrice(u16 itemId)
{
    if (sJourneyEverGrandeMarket
        && GetItemHoldEffect(itemId) == HOLD_EFFECT_MEGA_STONE)
        return 200000;
    return GetItemPrice(itemId) >> IsPokeNewsActive(POKENEWS_SLATEPORT);
}

'''+text[at:]
    text=text.replace('    sMartInfo.itemList = items;', '    sJourneyEverGrandeMarket = (items == JourneyEverGrande_MegaStock);\n    sMartInfo.itemList = items;')
    layer.stage('src/shop.c',text)
    # Restore the red native city emblem; Cave of Origin remains in the city
    # and keeps its registered name/GPS point without covering the city icon.
    header=(s/'src/data/journey_world_map.h').read_text();atlas=decode(header)
    native=Image.open(ROOT/'web/atlas/hoenn.png').convert('RGB').resize((124,46),Image.Resampling.NEAREST)
    palette=Image.new('P',(1,1));palette.putpalette([x for c in COLORS for x in c]+[0]*720)
    native=native.quantize(palette=palette,dither=Image.Dither.NONE)
    detail=list(map(int,re.search(r'sWorldDetailPixels\[\] = \{([^}]+)',header)[1].split(',')))
    city_pixels=[]
    for y in range(87,91):
        for x in range(111,114):
            color=native.getpixel((x-17,y-66));atlas.putpixel((x,y),color);city_pixels.append([x,y,color])
            for dy in [0,1]:
                for dx in [0,1]:
                    xx,yy=2*x+dx,2*y+dy;i=yy*224+xx//2;shift=(xx&1)*4
                    detail[i]=(detail[i]&~(15<<shift))|(color<<shift)
    assert any(c==13 for x,y,c in city_pixels)
    header=encode(header,atlas);header=re.sub(r'(sWorldDetailPixels\[\] = \{)[^}]+',lambda m:m[1]+','.join(map(str,detail)),header)
    layer.stage('src/data/journey_world_map.h',header)
    return layer.finish(houses=[dict(map=n,door=[x+1,y+3],item=item,flag=flag,flag_id=f) for n,x,y,item,flag,f in HOUSES],
        stall=dict(position=[25,50],seller=[26,52],interaction=[26,53],price=PRICE,stock=stones),
        imported_house_metatiles=house_ids,imported_stall_metatiles=stall_ids,city_pixels=city_pixels,
        original_center_victory_road_warps_preserved=True,all_surf_maps_unchanged=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    print(json.dumps(prepare(p.parse_args().source),indent=2))
