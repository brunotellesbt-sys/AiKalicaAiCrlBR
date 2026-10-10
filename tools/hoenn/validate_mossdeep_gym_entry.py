"""Enter Tate and Liza's real gym battle with two or three usable Pokemon."""
import argparse,hashlib,json,re,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',type=Path,required=True);parser.add_argument('--library',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--players',type=int,choices=[2,3],required=True)
entry_options=parser.parse_args();players=entry_options.players
sys.argv=[sys.argv[0],'--source',str(entry_options.source),'--library',str(entry_options.library),'--output',str(entry_options.output)]
bootstrap=(ROOT/'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
# Isolate one entry per emulator process.
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_trainer_levels.py'),'exec'))
assert players in [2,3]
team([6]*players)
for bank in [kanto_flags,hoenn_flags]:
 for flag in bank:rawflag(flag,False)
trainer=ids['TRAINER_TATE_AND_LIZA_1'];rawflag(0x500+trainer,False)
warp('MossdeepCity_Gym',11,5)
script(b'\x05'+struct.pack('<I',s['MossdeepCity_Gym_EventScript_TateAndLiza']),30)
for _ in range(300):
 if lib.read32(s['gMain']+4)&~1==s['BattleMainCB2'] and lib.read8(s['gPartiesCount']+1)==players:break
 press(1)
else:raise AssertionError(('Gym battle did not start',players,hex(lib.read32(s['gMain']+4))))
flags=lib.read32(s['gBattleTypeFlags']);double=bool(flags&1) # Native BATTLE_TYPE_DOUBLE
assert double==(True),(players,flags)
for _ in range(120):
 if any(lib.read32(s['gBattlerControllerFuncs']+i*4)&~1 in actions for i in range(4)):break
 press(2)
else:raise AssertionError('Gym controller menu missing')
picture('mossdeep-'+str(players)+'-player-pokemon')
lib.stop()
(args.output/'mossdeep-entry.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),player_count=players,leader_count=players,double_battle=double,native_gym_script=True,party_and_map_are_fixtures=True,enemy_party_not_written=True),indent=2)+'\n')
