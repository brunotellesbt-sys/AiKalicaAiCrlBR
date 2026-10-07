#!/usr/bin/env python3
"""Apply the reviewed journey source overlay to the pinned pret/pokefirered checkout."""
import argparse
import copy
import json
from pathlib import Path
import re
import shutil
import subprocess
import struct

ROOT = Path(__file__).resolve().parents[2]
FILES = ROOT/'tools/journey'
COMMIT = '7606f57650627704c9aad965a031fd3a454590e2'


def prepare(source):
    head = subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
    if head != COMMIT: raise ValueError('Wrong source commit')
    if subprocess.run(['git','-C',str(source),'diff','--quiet','HEAD','--']).returncode:
        raise ValueError('Use a clean source checkout; existing tracked changes are preserved')
    if (source / '.journey-prepared').exists(): raise ValueError('Use a fresh source checkout to reapply the overlay')
    config = json.loads((FILES/'homes.json').read_text())
    def load_map(name): return json.loads((source/f'data/maps/{name}/map.json').read_text())
    def write(relative,text):
        p = source/relative; p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    def replace(relative,old,new):
        p=source/relative;s=p.read_text()
        if old not in s: raise ValueError(f'Missing expected source in {relative}: {old[:70]}')
        p.write_text(s.replace(old,new,1))
    for name,target in [('journey.h','include/journey.h'),('journey.c','src/journey.c'),('events.inc','data/scripts/journey.inc')]:
        shutil.copyfile(FILES/name,source/target)
        if name == 'journey.c':
            p = source/target; text = p.read_text().replace('#include "field_fadetransition.h"','#include "field_fadetransition.h"\n#include "field_screen_effect.h"').replace('ScriptGiveMon(species[choice], 5, ITEM_NONE, 0, 0, 0);','ScriptGiveMon(species[choice], 5, ITEM_NONE);'); p.write_text(text)
    defs=(FILES/'journey.h').read_text()
    defines='\n'.join(line for line in defs.splitlines() if line.startswith('#define VAR_') or line.startswith('#define FLAG_'))
    for kind in ['vars','flags']:
        additions='\n'.join(line for line in defines.splitlines() if line.startswith('#define '+('VAR_' if kind=='vars' else 'FLAG_')))
        header=source/f'include/constants/{kind}.h'
        header.write_text(header.read_text().replace('#endif',additions+'\n#endif'))
    replace('data/event_scripts.s','#include "constants/global.h"','#include "constants/global.h"\n'+defines)
    with (source/'data/event_scripts.s').open('a') as f:f.write('\n\t.include "data/scripts/journey.inc"\n')
    replace('src/overworld.c','#include "global.h"','#include "global.h"\n#include "journey.h"')
    replace('src/overworld.c','    return gMapGroups[mapGroup][mapNum];','    const struct MapHeader *home = JourneyHomeHeader(mapGroup, mapNum);\n    if (home != NULL) return home;\n    return gMapGroups[mapGroup][mapNum];')
    replace('data/specials.inc','gSpecialsEnd::',''.join('\tdef_special '+n+'\n' for n in ['JourneyChooseHome','JourneyWarpBedroom','JourneySetRespawn','JourneySetupVisitors','JourneyFamilyInfo','JourneyGiveGift','JourneyGiveStarter'])+'gSpecialsEnd::')
    replace('src/field_move.c','#include "global.h"','#include "global.h"\n#include "journey.h"')
    replace('src/field_move.c','    return FlagGet(FLAG_BADGE05_GET);','    return VarGet(VAR_JOURNEY_HOME) != 0 || FlagGet(FLAG_BADGE05_GET);')
    replace('src/field_move.c','    return FlagGet(FLAG_BADGE07_GET);','    return VarGet(VAR_JOURNEY_HOME) != 0 || FlagGet(FLAG_BADGE07_GET);')
    replace('data/maps/PalletTown_PlayersHouse_2F/scripts.inc','\t.byte 0','\tmap_script MAP_SCRIPT_ON_FRAME_TABLE, Journey_FirstFrame\n\t.byte 0')
    with (source/'data/maps/PalletTown_PlayersHouse_2F/scripts.inc').open('a') as f:
        f.write('\nJourney_FirstFrame::\n\tmap_script_2 VAR_JOURNEY_CITY, 0, Journey_ChooseCity\n\t.2byte 0\n')
    replace('data/maps/PalletTown_PlayersHouse_1F/scripts.inc','PalletTown_PlayersHouse_1F_EventScript_Mom::','PalletTown_PlayersHouse_1F_EventScript_Mom::\n\tgoto_if_eq VAR_JOURNEY_CITY, 1, Journey_Family\nPalletTown_PlayersHouse_1F_EventScript_MomOriginal::')
    replace('data/maps/PalletTown_PlayersHouse_1F/scripts.inc','applymovement LOCALID_MOM, Common_Movement_FaceOriginalDirection','applymovement VAR_LAST_TALKED, Common_Movement_FaceOriginalDirection')
    replace('include/constants/menu.h','#define MULTICHOICE_NONE', '#define MULTICHOICE_JOURNEY_CITIES 65\n#define MULTICHOICE_JOURNEY_STARTERS 66\n\n#define MULTICHOICE_NONE')
    city_texts=''.join('static const u8 sJourneyCityText%d[] = _("%s");\n' % (i,c.get('label',c['name'])) for i,c in enumerate(config['cities']))
    starter_texts=''.join('static const u8 sJourneyStarterText%d[] = _("%s");\n' % (i,n) for i,n in enumerate(['Bulbasaur','Charmander','Squirtle']))
    lists=city_texts+starter_texts+'static const struct MenuAction sJourneyCities[] = {\n'+''.join('    {.text=sJourneyCityText%d, .func={.void_u8=NULL}},\n' % i for i in range(len(config['cities'])))+'};\nstatic const struct MenuAction sJourneyStarters[] = {\n'+''.join('    {.text=sJourneyStarterText%d, .func={.void_u8=NULL}},\n' % i for i in range(3))+'};\n\n'
    replace('src/script_menu.c','static const struct MultichoiceListStruct sMultichoiceLists[] = {',lists+'static const struct MultichoiceListStruct sMultichoiceLists[] = {\n    [MULTICHOICE_JOURNEY_CITIES] = MULTICHOICE(sJourneyCities),\n    [MULTICHOICE_JOURNEY_STARTERS] = MULTICHOICE(sJourneyStarters),')
    # Journey ferry access is independent of Celio/Lostelle/Liga completion.
    for entry in ['ChooseDestFromOneIsland','ChooseDestFromTwoIsland','ChooseDestFromIsland']:
        label='EventScript_'+entry+'::'
        replace('data/scripts/seagallop.inc',label,label+'\n\tgoto_if_set FLAG_JOURNEY_EARLY_FERRY, EventScript_SeviiDestinationsPage1')
    replace('data/maps/VermilionCity/scripts.inc',
            'VermilionCity_EventScript_FerrySailor::\n\tlock\n\tfaceplayer',
            'VermilionCity_EventScript_FerrySailor::\n\tlock\n\tfaceplayer\n\tgoto_if_set FLAG_JOURNEY_EARLY_FERRY, Journey_FerryFromVermilion')
    replace('data/maps/VermilionCity/scripts.inc',
            '\tgoto_if_eq VAR_MAP_SCENE_VERMILION_CITY, 3, VermilionCity_EventScript_CheckSeagallopPresentTrigger',
            '\tgoto_if_set FLAG_GOT_SS_TICKET, Journey_CheckTicketNormal\n\tgoto_if_set FLAG_JOURNEY_EARLY_FERRY, Journey_FerryFromVermilion\nJourney_CheckTicketNormal::\n\tgoto_if_eq VAR_MAP_SCENE_VERMILION_CITY, 3, VermilionCity_EventScript_CheckSeagallopPresentTrigger')
    for entry in ['CheckSeagallopPresent','CheckSeagallopPresentTrigger']:
        label='VermilionCity_EventScript_'+entry+'::\n\tsetvar VAR_0x8004, SEAGALLOP_VERMILION_CITY'
        replace('data/maps/VermilionCity/scripts.inc',label,label+'\n\tgoto_if_set FLAG_JOURNEY_EARLY_FERRY, EventScript_SeviiDestinationsPage1')
    # A small original suitcase sprite, using the game's white NPC palette.
    pixels=[[0]*16 for _ in range(16)]
    for y in range(5,14):
        for x in range(1,15):pixels[y][x]=1 if x in (1,14) or y in (5,13) else 3
    for x,y in [(6,3),(7,3),(8,3),(9,3),(6,4),(9,4)]:pixels[y][x]=1
    for y in range(6,13):pixels[y][5]=2;pixels[y][10]=2
    pixels[8][7]=pixels[8][8]=2
    packed=bytearray()
    for ty in (0,8):
        for tx in (0,8):
            for y in range(8):
                for x in range(0,8,2):packed.append(pixels[ty+y][tx+x]|pixels[ty+y][tx+x+1]<<4)
    vals=struct.unpack('<64H',packed)
    replace('include/constants/event_objects.h','#define NUM_OBJ_EVENT_GFX     157','#define OBJ_EVENT_GFX_JOURNEY_CASE 157\n#define NUM_OBJ_EVENT_GFX     158')
    with (source/'src/data/object_events/object_event_graphics.h').open('a') as f:f.write('\nconst u16 gObjectEventPic_JourneyCase[] = {'+','.join(hex(v) for v in vals)+'};\n')
    with (source/'src/data/object_events/object_event_pic_tables.h').open('a') as f:f.write('\nstatic const struct SpriteFrameImage sPicTable_JourneyCase[] = {overworld_frame(gObjectEventPic_JourneyCase, 2, 2, 0)};\n')
    info=(source/'src/data/object_events/object_event_graphics_info.h').read_text()
    item=re.search(r'const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_ItemBall = \{.*?\n\};',info,re.S).group()
    with (source/'src/data/object_events/object_event_graphics_info.h').open('a') as f:f.write('\n'+item.replace('gObjectEventGraphicsInfo_ItemBall','gObjectEventGraphicsInfo_JourneyCase').replace('sPicTable_ItemBall','sPicTable_JourneyCase')+'\n')
    replace('src/data/object_events/object_event_graphics_info_pointers.h','const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_ItemBall;', 'const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_ItemBall;\nconst struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_JourneyCase;')
    replace('src/data/object_events/object_event_graphics_info_pointers.h','    [OBJ_EVENT_GFX_ITEM_BALL]', '    [OBJ_EVENT_GFX_JOURNEY_CASE] = &gObjectEventGraphicsInfo_JourneyCase,\n    [OBJ_EVENT_GFX_ITEM_BALL]')
    groups=json.loads((source/'data/maps/map_groups.json').read_text())
    groups['group_order']+=['JourneyBedrooms','JourneyLivingRooms']
    groups['JourneyBedrooms']=[];groups['JourneyLivingRooms']=[]
    living=load_map('PalletTown_PlayersHouse_1F');bedroom=load_map('PalletTown_PlayersHouse_2F')
    base_object=copy.deepcopy(living['object_events'][0])
    rows=[];report=[]
    non_people={'OBJ_EVENT_GFX_NIDORAN_M','OBJ_EVENT_GFX_CUBONE','OBJ_EVENT_GFX_PIDGEY','OBJ_EVENT_GFX_SPEAROW','OBJ_EVENT_GFX_CLIPBOARD'}
    for city,c in enumerate(config['cities']):
        if len(c['houses']) != 1: raise ValueError('Each city must have exactly one fixed home')
        for name in c['houses']:
            original=load_map(name)
            people=[o for o in original['object_events'] if o['graphics_id'] not in non_people]
            female=lambda o: any(part in o['graphics_id'] for part in ['MOM','WOMAN','LASS','COOLTRAINER_F'])
            mother=next((i for i,o in enumerate(people) if female(o)),0)
            people.insert(0,people.pop(mother))
            roles=[1]+[4 if female(o) or 'GIRL' in o['graphics_id'] else (3 if any(t in o['graphics_id'] for t in ['BOY','YOUNGSTER']) else 2) for o in people[1:]]
            if len(people)>3: raise ValueError('House has more than three human residents')
            roles=(roles+[0,0])[:3]
            index=len(rows)
            bname=f'JourneyBedroom{index:02d}';lname=f'JourneyLiving{index:02d}'
            bid=f'MAP_JOURNEY_BEDROOM_{index:02d}';lid=f'MAP_JOURNEY_LIVING_{index:02d}'
            rows.append('{'+','.join([original['id'],lid,bid,c['heal'],str(city),str(len(people)),str(roles[1]),str(roles[2])])+'}')
            report.append({'index':index+1,'city':c['name'],'house':name,'original_map':original['id'],'bedroom_map':bid,'living_map':lid,'people':len(people),'original_people':[o['graphics_id'] for o in people],'roles':roles[:len(people)]})
            if city==0:continue
            out=copy.deepcopy(living);out.update(id=lid,name=lname,music=original['music'],region_map_section=original['region_map_section'])
            out['object_events']=[]
            for role,o in enumerate(people):
                obj=copy.deepcopy(base_object)
                obj.update(graphics_id='OBJ_EVENT_GFX_MOM' if role==0 else ('OBJ_EVENT_GFX_MAN' if roles[role]==2 else ('OBJ_EVENT_GFX_LITTLE_GIRL' if roles[role]==4 else 'OBJ_EVENT_GFX_LITTLE_BOY')),x=[8,8,3][role],y=[4,6,6][role],script='Journey_Family',local_id=f'LOCALID_JOURNEY_FAMILY_{index}_{role}',movement_type='MOVEMENT_TYPE_FACE_DOWN')
                out['object_events'].append(obj)
            # Pad unused local IDs with permanently hidden invisible objects. Oak/case IDs stay 10/11.
            while len(out['object_events'])<9:
                obj=copy.deepcopy(base_object);obj.update(graphics_id='OBJ_EVENT_GFX_MOM',x=0,y=0,script='EventScript_Return',flag='FLAG_0x8E2')
                obj.pop('local_id',None)
                out['object_events'].append(obj)
            for gfx,x,y,script in [('OBJ_EVENT_GFX_PROF_OAK',4,4,'Journey_Oak'),('OBJ_EVENT_GFX_JOURNEY_CASE',6,4,'Journey_Case')]:
                obj=copy.deepcopy(base_object);obj.update(graphics_id=gfx,x=x,y=y,script=script,flag='FLAG_JOURNEY_HIDE_VISITOR',movement_type='MOVEMENT_TYPE_FACE_DOWN')
                obj.pop('local_id',None)
                out['object_events'].append(obj)
            exit_warp=next(w for w in original['warp_events'] if w['dest_map'] == c['outside'])
            for w in out['warp_events']:
                if w['dest_map']=='MAP_PALLET_TOWN':w.update(dest_map=exit_warp['dest_map'],dest_warp_id=exit_warp['dest_warp_id'])
                else:w.update(dest_map=bid,dest_warp_id='0')
            out['coord_events']=[{'type':'trigger','x':x,'y':8,'elevation':3,'var':'VAR_JOURNEY_STAGE','var_value':'1','script':'Journey_NeedStarter'} for x in (4,5)]
            write(f'data/maps/{lname}/map.json',json.dumps(out,indent=2)+'\n')
            write(f'data/maps/{lname}/scripts.inc',lname+'_MapScripts::\n\tmap_script MAP_SCRIPT_ON_TRANSITION, Journey_Living_Transition\n\t.byte 0\n')
            groups['JourneyLivingRooms'].append(lname)
            b=copy.deepcopy(bedroom);b.update(id=bid,name=bname,music=original['music'],region_map_section=original['region_map_section'])
            b['warp_events'][0].update(dest_map=original['id'],dest_warp_id='2')
            write(f'data/maps/{bname}/map.json',json.dumps(b,indent=2)+'\n')
            write(f'data/maps/{bname}/scripts.inc',bname+'_MapScripts::\n\tmap_script MAP_SCRIPT_ON_TRANSITION, Journey_Bedroom_Transition\n\t.byte 0\n')
            groups['JourneyBedrooms'].append(bname)
    with (source/'data/event_scripts.s').open('a') as f:
        for name in groups['JourneyBedrooms']+groups['JourneyLivingRooms']:
            f.write('\t.include "data/maps/'+name+'/scripts.inc"\n')
    # Pallet table entries use real maps because there are no cloned rooms for it.
    rows[0]='{MAP_PALLET_TOWN_PLAYERS_HOUSE_1F,MAP_PALLET_TOWN_PLAYERS_HOUSE_1F,MAP_PALLET_TOWN_PLAYERS_HOUSE_2F,HEAL_LOCATION_PALLET_TOWN,0,1,0,0}'
    write('include/journey_homes.h','static const struct JourneyHome sJourneyHomes[] = {\n'+',\n'.join(rows)+'\n};\n')
    write('data/maps/map_groups.json',json.dumps(groups,indent=2)+'\n')
    # The hidden padding objects never spawn, including in a fresh save.
    replace('src/new_game.c','    InitEventData();','    InitEventData();\n    FlagSet(FLAG_0x8E2);')
    write('.journey-prepared',json.dumps({'homes':report,'excluded':config['excluded'],'commit':COMMIT},indent=2)+'\n')
    from open_world import apply
    apply(source)
    from wild_world import apply as apply_wild
    apply_wild(source)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    args=p.parse_args();print(json.dumps(prepare(args.source.resolve()),indent=2))
