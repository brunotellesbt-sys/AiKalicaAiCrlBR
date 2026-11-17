"""Reproduce reachable ecology and explicit remaining Dex claims, read-only.

The frozen ROM/source is authenticated before and after. Family preservation
and the stricter per-species/per-area Dex contract are separate results. This
diagnostic never edits encounter data, the Dex header, ROMs or release flags.
"""
import argparse
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path

from atlas_surf_bank_edges import audit_edges,requirement_scope
from atlas_surf_classification import census_native_bounds
from atlas_surf_ecology import repair_dex_locations
from atlas_surf_layout_requirements import build_requirements
from atlas_surf_reachability import audit
from atlas_surf_source import Source
from candidate_layer import Layer
from prepare_atlas_surf_layout import _read_evidence
from prepare_generated_area_review import PRIOR,LAYER
from restore_generated_area_review import verify_prefix
from validate_atlas_surf_ecology_source import census,compare

ROOT=Path(__file__).resolve().parents[2]


def load(path):
    path=Path(path);raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def run(frozen_path,parent,coasts_path,output):
    frozen=load(frozen_path);source=Path(frozen['source']).resolve();parent=Path(parent).resolve();output=Path(output).resolve()
    if any(output==p or output.is_relative_to(p) for p in (source,parent)):
        raise ValueError('Diagnostic output must be outside frozen/parent sources')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    metadata=load(source/'.journey-atlas-surf-layout');coasts=load(coasts_path)
    expected=Layer(source,'atlas-surf-layout',PRIOR+[LAYER]).expected;expected.update(metadata['prepared_sha256'])
    if json.dumps(coasts['adapter_plan'],sort_keys=True)!=json.dumps(metadata['adapter_plan'],sort_keys=True):
        raise ValueError('Coast classification differs from the frozen compiled plan')
    before=verify_prefix(parent,complete=True)
    if before['source_manifest_sha256']!=metadata['parent']['source_manifest_sha256']:
        raise ValueError('Ecology baseline parent differs from the compiled candidate')
    def unchanged():
        for key,name in [('rom_sha256','pokeemerald.gba'),('elf_sha256','pokeemerald.elf'),('marker_sha256','.journey-atlas-surf-layout')]:
            if sha(source/name)!=frozen[key]:raise ValueError(('Frozen artifact changed',name))
        for name,wanted in expected.items():
            if sha(source/name)!=wanted:raise ValueError(('Frozen source changed',name))
    unchanged();inputs=Source(source);native_parent=Source(parent);inventory,_,_,_=_read_evidence(native_parent)
    native=census_native_bounds(native_parent,coasts);req=build_requirements(inputs,metadata,inventory,native)
    banks=audit_edges(inputs,scope=requirement_scope(metadata,req));req['authenticated_bank_pairs']=banks['authenticated_bank_pairs']
    physical,graph=audit(inputs,plan=metadata['geometry_plan'],requirements=req,max_states=2000000,return_graph=True)
    if not physical['passed'] or physical['errors'] or physical['pending']:
        raise ValueError(('Ecology requires the actual passing physical graph',physical['errors'],physical['pending']))
    reachable={}
    for name in graph.names:
        layout=inputs.layout(name)
        reachable[name]=[[x,y] for y in range(layout['height']) for x in range(layout['width'])
                         if graph.component([name,x,y])==graph.ocean_component]
    retired=[r['map'] for r in metadata['expected_retired_maps']]
    retired += [r['name'] for r in metadata['geometry_plan']['retired_candidate_placeholders']]
    full=census(inputs,owner_mapping=metadata['owner_mapping'],retired_maps=retired)
    bounded=census(inputs,owner_mapping=metadata['owner_mapping'],retired_maps=retired,reachable_cells=reachable)
    baseline=load(ROOT/'docs/design/atlas-surf-layout/ecology-parent-source.json.gz');comparison=compare(baseline,full)
    new_families={cap:{int(family) for family,rows in full['family_witnesses'][cap].items()
                      if any(r['map'] in metadata['owner_mapping'] for r in rows)} for cap in ('493','1025')}
    missing={cap:sorted(families-set(bounded['families'][cap])) for cap,families in new_families.items()}
    # Ordinary rectangles omit ecology_owner in the geometry-only report.
    # Bind it from the actual compiled alias census without changing terrain.
    assert bounded['aliases']==metadata['owner_mapping']
    dex_plan=deepcopy(metadata['geometry_plan'])
    for row in dex_plan['chunks']:
        owner=metadata['owner_mapping'][row['name']]
        if row.get('ecology_owner',owner)!=owner:raise ValueError('Dex plan owner conflicts with compiled lookup')
        row['ecology_owner']=owner
    catalog=load(ROOT/'tools/hoenn/catalog_metadata.json')['species']
    try:
        _,dex=repair_dex_locations(inputs.read('src/data/journey_world_dex_locations.h').decode(),baseline,bounded,dex_plan,catalog)
        dex=dict(passed=True,proposal_only_not_staged=True,report=dex)
    except ValueError as error:
        detail=error.args[0]
        dex=dict(passed=False,proposal_only_not_staged=True,reason=detail[0] if isinstance(detail,tuple) else str(detail))
        if isinstance(detail,tuple) and len(detail)>1:
            dex['claims']=detail[1];dex['claim_count']=len(detail[1])
    output.mkdir(parents=True,exist_ok=True)
    for name,report in [('full',full),('graph-bounded',bounded),('comparison',comparison),('physical-source',physical),('dex-blocker',dex)]:
        (output/(name+'.json.gz')).write_bytes(gzip.compress(json.dumps(report,sort_keys=True,separators=(',',':')).encode(),mtime=0))
    summary=dict(kind='frozen-connected-ecology-diagnostic',ROM_sha256=frozen['rom_sha256'],
        ELF_sha256=frozen['elf_sha256'],marker_sha256=frozen['marker_sha256'],source_files_checked=len(expected),
        physical_graph_passed=True,generated_water_sccs=physical['generated_water_sccs'],family_comparison=comparison,
        graph_bounded_family_counts=bounded['catchable_family_counts'],all_new_route_families_reachable=not any(missing.values()),
        missing_new_route_families=missing,DEX_source_proposal_passed=dex['passed'],DEX_blocked_claim_count=dex.get('claim_count'),
        unchanged_native_campaign_outside_graph_not_newly_certified=True,
        native_encounters_and_caps_not_validated_here=True,source_or_ROM_written=False,final_release_validated=False)
    unchanged();inputs.assert_unchanged();native_parent.assert_unchanged()
    if verify_prefix(parent,complete=True)!=before:raise ValueError('Immutable parent changed during ecology audit')
    (output/'review.json').write_text(json.dumps(summary,indent=2)+'\n');return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('frozen','parent','coasts','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=run(a.frozen,a.parent,a.coasts,a.output);print(json.dumps(r,indent=2))
