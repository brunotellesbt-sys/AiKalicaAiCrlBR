"""Adapt every regional gym leader to gym rank, player party size and level."""
import argparse,hashlib,json
from pathlib import Path
from prepare_five_island_habitat import PRIOR,LAYER as PREVIOUS
LAYER='adaptive-gym-teams';PRIOR=PRIOR+[PREVIOUS]

def prepare(source):
 source=Path(source);marker=source/('.journey-'+LAYER)
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in r['prepared_sha256'].items(): assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  return r
 expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
 for layer in PRIOR:expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 outputs={};originals={}
 def stage(p,text):
  old=(source/p).read_bytes() if (source/p).exists() else None
  h=hashlib.sha256(old).hexdigest() if old is not None else None
  assert h==expected.get(p),p
  if h is not None: originals[p]=h
  outputs[p]=text.encode()
 stage('src/journey_adaptive_gym.c',(Path(__file__).with_name('adaptive_gym_teams.c')).read_text())
 p='include/journey_gym_scaling.h';text=(source/p).read_text().replace('struct Trainer;','struct Trainer;\nstruct TrainerMon;\nbool32 JourneyPrepareGymLeader(const struct Trainer *, struct Trainer *, struct TrainerMon *);');stage(p,text)
 p='src/battle_main.c';text=(source/p).read_text();anchor='    u8 monsCount;\n    if (battleTypeFlags & BATTLE_TYPE_TRAINER'
 assert text.count(anchor)==1
 text=text.replace(anchor,'    u8 monsCount = trainer->partySize;\n    struct Trainer adaptiveTrainer;\n    struct TrainerMon adaptiveMons[PARTY_SIZE];\n    if (!(battleTypeFlags & (BATTLE_TYPE_FRONTIER | BATTLE_TYPE_EREADER_TRAINER | BATTLE_TYPE_TRAINER_HILL))\n        && JourneyPrepareGymLeader(trainer, &adaptiveTrainer, adaptiveMons))\n        trainer = &adaptiveTrainer;\n    if (battleTypeFlags & BATTLE_TYPE_TRAINER',1)
 # Returned count must equal actual generated count, including half teams.
 start=text.index('u8 CreateNPCTrainerPartyFromTrainer(');end=text.index('static enum BattleTrainer GetBattlerTrainerFromParty',start)
 chunk=text[start:end];assert chunk.count('return trainer->partySize;')==1
 text=text[:start]+chunk.replace('return trainer->partySize;','return monsCount;')+text[end:];stage(p,text)
 r=dict(layer=LAYER,leader_count=16,party_rule='rank >= 4: 6; otherwise rank + 2 + (non_egg_player_count > rank + 2)',signature_families_prioritized=True,regional_levels_unchanged=True,original_sha256=originals,prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()})
 for p,raw in outputs.items():(source/p).write_bytes(raw)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.source),indent=2))
