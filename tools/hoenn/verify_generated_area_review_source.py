"""Reject incomplete, stale or unbound layer-171 source evidence."""
import hashlib
from pathlib import Path

import generated_area_review_contract as contract
from verify_sevii_route_boundaries_source import _sha, _integer, _rom_range, _relative, _true
from validate_generated_area_review_source import (PASSAGE, BEACH, SEA, HORIZONTE,
    HORIZONTE_CLOSURES, MOUTHS, CLIFF, CLIFF_DONORS, PORT_QUARTERS, PORT_MAPS,
    RUNTIME_SYMBOLS, VISIBLE_LIMITS, OUTER_WORDS, BOAT_SIZES, BOARDING_POINTS, BOAT_EVENTS)


def _names(value):
    assert isinstance(value,list) and value==sorted(set(value))
    assert all(isinstance(v,str) and v for v in value)
    return set(value)


def _cell(row):
    assert isinstance(row,list) and len(row)==2
    for number in row: _integer(number)
    return tuple(row)


def _navigation(row,compiled):
    _true(row,('all_surviving_cells_retain_global_connectivity','only_explicitly_reviewed_new_passages','every_physical_opening_preserved',
               'directed_connectivity_preserved','native_disabled_connection_flags_honored'))
    names=_names(row['network_maps'])
    assert names<=compiled
    assert row['network_maps_checked']==len(names)
    for key in ('global_components_before','global_components_after'):
        _integer(row[key],1)
    assert row['global_components_after']<=row['global_components_before']
    for key in ('directed_components_before','directed_components_after'):_integer(row[key],1)
    assert row['directed_components_after']<=row['directed_components_before']
    _integer(row['old_component_merges'])
    assert _names(row['allowed_merge_maps']) in (set(),{BEACH,SEA})
    assert row['old_component_merges']==0 or row['allowed_merge_maps']==sorted((BEACH,SEA))
    for key in ('removed_cells','added_cells'):
        cells=row[key]
        assert isinstance(cells,list) and len({tuple(c) for c in cells})==len(cells)
        for name,x,y in cells:
            assert name in names
            _cell([x,y])
    connections=row['physical_connections']
    assert len(connections)==row['physical_connections_checked']
    seen=set()
    for connection in connections:
        assert connection['map'] in names and connection['map'] not in seen
        seen.add(connection['map'])
        _integer(connection['openings'],1)
        _sha(connection['openings_sha256'])
    return row


