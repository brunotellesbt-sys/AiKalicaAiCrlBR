"""Generate all sixteen native leaders at every rank and player party size.
Initial player party, badge banks and map positions are fixtures.
"""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_trainer_levels.py'),'exec'))
scaling=json.loads((source/'.journey-gym-scaling').read_text())
leaders={}
for gym in scaling['gyms']:
 g,num=map_id(gym['map']);lib.write8(save()+4,g);lib.write8(save()+5,num)
 for name in gym['trainers'] + (['TRAINER_NORMAN_1'] if gym['map']=='PetalburgCity_Gym' else []):
  if name=='TRAINER_LEADER_GIOVANNI':name='TRAINER_JOURNEY_BLUE'
  trainer=base+ids[name]*abi[0]
  if lib.read8(trainer+abi[4]) in [abi[8],abi[9]]:leaders[name]=(gym,trainer)
assert len(leaders)==16,len(leaders)
with tempfile.TemporaryDirectory(dir='/tmp',prefix='gym-egg-abi-') as tmp:
 p=Path(tmp);(p/'egg.c').write_text('#include "global.h"\n#include "pokemon.h"\nconst u32 egg_field=MON_DATA_IS_EGG;\nconst u32 move_field=MON_DATA_MOVE1;\n')
 subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-iquote',str(source/'include'),'-mabi=apcs-gnu',str(p/'egg.c'),'-o',str(p/'egg.s')],check=True)
 egg_field=int(re.search(r'egg_field:\s*\.word\s+(\d+)',(p/'egg.s').read_text())[1])
 move_field=int(re.search(r'move_field:\s*\.word\s+(\d+)',(p/'egg.s').read_text())[1])
from audit_battle_database import compiled
database=compiled(source)
checks=[];egg_checks=0;move_checks=0
# Signature families are specified independently of the generated party helper.
ace_families={
 'LEADER_BROCK':['ONIX'], 'LEADER_MISTY':['STARYU','STARMIE'],
 'LEADER_LT_SURGE':['PIKACHU','RAICHU'], 'LEADER_ERIKA':['ODDISH','GLOOM','VILEPLUME'],
 'LEADER_KOGA':['KOFFING','WEEZING'], 'LEADER_SABRINA':['ABRA','KADABRA','ALAKAZAM'],
 'LEADER_BLAINE':['GROWLITHE','ARCANINE'], 'JOURNEY_BLUE':['PIDGEY','PIDGEOTTO','PIDGEOT'],
 'ROXANNE_1':['NOSEPASS'], 'BRAWLY_1':['MAKUHITA','HARIYAMA'],
 'WATTSON_1':['ELECTRIKE','MANECTRIC'], 'FLANNERY_1':['TORKOAL'],
 'NORMAN_1':['SLAKOTH','VIGOROTH','SLAKING'], 'WINONA_1':['SWABLU','ALTARIA'],
 'TATE_AND_LIZA_1':['SOLROCK'], 'JUAN_1':['HORSEA','SEADRA','KINGDRA']}
species_names={int(sid):row['name'].removeprefix('SPECIES_') for sid,row in json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text())['species'].items()}

for name,(gym,trainer) in leaders.items():
 g,num=map_id(gym['map']);lib.write8(save()+4,g);lib.write8(save()+5,num);lib.write8(s['isFrlg'],int(gym['kanto']))
 for rank in range(8):
  for bank,count in [(kanto_flags,rank if gym['kanto'] else 7-rank),(hoenn_flags,7-rank if gym['kanto'] else rank)]:
   for i,f in enumerate(bank):rawflag(f,i<count)
  ace=None
  for players in range(1,7):
   team([6]*players);levels=generated(trainer)
   expected=6 if rank>=4 else rank+2+(players>rank+2)
   assert len(levels)==expected,(name,rank,players,levels,expected)
   assert levels[-1]==scaling['ace_levels'][rank],(name,rank,levels)
   assert levels[:-1]==[scaling['ace_levels'][rank]-min(3,i+1) for i in range(expected-1)]
   species=[native('GetMonData3',enemy+i*abi[2],abi[7],0) for i in range(expected)]
   assert species_names[species[-1]] in ace_families[name.removeprefix("TRAINER_")],(name,species)
   if name=="TRAINER_TATE_AND_LIZA_1":assert "LUNATONE" in [species_names[sid] for sid in species]
   for index,(sid,level) in enumerate(zip(species,levels)):
    moveset=[native('GetMonData3',enemy+index*abi[2],move_field+slot,0) for slot in range(4)]
    available={move for at,move in database['species'][sid]['learnset'] if at<=level}
    if species_names[sid]=='ABRA':available.add(237) # Native Hidden Power TM ID.
    assert all(move in available for move in moveset if move),(name,rank,sid,level,moveset)
    limit=60 if level<20 else 80 if level<30 else 100 if level<42 else 140
    assert database['moves'][moveset[0]]['power']>=2,(name,sid,moveset)
    assert all(database['moves'][move]['power']<=limit for move in moveset if move),(name,rank,moveset)
    move_checks+=1
   if ace is None:ace=species[-1]
   assert species[-1]==ace,(name,rank,players,species)
   assert len(set(species))==expected,(name,species)
   checks.append(dict(leader=name,kanto=gym['kanto'],rank=rank+1,player_count=players,enemy_count=expected,levels=levels,species=species,ace=ace))
  team([6]*6)
  for i in range(2,6):
   lib.write8(scratch,1);native('SetMonData',party+i*abi[2],egg_field,scratch)
  assert len(generated(trainer))==(6 if rank>=4 else rank+2),(name,rank,'egg count')
  egg_checks+=1
 print('Adaptive native leader passed:',name,flush=True)
lib.stop()
(args.output/'adaptive-gym-teams.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),leaders=len(leaders),cases=len(checks),egg_cases=egg_checks,move_cases=move_checks,checks=checks,regional_badge_banks_independent=True,signature_preserved_across_party_sizes=True,initial_state_is_fixture=True,enemy_party_not_written=True,full_campaign_playthrough=False),indent=2)+'\n')
