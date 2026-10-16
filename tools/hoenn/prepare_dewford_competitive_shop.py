"""Add Dewford's two-person training stall without changing the sea network."""
import argparse
import io
import json
import re
import struct
from pathlib import Path
from PIL import Image

from candidate_layer import Layer
from import_native_pier import import_pier
from prepare_surf_review import PRIOR, LAYER as PREVIOUS
from render_sea_maps import MapRenderer

LAYER = 'dewford-competitive-shop'
PRIOR = PRIOR + [PREVIOUS]
HELD = ['CHOICE_BAND','CHOICE_SPECS','CHOICE_SCARF','FLAME_ORB','TOXIC_ORB',
        'LIFE_ORB','FOCUS_SASH','EVIOLITE','ROCKY_HELMET','AIR_BALLOON','RED_CARD',
        'EJECT_BUTTON','WEAKNESS_POLICY','ASSAULT_VEST','SAFETY_GOGGLES',
        'TERRAIN_EXTENDER','PROTECTIVE_PADS','THROAT_SPRAY','EJECT_PACK',
        'HEAVY_DUTY_BOOTS','BLUNDER_POLICY','ROOM_SERVICE','UTILITY_UMBRELLA',
        'CLEAR_AMULET','COVERT_CLOAK','LOADED_DICE','BOOSTER_ENERGY','MIRROR_HERB',
        'PUNCHING_GLOVE','ABILITY_SHIELD','LEFTOVERS','DESTINY_KNOT','POWER_HERB',
        'BLACK_SLUDGE']
PREMIUM = {'LIFE_ORB','FOCUS_SASH','EVIOLITE','ASSAULT_VEST','HEAVY_DUTY_BOOTS',
           'BOOSTER_ENERGY','CLEAR_AMULET','COVERT_CLOAK','LOADED_DICE','MIRROR_HERB',
           'LEFTOVERS','CHOICE_SCARF','CHOICE_SPECS'}
MID = {'CHOICE_BAND','WEAKNESS_POLICY','ROCKY_HELMET','SAFETY_GOGGLES',
       'PROTECTIVE_PADS','THROAT_SPRAY','PUNCHING_GLOVE','ABILITY_SHIELD',
       'DESTINY_KNOT','POWER_HERB','BLACK_SLUDGE'}
FLAG = 'FLAG_JOURNEY_DEWFORD_FULL_RESTORE'
TM_FLAG = 'FLAG_JOURNEY_DEWFORD_PLAY_ROUGH'


