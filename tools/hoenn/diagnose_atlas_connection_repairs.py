"""Reproduce new native coast proposals and independently audit physical water.

This source diagnostic cannot materialize a source, build or publish a ROM.
The southern Route128 outlet is an explicit geographic choice, not a search
for arbitrary nearby water. Compiled identities/saves need review before any
new partition is adopted; source reductions never certify native travel.
"""
import argparse
from collections import Counter
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path

from atlas_surf_bank_edges import audit_edges,requirement_scope
from atlas_surf_classification import census_native_bounds
from atlas_surf_geometry import plan_geometry
from atlas_surf_layout_requirements import build_requirements
from atlas_surf_occluded_routes import extract_occluded_routes
from atlas_surf_overlay import OverlaySource
from atlas_surf_reachability import audit
from atlas_surf_registrations import AUTHORED_COASTS,propose_registrations
from atlas_surf_source import Source
from atlas_surf_truth import decode_atlas
from prepare_atlas_surf_layout import _read_evidence,compose
from restore_generated_area_review import verify_prefix


def run(source,output):
    source,output=Path(source).resolve(),Path(output).resolve()
    if output==source or output.is_relative_to(source):raise ValueError('Output must be outside immutable source')
    before=verify_prefix(source,complete=True);inputs=Source(source)
    parent,inventory,old,scenery=_read_evidence(inputs)
    truth=decode_atlas(inputs.read('src/data/journey_world_map.h').decode())
    pixels=set(truth.blue_pixels)-{(96,40)}
    pixels.update((x,89) for x in range(128,134));pixels.add((119,104))
    hidden,_=extract_occluded_routes(inputs,truth);pixels.update(hidden)
    authored=deepcopy(AUTHORED_COASTS)
    authored['Route128',1]=[choice for choice in authored['Route128',1] if choice[0]=='down']
    coasts=propose_registrations(inputs,parent['adapters'],truth,plan_geometry(pixels),authored=authored,
        protected_reservations=scenery['reservations']+scenery['dive_features']['reservations'],
        allow_extended_native_contacts=True)
    if not coasts['all_inventory_components_registered']:raise ValueError(coasts['conflicts'])
    layer,metadata=compose(source,preview_occluded_routes=True,coast_proposals=coasts)
    view=OverlaySource(layer);native=census_native_bounds(inputs,coasts)
    requirements=build_requirements(view,metadata,parent,native)
    banks=audit_edges(view,scope=requirement_scope(metadata,requirements))
    requirements['authenticated_bank_pairs']=banks['authenticated_bank_pairs']
    report,graph=audit(view,plan=metadata['geometry_plan'],requirements=requirements,max_states=2000000,return_graph=True)
    counts=Counter()
    for chunk in metadata['geometry_plan']['chunks']:
        for y in range(chunk['height']):
            for x in range(chunk['width']):
                point=[chunk['name'],x,y]
                if view.water(*point):counts[graph.component(point,1)]+=1
    largest=counts.most_common(1)[0][0]
    # Diagnostic membership is separate from the audit's actual PASS gates.
    membership={}
    for kind in ('ports','caves'):
        rows=report['checks'][kind]
        membership[kind]=[r for r in rows if all(value==largest for value in
            (r.get('components') or [r.get('dry_component'),r.get('water_component')]))]
    old_plan=json.loads(gzip.decompress((Path(__file__).resolve().parents[2]/
        'docs/design/atlas-surf-layout/whole-layout-composed-source.json.gz').read_bytes()))['geometry_plan']
    identity=lambda p:{r['name']:(r['group_index'],r['number'],r['origin'],r['width'],r['height']) for r in p['chunks']}
    output.mkdir(parents=True,exist_ok=True);files={}
    for label,value in [('coasts',coasts),('native',native),('banks',banks),('source',report),
                        ('geometry',metadata['geometry_plan'])]:
        raw=json.dumps(value,sort_keys=True,separators=(',',':')).encode()+b'\n'
        packed=gzip.compress(raw,mtime=0);name=label+'.json.gz';(output/name).write_bytes(packed)
        files[name]=dict(sha256=hashlib.sha256(packed).hexdigest(),json_sha256=hashlib.sha256(raw).hexdigest())
    after=verify_prefix(source,complete=True)
    if before!=after:raise ValueError('Immutable source changed')
    result=dict(schema='atlas-connection-repair-source-diagnostic/v1',source=before,
        generated_maps=metadata['geometry_plan']['map_count'],generated_water_sccs=report['generated_water_sccs'],
        largest_component=largest,largest_component_cells=counts[largest],
        diagnostic_largest_component_membership={kind:len(rows) for kind,rows in membership.items()},
        cave_and_port_checks=report['checks']['caves']+report['checks']['ports'],
        source_passed=report['passed'],errors=dict(Counter(r['kind'] for r in report['errors'])),
        candidate_geometry_unchanged=identity(old_plan)==identity(metadata['geometry_plan']),
        new_partition_needs_candidate_save_migration=True,old_perimeter=metadata['old_perimeter'],
        prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in layer.outputs.items()},
        files=files,source_unchanged=True,public_ROMs_updated=False,native_ROM_validated=False,final_release_validated=False)
    (output/'review.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();r=run(args.source,args.output)
    print(json.dumps({k:r[k] for k in ('generated_maps','generated_water_sccs','source_passed','candidate_geometry_unchanged','final_release_validated')},indent=2))
