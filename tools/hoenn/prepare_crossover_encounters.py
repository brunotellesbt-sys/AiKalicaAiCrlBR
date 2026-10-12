"""Add twelve route encounters with independent, persistent six-battle progress."""
import argparse, hashlib, json
from pathlib import Path
from prepare_crossover_opponents import PRIOR,LAYER as PREVIOUS
ROOT=Path(__file__).resolve().parents[2];LAYER='crossover-encounters';PRIOR=PRIOR+[PREVIOUS]
DIALOGUES={
 'EREN':[
  'I do not know how I got here.\\nMikasa and Armin are not with me.\\pI touched that smiling Titan...\\nThen everything changed.\\pTEAM MAGMA knows something!\\nBattle me. I need to get stronger!',
  'I still cannot find my friends.\\nArmin would figure this out.\\pMAGMA wants to change the land?\\nThey must know about the portal!\\pI will not let them trap us here.\\nShow me how you battle!',
  'Mikasa would never give up on me.\\nI will not give up on her either.\\pEvery trail leads to more MAGMA.\\nWhy will nobody tell me the truth?\\pCome on! I need a real battle!',
  'I keep remembering that Titan.\\nWhat happened when I touched it?\\pNo walls here... but I am trapped!\\nMAGMA will answer my questions.\\pI will fight my way back home!',
  'They play with the whole world!\\nPeople are not theirs to control!\\pMy friends might be in danger\\nwhile I waste time here!\\pI cannot stand this any longer.\\nFight me with everything you have!',
  'I WILL GET BACK TO MY FRIENDS!\\nI WILL NOT BE THEIR PRISONER!\\pSomething is tearing through me.\\nI can feel that power again...\\pStand back... No. Battle me!\\nI need to get control of this!' ],
 'LUFFY':[
  'Hey! Have you seen my crew?\\nWe were just at SABAODY!\\pThere was a man made of light...\\nThen I woke up here.\\pAQUA acts like they own the sea!\\nLet us battle before I find them!',
  'Zoro probably got lost again!\\nNami would know where we are.\\pI cannot remember what that\\nlight guy did. Was it Kizaru?\\pAQUA will not keep me from them!\\nWant another battle?',
  'Sanji would cook these berries.\\nChopper would love the POKEMON!\\pBut I need to find all of them.\\nAQUA keeps getting in the way.\\pI am getting stronger here too!\\nLet us battle!',
  'Usopp would tell a great story\\nabout this weird place!\\pRobin might know about portals.\\nI wish she were here.\\pAQUA does not get to own the sea.\\nCome on! Give me a good battle!',
  'Franky could fix that old ship!\\nBrook would want to sing here.\\pI miss everyone. I really do.\\nBut I will get back to them!\\pWe are not letting AQUA win.\\nShow me your strongest POKEMON!',
  'My crew is waiting for me.\\nI know they are all out there!\\pTime and space? I do not get it.\\nBut I will help you stop this!\\pOne more battle, friend!\\nLet us give it everything!' ]}
def string(label,text):
 parts=text.split('\\p');rows=[]
 for i,part in enumerate(parts):
  lines=part.split('\\n')
  for j,line in enumerate(lines):
   assert len(line)<=36,(label,line)
   suffix='\\n' if j<len(lines)-1 else '\\p' if i<len(parts)-1 else '$'
   rows.append('\t.string "'+line+suffix+'"\n')
 return label+'::\n'+''.join(rows)
