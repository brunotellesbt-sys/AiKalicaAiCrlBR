"""Add the regional incursions, Mauville basements and Giovanni alliance.

Apply after the seven existing connected-world overlays. Native event IDs
are retained; this does not by itself prove complete campaign progression.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import textwrap

from prepare_crossing import PIN
from partner_portrait import patch as partner_portrait_patch
from team_stories import EPISODES, GUIDE_MESSAGES, GIOVANNI_DIALOGUE, PARTNER_PARTY


def prepare(source):
    source = Path(source)
    marker = source / '.journey-team-stories'
    if marker.exists():
        report = json.loads(marker.read_text())
        for p, digest in report['prepared_sha256'].items():
            if hashlib.sha256((source / p).read_bytes()).hexdigest() != digest:
                raise ValueError('Modified team-story output: ' + p)
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    if acquired['commit'] != PIN:
        raise ValueError('Unexpected base')
    expected = dict(acquired['sha256'])
    for name in ['hoenn-crossing','worldsea','westsea','region-state','east-coast','gym-scaling','campaign-gates']:
        expected.update(json.loads((source / f'.journey-{name}').read_text())['prepared_sha256'])
    outputs, originals, inputs = {}, {}, {}

    def read(path):
        raw = outputs.get(path)
        if raw is None:
            raw = (source / path).read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if digest != expected.get(path):
                raise ValueError('Unreviewed input: ' + path)
            if path in acquired['sha256']:
                inputs[path] = acquired['sha256'][path]
        return raw

    def stage(path, value):
        if path not in originals:
            original = (source / path).read_bytes() if (source / path).exists() else None
            digest = hashlib.sha256(original).hexdigest() if original is not None else None
            if digest is not None and digest != expected.get(path):
                raise ValueError('Unreviewed modification: ' + path)
            originals[path] = digest
        outputs[path] = value if isinstance(value, bytes) else value.encode()

    def jstage(path, value): stage(path, json.dumps(value, indent=2) + '\n')
    layouts = json.loads(read('data/layouts/layouts.json'))
    by_layout = {l['id']:l for l in layouts['layouts']}
    groups = json.loads(read('data/maps/map_groups.json'))
    maps = {}
    preserved = {}
    def existing(name):
        if name not in maps:
            maps[name] = json.loads(read(f'data/maps/{name}/map.json'))
            preserved[name] = {k:hashlib.sha256(json.dumps(maps[name].get(k,[]),sort_keys=True).encode()).hexdigest()
                               for k in ['object_events','warp_events','coord_events','bg_events']}
        return maps[name]
    def blocks(name):
        layout = by_layout[existing(name)['layout']]
        raw = read(layout['blockdata_filepath'])
        return layout,list(struct.unpack('<'+'H'*(len(raw)//2),raw))
    def set_blocks(layout, values): stage(layout['blockdata_filepath'],struct.pack('<'+'H'*len(values),*values))

    # Two Hoenn-format rooms use native Facility tiles, so badges and field
    # behavior do not switch to FRLG while exploring the Hoenn Rocket branch.
    new_maps=[]
    for floor in [1,2]:
        name=f'JourneyRocketBaseB{floor}F'; root=f'data/layouts/{name}'
        layout=dict(id='LAYOUT_'+name.upper(),name=name+'_Layout',width=22,height=20,
                    primary_tileset='gTileset_General',secondary_tileset='gTileset_Facility',
                    border_filepath=root+'/border.bin',blockdata_filepath=root+'/map.bin',
                    layout_version='emerald',border_width=2,border_height=2)
        layouts['layouts'].append(layout); by_layout[layout['id']]=layout
        values=[0x0601]*(22*20)
        for y in range(2,18):
            for x in range(2,20): values[y*22+x]=0x3228
        # Broad corridors around the partitions; no switches or terrestrial HMs.
        for y in range(5,15):
            if y not in [8,9,12]: values[y*22+10]=0x064A
        for x,y in ([(3,3),(18,16)] if floor == 1 else [(3,3)]): values[y*22+x]=0x32CC
        stage(root+'/map.bin',struct.pack('<'+'H'*len(values),*values))
        stage(root+'/border.bin',struct.pack('<4H',*([0x0601]*4)))
        maps[name]=dict(id='MAP_'+name.upper(),name=name,layout=layout['id'],music='MUS_RG_ROCKET_HIDEOUT',
                       region='REGION_HOENN',region_map_section='MAPSEC_MAUVILLE_CITY',requires_flash=False,
                       weather='WEATHER_NONE',map_type='MAP_TYPE_UNDERGROUND',allow_cycling=False,
                       allow_escaping=True,allow_running=True,show_map_name=False,
                       battle_scene='MAP_BATTLE_SCENE_NORMAL',connections=[],object_events=[],
                       warp_events=[],coord_events=[],bg_events=[])
        new_maps.append(name)
    casino=existing('MauvilleCity_GameCorner')
    casino_warp=len(casino['warp_events'])
    casino['warp_events'].append(dict(x=19,y=7,elevation=3,dest_map=maps[new_maps[0]]['id'],dest_warp_id='0'))
    layout,values=blocks('MauvilleCity_GameCorner'); values[7*layout['width']+19]=0x3206; set_blocks(layout,values)
    maps[new_maps[0]]['warp_events']=[dict(x=3,y=3,elevation=3,dest_map=casino['id'],dest_warp_id=str(casino_warp)),
                                     dict(x=18,y=16,elevation=3,dest_map=maps[new_maps[1]]['id'],dest_warp_id='0')]
    maps[new_maps[1]]['warp_events']=[dict(x=3,y=3,elevation=3,dest_map=maps[new_maps[0]]['id'],dest_warp_id='1')]
    groups[groups['group_order'][-1]].extend(new_maps)
    for name in new_maps: stage(f'data/maps/{name}/scripts.inc',name+'_MapScripts::\n\t.byte 0\n')

    # Copy self-contained native shoreline patches using only primary tiles.
    # Water at every map edge remains unchanged, preserving the Surf seams.
    patches={}
    for frlg,name,bounds in [(False,'Route109',(24,41,31,49)),(True,'Route20_Frlg',(30,11,35,16))]:
        layout,values=blocks(name); x0,y0,x1,y1=bounds
        patch=[[values[y*layout['width']+x] for x in range(x0,x1)]for y in range(y0,y1)]
        if any(v&1023>=512 for row in patch for v in row): raise ValueError('Secondary tile in shoreline patch')
        patches[frlg]=patch
    sea_names=[n for label in groups['group_order'] for n in groups[label]
               if n.startswith('Journey') and n not in new_maps+['JourneyHoennCrossing']]
    island_centers={}; ocean_design=[]
    for name in sea_names:
        data=existing(name); layout,values=blocks(name)
        frlg=layout['layout_version']=='frlg'; patch=patches[frlg]
        height,width=len(patch),len(patch[0]); w,h=layout['width'],layout['height']
        origins=[(max(3,w//4-width//2),max(3,h//4-height//2))]
        if w>=40 and h>=30: origins.append((w*3//4-width//2,h*3//4-height//2))
        centers=[]
        for x0,y0 in origins:
            if x0+width>w-2 or y0+height>h-2: continue
            for dy,row in enumerate(patch):
                for dx,value in enumerate(row): values[(y0+dy)*w+x0+dx]=value
            centers.append((x0+width//2,y0+height//2))
        if not centers: raise ValueError('No island room: '+name)
        set_blocks(layout,values); island_centers[name]=centers
        ocean_design.append(dict(map=name,islands=centers,shoreline_source='Route20_Frlg' if frlg else 'Route109'))

    trainers=[]; scripts=[]; parties=[]
    def text(label,lines):
        wrapped=[line for sentence in lines for line in textwrap.wrap(sentence,width=28)]
        value='\n'+label+'::\n'
        for i,line in enumerate(wrapped):
            suffix='$' if i==len(wrapped)-1 else '\\p' if i%2 else '\\n'
            value+=f'\t.string "{line}{suffix}"\n'
        return value
    def free(name,anchor,elevation=3,minimum=2):
        data=existing(name); layout,values=blocks(name); w,h=layout['width'],layout['height']
        occupied={(e['x'],e['y'])for key in ['object_events','warp_events','coord_events','bg_events']for e in data.get(key,[])}
        candidates=[]
        for y in range(2,h-2):
            for x in range(2,w-2):
                value=values[y*w+x]
                if value&0xC00 or value>>12!=elevation: continue
                if any(abs(x-a)+abs(y-b)<minimum for a,b in occupied):continue
                neighbors=sum(not values[yy*w+xx]&0xC00 and values[yy*w+xx]>>12==elevation
                              for xx,yy in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)])
                if neighbors<3:continue
                candidates.append((abs(x-anchor[0])+abs(y-anchor[1]),y,x))
        if not candidates:raise ValueError('No safe trainer position: '+name)
        _,y,x=min(candidates);return x,y
    def trainer(name,anchor,team,role,intro,mission=None,water=False):
        number=1478+len(trainers); key=f'TRAINER_JOURNEY_TEAM_{number}'
        x,y=free(name,anchor,1 if water else 3,2)
        classes={'magma':('Magma Admin' if role=='admin' else 'Team Magma', 'Magma Admin' if role=='admin' else 'Magma Grunt M', 'Magma'),
                 'aqua':('Aqua Admin' if role=='admin' else 'Team Aqua', 'Aqua Admin F' if role=='admin' else 'Aqua Grunt M','Aqua'),
                 'rocket':('Team Rocket Frlg','Rocket Grunt M Frlg','Aqua'),
                 'swimmer':('Swimmer M','Swimmer M','Swimmer')}
        cls,pic,music=classes[team]
        nickname={'magma':'VULCAN','aqua':'MARINA','rocket':'ATLAS','swimmer':'SWIMMER'}[team] if role=='admin' or team=='swimmer' else 'GRUNT'
        level=36 if role=='admin' else 32 if team!='swimmer' else 28
        species={'magma':['Numel','Mightyena','Golbat'],'aqua':['Carvanha','Mightyena','Golbat'],
                 'rocket':['Raticate','Golbat','Koffing'],'swimmer':['Tentacool','Wingull']}[team]
        if role=='admin': species={'magma':['Camerupt','Mightyena','Crobat'],
                                  'aqua':['Sharpedo','Mightyena','Crobat'],
                                  'rocket':['Persian','Weezing','Golbat','Hypno']}[team]
        parties.append(f'\n=== {key} ===\nName: {nickname}\nClass: {cls}\nPic: {pic}\nGender: {"Female" if team=="aqua" and role=="admin" else "Male"}\nMusic: {music}\nAI: Basic Trainer\n'
                       +''.join(f'\n{mon}\nLevel: {level}\nIVs: 15 HP / 15 Atk / 15 Def / 15 SpA / 15 SpD / 15 Spe\n'for mon in species))
        label=f'JourneyTeam_Trainer{number}'
        scripts.append(f'\n{label}::\n\ttrainerbattle_single {key}, {label}_Intro, {label}_Defeat\n\tmsgbox {label}_After, MSGBOX_NPC\n\tend\n'
                       +text(label+'_Intro',intro)+text(label+'_Defeat',['Our plan has failed!'])
                       +text(label+'_After',['You beat us. We are leaving this operation.']))
        gfx={'magma':'OBJ_EVENT_GFX_MAGMA_MEMBER_M','aqua':'OBJ_EVENT_GFX_AQUA_MEMBER_F'if role=='admin' else 'OBJ_EVENT_GFX_AQUA_MEMBER_M',
             'rocket':'OBJ_EVENT_GFX_ROCKET_M','swimmer':'OBJ_EVENT_GFX_SWIMMER_M_WATER'}[team]
        existing(name)['object_events'].append(dict(type='object',graphics_id=gfx,x=x,y=y,elevation=1 if water else 3,
            movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,movement_range_y=0,
            trainer_type='TRAINER_TYPE_NORMAL',trainer_sight_or_berry_tree_id='2',script=label,flag='0'))
        trainers.append(dict(id=number,key=key,map=name,x=x,y=y,water=water,team=team,role=role,mission=mission,level=level))
        return key
    missions=[]
    for episode in EPISODES:
        members=[]
        total=sum(count for _,_,count in episode['maps']); index=0
        for name,anchor,count in episode['maps']:
            if name in island_centers:anchor=island_centers[name][0]
            for _ in range(count):
                team=episode['team']
                if team=='mixed':team='magma' if index%2==0 else 'aqua'
                role='admin' if episode.get('admin') and index==total-1 else 'grunt'
                members.append(trainer(name,anchor,team,role,episode['intro'],episode['key']))
                index+=1
        missions.append(dict(key=episode['key'],event=episode['event'],kanto=episode['region']=='kanto',
                             badge_count=episode['badge_count'],trainers=members))
    for i,name in enumerate(sea_names):
        layout,_=blocks(name)
        for j in range(2 if layout['width']>=32 and layout['height']>=24 else 1):
            anchor=(layout['width']*(j+1)//3,layout['height']*(j+1)//3)
            trainer(name,anchor,'swimmer','trainer',['The sea connects our regions!', 'Let us test our POKEMON!'],water=True)

    # Unique opponents for the final pair, without reusing the Shelly flag from
    # her original Seafloor battle or replacing the native earlier encounters.
    alliance=[]
    for boss,cls,pic,mons in [('ARCHIE','Aqua Leader','Aqua Leader Archie',['Mightyena','Crobat','Sharpedo']),
                             ('SHELLY','Aqua Admin','Aqua Admin F',['Sharpedo','Ludicolo','Crobat'])]:
        number=1478+len(trainers);key=f'TRAINER_JOURNEY_{boss}_ALLIANCE';alliance.append(key)
        trainers.append(dict(id=number,key=key,map='SeafloorCavern_Room9',team='aqua',role='final_boss',mission=None))
        parties.append(f'\n=== {key} ===\nName: {boss}\nClass: {cls}\nPic: {pic}\nGender: {"Female" if boss=="SHELLY" else "Male"}\nMusic: Aqua\nAI: Basic Trainer\n'
                       +''.join(f'\n{mon}\nLevel: {54+i}\nIVs: 25 HP / 25 Atk / 25 Def / 25 SpA / 25 SpD / 25 Spe\n'for i,mon in enumerate(mons)))
    if 1478+len(trainers)>1622: raise ValueError('Trainer flag allocation overflow')
    path='include/constants/opponents.h'; body=read(path).decode()
    body=body.replace('#define TRAINERS_COUNT                      1478',f'#define TRAINERS_COUNT                      {1478+len(trainers)}')
    body=body.replace('#endif  // GUARD_CONSTANTS_OPPONENTS_H', '\n'.join(f'#define {t["key"]} {t["id"]}'for t in trainers)+'\n\n#endif  // GUARD_CONSTANTS_OPPONENTS_H')
    stage(path,body)
    path='src/data/trainers.party';stage(path,read(path).decode()+''.join(parties))
    path='include/constants/battle_partner.h';stage(path,read(path).decode().replace('#define PARTNER_COUNT 2','#define PARTNER_GIOVANNI 2\n#define PARTNER_COUNT 3'))
    path='src/battle_controller_player_partner.c';stage(path,partner_portrait_patch(read(path).decode()))
    path='src/data/battle_partners.party';stage(path,read(path).decode()+PARTNER_PARTY)

    mission_header='struct JourneyTeamMission { bool8 kanto; u8 badges; u8 event; u16 count; const u16 *trainers; };\n'
    for m in missions:mission_header+=f'static const u16 sJourneyMission_{m["key"]}[] = {{'+', '.join(m['trainers'])+'};\n'
    mission_header+='static const struct JourneyTeamMission sJourneyTeamMissions[] = {\n'
    for m in missions:mission_header+=f'    {{{"TRUE"if m["kanto"]else"FALSE"}, {m["badge_count"]}, {m["event"]}, {len(m["trainers"])}, sJourneyMission_{m["key"]}}},\n'
    mission_header+='};\n';stage('include/journey_team_missions.h',mission_header)
    path='src/journey_campaign_gates.c';body=read(path).decode()
    body=body.replace('#include "constants/vars.h"','#include "constants/vars.h"\n#include "constants/opponents.h"\n#include "journey_team_missions.h"')
    start=body.index('u32 JourneyPendingCampaignEvent(bool32 kanto)');end=body.index('\nvoid JourneyStartSpaceCenterInvasion',start)
    replacement=(Path(__file__).parent/'team_story_gates.c.inc').read_text()
    body=body[:start]+replacement+body[end:]
    body=body.replace('JourneyGymBadgeCount(FALSE) < 6','JourneyGymBadgeCount(FALSE) < 7').replace('before the seventh arbitrary gym','before the eighth arbitrary gym')
    stage(path,body)
    path='data/specials.inc';stage(path,read(path).decode()+'\tdef_special JourneySilphCoPermission\n\tdef_special JourneyArchiePermission\n')
    path='data/scripts/journey_campaign_gates.inc';body=read(path).decode()
    anchor='\tgoto_if_eq VAR_RESULT, 6, Journey_GymGuide_Event6\n'
    body=body.replace(anchor,anchor+''.join(f'\tgoto_if_eq VAR_RESULT, {event}, Journey_GymGuide_Event{event}\n'for event in GUIDE_MESSAGES))
    for event,(team,lines)in GUIDE_MESSAGES.items():
        body+=f'\nJourney_GymGuide_Event{event}::\n\tmsgbox Journey_GymGuide_Text{event}, MSGBOX_DEFAULT\n\trelease\n\tend\n'
        body+=text(f'Journey_GymGuide_Text{event}',['The GYM LEADER is busy','helping fight '+team+'!']+lines)
    stage(path,body)

    # Reject an early Silph boss fight without blocking access to Saffron/routes.
    path='data/maps/SilphCo_11F_Frlg/scripts.inc';body=read(path).decode()
    anchor='SilphCo_11F_EventScript_BattleGiovanni::\n'
    body=body.replace(anchor,anchor+'\tspecial JourneySilphCoPermission\n\tgoto_if_eq VAR_RESULT, FALSE, Journey_SilphTooEarly\n')
    stage(path,body)
    scripts.append('\nJourney_SilphTooEarly::\n\tmsgbox Journey_SilphTooEarly_Text, MSGBOX_DEFAULT\n\treleaseall\n\tend\n'
                   +text('Journey_SilphTooEarly_Text',['GIOVANNI: Finish six KANTO GYMS','and stop the outside incursions.','Then we will settle this.']))

    room=existing('SeafloorCavern_Room9');giovanni_id=len(room['object_events'])+1;shelly_id=giovanni_id+1
    for gfx,x,y in [('OBJ_EVENT_GFX_GIOVANNI',18,42),('OBJ_EVENT_GFX_AQUA_MEMBER_F',16,43)]:
        room['object_events'].append(dict(type='object',graphics_id=gfx,x=x,y=y,elevation=3,
            movement_type='MOVEMENT_TYPE_FACE_LEFT',movement_range_x=0,movement_range_y=0,
            trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',script='0x0',flag='FLAG_HIDE_JOURNEY_ARCHIE_ALLIES'))
    path='include/constants/flags.h';body=read(path).decode()
    body=body.replace('#define JOURNEY_FLAGS_END 0x1ABF','#define FLAG_HIDE_JOURNEY_ARCHIE_ALLIES 0x1ABC\n#define JOURNEY_FLAGS_END 0x1ABF')
    stage(path,body)
    path='src/new_game.c';body=read(path).decode();body=body.replace('    InitEventData();','    InitEventData();\n    FlagSet(FLAG_HIDE_JOURNEY_ARCHIE_ALLIES);',1);stage(path,body)
    path='data/maps/SeafloorCavern_Room9/scripts.inc';body=read(path).decode()
    anchor='SeafloorCavern_Room9_EventScript_ArchieAwakenKyogre::\n\tlockall\n'
    body=body.replace(anchor,anchor+'\tspecial JourneyArchiePermission\n\tgoto_if_eq VAR_RESULT, FALSE, Journey_ArchieTooEarly\n')
    anchor='\ttrainerbattle_no_intro TRAINER_ARCHIE, SeafloorCavern_Room9_Text_ArchieDefeat\n'
    battle=(f'\tclearflag FLAG_HIDE_JOURNEY_ARCHIE_ALLIES\n\taddobject {giovanni_id}\n\taddobject {shelly_id}\n'
            '\tmsgbox Journey_GiovanniRepentance, MSGBOX_DEFAULT\n\tclosemessage\n'
            f'\tmulti_fixed_2_vs_2 {alliance[0]}, SeafloorCavern_Room9_Text_ArchieDefeat, {alliance[1]}, Journey_ShellyDefeat, PARTNER_GIOVANNI\n'
            '\tgoto_if_ne VAR_RESULT, 1, Journey_ArchieAllianceLost\n'
            '\tmsgbox Journey_GiovanniAfterAlliance, MSGBOX_DEFAULT\n\tclosemessage\n'
            f'\tremoveobject {giovanni_id}\n\tremoveobject {shelly_id}\n\tsetflag FLAG_HIDE_JOURNEY_ARCHIE_ALLIES\n')
    if body.count(anchor)!=1:raise ValueError('Unexpected Archie battle')
    stage(path,body.replace(anchor,battle))
    scripts.append('\nJourney_ArchieAllianceLost::\n\tsetflag FLAG_HIDE_JOURNEY_ARCHIE_ALLIES\n\tfadescreen FADE_TO_BLACK\n\tspecial SetCB2WhiteOut\n\twaitstate\n\tend\n'
                   +text('Journey_GiovanniRepentance',GIOVANNI_DIALOGUE)
                   +text('Journey_ShellyDefeat',['We cannot control this world!'])
                   +text('Journey_GiovanniAfterAlliance',['GIOVANNI: Thank you.','I will keep repairing the harm','that TEAM ROCKET has caused.'])
                   +'\nJourney_ArchieTooEarly::\n\tmsgbox Journey_ArchieTooEarly_Text, MSGBOX_DEFAULT\n\treleaseall\n\tend\n'
                   +text('Journey_ArchieTooEarly_Text',['Complete seven HOENN GYMS,','the SPACE CENTER and ROCKET base.','Defeat GIOVANNI at SILPH CO.','He will join you here.']))
    stage('data/scripts/journey_team_stories.inc',''.join(scripts))
    path='data/event_scripts.s';stage(path,read(path).decode()+'\n\t.include "data/scripts/journey_team_stories.inc"\n'
         +''.join(f'\t.include "data/maps/{name}/scripts.inc"\n'for name in new_maps))
    for name,data in maps.items():
        # Templates used only for shoreline reads are not modified.
        if name in ['Route109','Route20_Frlg']:continue
        jstage(f'data/maps/{name}/map.json',data)
    jstage('data/layouts/layouts.json',layouts);jstage('data/maps/map_groups.json',groups)
    for path,raw in outputs.items():
        target=source/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    report=dict(status='integrated_team_story_candidate_not_full_campaign_validation',source_commit=PIN,
        missions=missions,trainers=trainers,casino='MauvilleCity_GameCorner',new_maps=new_maps,
        ocean_design=ocean_design,alliance=dict(partner='PARTNER_GIOVANNI',opponents=alliance,
            giovanni_local_id=giovanni_id,shelly_local_id=shelly_id,requires_silph=True,requires_hoenn_badges=7),
        before_gym_ordinals=dict(kanto=[3,5,7],hoenn=[3,5,6,8,8]),requires_new_save=True,
        preserved_event_sha256=preserved,input_sha256=inputs,original_sha256=originals,
        prepared_sha256={p:hashlib.sha256(raw).hexdigest()for p,raw in outputs.items()},full_story_validated=False)
    marker.write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(prepare(args.source),indent=2))
