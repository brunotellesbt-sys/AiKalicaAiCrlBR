"""Bind coastal closure proofs to layer 163 and pin layer 162 as history."""
import hashlib
import json
from pathlib import Path

from package_review_rom import verify as verify_review
from verify_dewford_coast_update import pinned_file
from verify_fuchsia_update import ROOT, previous_release
from verify_sevii_integrated_piers_update import (
    current_report, require_true, verify_captures, verify_integrated_piers,
    verify_native_avatar_pixels, verify_ocean_seams,
)


SCOPE = 'coastal-closures'
COMMON_KINDS = {'coastal-closures-source'}
EDITION_KINDS = {'six-coastal-closures', 'dewford-movement',
                 'affected-coast-connections', 'shore-animation',
                 'review-mode', 'cold-boot'}
# Finalized after the compiled 24-file source audit and the strict native
# Gen1-9-Normal post-DMA shore report passed on the frozen release ROM.
# Publication still checks all 31 proofs against their five exact ROM hashes.
CONTRACT_FINALIZED = True
ALLOWED_SOURCE_FILES = frozenset({
    'data/layouts/SixIsland_Frlg/map.bin',
    'data/layouts/SixIsland_WaterPath_Frlg/map.bin',
    'data/layouts/DewfordTown/map.bin',
    'data/layouts/Route106/map.bin',
    'data/layouts/Route107/map.bin',
    'data/layouts/JourneyDewfordPortIsland/map.bin',
    'include/journey_dewford_bridge.h',
    'data/tilesets/secondary/journey_dewford_harbor/metatiles.bin',
    'data/tilesets/secondary/journey_dewford_harbor/tiles.png',
    'data/tilesets/secondary/journey_dewford_harbor/palettes/09.pal',
    'data/tilesets/secondary/journey_dewford_harbor/anim/shore_frames.bin',
    'src/data/tilesets/journey_dewford_shore_anim.h',
    'src/tileset_anims.c',
    'src/main.c',
    'include/tileset_anims.h',
    'data/maps/OneIsland_Harbor_Frlg/map.json',
    'data/maps/TwoIsland_Harbor_Frlg/map.json',
    'data/maps/ThreeIsland_Harbor_Frlg/map.json',
    'data/maps/FourIsland_Harbor_Frlg/map.json',
    'data/maps/FiveIsland_Harbor_Frlg/map.json',
    'data/maps/SixIsland_Harbor_Frlg/map.json',
    'data/maps/SevenIsland_Harbor_Frlg/map.json',
    'src/data/journey_world_map.h',
    'src/data/journey_world_position.h',
})
PARENT_ROM_SHA256 = '08fc8a08b95e8e3a923e3342b4f1a31bbaccd1582cbc67ea010021191c43fd6e'
BASELINE_SHA256 = {
    'versions.json': 'd484518546094cf6562cbf314d08fb47e291f5e3f6c66acdbcc198c59eefbd9f',
    'review.json': 'b589c0663551eda74294f3a53ebbf6262337a7c204830d3d75c06d5bf03ee53b',
    'test.sav': 'eed564f4bc42657c7f529939a43ab9c8ec0ba18828f3894b40c7b79a0e0a14b8',
}
ATLAS_SHA256 = {
    'sWorldTiles': 'c8c7231314251a430fc10419cb4e13e1511b7df5fbfadd31be8bf6979b420b84',
    'sWorldTilemap': '6f24bbdae0bc26cbcbb5597b922f78618cb2096045976d4f99b7c193a453f80d',
    'sWorldPalette': '90f49d857b5a33b9ebf109f549d92ad922a18eaee214b048a9267bdde815da2d',
}

# Keep this literal independently of the staging helper and native validator.
SIX_CELLS = {
    (0, 2): 0x1273, (1, 2): 0x067A, (2, 2): 0x3132,
    (8, 2): 0x3134, (9, 2): 0x067C, (10, 2): 0x1273,
    **{(0, y): 0x1270 if y == 3 else 0x1274 for y in range(3, 22)},
    **{(1, y): 0x0473 for y in range(3, 22)},
    (0, 22): 0x1274, (1, 22): 0x047B, (0, 23): 0x1278,
    (16, 28): 0x047B, **{(x, 28): 0x047C for x in range(17, 24)},
    (14, 29): 0x1276, (15, 29): 0x1278,
    **{(x, 29): 0x126B for x in range(16, 23)}, (23, 29): 0x1269,
}
WATER_PATH_CELLS = {(0, 68): 0x04B3, **{(0, y): 0x0473 for y in range(69, 80)}}
SHORE_FRAME_SHA256 = '86730800296e5f7e61dda7f81584e188de07bffc89f3c8fe460cd9055ab500ba'
SHORE_GRAPHICS = [514, 523, 526, 527, 530, 533, 534, 535, 536,
                  537, 543, 544, 545, 546, 1020, 1021, 1022]
