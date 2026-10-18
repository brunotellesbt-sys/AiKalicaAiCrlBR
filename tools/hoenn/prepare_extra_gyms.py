"""Eight additional gyms and a persistent 24-badge League requirement."""
import argparse
import copy
import json
import re
import struct
from pathlib import Path
from candidate_layer import Layer
from extra_gym_art import IndoorBank
from extra_gyms import GYMS, VALERIE, STUDENT_PROFILES
from import_native_pier import import_pier
from prepare_ever_grande_market import PRIOR, LAYER as PREVIOUS
from render_sea_maps import MapRenderer
LAYER = 'extra-gyms'
PRIOR = PRIOR+[PREVIOUS]
ROOT = Path(__file__).resolve().parents[2]


def prepare(source):
    layer = Layer(source, LAYER, PRIOR)
    if old := layer.existing(): return old
    s = layer.source; r = MapRenderer(s)
    def read(p): return layer.outputs.get(p, (s/p).read_bytes() if (s/p).exists() else b'')
    def load(n):
        m=json.loads(read(f'data/maps/{n}/map.json'));l=r.layouts[m['layout']]
        return m,l,list(struct.unpack('<'+'H'*(l['width']*l['height']),read(l['blockdata_filepath'])))
    def stagejson(p,x): layer.stage(p,json.dumps(x,indent=2)+'\n')
    groups=json.loads(read('data/maps/map_groups.json'));groups['group_order'].append('JourneyExtraGyms');groups['JourneyExtraGyms']=[]
    layouts=json.loads(read('data/layouts/layouts.json'))
    flags=read('include/constants/flags.h').decode()
    # All these flags fit the existing 872-byte flag array. The source validator
    # compiles every old FLAG macro and checks this allocation against aliases.
    for i,g in enumerate(GYMS):
        g=copy.deepcopy(g);g['badge_flag']=0x1040+i;g['tm_flag']=0x1048+i
    for i,g in enumerate(GYMS):
        flags+=f'\n#define FLAG_JOURNEY_BADGE_{g["key"]} 0x{0x1040+i:X}\n#define FLAG_JOURNEY_TM_{g["key"]} 0x{0x1048+i:X}\n'
    for i in range(41):flags+=f'#define FLAG_JOURNEY_GYM_TRAINER_{i} 0x{0x1000+i:X}\n'
    layer.stage('include/constants/flags.h',flags)
    opponents=read('include/constants/opponents.h').decode();assert '#define TRAINERS_COUNT                      1760' in opponents
    opponents=opponents.replace('#define TRAINERS_COUNT                      1760','#define TRAINERS_COUNT                      1801')
    leaders=GYMS+[VALERIE]
    for i,g in enumerate(leaders):opponents+=f'\n#define TRAINER_JOURNEY_GYM_{g["key"]} {1760+i}\n'
    for i in range(32):opponents+=f'#define TRAINER_JOURNEY_GYM_STUDENT_{i} {1769+i}\n'
    layer.stage('include/constants/opponents.h',opponents)
    text=read('src/battle_setup.c').decode();anchor='static u16 JourneyBeachTrainerFlag(u16 trainerId)\n{'
    assert text.count(anchor)==1
    text=text.replace(anchor,anchor+'\n    if (trainerId >= 1760 && trainerId < 1801)\n        return 0x1000 + trainerId - 1760;')
    layer.stage('src/battle_setup.c',text)
    # Append five TMs into reserved item IDs 56-60; every existing TM/HM
    # number, item ID and save slot keeps its previous meaning.
    moves=['DAZZLING_GLEAM','FLASH_CANNON','X_SCISSOR','DRAGON_PULSE','DARK_PULSE']
    tms=read('include/constants/tms_hms.h').decode()
    tail=tms.split('#define FOREACH_HM',1)[0].rstrip().splitlines()[-1]
    tms=tms.replace(tail+'\n',tail+' \\\n'+''.join('    F('+m+')'+(' \\\n' if j<4 else '\n') for j,m in enumerate(moves)),1)
    layer.stage('include/constants/tms_hms.h',tms)
    items=read('src/data/items.h').decode()
    for j,move in enumerate(moves):
        number=56+j
        record='''[ITEM_TM_'''+move+'''] =
    {
        .name = ITEM_NAME("TM'''+str(number)+'''"),
        .price = 10000,
        .description = COMPOUND_STRING("Teaches '''+move.replace('_',' ')+'''\\n to a compatible\\nPOKeMON."),
        .importance = I_REUSABLE_TMS,
        .pocket = POCKET_TM_HM,
        .type = ITEM_USE_PARTY_MENU,
        .fieldUseFunc = ItemUseOutOfBattle_TMHM,
    },'''
        pattern=r'\[ITEM_TM'+str(number)+r'\]\s*=\s*\{.*?\n    \},'
        items,count=re.subn(pattern,lambda m:record,items,count=1,flags=re.S)
        if not count:items=items.replace('\n};','\n    '+record+'\n};')
    layer.stage('src/data/items.h',items)
    trainer_data=[]
    def trainer(key,name,pic,gender,team,leader=True,trainer_class=None):
        party=','.join('{.species=SPECIES_'+family[-2 if isinstance(family[-1],int) else -1]+',.lvl='+str(45+i)+',.iv=TRAINER_PARTY_IVS(20,20,20,20,20,20),.gender=TRAINER_MON_RANDOM_GENDER,.ball=POKEBALL_COUNT,.nature=NATURE_HARDY,.heldItem=ITEM_SITRUS_BERRY}' for i,family in enumerate(team))
        trainer_data.append(f'[DIFFICULTY_NORMAL][{key}]={{.trainerName=_("{name}"),.trainerClass=TRAINER_CLASS_'+(trainer_class or ('LEADER' if leader else 'COOLTRAINER'))+f',.trainerPic={pic},.gender=TRAINER_GENDER_{gender},.encounterMusic=TRAINER_ENCOUNTER_MUSIC_'+('FEMALE' if gender=='FEMALE' else 'MALE')+f',.aiFlags=AI_FLAG_BASIC_TRAINER,.partySize={len(team)},.party=(const struct TrainerMon[]){{{party}}}}},\n')
    for g in leaders:
        pic='TRAINER_PIC_PROFESSOR_OAK_FRLG' if g['key']=='OAK' else 'TRAINER_PIC_JOURNEY_PWT_'+g['key']
        trainer('TRAINER_JOURNEY_GYM_'+g['key'],g['leader'],pic,g['gender'],g['team'])
    for i,g in enumerate(GYMS):
        for j,(kind,pic,gfx,gender) in enumerate(STUDENT_PROFILES[g['key']]):
            trainer('TRAINER_JOURNEY_GYM_STUDENT_'+str(i*4+j),['Ari','Remy','Noel','Sage','Mina','Kai','Yuki','Luca','Rin','Finn','Ren','Rae','Alex','Eden','Sam','Lee','Robin','Jules','Dani','Toni','River','Sky','Ash','Avery','Blair','Taylor','Chris','Jamie','Morgan','Casey','Pat','Kim'][i*4+j],'TRAINER_PIC_'+pic,gender,g['team'][1+j:3+j],False,kind)
    layer.stage('src/data/journey_extra_gym_trainers.h',''.join(trainer_data))
    text=read('src/data.c').decode().replace('#include "data/journey_crossover_trainers.h"','#include "data/journey_crossover_trainers.h"\n#include "data/journey_extra_gym_trainers.h"')
    layer.stage('src/data.c',text)
    headers=read('src/data/tilesets/headers.h').decode();graphics=read('src/data/tilesets/graphics.h').decode();metas=read('src/data/tilesets/metatiles.h').decode()
    scripts=[];records=[];door_entries=[]
    _,dl,donor=load('PetalburgCity');facade=[donor[y*dl['width']+x] for y in range(4,9) for x in range(12,18)]
    base,bl,hall=load('RustboroCity_Gym')
    for i,g in enumerate(GYMS):
        n=g['name'];city,cl,v=load(g['city']);original_city=copy.deepcopy(city)
        # Enlarge only empty boundary land. Existing map coordinates, NPCs,
        # story triggers, door indices and connection offsets remain stable.
        if g['key']=='MORTY':
            old=v[:];v=[];ow=cl['width'];cl=copy.deepcopy(cl);cl['width']=32
            for y in range(cl['height']):v.extend(old[y*ow:y*ow+22]+[0x3001]*8+old[y*ow+22:y*ow+24])
            for yy in range(18,20):
                for xx in range(22,30):v[yy*32+xx]=old[yy*ow+2+(xx-22)%8]
            r.layouts[cl['id']]=cl
        if g['key']=='BUGSY':
            old=v[:];cl=copy.deepcopy(cl);cl['height']=26
            v=old[:18*20]+[0x3279]*(8*20)
            for y in range(24,26):v[y*20:(y+1)*20]=old[(y-6)*20:(y-5)*20]
            # Move complete native ash-town trees, including their canopy/base.
            for y in range(18,24,2):
                for x in [0,18]:
                    for dy in range(2):
                        for dx in range(2):v[(y+dy)*20+x+dx]=old[(18+dy)*20+x+dx]
            r.layouts[cl['id']]=cl
        if g['key'] in ['CLAIR','KAREN']:
            # Retain the original whole western tree column. Clear complete
            # groups, including the canopy and the eastern tree at Six Island.
            x0,x1,y0,y1=(2,10,11,20) if g['key']=='CLAIR' else (0,7,13,20)
            for yy in range(y0,y1):
                for xx in range(x0,x1):v[yy*cl['width']+xx]=0x3001
        if g['position']:
            x,y=g['position'];cut=640 if cl['layout_version']=='frlg' else 512
            if cut==512 and g['key']!='BUGSY':ids={mid:mid for mid in set(a&1023 for a in facade)}
            else:
                used=set()
                for other in r.layouts.values():
                    if other['secondary_tileset']!=cl['secondary_tileset']:continue
                    for k in ['blockdata_filepath','border_filepath']:
                        raw=read(other[k]);used.update(a&1023 for a in struct.unpack('<'+'H'*(len(raw)//2),raw))
                words=r.tileset(cl['secondary_tileset'])[2]
                # Reserve new native metatile slots as well as unused existing
                # ones; do not evict any harbor/door/animation metatile.
                h=re.search(r'const struct Tileset '+cl['secondary_tileset']+r'\s*=\s*\{(.*?)\};',r.headers,re.S)[1]
                symbol=re.search(r'\.metatiles\s*=\s*(\w+)',h)[1]
                metapath=re.search(r'\b'+symbol+r'\[\].*?"([^"]+)"',r.metas)[1]
                attrsymbol=re.search(r'\.metatileAttributes\s*=\s*(\w+)',h)[1]
                attrpath=re.search(r'\b'+attrsymbol+r'\[\].*?"([^"]+)"',r.metas)[1]
                meta=read(metapath);attrs=read(attrpath)
                tilepath=str(Path(metapath).parent/'tiles.png')
                layer.stage(tilepath,read(tilepath))
                layer.stage(metapath,meta+bytes((1024-cut)*16-len(meta)))
                layer.stage(attrpath,attrs+bytes((1024-cut)*(2 if cut==512 else 4)-len(attrs)))
                available=[a for a in range(cut,1024) if a not in used]
                mids=sorted(set(a&1023 for a in facade))
                donor_palettes=None
                if g['key']=='BUGSY':
                    # Preserve the complete foundation, adapting only its
                    # embedded native grass colors to Fallarbor's ash soil.
                    grass,_=r.render('PetalburgCity',values=[0x3001],dimensions=(1,1),npcs=False)
                    soil,_=r.render('FallarborTown',values=[0x3279],dimensions=(1,1),npcs=False)
                    greens=sorted(set(grass.getdata()),key=sum);browns=sorted(set(soil.getdata()),key=sum)
                    convert={c:browns[round(j*(len(browns)-1)/max(1,len(greens)-1))] for j,c in enumerate(greens)}
                    gp=r.tileset('gTileset_General')[1];sp=r.tileset(dl['secondary_tileset'])[1]
                    donor_palettes={bank:[convert.get(c,c) for c in (gp if bank<6 else sp)[bank]] for bank in range(13)}
                ids,files=import_pier(s,cl['secondary_tileset'],emerald=cut==512,donor=dl['secondary_tileset'],donor_emerald=True,mids=mids,metatile_slots=available[:len(mids)],overrides=layer.outputs,donor_palettes=donor_palettes)
                for p,raw in files.items():layer.stage(p,raw)
                meta=next(raw for p,raw in files.items() if p.endswith('/metatiles.bin'))
                bank=struct.unpack_from('<H',meta,(ids[0x1CD]-cut)*16+8)[0]>>12
                door_entries.append(f'    {{{ids[0x1CD]}, &{cl["secondary_tileset"]}, DOOR_SOUND_NORMAL, 1, sDoorAnimTiles_Gym, sDoorAnimPalettes_JourneyGym{i}}},')
                door_entries[-1]=(f'static const u8 sDoorAnimPalettes_JourneyGym{i}[] = {{'+','.join([str(bank)]*8)+'};',door_entries[-1])
            cells={(x+xx,y+yy) for xx in range(6) for yy in range(5)}
            assert not any((o.get('x'),o.get('y')) in cells for k in ['object_events','warp_events','coord_events','bg_events'] for o in city.get(k,[])),n
            for a,value in enumerate(facade):v[(y+a//6)*cl['width']+x+a%6]=((value&0xFC00) if g['key']!='STEVEN' or value&0xC00 else 0x5000)|ids[value&1023]
            # Clear the small front apron with the city's native ground.
            ground=0x5001 if g['key']=='STEVEN' else 0x3279 if g['key']=='BUGSY' else 0x3001
            for xx in range(x,x+6):v[(y+5)*cl['width']+xx]=ground
            entry=[x+3,y+4];outside_warp=len(city['warp_events'])
            city['warp_events'].append(dict(x=entry[0],y=entry[1],elevation=0,dest_map='MAP_'+n.upper(),dest_warp_id='0'))
        else:
            entry=[11,6];outside_warp=len(city['warp_events'])
            assert v[6*cl['width']+11]&0xC00==0
            # The lab shares BuildingFrlg's original, working stair metatile.
            v[6*cl['width']+11]=0x301D
            city['warp_events'].append(dict(x=11,y=6,elevation=3,dest_map='MAP_'+n.upper(),dest_warp_id='0'))
        stagejson(f'data/maps/{g["city"]}/map.json',city)
        layer.stage(cl['blockdata_filepath'],struct.pack('<'+'H'*len(v),*v))
        for j,ll in enumerate(layouts['layouts']):
            if ll['id']==cl['id']:layouts['layouts'][j]=cl;break
        # Each room has its own native walls, proportions, complete props
        # and open sightlines; no generic Rustboro dais or puzzle terrain.
        from extra_gym_interiors import build as build_room
        bank=IndoorBank(r,g['key']);values,room=build_room(r,bank,g['key'])
        h,gr,mt=bank.stage(layer);headers+='\n'+h;graphics+='\n'+gr;metas+='\n'+mt
        lay=dict(id='LAYOUT_'+n.upper(),name=n+'_Layout',width=room['width'],height=room['height'],primary_tileset='gTileset_Building',secondary_tileset='gTileset_JourneyExtra'+g['key'],border_filepath=f'data/layouts/{n}/border.bin',blockdata_filepath=f'data/layouts/{n}/map.bin',layout_version='emerald')
        layouts['layouts'].append(lay);layer.stage(lay['blockdata_filepath'],struct.pack('<'+'H'*len(values),*values));layer.stage(lay['border_filepath'],struct.pack('<4H',*([0x400|bank.add('RustboroCity_Gym',1)]*4)))
        # Border metatile was added after stage; serialize the final bank again.
        h,gr,mt=bank.stage(layer)
        inside=copy.deepcopy(base);inside.update(id='MAP_'+n.upper(),name=n,layout=lay['id'],region=city.get('region','REGION_HOENN'),region_map_section=city['region_map_section'],allow_running=True)
        gfx='OBJ_EVENT_GFX_PROF_OAK' if g['key']=='OAK' else 'OBJ_EVENT_GFX_JOURNEY_PWT_'+g['key']
        if g['key']=='WHITNEY':gfx='OBJ_EVENT_GFX_VAR_0'
        def obj(graphic,x,y,script,trainer=False,facing='DOWN'):return dict(graphics_id=graphic,x=x,y=y,elevation=3,movement_type='MOVEMENT_TYPE_FACE_'+facing,movement_range_x=0,movement_range_y=0,trainer_type='TRAINER_TYPE_NORMAL' if trainer else 'TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='6' if trainer else '0',script=script,flag='0')
        inside['object_events']=[obj(gfx,*room['leader'],n+'_Leader'),obj('OBJ_EVENT_GFX_MAN_2',*room['guide'],n+'_Guide')]
        for j,student in enumerate(room['students']):
            xx,yy=student['position'];assert not values[yy*room['width']+xx]&0xc00
            inside['object_events'].append(obj('OBJ_EVENT_GFX_'+STUDENT_PROFILES[g['key']][j][2],xx,yy,n+f'_Student{j}',True,student['facing']))
        inside['warp_events']=[dict(x=room['entry'][0]+dx,y=room['height']-1,elevation=0,dest_map=city['id'],dest_warp_id=str(outside_warp)) for dx in range(2)]
        inside.update(coord_events=[],bg_events=[])
        stagejson(f'data/maps/{n}/map.json',inside);groups['JourneyExtraGyms'].append(n)
        badge='FLAG_JOURNEY_BADGE_'+g['key'];tm='FLAG_JOURNEY_TM_'+g['key']
        lines=f'{n}_MapScripts::\n'
        if g['key']=='WHITNEY':lines+=f'\tmap_script MAP_SCRIPT_ON_LOAD, {n}_Load\n\t.byte 0\n{n}_Load:\n\tcallnative JourneyExtraGymEdition\n\tend\n'
        else:lines+='\t.byte 0\n'
        lines+=f'{n}_Leader::\n\tgoto_if_set {badge}, {n}_Gift\n'
        if g['key']=='WHITNEY':lines+=f'\tcallnative JourneyExtraGymEdition\n\tgoto_if_eq VAR_RESULT, TRUE, {n}_Valerie\n'
        lines+=f'\ttrainerbattle_single TRAINER_JOURNEY_GYM_{g["key"]}, {n}_Intro, {n}_Defeat, {n}_Award, NO_MUSIC\n\tgoto {n}_Award\n'
        if g['key']=='WHITNEY':lines+=f'{n}_Valerie:\n\ttrainerbattle_single TRAINER_JOURNEY_GYM_VALERIE, {n}_ValerieIntro, {n}_Defeat, {n}_Award, NO_MUSIC\n\tgoto {n}_Award\n{n}_ValerieIntro:\n\t.string "VALERIE: FAIRY POKeMON turn\\n"\n\t.string "every battle into a work of art!$"\n'
        lines+=f'''{n}_Award:
\tlock
\tfaceplayer
\tgoto_if_set {badge}, {n}_Gift
\tmessage {n}_Badge
\twaitmessage
\tcall Common_EventScript_PlayGymBadgeFanfare
\tsetflag {badge}
\tcall Journey_FirstBadgeReward
{n}_Gift:
\tlock
\tfaceplayer
\tgoto_if_set {tm}, {n}_After
\tgiveitem ITEM_TM_{g['tm']}, 1
\tgoto_if_eq VAR_RESULT, FALSE, {n}_Full
\tsetflag {tm}
{n}_After:
\tmsgbox {n}_Thanks, MSGBOX_DEFAULT
\trelease
\tend
{n}_Full:
\tmsgbox {n}_BagFull, MSGBOX_DEFAULT
\trelease
\tend
{n}_Guide::
\tmsgbox {n}_Advice, MSGBOX_NPC
\tend
{n}_Intro:
\t.string "{g['leader'].upper()}: Welcome to my GYM!\\n"
\t.string "Show me your {g['kind']} strategy!$"
{n}_Defeat:
\t.string "A wonderful battle!\\nYour bond has earned my BADGE.$"
{n}_Badge:
\t.string "You earned the {g['badge']} BADGE!$"
{n}_Thanks:
\t.string "Your BADGE is registered.\\n"
\t.string "All 24 are needed for the LEAGUES!$"
{n}_BagFull:
\t.string "Your BAG is full. Make room\\n"
\t.string "and return for your TM.$"
{n}_Advice:
\t.string "This GYM specializes in {g['kind']}.\\n"
\t.string "Its team adapts to your progress.\\p"
\t.string "Win its BADGE for the 24-BADGE\\n"
\t.string "KANTO and HOENN LEAGUE challenge!$"
'''
        for j in range(4):lines+=f'''{n}_Student{j}::
\ttrainerbattle_single TRAINER_JOURNEY_GYM_STUDENT_{i*4+j}, {n}_StudentIntro, {n}_StudentLose
\tmsgbox {n}_StudentAfter, MSGBOX_AUTOCLOSE
\tend
'''
        lines+=f'''{n}_StudentIntro:
\t.string "Can you read our battle strategy?$"
{n}_StudentLose:
\t.string "You found the winning approach!$"
{n}_StudentAfter:
\t.string "Our LEADER is waiting ahead.$"
'''
        scripts.append(lines)
        records.append(dict(**g,badge_flag=0x1040+i,tm_flag=0x1048+i,trainer=1760+i,entry=entry,exterior_warp=outside_warp,students=[1769+i*4+j for j in range(4)],room=room,original_events_preserved=True))
    stagejson('data/maps/map_groups.json',groups);stagejson('data/layouts/layouts.json',layouts)
    layer.stage('src/data/tilesets/headers.h',headers);layer.stage('src/data/tilesets/graphics.h',graphics);layer.stage('src/data/tilesets/metatiles.h',metas)
    layer.stage('data/maps/JourneyExtraGyms.inc','\n'.join(scripts));layer.stage('data/event_scripts.s',read('data/event_scripts.s').decode()+'\n\t.include "data/maps/JourneyExtraGyms.inc"\n')
    if door_entries:
        p='src/field_door.c';t=read(p).decode();anchor='static const struct DoorGraphics sDoorAnimGraphicsTable[] =\n{'
        t=t.replace(anchor,'\n'.join(a for a,b in door_entries)+'\n'+anchor+'\n'+'\n'.join(b for a,b in door_entries));layer.stage(p,t)
    from extra_gym_logic import apply_logic
    apply_logic(layer,records)
    from extra_gym_landscape import finish as finish_landscape
    landscape=finish_landscape(layer)
    from extra_gym_sprites import apply as apply_sprites
    sprites=apply_sprites(layer)
    from extra_coastal_fixes import repair as repair_coasts
    coastal_fixes = repair_coasts(layer)
    return layer.finish(landscape_review=landscape,leader_sprites=sprites,coastal_fixes=coastal_fixes,gyms=records,total_badges=24,both_leagues_require_24=True,oak_mixed_starters=True,
        pending_story_milestones=[18,22],pending_story_events_implemented=False,
        native_art_private_banks=True,existing_campaign_preserved=True,existing_save_flags_bytes=872,
        allocated_flags=list(range(0x1000,0x1029))+list(range(0x1040,0x1050)))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.source),indent=2))
