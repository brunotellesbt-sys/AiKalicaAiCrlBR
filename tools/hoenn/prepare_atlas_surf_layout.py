"""Assemble one reconstructed whole Surf source, preserving the immutable171.

Preview is entirely staged in memory. Materialization uses a new private copy
with no shared writable inodes. The marker records unresolved obligations and
is never a release certificate. Public ROM replacement is a separate operation
requiring current source/native/edition proofs; this preparer cannot publish.
"""
import argparse
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import shutil

from atlas_surf_adapters import stage_bindings
from atlas_surf_coasts import stage_route114_closure,stage_closed_native_connections
from atlas_surf_dives import reserve_patches,stage as stage_dives
from atlas_surf_dive_access import attach_accesses
from atlas_surf_ecology import stage as stage_ecology
from atlas_surf_layer import stage_geometry
from atlas_surf_legacy import stage_navigation_prune
from atlas_surf_names import stage as stage_names
from atlas_surf_marker import stage as stage_marker
from atlas_surf_overlay import OverlaySource
from atlas_surf_physical import stage as stage_physical
from atlas_surf_ports import stage as stage_ports
from atlas_surf_registrations import _donor
from atlas_surf_runtime import stage as stage_runtime
from atlas_surf_scenery import stage_placements
from atlas_surf_scenery_pack import preserve_native_water_collars,stage_native_water_collars
from atlas_surf_source import Source
from atlas_surf_truth import decode_atlas
from atlas_surf_plan import plan_reserved_geometry
from candidate_layer import Layer
from prepare_generated_area_review import PRIOR,LAYER
from restore_generated_area_review import verify_prefix


ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'docs/design/atlas-surf-layout'
PENDING=(
    'geographic/native SCC review of partial chart pixels and local coast registrations',
    'native coast GPS integration; historical grids disagree at32/33 interfaces',
    'global source SCC including fixed caves and transformed Dive',
    'safe version2 migration of every retired save position and warp reference',
    'all remaining C/script references to retired map IDs',
    'reachable ecology/DEX replacement and real edition caps',
    'whole-map rendering, native controls, batteries and five edition proofs',
)


def _sha(raw):return hashlib.sha256(raw).hexdigest()


def _native_regions(inputs,adapter_plan):
    result=[]
    for row in adapter_plan['native_bounds']:
        row=deepcopy(row);name=row['native_map'];layout=inputs.layout(name)
        a,b,c,d=row['local_rect']
        if not 0<=a<c<=layout['width'] or not 0<=b<d<=layout['height']:
            raise ValueError('Native coast registration extends outside actual terrain')
        binding=next(r for r in adapter_plan['bindings']
                     if r['native_map']==name and r['component']==row['component'])
        if [row['origin'][i]+binding['native_tile'][i] for i in (0,1)]!=binding['global_tile']:
            raise ValueError('Native terrain exclusion differs from its real coast mouth')
        row['evidence']=dict(binding=deepcopy(binding),
                            native_blockdata=layout['blockdata_filepath'],
                            native_blockdata_sha256=_sha(inputs.read(layout['blockdata_filepath'])),
                            native_map_sha256=_sha(inputs.read(f'data/maps/{name}/map.json')),
                            local_registration_only=True)
        result.append(row)
    return result


def _read_evidence(inputs):
    parent=json.loads((EVIDENCE/'parent-inventory.json').read_bytes())
    index=json.loads((EVIDENCE/'whole-layout-placement-review.json').read_bytes())
    result={}
    for key,path in [('coasts','coast-registrations-source.json.gz'),
                     ('scenery','whole-scenery-native-exclusive-source.json.gz')]:
        raw=(EVIDENCE/path).read_bytes();record=index['files'][path]
        if _sha(raw)!=record['gzip_sha256']:
            raise ValueError(('Stored placement evidence compressed bytes changed',path))
        plain=gzip.decompress(raw)
        if _sha(plain)!=record['json_sha256']:
            raise ValueError(('Stored placement evidence JSON changed',path))
        result[key]=json.loads(plain)
    checkpoint=json.loads((EVIDENCE/'integration-source-checkpoint.json').read_bytes())
    # The extraction binds its own complete native inputs. It remains a source
    # inventory, never an old ROM proof promoted to a reconstructed candidate.
    extraction_path='parent-scenery-extraction.json.gz'
    extraction_raw=(EVIDENCE/extraction_path).read_bytes()
    extraction_pin=next(r for r in checkpoint['reports'] if r['file']==extraction_path)
    extraction_json=gzip.decompress(extraction_raw)
    if _sha(extraction_raw)!=extraction_pin['compressed_sha256'] or _sha(extraction_json)!=extraction_pin['json_sha256']:
        raise ValueError('Frozen whole-scenery extraction changed')
    inventory=json.loads(extraction_json)
    for report in (parent,inventory,result['coasts']):
        for path,expected in report['input_sha256'].items():
            if _sha(inputs.read(path))!=expected:
                raise ValueError(('Frozen native inventory input differs',path))
    if not result['scenery']['complete'] or result['scenery']['unplaced_stamps']:
        raise ValueError('Stored authored scenery placement is incomplete')
    return parent,inventory,result['coasts'],result['scenery']