SHORE_DMA_RUNS = [
    dict(start=514, count=1, frame_word_offset=0),
    dict(start=523, count=1, frame_word_offset=16),
    dict(start=526, count=2, frame_word_offset=32),
    dict(start=530, count=1, frame_word_offset=64),
    dict(start=533, count=5, frame_word_offset=80),
    dict(start=543, count=4, frame_word_offset=160),
    dict(start=1020, count=3, frame_word_offset=224),
]
WATER_PHASE_SHA256 = [
    '92d5fe8c7ca132529dbc4974566c0a2deabf815857cc930ba77c5682add4fc7f',
    '3722b368b760664d19b409edf27a4ce50ce30ec729071558c73cc01daecb0017',
    '781bd5f6837d53667ccf2d3a9f155cba6388c1f89776ed4209427140645b8ed3',
    'e2d37e9f2fac51a14d445f34fa78837d7ac62c2048349d2e996e3d2866ea23c1',
    '761f737b87a8d176b802ae5ddda7ea60d9128d194ed6b3c9b179bebc3579a241',
    '3052e821aed736e0a7e3b52e86166cef6c3a77c42f6409ea7541029bc130345a',
    '2b6071e11f89b9db9ab49c38d1ab33689cc2201ca253700db4ac4f3677a5fc78',
    '47564444689ac954d965e9c3717645b8f7e552b45a08b469c043d885642c508b',
]
SAND_PHASE_SHA256 = [
    '010586f933201bbbd6782f14d24ff474f1beb0162d69595ed32c63d5a078978b',
    '4e29d17a65cc07ca837ef34755763fc491df6b9137083b9defbcf1f3193a1e78',
    '65865d4b1ba58a2e23e334258fa86523e464da26b41506ac3410c6c2c113748e',
    '3b4880adc25249190b71bc5d09415d1e02fdaac0d4d7c5beafcee0e8481e1efb',
    '7ae9707e7ed170d29c691de293cfc4b66e60a346c3a8fcb3f7cc7d8869f0e72c',
    '2d203ff71378933d8bd8b6307f5ade84a354f3be24b46a863313d32a7f60b1fb',
    '27f6e75dac484f0ed8cdb7c6e88be63883cb1d8c0616621dc670fe29515afbe8',
    '010586f933201bbbd6782f14d24ff474f1beb0162d69595ed32c63d5a078978b',
]


def require_final_contract():
    assert CONTRACT_FINALIZED is True, 'Coastal closure native contracts are not finalized'
    assert ALLOWED_SOURCE_FILES, 'The final source scope needs an independent literal allowlist'


def verify_baseline_bytes(name, raw):
    assert hashlib.sha256(raw).hexdigest() == BASELINE_SHA256[name], ('Layer 162 baseline changed', name)
    if name == 'versions.json':
        old = json.loads(raw)
        assert old['validated'] is True and old['validation_scope'] == 'sevii-integrated-piers'
        assert old['parent_rom_sha256'] == PARENT_ROM_SHA256
        assert len(old['integration_layers']) == 162 and len(old['proofs']) == 42
        return old
    if name == 'test.sav':
        assert len(raw) == 131072


def verify_source(report, info, old):
    assert report['kind'] == 'coastal-closures-source'
    assert report['layers'] == info['integration_layers']
    assert report['parent_rom_sha256'] == old['parent_rom_sha256']
    assert report['compiled_rom'] is True and report['preflight'] is False
    assert len(report['changed_files']) == len(set(report['changed_files'])) == len(ALLOWED_SOURCE_FILES)
    assert set(report['changed_files']) == set(report['allowed_changed_files']) == ALLOWED_SOURCE_FILES
    assert report['source_hashes_checked'] > 30000
    require_true(report, ['independent_replay', 'idempotent',
                          'unrelated_source_files_unchanged',
                          'save_and_link_abi_unchanged', 'atlas_graphics_unchanged',
                          'gyms_and_campaign_unchanged'])
    require_true(report['shore_animation'], [
        'native_private_secondary_reload_after_dma_refresh',
        'secondary_reload_only_marks_pending',
        'post_dma_refresh_only_after_all_requests_complete',
        'post_dma_refresh_one_shot_with_private_bank_and_general_callback_guards',
        'main_vblank_only_reviewed_post_dma_call',
        'public_tileset_api_only_reviewed_declaration',
    ])


