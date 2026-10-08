"""Traverse and win five native League battles, then exercise Hall of Fame/credits.
Badges and level-100 team are fixtures, with native healing between battles.
This validates the League sequence, not a full campaign playthrough.
"""
import argparse, hashlib, json, re, struct, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
# Reuse the existing new-game/team fixture without executing its first-room test.
bootstrap=(ROOT/'tools/hoenn/validate_league_battles.py').read_text().split('\nentry = ')[0]
bootstrap=bootstrap.replace('run_options = parser.parse_args()',"parser.add_argument('--home-index',type=int,choices=range(1,32))\nrun_options = parser.parse_args()")
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_league_battles.py'),'exec'))
home_index=run_options.home_index or (23 if kanto else 5)
home=next(h for h in json.loads((source/'.journey-birth').read_text())['homes'] if h['index']==home_index)
native('VarSet',0x40F7,home_index)
native('VarSet',0x40F9,2)
# Both regions begin unchampioned for the full-sequence isolation check.
for flag in (champion,game_clear,0x1AC2,0x1AB8):raw_flag(flag,False)
entry='IndigoPlateau_PokemonCenter_1F_Frlg' if kanto else 'EverGrandeCity_PokemonLeague_1F'
rooms=['PokemonLeague_'+n+'_Frlg' for n in ['LoreleisRoom','BrunosRoom','AgathasRoom','LancesRoom','ChampionsRoom']] if kanto else ['EverGrandeCity_'+n for n in ['SidneysRoom','PhoebesRoom','GlaciasRoom','DrakesRoom','ChampionsRoom']]
trainers=[abi[i] for i in ([117,122,123,124,125] if kanto else [119,126,127,128,129])]
defeated=[abi[i] for i in ([120,130,131,132,133] if kanto else [121,134,135,136])]
for flag in defeated:raw_flag(flag,False)
native('VarSet',abi[49] if kanto else abi[55],0)
actions={int(a,16) for a,kind,n in re.findall(r'^(\w+) (\w) (\S+)$',raw,re.M) if n=='HandleInputChooseAction'}
moves={int(a,16) for a,kind,n in re.findall(r'^(\w+) (\w) (\S+)$',raw,re.M) if n=='HandleInputChooseMove'}
def idle():return (lib.read32(s['gMain']+4)&~1)==s['CB2_Overworld'] and lib.read8(s['sGlobalScriptContextStatus'])==2 and not lib.read8(s['sLockFieldControls'])
def finish():
 for _ in range(200):
  if idle():return
  press(1)
 raise AssertionError(('field did not idle',location(),position()))
def north(target,limit=400):
 for _ in range(limit):
  step(4,64)
  if location()==map_id(target):return
 picture(run_options.region+'-completion-path-failed')
 raise AssertionError(('route incomplete',target,location(),position()))
