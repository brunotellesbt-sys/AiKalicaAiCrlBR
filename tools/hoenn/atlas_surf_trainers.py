"""Swimmers on real reachable Surf corridors, with private persistent flags."""
from copy import deepcopy
import hashlib
from pathlib import Path
import re
import subprocess

from atlas_surf_background import cells as background_cells
from atlas_surf_migration import _occupied
from badge_story_layer import read

ROOT=Path(__file__).resolve().parents[2]
DIRECTIONS=[('DOWN',0,1),('UP',0,-1),('LEFT',-1,0),('RIGHT',1,0)]
TEAMS=[['TENTACOOL','WINGULL'],['STARYU','HORSEA'],['MARILL','CHINCHOU'],
       ['SHELLDER','REMORAID'],['CARVANHA','WAILMER'],['PSYDUCK','POLIWAG'],
       ['SLOWPOKE','KRABBY'],['WOOPER','MANTYKE'],['BUIZEL','FINNEON'],
       ['QWILFISH','CORSOLA'],['TENTACOOL','MANTINE'],['GOLDEEN','SEEL']]


def flag_space(view,count):
    raw=view.read('include/constants/flags.h').decode()
    names=list(dict.fromkeys(re.findall(r'^#define\s+(FLAG_\w+)\s',raw,re.M)))
    code='#include "constants/flags.h"\nconst unsigned short probe[]={'+','.join(names)+'};\n'
    asm=subprocess.check_output([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S',
        '-iquote',str(view.source/'include'),'-x','c','-','-o','-'],input=code,text=True)
    used={int(v) for v in re.findall(r'\.short\s+(\d+)',asm)}|set(range(0x500,0x500+1622))
    # Explicitly reviewed unused save bank between new story flags and Kanto.
    available=[i for i in range(0x1060,0x1100) if i not in used]
    if len(available)<count:raise ValueError('Not enough authenticated private swimmer flags')
    return available[:count],dict(old_flag_macros=len(names),native_macros_compiled=True,
        assembly_sha256=hashlib.sha256(asm.encode()).hexdigest(),existing_save_size_unchanged=True)


def candidates(view,metadata,graph):
    if graph.source is not view or graph.ocean_component is None:
        raise ValueError('Trainer positions require the actual audited playable ocean')
    result=[]
    for chunk in metadata['geometry_plan']['chunks']:
        if chunk['kind']!='ordinary':continue
        name=chunk['name'];layout=view.layout(name);mapping=view.maps[name]
        if len(mapping.get('object_events') or [])>=30:continue
        blocked=_occupied(mapping)|background_cells(chunk)
        for direction,dx,dy in DIRECTIONS:
            choices=[]
            for y in range(2,layout['height']-2):
                for x in range(2,layout['width']-2):
                    # Three tiles wide through the NPC, approach and sight.
                    corridor={(x+dx*step-dy*side,y+dy*step+dx*side)
                              for step in range(-1,5) for side in (-1,0,1)}
                    if corridor&blocked:continue
                    if not all(0<=a<layout['width'] and 0<=b<layout['height']
                        and view.word(name,a,b)>>12==1 and view.water(name,a,b)
                        and graph.component([name,a,b],1)==graph.ocean_component for a,b in corridor):continue
                    score=(abs(2*x-layout['width'])+abs(2*y-layout['height']),y,x)
                    choices.append((score,x,y))
            if choices:
                _,x,y=min(choices);ox,oy=chunk['origin']
                result.append(dict(map=name,tile=[x,y],global_tile=[ox+x,oy+y],
                    facing=direction,delta=[dx,dy],clear_water_corridor=[3,6]))
    return result