def verify_six_closures(report, directory):
    assert report['kind'] == 'six-coastal-closures'
    assert report['preflight'] is False and report['native_validation_performed'] is True
    assert report['baseline_rom_sha256'] == PARENT_ROM_SHA256
    require_true(report, ['source_tree_objects_complete',
                          'west_shore_and_port_mountain_bodies_complete',
                          'buildings_events_paths_connections_dimensions_and_borders_preserved',
                          'source_map_renders_not_emulator_captures',
                          'loaded_town_blocks_match_source',
                          'water_path_loaded_observation_and_initial_town_position_are_fixtures',
                          'party_progress_and_trainer_flags_are_fixtures',
                          'player_movement_uses_controller_input',
                          'no_position_or_elevation_writes_after_initial_town_placement'])
    assert report['full_campaign_playthrough'] is False
    assert report['exact_source_cell_counts'] == [65, 12]
    assert report['complete_tree_count'] == len(report['objects']) == 12
    owned = set()
    for tree in report['objects']:
        require_true(tree, ['crown_middle_and_base_complete'])
        x, y, width, height = tree['bounds']
        assert width == 2 and height == 3 and 0 < x <= 22 and 0 <= y <= 27
        footprint = {(x + dx, y + dy) for dy in range(3) for dx in range(2)}
        assert not owned & footprint
        owned |= footprint
        assert tree['native_rows'][:2] == [[0x300E, 0x300F], [0x041E, 0x041F]]
        left, right = tree['native_rows'][2]
        assert left in [0x0424, 0x0426] and right in [0x0425, 0x0427]
    maps = {row['map']: row for row in report['maps']}
    assert len(report['maps']) == len(maps) == 2
    for name, cells, dimensions in [('SixIsland_Frlg', SIX_CELLS, [24, 30]),
                                    ('SixIsland_WaterPath_Frlg', WATER_PATH_CELLS, [24, 100])]:
        row = maps[name]
        assert row['dimensions'] == dimensions
        changes = row['changed_cells']
        assert len(changes) == len(cells)
        assert {tuple(item['position']): item['after'] for item in changes} == cells
        assert all(item['before'] != item['after'] for item in changes)
    assert report['loaded_town_cell_count'] == 720
    loaded = report['loaded_water_path_changed_cells']
    assert len(loaded) == 12
    assert {tuple(row['position']): row['value'] for row in loaded} == WATER_PATH_CELLS
    assert all(row['native_solid'] is True for row in loaded)
    solid = report['loaded_solid_cliff_cells']
    wet = report['loaded_adjacent_surf_height_one_cells']
    assert len(solid) == len({tuple(row['position']) for row in solid}) == 34
    assert len(wet) == len({tuple(row['position']) for row in wet}) == 35
    assert all(row['native_solid'] is True and row['loaded'] & 0xC00 == 0x400 for row in solid)
    assert all(row['native_surf_water'] is True and row['elevation'] == 1
               and row['loaded'] >> 12 == 1 and not row['loaded'] & 0xC00 for row in wet)
    assert report['loaded_dry_corridor'] == report['north_dry_corridor_preserved'] == [[8, 3], [8, 4], [8, 5]]
    assert len(report['preserved_buildings']) == 5
    for row in report['preserved_buildings']:
        require_true(row, ['complete_native_footprint_unchanged'])
    assert len(report['dry_controller_routes']) == 7
    assert {tuple(row['destination']) for row in report['dry_controller_routes']} == {
        (8, 19), (8, 12), (8, 3), (8, 8), (8, 16), (3, 21), (11, 22)}
    for row in report['dry_controller_routes']:
        require_true(row, ['dry', 'controller_input'])
    assert len(report['doors_tested']) == 5
    assert {row['warp_id'] for row in report['doors_tested']} == set(range(5))
    for row in report['doors_tested']:
        require_true(row, ['entered', 'exited', 'dry_return', 'controller_input'])
    assert len(report['native_map_transitions']) == 10
    assert len(report['collision_checks']) == 9
    for row in report['collision_checks']:
        require_true(row, ['blocked', 'native_collision', 'controller_input'])
    images = verify_captures(report['captures'], directory)
    assert len(images) >= 26
    assert len(report['surf_roundtrips']) == 2
    assert {row['side'] for row in report['surf_roundtrips']} == {'west', 'east'}
    for row in report['surf_roundtrips']:
        require_true(row, ['foot_blocked_from_ocean', 'native_surf_prompt',
                           'controller_coastal_route', 'returned_to_same_pier',
                           'head_body_feet_native_pixels_verified',
                           'no_coordinate_avatar_or_elevation_writes'])
        departure, returned = row['departure'], row['reboarded']
        assert (departure['map'], departure['tile']) == (returned['map'], returned['tile'])
        assert row['coast']['surfing'] is True and row['coast']['elevation'] == 1
        for state in [departure, returned]:
            assert state['surfing'] is False and state['elevation'] == 3
            require_true(state, ['sprite_visible', 'object_visible'])
            verify_native_avatar_pixels(state['native_avatar_pixels'], images[state['capture_file']])
    for attachment in report['source_review_images']:
        path = Path(attachment['file'])
        assert not path.is_absolute() and '..' not in path.parts
        assert hashlib.sha256((directory / path).read_bytes()).hexdigest() == attachment['sha256']


