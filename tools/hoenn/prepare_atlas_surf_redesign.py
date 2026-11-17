"""Prepare boundaries, swimmers, native species and103 complete-rock repairs.

The large cave exteriors and separate legendary chambers are still a later
batch. This explicit scope never labels the entire user redesign complete.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil

from atlas_surf_redesign_overlay import load
from atlas_surf_legendary_appearance import stage as stage_appearance
from atlas_surf_route_borders import stage as stage_borders,stage_undefined_drawing
from atlas_surf_background import stage as stage_background
from atlas_surf_trainers import stage as stage_trainers
from atlas_surf_redesign_migration import stage as stage_migration
from atlas_surf_build_inputs import stage as stage_build_inputs
from atlas_surf_rock_repairs import stage as stage_rock_repairs,stage_view_refresh
from atlas_surf_overlay import OverlaySource
from atlas_surf_source import Source
from atlas_surf_classification import census_native_bounds
from atlas_surf_layout_requirements import build_requirements
from atlas_surf_bank_edges import audit_edges,requirement_scope
from atlas_surf_reachability import audit
from prepare_atlas_surf_layout import _read_evidence,seed_build_cache
from prepare_atlas_connected_layout import checked_cache
from restore_generated_area_review import verify_prefix

ROOT=Path(__file__).resolve().parents[2]


def source_audit(layer,metadata):
    view=OverlaySource(layer);parent=Source(layer.source);inventory,_,_,_=_read_evidence(parent)
    path=ROOT/'docs/design/atlas-surf-layout/native-chart-connected-review/source/coasts.json.gz'
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!='f242a412b60c8a60b5fdbba827baad5c02bcfdfab73c678679f35a9187063c26':
        raise ValueError('The authenticated authored coast proposal changed')
    coasts=json.loads(gzip.decompress(raw))
    native=census_native_bounds(parent,coasts)
    requirements=build_requirements(view,metadata,inventory,native)
    banks=audit_edges(view,scope=requirement_scope(metadata,requirements))
    requirements['authenticated_bank_pairs']=banks['authenticated_bank_pairs']
    report,graph=audit(view,plan=metadata['geometry_plan'],requirements=requirements,
                       max_states=2000000,return_graph=True)
    if not report['passed']:raise ValueError(('Redesign source audit failed',report['errors'],report['pending']))
    return view,report,graph,banks


def compose(parent):
    layer,metadata=load(parent)
    metadata['build_input_guard']=stage_build_inputs(layer)
    captures=json.loads((Path(parent)/'.journey-sanctuaries').read_bytes())['captures']
    groups=json.loads((ROOT/'tools/hoenn/data/legendary-cave-groups.json').read_bytes())
    appearance=stage_appearance(layer,captures,groups)
    metadata,borders=stage_borders(layer,metadata)
    view=OverlaySource(layer);identities=dict(view.identities)
    borders['Dive_Emerge_protection']=stage_background(layer,metadata['geometry_plan'],identities)
    borders['undefined_drawing']=stage_undefined_drawing(layer,metadata,identities)
    borders['undefined_visual_border_treatment_pending']=False
    print('Native artwork, route limits and Dive guards staged',flush=True)
    view,report,graph,banks=source_audit(layer,metadata)
    print('Playable source ocean and directed background isolation PASS',flush=True)
    trainers=stage_trainers(layer,view,metadata,graph)
    changed_maps={r['map'] for r in appearance['changes']}|{r['map'] for r in trainers['trainers']}
    migration=stage_migration(layer,changed_maps,identities,trainers=trainers['trainers'])
    metadata['legendary_appearance_redesign']=appearance
    metadata['surf_trainer_redesign']=trainers
    metadata['template_redesign_migration']=migration
    metadata['migration']['final_version']=4
    metadata['native_General_rock_repairs']=stage_rock_repairs(layer)
    metadata['rock_view_migration']=stage_view_refresh(layer)
    metadata['migration']['final_version']=6
    metadata['pending_obligations']=[
        'native current-ROM boundary, Dive/Emerge, camera, sprite, trainer and old-save checks',
        'large distinct cave exteriors and separate entrances/chambers for all105 legendaries',
        'complete-rock review of other native primary banks; General103 repaired',
        'remaining DEX, five-edition, browser and final release gates']
    # A fresh source view authenticates all changed objects and restore code.
    view,report,graph,banks=source_audit(layer,metadata)
    metadata['source_audit_passed']=True
    borders['source_graph_finalized']=True
    metadata['route_border_redesign']=borders
    return layer,metadata,report,banks


def prepare(parent,target,output,cache_freeze=None):
    parent,target,output=map(lambda p:Path(p).resolve(),(parent,target,output))
    if target.exists() or target==parent or target.is_relative_to(parent):
        raise ValueError('Use a new private path and preserve all frozen sources')
    before=verify_prefix(parent,complete=True)
    layer,metadata,report,banks=compose(parent)
    output.mkdir(parents=True,exist_ok=True)
    for name,value in [('source',report),('banks',banks),('preparation',metadata)]:
        (output/(name+'.json.gz')).write_bytes(gzip.compress(json.dumps(value,sort_keys=True,separators=(',',':')).encode(),mtime=0))
    cache=checked_cache(cache_freeze,before) if cache_freeze else None
    if verify_prefix(parent,complete=True)!=before:raise ValueError('Immutable parent changed')
    shutil.copytree(parent,target,copy_function=shutil.copy2,symlinks=False)
    if cache:
        metadata['build_cache']=seed_build_cache(cache,target,set(layer.expected)|set(layer.outputs)|{p.name for p in parent.glob('.journey-*')})
    layer.source=target;layer.marker=target/'.journey-atlas-surf-layout'
    result=layer.finish(**metadata)
    if verify_prefix(parent,complete=True)!=before:raise ValueError('Immutable parent changed while materializing')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent',required=True,type=Path);parser.add_argument('--target',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path);parser.add_argument('--cache-freeze',type=Path)
    a=parser.parse_args();result=prepare(a.parent,a.target,a.output,a.cache_freeze)
    print(json.dumps(dict(private_source=str(a.target),source_passed=result['source_audit_passed'],
        trainers=result['surf_trainer_redesign']['count'],migration=result['migration']['final_version'],native_validated=False,release_eligible=False)))
