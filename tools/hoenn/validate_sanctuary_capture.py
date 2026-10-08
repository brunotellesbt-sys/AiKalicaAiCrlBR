"""Real altar interaction and scripted special battle, including escape and capture."""
from pathlib import Path
import json
import hashlib
import struct
root=Path(__file__).resolve().parents[2]
prefix=(root/'tools/hoenn/validate_sanctuaries.py').read_text().split("\nfor site in r['sites']:")[0].replace("native('ScriptGiveMon',7,60,0)","native('ScriptGiveMon',150,60,0)")
exec(compile(prefix,str(root/'tools/hoenn/validate_sanctuaries.py'),'exec'))
import subprocess,re
raw_symbols=subprocess.check_output([str(root/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),'--defined-only',str(source/'pokeemerald.elf')],text=True)
action_handlers={int(a,16) for a in re.findall(r'^([0-9a-f]+) . HandleInputChooseAction$',raw_symbols,re.M)}
cap=next(c for c in r['captures'] if c['national_dex']==1025)
assert native('GetSetPokedexFlag',1025,1)==0
native('FlagSet',abi[50]);assert native('AddBagItem',abi[64],1)
def badges(k,h):
 for count,start in [(k,0x1AB0),(h,abi[63])]:
  for i in range(8):
   f=start+i;a=save()+4720+f//8;v=lib.read8(a);mask=1<<(f&7);lib.write8(a,v|mask if i<count else v&~mask)
def talk():
 x,y=cap['position'];warp(cap['map'],x,y+1);native('SetPlayerAvatarTransitionFlags',1);step(30);step(1,64);step(15);step(1,1);step(35)
badges(8,7);talk();picture('special-pecharunt-locked')
for _ in range(5):press()
assert native('JourneySpecialUnlocked')==0
assert native('GetSetPokedexFlag',1025,1)==0
badges(8,8)
def start_battle():
 talk()
 for _ in range(15):
  if (lib.read32(s['gMain']+4)&~1) in [s['CB2_InitBattle'],s['BattleMainCB2']]:break
  press()
 step(400)
 print('Battle start:',hex(lib.read32(s['gBattleTypeFlags'])),hex(lib.read32(s['gMain']+4)&~1),flush=True)
 for _ in range(80):
  if (lib.read32(s['gBattlerControllerFuncs'])&~1) in action_handlers:break
  press(2)
 assert (lib.read32(s['gBattlerControllerFuncs'])&~1) in action_handlers
 step(1,64);step(10);step(1,32);step(10)
 assert lib.read8(s['gActionSelectionCursor'])==0
 picture('special-pecharunt-battle')
 assert (lib.read32(s['gMain']+4)&~1)==s['BattleMainCB2']
 assert not lib.read32(s['gBattleTypeFlags'])&abi[10]
start_battle()
# Action menu: Fight / Bag / Pokemon / Run; Run is lower-right.
step(1,128);step(10);step(1,16);step(10);assert lib.read8(s['gActionSelectionCursor'])==3
step(1,1);step(300)
for _ in range(30):
 if location()==map_id(cap['map']) and (lib.read32(s['gMain']+4)&~1)==s['CB2_Overworld']:break
 press(2)
print('Escape callback:',hex(lib.read32(s['gMain']+4)&~1),flush=True)
assert (lib.read32(s['gMain']+4)&~1)==s['CB2_Overworld']
step(200)
assert native('GetSetPokedexFlag',1025,1)==0
assert not native('FlagGet',cap['flag_id'])
start_battle()
step(1,16);step(10);assert lib.read8(s['gActionSelectionCursor'])==1
step(1,1);step(90);picture('special-pecharunt-bag')
# With Master Ball as the only usable item, choose its pocket and use it.
step(1,16);step(120);picture('special-pecharunt-ball-pocket')
step(1,1);step(60);picture('special-pecharunt-item-choice')
step(1,1);step(300)
for _ in range(100):
 if (lib.read32(s['gMain']+4)&~1)==s['CB2_Overworld']:break
 press(2)
picture('special-pecharunt-after-capture')
print('Capture callback:',hex(lib.read32(s['gMain']+4)&~1),flush=True)
assert (lib.read32(s['gMain']+4)&~1)==s['CB2_Overworld']
step(200)
assert native('GetSetPokedexFlag',1025,1)
assert native('FlagGet',cap['flag_id'])
assert native('TrySavingData',0,max_frames=6000)==1
native('FlagClear',cap['flag_id']);assert not native('FlagGet',cap['flag_id'])
assert native('LoadGameSave',0)==1;step(30)
assert native('FlagGet',cap['flag_id'])
warp(cap['map'],cap['position'][0],cap['position'][1]+1)
assert native('FlagGet',cap['flag_id'])
lib.stop()
(args.output/'sanctuary-capture.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),species=cap['species'],national_dex=1025,locked_with_15_badges=True,unlocked_with_16_before_leagues=True,real_escape_and_retry=True,real_master_ball_capture=True,capture_persists_on_map_reload=True,native_flash_save_restores_catch_flag=True),indent=2)+'\n')
