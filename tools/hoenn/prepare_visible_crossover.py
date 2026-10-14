"""Place dynamic rivals and arrival actors in the engine's buffered coordinates."""
import argparse
from pathlib import Path
from candidate_layer import Layer
from prepare_pwt_obedience import PRIOR,LAYER as PREVIOUS
LAYER='visible-crossover';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
 layer=Layer(source,LAYER,PRIOR)
 if r:=layer.existing():return r
 p='src/journey_crossover.c';t=(layer.source/p).read_text();old='JOURNEY_RIVAL_LOCALID,xx-7,yy-7,MapGridGetElevationAt(xx,yy)';assert t.count(old)==1;t=t.replace(old,'JOURNEY_RIVAL_LOCALID,xx,yy,MapGridGetElevationAt(xx,yy)');t=t.replace('            gSpecialVar_0x8007=d;','            gSpecialVar_0x8007=d;\n            gSpecialVar_LastTalked=JOURNEY_RIVAL_LOCALID;');layer.stage(p,t)
 p='src/event_object_movement.c';t=(layer.source/p).read_text();a=t.index('u8 SpawnSpecialObjectEventParameterized(');b=t.index('\nu8 TrySpawnObjectEvent(',a);chunk=t[a:b];assert chunk.count('struct ObjectEventTemplate objectEventTemplate;')==1;chunk=chunk.replace('struct ObjectEventTemplate objectEventTemplate;','struct ObjectEventTemplate objectEventTemplate = {0};');layer.stage(p,t[:a]+chunk+t[b:])
 p='src/journey_birth.c';t=(layer.source/p).read_text();t=t.replace('LOCALID_JOURNEY_ARRIVAL_TRUCK, arrival->truckX, arrival->truckY, elevation','LOCALID_JOURNEY_ARRIVAL_TRUCK, arrival->truckX + MAP_OFFSET, arrival->truckY + MAP_OFFSET, elevation');t=t.replace('arrival->boat ? arrival->landingX : arrival->truckX + 2,','(arrival->boat ? arrival->landingX : arrival->truckX + 2) + MAP_OFFSET,').replace('arrival->boat ? arrival->landingY - 1 : arrival->truckY - 1,','(arrival->boat ? arrival->landingY - 1 : arrival->truckY - 1) + MAP_OFFSET,');layer.stage(p,t)
 return layer.finish(rival_approach_on_screen=True,arrival_vehicle_and_mother_coordinates_fixed=True,special_object_template_initialized=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
