"""Talk to and beat both optional Galactic scouts through native battles.

Initial party, flags and travel are fixtures. Player battle stats are boosted
to finish these two regression checks quickly; this is not a balance test.
"""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_team_missions.py').read_text().split('\nassert pending(True) == 7')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_team_missions.py'),'exec'))
native('VarSet',0x40FE,7)
# Use legal physical Flying coverage: Croagunk can have Dry Skin, so the
# inherited water-only party is unsuitable for a deterministic regression.
aerial=int(re.search(r'\bMOVE_AERIAL_ACE\s*=\s*(\d+)',(source/'include/constants/moves.h').read_text())[1])
for i in range(6*abi[2]):lib.write8(party+i,0)
lib.write8(s['gPartiesCount'],0)
for i in range(3):
 assert native('ScriptGiveMon',149,100,0)==0
 for slot in range(4):native('ScriptSetMonMoveSlot',i,aerial if slot==0 else 0,slot)
with tempfile.TemporaryDirectory(dir='/tmp') as directory:
 p=Path(directory)/'hp.s'
 subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-mabi=apcs-gnu','-iquote',str(source/'include'),'-x','c','-','-o',str(p)],input='#include "global.h"\n#include "pokemon.h"\n#include <stddef.h>\nconst u32 offsets[]={offsetof(struct BattlePokemon,hp),offsetof(struct BattlePokemon,maxHP),offsetof(struct Pokemon,hp),offsetof(struct Pokemon,maxHP)};',text=True,check=True)
 hp,maxhp,partyhp,partymaxhp=[int(v) for v in re.findall(r'\.word\s+(\d+)',p.read_text())]
for tid in [1568,1569]+list(range(1570,1589)):rawflag(0x500+tid,False)
ship_before=[flag(0x500+tid) for tid in range(1570,1589)];wins=[]
for tid,x,y in [(1568,70,60),(1569,45,38)]:
 native('HealPlayerParty');warp('DiglettsCave_B1F_Frlg',x,y-1);step(120)
 # Face and talk to the physical NPC, without injecting its script.
 step(1,128);step(20);press(1);started=False;attacks=0
 for tick in range(2200):
  cb=lib.read32(s['gMain']+4)&~1
  if cb==s['BattleMainCB2']:
   started=True;assert lib.read16(s['gTrainerBattleParameter']+abi[13])==tid
   for b in [0,2]:
    if b<lib.read8(s['gBattlersCount']):
     lib.write16(s['gBattleMons']+b*abi[74]+pabi[15],16000);lib.write16(s['gBattleMons']+b*abi[74]+pabi[16],16000)
     lib.write16(s['gBattleMons']+b*abi[74]+hp,30000);lib.write16(s['gBattleMons']+b*abi[74]+maxhp,30000)
   for i in range(3):lib.write16(party+i*abi[2]+partyhp,30000);lib.write16(party+i*abi[2]+partymaxhp,30000)
   controllers={lib.read32(s['gBattlerControllerFuncs']+i*4)&~1 for i in range(4)}
   if controllers&actions:press(1)
   elif controllers&moves:press(1);attacks+=1
   else:press(2)
  elif started and cb==s['CB2_Overworld']:
   assert lib.read8(s['gBattleOutcome'])==1
   for _ in range(100):
    if idle():break
    press(1)
   assert idle() and flag(0x500+tid) and attacks>0
   picture('galactic-scout-'+str(tid)+'-defeated');wins.append(dict(trainer=tid,attacks=attacks,native_outcome=1,physical_npc_interaction=True));break
  else:press(1)
 else:
  picture('galactic-scout-stuck');raise AssertionError(('Galactic scout battle did not finish',tid,hex(cb),attacks,started))
 assert [flag(0x500+v) for v in range(1570,1589)]==ship_before,'Scout cleared a ship flag'
lib.stop();(args.output/'diglett-scouts.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),map='DiglettsCave_B1F_Frlg',wins=wins,independent_defeated_flags=True,ship_grunt_flags_unchanged=True,travel_party_flags_and_boosted_player_stats_are_fixtures=True,controller_npc_dialogue_and_battles=True,not_a_balance_test=True),indent=2)+'\n');print('Both Galactic scout battles won; ship flags unchanged',flush=True)