def verify_dewford_movement(report, directory):
    assert report['kind'] == 'dewford-movement'
    assert report['baseline_rom_sha256'] == PARENT_ROM_SHA256
    require_true(report, ['all_former_dry_boundaries_controller_roundtrip',
                          'ground_and_shore_level3',
                          'both_north_and_south_stairs_controller_roundtrip',
                          'upper_bridge_foot_level4_priority1',
                          'lower_bridge_surf_level1_priority2',
                          'both_bridge_rails_surfed_under',
                          'all_bridge_rails_block_foot',
                          'native_surf_prompt_and_northern_disembark',
                          'shore_to_terminal_dry_access_after_disembark',
                          'terminal_door_controller_roundtrip',
                          'terminal_wall_preserved',
                          'two_original_vendors_interacted',
                          'returned_to_original_dewford',
                          'dry_upper_and_surf_save_continue',
                          'dry_terrain_captures_compare_current_hardware_avatar_pixels',
                          'sprite_flags_alone_not_used_for_dry_visibility',
                          'no_midtrip_warps_or_coordinate_or_elevation_writes',
                          'initial_placement_party_badges_trainers_are_fixtures'])
    assert report['full_campaign_playthrough'] is False
    changed = report['changed_floor_blocks']
    assert len(changed) == len({(row['map'], *row['tile']) for row in changed}) == 76
    counts = {name: sum(row['map'] == name for row in changed) for name in {
        'DewfordTown', 'Route106', 'Route107', 'JourneyDewfordPortIsland'}}
    assert counts == {'DewfordTown': 27, 'Route106': 23, 'Route107': 17, 'JourneyDewfordPortIsland': 9}
    assert all(row['before'] >> 12 == 4 and row['after'] == ((row['before'] & 0xFFF) | 0x3000)
               and not row['before'] & 0xC00 for row in changed)
    assert report['former_invisible_boundary_count'] == len(report['boundary_checks']) == 29
    assert report['bridge_rails_checked'] == 22
    for row in report['boundary_checks']:
        require_true(row, ['native_controller_roundtrip'])
        for key in ['interior', 'shore', 'returned']:
            state = row[key]
            assert state['elevation'] == 3 and state['surf'] is False and state['priority'] == 2
        assert row['interior']['map'] == row['returned']['map']
        assert row['interior']['tile'] == row['returned']['tile']
    assert len(report['stair_checks']) == 4
    for row in report['stair_checks']:
        require_true(row, ['native_controller_roundtrip'])
        assert row['before']['elevation'] == row['returned']['elevation'] == 3
        assert row['upper']['elevation'] == 4 and row['upper']['priority'] == 1
        assert row['before']['map'] == row['returned']['map']
        assert row['before']['tile'] == row['returned']['tile']
    assert report['compiled_complete_native_stair_caps'] == [
        dict(metatile=0x2DF, quadrant=7, word=0x73FB),
        dict(metatile=0x2E1, quadrant=5, word=0x73FB)]
    saves = report['save_continue_checks']
    assert len(saves) == len({row['label'] for row in saves}) == 3
    assert {(row['state']['elevation'], row['state']['surf']) for row in saves} == {
        (3, False), (4, False), (1, True)}
    for row in saves:
        require_true(row, ['same_map_and_position', 'native_battery_reload_and_continue',
                           'no_coordinate_or_elevation_repair'])
    rails = [row for row in report['samples'] if row['label'].startswith('rail-')]
    assert len(rails) == len({row['label'] for row in rails}) == 22
    assert {row['label'] for row in rails} == {f'rail-{x}-{y}' for x in (5, 6) for y in range(4, 15)}
    for row in rails:
        _, x, y = row['label'].split('-')
        x, y = int(x), int(y)
        assert row['map'] == 'Route107' and row['tile'] == [x, y]
        assert row['metatile'] == 0x2B3 + (y - 4) * 4 + x - 5
        assert row['elevation'] == 4 and row['surf'] is False and row['priority'] == 1
    checkpoint_names = {
        'terminal-wall-remains-blocked': ('Route107', [6, 3], 4, False),
        'terminal-controller-entry': ('JourneyDewfordHarbor', [11, 14], 0, False),
        'terminal-controller-inner-floor': ('JourneyDewfordHarbor', [11, 13], 3, False),
        'terminal-controller-return': ('Route107', [5, 3], 4, False),
        'native-surf-departure': ('Route107', [8, 16], 1, True),
        'surf-under-both-bridge-rails': ('Route107', [8, 8], 1, True),
        'native-disembark-northern-island': ('Route107', [3, 6], 3, False),
        'shore-to-terminal-interior-after-disembark': ('Route107', [2, 5], 3, False),
        'returned-to-original-dewford': ('DewfordTown', [17, 16], 3, False),
    }
    for name, (map_name, position, elevation, surfing) in checkpoint_names.items():
        rows = [row for row in report['samples'] if row['label'] == name]
        assert len(rows) == 1
        row = rows[0]
        assert row['map'] == map_name and row['tile'] == position
        assert row['elevation'] == elevation and row['surf'] is surfing
        assert 'capture_file' in row
        if name == 'terminal-wall-remains-blocked':
            assert report['terminal_wall_sample'] == row
    images = verify_captures(report['captures'], directory)
    captured, vendor_captures = set(), set()
    for state in report['samples']:
        vendor_ui = state.get('capture_mode') == 'native-vendor-ui'
        if not vendor_ui:
            require_true(state, ['sprite_visible', 'object_visible'])
            assert state['priority'] == (1 if state['elevation'] == 4 else 2)
        if 'capture_file' in state:
            name = state['capture_file']
            assert name in images and name not in captured
            captured.add(name)
            if vendor_ui:
                assert state['label'] in {'competitive-vendor-menu', 'hyper-training-vendor-menu'}
                assert state['field_sprite_applicable'] is False
                assert state['native_menu_task_active'] is True
                task, callback = {
                    'competitive-vendor-menu': ('Task_HandleScrollingMultichoiceInput', 'CB2_Overworld'),
                    'hyper-training-vendor-menu': ('Task_HandleChooseMonInput', 'CB2_UpdatePartyMenu'),
                }[state['label']]
                assert state['native_menu_task'] == task
                assert state['native_main_callback_symbol'] == callback
                pointer = state['native_main_callback']
                assert type(pointer) is int and pointer == state['expected_main_callback']
                assert 0x08000000 <= pointer < 0x0A000000 and pointer % 2 == 0
                vendor_captures.add(state['label'])
            elif state['surf'] is False:
                verify_native_avatar_pixels(state['native_avatar_pixels'], images[name])
    assert captured == set(images), 'Every movement capture needs its observed current state'
    assert vendor_captures == {'competitive-vendor-menu', 'hyper-training-vendor-menu'}


