"""Prepare the connected mesh only after candidate533 save-source checks.

Creates a new isolated private source. It never writes public ROMs or declares
native/release validation. Native batteries must still be replayed on its build.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil

from atlas_surf_bank_edges import audit_edges, requirement_scope
from atlas_surf_candidate_history import load_terrain
from atlas_surf_candidate_migration import build_tables, stage as stage_candidate_migration
from atlas_surf_classification import census_native_bounds
from atlas_surf_layout_requirements import build_requirements
from atlas_surf_overlay import OverlaySource
from atlas_surf_reachability import audit
from atlas_surf_source import Source
from candidate_layer import Layer
from prepare_atlas_surf_layout import compose, _read_evidence, seed_build_cache
from prepare_generated_area_review import PRIOR, LAYER
from restore_generated_area_review import verify_prefix
from validate_atlas_candidate_migration_source import verify as verify_candidate_migration


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def diagnostic(path):
    path=Path(path); review=json.loads((path/'review.json').read_bytes())
    if (not review.get('source_passed') or review.get('generated_water_sccs') != 1
            or not review.get('candidate_identity_history') or not review.get('additional_native_edges_preview')):
        raise ValueError('Connected preparation requires a passing source audit with preserved candidate IDs')
    reports={}
    for name, row in review['files'].items():
        if Path(name).name!=name or not name.endswith('.json.gz'):
            raise ValueError('Unsafe diagnostic file path')
        raw=(path/name).read_bytes(); plain=gzip.decompress(raw)
        if hashlib.sha256(raw).hexdigest()!=row['sha256'] or hashlib.sha256(plain).hexdigest()!=row['json_sha256']:
            raise ValueError(('Diagnostic input changed',name))
        reports[name[:-8]]=json.loads(plain)
    source=reports['source']
    if source['passed'] is not True or source['errors'] or source['pending'] or source['generated_water_sccs']!=1:
        raise ValueError('Stored physical source report has unresolved obligations')
    return review,reports


def checked_cache(frozen_path, parent_proof):
    frozen=json.loads(Path(frozen_path).read_bytes());cache=Path(frozen['source'])
    marker=cache/'.journey-atlas-surf-layout'
    if digest(marker)!=frozen['marker_sha256'] or digest(cache/'pokeemerald.gba')!=frozen['rom_sha256'] or digest(cache/'pokeemerald.elf')!=frozen['elf_sha256']:
        raise ValueError('Preserve the changed compiled cache snapshot')
    record=json.loads(marker.read_bytes())
    if record['parent']['source_manifest_sha256']!=parent_proof['source_manifest_sha256'] or record['prepared_sha256']!=frozen['prepared_sha256']:
        raise ValueError('Cache is not derived from this immutable source')
    expected=Layer(cache,'atlas-surf-layout',PRIOR+[LAYER]).expected
    expected.update(frozen['prepared_sha256'])
    for path, wanted in expected.items():
        if digest(cache/path)!=wanted:
            raise ValueError(('Compiled cache input changed',path))
    return cache


def prepare(target, parent, review_path, travel_root, travel_source, *, cache_freeze=None, evidence=None):
    target,parent=Path(target).resolve(),Path(parent).resolve()
    if target.exists() or target==parent or target.is_relative_to(parent):
        raise ValueError('Choose a new private destination; preserve existing and parent sources')
    before=verify_prefix(parent,complete=True);review,reports=diagnostic(review_path)
    if review['source']!=before:
        raise ValueError('Connected diagnostic belongs to another immutable source')
    layer,metadata=compose(parent,preview_occluded_routes=True,coast_proposals=reports['coasts'],
        additional_native_edges=True,native_feature_travel=(travel_root,travel_source),preserve_candidate_ids=True)
    if json.dumps(metadata['geometry_plan'],sort_keys=True)!=json.dumps(reports['geometry'],sort_keys=True):
        raise ValueError('Reconstructed connected geometry differs from its source audit')
    view=OverlaySource(layer)
    inputs=Source(parent);inventory,_,_,_=_read_evidence(inputs)
    native=census_native_bounds(inputs,reports['coasts'])
    requirements=build_requirements(view,metadata,inventory,native)
    banks=audit_edges(view,scope=requirement_scope(metadata,requirements))
    requirements['authenticated_bank_pairs']=banks['authenticated_bank_pairs']
    source,graph=audit(view,plan=metadata['geometry_plan'],requirements=requirements,max_states=2000000,return_graph=True)
    if not source['passed'] or source['errors'] or source['pending'] or source['generated_water_sccs']!=1:
        raise ValueError(('Connected source audit failed',source['errors'],source['pending']))
    old,old_plan,history=load_terrain(parent)
    tables=build_tables(old,old_plan,view,metadata['geometry_plan'],physical_graph=graph,
                        native_features=metadata['native_chart_features'])
    host=verify_candidate_migration(tables,view)
    metadata['candidate533_migration']=stage_candidate_migration(layer,tables,
        refresh_native_maps=[view.identities[n] for n in ['PacifidlogTown','PacifidlogTown_House3']])
    metadata['candidate533_migration_history']=history
    metadata['candidate533_migration_host_proof']=host
    metadata['migration']['final_version']=3
    # Save code may not change a single physical audit input behind the graph.
    # This authenticates the completed overlay without repeating the same graph.
    for path,wanted in source['input_sha256'].items():
        if hashlib.sha256(view.read(path)).hexdigest()!=wanted:
            raise ValueError(('Save migration changed audited physical input',path))
    view.assert_unchanged()
    metadata.update(source_audit_passed=True,native_validated=False,release_eligible=False,
                    public_roms_updated=False,NATIVE_CONTRACT_FINALIZED=False)
    metadata['pending_obligations']=[
        'current compiled native coast/cave/port/Dive/camera and field-control proofs',
        'old battery Continue/menu-SAVE/new Continue on version3, all editions',
        'reachable ecology/DEX/edition caps and browser/Pages final checks',
        'final publication verification before requested PR']
    cache=checked_cache(cache_freeze,before) if cache_freeze is not None else None
    if evidence is not None:
        evidence=Path(evidence).resolve()
        if evidence==parent or evidence.is_relative_to(parent) or evidence==target or evidence.is_relative_to(target):
            raise ValueError('Evidence must be outside immutable/new sources')
        evidence.mkdir(parents=True,exist_ok=True)
        for name,report in [('migration-tables',tables),('migration-host',host),('source',source),('banks',banks)]:
            (evidence/(name+'.json.gz')).write_bytes(gzip.compress(json.dumps(report,sort_keys=True,separators=(',',':')).encode(),mtime=0))
    if verify_prefix(parent,complete=True)!=before:
        raise ValueError('Immutable source changed before materialization')
    shutil.copytree(parent,target,copy_function=shutil.copy2,symlinks=False)
    verify_prefix(target,complete=True)
    if cache is not None:
        metadata['build_cache']=seed_build_cache(cache,target,set(layer.expected)|set(layer.outputs)|{p.name for p in parent.glob('.journey-*')})
    layer.source=target;layer.marker=target/'.journey-atlas-surf-layout'
    result=layer.finish(**metadata)
    if verify_prefix(parent,complete=True)!=before:
        raise ValueError('Immutable source changed during isolated preparation')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('target','parent','source-review','native-travel-proofs','native-travel-source'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--cache-freeze',type=Path);parser.add_argument('--evidence',type=Path)
    a=parser.parse_args();result=prepare(a.target,a.parent,a.source_review,a.native_travel_proofs,
        a.native_travel_source,cache_freeze=a.cache_freeze,evidence=a.evidence)
    print(json.dumps(dict(source=str(a.target),maps=result['geometry_plan']['map_count'],
        source_audit_passed=result['source_audit_passed'],migration_version=3,native_validated=False,release_eligible=False)))
