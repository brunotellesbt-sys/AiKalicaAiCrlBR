"""Bind the seven ports and unobstructed Surf travel to the four current ROMs."""
import hashlib,json
from pathlib import Path
from verify_fuchsia_update import previous_release

ISLANDS={'One','Two','Three','Four','Five','Six','Seven'}


def verify_update(directory,info):
    directory=Path(directory);old=previous_release(info)
    assert old['validated'] and old['integration_layers']+['sevii-harbors']==info['integration_layers']
    expected={'common':info['parent_rom_sha256'],**{r['file']:r['sha256'] for r in info['variants']}};covered=set()
    for p in info['proofs']:
        path=Path(p['file']);assert not path.is_absolute() and '..' not in path.parts
        raw=(directory/path).read_bytes();assert hashlib.sha256(raw).hexdigest()==p['sha256']
        r=json.loads(raw);assert r['passed'] and r['rom_sha256']==expected[p['target']]
        if p['kind']=='sevii-harbors':
            assert {c['island'] for c in r['ports']}==ISLANDS and r['ship_sprite_size']==[96,40]
            for c in r['ports']:
                for field in ['controller_entry_and_exit','quay_walked_without_surf','small_boat_graphics_preserved',
                    'bridge_extended_three_tiles_and_walked','old_boat_gap_filled_and_walked','boats_clear_of_upper_quay',
                    'medium_boat_hull_blocked_over_water','small_boat_hull_blocked_over_water',
                    'one_indoor_captain','outside_captain_removed','captain_interacted_physically','ship_hull_blocked_over_water',
                    'network_arrival_inside','save_continue_inside','old_lodge_exit_preserved','south_surf_lane_crossed']:
                    assert c[field] is True,(c['island'],field)
                assert [t['destination'] for t in c['trips']]==['JourneyPalletHarbor',c['interior']]
            assert [t['destination'] for t in r['hoenn_roundtrip']]==['SlateportCity_Harbor','JourneySeviiOneHarbor']
            assert r['cinnabar_surf_under_pier_roundtrip'] and r['cinnabar_quay_walked_above']
        elif p['kind']=='sevii-harbor-source':
            assert r['original_inputs_verified'] and r['idempotent'] and not r['differences']
            assert r['layers']==info['integration_layers'] and r['unrelated_source_inputs_checked']>30000
            for field in ['south_row_byte_identical','west_two_columns_byte_identical',
                'surface_connections_and_dimensions_preserved','original_small_boat_graphics_preserved','native_ferry_arrivals_preserved',
                'varied_opposite_berths','boats_clear_of_upper_quay','bridge_extensions_three_tiles','old_boat_gap_closed',
                'all_other_port_placements_preserved','cinnabar_quay_art_pixel_identical','atlas_unchanged','shared_art_pixel_identical']:
                assert r[field] is True,field
        elif p['kind']=='sevii-surf-connections':
            assert len(r['islands'])==7 and len(r['seams'])==14 and r['walked_tiles']>1000
            for field in ['controller_roundtrip','native_disembark','no_midroute_warps_or_coordinate_writes',
                'save_continue_preserves_location','first_arrival_surf_does_not_trigger_ferry_cutscene']:
                assert r[field] is True,field
            assert r['active_screen_fade_frames']==0 and len(r['marker_samples'])==r['walked_tiles']+1
        elif p['kind']=='sevii-world-surf':
            assert {t['region'] for t in r['trips']}=={'KANTO','HOENN'}
            for t in r['trips']:
                assert t['controller_roundtrip'] and t['surf_preserved'] and t['no_midroute_warps_or_coordinate_writes']
                assert t['walked_tiles']>100 and t['transitions']>0
        elif p['kind']=='coast-connectivity':
            assert r['all_integrated_surface_seas_reachable'] and r['compiled_collision_and_water_behaviors']
        elif p['kind']=='world-route-chart':
            for field in ['all_edges_match_native_map_connections','all_segments_orthogonal',
                'compiled_atlas_pixels_match_source','compiled_zoom_pixels_match_source','all_route_names_registered',
                'native_map_open_zoom_and_return','cursor_tracks_controller_movement_on_reopen',
                'authored_corridors_visible','cursor_stays_within_authored_corridors']:
                assert r[field] is True,field
            assert r['new_passage_count']==3
        else:raise AssertionError(p['kind'])
        covered.add((p['target'],p['kind']))
    assert {(t,k) for t in expected for k in ['sevii-harbors','sevii-surf-connections','sevii-world-surf']}<=covered
    assert {('common',k) for k in ['sevii-harbor-source','coast-connectivity','world-route-chart']}<=covered
    from verify_three_harbor_update import verify_update as verify_previous
    verify_previous(directory,old)
