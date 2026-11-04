"""Bind aquatic ecology proofs to layer 166 while retaining layer 165 as history."""
import hashlib
import json
from pathlib import Path

import coastal_ecology_contract as contract
from package_review_rom import verify as verify_review
from publish_coastal_closures import report_dependencies
from verify_coastal_closures_update import verify_cold_boot,verify_review_mode
from verify_fuchsia_update import ROOT,previous_release
from verify_sevii_integrated_piers_update import (
    ISLANDS, require_true, verify_captures, verify_native_avatar_pixels,
)

SCOPE=contract.SCOPE
COMMON_KINDS=frozenset({'coastal-ecology-source','coastal-ecology-census',
                        'coastal-ecology-native','coastal-pallet','coastal-pier-perimeters',
                        'coastal-ocean-palette','coastal-fragments',
                        'coastal-pier-visibility'})
EDITION_KINDS=frozenset({'review-mode','cold-boot'})
OPTIONAL_COMMON_KINDS=frozenset({'shore-animation','integrated-piers'})


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def baseline(name,raw):
    assert hashlib.sha256(raw).hexdigest()==contract.BASELINE_SHA256[name], ('Layer-165 baseline changed',name)
    if name=='versions.json':
        old=json.loads(raw)
        assert old['validated'] is True and old['validation_scope']=='generated-world-audit'
        assert len(old['integration_layers'])==165 and len(old['proofs'])==26
        return old
    if name=='test.sav':assert len(raw)==131072


def require_final_contract():
    assert contract.PREPARED_SHA256, 'The final ecology source hashes are not pinned'
    assert contract.EXPECTED_WATER_MAPS, 'The reviewed aquatic map coverage is not pinned'
    assert contract.NATIVE_CONTRACT_FINALIZED is True, 'Ecology native contracts are not finalized'


def verify_proof(report,directory,kind,target,save,info,old):
    assert report['passed'] is True,kind
    assert report.get('kind',kind)==kind
    is_test=target=='test'
    if kind=='coastal-ecology-source':
        require_true(report,['compiled_rom','independent_replay','idempotent',
            'unrelated_source_files_unchanged','atlas_graphics_unchanged',
            'unrelated_maps_layouts_and_tilesets_unchanged','campaign_and_save_abi_source_unchanged'])
        assert report['preflight'] is False
        assert report['layers']==info['integration_layers']
        assert report['parent_rom_sha256']==old['parent_rom_sha256']
        assert report['prepared_sha256']==contract.PREPARED_SHA256
        assert set(report['changed_files'])==set(contract.PREPARED_SHA256)
        assert report['source_hashes_checked']>=32240 and report['preserved_spatial_inputs']>=6000
        symbols={r['symbol']:r for r in report['compiled_symbols']}
        assert {'gWildMonHeaders','sJourneyWildPools','sJourneyGeneration4Pools',
                'StandardWildEncounter','MetatileBehavior_IsWaterWildEncounter'}<=symbols.keys()
        assert all(row['bytes']>0 and len(row['sha256'])==64 for row in symbols.values())
        blocks=report['compiled_blockdata']
        expected={name:sha for name,sha in contract.PREPARED_SHA256.items() if name.endswith('.bin')}
        assert {r['file']:r['sha256'] for r in blocks}==expected
    elif kind=='coastal-ecology-census':
        require_true(report,['compiled_rom','native_headers_read_from_compiled_rom',
            'habitat_pools_read_from_compiled_rom','terrain_behaviors_read_from_compiled_tilesets',
            'layer166_marker_present'])
        assert report['diagnostic_allow_gaps'] is False
        assert report['all_time_periods_checked']==4 and report['missing_headers']==[]
        assert report['missing_fishing_headers']==report['missing_standard_wild_triggers']==[]
        rows=report['maps'];required=[r for r in rows if r['required']]
        assert report['aquatic_maps']==len(rows) and len({r['map'] for r in rows})==len(rows)
        assert report['required_aquatic_maps']==len(required)
        assert report['quiet_or_retired_maps']==len(rows)-len(required)
        assert sorted(r['map'] for r in required)==sorted(contract.EXPECTED_WATER_MAPS)
        assert set(report['coverage_by_cap'])=={'493','1025'}
        for cap,coverage in report['coverage_by_cap'].items():
            assert set(coverage)=={'missing_pools','missing_fishing_pools','invalid_roots','empty_phases'}
            assert all(value==[] for value in coverage.values()),(cap,coverage)
        for row in required:
            assert row['water_cells']>0 and row['native_header_index'] is not None
            assert len(row['time_periods'])==4
            assert [r['time'] for r in row['time_periods']]==list(range(4))
            assert all(0<r['rate']<=100 and r['species'] for r in row['time_periods'])
            assert all(row['pools'][cap] for cap in ('493','1025'))
            assert row['standard_wild_trigger_behaviors']
            if not row['underwater']:
                assert all(row['fishing_pools'][cap] for cap in ('493','1025'))
                assert len(row['fishing_time_periods'])==4
                assert [r['time'] for r in row['fishing_time_periods']]==list(range(4))
                assert all(0<r['rate']<=100 and r['species'] for r in row['fishing_time_periods'])
            else:assert row['fishing_time_periods']==[]
    elif kind in {'coastal-ecology-native','coastal-ecology-review'}:
        # This remains closed until the actual owner has produced and reviewed
        # the native observation schema. Source rows alone cannot seal it.
        assert contract.NATIVE_CONTRACT_FINALIZED is True
        verify_encounter_observations(report,kind,target)
    elif kind=='coastal-pallet':
        require_true(report,['original_bridge_preserved','bridge_walked_without_surf',
            'controller_entry_and_exit','interior_captain_interacted_physically',
            'bridges_joined_and_walked','complete_trees_checked','upper_cliff_rim',
            'returned_to_original_land','route21_surf_roundtrip','merged_bay_surfed',
            'south_bridge_walked','eastern_corridor_walked','bridge_crossed_by_surf_below',
            'compiled_rom','native_validation_performed',
            'all_tree_parts_checked_through_native_map_grid',
            'walking_surf_doors_and_ferry_use_controller',
            'fixture_wild_encounters_disabled'])
        assert report['whole_standalone_tree_pattern']==[0xE,0xF,0x1E,0x1F,0x26,0x27]
        assert report['captures']
        assert report['route21_atlas_seam_delta']==0 and report['trips']
        verify_pallet_shore(report)
    elif kind=='coastal-pier-perimeters':
        verify_pier_perimeters(report,directory)
    elif kind=='coastal-ocean-palette':
        verify_ocean_palette(report,directory)
    elif kind=='coastal-fragments':
        verify_coastal_fragments(report,directory)
    elif kind=='coastal-pier-visibility':
        verify_pier_visibility(report,directory)
    elif kind=='review-mode':verify_review_mode(report,is_test,save)
    elif kind=='cold-boot':verify_cold_boot(report,is_test,save)
    elif kind in OPTIONAL_COMMON_KINDS:
        from verify_generated_world_update import verify_proof as verify_geometry
        verify_geometry(report,directory,kind,is_test,save,info,old)
    else:raise AssertionError(('Unknown ecology proof',kind,target))


