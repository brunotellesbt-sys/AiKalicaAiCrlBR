"""Prepare five isolated native-Dive probes from a verified private171 copy.

This is a runtime diagnostic, not a classified/reachable final ocean network.
No existing prepared candidate is overwritten. A reused directory must still
be a complete, byte-verified171 parent with its exact original ROM and ELF.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from atlas_surf_dives import patch_specs, reserve_patches, stage as stage_dives
from atlas_surf_layer import stage_geometry
from atlas_surf_runtime import stage as stage_runtime
from atlas_surf_physical import stage as stage_physical
from atlas_surf_ecology import stage as stage_ecology
from atlas_surf_ports import stage as stage_ports
from atlas_surf_source import Source
from candidate_layer import Layer
from prepare_generated_area_review import PRIOR,LAYER
from restore_generated_area_review import verify_prefix


BASE_ROM='52156af727381fb5b47dacf83f8f57696e05dae05c4971368310b98515eba935'
BASE_ELF='000a4795be90877c83c4b133b3efa5234d042e8414e832d5e0e687ae4304bd46'


def diagnostic_plan():
    chunks=[]
    for number,spec in enumerate(patch_specs()):
        x,y=spec['atlas'];name='JourneyAtlasDiveProbe'+spec['name']
        chunks.append(dict(name=name,id='MAP_'+name.upper(),group='JourneyAtlasDiveDiagnostic',
                           number=number,origin=[8*x,8*y],width=8,height=8,
                           water_runs=[[y,1,7] for y in range(1,7)],connections=[]))
    return reserve_patches(dict(scale=8,corridor_width=6,chunks=chunks,
                                diagnostic_only=True,release_eligible=False))


def prepare(source, clone_from=None):
    source=Path(source).resolve()
    if clone_from is not None:
        clone_from=Path(clone_from).resolve()
        if source.exists():
            raise ValueError('Preserve the existing or partial diagnostic; choose a new destination')
        verify_prefix(clone_from,complete=True)
        shutil.copytree(clone_from,source,copy_function=shutil.copy2,symlinks=False)
    elif not source.is_dir():
        raise ValueError('Reuse requires an existing private verified171 copy')
    parent=verify_prefix(source,complete=True)
    parent_markers={'.journey-'+name for name in parent['layer_marker_sha256']}
    if any(p.name not in parent_markers for p in source.glob('.journey-atlas*')):
        raise ValueError('Preserve all existing Atlas work or diagnostic markers')
    for name,expected in [('pokeemerald.gba',BASE_ROM),('pokeemerald.elf',BASE_ELF)]:
        if hashlib.sha256((source/name).read_bytes()).hexdigest()!=expected:
            raise ValueError(('Private copy no longer has the original171 build',name))
    inputs=Source(source)
    donor='JourneyHoennNorthSea'
    # Find a genuine ordinary Surf cell and complete small reef within the
    # same authenticated native banks as Route127's known Diveable donor.
    words=inputs.words(donor);layout=inputs.layout(donor)
    water=next(i for i,w in enumerate(words) if w==0x1170 and inputs.water(donor,i%layout['width'],i//layout['width']))
    reef=next(i for i,w in enumerate(words) if w==0x15F9)
    donorspec=dict(map=donor,water_tile=[water%layout['width'],water//layout['width']],
                   reef_tile=[reef%layout['width'],reef//layout['width']])
    plan=diagnostic_plan();layer=Layer(source,'atlas-stage-smoke',PRIOR+[LAYER])
    plan,geometry=stage_geometry(layer,plan,{r['name']:donorspec for r in plan['chunks']})
    runtime=stage_runtime(layer,plan)
    physical=stage_physical(layer,plan)
    dives=stage_dives(layer,plan,donor=dict(map='Route127',tile=[72,49]))
    ecology=stage_ecology(layer,{r['name']:donor for r in plan['chunks']})
    ports=stage_ports(layer,inputs)
    inputs.assert_unchanged()
    report=layer.finish(diagnostic_only=True,release_eligible=False,diagnostic_role='five-isolated-dives',
                        parent=parent,geometry_plan=plan,geometry=geometry,runtime=runtime,
                        physical=physical,dives=dives,ecology=ecology,ports=ports,
                        real_route_classification_or_save_migration_proven=False)
    return dict(prepared_files=len(report['prepared_sha256']),diagnostic_maps=5,
                marker_sha256=hashlib.sha256(layer.marker.read_bytes()).hexdigest(),
                diagnostic_only=True,release_eligible=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--clone-from',type=Path)
    parser.add_argument('--reuse-verified-private-copy',action='store_true')
    args=parser.parse_args()
    if bool(args.clone_from)==bool(args.reuse_verified_private_copy):
        parser.error('Choose a new clone destination or explicit reuse of a clean verified171 private copy')
    print(json.dumps(prepare(args.source,args.clone_from),indent=2))
