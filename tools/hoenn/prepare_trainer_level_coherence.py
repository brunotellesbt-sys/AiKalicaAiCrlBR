"""Use one randomized level for evolution, legal moves and actual party creation."""
import argparse,hashlib,json
from pathlib import Path
from prepare_crossover_encounters import PRIOR,LAYER as PREVIOUS
LAYER='trainer-level-coherence';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
 source=Path(source);marker=source/('.journey-'+LAYER)
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in r['prepared_sha256'].items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  return r
 expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
 for layer in PRIOR:expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 outputs={};originals={}
 def stage(p,t):
  h=hashlib.sha256((source/p).read_bytes()).hexdigest();assert h==expected[p],p;originals[p]=h;outputs[p]=t.encode()
 p='src/battle_main.c';t=(source/p).read_text();needle='            struct TrainerMon competitiveMon = partyData[monIndex];';assert t.count(needle)==1;t=t.replace(needle,needle+'\n            u32 journeyLevel = JourneyGymLevel(trainer, competitiveMon.lvl);')
 assert t.count('JourneyGymLevel(trainer, competitiveMon.lvl)')==3
 t=t.replace('JourneyTrainerSpecies(competitiveMon.species, JourneyGymLevel(trainer, competitiveMon.lvl))','JourneyTrainerSpecies(competitiveMon.species, journeyLevel)').replace('JourneyPrepareCompetitiveMon(&competitiveMon, JourneyGymLevel(trainer, competitiveMon.lvl))','JourneyPrepareCompetitiveMon(&competitiveMon, journeyLevel)').replace('CreateMon(&party[i], partyData[monIndex].species, JourneyGymLevel(trainer, partyData[monIndex].lvl), personalityValue, otId);','CreateMon(&party[i], partyData[monIndex].species, journeyLevel, personalityValue, otId);');stage(p,t)
 for name in ['MossdeepCity','PacifidlogTown']:
  p='data/maps/'+name+'/map.json';t=(source/p).read_text();assert t.count('LOCALID_JOURNEY_PORT_BOAT')==1;t=t.replace('LOCALID_JOURNEY_PORT_BOAT','LOCALID_JOURNEY_'+name.upper()+'_BOAT');stage(p,t)
 r=dict(layer=LAYER,one_level_sample_per_pokemon=True,legal_moves_checked_at_actual_level=True,evolution_checked_at_actual_level=True,regional_gym_rank_scaling_preserved=True,unique_port_boat_localids=True,original_sha256=originals,prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()})
 for p,raw in outputs.items():(source/p).write_bytes(raw)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.source),indent=2))