def verify_pier_perimeters(report,directory):
    require_true(report,['compiled_rom','native_validation_performed',
        'all_seven_ports_verified','all_exposed_dry_water_edges_tested',
        'previous_video_defect_edges_included',
        'initial_placements_party_and_progress_are_fixtures',
        'movement_fixture_random_encounters_disabled',
        'controller_only_after_initial_placement',
        'no_midtrip_coordinate_elevation_or_avatar_writes',
        'legacy_save_recovery_tested'])
    ports=report['ports'];cases=report['cases']
    assert len(ports)==7 and {row['island'] for row in ports}==ISLANDS
    assert report['perimeter_edges']==len(cases)>0
    keys={(row['island'],tuple(row['dry']),tuple(row['water'])) for row in cases}
    assert len(keys)==len(cases), 'Duplicate pier perimeter observation'
    images=verify_captures(report['captures'],directory)
    assert len(images)>=7
    observed_captures=set()
    for port in ports:
        require_true(port,['all_exposed_edges_tested','walking_without_surf_blocked',
                           'native_controller_departure_and_reboard'])
        rows=[row for row in cases if row['island']==port['island']]
        assert port['perimeter_edges']==len(rows)>0
        assert any('capture_file' in row for row in rows)
        for row in rows:
            require_true(row,['walking_without_surf_blocked','native_surf_prompt',
                'native_controller_departure_and_reboard',
                'no_midtrip_coordinate_elevation_or_avatar_writes'])
            assert row['water_block']>>12==1 and not row['water_block']&0xC00
            assert row['water_behavior'] in {16,17,18,20,21,25,34,42,44,80,81,82,83}
            assert row['key'] in {16,32,64,128}
            for label,surfing,elevation,cell in (
                    ('initial',False,3,row['dry']),('blocked_walk',False,3,row['dry']),
                    ('surf_departure',True,1,row['water']),('reboarded',False,3,row['dry'])):
                state=row[label]
                assert [state['map'],*state['tile']]==cell
                assert state['surfing'] is surfing and state['elevation']==elevation
                assert state['tile_elevation']==elevation and state['priority']==2
                require_true(state,['sprite_visible','object_visible'])
            if 'capture_file' in row:
                name=row['capture_file'];assert name in images
                assert name not in observed_captures
                observed_captures.add(name)
                verify_native_avatar_pixels(row['reboarded']['native_avatar_pixels'],images[name])
    for dry,water in (([20,6],[21,6]),([16,6],[16,7])):
        assert any(row['dry']==['OneIsland_TreasureBeach_Frlg',*dry]
                   and row['water']==['OneIsland_TreasureBeach_Frlg',*water] for row in cases)
    assert report['legacy_source_rom_sha256']==contract.PARENT_ROM_SHA256
    legacy=report['legacy_save_recovery']
    require_true(legacy,['passed','legacy_walking_water_save_recovers_native_surf',
                         'bundled_save_continue_to_field','bundled_save_tested'])
    assert legacy['rom_sha256']==report['rom_sha256']
    verify_cold_boot(legacy,False,None)
    battery=[row for row in legacy['runs'] if row['battery']]
    assert len(battery)==1
    row=battery[0]
    assert row['field_map']==[37,46] and row['player_tile']==[21,7]
    assert row['avatar_surfing'] is True and row['elevation']==1
    require_true(row,['legacy_controller_returned_to_pier'])
    moves=row['legacy_controller_movements'];assert len(moves)==2
    current=dict(player_tile=[21,7],avatar_surfing=True,elevation=1)
    for movement,goal,key,surfing,elevation in (
            (moves[0],[21,6],64,True,1),(moves[1],[20,6],32,False,3)):
        require_true(movement,['controller_input_only'])
        assert movement['initial']==current
        assert movement['direction_key']==key and 0<movement['held_input_frames']<120
        current=dict(player_tile=goal,avatar_surfing=surfing,elevation=elevation)
        assert movement['returned']==current
    assert row['legacy_final_state']==current
    captures=report['legacy_save_recovery_captures']
    names={'legacy-continue/battery-continued-to-field.png',
           'legacy-continue/legacy-reboarded-to-pier.png'}
    assert len(captures)==2 and {row['file'] for row in captures}==names
    assert all(row in report['captures'] for row in captures)
    assert observed_captures==set(images)-names
    assert names<=images.keys()


