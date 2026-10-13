"""Complete all PWT walking identities and build a dedicated tournament stadium."""
import argparse,hashlib,io,json,struct
from pathlib import Path
from PIL import Image
from candidate_layer import Layer
from prepare_pwt_builds import PRIOR,LAYER as PREVIOUS
from pwt_catalog import load
HERE=Path(__file__).resolve().parent
LAYER='pwt-stadium';PRIOR=PRIOR+[PREVIOUS]

def encode_arena(layer):
    art=Image.open(HERE/'data/pwt/generated/arena-source.png').convert('RGB')
    # Technical reduction of the authored map into the native 320x160 canvas.
    image=art.resize((320,160),Image.Resampling.NEAREST).quantize(colors=15,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    palette=[0,0,0]+image.getpalette()[:45]
    palette+=[0]*(768-len(palette))
    pixels=[v+1 for v in image.get_flattened_data()]
    tiles=[bytes(64)];lookup={tiles[0]:0};tile_ids=[]
    for y in range(0,160,8):
        for x in range(0,320,8):
            raw=bytes(pixels[(y+dy)*320+x+dx] for dy in range(8) for dx in range(8))
            if raw not in lookup:lookup[raw]=len(tiles);tiles.append(raw)
            tile_ids.append(lookup[raw])
    assert len(tiles)<=1024,len(tiles)
    for bank,name in [(0,'base'),(1,'rest')]:
        folder='data/tilesets/'+('primary/' if bank==0 else 'secondary/')+'journey_pwt_'+name
        sheet=Image.new('P',(128,256));sheet.putpalette(palette)
        for i,raw in enumerate(tiles[bank*512:(bank+1)*512]):
            tile=Image.frombytes('P',(8,8),raw);sheet.paste(tile,(i%16*8,i//16*8))
        data=io.BytesIO();sheet.save(data,format='PNG');layer.stage(folder+'/tiles.png',data.getvalue())
        colors=[tuple(palette[i:i+3]) for i in range(0,48,3)]
        pal='JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in colors)+'\n'
        for i in range(16):layer.stage(folder+f'/palettes/{i:02}.pal',pal)
        metas=[]
        if bank==0:
            for y in range(10):
                for x in range(20):
                    metas+=[tile_ids[(y*2+dy)*40+x*2+dx] for dy,dx in [(0,0),(0,1),(1,0),(1,1)]]+[0]*4
        else:metas=[0]*8
        layer.stage(folder+'/metatiles.bin',struct.pack('<'+'H'*len(metas),*metas))
        layer.stage(folder+'/metatile_attributes.bin',bytes(2*(len(metas)//8)))
    return len(tiles)

def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    source=layer.source
    manifest=json.loads((HERE/'data/pwt/generated/sources.json').read_text());records=manifest['records']
    assert len(records)==79
    missing=set(json.loads((source/'.journey-pwt-entrances').read_text())['missing_walking_identities'])
    assert {r['name'] for r in records}==missing
    names=[r['key'] for r in records]
    for r in records:
        image=(HERE/'data/pwt/generated'/r['file']).read_bytes()
        assert hashlib.sha256(image).hexdigest()==r['converted_sha256']
        layer.stage('graphics/object_events/pics/people/journey_pwt_'+r['key'].lower()+'.png',image)
    p='include/constants/event_objects.h';t=(source/p).read_text();assert t.count('    NUM_OBJ_EVENT_GFX,')==1
    t=t.replace('    NUM_OBJ_EVENT_GFX,',''.join('    OBJ_EVENT_GFX_JOURNEY_PWT_'+n+',\n' for n in names)+'    NUM_OBJ_EVENT_GFX,')
    t+='\n'+''.join('#define OBJ_EVENT_PAL_TAG_JOURNEY_PWT_'+n+' '+hex(0x1480+i)+'\n' for i,n in enumerate(names));layer.stage(p,t)
    p='src/data/object_events/object_event_graphics.h';layer.stage(p,(source/p).read_text()+'\n'+''.join('const u32 gObjectEventPic_JourneyPWT'+n+'[] = INCBIN_U32("graphics/object_events/pics/people/journey_pwt_'+n.lower()+'.4bpp");\nconst u16 gObjectEventPal_JourneyPWT'+n+'[] = INCBIN_U16("graphics/object_events/pics/people/journey_pwt_'+n.lower()+'.gbapal");\n' for n in names))
    p='src/data/object_events/object_event_pic_tables.h';layer.stage(p,(source/p).read_text()+'\n'+''.join('static const struct SpriteFrameImage sPicTable_JourneyPWT'+n+'[] = { overworld_ascending_frames(gObjectEventPic_JourneyPWT'+n+', 4, 4) };\n' for n in names))
    p='src/data/object_events/object_event_graphics_info.h';layer.stage(p,(source/p).read_text()+'\n'+''.join('const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_JourneyPWT'+n+' = { .tileTag=TAG_NONE, .paletteTag=OBJ_EVENT_PAL_TAG_JOURNEY_PWT_'+n+', .reflectionPaletteTag=OBJ_EVENT_PAL_TAG_NONE, .size=512, .width=32, .height=32, .paletteSlot=10, .shadowSize=SHADOW_SIZE_M, .inanimate=FALSE, .compressed=FALSE, .tracks=TRACKS_FOOT, .oam=&gObjectEventBaseOam_32x32, .subspriteTables=sOamTables_32x32, .anims=sAnimTable_Standard, .images=sPicTable_JourneyPWT'+n+' };\n' for n in names))
    p='src/data/object_events/object_event_graphics_info_pointers.h';t=(source/p).read_text();t=''.join('extern const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_JourneyPWT'+n+';\n' for n in names)+t
    start=t.index('const struct ObjectEventGraphicsInfo *const gObjectEventGraphicsInfoPointers');end=t.index('};',start)
    layer.stage(p,t[:end]+''.join('    [OBJ_EVENT_GFX_JOURNEY_PWT_'+n+'] = &gObjectEventGraphicsInfo_JourneyPWT'+n+',\n' for n in names)+t[end:])
    p='src/event_object_movement.c';t=(source/p).read_text();needle='static const struct SpritePalette sObjectEventSpritePalettes[] = {';assert t.count(needle)==1
    layer.stage(p,t.replace(needle,needle+'\n'+''.join('    {gObjectEventPal_JourneyPWT'+n+', OBJ_EVENT_PAL_TAG_JOURNEY_PWT_'+n+'},\n' for n in names)))
    layer.stage('src/data/journey_pwt_walking.h','static const u16 sPWTWalking[] = {\n'+''.join('    OBJ_EVENT_GFX_JOURNEY_PWT_'+r['key']+',\n' for r in load())+'};\n')
    p='src/journey_pwt_entrance.c';t=(source/p).read_text()
    t=t.replace('    u8 event=SpawnSpecialObjectEventParameterized','    TryMoveObjectEventToMapCoords(LOCALID_PLAYER,gSaveBlock1Ptr->location.mapNum,gSaveBlock1Ptr->location.mapGroup,2,6);\n    u8 event=SpawnSpecialObjectEventParameterized')
    layer.stage(p,t)
    p='data/scripts/journey_pwt.inc';t=(source/p).read_text()
    t=t.replace('JourneyPWT_NextRound::\n\tspecial JourneyPWTEntrance','JourneyPWT_NextRound::\n\tfadescreen FADE_TO_BLACK\n\tspecial JourneyPWTEntrance')
    t=t.replace('\tapplymovement 14, JourneyPWT_EntranceMovement','\tfadescreen FADE_FROM_BLACK\n\tapplymovement LOCALID_PLAYER, JourneyPWT_PlayerEntranceMovement\n\tapplymovement 14, JourneyPWT_EntranceMovement')
    t+='\nJourneyPWT_PlayerEntranceMovement:\n'+ '\twalk_right\n'*7+'\tstep_end\n'
    layer.stage(p,t)
    tiles=encode_arena(layer)
    p='src/data/tilesets/graphics.h';t=(source/p).read_text()
    pmeta='src/data/tilesets/metatiles.h';meta=(source/pmeta).read_text()
    pheader='src/data/tilesets/headers.h';header=(source/pheader).read_text()
    for name,secondary in [('Base',False),('Rest',True)]:
        folder='data/tilesets/'+('secondary/' if secondary else 'primary/')+'journey_pwt_'+name.lower()
        t+='\nconst u32 gTilesetTiles_JourneyPWT'+name+'[] = INCBIN_U32("'+folder+'/tiles.4bpp.lz");\nconst u16 gTilesetPalettes_JourneyPWT'+name+'[][16] = {\n'+''.join(' INCBIN_U16("'+folder+f'/palettes/{i:02}.gbapal"),\n' for i in range(16))+'};\n'
        meta+='\nconst u16 gMetatiles_JourneyPWT'+name+'[] = INCBIN_U16("'+folder+'/metatiles.bin");\nconst u16 gMetatileAttributes_JourneyPWT'+name+'[] = INCBIN_U16("'+folder+'/metatile_attributes.bin");\n'
        header+='\nconst struct Tileset gTileset_JourneyPWT'+name+'={.isCompressed=TRUE,.isSecondary='+('TRUE' if secondary else 'FALSE')+',.tiles=gTilesetTiles_JourneyPWT'+name+',.palettes=gTilesetPalettes_JourneyPWT'+name+',.metatiles=gMetatiles_JourneyPWT'+name+',.metatileAttributes=gMetatileAttributes_JourneyPWT'+name+',.callback=NULL};\n'
    layer.stage(p,t);layer.stage(pmeta,meta);layer.stage(pheader,header)
    p='data/layouts/layouts.json';layouts=json.loads((source/p).read_text())
    layouts['layouts'].append(dict(id='LAYOUT_JOURNEY_PWT_STADIUM',name='JourneyPWTStadium_Layout',width=20,height=10,
        primary_tileset='gTileset_JourneyPWTBase',secondary_tileset='gTileset_JourneyPWTRest',
        border_filepath='data/layouts/JourneyPWTStadium/border.bin',blockdata_filepath='data/layouts/JourneyPWTStadium/map.bin',layout_version='emerald'))
    layer.stage(p,json.dumps(layouts,indent=2)+'\n')
    blocks=[]
    for y in range(10):
        for x in range(20):
            blocked=x in (0,19) or y in (0,1,2,3,9) or (y in (4,8) and x in (2,3,16,17))
            blocks.append(0x3000 | (0xC00 if blocked else 0) | (y*20+x))
    layer.stage('data/layouts/JourneyPWTStadium/map.bin',struct.pack('<'+'H'*len(blocks),*blocks))
    layer.stage('data/layouts/JourneyPWTStadium/border.bin',struct.pack('<4H',0x3C00,0x3C13,0x3CB4,0x3CC7))
    p='data/maps/JourneyPWTArena/map.json';m=json.loads((source/p).read_text());m['layout']='LAYOUT_JOURNEY_PWT_STADIUM';m['battle_scene']='MAP_BATTLE_SCENE_FRONTIER'
    m['object_events'][0].update(x=10,y=3)
    layer.stage(p,json.dumps(m,indent=2)+'\n')
    return layer.finish(all_162_walking_identities_registered=True,generated_walking_identities=names,
        walking_frames_per_identity=9,arena_tiles=tiles,arena_dimensions=[20,10],
        arena_is_dedicated=True,original_battle_dome_preserved=True,opposing_side_entrances=True,
        source_art_sha256=hashlib.sha256((HERE/'data/pwt/generated/arena-source.png').read_bytes()).hexdigest(),
        published_roms_updated=False)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
