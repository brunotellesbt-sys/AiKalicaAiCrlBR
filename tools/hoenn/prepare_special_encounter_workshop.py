"""Reserve event-only families and add Lavender's appliance workshop."""
import argparse,copy,io,json,re,struct
from pathlib import Path
from PIL import Image,ImageDraw
from candidate_layer import Layer
from prepare_form_move_legality import PRIOR,LAYER as PREVIOUS
from special_encounters import EVENTS,FOSSILS,FORM_TOOLS
from prepare_ecology import weighted_slots,LAND_RATES

ROOT=Path(__file__).resolve().parents[2]
LAYER='special-encounter-workshop';PRIOR=PRIOR+[PREVIOUS]

def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    source=layer.source
    def read(path):return layer.outputs.get(path,(source/path).read_bytes() if (source/path).exists() else b'')
    def edit(path,old,new):
        text=read(path).decode();assert text.count(old)==1,(path,old);layer.stage(path,text.replace(old,new))
    def append(path,text):layer.stage(path,read(path).decode()+text)
    def read_map(name):return json.loads(read(f'data/maps/{name}/map.json'))
    def save_map(m):layer.stage(f'data/maps/{m["name"]}/map.json',json.dumps(m,indent=2)+'\n')
    layouts=json.loads(read('data/layouts/layouts.json'));by_layout={l['id']:l for l in layouts['layouts']}
    def blocks(m):
        l=by_layout[m['layout']];return l,list(struct.unpack('<'+'H'*(l['width']*l['height']),read(l['blockdata_filepath'])))
    def npc(m,x,y,gfx,script):
        assert not any(e.get('x')==x and e.get('y')==y for k in ('object_events','warp_events','bg_events','coord_events') for e in m.get(k,[])),(m['name'],x,y)
        assert len(m['object_events'])<16
        m['object_events'].append(dict(graphics_id=gfx,x=x,y=y,elevation=3,movement_type='MOVEMENT_TYPE_FACE_DOWN',
            movement_range_x=0,movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',script=script,flag='0'))
    def free_spot(m,wanted):
        l,b=blocks(m);busy=[e for k in ('object_events','warp_events','coord_events','bg_events') for e in m.get(k,[])]
        spots=[]
        for y in range(2,l['height']-2):
            for x in range(2,l['width']-2):
                if any(abs(x-e.get('x',-99))<=1 and abs(y-e.get('y',-99))<=1 for e in busy):continue
                def ground(px,py):return not b[py*l['width']+px]&0xC00 and (b[py*l['width']+px]>>12)!=1
                if not ground(x,y) or not ground(x,y+1):continue
                if sum(ground(px,py) for px,py in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)])<2:continue
                spots.append(((x-wanted[0])**2+(y-wanted[1])**2,x,y))
        assert spots,m['name'];_,x,y=min(spots);return x,y

    # Small, distinct pixel-art appliances. Their entire 16x32 footprint is
    # collision; the sprite never overlaps the player's head or a walking tile.
    palette=[(0,0,0),(232,216,168),(76,78,91),(142,155,162),(229,239,238),(48,68,91),
             (60,154,202),(31,44,61),(232,87,69),(236,184,64),(91,149,77),(170,101,61),
             (111,87,62),(180,196,208),(246,246,218),(115,217,217)]
    sheet=Image.new('P',(128,32),1);sheet.putpalette([v for c in palette for v in c]+[0]*(768-48))
    draw=ImageDraw.Draw(sheet)
    for index,kind in enumerate(['tv','oven','washer','fridge','fan','mower']):
        x=index*16;draw.rectangle((x+2,5,x+13,28),fill=2)
        draw.rectangle((x+3,6,x+12,26),fill=4)
        draw.rectangle((x+3,27,x+5,29),fill=7);draw.rectangle((x+10,27,x+12,29),fill=7)
        if kind=='tv':
            draw.rectangle((x+3,7,x+12,19),fill=7)
            for py in range(8,19):
                for px in range(x+4,x+12):draw.point((px,py),fill=13 if (px*13+py*7)%3 else 5)
            draw.line((x+6,23,x+9,23),fill=6)
        elif kind=='oven':
            draw.rectangle((x+4,13,x+11,23),fill=5);draw.line((x+4,12,x+11,12),fill=8)
            draw.point((x+4,8),fill=8);draw.point((x+7,8),fill=8);draw.point((x+10,8),fill=8)
        elif kind=='washer':
            draw.ellipse((x+4,12,x+11,22),fill=5);draw.ellipse((x+5,14,x+10,20),fill=6)
            draw.line((x+4,9,x+9,9),fill=3)
        elif kind=='fridge':
            draw.line((x+3,13,x+12,13),fill=2);draw.line((x+10,16,x+10,22),fill=5);draw.point((x+10,10),fill=5)
        elif kind=='fan':
            draw.rectangle((x+2,5,x+13,28),fill=1);draw.ellipse((x+2,5,x+13,18),fill=3)
            draw.line((x+7,7,x+7,16),fill=4);draw.line((x+4,11,x+11,11),fill=4)
            draw.rectangle((x+7,18,x+8,26),fill=5);draw.rectangle((x+4,27,x+11,28),fill=2)
        else:
            draw.rectangle((x+2,5,x+13,28),fill=1);draw.line((x+4,7,x+4,23),fill=5);draw.line((x+4,7,x+12,7),fill=5)
            draw.rectangle((x+3,22,x+13,28),fill=10);draw.rectangle((x+5,20,x+11,23),fill=8)
            draw.rectangle((x+2,25,x+4,30),fill=7);draw.rectangle((x+12,25,x+14,30),fill=7)
    # Last tile is genuinely transparent, for the upper background layer.
    draw.rectangle((120,24,127,31),fill=0)
    folder='data/tilesets/secondary/journey_appliances'
    native_folder=source/'data/tilesets/secondary/generic_building'
    native_sheet=Image.open(native_folder/'tiles.png').copy()
    for tile in range(64):
        chip=sheet.crop((tile%16*8,tile//16*8,tile%16*8+8,tile//16*8+8))
        dest=448+tile;native_sheet.paste(chip,(dest%16*8,dest//16*8))
    data=io.BytesIO();native_sheet.save(data,format='PNG');layer.stage(folder+'/tiles.png',data.getvalue())
    pal='JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in palette)+'\n'
    for i in range(16):layer.stage(folder+f'/palettes/{i:02}.pal',pal if i==12 else (native_folder/f'palettes/{i:02}.pal').read_bytes())
    metas=[]
    for icon in range(6):
        for half in range(2):
            metas += [0xC000+960+half*32+dy*16+icon*2+dx for dy,dx in ((0,0),(0,1),(1,0),(1,1))]+[0xC000+1023]*4
    native_metas=bytearray((native_folder/'metatiles.bin').read_bytes())
    native_metas[400*16:412*16]=struct.pack('<'+'H'*len(metas),*metas)
    layer.stage(folder+'/metatiles.bin',native_metas)
    layer.stage(folder+'/metatile_attributes.bin',(native_folder/'metatile_attributes.bin').read_bytes())
    append('src/data/tilesets/graphics.h','\nconst u32 gTilesetTiles_JourneyAppliances[]=INCBIN_U32("'+folder+'/tiles.4bpp.lz");\nconst u16 gTilesetPalettes_JourneyAppliances[][16]={\n'+''.join('INCBIN_U16("'+folder+f'/palettes/{i:02}.gbapal"),\n' for i in range(16))+'};\n')
    append('src/data/tilesets/metatiles.h','\nconst u16 gMetatiles_JourneyAppliances[]=INCBIN_U16("'+folder+'/metatiles.bin");\nconst u16 gMetatileAttributes_JourneyAppliances[]=INCBIN_U16("'+folder+'/metatile_attributes.bin");\n')
    append('src/data/tilesets/headers.h','\nconst struct Tileset gTileset_JourneyAppliances={.isCompressed=TRUE,.isSecondary=TRUE,.tiles=gTilesetTiles_JourneyAppliances,.palettes=gTilesetPalettes_JourneyAppliances,.metatiles=gMetatiles_JourneyAppliances,.metatileAttributes=gMetatileAttributes_JourneyAppliances,.callback=NULL};\n')
    tower=read_map('PokemonTower_1F_Frlg');tl,tb=blocks(tower)
    entry=(21,9);assert not any((e['x'],e['y'])==entry for e in tower['warp_events'])
    tb[entry[1]*tl['width']+entry[0]]=tb[9*tl['width']+18]
    layer.stage(tl['blockdata_filepath'],struct.pack('<'+'H'*len(tb),*tb))
    entry_warp=len(tower['warp_events']);tower['warp_events'].append(dict(x=entry[0],y=entry[1],elevation=3,dest_map='MAP_JOURNEYLAVENDERWORKSHOP',dest_warp_id='0'));save_map(tower)
    room=copy.deepcopy(read_map('MauvilleCity_House2'))
    room.update(id='MAP_JOURNEYLAVENDERWORKSHOP',name='JourneyLavenderWorkshop',layout='LAYOUT_JOURNEY_LAVENDER_WORKSHOP',region='REGION_KANTO',
                region_map_section='MAPSEC_POKEMON_TOWER',music='MUS_RG_POKE_TOWER',object_events=[],warp_events=[],bg_events=[],coord_events=[],allow_escaping=True)
    # Primary Building floor/wall/door metatiles are taken from its native house.
    house_l,house_b=blocks(read_map('MauvilleCity_House2'))
    floor=house_b[6*house_l['width']+5]&0x3FF;wall=house_b[0]&0x3FF;door=house_b[8*house_l['width']+3]&0x3FF
    assert floor<1024 and wall<1024 and door<1024,(floor,wall,door)
    width,height=18,12;rb=[0x3000|floor]*(width*height)
    for y in range(height):
        for x in range(width):
            if x in (0,width-1) or y in (0,1):rb[y*width+x]=0x3C00|wall
    stations=[]
    for i,x in enumerate([2,5,8,11,14,8]):
        y=3 if i<5 else 7
        rb[y*width+x]=0x3C00|912+i*2;rb[(y+1)*width+x]=0x3C00|913+i*2
        script='JourneySpecial_RotomTV' if i==0 else 'JourneySpecial_Appliances'
        room['bg_events'].append(dict(type='sign',x=x,y=y+1,elevation=3,player_facing_dir='BG_EVENT_PLAYER_FACING_ANY',script=script))
        stations.append(dict(appliance=['TV','oven','washer','fridge','fan','mower'][i],x=x,y=y+1))
    rb[10*width+8]=0x3000|door;room['warp_events']=[dict(x=8,y=10,elevation=0,dest_map=tower['id'],dest_warp_id=str(entry_warp))]
    npc(room,3,8,'OBJ_EVENT_GFX_SCIENTIST_1','JourneySpecial_FormTools')
    npc(room,14,8,'OBJ_EVENT_GFX_SCIENTIST_1','JourneySpecial_WorkshopGuide')
    npc(room,12,8,'OBJ_EVENT_GFX_BREAKABLE_ROCK_FRLG','JourneySpecial_DeoxysMeteorite')
    save_map(room)
    layout=dict(id=room['layout'],name='JourneyLavenderWorkshop_Layout',width=width,height=height,primary_tileset='gTileset_Building',
        secondary_tileset='gTileset_JourneyAppliances',blockdata_filepath='data/layouts/JourneyLavenderWorkshop/map.bin',
        border_filepath='data/layouts/JourneyLavenderWorkshop/border.bin',layout_version='emerald')
    layouts['layouts'].append(layout);by_layout[layout['id']]=layout
    layer.stage(layout['blockdata_filepath'],struct.pack('<'+'H'*len(rb),*rb));layer.stage(layout['border_filepath'],struct.pack('<4H',*([0x3C00|wall]*4)))
    layer.stage('data/maps/JourneyLavenderWorkshop/scripts.inc','JourneyLavenderWorkshop_MapScripts::\n\t.byte 0\n')

    # Native icons become small, static overworld sprites; the well is authored
    # in the same indexed-palette format as the existing object graphics.
    well=Image.new('P',(32,32));well.putpalette(sheet.getpalette());wd=ImageDraw.Draw(well)
    wd.ellipse((3,11,28,30),fill=2);wd.rectangle((4,17,27,26),fill=3)
    for y in (18,23):wd.line((5,y,26,y),fill=2)
    for x,y in [(10,18),(20,18),(7,23),(16,23),(25,23)]:wd.line((x,y,x,y+4),fill=2)
    wd.ellipse((3,9,28,21),fill=13);wd.ellipse((7,12,24,18),fill=7)
    wd.line((5,4,5,14),fill=12,width=2);wd.line((26,4,26,14),fill=12,width=2);wd.rectangle((3,2,28,5),fill=11)
    sprites={'Well':well,'Glyph':Image.open(source/'graphics/pokemon/unown/icon.png').crop((0,0,32,32)),
             'CoinChest':Image.open(source/'graphics/pokemon/gimmighoul/icon.png').crop((0,0,32,32))}
    for index,(name,icon) in enumerate(sprites.items()):
        frames=Image.new('P',(32,288));frames.putpalette(icon.getpalette());frames.info['transparency']=0
        for frame in range(9):frames.paste(icon,(0,frame*32))
        buf=io.BytesIO();frames.save(buf,format='PNG');path='graphics/object_events/pics/misc/journey_'+name.lower()+'.png';layer.stage(path,buf.getvalue())
        append('include/constants/event_objects.h','\n#define OBJ_EVENT_PAL_TAG_JOURNEY_'+name.upper()+' '+hex(0x1520+index)+'\n')
        edit('include/constants/event_objects.h','    NUM_OBJ_EVENT_GFX,','    OBJ_EVENT_GFX_JOURNEY_'+name.upper()+',\n    NUM_OBJ_EVENT_GFX,')
        append('src/data/object_events/object_event_graphics.h','\nconst u32 gObjectEventPic_Journey'+name+'[]=INCBIN_U32("'+path.replace('.png','.4bpp')+'");\nconst u16 gObjectEventPal_Journey'+name+'[]=INCBIN_U16("'+path.replace('.png','.gbapal')+'");\n')
        append('src/data/object_events/object_event_pic_tables.h','\nstatic const struct SpriteFrameImage sPicTable_Journey'+name+'[]={overworld_ascending_frames(gObjectEventPic_Journey'+name+',4,4)};\n')
        append('src/data/object_events/object_event_graphics_info.h','\nconst struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_Journey'+name+'={.tileTag=TAG_NONE,.paletteTag=OBJ_EVENT_PAL_TAG_JOURNEY_'+name.upper()+',.reflectionPaletteTag=OBJ_EVENT_PAL_TAG_NONE,.size=512,.width=32,.height=32,.paletteSlot=10,.shadowSize=SHADOW_SIZE_M,.inanimate=TRUE,.compressed=FALSE,.tracks=TRACKS_FOOT,.oam=&gObjectEventBaseOam_32x32,.subspriteTables=sOamTables_32x32,.anims=sAnimTable_Standard,.images=sPicTable_Journey'+name+'};\n')
        p='src/data/object_events/object_event_graphics_info_pointers.h'
        layer.stage(p,'extern const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_Journey'+name+';\n'+read(p).decode())
        edit('src/data/object_events/object_event_graphics_info_pointers.h','const struct ObjectEventGraphicsInfo *const gObjectEventGraphicsInfoPointers[NUM_OBJ_EVENT_GFX] = {',
             'const struct ObjectEventGraphicsInfo *const gObjectEventGraphicsInfoPointers[NUM_OBJ_EVENT_GFX] = {\n [OBJ_EVENT_GFX_JOURNEY_'+name.upper()+']=&gObjectEventGraphicsInfo_Journey'+name+',')
        edit('src/event_object_movement.c','static const struct SpritePalette sObjectEventSpritePalettes[] = {',
             'static const struct SpritePalette sObjectEventSpritePalettes[] = {\n {gObjectEventPal_Journey'+name+',OBJ_EVENT_PAL_TAG_JOURNEY_'+name.upper()+'},')
    placed=[]
    for name,wanted,gfx,script in [(EVENTS[1][1],(16,47),'Well','JourneySpecial_SpiritombWell'),
        (EVENTS[2][1],(11,8),'Glyph','JourneySpecial_UnownGlyph'),(EVENTS[3][1],(6,5),'CoinChest','JourneySpecial_CoinChest')]:
        m=read_map(name);x,y=free_spot(m,wanted);npc(m,x,y,'OBJ_EVENT_GFX_JOURNEY_'+gfx.upper(),script);save_map(m)
        placed.append(dict(map=name,x=x,y=y,script=script))
    excavation=read_map('AlteringCave');x,y=free_spot(excavation,(5,6));npc(excavation,x,y,'OBJ_EVENT_GFX_HIKER','JourneySpecial_Excavation');save_map(excavation)
    placed.append(dict(map='AlteringCave',x=x,y=y,script='JourneySpecial_Excavation'))
    # Restore modern fossils through a new museum scientist. A compact paged
    # list is implemented in ordinary script menus, not a battle/stat shortcut.
    museum=read_map('PewterCity_Museum_1F_Frlg');x,y=free_spot(museum,(24,7));npc(museum,x,y,'OBJ_EVENT_GFX_SCIENTIST_1','JourneySpecial_FossilMenu');save_map(museum)
    placed.append(dict(map=museum['name'],x=x,y=y,script='JourneySpecial_FossilMenu'))
    layer.stage('data/layouts/layouts.json',json.dumps(layouts,indent=2)+'\n')
    groups=json.loads(read('data/maps/map_groups.json'));groups[groups['group_order'][-1]].append(room['name']);layer.stage('data/maps/map_groups.json',json.dumps(groups,indent=2)+'\n')
    append('include/constants/flags.h','\n#define FLAG_JOURNEY_SPIRITOMB_KEYSTONE 0x1B3A\n#define FLAG_JOURNEY_EXCAVATION_RELICS 0x1B3B\n')

    meta=json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text())
    species={int(sid):r for sid,r in meta['species'].items()};names={r['name']:sid for sid,r in species.items()}
    ecology=json.loads(read('.journey-five-island-habitat'))
    event_names=['SPECIES_'+r[0] for r in EVENTS]+['SPECIES_'+r[0] for r in FOSSILS]
    event_roots={names[n] for n in event_names}
    families={f['root']:f for h in ecology['locations_data'] for f in h['families'] if f['root'] in event_roots}
    assert len(families)==len(event_roots)==21
    event_dex={m['national_dex'] for f in families.values() for m in f['species']}
    all_members={sid for sid,row in species.items() if row['national_dex'] in event_dex}
    removed_maps=set()
    for h in ecology['locations_data']:
        old=h['families'];h['families']=[f for f in old if f['root'] not in event_roots];h['family_count']=len(h['families'])
        if len(old)!=len(h['families']):removed_maps.update(h['maps'])
    for pool in ecology['pools']:
        if pool['map'] not in removed_maps:continue
        remaining=[r for r in pool['roots'] if r not in event_roots]
        if remaining:
            # Retain each remaining family's original relative weight, then
            # fill emptied slots cyclically without importing another habitat.
            pool['roots']=[r if r not in event_roots else remaining[i%len(remaining)] for i,r in enumerate(pool['roots'])]
        else:pool['roots']=[]
    for map_id,ids in ecology['map_species'].items():ecology['map_species'][map_id]=[sid for sid in ids if sid not in all_members]
    encounters=json.loads(read('src/data/wild_encounters.json'));rows=encounters['wild_encounter_groups'][0]['encounters']
    pools={(p['map'],p['area']):p for p in ecology['pools']}
    fields=['land_mons','water_mons','rock_smash_mons','fishing_mons','hidden_mons']
    for row in rows:
        if row['map'] not in removed_maps:continue
        for area,field in enumerate(fields):
            if field not in row:continue
            kept=[mon['species'] for mon in row[field]['mons'] if mon['species'] not in event_names and names.get(mon['species']) not in all_members]
            for i,mon in enumerate(row[field]['mons']):
                if names.get(mon['species']) in all_members:mon['species']=kept[i%len(kept)] if kept else 'SPECIES_NONE'
    for header in ['include/journey_wild_data.h','include/journey_generation4_pools.h']:
        text=read(header).decode()
        pattern=r'^\{(MAP_\w+),(\s*\d+),(\s*\d+),\{([^}]*)\}\}(,?)$'
        def clean_pool(match):
            moves=[m.strip() for m in match[4].split(',') if m.strip()];remaining=[m for m in moves if names.get(m) not in event_roots]
            if not remaining:return '{'+match[1]+','+match[2]+',0,{}}'+match[5]
            values=[m if names.get(m) not in event_roots else remaining[i%len(remaining)] for i,m in enumerate(moves)]
            return '{'+match[1]+','+match[2]+','+str(len(values))+',{'+','.join(values)+'}}'+match[5]
        text=re.sub(pattern,clean_pool,text,flags=re.M)
        layer.stage(header,text)
    for header in ['include/journey_habitat_data.h','include/journey_generation4_habitats.h']:
        text=read(header).decode()
        pattern=r'^\{(MAP_\w+),\s*\d+,\s*\{([^}]*)\}\}(,?)$'
        def clean_dex(match):
            kept=[m.strip() for m in match[2].split(',') if m.strip() and names.get(m.strip()) not in all_members]
            return '{'+match[1]+','+str(len(kept))+',{'+','.join(kept)+'}}'+match[3]
        layer.stage(header,re.sub(pattern,clean_dex,text,flags=re.M))
    destinations=[(names['SPECIES_'+name],read_map(map_name)['id'],method) for name,map_name,method in EVENTS]
    destinations += [(names['SPECIES_'+name],museum['id'],'Revive with '+item+(' + '+other if other else '')) for name,item,other in FOSSILS]
    event_table=[]
    for sid,map_id,method in destinations:
        dexids=sorted({m['national_dex'] for m in families[sid]['species']})
        for dex in dexids:event_table.append('{'+str(dex)+','+map_id+'}')
        # The Pokédex's native area scanner enumerates wild headers. The dummy
        # table is disabled by a zero-size pool and cannot spawn a random mon.
        if not any(e['map']==map_id for e in rows):
            dummy=copy.deepcopy(next(e for e in rows if e['map']=='MAP_ROUTE101'))
            dummy={k:v for k,v in dummy.items() if k in ('map','base_label','land_mons')};dummy['map']=map_id;dummy['base_label']=map_id.replace('MAP_','gJourneyEvent')
            for mon in dummy['land_mons']['mons']:mon['species']='SPECIES_NONE'
            rows.append(dummy)
    layer.stage('src/data/wild_encounters.json',json.dumps(encounters,indent=2)+'\n')
    family_dex=','.join(str(d) for d in sorted(event_dex))
    layer.stage('src/data/journey_event_habitats.h','static const u16 sJourneyEventDex[]={'+family_dex+'};\nstruct JourneyEventHabitat {u16 dex,map;};\nstatic const struct JourneyEventHabitat sJourneyEventHabitats[]={'+','.join(event_table)+'};\n')
    p='src/journey_habitats.c';text=read(p).decode();text=text.replace('#include "journey_generation4_habitats.h"','#include "journey_generation4_habitats.h"\n#include "data/journey_event_habitats.h"\n#include "pokemon.h"')
    anchor='    u32 i, j;';assert text.count(anchor)==1
    text=text.replace(anchor,anchor+'\n    u32 dex=SpeciesToNationalPokedexNum(species);\n    for(i=0;i<ARRAY_COUNT(sJourneyEventDex);i++)if(dex==sJourneyEventDex[i])\n    {\n        if(!JourneySpeciesAllowed(species))return FALSE;\n        for(j=0;j<ARRAY_COUNT(sJourneyEventHabitats);j++)\n            if(dex==sJourneyEventHabitats[j].dex && group==MAP_GROUP(sJourneyEventHabitats[j].map) && map==MAP_NUM(sJourneyEventHabitats[j].map))return TRUE;\n        return FALSE;\n    }')
    layer.stage(p,text)
    # Every mode's pool is cleaned, and the runtime guard covers forms, fishing,
    # outbreaks and direct calls that use an older source-species slot.
    p='src/journey_wild.c';text=read(p).decode();anchor='    u32 selected=original,phase=JourneyWildPhase(),stage;'
    assert text.count(anchor)==1
    text=text.replace(anchor,'    static const u16 eventDex[]={'+family_dex+'};\n'+anchor)
    anchor='    const struct JourneyWildStages *family=&sJourneyWildStages[selected];'
    text=text.replace(anchor,'    for(u32 event=0;event<ARRAY_COUNT(eventDex);event++)\n        if(SpeciesToNationalPokedexNum(selected)==eventDex[event])return SPECIES_NONE;\n'+anchor)
    layer.stage(p,text)

    layer.stage('src/journey_event_encounters.c',native_code())
    append('data/scripts.inc','\n\t.include "data/scripts/journey_event_encounters.inc"\n')
    layer.stage('data/scripts/journey_event_encounters.inc',event_scripts())
    # Reuse the native Rotom catalog's full animation, move replacement prompt,
    # stats calculation and reversible form logic, opening it from the room.
    append('src/party_menu.c','''
static EWRAM_DATA u16 sJourneyWorkshopFormItem;
static void Task_JourneyRotomWorkshop(u8 taskId)
{
    if (!gPaletteFade.active)
    {
        CleanupOverworldWindowsAndTilemaps();
        gSpecialVar_ItemId = sJourneyWorkshopFormItem;
        gItemUseCB = sJourneyWorkshopFormItem == ITEM_ROTOM_CATALOG ? ItemUseCB_RotomCatalog : ItemUseCB_FormChange;
        InitPartyMenu(PARTY_MENU_TYPE_FIELD, PARTY_LAYOUT_SINGLE, PARTY_ACTION_USE_ITEM, FALSE,
            PARTY_MSG_CHOOSE_MON, Task_HandleChooseMonInput, CB2_ReturnToField);
        DestroyTask(taskId);
    }
}
void JourneyOpenRotomWorkshop(void)
{
    sJourneyWorkshopFormItem = ITEM_ROTOM_CATALOG;
    LockPlayerFieldControls();
    gFieldCallback2 = CB2_FadeFromPartyMenu;
    FadeScreen(FADE_TO_BLACK, 0);
    CreateTask(Task_JourneyRotomWorkshop, 10);
}
void JourneyOpenDeoxysMeteorite(void)
{
    sJourneyWorkshopFormItem = ITEM_METEORITE;
    LockPlayerFieldControls();
    gFieldCallback2 = CB2_FadeFromPartyMenu;
    FadeScreen(FADE_TO_BLACK, 0);
    CreateTask(Task_JourneyRotomWorkshop, 10);
}
''')
    return layer.finish(locations_data=ecology['locations_data'],map_species=ecology['map_species'],pools=ecology['pools'],
        field_slots=ecology['field_slots'],event_families=[families[root] for root in sorted(event_roots)],
        event_only_families=21,random_families=444-21,random_removed_maps=sorted(removed_maps),
        destinations=[dict(root=sid,map=map_id,method=method) for sid,map_id,method in destinations],
        placed_objects=placed,appliance_stations=stations,workshop_entry=dict(map=tower['name'],x=entry[0],y=entry[1]),
        all_modes_cleaned=True,rotom_only_base_is_capturable=True,original_story_gifts_preserved=True,
        artifacts_and_origin_orbs_story_rewards_preserved=True)

def native_code():
    fossils=',\n'.join('{SPECIES_'+name+',ITEM_'+item+','+('ITEM_'+other if other else 'ITEM_NONE')+'}' for name,item,other in FOSSILS)
    relics=sorted({item for _,item,other in FOSSILS for item in (item,other) if item})
    return '''#include "global.h"
#include "pokemon.h"
#include "pokedex.h"
#include "event_data.h"
#include "item.h"
#include "script_pokemon_util.h"
#include "journey_version.h"
#include "journey_wild.h"
#include "script_menu.h"
#include "malloc.h"
#include "string_util.h"
#include "constants/pokedex.h"
#include "constants/flags.h"
#include "constants/species.h"
#include "constants/items.h"
void JourneyFossilMenu(void)
{
    static const u16 species[]={'''+','.join('SPECIES_'+name for name,_,_ in FOSSILS)+'''};
    struct ListMenuItem *items=AllocZeroed(ARRAY_COUNT(species)*sizeof(*items));
    u32 count=0;
    for(u32 i=0;i<ARRAY_COUNT(species);i++)
    {
        if(!JourneySpeciesAllowed(species[i]))continue;
        u8 *label=AllocZeroed(POKEMON_NAME_LENGTH+1);
        StringCopy(label,GetSpeciesName(species[i]));
        items[count].name=label;items[count++].id=i;
    }
    ScriptMenu_MultichoiceDynamic(1,1,count,items,FALSE,6,0,DYN_MULTICHOICE_CB_NONE);
}
void JourneyEventEncounterReady(void)
{
    static const u16 species[]={SPECIES_ROTOM,SPECIES_SPIRITOMB,SPECIES_UNOWN,SPECIES_GIMMIGHOUL_CHEST};
    u32 index=gSpecialVar_0x8004;
    gSpecialVar_Result=3;
    if(index>=ARRAY_COUNT(species) || !JourneySpeciesAllowed(species[index]))return;
    if(index!=2 && GetSetPokedexFlag(SpeciesToNationalPokedexNum(species[index]),FLAG_GET_CAUGHT))
    {gSpecialVar_Result=2;return;}
    if(index==1 && !FlagGet(FLAG_JOURNEY_SPIRITOMB_KEYSTONE))
    {
        if(!CheckBagHasItem(ITEM_ODD_KEYSTONE,1)){gSpecialVar_Result=0;return;}
        RemoveBagItem(ITEM_ODD_KEYSTONE,1);FlagSet(FLAG_JOURNEY_SPIRITOMB_KEYSTONE);
    }
    gSpecialVar_Result=1;
}
void JourneyGiveFormTools(void)
{
    static const u16 items[]={'''+','.join('ITEM_'+name for name in FORM_TOOLS)+'''};
    for(u32 i=0;i<ARRAY_COUNT(items);i++)if(!CheckBagHasItem(items[i],1))AddBagItem(items[i],1);
}
void JourneyGiveExcavationRelics(void)
{
    static const u16 fossils[]={'''+','.join('ITEM_'+name for name in relics)+'''};
    if(!FlagGet(FLAG_JOURNEY_EXCAVATION_RELICS))
    {
        for(u32 i=0;i<ARRAY_COUNT(fossils);i++)AddBagItem(fossils[i],fossils[i]>=ITEM_FOSSILIZED_BIRD && fossils[i]<=ITEM_FOSSILIZED_DINO?2:1);
        FlagSet(FLAG_JOURNEY_EXCAVATION_RELICS);
    }
    if(!FlagGet(FLAG_JOURNEY_SPIRITOMB_KEYSTONE) && !CheckBagHasItem(ITEM_ODD_KEYSTONE,1))AddBagItem(ITEM_ODD_KEYSTONE,1);
}
void JourneyReviveModernFossil(void)
{
    static const struct {u16 species,item,second;} fossils[]={'''+fossils+'''};
    u32 index=gSpecialVar_0x8004;
    gSpecialVar_Result=3;
    if(index>=ARRAY_COUNT(fossils) || !JourneySpeciesAllowed(fossils[index].species))return;
    gSpecialVar_Result=0;
    if(!CheckBagHasItem(fossils[index].item,1) || (fossils[index].second && !CheckBagHasItem(fossils[index].second,1)))return;
    u32 result=ScriptGiveMon(fossils[index].species,JourneyWildLevel(),ITEM_NONE);
    if(result==MON_CANT_GIVE){gSpecialVar_Result=2;return;}
    RemoveBagItem(fossils[index].item,1);
    if(fossils[index].second)RemoveBagItem(fossils[index].second,1);
    gSpecialVar_Result=1;
}
'''

def event_scripts():
    text=''
    for index,(label,species,prompt) in enumerate([
        ('RotomTV','ROTOM','The television hisses with static.\nSomething is moving inside...'),
        ('SpiritombWell','SPIRITOMB','An old well. A hollow in its rim\nfits an ODD KEYSTONE.'),
        ('UnownGlyph','UNOWN','The ancient letters begin to glow.'),
        ('CoinChest','GIMMIGHOUL_CHEST','A weathered chest jingles with coins.')]):
        text+=f'''JourneySpecial_{label}::
\tlockall
\tmsgbox JourneySpecial_{label}_Text, MSGBOX_DEFAULT
\tsetvar VAR_0x8004, {index}
\tcallnative JourneyEventEncounterReady
\tgoto_if_eq VAR_RESULT, 0, JourneySpecial_NeedKeystone
\tgoto_if_eq VAR_RESULT, 2, JourneySpecial_Quiet
\tgoto_if_eq VAR_RESULT, 3, JourneySpecial_Empty
\tsetwildbattle SPECIES_{species}, 5
\tdowildbattle
\treleaseall
\tend
JourneySpecial_{label}_Text:
\t.string "{prompt.replace(chr(10),chr(92)+'n')}$"
'''
    text+='''JourneySpecial_Appliances::
\tlockall
\tmsgbox JourneySpecial_Appliances_Text, MSGBOX_DEFAULT
\tcallnative JourneyOpenRotomWorkshop
\twaitstate
\treleaseall
\tend
JourneySpecial_FormTools::
\tlock
\tfaceplayer
\tcallnative JourneyGiveFormTools
\tmsgbox JourneySpecial_FormTools_Text, MSGBOX_DEFAULT
\trelease
\tend
JourneySpecial_DeoxysMeteorite::
\tlockall
\tmsgbox JourneySpecial_DeoxysMeteorite_Text, MSGBOX_DEFAULT
\tcallnative JourneyOpenDeoxysMeteorite
\twaitstate
\treleaseall
\tend
JourneySpecial_DeoxysMeteorite_Text:
\t.string "This meteorite changes DEOXYS' form.\nChoose DEOXYS to cycle its forms.$"
JourneySpecial_WorkshopGuide::
\tmsgbox JourneySpecial_WorkshopGuide_Text, MSGBOX_NPC
\tend
JourneySpecial_Excavation::
\tlock
\tfaceplayer
\tcallnative JourneyGiveExcavationRelics
\tmsgbox JourneySpecial_Excavation_Text, MSGBOX_DEFAULT
\trelease
\tend
JourneySpecial_NeedKeystone:
\tmsgbox JourneySpecial_NeedKeystone_Text, MSGBOX_DEFAULT
\treleaseall
\tend
JourneySpecial_Quiet:
\tmsgbox JourneySpecial_Quiet_Text, MSGBOX_DEFAULT
\treleaseall
\tend
JourneySpecial_Empty:
\tmsgbox JourneySpecial_Empty_Text, MSGBOX_DEFAULT
\treleaseall
\tend
JourneySpecial_Appliances_Text:
\t.string "Choose ROTOM, then the appliance it\nshould enter. Choose LIGHT BULB to\lreturn it to its original form.$"
JourneySpecial_FormTools_Text:
\t.string "Here are reusable form-changing tools.\nUse them on compatible POKéMON.\pThe fused partners must be in your\nparty. Some forms require daytime.$"
JourneySpecial_WorkshopGuide_Text:
\t.string "ROTOM hides in the television.\nIts appliance forms aren't wild.\pThe oven, washer, refrigerator, fan\nand mower change its type and move.\pI don't make Mega Stones or the\nGalactic story's Origin Orbs.$"
JourneySpecial_Excavation_Text:
\t.string "These fossils came from a deep dig.\nPewter Museum can revive them!\pThis ODD KEYSTONE belongs in the\nold well at Memorial Pillar, Sevii.$"
JourneySpecial_NeedKeystone_Text:
\t.string "Bring an ODD KEYSTONE. An explorer\nin Hoenn's Altering Cave has one.$"
JourneySpecial_Quiet_Text:
\t.string "The presence has gone.\nEverything is quiet now.$"
JourneySpecial_Empty_Text:
\t.string "Nothing is stirring here.$"
JourneySpecial_FossilMenu::
\tlock
\tfaceplayer
\tmsgbox JourneySpecial_FossilMenu_Text, MSGBOX_DEFAULT
'''
    # Use a native dynamically populated list; indexes map to frozen fossil rows.
    text+='\tcallnative JourneyFossilMenu\n\twaitstate\n\tgoto_if_eq VAR_RESULT, 127, JourneySpecial_FossilDone\n\tcopyvar VAR_0x8004, VAR_RESULT\n\tcallnative JourneyReviveModernFossil\n\tgoto_if_eq VAR_RESULT, 0, JourneySpecial_FossilMissing\n\tgoto_if_eq VAR_RESULT, 2, JourneySpecial_FossilFull\n\tgoto_if_eq VAR_RESULT, 3, JourneySpecial_FossilUnavailable\n\tmsgbox JourneySpecial_FossilSuccess_Text, MSGBOX_DEFAULT\n\tgoto JourneySpecial_FossilDone\n'
    for name,message in [('Missing','Bring the fossil, or both fragments.\nThe explorer in Altering Cave has some.'),('Full','Your party and PC are full.\nYour fossils have not been consumed.'),('Unavailable','This species is not available in\nthis edition.')]:
        text+=f'JourneySpecial_Fossil{name}:\n\tmsgbox JourneySpecial_Fossil{name}_Text, MSGBOX_DEFAULT\n\tgoto JourneySpecial_FossilDone\nJourneySpecial_Fossil{name}_Text:\n\t.string "{message.replace(chr(10),chr(92)+"n")}$"\n'
    text+='JourneySpecial_FossilDone:\n\trelease\n\tend\nJourneySpecial_FossilMenu_Text:\n\t.string "I can revive any compatible fossil.\nWhich species should I restore?$"\nJourneySpecial_FossilSuccess_Text:\n\t.string "The fossil has been restored!\nYour POKéMON is in your party or PC.$"\n'
    # C-style backslash escapes in the script are data, never Python newlines
    # inside a quoted assembler string.
    return re.sub(r'(\.string ")([^"]*)(")',lambda m:m[1]+m[2].replace('\n','\\n')+m[3],text)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