def verify_ocean_palette(report,directory):
    require_true(report,['compiled_rom','native_validation_performed',
        'former_bay_border_palette_seam_removed',
        'upper_object_layers_attributes_and_geometry_preserved',
        'initial_party_progress_travel_and_encounter_suppression_are_fixtures',
        'no_palette_vram_map_grid_or_avatar_coordinate_writes'])
    assert report['lower_water_words_changed']==498
    expected={name:sha for name,sha in contract.PREPARED_SHA256.items()
              if name.endswith('.bin') and name.startswith('data/tilesets/')}
    tables=report['compiled_tables']
    assert len(tables)==len(expected)==11
    assert {row['path']:row['sha256'] for row in tables}==expected
    assert len({row['tileset'] for row in tables})==11
    assert sum(row['words_changed'] for row in tables)==498
    assert all(row['words_changed']>0 for row in tables)
    loaded=report['loaded_maps'];maps=report['target_maps']
    assert report['loaded_map_count']==len(loaded)==len(maps)==43
    assert len(set(maps))==43 and set(maps)==set(contract.OCEAN_TARGET_MAPS)
    assert {row['map'] for row in loaded}==set(maps)
    assert 'OneIsland_TreasureBeach_Frlg' in maps
    for row in loaded:
        require_true(row,['banks_loaded_from_final_rom'])
        assert (row['primary'],row['secondary'])==contract.OCEAN_LOADED_BANKS[row['map']]
        assert len(row['initial_position'])==2 and type(row['surfing']) is bool
        assert all(0x08000000<=row[key]<0x0A000000 for key in ('primary_pointer','secondary_pointer'))
    headers=report['compiled_native_bank_aliases']
    assert len(headers)==8
    assert {row['original']:row['private'] for row in headers}==contract.OCEAN_HEADER_ALIASES
    private_addresses={row['private']:row['private_address'] for row in headers}
    for row in loaded:
        assert row['primary_pointer']==private_addresses[row['primary']]
        if row['secondary'] in private_addresses:
            assert row['secondary_pointer']==private_addresses[row['secondary']]
    for row in headers:
        require_true(row,['header_fields_except_private_metatile_pointer_identical'])
        assert row['original_address']!=row['private_address']
        assert all(0x08000000<=row[key]<0x0A000000 for key in ('original_address','private_address'))
    aliases=report['native_coast_layout_aliases']
    assert len(aliases)==25 and {row['map'] for row in aliases}==set(contract.OCEAN_LAYOUT_ALIASES)
    loaded_by_map={row['map']:row for row in loaded}
    for row in aliases:
        require_true(row,['actual_loaded_private_bank_pointers_match_final_layout'])
        assert (row['layout'],row['primary'],row['secondary'])==contract.OCEAN_LAYOUT_ALIASES[row['map']]
        assert row['primary_pointer']==private_addresses[row['primary']]
        assert row['secondary_pointer']==loaded_by_map[row['map']]['secondary_pointer']
    names={name+'-native.png' for name in maps}
    names|={'treasure-bay-and-border-phase-'+str(i)+'.png' for i in range(8)}
    names|={'mossdeep-ocean-native-phase-'+str(i)+'.png' for i in range(8)}
    names|={'mossdeep-ocean-seam-'+name+'.png' for name in ('JourneyMossdeepOuterSea','MossdeepCity')}
    images=verify_captures(report['captures'],directory,names)
    checks=report['native_same_frame_pixel_checks']
    assert len(checks)==8 and [row['sample'] for row in checks]==list(range(8))
    phases=set()
    for row in checks:
        require_true(row,['same_native_frame'])
        assert row['bay_cell']==[15,7] and row['offshore_cell']==[21,3]
        phase=row['valid_animation_phases']
        assert phase and set(phase)<=set(range(8));phases.update(phase)
        screenshot=images['treasure-bay-and-border-phase-'+str(row['sample'])+'.png']
        bay=screenshot.crop((32,88,48,104)).tobytes()
        offshore=screenshot.crop((128,24,144,40)).tobytes()
        assert bay==offshore
        assert hashlib.sha256(bay).hexdigest()==row['identical_rgb_sha256']
    assert phases==set(range(8))
    groups=report['source_ocean_groups']
    assert len(groups)==2 and {r['region'] for r in groups}=={'sevii','kanto'}
    assert {r['region']:(len(r['maps']),r['lower_water_words_changed']) for r in groups}=={
        'sevii':(28,338),'kanto':(15,160)}
    assert len({name for r in groups for name in r['maps']})==43
    assert {name for r in groups for name in r['maps']}==set(maps)
    verify_hoenn_ocean(report['hoenn_ocean'],images)