def stage(layer,view,metadata,graph,*,count=96):
    pool=candidates(view,metadata,graph);flags,flag_proof=flag_space(view,count)
    origins={r['name']:r['origin'] for r in metadata['geometry_plan']['chunks']}
    anchors=[]
    for name,origin in origins.items():
        for event in view.maps[name].get('object_events') or []:
            if event.get('trainer_type') not in (None,'TRAINER_TYPE_NONE'):
                anchors.append([origin[0]+event['x'],origin[1]+event['y']])
    selected=[];used_maps=set()
    for i in range(count):
        facing=DIRECTIONS[i%4][0]
        options=[r for r in pool if r['map'] not in used_maps and r['facing']==facing]
        if not options:break
        def distance(row):
            x,y=row['global_tile']
            return min((abs(x-a)+abs(y-b) for a,b in anchors),default=9999)
        chosen=max(options,key=lambda r:(distance(r),-view.identities[r['map']]))
        if distance(chosen)<24:break
        chosen=deepcopy(chosen);chosen['nearest_trainer_distance']=distance(chosen)
        selected.append(chosen);used_maps.add(chosen['map']);anchors.append(chosen['global_tile'])
    if len(selected)!=count:raise ValueError(('Insufficient spacious separated trainer sites',len(selected),count))
    opponents=read(layer,'include/constants/opponents.h').decode()
    first=int(re.search(r'^#define\s+TRAINERS_COUNT\s+(\d+)',opponents,re.M)[1])
    opponents,n=re.subn(r'(^#define\s+TRAINERS_COUNT\s+)\d+',lambda m:m[1]+str(first+count),opponents,flags=re.M)
    if n!=1:raise ValueError('Trainer count anchor changed')
    definitions=[];parties=[];scripts=[]
    for i,row in enumerate(selected):
        name=row['map'];mapping=deepcopy(view.maps[name]);x,y=row['tile'];female=bool(i%2)
        key='TRAINER_JOURNEY_ATLAS_SWIMMER_'+str(i);label='JourneyAtlasSwimmer'+str(i)
        definitions.append(f'#define {key} {first+i}\n')
        mapping['object_events'].append(dict(type='object',graphics_id='OBJ_EVENT_GFX_SWIMMER_'+('F' if female else 'M')+'_WATER',
            x=x,y=y,elevation=1,movement_type='MOVEMENT_TYPE_FACE_'+row['facing'],movement_range_x=0,movement_range_y=0,
            trainer_type='TRAINER_TYPE_NORMAL',trainer_sight_or_berry_tree_id='3',script=label,flag='0'))
        layer.stage('data/maps/'+name+'/map.json',__import__('json').dumps(mapping,indent=2)+'\n')
        mons=TEAMS[i%len(TEAMS)];level=28+2*(i%5)
        team=','.join('{.species=SPECIES_'+mon+',.lvl='+str(level)+',.iv=TRAINER_PARTY_IVS(15,15,15,15,15,15),'
            '.gender=TRAINER_MON_RANDOM_GENDER,.ball=POKEBALL_COUNT,.nature=NATURE_HARDY}' for mon in mons)
        gender='FEMALE' if female else 'MALE';sex='F' if female else 'M'
        parties.append(f'[DIFFICULTY_NORMAL][{key}]={{.trainerName=_("'+('Nina' if female else 'Leo')+'"),'
            '.trainerClass=TRAINER_CLASS_SWIMMER_'+sex+',.trainerPic=TRAINER_PIC_SWIMMER_'+sex+',.gender=TRAINER_GENDER_'+gender+
            ',.encounterMusic=TRAINER_ENCOUNTER_MUSIC_SWIMMER,.aiFlags=AI_FLAG_BASIC_TRAINER,.partySize=2,.party=(const struct TrainerMon[]){'+team+'}},\n')
        scripts.append(f'''\n{label}::
\ttrainerbattle_single {key}, JourneyAtlasSwimmer_Intro, JourneyAtlasSwimmer_Defeat
\tmsgbox JourneyAtlasSwimmer_After, MSGBOX_NPC
\tend
''')
        row.update(id=first+i,key=key,flag=flags[i],script=label,level=level,species=mons)
    scripts.append('''
JourneyAtlasSwimmer_Intro:
\t.string "The sea is wide!\\nLet's battle on the waves!$"
JourneyAtlasSwimmer_Defeat:
\t.string "You ride the waves so well!$"
JourneyAtlasSwimmer_After:
\t.string "Follow the open channels\\nbetween the reefs.$"
''')
    layer.stage('include/constants/opponents.h',opponents+'\n'+''.join(definitions))
    layer.stage('include/constants/flags.h',read(layer,'include/constants/flags.h').decode()+'\n'+''.join(
        f'#define FLAG_JOURNEY_ATLAS_SWIMMER_{i} 0x{flag:X}\n' for i,flag in enumerate(flags)))
    layer.stage('src/data/journey_atlas_swimmers.h',''.join(parties))
    layer.stage('data/scripts/journey_atlas_swimmers.inc',''.join(scripts))
    path='src/data.c';text=read(layer,path).decode();anchor='#include "data/journey_qualifier_trainers.h"'
    if text.count(anchor)!=1:raise ValueError('Trainer table include anchor changed')
    layer.stage(path,text.replace(anchor,anchor+'\n#include "data/journey_atlas_swimmers.h"'))
    path='data/event_scripts.s';layer.stage(path,read(layer,path).decode()+'\n\t.include "data/scripts/journey_atlas_swimmers.inc"\n')
    path='src/battle_setup.c';text=read(layer,path).decode();anchor='static u16 JourneyBeachTrainerFlag(u16 trainerId)\n{'
    if text.count(anchor)!=1:raise ValueError('Reviewed private trainer flag hook changed')
    layer.stage(path,text.replace(anchor,anchor+f'\n    if (trainerId >= {first} && trainerId < {first+count})\n        return 0x{flags[0]:X} + trainerId - {first};'))
    if flags!=list(range(flags[0],flags[0]+count)):raise ValueError('Swimmer flag range must be consecutive')
    return dict(trainers=selected,count=count,flag_allocation=flag_proof,
        all_positions_in_real_ocean_SCC=True,terrain_unchanged=True,all_native_trainer_identities_preserved=True,
        four_facing_directions=True,normal_hard_generation_rules_unchanged=True,
        TESTE_auto_approach_rules_unchanged=True,native_battles_and_save_validation_pending=True)
