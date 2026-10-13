"""Use pinned original Four Island fields for deterministic aquatic recovery."""
import argparse,json
from pathlib import Path
from candidate_layer import Layer
from refresh_ecology import compile_tables
from prepare_water_habitat_recovery import PRIOR,LAYER as PREVIOUS

LAYER='reproducible-water';PRIOR=PRIOR+[PREVIOUS]


def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if result:=layer.existing():return result
    source=layer.source
    locations=json.loads((source/'.journey-water-habitat-recovery').read_text())['ecology']['locations_data']
    outputs,ecology=compile_tables(source,locations,restore_native_water=True)
    # Species/pools/habitats already match; only restore exact native water fields.
    layer.stage('src/data/wild_encounters.json',outputs['src/data/wild_encounters.json'])
    return layer.finish(ecology=ecology,pinned_four_island_water_fields=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