def verify_hoenn_ocean(report,images):
    require_true(report,['all_eight_original_water_frames_observed',
        'native_visible_pixels_match_loaded_graphics',
        'identical_loaded_banks_across_mossdeep_city_outer_sea',
        'controller_surf_crossing_both_directions',
        'primary_animation_clock_continuous_across_both_connections',
        'palette_vram_animation_clock_and_map_grid_not_written',
        'initial_travel_progress_and_surf_state_are_fixtures'])
    census=report['source_census']
    require_true(census,['source_analysis_only','all_referenced_hoenn_ocean_words_use_palette4',
        'original_river_deep_water_dive_and_current_behaviors_unchanged'])
    maps=census['maps']
    assert census['map_count']==len(maps)==len({r['map'] for r in maps})>=85
    assert census['water_graphics']==[454,455] and census['ocean_palette']==4
    assert all(r['primary']=='gTileset_General' and len(r['blockdata_sha256'])==64 for r in maps)
    assert {'MossdeepCity','JourneyMossdeepOuterSea'}<={r['map'] for r in maps}
    assert census['water_banks'] and all(r['referenced_lower_water_words']>0 for r in census['water_banks'])
    phases=report['phases']
    assert len(phases)==8 and {r['phase'] for r in phases}==set(range(8))
    for row in phases:
        assert row['visible_native_water_pixels']>1000 and len(row['water_vram_sha256'])==64
        assert row['tile']==[79,34]
        image=images['mossdeep-ocean-native-phase-'+str(row['phase'])+'.png']
        assert len(image.getcolors(38400) or [])>=16
    crossings=report['crossings']
    assert [(r['map'],r['tile']) for r in crossings]==[
        ('JourneyMossdeepOuterSea',[0,26]),('MossdeepCity',[79,34])]
    assert all(r['surfing'] is True for r in crossings)
    for key in ('primary_pointer','secondary_pointer'):
        assert crossings[0][key]==crossings[1][key]
        assert 0x08000000<=crossings[0][key]<0x0A000000
    for row in crossings:
        require_true(row,['primary_animation_clock_continuous_across_connection'])
        samples=row['native_primary_animation_counter_steps']
        assert samples and all(0<=s['before']<256 and 0<=s['after']<256
            and (s['after']-s['before'])%256<=1 for s in samples)
    names={'mossdeep-ocean-native-phase-'+str(i)+'.png' for i in range(8)}
    names|={'mossdeep-ocean-seam-'+r['map']+'.png' for r in crossings}
    assert len(report['captures'])==10 and {r['file'] for r in report['captures']}==names


