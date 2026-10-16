"""Bind new Surf connections, map cursor and ocean colors to shipped ROMs."""
import hashlib, json
from pathlib import Path
from verify_fuchsia_update import previous_release


def verify_update(directory, info):
    directory = Path(directory); old = previous_release(info)
    assert old['validated'] and old['integration_layers'] + ['continuous-ocean', 'annotated-world-links', 'surf-cave-coasts'] == info['integration_layers']
    expected = {'common': info['parent_rom_sha256'], **{r['file']: r['sha256'] for r in info['variants']}}
    covered = set()
    for p in info['proofs']:
        path = Path(p['file']); assert not path.is_absolute() and '..' not in path.parts
        raw = (directory / path).read_bytes(); assert hashlib.sha256(raw).hexdigest() == p['sha256']
        r = json.loads(raw); assert r['passed'] and r['rom_sha256'] == expected[p['target']]
        k = p['kind']
        if k == 'continuous-ocean-source':
            assert r['layers'] == info['integration_layers'] and r['original_inputs_verified'] and r['idempotent'] and not r['differences']
            assert r['unrelated_source_inputs_checked'] > 30000 and r['all_native_events_preserved']
            assert r['canonical_water_pixels_and_indices_identical'] and r['eight_animation_frames_identical']
            assert r['native_land_and_town_atlas_art_preserved'] and r['all_new_outer_limits_closed']
            assert len(r['islands']) == 9 and len(r['cave_approaches']) == 15 and r['pr90_events_and_ports_preserved']
            assert len(r['new_maps']) == 7 and len(r['annotations']) == 6
            assert sum(a['new_map'] for a in r['annotations']) == 5
            assert r['gps']['maximum_neighbor_pixel_step'] <= 2 and r['gps']['maximum_seam_delta'] == 0
        elif k == 'all-surf-links':
            assert r['all_usable_outdoor_surf_connections_covered'] and r['usable_reciprocal_water_links'] > 150
            assert r['crossings'] == 2 * len(r['links']) + len(r['native_current_links']) and r['no_midcrossing_warps_or_coordinate_writes']
            assert all(c['surf_preserved'] and c['outbound_and_return'] for c in r['links'])
            assert len(r['visible_outer_rock_checks']) + len(r['routes_without_exposed_water_edges']) == 65
            assert r['visible_outer_rock_checks']
        elif k == 'coastal-cave-access':
            assert len(r['caves']) == 15 and r['native_controller_entries_and_returns']
            assert r['no_internal_warps_or_coordinate_writes'] and r['legendary_capture_rules_preserved']
        elif k == 'cave-map':
            assert len(r['caves']) == 15 and r['native_map_open_zoom_and_return']
            assert r['all_cave_cursor_positions_match_visible_icons']
        elif k == 'beach-trainers':
            assert len(r['islands']) == 9 and r['save_continue_retains_all_private_flags']
            assert all(i['won_native_battle'] and i['private_defeated_flag'] and i['native_landing_and_surf_return'] for i in r['islands'])
        elif k == 'mossdeep-harbor':
            assert r['terminal'] == [3,26,5,5] and r['controller_entry_and_exit'] and r['both_pier_rows_walked_without_surf']
            assert r['legacy_exit_preserved'] and r['outside_boat_over_water'] and r['inside_ship_over_water']
        elif k == 'dewford-island-harbor':
            assert r['stairs_walked'] == [[5,3],[6,3],[5,15],[6,15]]
            assert r['bridge_walked_above_without_surf'] and r['surf_crossed_below_without_dismounting'] and r['controller_entry_and_exit']
            assert r['north_island_seamless_controller_connections'] and r['west_house_foot_access'] and r['ship_channel_surfed']
        elif k == 'ocean-seams':
            assert len(r['seams']) == 13 and r['crossings'] == 26 and r['all_outdoor_format_seams_covered']
            assert all(s['outbound_and_return'] and s['surf_preserved'] and s['colors_identical'] for s in r['seams'])
            assert r['no_midcrossing_warps_or_coordinate_writes']
        elif k == 'continuous-ocean':
            assert r['departure'][0] == 'MossdeepCity' and r['arrival'][0] == 'OneIsland_Frlg'
            assert r['walked_tiles'] > 200 and r['video_seconds'] > 30
            for field in ['native_surf_and_disembark', 'controller_movement_only', 'no_midroute_warps_or_coordinate_writes', 'all_seam_ocean_colors_identical', 'continuous_video']:
                assert r[field], field
            assert len(r['seam_palette_samples']) >= 5
        elif k == 'sevii-surf-connections':
            assert len(r['islands']) == 7 and len(r['seams']) == 14 and r['walked_tiles'] > 1000
            for field in ['controller_roundtrip', 'native_disembark', 'no_midroute_warps_or_coordinate_writes', 'save_continue_preserves_location']:
                assert r[field], field
            assert r['active_screen_fade_frames'] == 0
        elif k == 'coast-connectivity':
            assert r['all_integrated_surface_seas_reachable'] and r['compiled_collision_and_water_behaviors']
            assert len(r['required_sea_maps']) >= 61 and r['unconnected_outer_borders_blocked']
        elif k == 'world-route-chart':
            assert r['new_passage_count'] == 10 and r['cave_approaches_visible_count'] == 15
            for field in ['all_edges_match_native_map_connections', 'all_segments_orthogonal', 'compiled_atlas_pixels_match_source', 'compiled_zoom_pixels_match_source', 'all_route_names_registered', 'native_map_open_zoom_and_return', 'cursor_tracks_controller_movement_on_reopen', 'authored_corridors_visible', 'cursor_stays_within_authored_corridors']:
                assert r[field], field
        else:
            raise AssertionError(k)
        covered.add((p['target'], k))
    assert {(t, k) for t in expected for k in ['ocean-seams', 'sevii-surf-connections', 'continuous-ocean', 'mossdeep-harbor', 'dewford-island-harbor']} <= covered
    assert {('common', k) for k in ['continuous-ocean-source', 'coast-connectivity', 'world-route-chart', 'all-surf-links', 'coastal-cave-access', 'beach-trainers', 'cave-map']} <= covered
    # Old reports retain the original ROM hashes and remain historical.
    from verify_island_harbor_update import verify_update as verify_previous
    verify_previous(directory, old)