def verify_coast_connections(report, directory):
    assert report['kind'] == 'affected-coast-connections'
    require_true(report, ['components_bound_to_current_rom',
                          'player_movement_uses_controller_input',
                          'no_midcrossing_warps_or_coordinate_or_elevation_writes'])
    assert len(report['components']) == 3
    components = {row['kind']: row for row in report['components']}
    assert set(components) == {'integrated-piers', 'ocean-seams', 'coastal-route-identity'}
    for kind, verifier in [('integrated-piers', verify_integrated_piers),
                           ('ocean-seams', verify_ocean_seams),
                           ('coastal-route-identity', verify_route_identity)]:
        row = components[kind]
        path = Path(row['file'])
        assert not path.is_absolute() and '..' not in path.parts and path.suffix == '.json'
        raw = (directory / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row['sha256']
        component = current_report(raw, report['rom_sha256'], kind)
        assert component['review_mode'] is report['review_mode']
        verifier(component, directory / path.parent)


def verify_route_identity(report, directory):
    assert report['kind'] == 'coastal-route-identity'
    assert report['compiled_rom'] is True and report['preflight'] is False
    assert report['full_campaign_playthrough'] is False
    require_true(report, ['all_connected_border_pixels_preserved',
                          'all_other_grids_bitwise_unchanged', 'atlas_arrays_unchanged',
                          'all_route_names_and_banners_checked',
                          'actual_journey_world_position_samples',
                          'ui_map_open_matches_actual_player', 'fly_gating_verified',
                          'no_midcrossing_warps_or_coordinate_writes',
                          'initial_positions_avatar_modes_party_progress_and_banner_display_are_fixtures'])
    assert report['atlas_arrays_sha256'] == ATLAS_SHA256
    assert report['connections'] == len(report['seams']) == 25
    assert report['native_controller_crossings'] == 50
    assert report['maximum_seam_delta'] == 0
    assert report['maximum_neighbor_pixel_step'] <= 2
    assert report['compiled_grid_values_checked'] == 523928
    assert report['controller_observation_samples'] >= 50 and report['walked_tiles'] >= 150
    islands = ('One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven')
    routes = {row['map']: row for row in report['routes']}
    expected_names = {island + 'Island_Harbor_Frlg': island.upper() + ' ISLAND COAST'
                      for island in islands}
    assert len(report['routes']) == len(routes) == 7 and set(routes) == set(expected_names)
    images = verify_captures(report['captures'], directory)
    assert len(images) == 64
    captures = {row['file']: row for row in report['captures']}
    used, map_ids = set(), {}

    def capture(reference):
        name = reference['file']
        assert name in images and name not in used and reference == captures[name]
        used.add(name)

    def sample(row):
        assert row['surfing'] is True
        map_id = row['map_id']
        assert len(map_id) == 2 and all(type(value) is int and 0 <= value <= 255 for value in map_id)
        assert map_ids.setdefault(row['map'], map_id) == map_id
        point = row['actual_projection']
        assert point == row['expected_projection'] and len(point) == 2
        assert all(type(value) is int and 0 <= value <= 255 for value in point)
        assert len(row['tile']) == 2 and all(type(value) is int and value >= 0 for value in row['tile'])
        if row['map'] in routes:
            assert row['tile'][0] < 17 and row['tile'][1] < 13
        return point

    for name, route in routes.items():
        assert route['name'] == route['actual_banner'] == expected_names[name]
        assert route['flyable'] is False and route['heal_location'] is False
        require_true(route, ['map_open_preserved_player_location', 'recenter_matches_actual_player'])
        map_ids[name] = route['map_id']
        paths = {row['direction']: row for row in route['central_crossings']}
        assert len(paths) == len(route['central_crossings']) == 2 and set(paths) == {'east', 'south'}
        flattened = []
        for direction, path in paths.items():
            assert path['primary_axis_monotonic'] is True
            assert path['primary_axis'] in ['x', 'y'] and path['primary_direction'] in [-1, 0, 1]
            rows = path['actual_gps_samples']
            tiles = [[x, 6] for x in range(2, 15)] if direction == 'east' else [[8, y] for y in range(2, 11)]
            assert [row['tile'] for row in rows] == tiles and all(row['map'] == name for row in rows)
            points = [sample(row) for row in rows]
            if path['primary_direction'] == 0:
                assert len({tuple(point) for point in points}) == 1
            axis = 'xy'.index(path['primary_axis'])
            assert all((b[axis] - a[axis]) * path['primary_direction'] >= 0 for a, b in zip(points, points[1:]))
            assert all(max(abs(x - y) for x, y in zip(a, b)) <= 2 for a, b in zip(points, points[1:]))
            flattened.extend(rows)
        assert route['actual_gps_samples'] == flattened
        assert route['ui_actual_projection'] == route['ui_expected_projection'] == route['expected_projection']
        assert route['expected_projection'] == flattened[-1]['actual_projection']
        capture(route['banner_capture'])
        capture(route['ui_capture'])
    assert len({tuple(map_ids[name]) for name in routes}) == 7
    covered, counts = set(), {name: 0 for name in routes}
    for seam in report['seams']:
        source, target = seam['source'], seam['destination']
        assert source in routes and target != source
        key = source, target, seam['direction'], seam['offset']
        assert key not in covered and seam['direction'] in ['left', 'right', 'up', 'down']
        covered.add(key)
        counts[source] += 1
        require_true(seam, ['outbound_and_return', 'surf_preserved',
                            'no_midcrossing_warps_or_coordinate_writes'])
        assert seam['native_controller_crossings'] == len(seam['transitions']) == 2
        rows = seam['actual_gps_samples']
        assert len(rows) == 7
        assert [row['map'] for row in rows] == [source, source, target, target, target, source, source]
        points = [sample(row) for row in rows]
        assert rows[0]['tile'] == rows[-1]['tile'] == seam['source_tile']
        assert rows[3]['tile'] == seam['destination_tile']
        assert points[1] == points[2] and points[4] == points[5]
        assert seam['maximum_seam_delta'] == 0
        maximum = max(max(abs(x - y) for x, y in zip(a, b)) for a, b in zip(points, points[1:]))
        assert maximum == seam['maximum_neighbor_pixel_step'] <= 2
        for transition, before, after in zip(seam['transitions'], [rows[1], rows[4]], [rows[2], rows[5]]):
            assert transition['source'] == [before['map'], *before['tile']]
            assert transition['destination'] == [after['map'], *after['tile']]
        assert len(seam['captures']) == 2
        for reference in seam['captures']:
            capture(reference)
    assert counts == {island + 'Island_Harbor_Frlg': count for island, count in zip(islands, [4, 2, 3, 4, 4, 4, 4])}
    assert used == set(images)


def verify_shore_animation(report, directory):
    assert report['kind'] == 'shore-animation'
    assert report['compiled_rom'] is True and report['preflight'] is False
    assert report['native_phase_count'] == 8
    assert report['animated_graphics'] == SHORE_GRAPHICS
    assert report['dma_runs'] == SHORE_DMA_RUNS
    assert report['full_campaign_playthrough'] is False
    require_true(report, ['water_and_foam_visible_pixels_animate',
                          'sea_native_sand_and_private_composites_share_phase',
                          'one_shot_private_reload_refresh_after_native_bg_dma_verified',
                          'private_static_bridge_stairs_and_terrain_graphics_preserved',
                          'native_flag_animation_slots_excluded', 'hardware_scanout_pixels_verified',
                          'six_native_frgl_water_pattern_not_replaced',
                          'initial_party_progress_position_and_avatar_mode_are_fixtures',
                          'no_animation_callback_clock_or_vram_writes'])
    raw = bytes.fromhex(report['frame_data_hex'])
    assert len(raw) == 4352
    assert hashlib.sha256(raw).hexdigest() == report['frame_data_sha256'] == SHORE_FRAME_SHA256
    private_phases = [hashlib.sha256(raw[i * 544:(i + 1) * 544]).hexdigest() for i in range(8)]
    images = verify_captures(report['captures'], directory)
    cycles = report['cycles']
    maps = {'DewfordTown', 'Route106', 'Route107', 'JourneyDewfordPortIsland'}
    assert len(cycles) == 4 and {row['map'] for row in cycles} == maps
    used_images = set()
    for cycle in cycles:
        frames = cycle['frames']
        assert len(frames) == 8 and {row['phase'] for row in frames} == set(range(8))
        groups = {kind: [] for kind in ['water', 'foam', 'static']}
        for frame in frames:
            phase = frame['phase']
            assert frame['static_private_graphics_unchanged'] is True
            assert frame['water_vram_sha256'] == WATER_PHASE_SHA256[phase]
            assert frame['private_vram_sha256'] == private_phases[phase]
            assert frame['sand_vram_sha256'] == SAND_PHASE_SHA256[phase]
            name = frame['capture_file']
            assert name in images and name not in used_images
            used_images.add(name)
            screenshot = images[name]
            points = frame['expected_screen_pixels']
            assert set(points) == {'water', 'foam', 'static'}
            for kind, minimum in [('water', 24), ('foam', 4), ('static', 8)]:
                rows = points[kind]
                coordinates = {(row[0], row[1]) for row in rows}
                assert len(rows) == len(coordinates) >= minimum
                actual = {}
                for px, py, red, green, blue in rows:
                    assert type(px) is int and type(py) is int and 0 <= px < 240 and 0 <= py < 160
                    assert all(type(value) is int and 0 <= value <= 248 and value % 8 == 0
                               for value in [red, green, blue])
                    rgb = screenshot.getpixel((px, py))
                    assert all(abs(a - b) <= 7 for a, b in zip(rgb, [red, green, blue]))
                    actual[px, py] = tuple([red, green, blue])
                groups[kind].append(actual)
        for kind, values in groups.items():
            coordinates = set(values[0])
            assert all(set(row) == coordinates for row in values), (cycle['map'], kind, 'Changed sampling coordinates')
            changes = sum(len({row[point] for row in values}) > 1 for point in coordinates)
            if kind == 'static':
                assert changes == 0, (cycle['map'], 'Static terrain changed with the beach cycle')
            else:
                assert changes >= (8 if kind == 'water' else 2), (cycle['map'], kind, 'No actual native animation')
        static = cycle['static_pixel_kind_proofs']
        assert set(static) == {'static_land', 'static_bridge'}
        assert len(static['static_land']) == 32
        if cycle['map'] in {'DewfordTown', 'Route107'}:
            assert len(static['static_bridge']) == 32
        for rows in static.values():
            assert len(rows) == len({(row[0], row[1]) for row in rows}) <= 32
            for px, py, red, green, blue in rows:
                assert type(px) is int and type(py) is int and 0 <= px < 240 and 0 <= py < 160
                assert all(type(value) is int and 0 <= value <= 248 and value % 8 == 0
                           for value in [red, green, blue])
                assert all(all(abs(a - b) <= 7 for a, b in zip(
                    images[frame['capture_file']].getpixel((px, py)), [red, green, blue])) for frame in frames)
    verify_shore_connections(report, directory, images, private_phases)


def verify_shore_connections(report, directory, images, private_phases):
    expected_pairs = {
        ('DewfordTown', 'Route106'), ('DewfordTown', 'Route107'),
        ('JourneyDewfordPortIsland', 'Route106'),
        ('JourneyDewfordPortIsland', 'Route107'),
        ('Route105', 'Route106'), ('Route107', 'Route108'),
    }
    dimensions = {'DewfordTown': (20, 20), 'Route106': (80, 20), 'Route107': (60, 20),
                  'JourneyDewfordPortIsland': (16, 12), 'Route105': (40, 80), 'Route108': (60, 20)}
    samples = report['onload_samples']
    assert len(samples) == 10
    assert {name: sum(row['map'] == name for row in samples) for name in dimensions if name not in {'Route105', 'Route108'}} == {
        'DewfordTown': 2, 'Route106': 3, 'Route107': 3, 'JourneyDewfordPortIsland': 2}
    used_samples, pairs = set(), set()
    used_images = {frame['capture_file'] for cycle in report['cycles'] for frame in cycle['frames']}
    assert len(used_images) == 32 and len(images) == 44

    def tile(name, position):
        width, height = dimensions[name]
        assert len(position) == 2 and all(type(value) is int for value in position)
        assert 0 <= position[0] < width and 0 <= position[1] < height

    assert len(report['connections']) == 6
    for connection in report['connections']:
        pair = tuple(connection['maps'])
        assert pair in expected_pairs and pair not in pairs
        pairs.add(pair)
        require_true(connection, ['global_phase_checked_on_private_bank_load',
                                  'no_midcrossing_warps_or_clock_or_graphics_writes'])
        assert connection['native_controller_crossings'] == len(connection['observed_crossings']) == 2
        origin, x, y = connection['initial_fixture']
        assert origin in pair
        tile(origin, [x, y])
        other = pair[1] if origin == pair[0] else pair[0]
        key = {'left': 32, 'right': 16, 'up': 64, 'down': 128}[connection['direction']]
        inverse = {16: 32, 32: 16, 64: 128, 128: 64}[key]
        for index, crossing in enumerate(connection['observed_crossings']):
            source, target = (origin, other) if index == 0 else (other, origin)
            assert crossing['source_map'] == source and crossing['destination_map'] == target
            assert crossing['controller_key'] == (key if index == 0 else inverse)
            assert crossing['native_surf_mode'] is True
            timer = crossing['secondary_timer']
            assert type(timer) is int and 0 <= timer <= 2
            assert crossing['pending_secondary_graphics_dma'] == []
            assert crossing['private_shore_refresh_pending'] is False
            tile(source, crossing['start_tile'])
            tile(source, crossing['last_source_tile'])
            tile(target, crossing['first_destination_tile'])
            tile(target, crossing['ready_destination_tile'])
            if index == 0:
                assert crossing['start_tile'] == [x, y]
            changed, loaded = crossing['frames_until_map_change'], crossing['frames_until_first_loaded']
            assert type(changed) is int and type(loaded) is int and 1 <= changed <= loaded <= 500
            initialized = crossing['initialization_observation']
            assert initialized['secondary_timer'] == 0
            initialized_frame = initialized['frame']
            assert type(initialized_frame) is int and changed <= initialized_frame <= changed + 12
            assert initialized_frame <= loaded <= initialized_frame + 2
            pending = initialized['pending_secondary_graphics_dma']
            assert len(pending) == len({row['index'] for row in pending})
            assert type(initialized['private_shore_refresh_pending']) is bool
            if target not in {'Route105', 'Route108'} and pending:
                assert initialized['private_shore_refresh_pending'] is True
            for request in pending:
                assert type(request['index']) is int and 0 <= request['index'] < 128
                address, size = request['destination'], request['bytes']
                assert type(address) is int and type(size) is int and 0 < size < 65536
                assert 0x06000000 <= address < 0x06008000 and address + size > 0x06004000
            file = crossing['capture_file']
            assert file in images and file not in used_images
            used_images.add(file)
            if target in {'Route105', 'Route108'}:
                assert 'onload_sample_index' not in crossing
                continue
            sample_index = crossing['onload_sample_index']
            assert type(sample_index) is int and 0 <= sample_index < len(samples) and sample_index not in used_samples
            used_samples.add(sample_index)
            sample = samples[sample_index]
            assert sample['map'] == target and sample['capture_file'] == file
            assert sample['secondary_timer'] == timer
            assert sample['pending_secondary_graphics_dma'] == []
            assert sample['private_shore_refresh_pending'] is False
            require_true(sample, ['first_loaded_frame', 'initialization_secondary_counter_zero_observed',
                                  'static_private_graphics_unchanged',
                                  'current_global_phase_after_native_bg_dma_verified'])
            phase, clock = sample['phase'], sample['vblank_counter']
            assert type(phase) is int and 0 <= phase < 8 and type(clock) is int and clock >= 0
            assert 0 <= clock - initialized['vblank_counter'] <= 2
            assert phase in {(clock >> 4) & 7, ((clock - 1) >> 4) & 7}
            assert sample['water_vram_sha256'] == WATER_PHASE_SHA256[phase]
            assert sample['private_vram_sha256'] == private_phases[phase]
            assert sample['sand_vram_sha256'] == SAND_PHASE_SHA256[phase]
    assert pairs == expected_pairs and used_samples == set(range(10))
    assert used_images == set(images)


def verify_cold_boot(report, test, save):
    require_true(report, ['fresh_rom_boot_to_title', 'fresh_rom_title_to_new_game',
                          'no_assert_screen', 'controllers_only', 'no_game_memory_writes'])
    if test:
        assert report['bundled_save_continue_to_field'] is True
        assert hashlib.sha256(save.read_bytes()).hexdigest() == report['bundled_save_sha256']


def verify_review_mode(report, test, save):
    assert report['fixture_wild_encounters_disabled'] is False
    checks = report['checks']
    assert bool(checks['trainer_approach_result']) == (not test)
    if test:
        assert checks['random_wild_attempts'] >= 200
        require_true(checks, ['native_flash_save_exported', 'no_random_encounters',
                              'no_fishing_encounters', 'no_sweet_scent_encounters',
                              'no_rock_smash_encounters',
                              'no_automatic_approach_after_600_frames'])
        assert hashlib.sha256(save.read_bytes()).hexdigest() == checks['save_sha256']


def verify_update(directory, info):
    require_final_contract()
    directory = Path(directory)
    old = previous_release(info)
    previous = info['previous_port_validation']
    assert previous['manifest_sha256'] == BASELINE_SHA256['versions.json']
    assert previous['retested_on_current_rom'] is False
    assert verify_baseline_bytes('versions.json', (ROOT / previous['manifest']).read_bytes()) == old
    assert info['integration_layers'] == old['integration_layers'] + [SCOPE]
    assert len(info['integration_layers']) == 163
    assert info['historical_validation'] == old['historical_validation']
    assert info['previous_validation'] == old['previous_validation']
    assert info['full_campaign_playthrough'] is False
    assert info['previous_features_retested_on_current_rom'] is False
    _, review_raw = pinned_file(info['previous_review_validation'])
    previous_save, save_raw = pinned_file(info['previous_review_save_validation'])
    verify_baseline_bytes('review.json', review_raw)
    verify_baseline_bytes('test.sav', save_raw)
    historical_review = json.loads(review_raw)
    historical = info['historical_release']
    assert historical == dict(scope=old['validation_scope'],
                              parent_rom_sha256=old['parent_rom_sha256'],
                              variants={row['file']: row['sha256'] for row in old['variants']},
                              test_rom_sha256=historical_review['sha256'],
                              proof_count=42, retested_on_current_rom=False)
    test = verify_review(ROOT / 'roms/rom-de-teste',
                         directory / 'Pokemon-Journey-Gen1-9-Normal.gba')
    expected = {'common': info['parent_rom_sha256'], 'test': test['sha256'],
                **{row['file']: row['sha256'] for row in info['variants']}}
    required = {('common', kind) for kind in COMMON_KINDS}
    required |= {(target, kind) for target in expected if target != 'common'
                 for kind in EDITION_KINDS}
    assert len(required) == len(info['proofs']) == 31
    covered = set()
    native = {'six-coastal-closures': verify_six_closures,
              'dewford-movement': verify_dewford_movement,
              'affected-coast-connections': verify_coast_connections,
              'shore-animation': verify_shore_animation}
    save = ROOT / 'roms/rom-de-teste/Pokemon-Journey-TESTE.sav'
    for proof in info['proofs']:
        key = proof['target'], proof['kind']
        assert key in required and key not in covered, key
        covered.add(key)
        path = Path(proof['file'])
        assert not path.is_absolute() and '..' not in path.parts
        raw = (directory / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == proof['sha256']
        report = current_report(raw, expected[proof['target']], key)
        is_test = proof['target'] == 'test'
        kind = proof['kind']
        if kind in EDITION_KINDS and kind != 'cold-boot':
            assert report['review_mode'] is is_test
        if kind == 'coastal-closures-source':
            verify_source(report, info, old)
        elif kind in native:
            native[kind](report, directory / path.parent)
        elif kind == 'cold-boot':
            verify_cold_boot(report, is_test, save)
        elif kind == 'review-mode':
            verify_review_mode(report, is_test, save)
        else:
            raise AssertionError(('Unsupported proof contract', kind))
    assert covered == required
    assert all((directory / row['file']).read_bytes()[test['review_mode_offset']] == 0
               for row in info['variants'])
    from verify_sevii_integrated_piers_update import verify_update as verify_previous
    verify_previous(directory, old, historical_review=historical_review,
                    historical_save=previous_save)