def verify_pallet_shore(report):
    require_true(report,['all_wet_mixed_rim_cells_blocked','north_rim_surrounding_land_route_walked',
        'south_bridge_from_full_grass_controller_roundtrip','no_new_travel_fixture_after_initial_land_route'])
    cells=report['north_rim_cells']
    assert len(cells)==8 and {tuple(r['tile']) for r in cells}=={(x,17) for x in range(15,23)}
    expected=[0x302]*7+[0x303]
    assert sorted((r['tile'][0],r['metatile']) for r in cells)==list(zip(range(15,23),expected))
    assert all((r['elevation'],r['collision'],r['behavior'])==(3,1,0) for r in cells)
    probes=report['north_rim_blocked_probes']
    edges={((14,17),(15,17),16),((23,17),(22,17),32)}
    edges|={((x,16),(x,17),128) for x in (15,16,17,18,19,21,22)}
    assert len(probes)==9 and {(tuple(r['start']),tuple(r['target']),r['direction_key']) for r in probes}==edges
    for row in probes:
        require_true(row,['controller_input_only','blocked'])
        assert row['before']==row['after'] and row['held_input_frames']==48
        assert row['before']==dict(tile=row['start'],surfing=False,elevation=3,tile_elevation=3)
    states=report['south_bridge_dry_roundtrip']
    assert len(states)==5 and [r['tile'] for r in states]==[[18,y] for y in (26,25,24,25,26)]
    assert all(r==dict(tile=[18,y],surfing=False,elevation=3,tile_elevation=15 if y==25 else 3)
               for r,y in zip(states,(26,25,24,25,26)))


def verify_pier_visibility(report,directory):
    require_true(report,['compiled_rom','native_validation_performed',
        'all_sixteen_dry_approach_cells_both_directions_verified',
        'full_head_body_feet_actual_vram_scanout_compared',
        'both_existing_lower_surf_routes_preserved',
        'native_surf_departure_and_reboard_both_ports',
        'initial_placements_party_and_progress_are_fixtures',
        'movement_fixture_random_encounters_disabled','controller_only_after_initial_placement',
        'no_midtrip_coordinate_elevation_or_avatar_writes'])
    assert report['pixel_failures']==[]
    assert report['dry_approach_cells']==16 and report['dry_approach_directional_samples']==32
    images=verify_captures(report['captures'],directory)
    used=set()
    def state(row,name,tile,surfing,priority):
        assert row['map']==name and row['tile']==list(tile)
        assert row['surfing'] is surfing and row['elevation']==(1 if surfing else 3)
        assert row['priority']==priority
        require_true(row,['sprite_visible','object_visible'])
        capture=row['capture_file'];assert capture in images and capture not in used
        used.add(capture)
        if not surfing:verify_native_avatar_pixels(row['native_avatar_pixels'],images[capture])
    expected={'CinnabarIsland_Frlg':([9,16,10,17],{(x,y) for x in (9,10) for y in (16,17)}),
              'PalletTown_Frlg':([11,26,22,26],{(x,26) for x in range(11,23)})}
    approaches=report['approaches']
    assert len(approaches)==2 and {r['map'] for r in approaches}==set(expected)
    for row in approaches:
        bounds,cells=expected[row['map']]
        assert row['bounds']==bounds and row['both_directions'] is True
        assert len(row['expected_cells'])==len(cells) and set(map(tuple,row['expected_cells']))==cells
        assert len(row['samples'])==len(cells)*2
        assert {(r['direction'],tuple(r['tile'])) for r in row['samples']}=={
            (d,xy) for d in ('outbound','return') for xy in cells}
        for sample in row['samples']:state(sample,row['map'],sample['tile'],False,1)
    bridges=report['bridge_foot_samples']
    expected_bridges={('CinnabarIsland_Frlg',d,x,15,1) for d in ('outbound','return') for x in range(6,12)}
    expected_bridges|={('PalletTown_Frlg',d,18,y,1 if y==25 or y==26 else 2)
        for d,y in [('outbound',25),('outbound',24),('return',25),('return',26)]}
    assert len(bridges)==16 and {(r['map'],r['direction'],*r['tile'],r['priority']) for r in bridges}==expected_bridges
    for row in bridges:state(row,row['map'],row['tile'],False,row['priority'])
    routes={'CinnabarIsland_Frlg':((16,16),[(16,15)]+[(x,15) for x in range(11,5,-1)]
            +[(x,15) for x in range(6,12)]+[(16,15),(16,16)]),
            'PalletTown_Frlg':((17,25),[(18,25),(19,25),(18,25),(17,25)])}
    underpasses=report['underpasses']
    assert len(underpasses)==2 and {r['map'] for r in underpasses}==set(routes)
    for row in underpasses:
        require_true(row,['both_directions','continuous_native_surf','full_multilevel_bridge_crossed',
            'native_lower_priority2_preserved'])
        start,route=routes[row['map']]
        assert row['start']==list(start) and row['route']==list(map(list,route))
        assert len(row['samples'])==len(route)+1
        for sample,tile in zip(row['samples'],[start,*route]):state(sample,row['map'],tile,True,2)
    transitions=report['surf_transitions']
    assert len(transitions)==2 and {r['map'] for r in transitions}==set(routes)
    for row in transitions:
        require_true(row,['native_surf_prompt','native_controller_departure_and_reboard'])
        dry,water=([9,17],[9,18]) if row['map']=='CinnabarIsland_Frlg' else ([17,26],[17,25])
        assert row['dry']==dry and row['water']==water
        state(row['surf_departure'],row['map'],water,True,2)
        state(row['reboarded'],row['map'],dry,False,1)
        if row['map']=='PalletTown_Frlg':state(row['initial_reboarded'],row['map'],dry,False,1)
    assert used<=images.keys() and len(images)-len(used)==1, 'Only the initial dry-land reference may be extra'


