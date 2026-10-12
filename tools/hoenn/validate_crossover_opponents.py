"""Inspect compiled crossover teams, legal moves/stages, EVs and battle ability."""
from pathlib import Path
import hashlib,json,re,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_competitive_bosses.py').read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_competitive_bosses.py'),'exec'))
# Story state is a declared fixture here; this test inspects native party creation.
native('VarSet',0x40FE,4)
marker=json.loads((source/'.journey-crossover-opponents').read_text())
checks=[]
for mean in [5,40,70]:
 team([mean]*6)
 for tr in marker['registered_trainers']:
  trainer=base+tr['id']*abi[0];levels=generated(trainer);mons=[]
  assert len(levels)==len(tr['team']),(tr['key'],levels)
  important=bool(native('JourneyCompetitiveAiFlags',tr['id'])&0x80000000)
  assert important==tr['important'],tr['key']
  for i,level in enumerate(levels):
   mon=enemy+i*abi[2];species=data(mon,'MON_DATA_SPECIES');ivs=data(mon,'MON_DATA_IVS');evs=[data(mon,name) for name in fields[1:7]]
   assert max(1,mean-5)<=level<=min(100,mean+2),(tr['key'],mean,level)
   assert native('JourneyTrainerSpecies',species,level)==species,(tr['key'],species,level)
   moves=[native('GetMonData3',mon,values['MON_DATA_MOVE1']+slot,0) for slot in range(4)]
   if important:
    assert ivs&0x3FFFFFFF==0x3FFFFFFF and sum(evs)==510 and max(evs)<=252,(tr['key'],ivs,evs)
    assert all(move in nonlevel[species]|{mid for at,mid in database['species'][species]['learnset'] if at<=level} for move in moves if move),(tr['key'],species,level,moves)
   mons.append(dict(species=species,level=level,evs=evs,ivs=ivs,moves=moves))
  checks.append(dict(trainer=tr['key'],player_mean=mean,important=important,mons=mons))
 print('Crossover parties passed at player mean',mean,flush=True)
with tempfile.TemporaryDirectory(dir='/tmp') as temp:
 p=Path(temp);(p/'probe.c').write_text('#include "global.h"\n#include "battle_setup.h"\n#include "constants/abilities.h"\n#include <stddef.h>\nconst u32 opponent_offset=offsetof(TrainerBattleParameter,params.opponentA);\nconst u32 mold_breaker=ABILITY_MOLD_BREAKER;\n')
 subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-iquote',str(source/'include'),'-mabi=apcs-gnu',str(p/'probe.c'),'-o',str(p/'probe.s')],check=True)
 asm=(p/'probe.s').read_text();offset=int(re.search(r'opponent_offset:\s*\.word\s+(\d+)',asm)[1]);mold=int(re.search(r'mold_breaker:\s*\.word\s+(\d+)',asm)[1])
team([70]*6);generated(base+ids['TRAINER_JOURNEY_EREN_6']*abi[0])
lib.write16(s['gTrainerBattleParameter']+offset,ids['TRAINER_JOURNEY_EREN_6'])
old_battle_flags=lib.read32(s['gBattleTypeFlags']);lib.write32(s['gBattleTypeFlags'],old_battle_flags|abi[10])
ability=native('GetMonAbility',enemy+5*abi[2]);assert ability==mold,(ability,mold)
lib.write32(s['gBattleTypeFlags'],old_battle_flags&~abi[10]);assert native('GetMonAbility',enemy+5*abi[2])!=mold
lib.write32(s['gBattleTypeFlags'],old_battle_flags|abi[10])
lib.write16(s['gTrainerBattleParameter']+offset,ids['TRAINER_JOURNEY_LUFFY_6'])
assert native('GetMonAbility',enemy+5*abi[2])!=mold
lib.write32(s['gBattleTypeFlags'],old_battle_flags)
progress=[]
for mask in [0,1,0b101010,0b111111,0b101010000000,0b111111111111]:
 native('VarSet',0x40FF,mask)
 counts=[native('JourneyCrossoverCount',hero) for hero in [0,1]]
 assert counts==[(mask&63).bit_count(),((mask>>6)&63).bit_count()],(mask,counts)
 progress.append(dict(mask=mask,counts=counts))
assert hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()==initial_sha
lib.stop()
(args.output/'crossover-opponents.json').write_text(json.dumps(dict(passed=True,rom_sha256=initial_sha,checks=checks,progress=progress,eren_regigigas_battle_only_mold_breaker=True,ordinary_grunts_not_competitive=True,party_creation_native=True,story_progress_fixture=True,full_chapter_playthrough=False),indent=2)+'\n')
print('Native crossover rosters, independent counters and ability exception passed',flush=True)