def verify_report(report,directory,romsha):
    from prepare_generated_area_review import PRIOR
    directory=Path(directory).resolve()
    assert report['kind']=='generated-area-review-source'
    _true(report,('passed','compiled_rom','independent_replay','prefix_markers_unchanged',
                  'unrelated_source_files_unchanged','scripts_and_atlas_art_unchanged','source_gallery_not_emulator',
                  'stable_source_rechecked','stable_rom_elf_rechecked'))
    assert report['preflight'] is False
    assert report['full_campaign_playthrough'] is False
    assert len(PRIOR)==170 and report['layers']==PRIOR+[contract.SCOPE]
    assert report['parent_rom_sha256']==contract.PARENT_ROM_SHA256
    assert contract.PREPARED_SHA256,'Final generated-area source hashes are not pinned'
    for name,sha in contract.PREPARED_SHA256.items():
        _relative(name);_sha(sha)
    assert report['prepared_sha256']==contract.PREPARED_SHA256
    assert report['changed_files']==sorted(contract.PREPARED_SHA256)
    for sha in (romsha,report['rom_sha256'],report['elf_sha256']): _sha(sha)
    assert report['rom_sha256']==romsha!=contract.PARENT_ROM_SHA256,'Stale source ROM'
    assert report['elf_sha256']!=contract.PARENT_ELF_SHA256,'Stale source ELF'
    _integer(report['source_hashes_checked'],len(contract.PREPARED_SHA256))
    _integer(report['elf_rom_load_segments_checked'],1)

    extension=report['south_passage_audit']
    assert extension['map']==PASSAGE and extension['dimensions']==[8,32]
    assert extension['new_map_count']==extension['old_map_count']+1
    _integer(extension['old_map_count'],1)
    assert extension['map_group']=='JourneyWorldOcean' and extension['appended_map_number']==67
    assert extension['existing_mouth_cells']==18 and extension['native_cliff_cells']==4
    assert extension['gps_values_appended']==256 and extension['new_water_cells']==192
    assert extension['maximum_gps_step']<=1
    _integer(extension['maximum_gps_step'])
    _true(extension,('old_gps_values_unchanged','old_map_ids_events_warps_coordinates_and_atlas_art_preserved',
                     'two_reciprocal_connections','shared_gps_seams_exact','only_empty_map_script_added',
                     'native_encounter_family_preserved'))
    assert extension['native_cliff_donors']==[dict(map=n,cell=[x,y],word=w) for n,x,y,w in CLIFF_DONORS]
    context=extension['complete_cliff_context']
    assert len(context)==10 and len({tuple(r['cell']) for r in context})==10
    assert {(tuple(r['cell']),r['word']) for r in context}=={
        ((7,37),0x0517),((7,38),0x0473),((7,39),0x0473),((6,38),0x1128),((6,39),0x112C),
        ((32,37),0x051F),((32,38),0x0475),((32,39),0x0475),((33,38),0x1129),((33,39),0x112A)}

    geometry=report['geometry_audit']
    names=_names(geometry['map_names'])
    assert geometry['maps']==len(names)==extension['new_map_count']
    changed=_names(geometry['changed_maps'])
    assert changed=={HORIZONTE,BEACH,SEA,PASSAGE,'FourIsland_Frlg','FiveIsland_Frlg','SixIsland_Frlg',
                     'ThreeIsland_Port_Frlg','SevenIsland_SevaultCanyon_Entrance_Frlg'}<=names
    _true(geometry,('all_old_map_metadata_preserved_except_two_appended_connections','all_old_layout_metadata_unchanged',
                    'all_old_borders_unchanged','only_reviewed_native_geometry_changed'))
    cells=geometry['cells']
    assert isinstance(cells,list) and len(cells)==geometry['changed_cells']
    observed={}
    for row in cells:
        assert row['map'] in changed
        key=(row['map'],*_cell(row['cell']))
        assert key not in observed,'Duplicate geometry cell'
        for key2 in ('before','after'):
            _integer(row[key2]);assert row[key2]<=65535
        assert row['before']!=row['after']
        observed[key]=(row['before'],row['after'])
    assert {r['map'] for r in cells}==changed-{PASSAGE}
    assert all(observed[key]==(0x1643,0x112B) for key in MOUTHS)
    assert all(observed[key]==pair for key,pair in CLIFF.items())
    assert observed['SixIsland_Frlg',2,29]==(0x1673,0x1273)
    outer=geometry['outer_boundary_cells']
    assert {(r['map'],*r['cell']) for r in outer}==VISIBLE_LIMITS and len(outer)==53
    for row in outer:
        key=row['map'],*_cell(row['cell'])
        assert row['map'] in PORT_MAPS and observed[key]==(row['before'],row['after'])
        assert (row['before'],row['after'])==OUTER_WORDS[key]
        assert row['pure_water_words']==[0x41C6,0x41C7,0x41C7,0x41C6,0,0,0,0]

    portals=report['portal_audit']
    _true(portals,('complete_native_closures','active_entry_exit_events_preserved','active_exit_and_all_npc_approaches_connected'))
    assert portals['reviewed_maps']==[HORIZONTE] and portals['changed_cells']==20
    assert len(portals['objects'])==len(HORIZONTE_CLOSURES)
    portal_keys=set()
    for row,(expected_cells,donor,donor_cell,word) in zip(portals['objects'],HORIZONTE_CLOSURES):
        assert row['map']==HORIZONTE and row['native_donor_map']==donor
        assert row['native_donor_cell']==list(donor_cell) and row['native_word']==word
        _true(row,('whole_footprint','active_events_unchanged'))
        assert {tuple(c['cell']) for c in row['cells']}==set(expected_cells)
        for cell in row['cells']:
            key=HORIZONTE,*_cell(cell['cell'])
            assert observed[key]==(cell['before'],cell['after']) and cell['after']==word
            portal_keys.add(key)
    assert len(portal_keys)==20
    ports=report['port_object_audit']
    assert ports['whole_objects']==4 and ports['changed_art_cells']==9 and ports['whole_native_objects'] is True
    assert len(ports['objects'])==4
    port_keys=set()
    for row,(name,anchor,family,quarters,target,block) in zip(ports['objects'],PORT_QUARTERS):
        assert row['map']==name and row['whole_footprint'] is True and row['anchor']==list(anchor)
        x,y=_cell(row['anchor'])
        assert len(row['before'])==len(row['after'])==4
        assert tuple(word&1023 for word in row['before'])==family
        for q,(before,after) in enumerate(zip(row['before'],row['after'])):
            expected=before if q not in quarters else (before&~1023)|target
            if q in quarters and block:expected=(expected&~0xC00)|0x400
            assert after==expected
            if before!=after:
                key=row['map'],x+q%2,y+q//2
                assert observed[key]==(before,after)
                port_keys.add(key)
    assert len(port_keys)==9
    allowed=portal_keys|port_keys|MOUTHS|set(CLIFF)|{('SixIsland_Frlg',2,29)}|{(r['map'],*r['cell']) for r in outer}
    assert set(observed)==allowed,'Unreviewed geometry cell in source proof'

    guards=report['port_guards']
    _true(guards,('boarding_water_and_dry_elevations_valid','only_six_blocked_boarding_water_restored',
                  'complete_native_sprite_bounds_checked','no_new_boat_obstacles'))
    assert guards['boarding_pairs_checked']==7 and len(guards['boarding_pairs'])==7
    assert {r['island'] for r in guards['boarding_pairs']}=={'One','Two','Three','Four','Five','Six','Seven'}
    for row in guards['boarding_pairs']:
        name,dry,wet=BOARDING_POINTS[row['island']]
        assert row['dry']['map']==row['water']['map']==name
        assert row['dry']['cell']==list(dry) and row['water']['cell']==list(wet)
        for kind,elevation in (('dry',3),('water',1)):
            cell=row[kind]
            assert cell['map'] in PORT_MAPS
            key=(cell['map'],*_cell(cell['cell']))
            for value in (cell['before'],cell['after']):_integer(value);assert value<=65535
            assert cell['after']>>12==elevation and cell['after']&0xC00==0
            assert cell['after']==(0x1273 if key==('SixIsland_Frlg',2,29) and kind=='water' else cell['before'])
            assert key not in observed or (cell['before'],cell['after'])==observed[key]
        assert row['dry']['map']==row['water']['map']
        assert sum(abs(a-b) for a,b in zip(row['dry']['cell'],row['water']['cell']))==1
    assert guards['boat_footprints_checked']==12 and len(guards['boat_footprints'])==12
    seen_boats=set()
    for row in guards['boat_footprints']:
        assert row['map'] in PORT_MAPS and row['graphics_id'] in BOAT_SIZES
        x,y=_cell(row['event_cell']);key=(row['map'],x,y,row['graphics_id'])
        assert key not in seen_boats;seen_boats.add(key)
        width,height=BOAT_SIZES[row['graphics_id']]
        assert row['source_sprite_size']==[width,height]
        left,top=16*x+8-width//2,16*y+16-height
        assert row['pixel_bounds']==[left,top,width,height]
        footprint=[[xx,yy] for yy in range(top//16,(top+height-1)//16+1) for xx in range(left//16,(left+width-1)//16+1)]
        assert row['all_intersected_cells']==footprint
        changes={}
        for cell in row['reviewed_art_changes']:
            cell_key=row['map'],*_cell(cell['cell'])
            assert cell_key in port_keys and cell_key not in changes
            pair=cell['before'],cell['after']
            assert observed[cell_key]==pair and pair[0]&0xFC00==pair[1]&0xFC00 and pair[1]&0xC00==0
            changes[cell_key]=pair
        assert set(changes)=={(row['map'],*cell) for cell in footprint}&set(observed)
    assert seen_boats==BOAT_EVENTS

    camera=report['camera_runtime']
    _true(camera,('visual_queries_only','collision_elevation_movement_and_undefined_grid_unchanged','native_compatibility_checks_preserved'))
    assert isinstance(camera['modified_functions'],list) and camera['modified_functions']
    assert set(camera['modified_functions'])<={'JourneyMarineViewMap','JourneyMarineCornerMetatile','JourneyMarineRectangleDistance','JourneyMarineApronMetatile'}
    cameras=report['camera_audit']
    camera_names=_names(cameras['map_names'])
    assert cameras['unresolved_cells']==0 and cameras['unresolved_scope']=='reviewed-aperture-policy'
    assert cameras['full_world_camera_certified'] is False
    assert cameras['raw_conflicting_cells']==cameras['previous_raw_conflicting_cells']==30
    assert cameras['raw_conflicting_maps']=={'JourneyWorldFill21Right':13,'JourneyWorldSea02':17}
    assert cameras['raw_source_conflicts_unchanged'] is True
    from generated_coast_cameras import SCOPED_MAPS,REPRO_CASES,CONTROL_CASES
    assert _names(cameras['changed_camera_maps'])==set(SCOPED_MAPS)<=camera_names
    cases=cameras['scoped_policy_cases']
    assert len(cases)==len(REPRO_CASES+CONTROL_CASES)
    for row,expected in zip(cases,REPRO_CASES+CONTROL_CASES):
        assert row['case']==expected and row['passed'] is True
        assert row['after']==row['expected']==expected['expected_metatile']
        _integer(row['before']);assert row['before']<=1023
        assert isinstance(row['owner_evidence'],dict) and row['owner_evidence']
    expanded=cameras['expanded_census']
    assert expanded['raw_conflicting_cells']==30 and expanded['raw_conflicting_maps']==cameras['raw_conflicting_maps']
    assert len(expanded['conflicts'])==30 and expanded['raw_conflicts_are_not_claimed_eliminated'] is True
    from generated_coast_cameras import OPENING_MAP,OPENING_NEIGHBOR
    assert cameras['seven_east_openings_source_unchanged'] is True
    openings=cameras['seven_east_openings']
    assert len(openings)==11
    assert [(r['map'],r['neighbor'],r['player'],r['target'],r['direction']) for r in openings]==[
        (OPENING_MAP,OPENING_NEIGHBOR,[16,y],[0,y],'right') for y in range(1,12)]
    census=report['boulder_census']
    census_names=_names(census['map_names'])
    assert census['maps']==len(census_names) and PORT_MAPS|set(SCOPED_MAPS)<=census_names
    assert census['new_partial_objects']==census['mixed_small_and_large_objects']==0
    _true(census,('inherited_context_patterns_preserved','source_census_not_native_camera_proof'))
    from collections import Counter
    assert dict(Counter(row['classification'] for row in census['objects']))==census['classifications']
    assert set(census['classifications'])<={'complete','native_context_variant','outer_continuation'}

    compiled=_names(report['compiled_map_names'])
    reviewed=_names(report['reviewed_maps'])
    assert changed|set(SCOPED_MAPS)<=reviewed<=compiled and camera_names|census_names<=compiled
    water=_navigation(report['surface_navigation'],compiled)
    land=_navigation(report['land_navigation'],compiled)
    assert {tuple(c) for c in land['removed_cells']}=={(HORIZONTE,15,19),(HORIZONTE,30,25)}
    assert land['added_cells']==[]
    assert set(map(tuple,water['added_cells']))==MOUTHS|{(PASSAGE,x,y) for y in range(32) for x in range(1,7)}|{('SixIsland_Frlg',2,29)}
    assert all(tuple(c) in set(observed) for c in water['removed_cells'])
    assert water['allowed_merge_maps']==sorted((BEACH,SEA)) and land['allowed_merge_maps']==[]

    layouts=report['compiled_layouts']
    assert isinstance(layouts,list) and len(layouts)==len(compiled)
    assert {row['map'] for row in layouts}==compiled
    for row in layouts:
        assert isinstance(row['layout'],str) and row['layout']
        assert isinstance(row['symbol'],str) and row['symbol']
        _rom_range(row['address'],28);assert row['address']%4==0
        for key in ('width','height','border_width','border_height'): _integer(row[key],1)
        assert type(row['is_frlg']) is bool
        assert (row['stored_border_width'],row['stored_border_height'])==((row['border_width'],row['border_height']) if row['is_frlg'] else (0,0))
        for key in ('primary_pointer','secondary_pointer'):
            _rom_range(row[key]);assert row[key]%4==0
        assert row['compiled_layout_bytes_match'] is True
        for key,size in (('blockdata',2*row['width']*row['height']),('borderdata',2*row['border_width']*row['border_height'])):
            binding=row[key];path=_relative(binding['file'])
            assert path.parts[:2]==('data','layouts') and path.suffix=='.bin'
            assert binding['bytes']==size
            _sha(binding['sha256']);_rom_range(binding['address'],size)
            if binding['file'] in contract.PREPARED_SHA256:
                assert binding['sha256']==contract.PREPARED_SHA256[binding['file']],'Compiled map not bound to reviewed source'
    projection=report['compiled_gps']
    passage_layout=next(row for row in layouts if row['map']==PASSAGE)
    assert (passage_layout['width'],passage_layout['height'])==(8,32)
    assert projection['symbol']=='sWorldNavigationPixels'
    _integer(projection['bytes'],2*256);assert projection['bytes']%2==0
    _rom_range(projection['address'],projection['bytes']);_sha(projection['sha256'])
    assert set(report['runtime_export_names'])==set(RUNTIME_SYMBOLS) and len(report['runtime_export_names'])==len(RUNTIME_SYMBOLS)
    runtime=report['compiled_runtime']
    assert len(runtime)==len(RUNTIME_SYMBOLS) and {row['symbol'] for row in runtime}==set(RUNTIME_SYMBOLS)
    for row in runtime:
        _integer(row['bytes'],1);_rom_range(row['address'],row['bytes']);_sha(row['sha256'])

    headers=report['compiled_map_headers']
    assert isinstance(headers,list) and len(headers)==len(compiled) and {r['map'] for r in headers}==compiled
    header_by_map={row['map']:row for row in headers}
    layouts_by_map={row['map']:row for row in layouts}
    for row in headers:
        _true(row,('compiled_header_and_connections_match',))
        for key in ('map_group','map_number'):_integer(row[key]);assert row[key]<256
        for key,size in (('address',28),('map_table_address',4),('layout_pointer',28),('events_pointer',20),('scripts_pointer',1)):
            _rom_range(row[key],size);assert row[key]%4==0 or key=='scripts_pointer'
        assert row['layout_pointer']==layouts_by_map[row['map']]['address']
        assert len(row['event_counts'])==4
        for count in row['event_counts']:_integer(count);assert count<256
        connections=row['connections']
        assert type(row['connections_disabled']) is bool
        if row['connections_disabled']:assert connections==[]
        assert row['connection_bytes']==len(connections)*12
        _sha(row['connection_sha256'])
        if connections:
            _rom_range(row['connection_pointer'],8);_rom_range(row['connection_list_pointer'],row['connection_bytes'])
        else:assert row['connection_pointer']==row['connection_list_pointer']==0
        for connection in connections:
            assert connection['direction'] in {'up','down','left','right','dive','emerge'}
            assert type(connection['offset']) is int
            target=header_by_map.get(connection['target'])
            if target is not None:
                assert (connection['map_group'],connection['map_number'])==(target['map_group'],target['map_number'])
    passage=header_by_map[PASSAGE]
    assert passage['map_number']==67 and passage['event_counts']==[0,0,0,0]
    expected_connections={PASSAGE:[('up',0,BEACH),('down',-62,SEA)],
                          BEACH:[('down',0,PASSAGE)],SEA:[('up',62,PASSAGE)]}
    for name,expected in expected_connections.items():
        rows=[(r['direction'],r['offset'],r['target']) for r in header_by_map[name]['connections']]
        assert (rows if name==PASSAGE else rows[-1:])==expected
    grids=report['compiled_gps_grids']
    assert grids['symbol']=='sWorldTileGrids' and grids['compiled_all_map_ids_dimensions_and_offsets_match'] is True
    _integer(grids['grids'],1);assert grids['bytes']==12*grids['grids']
    _rom_range(grids['address'],grids['bytes']);_sha(grids['sha256'])

    assert report['source_gallery_rendered'] is True,'Required before/after full-map source gallery missing'
    captures=report['captures'];files,views=set(),set()
    for row in captures:
        path=_relative(row['file'])
        assert path.as_posix() not in files,'Duplicate source attachment'
        files.add(path.as_posix());_sha(row['sha256'])
        target=(directory/path).resolve()
        assert target.is_relative_to(directory)
        assert hashlib.sha256(target.read_bytes()).hexdigest()==row['sha256'],'Source gallery attachment changed'
        assert row['map'] in reviewed and row['phase'] in {'before','after'}
        _true(row,('full_map','npcs','source_render_not_emulator','label_present'))
        _integer(row['width_tiles'],1);_integer(row['height_tiles'],1)
        exists=not (row['phase']=='before' and row['map']==PASSAGE)
        assert row['map_exists'] is exists and row['absent_parent_panel'] is (not exists)
        layout=layouts_by_map[row['map']]
        assert (row['width_tiles'],row['height_tiles'])==(layout['width'],layout['height'])
        from PIL import Image
        with Image.open(target) as capture:
            assert capture.format=='PNG' and capture.width>=16*row['width_tiles'] and capture.height==16*row['height_tiles']+38
        key=row['phase'],row['map'];assert key not in views;views.add(key)
    assert views=={(phase,name) for phase in ('before','after') for name in reviewed}
    return report
