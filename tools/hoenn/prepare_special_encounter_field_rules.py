"""Link the new workshop's map scripts into the native map script table."""
import argparse
from pathlib import Path
from candidate_layer import Layer
from prepare_special_encounter_workshop import PRIOR,LAYER as PREVIOUS
LAYER='special-encounter-field-rules';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    p='data/event_scripts.s'
    layer.stage(p,(layer.source/p).read_text()+'\n\t.include "data/maps/JourneyLavenderWorkshop/scripts.inc"\n\t.include "data/scripts/journey_event_encounters.inc"\n')
    return layer.finish(workshop_map_script_linked=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
