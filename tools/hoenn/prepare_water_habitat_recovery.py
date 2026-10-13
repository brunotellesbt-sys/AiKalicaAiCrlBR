"""Restore native aquatic fields lost by an earlier root-type-only filter."""
import argparse,json
from pathlib import Path
from candidate_layer import Layer
from refresh_ecology import compile_tables
from world_dex_locations import compile_locations
from prepare_variant_dex import PRIOR,LAYER as PREVIOUS

LAYER='water-habitat-recovery';PRIOR=PRIOR+[PREVIOUS]


def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if result:=layer.existing():return result
    source=layer.source
    locations=json.loads((source/'.journey-final-ecology').read_text())['ecology']['locations_data']
    outputs,ecology=compile_tables(source,locations,restore_native_water=True)
    for name,raw in outputs.items():layer.stage(name,raw)
    gen4=(source/'include/journey_generation4_habitats.h').read_text()
    h9=outputs['include/journey_habitat_data.h'].decode()
    # Keep enough capacity for either variant's actual families.
    import re
    max4=max(int(n) for n in re.findall(r'\{MAP_\w+,(\d+),',gen4))
    oldsize=int(re.search(r'species\[(\d+)\]',h9)[1])
    h9=h9.replace(f'species[{oldsize}]',f'species[{max(oldsize,max4)}]')
    layer.stage('include/journey_habitat_data.h',h9)
    dex,metadata=compile_locations(source,{4:gen4,9:h9})
    layer.stage('src/data/journey_world_dex_locations.h',dex)
    return layer.finish(ecology=ecology,dex=metadata,native_water_fields_restored=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
