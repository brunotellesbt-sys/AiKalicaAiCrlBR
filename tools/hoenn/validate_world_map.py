"""Open the actual MAP menu with controller input; travel and party are fixtures."""
from pathlib import Path
import hashlib, json, sys
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_abilities.py').read_text().split('ability_field, froakie')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_abilities.py'),'exec'))
assert native('ScriptGiveMon',1,5,0)==0
report=json.loads((source/('.journey-coastal-world-map' if (source/'.journey-coastal-world-map').exists() else '.journey-world-map')).read_text())
def callback():return lib.read32(s['gMain']+4)&~1
def wait_for(predicate,limit=300):
 for _ in range(limit):
  if predicate():return
  step(8)
 picture('failure');raise AssertionError(('Timeout',hex(callback())))
def open_map():
 press(8)
 wait_for(lambda:lib.read8(s['sNumStartMenuActions'])>0)
 step(80)
 count=lib.read8(s['sNumStartMenuActions']);assert count<=9
 actions=[lib.read8(s['sCurrentStartMenuActions']+i) for i in range(count)]
 index=next(i for i,v in enumerate(actions) if lib.read32(s['sStartMenuItems']+v*8+4)&~1==s['StartMenuWorldMapCallback'])
 for _ in range(12):
  pos=lib.read8(s['sStartMenuCursorPos'])
  if pos==index:break
  press(128 if pos<index else 64)
 assert lib.read8(s['sStartMenuCursorPos'])==index
 press(1);wait_for(lambda:callback()==s['CB2_JourneyWorldMap']);step(60)
 ptr=lib.read32(s['sJourneyWorldMap']);assert ptr and lib.read8(ptr+2058)==1
 return ptr
checks=[]
for name,x,y in [('JourneyRoute12Shipyard',24,39),('Route1_Frlg',5,12),('LittlerootTown',5,5),('SixIsland_Frlg',8,8)]:
 warp(name,x,y);step(60)
 before=(location(),position())
 expected=native('JourneyWorldMapPlayerPoint');point=report['points'][expected]
 ptr=open_map();assert lib.read16(ptr+2052)==expected
 xy=lambda:(lib.read8(ptr+2056),lib.read8(ptr+2057))
 assert xy()==(point['x'],point['y'])
 picture('world-map-'+name)
 press(16);assert xy()!=(point['x'],point['y'])
 press(4);assert xy()==(point['x'],point['y'])
 press(2);wait_for(lambda:callback()==s['CB2_Overworld']);step(120)
 assert lib.read32(s['sJourneyWorldMap'])==0
 press(2);step(90);assert before==(location(),position())
 checks.append(dict(map=name,player_point=expected,coordinates=list(xy()) if lib.read32(s['sJourneyWorldMap']) else [point['x'],point['y']],controller_open=True,move=True,recenter=True,back=True,position_preserved=True))
 print('Native world map:',name,flush=True)
# Filling out the normal menu must not hide SAVE or prevent saving after MAP.
native('SetDexPokemonPokenavFlags')
before=(location(),position());saved_count=native('GetGameStat',0)
ptr=open_map();press(2);wait_for(lambda:callback()==s['CB2_Overworld']);step(120)
count=lib.read8(s['sNumStartMenuActions']);assert count<=9
items=[lib.read8(s['sCurrentStartMenuActions']+i) for i in range(count)]
index=next(i for i,v in enumerate(items) if lib.read32(s['sStartMenuItems']+v*8+4)&~1==s['StartMenuSaveCallback'])
for _ in range(12):
 pos=lib.read8(s['sStartMenuCursorPos'])
 if pos==index:break
 press(128 if pos<index else 64)
assert lib.read8(s['sStartMenuCursorPos'])==index
press(1);saw_saved=False
for _ in range(400):
 saw_saved|=(lib.read32(s['sSaveDialogCallback'])&~1) in [s['SaveSuccessCallback'],s['SaveReturnSuccessCallback']]
 if saw_saved and not lib.read8(s['sLockFieldControls']):break
 press(1)
assert saw_saved and native('GetGameStat',0)==saved_count+1
assert native('LoadGameSave',0,max_frames=6000)==1
lib.write32(s['gMain']+4,s['CB2_ContinueSavedGame']|1);step(1500)
assert before==(location(),position());picture('world-map-save-continue')
# The native Pokénav entry uses its normal menu and shutdown path.
lib.write32(s['gMain']+4,s['CB2_InitPokeNav']|1);step(300)
for _ in range(20):
 if callback()==s['CB2_JourneyWorldMap']:break
 press(1)
assert callback()==s['CB2_JourneyWorldMap'],('Pokenav MAP did not open',hex(callback()))
step(60);picture('world-map-pokenav');press(2)
wait_for(lambda:callback()==s['CB2_Pokenav']);step(120)
assert lib.read32(s['sJourneyWorldMap'])==0
lib.stop()
(args.output/'world-map.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),checks=checks,pokenav_entry_and_return=True,native_save_menu_and_continue=True,maximum_normal_menu_rows=count,travel_party_and_new_game_setup_are_fixtures=True,full_campaign_playthrough=False),indent=2)+'\n')