def verify_coastal_fragments(report,directory):
    require_true(report,['compiled_rom','native_validation_performed',
        'all_cliff_foot_surf_roundtrips_use_controller',
        'native_grid_and_loaded_banks_checked',
        'no_avatar_coordinate_elevation_map_grid_palette_or_vram_writes',
        'initial_party_progress_travel_and_encounter_suppression_are_fixtures',
        'high_coordinate_fixture_uses_restored_private_16bit_warp_event'])
    expected={(name,x,y) for name,anchors in contract.CLIFF_ROCK_ANCHORS.items()
              for x,y in anchors}
    rows=report['cliff_rock_sites']
    assert report['cliff_rock_sites_checked']==len(rows)==16
    assert report['cliff_rock_maps_checked']==len({row['map'] for row in rows})==9
    assert {(row['map'],*row['anchor']) for row in rows}==expected
    names=set()
    for row in rows:
        require_true(row,['physical_bits_preserved','native_grid_and_loaded_banks_checked'])
        words=row['compiled_words'];assert len(words)==4
        assert [word&1023 for word in words]==[0x123,0x123,0x12B,0x12B]
        x,y=row['anchor']
        first,last=row['initial_fixture'],row['return_state']
        assert first==last
        assert first['surfing'] is True and first['elevation']==1
        assert first['tile']==[x,y+1] and len(first['location'])==2
        moves=row['movements'];assert len(moves)==2
        for movement,start,end,key in (
                (moves[0],[x,y+1],[x+1,y+1],16),
                (moves[1],[x+1,y+1],[x,y+1],32)):
            require_true(movement,['controller_input_only','surfing_preserved'])
            assert movement['start']==start and movement['end']==end
            assert movement['direction_key']==key and 0<movement['held_input_frames']<96
        label=f"cliff-foot-{row['map']}-{x}-{y}"
        names|={label+'-before.png',label+'-return.png'}
    complete=report['preserved_complete_native_rocks']
    assert len(complete)==2
    assert {(row['map'],*row['anchor']) for row in complete}=={
        ('SixIsland_GreenPath_Frlg',37,17),('SixIsland_GreenPath_Frlg',39,17)}
    for row in complete:
        require_true(row,['complete_native_variant_preserved'])
        assert [word&1023 for word in row['compiled_words']]==[0x108,0x109,0x118,0x119]
        x,y=row['anchor'];names.add(f'preserved-cliff-rock-{x}-{y}.png')
    verify_kindle_cliff(report['kindle_road_cliff'])
    names|={'kindle-cliff-face-native.png','kindle-cliff-toe-native.png',
            'kindle-cliff-town-return-native.png','kindle-cliff-retired-foot-treasure-native.png'}
    verify_captures(report['captures'],directory,names)


