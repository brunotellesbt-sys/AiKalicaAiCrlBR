"""Exercise native creation, level-up learning and Fairy matchups for the released catalog."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_abilities.py').read_text().split('\nability_field,')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_abilities.py'),'exec'))
from audit_battle_database import compiled,REFERENCE
catalog=compiled(source);reference=json.loads(REFERENCE.read_text())
canonical=json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text())['canonical_species']
party=s['gParties'];cases=[];learned=0;evolution_moves=0
for dex,sid in sorted(canonical.items(),key=lambda item:int(item[0])):
 table=catalog['species'][sid]['learnset']
 assert sorted(set(map(tuple,table)))==sorted(set(map(tuple,reference['species'][str(sid)]['learnset'])))
 for level in [1,5,20,50,100]:
  native('ZeroMonData',party);lib.write8(s['gPartiesCount'],0)
  assert native('ScriptGiveMon',sid,level,0)==0
  expected=[]
  for at,move in table:
   if at>level:break
   if at and move not in expected:expected=(expected+[move])[-4:]
  expected+=(4-len(expected))*[0]
  observed=[native('GetMonData2',party,abi[92]+slot) for slot in range(4)]
  assert observed==expected,(dex,sid,level,expected,observed)
 # Isolate the native level-up routine from the player's move-choice UI.
 for slot in range(4):native('ScriptSetMonMoveSlot',0,0,slot)
 chosen=next((level for level,_ in table if level>1),None)
 if chosen is not None:
  wanted=[move for level,move in table if level==chosen]
  for index,move in enumerate(wanted):
   actual=native('MonTryLearningNewMoveAtLevel',party,index==0,chosen)
   assert actual==move,(dex,chosen,move,actual)
   learned+=1
  assert native('MonTryLearningNewMoveAtLevel',party,False,chosen)==0
 for slot in range(4):native('ScriptSetMonMoveSlot',0,0,slot)
 evolution=[move for level,move in table if level in [0,100]]
 for index,move in enumerate(evolution):
  actual=native('MonTryLearningNewMoveEvolution',party,index==0)
  assert actual==move,(dex,'evolution',move,actual)
  evolution_moves+=1
 assert native('MonTryLearningNewMoveEvolution',party,not evolution)==0
 cases.append(dict(national_dex=int(dex),species=sid,creation_levels=[1,5,20,50,100],level_up_tested=chosen))
 if int(dex)%100==0:print('Native creation and learning passed through Dex',dex,flush=True)
matchups=[]
for attacker,defender,wanted in [(19,17,8192),(19,2,8192),(19,18,8192),(19,4,2048),(19,9,2048),(19,11,2048),(17,19,0),(4,19,8192),(9,19,8192),(2,19,2048),(7,19,2048),(18,19,2048)]:
 actual=native('GetTypeModifier',attacker,defender);assert actual==wanted,(attacker,defender,actual,wanted)
 matchups.append(dict(attacker=attacker,defender=defender,modifier=actual))
assert native('TrySavingData',0,max_frames=6000)==1
before=[native('GetMonData2',party,abi[92]+slot) for slot in range(4)]
assert native('LoadGameSave',0)==1
assert before==[native('GetMonData2',party,abi[92]+slot) for slot in range(4)]
lib.stop()
r=dict(passed=True,rom_sha256=catalog['rom_sha256'],reference_sha256=hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),base_species=1025,native_creation_cases=len(cases)*5,native_level_up_moves=learned,native_evolution_moves=evolution_moves,cases=cases,fairy_matchups=matchups,native_save_preserves_moves=True,party_and_levels_are_fixtures=True,full_campaign_playthrough=False)
(args.output/'learnsets.json').write_text(json.dumps(r,indent=2)+'\n');print('All 1025 base species creation and native level-up checks passed',flush=True)
