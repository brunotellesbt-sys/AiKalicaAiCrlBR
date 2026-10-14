"""Exercise current-party scaling, including ordinary trainers inside both gyms."""
import hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_trainer_levels.py'),'exec'))
checks=[];scaling=json.loads((source/'.journey-gym-scaling').read_text());tested_maps=set()
for levels in [[5],[18,19],[20],[95],[5,10,21]]:
 team(levels);mean=sum(levels)//len(levels)
 for gym in scaling['gyms']:
  g,num=map_id(gym['map']);lib.write8(save()+4,g);lib.write8(save()+5,num);lib.write8(s['isFrlg'],int(gym['kanto']));tested_maps.add(gym['map'])
  for name in gym['trainers']+(['TRAINER_NORMAN_1'] if gym['map']=='PetalburgCity_Gym' else []):
   if name=='TRAINER_LEADER_GIOVANNI':name='TRAINER_JOURNEY_BLUE'
   trainer=base+ids[name]*abi[0];leader=lib.read8(trainer+abi[4]) in [abi[8],abi[9]]
   # Stage the party only; all enemy levels come from the native generator.
   result=generated(trainer);lo=max(1,mean-(1 if leader else 5));hi=min(100,mean+(5 if leader else 2))
   assert result and all(lo<=v<=hi for v in result),(name,mean,result,lo,hi)
   if leader:assert result[-1]==min(100,mean+5),(name,mean,result)
   for i,level in enumerate(result):
    species=native('GetMonData3',enemy+i*abi[2],abi[7],0);assert native('JourneyTrainerSpecies',species,level)==species,(name,species,level)
   checks.append(dict(map=gym['map'],trainer=name,leader=leader,player_levels=levels,mean=mean,enemy_levels=result))
 print('Live gym/common levels passed at mean',mean,flush=True)
# Read an actual double-gym entry at the reported player's levels.
team([18,19])
for bank in [kanto_flags,hoenn_flags]:
 for flag in bank:rawflag(flag,False)
rawflag(0x500+ids['TRAINER_TATE_AND_LIZA_1'],False);warp('MossdeepCity_Gym',11,5)
script(b'\x05'+struct.pack('<I',s['MossdeepCity_Gym_EventScript_TateAndLiza']),30)
for _ in range(300):
 if lib.read32(s['gMain']+4)&~1==s['BattleMainCB2'] and lib.read8(s['gPartiesCount']+1)==2:break
 press(1)
else:raise AssertionError('Tate/Liza battle entry')
actual=[lib.read8(enemy+i*abi[2]+pabi[17]) for i in range(2)]
assert 17<=actual[0]<=23 and actual[1]==23,actual
step(500)
for _ in range(80):
 press(2)
 if any(lib.read32(s['gBattlerControllerFuncs']+i*4)&~1 in actions for i in range(4)):break
picture('mossdeep-current-levels')
lib.stop();(args.output/'live-levels.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),current_party_mean=True,ace_offset=5,ordinary_offset=[-5,2],leader_offset=[-1,5],maps=sorted(tested_maps),checks=checks,native_generated_parties=True,enemy_levels_written=False,actual_mossdeep_battle_levels=actual,initial_party_badges_and_script_are_fixtures=True,full_campaign_playthrough=False),indent=2)+'\n')
