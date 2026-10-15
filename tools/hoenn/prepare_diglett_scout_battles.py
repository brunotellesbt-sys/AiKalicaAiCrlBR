"""Two optional scouting battles with independent, otherwise unused trainer flags."""
import argparse,json
from pathlib import Path
from candidate_layer import Layer
from prepare_complete_beach_edges import PRIOR,LAYER as PREVIOUS
LAYER='diglett-scout-battles';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
 layer=Layer(source,LAYER,PRIOR)
 if old:=layer.existing():return old
 s=layer.source;p='data/scripts/journey_galactic.inc';t=(s/p).read_text();trainers=['TRAINER_JOURNEY_GRUNT_M','TRAINER_JOURNEY_GRUNT_F']
 # These two original generic records are unused by the ship's 18 individual
 # grunts and bulkhead guard. Defeating scouts cannot clear the ship mission.
 assert all(name not in t for name in trainers)
 for i,name in enumerate(trainers):
  needle=f'JourneyDiglettGalactic_Scout{i}::\n\tmsgbox JourneyDiglettGalactic_Text{i}, MSGBOX_NPC\n\tend';assert needle in t
  replacement=f'JourneyDiglettGalactic_Scout{i}::\n\ttrainerbattle_single {name}, JourneyDiglettGalactic_Text{i}, JourneyDiglettGalactic_Defeat\n\tmsgbox JourneyDiglettGalactic_After{i}, MSGBOX_NPC\n\tend';t=t.replace(needle,replacement)
 t+='\nJourneyDiglettGalactic_Defeat::\n\t.string "Our exploration continues...$"\nJourneyDiglettGalactic_After0::\n\t.string "We are exploring KANTO, not\\nblocking its roads. You can pass.\\p"\n\t.string "Our report will include your\\nbattle. You are worth watching.$"\nJourneyDiglettGalactic_After1::\n\t.string "Your POKEMON know this region\\nbetter than our equipment does.\\p"\n\t.string "We will continue our survey.\\nDo not disturb the DIGLETT.$"\n'
 layer.stage(p,t);p='data/maps/DiglettsCave_B1F_Frlg/map.json';m=json.loads((s/p).read_text())
 for o in m['object_events'][:2]:o.update(trainer_type='TRAINER_TYPE_NORMAL',trainer_sight_or_berry_tree_id='1')
 layer.stage(p,json.dumps(m,indent=2)+'\n')
 return layer.finish(map=m['name'],trainers=trainers,trainer_ids=[1568,1569],ship_grunt_ids=list(range(1570,1589)),independent_defeated_flags=True,two_optional_battles=True,third_grunt_is_surveyor=True,ordinary_current_party_level_rules=True,no_new_mandatory_gate=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
