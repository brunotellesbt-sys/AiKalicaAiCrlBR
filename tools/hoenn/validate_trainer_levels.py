"""Generate native ordinary and gym parties; reproduce the low-level Route125 battle."""
from pathlib import Path
import hashlib,json,re,struct
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_team_missions.py').read_text().split('\nassert pending(True) == 7')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_team_missions.py'),'exec'))
ids={}
for path in ['include/constants/opponents.h','include/constants/opponents_frlg.h']:
    ids.update({n:int(v) for n,v in re.findall(r'#define\s+(TRAINER_\w+)\s+(\d+)\b',(source/path).read_text())})
base=s['gTrainers']+abi[12]*abi[11]*abi[0]
def team(levels):
    for i in range(6*abi[2]):lib.write8(party+i,0)
    lib.write8(s['gPartiesCount'],0)
    for level in levels:assert native('ScriptGiveMon',abi[54],level,0)==0
def generated(trainer):
    count=native('CreateNPCTrainerPartyFromTrainer',enemy,trainer,0,abi[10])
    return [native('GetMonData3',enemy+i*abi[2],abi[6],0) for i in range(count)]
checks=[]
for levels in [[6],[1],[100],[5,20,50],[10,10,20,20,30,30]]:
    team(levels);mean=sum(levels)//len(levels)
    for n in ['Route125','Route1_Frlg']:
        g,num=map_id(n);lib.write8(save()+4,g);lib.write8(save()+5,num)
        lib.write8(s['isFrlg'],int(n.endswith('_Frlg')))
        tested=0
        # Every normal-difficulty trainer uses this native generation path.
        for i in range(1,abi[11]):
            trainer=base+i*abi[0]
            result=generated(trainer)
            assert all(max(1,mean-5)<=v<=min(100,mean+2) for v in result),(n,i,levels,result)
            tested+=1
        checks.append(dict(map=n,player_levels=levels,mean=mean,trainer_parties=tested))
    print('Ordinary trainer parties passed at mean',mean,flush=True)
# Preserve the regional gym rank table, independent of the other badge bank.
team([6]);scaling=json.loads((source/'.journey-gym-scaling').read_text());gym_count=0
for gym in scaling['gyms']:
    g,num=map_id(gym['map']);lib.write8(save()+4,g);lib.write8(save()+5,num)
    lib.write8(s['isFrlg'],int(gym['kanto']))
    for rank in range(8):
        for bank,count in [(kanto_flags,rank if gym['kanto'] else 7-rank),(hoenn_flags,7-rank if gym['kanto'] else rank)]:
            for i,f in enumerate(bank):rawflag(f,i<count)
        for name in gym['trainers'] + (['TRAINER_NORMAN_1'] if gym['map']=='PetalburgCity_Gym' else []):
            if name=='TRAINER_LEADER_GIOVANNI':name='TRAINER_JOURNEY_BLUE'
            trainer=base+ids[name]*abi[0];pointer=lib.read32(trainer+abi[3]);result=generated(trainer)
            leader=lib.read8(trainer+abi[4]) in [abi[8],abi[9]]
            highest=0 if leader else max(lib.read8(pointer+i*abi[1]+abi[5]) for i in range(len(result)))
            for i,actual in enumerate(result):
                original=0 if leader else lib.read8(pointer+i*abi[1]+abi[5])
                expected=scaling['ace_levels'][rank]-(0 if i == len(result)-1 else min(3,i+1)) if leader else scaling['ace_levels'][rank]-min(6,highest-original)-2
                assert actual==expected,(gym['map'],rank,name,actual,expected)
            gym_count+=1
print('Regional gym parties passed:',gym_count,flush=True)
# Actual original Route125 NPC script, no direct writes to enemy levels.
team([6]);warp('Route125',50,25)
scripts=(source/'data/maps/Route125/scripts.inc').read_text()
trainer_names=re.findall(r'trainerbattle_single\s+(TRAINER_\w+)',scripts)
tropius=None
for name in trainer_names:
    trainer=base+ids[name]*abi[0];p=lib.read32(trainer+abi[3])
    # Species is at the beginning of the pinned TrainerMon structure.
    count=generated(trainer)
    if any(native('GetMonData3',enemy+i*abi[2],abi[7],0)==357 for i in range(len(count))):tropius=name;break
assert tropius,'Original Route125 Tropius trainer missing'
label=re.search(r'(Route125_EventScript_\w+)::\s*trainerbattle_single\s+'+tropius,scripts)[1]
rawflag(0x500+ids[tropius],False)
script(b'\x05'+struct.pack('<I',s[label]),30)
for _ in range(500):
    press(1)
    if lib.read32(s['gMain']+4)&~1==s['BattleMainCB2'] and lib.read16(s['gBattleMons']+abi[74]+abi[75])==357:break
else:raise AssertionError('Route125 Tropius battle did not start')
enemy_level=lib.read8(enemy+pabi[17])
assert 1<=enemy_level<=8,enemy_level
for _ in range(240):
    press(2)
    if any(lib.read32(s['gBattlerControllerFuncs']+i*4)&~1 in actions for i in range(4)):break
else:raise AssertionError('Trainer battle never reached the command menu')
picture('route125-tropius-level-six-party')
lib.stop()
(args.output/'trainer-levels.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),checks=checks,gym_parties=gym_count,all_normal_difficulty_trainers_generated=True,route125_tropius_battle=True,enemy_level=enemy_level,player_level=6,initial_party_and_script_entry_are_fixtures=True,enemy_levels_not_written=True,full_campaign_playthrough=False),indent=2)+'\n')