def compose(source, *, preview_occluded_routes=False, cave_radius=9,coast_proposals=None,
            additional_native_edges=False):
    """Return a complete staged terrain/event candidate plus honest blockers."""
    source=Path(source).resolve();parent_proof=verify_prefix(source,complete=True)
    inputs=Source(source);parent,inventory,coasts,scenery=_read_evidence(inputs)
    truth=decode_atlas(inputs.read('src/data/journey_world_map.h').decode())
    if dict(truth.array_sha256)!=parent['art_sha256']:
        raise ValueError('Immutable world art differs from the inventory')
    # Native local rectangles own their actual terrain, including dry/blocked
    # cells. A mixed chart pixel does not need a fictitious 6x6 native ocean.
    pixels=set(truth.blue_pixels)-{(96,40)}
    pixels.update((x,89) for x in range(128,134));pixels.add((119,104))
    occluded_routes=None
    if preview_occluded_routes:
        from atlas_surf_occluded_routes import extract_occluded_routes
        hidden,occluded_routes=extract_occluded_routes(inputs,truth)
        pixels.update(hidden)
        from atlas_surf_scenery_pack import rebind_cave_route_water
        scenery=rebind_cave_route_water(inventory,scenery,pixels)
    scenery=preserve_native_water_collars(inputs,inventory,scenery,cave_radius=cave_radius)
    component_inventory=parent['adapters']
    if additional_native_edges:
        if coast_proposals is None:raise ValueError('New native exits require a complete explicit coast preview')
        from atlas_surf_native_edges import extend_inventory
        component_inventory=extend_inventory(inputs,component_inventory)
    if coast_proposals is not None:
        from atlas_surf_adapters import plan_adapters
        from atlas_surf_geometry import plan_geometry
        if not coast_proposals.get('all_inventory_components_registered') or coast_proposals.get('generated_water_added'):
            raise ValueError('Coast preview must cover all actual components without adding raster water')
        for path,wanted in coast_proposals['input_sha256'].items():
            if _sha(inputs.read(path))!=wanted:raise ValueError(('Coast proposal source changed',path))
        actual=plan_adapters(inputs,component_inventory,plan_geometry(pixels),
                             coast_proposals['registrations'],truth)
        for reservation,binding in zip(actual['reservations'],actual['bindings']):
            row=next(r for r in component_inventory['adapters']
                     if (r['native_map'],r['component'])==(binding['native_map'],binding['component']))
            _,proof=_donor(inputs,row)
            reservation['evidence']=dict(kind='authored-local-native-coast',native_map=binding['native_map'],
                native_component=binding['component'],atlas_evidence=deepcopy(binding['atlas_evidence']),donor_evidence=proof)
        if json.dumps(actual,sort_keys=True)!=json.dumps(coast_proposals['adapter_plan'],sort_keys=True):
            raise ValueError('Coast proposal plan differs from its reauthenticated native registrations')
        coasts=coast_proposals
    adapter_plan=coasts['adapter_plan']
    native_regions=_native_regions(inputs,adapter_plan)
    dive_reservations=attach_accesses(truth,scenery['dive_features']['reservations'],pixels)
    reservations=deepcopy(adapter_plan['reservations']+scenery['reservations']
                          +dive_reservations)
    for row in reservations:
        if row.get('route_water_obstructed'):
            row['route_obstruction_evidence']=dict(kind='fixed-cave-native-whole-footprint',
                fixed_atlas=row['fixed_atlas'],stamp_sha256=row['stamp_sha256'],
                blocked_water_cells=row['route_water_obstructed'],
                source_scc_and_native_travel_still_required=True)
    underlay_obstructions=[]
    if preview_occluded_routes:
        from atlas_surf_occluded_routes import record_native_obstructions
        underlay_obstructions=record_native_obstructions(reservations,pixels,hidden,occluded_routes)
    plan=reserve_patches(plan_reserved_geometry(pixels,reservations,native_regions=native_regions))
    layer=Layer(source,'atlas-surf-layout',PRIOR+[LAYER])
    retired=parent['coasts']['retired_maps']
    legacy=stage_navigation_prune(layer,retired)
    anchors=inputs.anchors()
    owners_with_anchor=[r['map'] for r in retired if r['map'] in anchors
                        and not r['map'].endswith('_Harbor_Frlg')]
    donors={};owners={};bank_donors={};donor_evidence={}
    for row in plan['chunks']:
        center=[(row['origin'][axis]+(row['width'] if axis==0 else row['height'])//2)//8 for axis in (0,1)]
        owner=row.get('ecology_owner')
        if owner is None:
            owner=min(owners_with_anchor,key=lambda name:(
                abs(anchors[name]['atlas'][0]-center[0])+abs(anchors[name]['atlas'][1]-center[1]),name))
        owners[row['name']]=owner
        if isinstance(row.get('donor'),dict):donors[row['name']]=row['donor'];continue
        # The new Dive patches replace the old generic coast markers. All
        # five require the full native General/Mossdeep bank pair, including
        # Rustboro/Dewford whose old marker maps used a different secondary.
        donor_owner='JourneyHoennNorthSea' if row.get('kind')=='dive' else row.get('donor',owner)
        layout=inputs.layout(donor_owner)
        banks=tuple(layout[k] for k in ('primary_tileset','secondary_tileset','layout_version'))
        if banks not in bank_donors:
            spec,proof=_donor(inputs,dict(native_map=donor_owner,source_wet_edge_witnesses=[]))
            bank_donors[banks]=spec;donor_evidence[donor_owner]=proof
        donors[row['name']]=bank_donors[banks]
    plan,geometry=stage_geometry(layer,plan,donors)
    runtime=stage_runtime(layer,plan);physical=stage_physical(layer,plan)
    objects=stage_placements(layer,inputs,inventory,scenery['placements'])
    fringe=stage_native_water_collars(layer,scenery)
    from atlas_surf_old_perimeter import stage as stage_old_perimeter
    old_perimeter=stage_old_perimeter(layer,inputs,plan,scenery['placements'])
    stage_bindings(layer,adapter_plan,retired_maps=[r['map'] for r in retired])
    route114=stage_route114_closure(layer)
    from atlas_surf_three_port import stage as stage_three_port
    three_port=stage_three_port(layer,inputs)
    dives=stage_dives(layer,plan,donor=dict(map='Route127',tile=[72,49]))
    ecology=stage_ecology(layer,owners);names=stage_names(layer,plan,owners)
    marker=stage_marker(layer)
    ports=stage_ports(layer,inputs)
    from atlas_surf_pacifidlog_captain import stage as stage_pacifidlog_captain
    pacifidlog_captain=stage_pacifidlog_captain(layer,inputs)
    from atlas_surf_slateport_rocks import stage as stage_slateport_rocks
    slateport_rocks=stage_slateport_rocks(layer,inputs)
    from atlas_surf_native_scenery import repair as repair_native_scenery
    native_scenery=repair_native_scenery(layer)
    closed_native=stage_closed_native_connections(layer,inputs,retired,route114_closure=route114)
    from atlas_surf_retirement import stage as stage_retirement
    retirement=stage_retirement(layer,retired,objects['relocated_events'])
    from atlas_surf_migration import stage as stage_migration
    migration=stage_migration(layer,inputs,plan,scenery['placements'],objects['relocated_events'],
                              retired_maps=retired,scenery_inventory=inventory)
    inputs.assert_unchanged()
    view=OverlaySource(layer)
    for row in plan['chunks']:
        if view.identities[row['name']] != (row['group_index']<<8)|row['number']:
            raise ValueError('Staged compiled map identity disagrees with its physical rectangle')
    art_after=decode_atlas(view.read('src/data/journey_world_map.h').decode())
    if dict(art_after.array_sha256)!=dict(truth.array_sha256):
        raise ValueError('Source preparation altered immutable world art')
    view.assert_unchanged()
    metadata=dict(schema='atlas-surf-layout-preparation/v1',reconstructed_not_recovered=True,
                  parent=parent_proof,geometry_plan=plan,geometry=geometry,runtime=runtime,
                  physical=physical,objects=objects,native_water_fringe=fringe,
                  dives=dives,ecology=ecology,names=names,ports=ports,legacy=legacy,
                  pacifidlog_captain=pacifidlog_captain,
                  slateport_rocks=slateport_rocks,
                  native_scenery=native_scenery,route114=route114,
                  three_port=three_port,
                  old_perimeter=old_perimeter,
                  player_marker=marker,
                  closed_native_faces=closed_native,retirement=retirement,migration=migration,
                  adapter_plan=adapter_plan,donor_evidence=donor_evidence,
                  coast_proposals_preview=coast_proposals is not None,
                  additional_native_edges_preview=additional_native_edges,
                  occluded_routes_preview=occluded_routes,
                  occluded_routes_native_obstructions=underlay_obstructions,
                  owner_mapping=owners,art_sha256=dict(truth.array_sha256),
                  expected_retired_maps=retired,pending_obligations=list(PENDING),
                  source_audit_passed=False,native_validated=False,release_eligible=False,
                  NATIVE_CONTRACT_FINALIZED=False,public_roms_updated=False)
    return layer,metadata


def _derived_cache_path(relative):
    """Recognize known make outputs; leave every unknown path for make."""
    if relative.parts[0]=='build':
        return relative.suffix in ('.o','.d','.s','.a')
    if relative.parts[0]=='graphics':
        return relative.name.endswith((
            '.1bpp','.4bpp','.8bpp','.gbapal',
            '.4bpp.lz','.8bpp.lz','.gbapal.lz','.bin.lz',
            '.4bpp.smol','.8bpp.smol','.gbapal.smol','.bin.smolTM'))
    if relative.as_posix() in {
        'data/layouts/layouts.inc','data/layouts/layouts_table.inc',
        'include/constants/map_groups.h','include/constants/layouts.h',
        'include/constants/map_event_ids.h','src/data/map_group_count.h',
        'data/maps/connections.inc','data/maps/groups.inc',
        'data/maps/events.inc','data/maps/headers.inc',
        'include/constants/region_map_sections.h',
        'src/data/region_map/region_map_entries.h',
    }:
        return True
    return (len(relative.parts)==4 and relative.parts[:2]==('data','maps')
            and relative.name in ('header.inc','events.inc','connections.inc'))


def seed_build_cache(cache,target,protected_paths):
    """Copy only derived artifacts; verified/staged source always wins."""
    cache,target=Path(cache),Path(target);count=0;copied_bytes=0
    protected=set(protected_paths)|{'.source-acquired.json'}
    for before in cache.rglob('*'):
        if not before.is_file():continue
        relative=before.relative_to(cache);name=relative.as_posix()
        if name in protected or relative.parts[0].startswith('.'):
            continue
        if not _derived_cache_path(relative):
            continue
        after=target/relative
        if after.exists():continue
        after.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(before,after)
        count+=1;copied_bytes+=after.stat().st_size
    return dict(kind='private-derived-build-cache-copy',files=count,bytes=copied_bytes,
                verified_source_overwritten=False,shared_writable_inodes=False)


def prepare(source,clone_from=None,*,preview_output=None,build_cache_from=None,
            preview_occluded_routes=False):
    target=Path(source).resolve()
    parent=Path(clone_from).resolve() if clone_from is not None else target
    if clone_from is not None and target.exists():
        raise ValueError('Preserve the existing candidate or partial preparation; choose a new private path')
    if preview_occluded_routes and preview_output is None:
        raise ValueError('Occluded-route preview cannot materialize a source before candidate-save identity review')
    layer,metadata=compose(parent,preview_occluded_routes=preview_occluded_routes)
    if preview_output is not None:
        report=dict(metadata,prepared_sha256={p:_sha(raw) for p,raw in layer.outputs.items()},
                    source_written=False)
        Path(preview_output).write_text(json.dumps(report,indent=2)+'\n')
        return report
    if clone_from is None:
        raise ValueError('Materialization requires a new private --clone-from copy; the parent is immutable')
    if target==parent or target.is_relative_to(parent):
        raise ValueError('Private source destination may not replace or nest in its immutable parent')
    cache_proof=None
    if build_cache_from is not None:
        cache_proof=verify_prefix(Path(build_cache_from),complete=True)
        if cache_proof['source_manifest_sha256']!=metadata['parent']['source_manifest_sha256']:
            raise ValueError('Build cache sources do not match the immutable parent')
    shutil.copytree(parent,target,copy_function=shutil.copy2,symlinks=False)
    verify_prefix(target,complete=True)
    if cache_proof is not None:
        metadata['build_cache']=seed_build_cache(build_cache_from,target,
            set(layer.expected)|set(layer.outputs)|{p.name for p in parent.glob('.journey-*')})
        metadata['build_cache']['source_manifest_sha256']=cache_proof['source_manifest_sha256']
    layer.source=target;layer.marker=target/'.journey-atlas-surf-layout'
    report=layer.finish(**metadata)
    verify_prefix(parent,complete=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--clone-from',type=Path)
    parser.add_argument('--preview-output',type=Path)
    parser.add_argument('--build-cache-from',type=Path)
    parser.add_argument('--preview-occluded-routes',action='store_true',
        help='Preview authenticated underlay only; requires --preview-output until candidate-save identities are reviewed')
    args=parser.parse_args()
    report=prepare(args.source,args.clone_from,preview_output=args.preview_output,build_cache_from=args.build_cache_from,
                   preview_occluded_routes=args.preview_occluded_routes)
    print(json.dumps(dict(maps=report['geometry_plan']['map_count'],
                         prepared_files=len(report['prepared_sha256']),
                         pending=report['pending_obligations'],release_eligible=False),indent=2))