def verify_kindle_cliff(report):
    road,town='OneIsland_KindleRoad_Frlg','OneIsland_Frlg'
    treasure='OneIsland_TreasureBeach_Frlg'
    assert report['map']==road
    require_true(report,['all26_native_cells_checked','complete_face_and_water_toe_loaded',
        'all_six_retired_treasure_foot_cells_surfed',
        'town_treasure_surf_seam_roundtrip_controller',
        'cape_surf_roundtrip_and_town_seam_controller',
        'restored_private_16bit_initial_warp_fixture'])
    expected={(town,22,18):0x112C,(town,23,18):0x047B,
              (town,22,19):0x112B,(town,23,19):0x1123,
              **{(road,x,138):0x047C for x in range(6)},
              (road,6,138):0x047D,(road,7,138):0x1120,
              **{(road,x,139):0x1123 for x in range(7)},(road,7,139):0x1131,
              **{(treasure,x,y):0x112B for x in (22,23) for y in range(3)}}
    cells=report['native_loaded_cells'];assert len(cells)==26
    assert {(row['source_map'],*row['source_tile']) for row in cells}==set(expected)
    for row in cells:
        require_true(row,['native_grid_checked','native_banks_checked'])
        name=row['source_map'];x,y=row['source_tile']
        assert row['observed']==row['expected']==expected[name,x,y]
        assert row['loaded_map']==(treasure if name==treasure else road)
        assert row['loaded_tile']==([x-24,y+120] if name==town else [x,y])
    start,end=report['initial_fixture'],report['return_state']
    assert start==end and start['surfing'] is True and start['elevation']==1
    assert start['tile']==[7,137] and start['location']==[37,45]
    route=[([7,138],128),([7,139],128)]
    route.extend(([x,139],32) for x in range(6,-1,-1))
    route.extend([([23,19],32),([23,0],128),([23,1],128),([23,2],128),
                  ([22,2],32),([22,1],64),([22,0],64),([23,0],16),
                  ([23,19],64),([0,139],16)])
    route.extend(([x,139],16) for x in range(1,8))
    route.extend([([7,138],64),([7,137],64)])
    moves=report['movements']
    assert report['controller_steps']==len(moves)==len(route)==28
    previous=start['tile'];location=start['location']
    for i,(movement,(destination,key)) in enumerate(zip(moves,route)):
        require_true(movement,['controller_input_only','surfing_preserved'])
        assert movement['start']==previous and movement['end']==destination
        assert movement['direction_key']==key and 0<movement['held_input_frames']<96
        assert movement['source_location']==location
        target=movement['destination_location']
        expected_location=[37,12] if i in (9,17) else [37,46] if 10<=i<=16 else [37,45]
        assert target==expected_location
        previous,location=destination,target
    assert previous==start['tile'] and location==start['location']
    for name,tile,key in [('west_face_probe',[7,138],32),
                          ('south_boundary_probe',[7,139],128)]:
        probe=report[name]
        require_true(probe,['blocked','controller_input_only'])
        assert probe['direction_key']==key and probe['held_input_frames']==48
        before,after=probe['before'],probe['after'];assert before==after
        assert before['location']==start['location'] and before['tile']==tile
        assert before['surfing'] is True and before['elevation']==1


def verify_encounter_observations(report,kind,target):
    require_true(report,['compiled_rom','native_validation_performed',
        'coast_open_sea_river_new_and_native_depth_checked',
        'no_encounter_forcing_repel_or_disabled_wild_fixture',
        'no_battle_result_or_avatar_coordinate_writes'])
    review=kind=='coastal-ecology-review'
    assert (target=='test') is review and report['review_mode'] is review
    cap=493 if target=='Pokemon-Journey-Gen1-4-Normal.gba' else 1025
    assert report['max_national_dex']==cap
    expected=[('SixIsland_Frlg','coast',44,0),
              ('JourneyHoennMiddleSea','open-sea',21,1),
              ('Route114','river',21,2),
              ('JourneyDepthMares','new-depth',0,2),
              ('Underwater_Route105','native-depth',25,1)]
    rows=report['cases'];assert len(rows)==len(expected)
    captures=[]
    for row,(name,profile,behavior,phase) in zip(rows,expected):
        require_true(row,['passed','compiled_rom','native_validation_performed',
            'controller_input_only_after_initial_fixture',
            'party_and_map_and_badges_are_initial_fixtures',
            'trainer_defeat_flags_not_written','no_battle_result_or_avatar_coordinate_writes'])
        assert (row['map'],row['profile'],row['native_case_behavior'],row['phase'])==(name,profile,behavior,phase)
        assert row['kind']=='coastal-ecology-native-case' and row['area']==1
        assert row['rom_sha256']==report['rom_sha256'] and row['elf_sha256']==report['elf_sha256']
        assert row['review_mode'] is review and row['max_national_dex']==cap
        assert row['underwater'] is (profile in {'new-depth','native-depth'})
        assert row['wild_encounters_disabled_fixture'] is False and row['repel_fixture_steps']==0
        pair=row['walking_pair']
        assert len(pair)==2 and row['initial_position']==pair[0]
        assert abs(pair[0][0]-pair[1][0])+abs(pair[0][1]-pair[1][1])==1
        assert row['actual_controller_steps']>0
        assert row['allowed_species'] and row['native_pool_samples']
        assert set(row['native_pool_samples'])<=set(row['allowed_species'])
        if not row['underwater']:assert row['native_fishing_available'] is (not review)
        if review:
            assert row['actual_controller_steps']>=220
            assert row['battle'] is None and row['standard_encounter_suppression_attempts']==200
        else:
            battle=row['battle'];assert battle and row['standard_encounter_suppression_attempts']==0
            assert battle['actual_battle_main_callback'] is True and not battle['battle_type_flags']&8
            assert battle['battle_action_menu_rendered'] is True
            assert battle['framebuffer_distinct_rgb_colors']>=16
            assert battle['framebuffer_nonblack_pixels']>=9600
            assert battle['species'] in row['allowed_species']
            assert 0<battle['national_dex']<=cap and 30<=battle['level']<=37
        assert row['captures'];captures.extend(row['captures'])
    assert report['actual_controller_steps']==sum(row['actual_controller_steps'] for row in rows)
    if review:
        assert report['all_review_cases_suppressed_encounters'] is True
        assert report['all_normal_cases_started_actual_wild_battles'] is None
    else:
        assert report['all_normal_cases_started_actual_wild_battles'] is True
        assert report['all_review_cases_suppressed_encounters'] is None
    assert report['captures']==captures and len({row['file'] for row in captures})==len(captures)