def compact_graphics(renderer, used):
    """Free identical indexed graphics, preserving palette/flip bits and animation."""
    image,_,old=renderer.tileset('gTileset_JourneyDewfordHarbor')
    seen={};mapping={}
    for mid in range(512,1024):
        if mid in range(682,688):continue # native animated flag
        tile=image.crop(((mid-512)%16*8,(mid-512)//16*8,(mid-512)%16*8+8,(mid-512)//16*8+8))
        for transformed,bits in [(tile,0),(tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT),0x400),
                                 (tile.transpose(Image.Transpose.FLIP_TOP_BOTTOM),0x800),
                                 (tile.transpose(Image.Transpose.ROTATE_180),0xC00)]:
            if transformed.tobytes() in seen:
                mapping[mid]=(seen[transformed.tobytes()],bits);break
        else:seen[tile.tobytes()]=mid
    words=[((w&~1023)^mapping[w&1023][1])|mapping[w&1023][0] if w&1023 in mapping else w for w in old]
    for mid in range(512,512+len(words)//8):
        if mid not in used | {0x239,0x23A}:words[(mid-512)*8:(mid-511)*8]=[0]*8
    # The Dewford callback writes these flag tiles even when no current map
    # references them. Reserve them in one unused metatile for the importer.
    guard=max(mid for mid in range(512,512+len(words)//8) if mid not in used | {0x239,0x23A})
    words[(guard-512)*8:(guard-511)*8]=list(range(682,688))+[682,683]
    png=io.BytesIO();image.save(png,format='PNG')
    return {'data/tilesets/secondary/journey_dewford_harbor/metatiles.bin':struct.pack('<'+'H'*len(words),*words),
            'data/tilesets/secondary/journey_dewford_harbor/tiles.png':png.getvalue()}


def inventory(source):
    constants=(Path(source)/'include/constants/items.h').read_text()
    mints=re.findall(r'^\s*ITEM_(\w+_MINT)\s*=',constants,re.M)
    groups=[HELD,['ABILITY_CAPSULE','ABILITY_PATCH'],mints,
            ['HEALTH_FEATHER','MUSCLE_FEATHER','RESIST_FEATHER','GENIUS_FEATHER',
             'CLEVER_FEATHER','SWIFT_FEATHER','POWER_WEIGHT','POWER_BRACER',
             'POWER_BELT','POWER_LENS','POWER_BAND','POWER_ANKLET'],
            ['BOTTLE_CAP','GOLD_BOTTLE_CAP']]
    prices={i:100000 if i in PREMIUM else 75000 if i in MID else 50000 for i in HELD}
    prices.update(ABILITY_CAPSULE=250000,ABILITY_PATCH=500000,
                  BOTTLE_CAP=100000,GOLD_BOTTLE_CAP=500000)
    prices.update({i:100000 for i in mints})
    prices.update({i:15000 if i.endswith('FEATHER') else 80000 for i in groups[3]})
    assert set(prices)=={i for group in groups for i in group}
    return groups,prices


def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    s=layer.source;r=MapRenderer(s);layouts=json.loads((s/'data/layouts/layouts.json').read_text())['layouts']
    ls={l['id']:l for l in layouts};maps={};grids={};used=set()
    for p in (s/'data/maps').glob('*/map.json'):
        m=json.loads(p.read_text());l=ls[m['layout']]
        if l['secondary_tileset']!='gTileset_JourneyDewfordHarbor':continue
        maps[p.parent.name]=m
        for key in ('blockdata_filepath','border_filepath'):
            raw=(s/l[key]).read_bytes();vals=list(struct.unpack('<'+'H'*(len(raw)//2),raw))
            used.update(v&1023 for v in vals)
            if key=='blockdata_filepath':grids[p.parent.name]=vals
    slots=[mid for mid in range(512,1024) if mid not in used]
    # One covered Slateport market booth, shortened by one repeated center
    # column. It keeps both original end posts and two adjacent attendants.
    booth=[[0x270,0x216,0x216,0x272],[0x278,0x21E,0x21E,0x27A]]
    donor_mids=list(dict.fromkeys(sum(booth,[])+[0x263,0x264]))
    ids,files=import_pier(s,'gTileset_JourneyDewfordHarbor',emerald=True,
                         donor='gTileset_Slateport',donor_emerald=True,
                         mids=donor_mids,metatile_slots=slots[:len(donor_mids)],
                         overrides=compact_graphics(r,used))
    attrpath='data/tilesets/secondary/journey_dewford_harbor/metatile_attributes.bin'
    attrs=bytearray(files[attrpath])
    for mid in ids.values():struct.pack_into('<H',attrs,(mid-512)*2,0)
    metapath='data/tilesets/secondary/journey_dewford_harbor/metatiles.bin'
    words=list(struct.unpack('<'+'H'*(len(files[metapath])//2),files[metapath]))
    sand=r.tileset('gTileset_General')[2][0x124*8:0x124*8+4]
    # Ground at the original market posts is paving; Dewford retains sand.
    for donor in (0x270,0x272,0x278,0x27A,0x263,0x264):
        mid=ids[donor];words[(mid-512)*8:(mid-512)*8+4]=sand
    # Keep the two right canopy cells over the exact shore at (3,12).
    shore=grids['Route107'][12*ls[maps['Route107']['layout']]['width']+3]&1023
    assert shore>=512
    beach=words[(shore-512)*8+4:(shore-511)*8]
    for donor in (0x272,0x27A):
        at=(ids[donor]-512)*8;words[at:at+4]=beach
    files[metapath]=struct.pack('<'+'H'*len(words),*words)
    files[attrpath]=bytes(attrs)
    for p,raw in files.items():layer.stage(p,raw)
    def put(n,x,y,value):grids[n][y*ls[maps[n]['layout']]['width']+x]=value
    for y,row in enumerate(booth):
        for x,mid in enumerate(row):put('Route107',x,y+13,0x3400|ids[mid])
    put('Route107',0,15,0x3400|ids[0x263]);put('Route107',3,15,0x3400|ids[0x264])
    for x in (1,2):put('Route107',x,15,0x3124)
    for x in (8,9):
        put('JourneyDewfordPortIsland',x,6,0x4639) # world y=-6
        put('JourneyDewfordPortIsland',x,7,0x463A)
    # Preserve the complete beach under the eastern tree instead of replacing
    # its wet-sand edge with a square of plain sand.
    words=list(struct.unpack('<'+'H'*(len(files[metapath])//2),files[metapath]))
    original=struct.unpack('<'+'H'*((s/ls[maps['JourneyDewfordPortIsland']['layout']]['blockdata_filepath']).stat().st_size//2),
                           (s/ls[maps['JourneyDewfordPortIsland']['layout']]['blockdata_filepath']).read_bytes())
    native=words[:]
    for yy,tree,slot in zip((6,7),(0x239,0x23A),slots[len(donor_mids):len(donor_mids)+2]):
        old=original[yy*16+9]&1023
        assert old>=512
        base=native[(old-512)*8+4:(old-511)*8]
        foreground=native[(tree-512)*8+4:(tree-511)*8]
        words[(slot-512)*8:(slot-511)*8]=list(base)+list(foreground)
        struct.pack_into('<H',attrs,(slot-512)*2,0)
        put('JourneyDewfordPortIsland',9,yy,0x4400|slot)
    layer.stage(metapath,struct.pack('<'+'H'*len(words),*words));layer.stage(attrpath,bytes(attrs))
    def npc(x,script,gfx):
        return dict(type='object',graphics_id=gfx,x=x,y=15,elevation=3,
                    movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,
                    movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',
                    trainer_sight_or_berry_tree_id='0',script=script,flag='0')
    maps['Route107']['object_events'] += [npc(1,'JourneyCompetitive_Trainer','OBJ_EVENT_GFX_EXPERT_M'),
                                        npc(2,'JourneyCompetitive_Seller','OBJ_EVENT_GFX_MART_EMPLOYEE')]
    item=dict(type='object',graphics_id='OBJ_EVENT_GFX_ITEM_BALL',x=75,y=16,
              elevation=4,movement_type='MOVEMENT_TYPE_LOOK_AROUND',movement_range_x=0,
              movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',
              trainer_sight_or_berry_tree_id='0',script='JourneyCompetitive_FullRestore',flag=FLAG)
    assert all((o['x'],o['y'])!=(75,16) for o in maps['Route106']['object_events'])
    maps['Route106']['object_events'].append(item)
    tm=dict(item,graphics_id='OBJ_EVENT_GFX_ITEM_BALL',x=7,y=6,
            script='JourneyCompetitive_PlayRough',flag=TM_FLAG)
    maps['JourneyDewfordPortIsland']['object_events'].append(tm)
    # The lighthouse peak is vertical artwork, not a ground-level obstacle.
    for x in (78,79):
        pos=14*ls[maps['Route106']['layout']]['width']+x
        grids['Route106'][pos]&=~0xC00
    for n in maps:
        l=ls[maps[n]['layout']]
        if n in ('Route107','Route106','JourneyDewfordPortIsland'):layer.stage(l['blockdata_filepath'],struct.pack('<'+'H'*len(grids[n]),*grids[n]))
        if n in ('Route107','Route106','JourneyDewfordPortIsland'):layer.stage(f'data/maps/{n}/map.json',json.dumps(maps[n],indent=2)+'\n')
    p='include/constants/flags.h';flags=(s/p).read_text()
    assert '#define JOURNEY_FLAGS_END' in flags
    usedflags={int(v,16) for v in re.findall(r'^#define\s+\w+\s+(0x[0-9A-Fa-f]+)\b',flags,re.M)}
    flag=next(f for f in range(0x1B3C,0x1B80) if f not in usedflags)
    assert flag+1 not in usedflags and flag+1<=0x1B3F
    layer.stage(p,flags+f'\n#define {FLAG} {hex(flag)}\n#define {TM_FLAG} {hex(flag+1)}\n')
    p='include/constants/tms_hms.h';tms=(s/p).read_text()
    tm_count=len(re.findall(r'F\(\w+\)',tms.split('#define FOREACH_TM(F)',1)[1].split('#define FOREACH_HM',1)[0]))
    old=tms.split('#define FOREACH_HM',1)[0].rstrip().splitlines()[-1]
    tms=tms.replace(old+'\n',old+' \\\n    F(PLAY_ROUGH)\n',1);layer.stage(p,tms)
    # Keep the modern story rewards and let the original Orbs transform too.
    p='src/data/pokemon/form_change_tables.h';forms=(s/p).read_text()
    for species,item,modern in [('DIALGA','ADAMANT_ORB','ADAMANT_CRYSTAL'),
                                ('PALKIA','LUSTROUS_ORB','LUSTROUS_GLOBE')]:
        needle='{FORM_CHANGE_ITEM_HOLD, SPECIES_'+species+'_ORIGIN, ITEM_'+modern+'},'
        assert forms.count(needle)==1
        forms=forms.replace(needle,needle+'\n    {FORM_CHANGE_ITEM_HOLD, SPECIES_'+species+'_ORIGIN, ITEM_'+item+'},')
    needle='#if I_GRISEOUS_ORB_FORM_CHANGE < GEN_9\n    {FORM_CHANGE_ITEM_HOLD, SPECIES_GIRATINA_ORIGIN, ITEM_GRISEOUS_ORB},\n#endif'
    assert forms.count(needle)==1
    forms=forms.replace(needle,'    {FORM_CHANGE_ITEM_HOLD, SPECIES_GIRATINA_ORIGIN, ITEM_GRISEOUS_ORB},')
    layer.stage(p,forms)
    groups,prices=inventory(s)
    p='src/data/items.h';text=(s/p).read_text()
    for item,price in prices.items():
        pattern=r'(\[ITEM_'+item+r'\]\s*=\s*\{.*?\.price\s*=\s*)[^,]+,'
        text,count=re.subn(pattern,lambda m:m[1]+str(price)+',',text,count=1,flags=re.S)
        assert count==1,item
    for item,description in [('ADAMANT_ORB',"Reveals Dialga's\\nOrigin form. Boosts\\nDragon and Steel."),
                             ('LUSTROUS_ORB',"Reveals Palkia's\\nOrigin form. Boosts\\nDragon and Water."),
                             ('GRISEOUS_ORB',"Reveals Giratina's\\nOrigin form. Boosts\\nDragon and Ghost."),
                             ('BOTTLE_CAP','Trade for one stat of\\nHyper Training at\\nDewford\'s stall.'),
                             ('GOLD_BOTTLE_CAP','Trade for all six stats\\nof Hyper Training at\\nDewford\'s stall.')]:
        pattern=r'(\[ITEM_'+item+r'\]\s*=\s*\{.*?\.description\s*=\s*)COMPOUND_STRING\(.*?\),'
        text,count=re.subn(pattern,lambda m:m[1]+'COMPOUND_STRING("'+description+'"),',text,count=1,flags=re.S);assert count==1
    tm_name=f'TM{tm_count+1:02}'
    pattern=r'\[ITEM_'+tm_name+r'\]\s*=\s*\{.*?\n    \},'
    record='''[ITEM_TM_PLAY_ROUGH] =
    {
        .name = ITEM_NAME("'''+tm_name+'''"),
        .price = 10000,
        .description = COMPOUND_STRING("Plays rough with the\\nfoe. May lower its\\nAttack stat."),
        .importance = I_REUSABLE_TMS,
        .pocket = POCKET_TM_HM,
        .type = ITEM_USE_PARTY_MENU,
        .fieldUseFunc = ItemUseOutOfBattle_TMHM,
    },'''
    text,count=re.subn(pattern,lambda m:record,text,count=1,flags=re.S)
    if not count:
        assert text.count('\n};')==1
        text=text.replace('\n};','\n    '+record+'\n};')
    layer.stage(p,text)
    script=(Path(__file__).parent/'data/dewford-competitive-shop.inc').read_text()
    for i,group in enumerate(groups):
        script+=f'\n\t.align 2\nJourneyCompetitive_Stock{i}:\n'+''.join('\t.2byte ITEM_'+item+'\n' for item in group)+'\t.2byte ITEM_NONE\n'
    layer.stage('data/scripts/journey_competitive_shop.inc',script)
    layer.stage('src/journey_competitive_shop.c',(Path(__file__).parent/'data/dewford-competitive-shop.c').read_bytes())
    p='data/event_scripts.s';layer.stage(p,(s/p).read_text()+'\n\t.include "data/scripts/journey_competitive_shop.inc"\n')
    return layer.finish(stocks=groups,prices=prices,seller=[2,15],hyper_trainer=[1,15],
                        booth=[0,13,4,3],booth_shore_underlay=dict(cells=[[3,13],[3,14]],reference=[3,12]),item=dict(map='Route106',world=[-5,-4],position=[75,16],item='ITEM_FULL_RESTORE',flag=flag),
                        tm=dict(map='JourneyDewfordPortIsland',world=[7,-6],position=[7,6],item='ITEM_TM_PLAY_ROUGH',number=tm_count+1,flag=flag+1),
                        lighthouse_peak_walkable=[[-2,-6],[-1,-6]],
                        closing_trees=[[8,-6],[9,-6]],hyper_training_minimum_level=50,
                        origin_orbs={'DIALGA':'ADAMANT_ORB','PALKIA':'LUSTROUS_ORB','GIRATINA':'GRISEOUS_ORB'},
                        modern_origin_rewards_preserved=True,
                        all_existing_npcs_preserved=True,bridge_and_water_preserved=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    print(json.dumps(prepare(p.parse_args().source),indent=2))
