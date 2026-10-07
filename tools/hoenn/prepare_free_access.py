"""Ninth overlay: remove terrestrial HM obstacles and fixed gym-order doors.

Story completion flags and trainer flags are not awarded to open roads.
Water terrain and both regional League requirements remain intact.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
from prepare_crossing import PIN

LAYERS=['hoenn-crossing','worldsea','westsea','region-state','east-coast','gym-scaling','campaign-gates','team-stories']
HM_SCRIPTS={'EventScript_CutTree','EventScript_RockSmash','EventScript_StrengthBoulder'}

def prepare(source):
    source=Path(source);marker=source/'.journey-free-access'
    if marker.exists():
        report=json.loads(marker.read_text())
        for path,digest in report['prepared_sha256'].items():
            if hashlib.sha256((source/path).read_bytes()).hexdigest()!=digest:raise ValueError('Modified access output: '+path)
        return report
    acquired=json.loads((source/'.source-acquired.json').read_text())
    if acquired['commit']!=PIN:raise ValueError('Unexpected base')
    expected=dict(acquired['sha256'])
    for layer in LAYERS:expected.update(json.loads((source/f'.journey-{layer}').read_text())['prepared_sha256'])
    outputs={};originals={};inputs={}
    def read(path):
        if path in outputs:return outputs[path]
        raw=(source/path).read_bytes();digest=hashlib.sha256(raw).hexdigest()
        if digest!=expected.get(path):raise ValueError('Unreviewed access input: '+path)
        if path in acquired['sha256']:inputs[path]=acquired['sha256'][path]
        return raw
    def stage(path,value):
        if path not in originals:
            original=(source/path).read_bytes()if(source/path).exists()else None
            digest=hashlib.sha256(original).hexdigest()if original is not None else None
            if digest is not None and digest!=expected.get(path):raise ValueError('Unreviewed output: '+path)
            originals[path]=digest
        outputs[path]=value if isinstance(value,bytes)else value.encode()
    def edit(path,old,new):
        body=read(path).decode()
        if body.count(old)!=1:raise ValueError('Ambiguous replacement: '+path+' '+old[:70])
        stage(path,body.replace(old,new))
    layouts={l['id']:l for l in json.loads(read('data/layouts/layouts.json'))['layouts']}
    changes=[];obstacles=[];flash=[];relocations=[];maps={}
    # Audit every original map JSON, including unchanged maps, so reproduction
    # cannot silently miss another obstacle. Templates retain implicit local IDs.
    paths=sorted({p for p in acquired['sha256']if p.startswith('data/maps/')and p.endswith('/map.json')}
                 |{p for p in expected if p.startswith('data/maps/Journey')and p.endswith('/map.json')})
    for path in paths:
        data=json.loads(read(path));name=data['name'];before=json.loads(json.dumps(data))
        for index,obj in enumerate(data.get('object_events',[])):
            if obj.get('script')in HM_SCRIPTS:
                obstacles.append(dict(map=name,local_id=index+1,x=obj['x'],y=obj['y'],script=obj['script']))
                obj['flag']='FLAG_HIDE_JOURNEY_LAND_OBSTACLES'
        if data.get('requires_flash'):
            data['requires_flash']=False;flash.append(name)
        maps[name]=data
        if data!=before:
            changes.append(dict(map=name,before=before,after=json.loads(json.dumps(data))))
            stage(path,json.dumps(data,indent=2)+'\n')
    # Move guards away from entrances, retaining their scripts and visibility.
    # Leave city story flags untouched: moving a guard is not defeating a boss.
    requests={'SaffronCity_Frlg':[3,6],'Route112':[1,6]}
    for name,ids in requests.items():
        data=maps[name];before=json.loads(json.dumps(data));layout=layouts[data['layout']]
        raw=read(layout['blockdata_filepath']);values=struct.unpack('<'+'H'*(len(raw)//2),raw)
        occupied={(o['x'],o['y'])for k in ['object_events','warp_events','coord_events','bg_events']for o in data.get(k,[])}
        for local_id in ids:
            obj=data['object_events'][local_id-1];x0,y0=obj['x'],obj['y'];candidates=[]
            for y in range(max(1,y0-5),min(layout['height']-1,y0+6)):
                for x in range(max(1,x0-5),min(layout['width']-1,x0+6)):
                    tile=values[y*layout['width']+x]
                    if abs(x-x0)+abs(y-y0)<2 or (x,y)in occupied or tile&0xC00 or tile>>12!=3:continue
                    if sum(not(values[yy*layout['width']+xx]&0xC00)and values[yy*layout['width']+xx]>>12==3 for xx,yy in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)])<3:continue
                    candidates.append((abs(x-x0)+abs(y-y0),y,x))
            if not candidates:raise ValueError('No safe guard position: '+name)
            _,y,x=min(candidates);obj['x']=x;obj['y']=y;occupied.add((x,y))
            relocations.append(dict(map=name,local_id=local_id,before=[x0,y0],after=[x,y]))
        changes.append(dict(map=name,before=before,after=json.loads(json.dumps(data))))
        stage(f'data/maps/{name}/map.json',json.dumps(data,indent=2)+'\n')
    path='include/constants/flags.h'
    edit(path,'#define FLAG_HIDE_JOURNEY_ARCHIE_ALLIES 0x1ABC','#define FLAG_HIDE_JOURNEY_LAND_OBSTACLES 0x1ABB\n#define FLAG_HIDE_JOURNEY_ARCHIE_ALLIES 0x1ABC')
    # These are access/puzzle states, not team victories or badge awards.
    init='''    FlagSet(FLAG_HIDE_JOURNEY_LAND_OBSTACLES);
    FlagSet(FLAG_KECLEON_FLED_FORTREE);
    FlagSet(FLAG_STOPPED_SEAFOAM_B3F_CURRENT);
    FlagSet(FLAG_STOPPED_SEAFOAM_B4F_CURRENT);
    VarSet(VAR_MAP_SCENE_ROUTE5_ROUTE6_ROUTE7_ROUTE8_GATES, 1);
    VarSet(VAR_MAP_SCENE_VIRIDIAN_CITY_OLD_MAN, 2);
'''
    edit('src/new_game.c','    FlagSet(FLAG_HIDE_JOURNEY_ARCHIE_ALLIES);','    FlagSet(FLAG_HIDE_JOURNEY_ARCHIE_ALLIES);\n'+init)
    # Surf and Waterfall require the move, but not a fixed gym's badge. Dive's
    # badge/story rule and all actual water terrain are left unchanged.
    path='src/field_move.c';body=read(path).decode()
    for name in ['Surf','Waterfall']:
        body,n=re.subn(r'static bool32 IsFieldMoveUnlocked_'+name+r'\(void\)\n\{.*?\n\}',
                       'static bool32 IsFieldMoveUnlocked_'+name+'(void)\n{\n    return TRUE;\n}',body,flags=re.S)
        if n!=1:raise ValueError('Missing field permission '+name)
    stage(path,body)
    path='data/maps/ViridianCity_Frlg/scripts.inc';body=read(path).decode()
    for badge in range(2,8):body=body.replace(f'\tgoto_if_unset FLAG_BADGE0{badge}_GET, Common_EventScript_NopReturn\n','')
    stage(path,body)
    edit('data/maps/CinnabarIsland_Frlg/scripts.inc',
         '\tgoto_if_set FLAG_HIDE_POKEMON_MANSION_B1F_SECRET_KEY, CinnabarIsland_EventScript_UnlockGym',
         '\tgoto CinnabarIsland_EventScript_UnlockGym')
    # Keep Wally's tutorial; after it Norman accepts any number of badges.
    path='data/maps/PetalburgCity_Gym/scripts.inc'
    edit(path,'PetalburgCity_Gym_OnLoad:\n','PetalburgCity_Gym_OnLoad:\n\tcall Journey_NormanReady\n')
    edit(path,'\tsetvar VAR_PETALBURG_GYM_STATE, 2\n','\tsetvar VAR_PETALBURG_GYM_STATE, 6\n')
    stage(path,read(path).decode()+'''\nJourney_NormanReady::
\tgoto_if_lt VAR_PETALBURG_GYM_STATE, 2, Common_EventScript_NopReturn
\tgoto_if_ge VAR_PETALBURG_GYM_STATE, 6, Common_EventScript_NopReturn
\tsetvar VAR_PETALBURG_GYM_STATE, 6
\treturn
''')
    # The old dialogue must not advertise four badges after removing that gate.
    path='data/maps/PetalburgCity_Gym/scripts.inc';body=read(path).decode()
    for label,lines in {
        'DadGoCollectBadges':['DAD: Choose any HOENN GYM.','You may challenge me now, too!'],
        'NormanIntro':['DAD: You are ready to battle.','Our teams will match the','progress of your journey.','Give this battle your best!'],
    }.items():
        key='PetalburgCity_Gym_Text_'+label
        replacement=key+':\n'+''.join('\t.string "'+line+('$'if i==len(lines)-1 else '\\n')+'"\n'for i,line in enumerate(lines))+'\n'
        body,n=re.subn(key+r':\n.*?(?=\n\w+:|\Z)',lambda m:replacement,body,flags=re.S)
        if n!=1:raise ValueError('Missing Norman text')
    stage(path,body)
    # Only the journey guide gates Sootopolis's gym; preserve weather scenes.
    path='data/maps/SootopolisCity/scripts.inc'
    edit(path,'\tcall_if_unset FLAG_SOOTOPOLIS_ARCHIE_MAXIE_LEAVE, SootopolisCity_EventScript_LockGymDoor\n','')
    layout=layouts[maps['SootopolisCity']['layout']];raw=read(layout['blockdata_filepath']);tile=struct.unpack_from('<H',raw,(32*layout['width']+31)*2)[0]&1023
    edit(path,'\tcall SootopolisCity_EventScript_SetLayout\n',f'\tcall SootopolisCity_EventScript_SetLayout\n\tsetmetatile 31, 32, {tile}, FALSE\n')
    path='data/maps/SootopolisCity_Gym_1F/scripts.inc';body=read(path).decode()
    body=re.sub(r'^\tgoto_if_unset FLAG_BADGE06_GET, .*\n','',body,flags=re.M);stage(path,body)
    # Open the boulder switches directly: hiding rocks alone must not leave
    # their terrain barriers in place. No trainers/items/legendaries are cleared.
    for floor,variables,coords in [(1,['VAR_MAP_SCENE_VICTORY_ROAD_1F'],[(12,14)]),
        (2,['VAR_MAP_SCENE_VICTORY_ROAD_2F_BOULDER1','VAR_MAP_SCENE_VICTORY_ROAD_2F_BOULDER2'],[(13,10),(33,16)]),
        (3,['VAR_MAP_SCENE_VICTORY_ROAD_3F'],[(12,12)])]:
        path=f'data/maps/VictoryRoad_{floor}F_Frlg/scripts.inc';body=read(path).decode()
        for var in variables:body=re.sub(r'^\tcall_if_ne '+var+r', 100, .*\n',f'\tsetvar {var}, 100\n',body,flags=re.M)
        anchor='\tend\n';extra=''.join(f'\tsetmetatile {x}, {y}, METATILE_Cave_Floor_Ledge_Top, FALSE\n\tsetmetatile {x}, {y+1}, METATILE_Cave_Floor_Ledge_Bottom, FALSE\n'for x,y in coords)
        body=body.replace(anchor,extra+anchor,1);stage(path,body)
    # The sea remains traversable without pretending the Aqua hideout is won.
    edit('data/maps/LilycoveCity/scripts.inc','\tcall_if_unset FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE, LilycoveCity_EventScript_SetWailmerMetatiles\n','')
    edit('data/maps/Route111/scripts.inc','\tgoto_if_eq VAR_RESULT, FALSE, Route111_EventScript_PreventRouteAccess\n','')
    for path,raw in outputs.items():
        target=source/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    # Store only actual field edits, keeping the review manifest readable.
    field_changes=[]
    for change in changes:
        before,after=change['before'],change['after']
        for key in before:
            if before[key]==after[key]:continue
            if key=='object_events':
                if len(before[key])!=len(after[key]):raise ValueError('Access must preserve event IDs')
                for i,(old,new)in enumerate(zip(before[key],after[key])):
                    for field in old:
                        if old[field]!=new[field]:field_changes.append(dict(map=change['map'],path=[key,i,field],before=old[field],after=new[field]))
            else:field_changes.append(dict(map=change['map'],path=[key],before=before[key],after=after[key]))
    report=dict(status='free_access_candidate_not_full_campaign_validation',source_commit=PIN,obstacles=obstacles,
                dark_maps=flash,relocations=relocations,event_changes=field_changes,water_moves=dict(surf='move_only',waterfall='move_only',dive='unchanged'),
                leagues='eight_badges_of_own_region_unchanged',norman_tutorial_preserved=True,
                requires_new_save=True,full_story_validated=False,input_sha256=inputs,original_sha256=originals,
                prepared_sha256={p:hashlib.sha256(raw).hexdigest()for p,raw in outputs.items()})
    marker.write_text(json.dumps(report,indent=2)+'\n');return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True)
    args=parser.parse_args();report=prepare(args.source);print(json.dumps(dict(obstacles=len(report['obstacles']),maps=len({o['map']for o in report['obstacles']}),outputs=len(report['prepared_sha256']))))
