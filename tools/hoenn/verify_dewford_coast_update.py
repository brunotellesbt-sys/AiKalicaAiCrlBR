"""Verify focused coast proofs without relabeling the earlier gym evidence."""
import hashlib
import json
from pathlib import Path

from package_review_rom import verify as verify_review
from verify_fuchsia_update import ROOT, previous_release

SCOPE = 'dewford-coast-safety'
ALLOWED_SOURCE_FILES = {
    'data/layouts/Route107/map.bin',
    'include/journey_dewford_bridge.h',
    'include/journey_dewford_coast.h',
    'include/journey_dewford_coast_view.h',
    'include/journey_coastal_piers.h',
    'src/event_object_movement.c',
    'src/fieldmap.c',
    'data/tilesets/primary/general_frlg/metatiles.bin',
    'data/tilesets/primary/general_frlg/metatile_attributes.bin',
}
SEVII_TOWNS = ['OneIsland_Frlg', 'TwoIsland_Frlg', 'ThreeIsland_Port_Frlg',
               'FourIsland_Frlg', 'FiveIsland_Frlg', 'SixIsland_Frlg',
               'SevenIsland_Frlg', 'OneIsland_TreasureBeach_Frlg']
ALLOWED_SOURCE_FILES |= {f'data/maps/{town}/map.json' for town in SEVII_TOWNS}
ALLOWED_SOURCE_FILES |= {f'data/layouts/{town}/map.bin' for town in SEVII_TOWNS}
ALLOWED_SOURCE_FILES.add('data/maps/OneIsland_Harbor_Frlg/map.json')
ALLOWED_SOURCE_FILES |= {f'data/layouts/JourneyWorldSea{number:02d}/map.bin'
                         for number in range(9)}


