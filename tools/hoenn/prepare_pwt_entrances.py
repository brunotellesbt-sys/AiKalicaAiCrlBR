"""Add sourced animated PWT entrants; missing modern walking art stays explicit."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image
from candidate_layer import Layer
from prepare_pwt_world_cup import PRIOR,LAYER as PREVIOUS
from pwt_catalog import load
from pack_crossover_assets import fit,indexed
HERE=Path(__file__).resolve().parent
LAYER='pwt-entrances';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    source=layer.source;rows=load();assets=HERE/'data/pwt/walking'
    references={r['key']:r for r in json.loads((assets/'sources.json').read_text())['walking']}
    packed={}
    for row in rows:
        ref=references[row['key']]
        if ref['status']=='acquired':
            data=(assets/ref['converted']).read_bytes()
            assert hashlib.sha256(data).hexdigest()==ref['converted_sha256']
            packed[row['key']]=data
    for key in ('EREN','LUFFY'):
        packed[key]=(source/('graphics/object_events/pics/people/journey_'+key.lower()+'.png')).read_bytes()
    for key in ('BRENDAN','MAY'):
        image=Image.open(source/('graphics/object_events/pics/people/'+key.lower()+'/walking.png')).convert('RGBA')
        assert image.size==(144,32)
        canvas=Image.new('RGBA',(16,288))
        for frame in range(9):canvas.alpha_composite(fit(image.crop((frame*16,0,(frame+1)*16,32)),16,32),(0,frame*32))
        import io
        buffer=io.BytesIO();indexed(canvas).save(buffer,format='PNG');packed[key]=buffer.getvalue()
    for key,data in packed.items():layer.stage('graphics/object_events/pics/people/journey_pwt_'+key.lower()+'.png',data)
    names=list(packed)
    p='include/constants/event_objects.h';t=(source/p).read_text();assert t.count('    NUM_OBJ_EVENT_GFX,')==1
    t=t.replace('    NUM_OBJ_EVENT_GFX,',''.join('    OBJ_EVENT_GFX_JOURNEY_PWT_'+n+',\n' for n in names)+'    NUM_OBJ_EVENT_GFX,')
    t+='\n'+''.join('#define OBJ_EVENT_PAL_TAG_JOURNEY_PWT_'+n+' '+hex(0x1400+i)+'\n' for i,n in enumerate(names))
    layer.stage(p,t)
    p='src/data/object_events/object_event_graphics.h';layer.stage(p,(source/p).read_text()+'\n'+''.join('const u32 gObjectEventPic_JourneyPWT'+n+'[] = INCBIN_U32("graphics/object_events/pics/people/journey_pwt_'+n.lower()+'.4bpp");\nconst u16 gObjectEventPal_JourneyPWT'+n+'[] = INCBIN_U16("graphics/object_events/pics/people/journey_pwt_'+n.lower()+'.gbapal");\n' for n in names))
    p='src/data/object_events/object_event_pic_tables.h';layer.stage(p,(source/p).read_text()+'\n'+''.join('static const struct SpriteFrameImage sPicTable_JourneyPWT'+n+'[] = { overworld_ascending_frames(gObjectEventPic_JourneyPWT'+n+', 2, 4) };\n' for n in names))
    p='src/data/object_events/object_event_graphics_info.h';layer.stage(p,(source/p).read_text()+'\n'+''.join('const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_JourneyPWT'+n+' = { .tileTag=TAG_NONE, .paletteTag=OBJ_EVENT_PAL_TAG_JOURNEY_PWT_'+n+', .reflectionPaletteTag=OBJ_EVENT_PAL_TAG_NONE, .size=256, .width=16, .height=32, .paletteSlot=10, .shadowSize=SHADOW_SIZE_M, .inanimate=FALSE, .compressed=FALSE, .tracks=TRACKS_FOOT, .oam=&gObjectEventBaseOam_16x32, .subspriteTables=sOamTables_16x32, .anims=sAnimTable_Standard, .images=sPicTable_JourneyPWT'+n+' };\n' for n in names))
    p='src/data/object_events/object_event_graphics_info_pointers.h';t=(source/p).read_text();t=''.join('extern const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_JourneyPWT'+n+';\n' for n in names)+t;start=t.index('const struct ObjectEventGraphicsInfo *const gObjectEventGraphicsInfoPointers');end=t.index('};',start)
    layer.stage(p,t[:end]+''.join('    [OBJ_EVENT_GFX_JOURNEY_PWT_'+n+'] = &gObjectEventGraphicsInfo_JourneyPWT'+n+',\n' for n in names)+t[end:])
    p='src/event_object_movement.c';t=(source/p).read_text();needle='static const struct SpritePalette sObjectEventSpritePalettes[] = {';assert t.count(needle)==1
    layer.stage(p,t.replace(needle,needle+'\n'+''.join('    {gObjectEventPal_JourneyPWT'+n+', OBJ_EVENT_PAL_TAG_JOURNEY_PWT_'+n+'},\n' for n in names)))
    layer.stage('src/data/journey_pwt_walking.h','static const u16 sPWTWalking[] = {\n'+''.join('    '+('OBJ_EVENT_GFX_JOURNEY_PWT_'+r['key'] if r['key'] in packed else '0xFFFF')+',\n' for r in rows)+'};\n')
    layer.stage('src/journey_pwt_entrance.c',(HERE/'pwt_entrance.c').read_bytes())
    p='include/journey_pwt.h';t=(source/p).read_text();layer.stage(p,t.replace('#endif','void JourneyPWTEntrance(void);\nvoid JourneyPWTExit(void);\nbool32 JourneyPWTWalkingAvailable(u32);\n#endif'))
    p='data/specials.inc';layer.stage(p,(source/p).read_text()+'\n\tdef_special JourneyPWTEntrance\n\tdef_special JourneyPWTExit\n')
    p='data/scripts/journey_pwt.inc';t=(source/p).read_text()
    t=t.replace('JourneyPWT_NextRound::\n','JourneyPWT_NextRound::\n\tspecial JourneyPWTEntrance\n\tgoto_if_eq VAR_RESULT, FALSE, JourneyPWT_BoardStart\n\tapplymovement 14, JourneyPWT_EntranceMovement\n\twaitmovement 0\nJourneyPWT_BoardStart::\n')
    t=t.replace('\tspecial JourneyPWTAdvance','\tspecial JourneyPWTExit\n\tspecial JourneyPWTAdvance')
    t+='\nJourneyPWT_EntranceMovement:\n\twalk_left\n\twalk_left\n\twalk_left\n\twalk_left\n\tstep_end\n'
    layer.stage(p,t)
    # Sketch gives Smeargle a legal support build; otherwise the generic
    # level-up picker produces four empty move slots for this participant.
    p='src/journey_competitive.c';t=(source/p).read_text()
    anchor='    if(move==MOVE_NONE || move==MOVE_UNAVAILABLE)return FALSE;'
    assert t.count(anchor)==1
    t=t.replace(anchor,anchor+'\n    if(species==SPECIES_SMEARGLE && (move==MOVE_SPORE || move==MOVE_STICKY_WEB || move==MOVE_STEALTH_ROCK || move==MOVE_NUZZLE))return TRUE;')
    anchor='    if(HasMove(mon,MOVE_RETURN))mon->friendship=255;'
    assert t.count(anchor)==1
    special='''    if(mon->species==SPECIES_SMEARGLE)
    {
        static const u8 evs[]={252,0,6,0,0,252};
        mon->moves[0]=MOVE_SPORE;mon->moves[1]=MOVE_STICKY_WEB;
        mon->moves[2]=MOVE_STEALTH_ROCK;mon->moves[3]=MOVE_NUZZLE;
        mon->heldItem=ITEM_FOCUS_SASH;mon->ev=evs;mon->nature=NATURE_JOLLY;
        mon->ability=ABILITY_OWN_TEMPO;
    }
'''
    layer.stage(p,t.replace(anchor,special+anchor))
    return layer.finish(animated_identities=names,walking_sprites_count=len(names),
        missing_walking_identities=[r['name'] for r in rows if r['key'] not in packed],
        campaign_shared_gym_battles_unchanged=True,original_battle_dome_arena_preserved=True,
        presentation_complete=False,smeargle_sketch_support_build=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
