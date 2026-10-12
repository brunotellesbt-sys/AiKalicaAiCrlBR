"""Inspect real generated boss parties, EVs, IVs, moves and active battle AI."""
from pathlib import Path
import hashlib,json,re,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_trainer_levels.py'),'exec'))
initial_sha=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()
with tempfile.TemporaryDirectory(dir='/tmp') as temp:
 p=Path(temp);fields=['MON_DATA_IVS','MON_DATA_HP_EV','MON_DATA_ATK_EV','MON_DATA_DEF_EV','MON_DATA_SPATK_EV','MON_DATA_SPDEF_EV','MON_DATA_SPEED_EV','MON_DATA_MOVE1','MON_DATA_HELD_ITEM','MON_DATA_ABILITY_NUM','MON_DATA_SPECIES','MON_DATA_LEVEL']
 code='#include "global.h"\n#include "pokemon.h"\n#include "battle.h"\n#include <stddef.h>\n'+''.join('const u32 field_'+str(i)+'='+name+';\n' for i,name in enumerate(fields))+'const u32 ai_offset=offsetof(struct AiThinkingStruct,aiFlags);\n'
 (p/'fields.c').write_text(code);subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-iquote',str(source/'include'),'-mabi=apcs-gnu',str(p/'fields.c'),'-o',str(p/'fields.s')],check=True)
 asm=(p/'fields.s').read_text();values={name:int(re.search('field_'+str(i)+r':\s*\.word\s+(\d+)',asm)[1]) for i,name in enumerate(fields)};ai_offset=int(re.search(r'ai_offset:\s*\.word\s+(\d+)',asm)[1])
def data(mon,name):return native('GetMonData3',mon,values[name],0)
warp('OldaleTown_PokemonCenter_1F',3,6)
from audit_battle_database import compiled,compiled_teachable_and_egg_moves
database=compiled(source);nonlevel=compiled_teachable_and_egg_moves(source)
checks=[]
scaling=json.loads((source/'.journey-gym-scaling').read_text())
for gym in scaling['gyms']:
 g,num=map_id(gym['map']);lib.write8(save()+4,g);lib.write8(save()+5,num);lib.write8(s['isFrlg'],int(gym['kanto']))
 candidates=gym['trainers']+(['TRAINER_NORMAN_1'] if gym['map']=='PetalburgCity_Gym' else [])
 for rank,players in [(rank,2 if rank==0 else 6) for rank in range(8)]:
  for bank,cnt in [(kanto_flags,rank if gym['kanto'] else 0),(hoenn_flags,0 if gym['kanto'] else rank)]:
   for i,flag in enumerate(bank):rawflag(flag,i<cnt)
  team([25]*players)
  for name in candidates:
   if name=='TRAINER_LEADER_GIOVANNI':name='TRAINER_JOURNEY_BLUE'
   trainer=base+ids[name]*abi[0];levels=generated(trainer)
   important=bool(native('JourneyCompetitiveAiFlags',ids[name])&0x80000000)
   if not important:continue
   mons=[]
   for i,level in enumerate(levels):
    mon=enemy+i*abi[2];species=data(mon,'MON_DATA_SPECIES');ivs=data(mon,'MON_DATA_IVS');evs=[data(mon,name) for name in fields[1:7]];nature=native('GetNature',mon)
    assert ivs&0x3FFFFFFF==0x3FFFFFFF,(name,ivs)
    assert sum(evs)==510 and all(0<=v<=252 for v in evs),(name,evs)
    moveset=[native('GetMonData3',mon,values['MON_DATA_MOVE1']+slot,0) for slot in range(4)]
    assert any(moveset),(name,species)
    assert all(move in nonlevel[species]|{mid for at,mid in database['species'][species]['learnset'] if at<=level} for move in moveset if move),(name,species,level,moveset)
    mons.append(dict(species=species,level=level,ivs=ivs,evs=evs,nature=nature,moves=moveset,ability=data(mon,'MON_DATA_ABILITY_NUM'),item=data(mon,'MON_DATA_HELD_ITEM')))
   checks.append(dict(map=gym['map'],trainer=name,rank=rank+1,player_count=players,mons=mons))
 print('Competitive gym parties:',gym['map'],flush=True)
# Inspect both full League rosters, including their rematches through shared classes.
team([60]*6)
for region,mapname,names in [('kanto','PokemonLeague_LoreleisRoom_Frlg',['TRAINER_ELITE_FOUR_LORELEI','TRAINER_ELITE_FOUR_BRUNO','TRAINER_ELITE_FOUR_AGATHA','TRAINER_ELITE_FOUR_LANCE','TRAINER_CHAMPION_FIRST_BULBASAUR']),('hoenn','EverGrandeCity_SidneysRoom',['TRAINER_SIDNEY','TRAINER_PHOEBE','TRAINER_GLACIA','TRAINER_DRAKE','TRAINER_WALLACE'])]:
 g,num=map_id(mapname);lib.write8(save()+4,g);lib.write8(save()+5,num)
 for name in names:
  assert name in ids,name
  trainer=base+ids[name]*abi[0];levels=generated(trainer);mons=[]
  assert native('JourneyCompetitiveAiFlags',ids[name])&0x80000000
  for i,level in enumerate(levels):
   mon=enemy+i*abi[2];ivs=data(mon,'MON_DATA_IVS');evs=[data(mon,k) for k in fields[1:7]]
   assert ivs&0x3FFFFFFF==0x3FFFFFFF and sum(evs)==510,(name,ivs,evs)
   mons.append(dict(species=data(mon,'MON_DATA_SPECIES'),level=level,ivs=ivs,evs=evs,nature=native('GetNature',mon)))
  checks.append(dict(map=mapname,trainer=name,mons=mons))
# Enter an actual first Tate/Liza double battle and read the AI flags in RAM.
team([6]*2)
for bank in [kanto_flags,hoenn_flags]:
 for flag in bank:rawflag(flag,False)
rawflag(0x500+ids['TRAINER_TATE_AND_LIZA_1'],False);warp('MossdeepCity_Gym',11,5)
script(b'\x05'+struct.pack('<I',s['MossdeepCity_Gym_EventScript_TateAndLiza']),30)
for _ in range(300):
 if lib.read32(s['gMain']+4)&~1==s['BattleMainCB2'] and lib.read8(s['gPartiesCount']+1)==2:break
 press(1)
else:raise AssertionError('First double gym did not start')
for _ in range(100):
 ptr=lib.read32(s['gAiThinkingStruct'])
 if ptr and lib.read32(ptr+ai_offset+8)&0x80000000:break
 press(2)
else:raise AssertionError('Competitive AI was not active in battle')
actual_ai=lib.read32(ptr+ai_offset+8);assert actual_ai&(1<<26) and actual_ai&(1<<14) and actual_ai&(1<<16)
picture('first-mossdeep-competitive-ai')
assert hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()==initial_sha
lib.stop();(args.output/'competitive-bosses.json').write_text(json.dumps(dict(passed=True,rom_sha256=initial_sha,checks=checks,actual_double_gym_ai=actual_ai,first_gym_two_pokemon=True,ivs=31,ev_budget=510,native_parties_and_ai=True,enemy_party_not_written=True,initial_party_maps_flags_are_fixtures=True),indent=2)+'\n')