def verify_elf_binding(reports):
    sources=[report for kind,report in reports if kind=='coastal-ecology-source']
    assert len(sources)==1, 'Exactly one compiled source proof is required'
    elf=sources[0]['elf_sha256']
    assert isinstance(elf,str) and len(elf)==64
    for kind,report in reports:
        if kind in {'coastal-ecology-census','coastal-ecology-native',
                    'coastal-ecology-review','coastal-pallet','coastal-pier-perimeters',
                    'coastal-ocean-palette','coastal-fragments','coastal-pier-visibility'}:
            assert report['elf_sha256']==elf, ('Native proof used an unaudited ELF',kind)


def required_keys(info):
    targets={'test',*[r['file'] for r in info['variants']]}
    return ({('common',kind) for kind in COMMON_KINDS}|
            {(target,kind) for target in targets for kind in EDITION_KINDS}|
            {('Pokemon-Journey-Gen1-4-Normal.gba','coastal-ecology-native'),
             ('test','coastal-ecology-review')})


def verify_update(directory,info,*,historical_review=None,historical_save=None):
    require_final_contract()
    directory=Path(directory);old=previous_release(info)
    ref=info['previous_port_validation']
    assert baseline('versions.json',(ROOT/ref['manifest']).read_bytes())==old
    assert ref['manifest_sha256']==contract.BASELINE_SHA256['versions.json']
    assert ref['retested_on_current_rom'] is False
    assert info['integration_layers']==old['integration_layers']+[SCOPE] and len(info['integration_layers'])==166
    assert info['historical_validation']==old['historical_validation']
    assert info['previous_validation']==old['previous_validation']
    assert info['full_campaign_playthrough'] is info['previous_features_retested_on_current_rom'] is False
    references={}
    for key,name in [('previous_review_validation','review.json'),('previous_review_save_validation','test.sav')]:
        row=info[key];path=ROOT/row['file']
        assert digest(path)==row['sha256']==contract.BASELINE_SHA256[name]
        baseline(name,path.read_bytes());references[name]=path
    if historical_review is None:
        assert historical_save is None
        test=verify_review(ROOT/'roms/rom-de-teste',directory/'Pokemon-Journey-Gen1-9-Normal.gba')
        proof_save=ROOT/'roms/rom-de-teste/Pokemon-Journey-TESTE.sav'
    else:
        test=historical_review
        assert historical_save is not None, 'Historical TESTE evidence requires its pinned save'
        normal=next(r for r in info['variants'] if r['file']==test['base_normal_file'])
        assert test['base_normal_sha256']==normal['sha256'] and test['bytes']==33554432
        assert test['file']=='Pokemon-Journey-TESTE.gba' and test['separate_save_identity'] is True
        assert test['random_wild_encounters'] is False and test['automatic_trainer_approaches'] is False
        proof_save=Path(historical_save)
    expected={'common':info['parent_rom_sha256'],'test':test['sha256'],
              **{r['file']:r['sha256'] for r in info['variants']}}
    covered=set();reports=[]
    for proof in info['proofs']:
        key=proof['target'],proof['kind']
        assert key not in covered
        assert key in required_keys(info) or key[0]=='common' and key[1] in OPTIONAL_COMMON_KINDS
        covered.add(key);relative=Path(proof['file'])
        assert not relative.is_absolute() and '..' not in relative.parts
        file=directory/relative;report_dependencies(file,expected_sha=proof['sha256'])
        report=json.loads(file.read_bytes())
        assert report['rom_sha256']==expected[proof['target']],('Stale current proof',key)
        reports.append((proof['kind'],report))
        verify_proof(report,file.parent,proof['kind'],proof['target'],
                     proof_save,info,old)
    assert required_keys(info)<=covered
    verify_elf_binding(reports)
    previous_review=json.loads(references['review.json'].read_bytes())
    assert info['historical_release']==dict(scope='generated-world-audit',
        parent_rom_sha256=old['parent_rom_sha256'],variants={r['file']:r['sha256'] for r in old['variants']},
        test_rom_sha256=previous_review['sha256'],proof_count=26,retested_on_current_rom=False)
    from verify_generated_world_update import verify_update as verify_previous
    verify_previous(directory,old,historical_review=previous_review,historical_save=references['test.sav'])
    return info