def prepare(source):
 source=Path(source);marker=source/('.journey-'+LAYER)
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in r['prepared_sha256'].items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  return r
 expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
 for layer in PRIOR:expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 outputs={};originals={}
 def stage(p,text):
  old=(source/p).read_bytes() if (source/p).exists() else None;h=hashlib.sha256(old).hexdigest() if old else None;assert h==expected.get(p),p
  if h:originals[p]=h
  outputs[p]=text.encode()
 stage('include/journey_crossover.h','#ifndef GUARD_JOURNEY_CROSSOVER_H\n#define GUARD_JOURNEY_CROSSOVER_H\nbool8 JourneyCrossoverTryEncounter(void);\nu32 JourneyCrossoverCount(u32 hero);\nvoid JourneyCrossoverInfo(void);\nvoid JourneyCrossoverFinish(void);\n#endif\n')
 stage('src/journey_crossover.c',(ROOT/'tools/hoenn/journey_crossover.c').read_text())
 p='src/script.c';t=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_crossover.h"',1);needle='    ptr = MapHeaderCheckScriptTable(MAP_SCRIPT_ON_FRAME_TABLE);\n\n    if (!ptr)\n        return FALSE;';assert needle in t;t=t.replace(needle,'    ptr = MapHeaderCheckScriptTable(MAP_SCRIPT_ON_FRAME_TABLE);\n\n    if (!ptr)\n        return JourneyCrossoverTryEncounter();');stage(p,t)
 script='''JourneyCrossover_Encounter::
\tlockall
\tgoto_if_eq VAR_0x8007, 0, JourneyCrossover_FromLeft
\tgoto_if_eq VAR_0x8007, 1, JourneyCrossover_FromRight
\tgoto_if_eq VAR_0x8007, 2, JourneyCrossover_FromAbove
\tapplymovement 240, JourneyCrossover_WalkUp
\tgoto JourneyCrossover_StartBattle
JourneyCrossover_FromLeft::
\tapplymovement 240, JourneyCrossover_WalkRight
\tgoto JourneyCrossover_StartBattle
JourneyCrossover_FromRight::
\tapplymovement 240, JourneyCrossover_WalkLeft
\tgoto JourneyCrossover_StartBattle
JourneyCrossover_FromAbove::
\tapplymovement 240, JourneyCrossover_WalkDown
JourneyCrossover_StartBattle::
\twaitmovement 0
\tapplymovement 240, Common_Movement_FacePlayer
\twaitmovement 0
\tspecial JourneyCrossoverInfo
'''
 for hero in ['EREN','LUFFY']:
  for i in range(6):script+='\tgoto_if_eq VAR_RESULT, '+str(i+(6 if hero=='LUFFY' else 0))+', JourneyCrossover_'+hero+str(i+1)+'\n'
 script+='\tgoto JourneyCrossover_AfterBattle\n'
 for hero in ['EREN','LUFFY']:
  for i in range(6):
   label=hero+str(i+1);script+='JourneyCrossover_'+label+'::\n\ttrainerbattle_single TRAINER_JOURNEY_'+hero+'_'+str(i+1)+', JourneyCrossover_Text_'+label+', JourneyCrossover_Text_Defeat, JourneyCrossover_AfterBattle\n\tend\n'
 script+='''JourneyCrossover_AfterBattle::
\tmsgbox JourneyCrossover_Text_After
\tclosemessage
\tspecial JourneyCrossoverFinish
\treleaseall
\tend
'''
 for direction in ['Up','Down','Left','Right']:script+='JourneyCrossover_Walk'+direction+'::\n\twalk_'+direction.lower()+'\n\tstep_end\n'
 script+=string('JourneyCrossover_Text_Defeat','You won. I still have a lot\\nto learn about this world!')+string('JourneyCrossover_Text_After','Thanks for the battle.\\nI am going to keep searching.\\pWe will meet again!')
 for hero,texts in DIALOGUES.items():
  for i,text in enumerate(texts):script+=string('JourneyCrossover_Text_'+hero+str(i+1),text)
 stage('data/scripts/journey_crossover.inc',script)
 p='data/event_scripts.s';stage(p,(source/p).read_text()+'\n\t.include "data/scripts/journey_crossover.inc"\n')
 p='data/specials.inc';stage(p,(source/p).read_text()+'\n\tdef_special JourneyCrossoverInfo\n\tdef_special JourneyCrossoverFinish\n')
 p='src/pokemon.c';t=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "constants/opponents.h"\n#include "battle_setup.h"',1);needle='    enum Species species = GetMonData(mon, MON_DATA_SPECIES);\n    u8 abilityNum = GetMonData(mon, MON_DATA_ABILITY_NUM);\n    return GetAbilityBySpecies(species, abilityNum);';assert needle in t
 t=t.replace(needle,'    enum Species species = GetMonData(mon, MON_DATA_SPECIES);\n    u8 abilityNum = GetMonData(mon, MON_DATA_ABILITY_NUM);\n    if (species == SPECIES_REGIGIGAS && TRAINER_BATTLE_PARAM.opponentA == TRAINER_JOURNEY_EREN_6\n        && (u32)mon >= (u32)gEnemyParty && (u32)mon < (u32)(gEnemyParty + PARTY_SIZE))\n        return ABILITY_MOLD_BREAKER;\n    return GetAbilityBySpecies(species, abilityNum);')
 t=t.replace('dst->ability = GetAbilityBySpecies(dst->species, dst->abilityNum);','dst->ability = GetMonAbility(src);');stage(p,t)
 r=dict(layer=LAYER,independent_progression=True,encounters_per_hero=6,kanto_encounters_per_hero=3,hoenn_encounters_per_hero=3,visiting_order='any',dynamic_actors_only_during_encounter=True,original_rival_scenes_unchanged=True,eren_regigigas_mold_breaker_battle_only=True,used_existing_save_vars=['0x40FE','0x40FF'],original_sha256=originals,prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()})
 for p,raw in outputs.items():(source/p).write_bytes(raw)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.source),indent=2))