def pinned_file(reference):
    path = Path(reference['file'])
    assert not path.is_absolute() and '..' not in path.parts
    raw = (ROOT / path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == reference['sha256']
    return ROOT / path, raw


def verify_update(directory, info):
    directory = Path(directory)
    old = previous_release(info)
    assert old['validated'] and old['validation_scope'] == 'extra-gyms'
    assert old['integration_layers'] + [SCOPE] == info['integration_layers']
    assert info['historical_validation'] == old['historical_validation']
    assert info['previous_validation'] == old['previous_validation']
    assert info['full_campaign_playthrough'] is False
    assert info['previous_features_retested_on_current_rom'] is False

    _, previous_review = pinned_file(info['previous_review_validation'])
    previous_save, save_bytes = pinned_file(info['previous_review_save_validation'])
    assert len(save_bytes) == 131072
    test = verify_review(ROOT / 'roms/rom-de-teste',
                         directory / 'Pokemon-Journey-Gen1-9-Normal.gba')
    expected = {'common': info['parent_rom_sha256'], 'test': test['sha256'],
                **{row['file']: row['sha256'] for row in info['variants']}}
    required = {('common', 'dewford-coast-source'), ('common', 'all-surf-links')}
    required |= {(target, kind) for target in expected if target != 'common'
                 for kind in ['dewford-coast', 'review-mode',
                              'coastal-pier-safety', 'coastal-cave-finishing',
                              'cold-boot']}
    covered = set()
    for proof in info['proofs']:
        key = proof['target'], proof['kind']
        assert key in required and key not in covered, key
        covered.add(key)
        path = Path(proof['file'])
        assert not path.is_absolute() and '..' not in path.parts
        raw = (directory / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == proof['sha256']
        report = json.loads(raw)
        assert report['passed'] is True
        assert report['rom_sha256'] == expected[proof['target']], ('Stale evidence', key)
        kind = proof['kind']
        if kind == 'dewford-coast-source':
            assert report['layers'] == info['integration_layers']
            assert report['parent_rom_sha256'] == old['parent_rom_sha256']
            assert report['compiled_rom'] is True and report['preflight'] is False
            assert set(report['changed_files']) == ALLOWED_SOURCE_FILES
            assert set(report['allowed_changed_files']) == ALLOWED_SOURCE_FILES
            assert len(report['changed_files']) == len(ALLOWED_SOURCE_FILES)
            assert report['source_hashes_checked'] > 30000
            for field in ['independent_replay', 'idempotent',
                          'unrelated_source_files_unchanged',
                          'other_maps_events_and_gyms_unchanged',
                          'authorized_port_warp_changes_only',
                          'map_dimensions_connections_and_npcs_unchanged',
                          'cave_events_and_warps_unchanged',
                          'cave_mountains_rebuilt_from_exact_native_donor',
                          'atlas_graphics_unchanged', 'save_and_link_abi_unchanged']:
                assert report[field] is True, field
        elif kind == 'all-surf-links':
            assert report['all_usable_outdoor_surf_connections_covered']
            assert report['no_midcrossing_warps_or_coordinate_writes']
            assert len(report['links']) == report['usable_reciprocal_water_links'] > 150
            assert report['crossings'] == 2 * len(report['links']) + len(report['native_current_links'])
            assert all(row['outbound_and_return'] and row['surf_preserved']
                       for row in report['links'])
            assert report['visible_outer_rock_checks']
            assert all(row['visible_rock_blocks_controller'] for row in report['visible_outer_rock_checks'])
            assert all(row['native_one_way_current_preserved'] and row['surf_preserved']
                       for row in report['native_current_links'])
        elif kind == 'dewford-coast':
            assert report['review_mode'] is (proof['target'] == 'test')
            for field in ['native_dewford_route107_bidirectional',
                          'foot_and_surf_states_preserved', 'land_blocks_surf',
                          'water_blocks_foot', 'controllers_only',
                          'all_bridge_rails_block_foot',
                          'three_transition_sands_are_level3',
                          'stair_edges_3_to4_walked', 'foot_drawn_above_bridge',
                          'surf_drawn_below_bridge', 'save_continue_upper_and_lower',
                          'terminal_door_roundtrip', 'two_dewford_vendors_interacted',
                          'loaded_diagonal_neighbors_match_source',
                          'native_surf_prompt', 'native_disembark',
                          'native_southern_corner_landing_and_reembarkation',
                          'no_elevation_writes',
                          'continuous_terminal_bridge_vendors_dewford_controller_trip',
                          'no_midroute_warp_or_coordinate_writes',
                          'initial_party_badges_trainers_and_first_placement_are_fixtures']:
                assert report[field] is True, field
            assert report['bridge_rails_checked'] == 22
            assert len(report['rail_checks']) == 22
            assert report['prices_checked'] == 71
            assert report['dry_landings']
            assert report['neighbor_checks']
            if proof['target'] == 'Pokemon-Journey-Gen1-9-Normal.gba':
                recording = ROOT / 'docs/videos/dewford-coast-corrected.mp4'
                assert hashlib.sha256(recording.read_bytes()).hexdigest() == report['video_sha256']
                assert report['video_frames'] > 0 and report['video_seconds'] > 0
            channels = {tuple(pair) for pair in report['channels_bidirectional']}
            assert len(channels) >= 6
            assert all((destination, source) in channels for source, destination in channels)
        elif kind == 'coastal-pier-safety':
            assert report['review_mode'] is (proof['target'] == 'test')
            assert len(report['town_bridges']) == len(report['low_piers']) == 7
            islands = {'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven'}
            assert {row['island'] for row in report['town_bridges']} == islands
            assert {row['island'] for row in report['low_piers']} == islands
            for field in ['native_controller_town_bridge_terminal_return',
                          'walked_all_extended_deck_rows', 'native_foot_elevation_3',
                          'foot_blocks_water', 'surf_entry_blocked_on_low_deck',
                          'open_sea_bypass_bidirectional',
                          'all_seven_surface_seams_preserved',
                          'wooden_endcaps_compiled', 'wooden_endcaps_loaded',
                          'no_metal_endcaps', 'native_endpoint_behaviors_preserved',
                          'no_midtrip_coordinate_or_elevation_writes',
                          'placements_progress_party_are_fixtures']:
                assert report[field] is True, field
            for bridge in report['town_bridges']:
                for field in ['controller_terminal_return', 'all_deck_rows_walked',
                              'foot_elevation_3', 'foot_above_boards',
                              'foot_blocks_water',
                              'wooden_endcaps_loaded', 'no_metal_endcaps',
                              'no_midtrip_coordinate_or_elevation_writes']:
                    assert bridge[field] is True, (bridge['island'], field)
                assert bridge['one_beach_seam_crossed'] is (bridge['island'] == 'One')
                assert bridge['native_endpoint']['metatile_ids'] == [0x228, 0x229, 0x22A]
                assert bridge['native_endpoint']['behaviors'] == [0, 0x65, 0]
                assert bridge['native_endpoint']['elevations'] == [3, 3, 3]
            compiled = report['compiled_wooden_endcaps']
            assert len(compiled) == 3
            for cap, tile, donor, attribute in zip(compiled, [0x228, 0x229, 0x22A],
                                                  [0x1C5, 0x1C6, 0x1C7], [0, 0x65, 0]):
                assert cap['metatile'] == tile and cap['native_donor'] == donor
                assert cap['compiled_attribute'] == attribute
                assert len(cap['compiled_art']) == 8
                assert cap['exact_native_wood_art'] is True
                assert cap['native_warp_behavior_preserved'] is True
            for pier in report['low_piers']:
                for field in ['surf_entry_blocked', 'connected_map_entry_blocked',
                              'open_sea_bypass_bidirectional',
                              'all_surface_seams_controller_roundtrip',
                              'no_midtrip_coordinate_or_elevation_writes']:
                    assert pier[field] is True, (pier['island'], field)
                expected_seams = {'One': 4, 'Two': 2, 'Three': 3, 'Four': 4,
                                  'Five': 4, 'Six': 4, 'Seven': 4}[pier['island']]
                assert pier['surface_seams_checked'] == len(pier['seams']) == expected_seams
                assert all(seam['controller_roundtrip'] is True for seam in pier['seams'])
            assert sum(pier['surface_seams_checked'] for pier in report['low_piers']) == 25
        elif kind == 'coastal-cave-finishing':
            assert len(report['caves']) == 9
            assert {cave['surface'] for cave in report['caves']} == {
                f'JourneyWorldSea{number:02d}' for number in range(9)}
            for field in ['all_nine_native_mountains_complete',
                          'all_nine_controller_entries_and_returns',
                          'all_nine_native_surf_landings_and_reembarkations',
                          'two_roundtrips_per_cave', 'atlas_events_and_warps_unchanged',
                          'no_internal_warps_or_coordinate_writes',
                          'initial_positions_and_party_are_fixtures']:
                assert report[field] is True, field
            for cave in report['caves']:
                assert cave['native_mountain_cells_checked'] == 81
                for field in ['complete_native_mountain_loaded',
                              'controller_door_roundtrip',
                              'native_surf_landing_and_reembarkation',
                              'foot_state_inside']:
                    assert cave[field] is True, (cave['surface'], field)
                assert len(cave['cycles']) == 2
                assert len(cave['native_controller_transitions']) == 4
                assert len(cave['native_surf_prompts']) == 2
                assert cave['walked_tiles']
        elif kind == 'cold-boot':
            for field in ['fresh_rom_boot_to_title', 'fresh_rom_title_to_new_game',
                          'no_assert_screen', 'controllers_only',
                          'no_game_memory_writes']:
                assert report[field] is True, field
            if proof['target'] == 'test':
                assert report['bundled_save_continue_to_field'] is True
                current_save = ROOT / 'roms/rom-de-teste/Pokemon-Journey-TESTE.sav'
                assert hashlib.sha256(current_save.read_bytes()).hexdigest() == report['bundled_save_sha256']
        elif kind == 'review-mode':
            assert report['review_mode'] is (proof['target'] == 'test')
            assert report['fixture_wild_encounters_disabled'] is False
            checks = report['checks']
            assert bool(checks['trainer_approach_result']) == (proof['target'] != 'test')
            if proof['target'] == 'test':
                assert checks['random_wild_attempts'] >= 200
                for field in ['native_flash_save_exported', 'no_random_encounters',
                              'no_fishing_encounters', 'no_sweet_scent_encounters',
                              'no_rock_smash_encounters',
                              'no_automatic_approach_after_600_frames']:
                    assert checks[field] is True, field
                current_save = ROOT / 'roms/rom-de-teste/Pokemon-Journey-TESTE.sav'
                assert hashlib.sha256(current_save.read_bytes()).hexdigest() == checks['save_sha256']
    assert covered == required
    assert all((directory / row['file']).read_bytes()[test['review_mode_offset']] == 0
               for row in info['variants'])

    # These 33 reports retain their layer-160 hashes. The new source audit
    # proves preservation, rather than claiming another 200 gym battles.
    from verify_extra_gyms_update import verify_update as verify_previous
    verify_previous(directory, old, historical_review=json.loads(previous_review),
                    historical_save=previous_save)