def battle(expected,name):
 started=ash_seen=False;attacks=0
 for tick in range(3000):
  cb=lib.read32(s['gMain']+4)&~1
  if cb==s['BattleMainCB2']:
   started=True
   actual=lib.read16(s['gTrainerBattleParameter']+abi[13])
   assert actual==expected,(name,expected,actual)
   ash_seen |= lib.read16(s['gBattleMons']+abi[75])==abi[69]
   ctrl=lib.read32(s['gBattlerControllerFuncs'])&~1
   if ctrl in actions or ctrl in moves:
    step(1,64);step(8);step(1,32);step(8);press(1)
    attacks+=ctrl in moves
   else:press(2)
  elif cb in {s['CB2_InitPartyMenu'],s['CB2_UpdatePartyMenu']}:
   if task('Task_HandleChooseMonInput'):
    available=[]
    for slot in range(1,6):
     order=lib.read8(s['gBattlePartyCurrentOrder']+slot//2)
     physical=(order&15) if slot&1 else (order>>4)
     if lib.read16(party+physical*abi[2]+abi[101])>0:available.append(slot)
    assert available,'Entire fixture team fainted'
    desired=available[0]
    if lib.read8(s['gPartyMenu']+abi[100])!=desired:step(3,128);step(20)
    else:press(1)
   else:press(1)
  elif started and cb==s['CB2_Overworld']:
   assert lib.read8(s['gBattleOutcome'])==1, ('Battle lost',name,expected,lib.read8(s['gBattleOutcome']))
   picture(run_options.region+'-'+name+'-won')
   return dict(trainer=expected,name=name,attacks=attacks,ash_after_ko=ash_seen)
  else:press(1)
 picture(run_options.region+'-'+name+'-battle-failed')
 raise AssertionError(('battle incomplete',name,attacks,hex(cb)))
warp(entry,4 if kanto else 9,4)
native('SetPlayerAvatarTransitionFlags',1);step(30)
if not kanto:step(40,64);press(1);finish()
north(rooms[0])
wins=[]
for i,room in enumerate(rooms):
 assert location()==map_id(room),(room,location())
 if i<4:
  step(1500);finish()
  print('Room ready',room,position(),flush=True)
  native('HealPlayerParty')
  move=abi[76] if kanto and i==1 else abi[104]
  for slot in range(6):native('ScriptSetMonMoveSlot',slot,move,0)
  step(16,64);step(30);press(1)
 wins.append(battle(trainers[i],room))
 print('Victory',wins[-1],flush=True)
 if i==4:break
 finish()
 assert native('FlagGet',defeated[i])
 assert not native('FlagGet',champion)
 assert native('GetMonData2',party,abi[7])==abi[68]
 assert [native('GetMonData2',party+j*abi[2],abi[105]) for j in range(6)]==identity
 native('HealPlayerParty')
 for slot in range(6):native('ScriptSetMonMoveSlot',slot,abi[104],0)
 # Circle the NPC and use the real open door.
 step(16,32);step(30);step(48,64);step(30);step(16,16);step(30)
 if kanto:north(rooms[i+1])
 else:
  north('EverGrandeCity_Hall'+str(i+1))
  step(1000);north(rooms[i+1])
# Follow the original champion aftermath without injecting a warp or completion flag.
hof_seen=credits_seen=False
for tick in range(5000):
 cb=lib.read32(s['gMain']+4)&~1
 hof_seen |= cb in {s.get('CB2_HofIdle'),s.get('CB2_HallOfFame'),s.get('CB2_DoHallOfFameScreenFrlg'),s.get('CB2_DoHallOfFameScreen')}
 credits_seen |= cb in {int(a,16) for a,kind,n in re.findall(r'^(\w+) (\w) (\S+)$',raw,re.M) if n in ('CB2_Credits','CB2_StartCreditsSequenceFrlg','CB2_StartCreditsSequence')}
 if tick%200==0:print('Aftermath',tick,hex(cb),location(),hof_seen,credits_seen,flush=True)
 if credits_seen:break
 press(1)
assert hof_seen and credits_seen
picture(run_options.region+'-credits-start')
result=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),region=run_options.region,wins=wins,native_hall_of_fame=hof_seen,native_credits=credits_seen,healing_between_battles_is_fixture=True,full_campaign_playthrough=False)
if (source/'.journey-league-completion').exists():
 # Credits must finish naturally. Use title/menu A inputs to Continue the native save.
 main_menu_seen=False
 for tick in range(6000):
  cb=lib.read32(s['gMain']+4)&~1
  if task('Task_HandleMainMenuInput'):
   if not main_menu_seen:picture(run_options.region+'-continue-menu')
   main_menu_seen=True
  if main_menu_seen and idle():break
  if tick%500==0:print('Credits/Continue',tick,hex(cb),main_menu_seen,flush=True)
  press(1)
 else:
  picture(run_options.region+'-resume-failed')
  raise AssertionError(('No field return after credits',hex(cb),main_menu_seen))
 # Resolve actual map names from JSON IDs, including the substituted home interior.
 bedroom=next(p.parent.name for p in (source/'data/maps').glob('*/map.json') if json.loads(p.read_text())['id']==home['bedroom_map'])
 assert location()==map_id(bedroom),(home['city'],bedroom,location(),position())
 assert native('VarGet',0x40F7)==home_index
 assert [native('GetMonData2',party+j*abi[2],abi[105]) for j in range(6)]==identity
 assert native('GetMonData2',party,abi[7])==abi[68]
 assert native('GetMonData2',party,abi[65])==2
 def raw_get(flag):return bool(lib.read8(save()+4720+flag//8)&(1<<(flag&7)))
 own_flags=(0x1AC2,0x1AB8) if kanto else (champion,game_clear)
 other_flags=(champion,game_clear) if kanto else (0x1AC2,0x1AB8)
 assert all(raw_get(f) for f in own_flags)
 assert not any(raw_get(f) for f in other_flags)
 picture(run_options.region+'-home-after-credits')
 assert native('TrySavingData',0,max_frames=6000)==1
 assert native('LoadGameSave',0)==1
 step(30)
 assert all(raw_get(f) for f in own_flags) and not any(raw_get(f) for f in other_flags)
 assert native('VarGet',0x40F7)==home_index
 result.update(native_credits_finished=True,native_continue_menu=True,selected_home=home['city'],
               selected_home_index=home_index,selected_home_map=bedroom,return_to_selected_home=True,
               team_identity_and_hidden_slot_preserved=True,other_region_uncompleted=True,native_flash_save_reload=True)
(args.output/(run_options.region+'-league-completion.json')).write_text(json.dumps(result,indent=2)+'\n')
lib.stop()
print(result,flush=True)
