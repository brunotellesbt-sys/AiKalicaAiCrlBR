"""Win Galactic battles and exercise gates, rewards and the native final scene.

Travel/script entry, prior badges and boosted player battle stats are fixtures.
Enemy parties, outcomes, defeated flags, chapter state and rewards are native.
"""
import hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_team_missions.py').read_text().split('\nassert pending(True) == 7')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_team_missions.py'),'exec'))
sha=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()
chapter=json.loads((source/'.journey-galactic-chapter').read_text())
if (source/'.journey-galactic-continuity').exists():chapter['grunts']=json.loads((source/'.journey-galactic-continuity').read_text())['grunts']
# No region is allowed to skip the new final chapter even after all 16 badges.
for f in kanto_flags+hoenn_flags:rawflag(f,True)
native('VarSet',0x40FE,0);native('VarSet',0x40FF,4095)
state_address=native('GetVarPointer',0x40FE)
assert special('JourneyGalacticAvailable')==1
assert native('JourneyGalacticLeagueReady')==0
assert native('JourneyGalacticCaptureLocked',483)==1
assert native('JourneyGalacticCaptureLocked',484)==1
assert native('JourneyGalacticCaptureLocked',487)==1
for grunt in chapter['grunts']:rawflag(0x500+grunt['id'],False)
assert special('JourneyGalacticGruntsCleared')==0
for key in ['MARS','JUPITER','SATURN','CHARON','CYRUS']:
 ident=re.search(r'#define TRAINER_JOURNEY_'+key+r' (\d+)',(source/'include/constants/opponents.h').read_text())[1];rawflag(0x500+int(ident),False)
targets={int(a,16) for a,_,n in re.findall(r'^(\w+) (\w) (\S+)$',raw,re.M) if n in ['HandleInputChooseTarget','HandleInputShowTargets','HandleInputShowEntireFieldTargets']}
def boost():
 # Deliberately strong player-side fixture, to validate state transitions.
 for battler in [0]:
  lib.write16(s['gBattleMons']+battler*abi[74]+pabi[12],16000)
  lib.write16(s['gBattleMons']+battler*abi[74]+pabi[16],10000)
  lib.write16(s['gBattleMons']+battler*abi[74]+pabi[20],30000)
  if lib.read16(s['gBattleMons']+battler*abi[74]+abi[102]):lib.write16(s['gBattleMons']+battler*abi[74]+abi[102],30000)
 for i in range(3):
  lib.write16(party+i*abi[2]+pabi[8],16000)
  lib.write16(party+i*abi[2]+pabi[9],10000)
  lib.write16(party+i*abi[2]+pabi[21],30000)
  if lib.read16(party+i*abi[2]+abi[101]):lib.write16(party+i*abi[2]+abi[101],30000)
def battle_input():
 boost();controllers={lib.read32(s['gBattlerControllerFuncs']+4*i)&~1 for i in range(4)}
 if controllers&targets:press(1)
 elif controllers&(actions|moves):
  step(1,64);step(8);step(1,32);step(8);press(1)
 else:press(2)
def one_battle(label,limit=2400):
 started=False;turns=0;opponent=None
 for _ in range(limit):
  cb=lib.read32(s['gMain']+4)&~1
  if cb==s['BattleMainCB2']:
   started=True;opponent=lib.read16(s['gTrainerBattleParameter']+abi[13]);battle_input();turns+=1
  elif started and cb==s['CB2_Overworld']:
   outcome=lib.read8(s['gBattleOutcome']);assert outcome==1,(label,outcome)
   finish();return dict(label=label,opponent=opponent,outcome=outcome,battle_controller_ticks=turns)
  else:press(1)
 picture('galactic-battle-failed');raise AssertionError((label,'battle timeout',hex(cb)))
wins=[]
for i,g in enumerate(chapter['grunts']):
 native('HealPlayerParty');warp(g['map'],0,0)
 label='JourneyGalactic_Gate' if g['key']=='GALACTIC_BULKHEAD_GUARD' else 'JourneyGalactic_'+g['key']
 script(b'\x05'+struct.pack('<I',s[label]),30)
 win=one_battle(g['key']);assert win['opponent']==g['id'],win
 assert native('FlagGet',0x500+g['id'])==1
 wins.append(win);print('Galactic grunt',i+1,'won',flush=True)
assert special('JourneyGalacticGruntsCleared')==1
native('HealPlayerParty');warp('JourneyGalacticHall',15,7)
picture('galactic-prison-before-finale')
script(b'\x05'+struct.pack('<I',s['JourneyGalactic_Cyrus']),30)
last_cb=None;started=False;finale=[];states=[];timeout=0
for tick in range(16000):
 cb=lib.read32(s['gMain']+4)&~1;state=lib.read16(state_address)
 if not states or states[-1]!=state:states.append(state);print('Galactic state',state,flush=True)
 if cb==s['BattleMainCB2']:
  if not started:
   started=True
   entry=dict(state=state,opponent=lib.read16(s['gTrainerBattleParameter']+abi[13]),battle_type=lib.read32(s['gBattleTypeFlags']))
   finale.append(entry);picture('galactic-finale-battle-'+str(len(finale)))
  battle_input()
 else:
  if started:
   started=False;finale[-1]['outcome']=lib.read8(s['gBattleOutcome']);assert finale[-1]['outcome']==1,finale[-1]
  if state==7 and idle():break
  press(1)
else:
 picture('galactic-finale-timeout');raise AssertionError(('Finale timeout',states,finale,hex(cb)))
assert len(finale)==4 and states[-1]==7,(states,finale)
picture('galactic-prison-after-finale')
assert native('JourneyGalacticCaptureLocked',483)==0
assert native('JourneyGalacticCaptureLocked',484)==0
assert native('JourneyGalacticCaptureLocked',487)==0
assert native('JourneyGalacticNoCatch')==0
assert hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()==sha
lib.stop()
(args.output/'galactic-chapter.json').write_text(json.dumps(dict(passed=True,rom_sha256=sha,grunts=wins,finale=finale,states=states,optional_legendary_captures_unlock_after_chapter=True,enemy_party_not_written=True,player_battle_stats_boosted=True,prior_badges_and_travel_are_fixtures=True,full_campaign_playthrough=False),indent=2)+'\n')
print('Native Galactic chapter complete',flush=True)
