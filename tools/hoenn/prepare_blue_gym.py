"""Replace Viridian's Rocket boss with Blue, retaining regional gym scaling."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from prepare_crossing import PIN
from prepare_free_access import LAYERS

def prepare(source):
    source=Path(source);marker=source/'.journey-blue-gym'
    if marker.exists():
        result=json.loads(marker.read_text())
        for p,d in result['prepared_sha256'].items():
            if hashlib.sha256((source/p).read_bytes()).hexdigest()!=d:raise ValueError('Modified Blue output: '+p)
        return result
    acquired=json.loads((source/'.source-acquired.json').read_text());assert acquired['commit']==PIN
    expected=dict(acquired['sha256'])
    for layer in LAYERS+['free-access']:expected.update(json.loads((source/f'.journey-{layer}').read_text())['prepared_sha256'])
    inputs={};originals={};outputs={}
    def read(path):
        if path in outputs:return outputs[path]
        raw=(source/path).read_bytes();assert hashlib.sha256(raw).hexdigest()==expected[path],path
        if path in acquired['sha256']:inputs[path]=acquired['sha256'][path]
        return raw
    def stage(path,body):
        if path not in originals:originals[path]=hashlib.sha256(read(path)).hexdigest()
        outputs[path]=body if isinstance(body,bytes)else body.encode()
    name='TRAINER_JOURNEY_BLUE';number=1550
    path='include/constants/opponents.h';body=read(path).decode()
    assert '#define TRAINERS_COUNT                      1550'in body
    body=body.replace('#define TRAINERS_COUNT                      1550','#define TRAINERS_COUNT                      1551')
    body=body.replace('#endif  // GUARD_CONSTANTS_OPPONENTS_H',f'#define {name} {number}\n\n#endif  // GUARD_CONSTANTS_OPPONENTS_H');stage(path,body)
    path='src/data/trainers.party'
    party=f'\n=== {name} ===\nName: BLUE\nClass: Leader Frlg\nPic: Champion Rival Frlg\nGender: Male\nMusic: Male\nAI: Basic Trainer\n'
    for species,level in [('Pidgeot',60),('Alakazam',58),('Rhydon',58),('Exeggutor',58),('Gyarados',58),('Arcanine',60)]:
        party+=f'\n{species}\nLevel: {level}\nIVs: 25 HP / 25 Atk / 25 Def / 25 SpA / 25 SpD / 25 Spe\n'
    stage(path,read(path).decode()+party)
    path='data/maps/ViridianCity_Gym_Frlg/map.json';data=json.loads(read(path));before=json.loads(json.dumps(data))
    found=[o for o in data['object_events']if o.get('script')=='ViridianCity_Gym_EventScript_Giovanni'];assert len(found)==1
    found[0]['graphics_id']='OBJ_EVENT_GFX_BLUE';stage(path,json.dumps(data,indent=2)+'\n')
    path='data/maps/ViridianCity_Gym_Frlg/scripts.inc';body=read(path).decode()
    body=body.replace('TRAINER_LEADER_GIOVANNI,',name+',')
    body=re.sub(r'^\tfamechecker FAMECHECKER_GIOVANNI.*\n','',body,flags=re.M)
    for line in ['\tsetflag FLAG_HIDE_MISC_KANTO_ROCKETS\n','\tsetvar VAR_MAP_SCENE_ROUTE22, 3\n',
                 '\tfadescreen FADE_TO_BLACK\n','\tremoveobject LOCALID_VIRIDIAN_GIOVANNI\n','\tfadescreen FADE_FROM_BLACK\n']:
        body=body.replace(line,'')
    texts={'GiovanniIntro':['BLUE: I lead this GYM now.','Challenge us in any order.','Show me how far you have come!'],
           'GiovanniDefeat':['That was an excellent battle!','You earned the EARTHBADGE!','{PAUSE_MUSIC}{PLAY_BGM}{MUS_OBTAIN_BADGE}{PAUSE 0xFE}{PAUSE 0x56}{RESUME_MUSIC}'],
           'GiovanniPostBattle':['Keep training your team.','All eight KANTO badges are','needed for the KANTO LEAGUE.'],
           'ExplainEarthBadgeTakeThis':['You earned the EARTHBADGE.','Collect all eight KANTO badges','to challenge our LEAGUE.','Take this EARTHQUAKE TM!'],
           'ReceivedTM26FromGiovanni':['{PLAYER} received TM26','from BLUE.'],
           'ExplainTM26':['TM26 contains EARTHQUAKE.','A powerful move for your team!']}
    for label,lines in texts.items():
        key='ViridianCity_Gym_Text_'+label
        replacement=key+'::\n'+''.join('\t.string "'+line+('$'if i==len(lines)-1 else '\\n'if i%2==0 else '\\p')+'"\n'for i,line in enumerate(lines))+'\n'
        body,n=re.subn(key+r'::\n.*?(?=\n\w+::|\Z)',lambda m:replacement,body,flags=re.S);assert n==1,key
    # Legacy event/flag labels are retained for compatibility, but player text
    # must no longer describe Blue as Rocket or Giovanni.
    body=re.sub(r'^(\s*\.string ".*)GIOVANNI',r'\1BLUE',body,flags=re.M)
    stage(path,body)
    path='src/journey_campaign_gates.c';body=read(path).decode()
    anchor='    u32 gate;\n'
    assert body.count(anchor)==1
    stage(path,body.replace(anchor,anchor+'''    if (isFrlg && JourneyGymBadgeCount(TRUE) == 8
        && VarGet(VAR_MAP_SCENE_ROUTE22) < 3)
        VarSet(VAR_MAP_SCENE_ROUTE22, 3);
'''))
    for path,raw in outputs.items():(source/path).write_bytes(raw)
    result=dict(status='blue_gym_candidate',source_commit=PIN,trainer=name,trainer_id=number,
        gym='ViridianCity_Gym_Frlg',leader='Blue',team_rocket_event=False,scaling='existing_regional_rank',
        blue_remains_after_victory=True,route22_final_rival_requires_all_kanto_badges=True,
        event_changes=[dict(map='ViridianCity_Gym_Frlg',before=before,after=data)],
        input_sha256=inputs,original_sha256=originals,prepared_sha256={p:hashlib.sha256(raw).hexdigest()for p,raw in outputs.items()},full_story_validated=False)
    marker.write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(prepare(args.source),indent=2))
