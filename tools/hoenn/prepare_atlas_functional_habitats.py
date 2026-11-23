"""Prepare the narrow sand habitat repair in a fresh authenticated source."""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path

from atlas_legendary_chambers import load_current, stage as stage_rooms, refresh_saved_objects
from atlas_large_cave_exteriors import stage as stage_exteriors, stage_save_rescues
from atlas_sand_habitats import stage as stage_sand, OWNERS
from atlas_dex_retired_habitats import relocate
from badge_story_layer import read
from candidate_layer import Layer
from prepare_generated_area_review import PRIOR, LAYER
from prepare_legendary_chambers import clone_authenticated
from prepare_atlas_surf_redesign import source_audit
from validate_atlas_surf_ecology_source import census

ROOT=Path(__file__).resolve().parents[2]


def load(path):
    path=Path(path);raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def dump(path,value):
    path.write_bytes(gzip.compress(json.dumps(value,sort_keys=True,separators=(',',':')).encode(),mtime=0))


def replay(parent,reference):
    layer,meta=load_current(parent)
    rooms=stage_rooms(layer,reference);exteriors=stage_exteriors(layer,meta)
    meta['large_cave_exteriors']=exteriors;meta['legendary_individual_chambers']=rooms
    refresh_saved_objects(layer,rooms['changed_parent_maps']+['MAP_'+r['map'].upper() for r in exteriors['maps']])
    stage_save_rescues(layer,exteriors);meta['migration']['final_version']=8
    return layer,meta


def prepare(parent,reference,cache_freeze,target,output):
    target,output=Path(target).resolve(),Path(output).resolve()
    if target.exists():raise ValueError('Preserve existing private source')
    output.mkdir(parents=True,exist_ok=True)
    frozen=load(cache_freeze);cache=Path(frozen['source'])
    cache_meta=load(cache/'.journey-atlas-surf-layout')
    expected=Layer(cache,'atlas-surf-layout',PRIOR+[LAYER]).expected
    expected.update(frozen['prepared_sha256'])
    for name,digest in expected.items():
        assert hashlib.sha256((cache/name).read_bytes()).hexdigest()==digest,name
    layer,meta=replay(parent,reference)
    baseline=load(ROOT/'docs/design/atlas-surf-layout/ecology-parent-source.json.gz')
    catalog=load(ROOT/'tools/hoenn/catalog_metadata.json')['species']
    original=read(layer,'src/data/journey_world_dex_locations.h').decode()
    # Independently reproduce C before extending its verified source.
    c_census=load(ROOT/'docs/design/legendary-chambers-review/compiled-c-v8/ecology-source/graph-bounded.json.gz')
    c_header,_=relocate(original,baseline,c_census,meta['geometry_plan'],catalog)
    c_outputs=dict(layer.outputs);c_outputs['src/data/journey_world_dex_locations.h']=c_header.encode()
    assert {n:hashlib.sha256(v).hexdigest() for n,v in c_outputs.items()}==frozen['prepared_sha256']
    meta['sand_land_habitats']=stage_sand(layer)
    view,physical,graph,banks=source_audit(layer,meta)
    print('Unchanged physical graph and private source replay PASS',flush=True)
    reachable=defaultdict(set)
    for key,label in zip(graph.keys,graph.labels):
        if label==graph.ocean_component:
            name,x,y=graph.location(key//32);reachable[name].add((x,y))
    retired=[r['map'] if isinstance(r,dict) else r for r in meta['retirement']['retired_maps']]
    after=census(view,retired_maps=retired,reachable_cells=reachable)
    header,dex=relocate(original,baseline,after,meta['geometry_plan'],catalog,restore_inactive_from_owners=OWNERS)
    layer.stage('src/data/journey_world_dex_locations.h',header)
    meta['retired_habitat_dex_relocation']=dex
    meta['source_audit_passed']=True
    print('Exact reachable AREA relocation PASS:',len(dex['relocated']),'restored',sum(r['restored_land_trigger'] for r in dex['relocated']),flush=True)
    dump(output/'graph-bounded.json.gz',after);dump(output/'physical-source.json.gz',physical)
    dump(output/'dex-relocation.json.gz',dex);dump(output/'banks.json.gz',banks)
    # Share authenticated C inputs only. All compiled files and changed inputs
    # use private inodes, so rebuilding cannot mutate C or earlier releases.
    shared=clone_authenticated(cache,target,expected,omit_compiled_artifacts=True)
    dump(output/'readonly-source-sharing.json.gz',shared)
    layer.source=target;layer.marker=target/'.journey-atlas-surf-layout'
    result=layer.finish(**meta)
    assert cache_meta==load(cache/'.journey-atlas-surf-layout')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('parent','reference','cache-freeze','target','output'):p.add_argument('--'+n,type=Path,required=True)
    prepare(**vars(p.parse_args()))
