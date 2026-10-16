"""Bind the integrated release to current Surf/port/atlas proof and harbor history."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
ISLANDS={'OneIsland_Frlg','TwoIsland_Frlg','ThreeIsland_Port_Frlg','FourIsland_Frlg','FiveIsland_Frlg','SixIsland_Frlg','SevenIsland_Frlg'}

def verify_update(directory,info):
    directory=Path(directory);variants={r['file']:r['sha256'] for r in info['variants']};covered=set()
    for p in info['proofs']:
        path=Path(p['file']);assert not path.is_absolute() and '..' not in path.parts
        raw=(directory/path).read_bytes();assert hashlib.sha256(raw).hexdigest()==p['sha256'];r=json.loads(raw);assert r['passed']
        kind,target=p['kind'],p['target'];expected=info['parent_rom_sha256'] if target=='common' else variants[target]
        if kind=='pallet-reproduction':
            assert target=='common' and r['original_inputs_verified'] and r['idempotent']
            assert r['layers']==info['integration_layers'][:info['integration_layers'].index('pallet-harbor')+1]
            layout=json.loads((ROOT/'mods/hoenn/pallet-harbor-validation/layout.json').read_text())
            assert r['prepared_sha256']==layout['prepared_sha256'] and len(r['byte_identical_outputs'])==14
        elif kind=='reproduction':
            assert target=='common' and r['layers']==info['integration_layers'] and not r['differences']
            assert r['original_inputs_verified'] and r['idempotent']
            layers=['sevii-surf-connections','sevii-coast-camera','sevii-surf-embarkation','sevii-arrival-layout','world-route-chart']
            if info.get('lavender_harbor_validated'):layers.append('lavender-harbor')
            assert r['reproduced_layers']==layers
        else:assert r['rom_sha256']==expected,(kind,target,'Stale evidence')
        if kind=='sevii-surf-connections':
            assert {i['map'] for i in r['islands']}==ISLANDS and len(r['seams'])==14
            assert r['controller_roundtrip'] and r['native_disembark'] and r['no_midroute_warps_or_coordinate_writes']
            assert r['save_continue_preserves_location'] and r['first_arrival_surf_does_not_trigger_ferry_cutscene']
            assert r['active_screen_fade_frames']==0 and r['observed_seam_frames']>1000 and r['walked_tiles']>1000
            assert len(r['marker_samples'])==r['walked_tiles']+1
        elif kind=='sevii-source-scope':
            assert r['port_buildings_boats_captains_and_warps_unchanged'] and r['native_sevii_land_unchanged']
            assert r['birth_and_navel_arrival_layout_preserved']
            assert r['unchanged_source_inputs_checked']>30000 and r['preserved_port_paths']
            layout=json.loads((ROOT/'mods/hoenn/world-route-chart-validation/layout.json').read_text())
            assert r['compiled_gps_tiles']==info['compiled_gps_tiles']==sum(p['width']*p['height'] for p in layout['projections'])
            assert r['maximum_neighbor_pixel_step']<=2 and r['maximum_seam_delta']==0
            assert not any('sootopolis' in n.lower() or 'pallet' in n.lower() for n in r['changed_source_files'])
        elif kind=='coast-connectivity':
            assert r['all_integrated_surface_seas_reachable'] and r['compiled_collision_and_water_behaviors']
            assert ISLANDS<=set(r['reachable_maps'])
        elif kind=='special-encounters':
            assert r['actual_tv_capture_and_form_ui'] and len(r['rotom_changes'])==6
            assert len(r['dex_locations'])==r['event_only_families']==21 and r['form_tools_available']==54
        elif kind=='pallet-harbor':
            for field in ['original_bridge_preserved','outside_boat_shifted_right','controller_entry_and_exit',
                          'outside_captain_removed','bridges_joined_and_walked','complete_trees_checked',
                          'interior_captain_interacted_physically','ship_hull_blocked_over_water',
                          'route21_surf_roundtrip','merged_bay_surfed','south_bridge_walked',
                          'eastern_corridor_walked','bridge_crossed_by_surf_below','upper_corner_corrected']:
                assert r[field] is True,field
            assert r['ship_sprite_size']==[96,40] and r['route21_atlas_seam_delta']==0
            lavender='JourneyLavenderHarbor' if info.get('lavender_harbor_validated') else 'JourneyRoute12Shipyard'
            assert [t['destination'] for t in r['trips']]==[lavender,'JourneyPalletHarbor']
        elif kind=='lavender-harbor':
            for field in ['controller_entry_and_exit','captain_interacted_physically',
                          'outside_captain_removed','one_indoor_captain','ship_hull_blocked_over_water',
                          'network_arrivals_inside_terminal','save_continue_inside_terminal','returned_to_original_pier',
                          'old_lodge_exit_walked']:
                assert r[field] is True,field
            assert r['ship_sprite_size']==[96,40]
            assert [t['destination'] for t in r['trips']]==['JourneyPalletHarbor','JourneyLavenderHarbor']
        elif kind=='sootopolis-harbor':
            for field in ['bridge_walked_without_surf','controller_entry_and_exit','crisis_layout_controller_access',
                          'captain_interacted_physically','submarine_hull_blocked_over_water','returned_to_original_land',
                          'shore_end_uses_native_grass','extra_bottom_bridge_row_removed','bridge_end_stays_in_original_tile']:
                assert r[field] is True,field
            assert r['submarine_sprite_size']==[64,64]
            assert [t['destination'] for t in r['trips']]==['SlateportCity_Harbor','JourneySootopolisHarbor']
        elif kind=='world-route-chart':
            for field in ['all_edges_match_native_map_connections','all_segments_orthogonal',
                          'compiled_atlas_pixels_match_source','all_route_names_registered',
                          'native_map_open_zoom_and_return','native_land_and_town_art_preserved',
                          'compiled_zoom_pixels_match_source','cursor_tracks_controller_movement_on_reopen',
                          'authored_corridors_visible','cursor_stays_within_authored_corridors']:
                assert r[field] is True,field
            layout=json.loads((ROOT/'mods/hoenn/world-route-chart-validation/layout.json').read_text())
            assert r['actual_connection_edges']==len(layout['routes']) and r['named_nodes']==len(layout['nodes'])
            assert r['new_passage_count']==len(r['new_surf_passages'])==len(layout['passages'])==3
            for passage in r['new_surf_passages']:
                assert passage['no_midroute_coordinate_writes']
                assert all(c['outbound_and_return'] and c['surf_preserved'] for c in passage['controller_crossings'])
                assert len({tuple(s['marker']) for s in passage['cursor_samples'] if s['map']==passage['map']})>1
                assert all(s['cursor_matches_compiled_tile_position'] and s['recenter'] and s['zoom'] for s in passage['cursor_samples'])
        else:assert kind in ('reproduction','pallet-reproduction'),kind
        covered.add((target,kind))
    assert {('common',k) for k in ['sevii-surf-connections','sevii-source-scope','coast-connectivity','reproduction']}<=covered
    assert {(n,k) for n in variants for k in ['sevii-surf-connections','special-encounters']}<=covered
    assert {(n,k) for n in variants for k in ['pallet-harbor','sootopolis-harbor']}<=covered
    assert {('common',k) for k in ['pallet-harbor','pallet-reproduction','sootopolis-harbor','world-route-chart']}<=covered
    assert info['pallet_harbor_validated'] and info['sootopolis_harbor_retested'] and info['world_route_chart_validated']
    if info.get('lavender_harbor_validated'):
        assert 'lavender-harbor' in info['integration_layers']
        assert {(n,'lavender-harbor') for n in ['common',*variants]}<=covered
    reference=info['previous_sootopolis_validation'];assert reference['retested_on_current_rom'] is False
    raw=(ROOT/reference['manifest']).read_bytes();assert hashlib.sha256(raw).hexdigest()==reference['manifest_sha256']
    previous=json.loads(raw)
    from verify_sootopolis_update import verify_update as verify_previous
    verify_previous(directory,previous)
    assert info['historical_validation']==previous['historical_validation']
    assert info['special_encounters_validated'] and info['full_campaign_playthrough'] is False
    return info
