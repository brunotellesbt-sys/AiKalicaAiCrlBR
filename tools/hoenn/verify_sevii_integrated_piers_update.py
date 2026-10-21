"""Bind integrated island ports to current ROMs while retaining older proofs."""
import hashlib
import json
from pathlib import Path

from PIL import Image

from package_review_rom import verify as verify_review
from verify_dewford_coast_update import pinned_file
from verify_fuchsia_update import ROOT, previous_release

SCOPE = 'sevii-integrated-piers'
ISLANDS = {'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven'}
EDITION_KINDS = {'integrated-piers', 'dewford-coast', 'coastal-cave-finishing',
                 'review-mode', 'cold-boot', 'dewford-beach-visibility',
                 'six-landscape', 'ocean-seams'}


ALLOWED_SOURCE_FILES = {
    'data/layouts/FiveIsland_Frlg/map.bin',
    'data/layouts/FourIsland_Frlg/map.bin',
    'data/layouts/JourneySeviiFivePort/map.bin',
    'data/layouts/JourneySeviiFourPort/map.bin',
    'data/layouts/JourneySeviiOnePort/map.bin',
    'data/layouts/JourneySeviiSevenPort/map.bin',
    'data/layouts/JourneySeviiSixPort/map.bin',
    'data/layouts/JourneySeviiThreePort/map.bin',
    'data/layouts/JourneySeviiTwoPort/map.bin',
    'data/layouts/OneIsland_Frlg/map.bin',
    'data/layouts/OneIsland_TreasureBeach_Frlg/map.bin',
    'data/layouts/SevenIsland_Frlg/map.bin',
    'data/layouts/SevenIsland_SevaultCanyon_Entrance_Frlg/map.bin',
    'data/layouts/SixIsland_Frlg/map.bin',
    'data/layouts/ThreeIsland_Port_Frlg/map.bin',
    'data/layouts/TwoIsland_Frlg/map.bin',
    'data/layouts/layouts.json',
    'data/maps/FiveIsland_Frlg/map.json',
    'data/maps/FiveIsland_Harbor_Frlg/map.json',
    'data/maps/FourIsland_Frlg/map.json',
    'data/maps/FourIsland_Harbor_Frlg/map.json',
    'data/maps/JourneySeviiFiveHarbor/map.json',
    'data/maps/JourneySeviiFourHarbor/map.json',
    'data/maps/JourneySeviiOneHarbor/map.json',
    'data/maps/JourneySeviiSevenHarbor/map.json',
    'data/maps/JourneySeviiSixHarbor/map.json',
    'data/maps/JourneySeviiThreeHarbor/map.json',
    'data/maps/JourneySeviiTwoHarbor/map.json',
    'data/maps/OneIsland_Harbor_Frlg/map.json',
    'data/maps/OneIsland_TreasureBeach_Frlg/map.json',
    'data/maps/SevenIsland_Frlg/map.json',
    'data/maps/SevenIsland_Harbor_Frlg/map.json',
    'data/maps/SevenIsland_SevaultCanyon_Entrance_Frlg/map.json',
    'data/maps/SixIsland_Frlg/map.json',
    'data/maps/SixIsland_Harbor_Frlg/map.json',
    'data/maps/ThreeIsland_Harbor_Frlg/map.json',
    'data/maps/ThreeIsland_Port_Frlg/map.json',
    'data/maps/TwoIsland_Frlg/map.json',
    'data/maps/TwoIsland_Harbor_Frlg/map.json',
    'data/tilesets/primary/general_frlg/journey_sevii_sea_metatiles.bin',
    'data/tilesets/secondary/journey_dewford_harbor/metatile_attributes.bin',
    'data/tilesets/secondary/journey_sevii_integrated_123/metatile_attributes.bin',
    'data/tilesets/secondary/journey_sevii_integrated_123/metatiles.bin',
    'data/tilesets/secondary/journey_sevii_integrated_123/palettes/00.pal',
    'data/tilesets/secondary/journey_sevii_integrated_123/palettes/01.pal',
    'data/tilesets/secondary/journey_sevii_integrated_123/palettes/02.pal',
    'data/tilesets/secondary/journey_sevii_integrated_123/palettes/03.pal',
    'data/tilesets/secondary/journey_sevii_integrated_123/palettes/04.pal',
    'data/tilesets/secondary/journey_sevii_integrated_123/palettes/05.pal',
    'data/tilesets/secondary/journey_sevii_integrated_123/palettes/06.pal',
    'data/tilesets/secondary/journey_sevii_integrated_123/palettes/07.pal',
    'data/tilesets/secondary/journey_sevii_integrated_123/palettes/08.pal',
    'data/tilesets/secondary/journey_sevii_integrated_123/palettes/09.pal',
    'data/tilesets/secondary/journey_sevii_integrated_123/palettes/10.pal',
    'data/tilesets/secondary/journey_sevii_integrated_123/palettes/11.pal',
    'data/tilesets/secondary/journey_sevii_integrated_123/palettes/12.pal',
    'data/tilesets/secondary/journey_sevii_integrated_123/palettes/13.pal',
    'data/tilesets/secondary/journey_sevii_integrated_123/palettes/14.pal',
    'data/tilesets/secondary/journey_sevii_integrated_123/palettes/15.pal',
    'data/tilesets/secondary/journey_sevii_integrated_123/tiles.png',
    'data/tilesets/secondary/journey_sevii_integrated_45/metatile_attributes.bin',
    'data/tilesets/secondary/journey_sevii_integrated_45/metatiles.bin',
    'data/tilesets/secondary/journey_sevii_integrated_45/palettes/00.pal',
    'data/tilesets/secondary/journey_sevii_integrated_45/palettes/01.pal',
    'data/tilesets/secondary/journey_sevii_integrated_45/palettes/02.pal',
    'data/tilesets/secondary/journey_sevii_integrated_45/palettes/03.pal',
    'data/tilesets/secondary/journey_sevii_integrated_45/palettes/04.pal',
    'data/tilesets/secondary/journey_sevii_integrated_45/palettes/05.pal',
    'data/tilesets/secondary/journey_sevii_integrated_45/palettes/06.pal',
    'data/tilesets/secondary/journey_sevii_integrated_45/palettes/07.pal',
    'data/tilesets/secondary/journey_sevii_integrated_45/palettes/08.pal',
    'data/tilesets/secondary/journey_sevii_integrated_45/palettes/09.pal',
    'data/tilesets/secondary/journey_sevii_integrated_45/palettes/10.pal',
    'data/tilesets/secondary/journey_sevii_integrated_45/palettes/11.pal',
    'data/tilesets/secondary/journey_sevii_integrated_45/palettes/12.pal',
    'data/tilesets/secondary/journey_sevii_integrated_45/palettes/13.pal',
    'data/tilesets/secondary/journey_sevii_integrated_45/palettes/14.pal',
    'data/tilesets/secondary/journey_sevii_integrated_45/palettes/15.pal',
    'data/tilesets/secondary/journey_sevii_integrated_45/tiles.png',
    'data/tilesets/secondary/journey_sevii_integrated_67/metatile_attributes.bin',
    'data/tilesets/secondary/journey_sevii_integrated_67/metatiles.bin',
    'data/tilesets/secondary/journey_sevii_integrated_67/palettes/00.pal',
    'data/tilesets/secondary/journey_sevii_integrated_67/palettes/01.pal',
    'data/tilesets/secondary/journey_sevii_integrated_67/palettes/02.pal',
    'data/tilesets/secondary/journey_sevii_integrated_67/palettes/03.pal',
    'data/tilesets/secondary/journey_sevii_integrated_67/palettes/04.pal',
    'data/tilesets/secondary/journey_sevii_integrated_67/palettes/05.pal',
    'data/tilesets/secondary/journey_sevii_integrated_67/palettes/06.pal',
    'data/tilesets/secondary/journey_sevii_integrated_67/palettes/07.pal',
    'data/tilesets/secondary/journey_sevii_integrated_67/palettes/08.pal',
    'data/tilesets/secondary/journey_sevii_integrated_67/palettes/09.pal',
    'data/tilesets/secondary/journey_sevii_integrated_67/palettes/10.pal',
    'data/tilesets/secondary/journey_sevii_integrated_67/palettes/11.pal',
    'data/tilesets/secondary/journey_sevii_integrated_67/palettes/12.pal',
    'data/tilesets/secondary/journey_sevii_integrated_67/palettes/13.pal',
    'data/tilesets/secondary/journey_sevii_integrated_67/palettes/14.pal',
    'data/tilesets/secondary/journey_sevii_integrated_67/palettes/15.pal',
    'data/tilesets/secondary/journey_sevii_integrated_67/tiles.png',
    'data/tilesets/secondary/sevii_islands_123_frlg/journey_sevii_sea_metatiles.bin',
    'data/tilesets/secondary/sevii_islands_45_frlg/journey_sevii_sea_metatiles.bin',
    'data/tilesets/secondary/sevii_islands_67_frlg/journey_sevii_sea_metatiles.bin',
    'include/tilesets.h',
    'src/data/tilesets/graphics.h',
    'src/data/tilesets/headers.h',
    'src/data/tilesets/metatiles.h',
    'src/event_object_movement.c',
    'src/field_door.c',
    'src/journey_sevii_surf.c',
}


def require_true(report, fields):
    for field in fields:
        assert report[field] is True, field


def current_report(raw, expected_sha, key):
    report = json.loads(raw)
    assert report['passed'] is True, ('Failed evidence', key)
    assert report['rom_sha256'] == expected_sha, ('Stale evidence', key)
    return report


def verify_captures(captures, directory, expected_names=None):
    images = {}
    for capture in captures:
        path = Path(capture['file'])
        assert not path.is_absolute() and '..' not in path.parts
        assert path.as_posix() not in images, ('Duplicate capture', path)
        raw = (directory / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == capture['sha256'], path
        with Image.open(directory / path) as screenshot:
            pixels = screenshot.convert('RGB')
        assert pixels.size == (240, 160), path
        images[path.as_posix()] = pixels
    if expected_names is not None:
        assert set(images) == set(expected_names)
    return images


def verify_reboarding_baseline(reference, expected_sha):
    path, raw = pinned_file(reference)
    report = json.loads(raw)
    assert report['passed'] is False and report['expected_broken_baseline'] is True
    assert report['rom_sha256'] == expected_sha
    require_true(report, ['bug_reproduced', 'all_seven_town_pier_returns_blocked',
                          'water_placements_and_initial_surf_mode_are_fixtures',
                          'no_midapproach_warps_or_coordinate_or_elevation_writes'])
    assert len(report['ports']) == 7
    assert {row['island'] for row in report['ports']} == ISLANDS
    for row in report['ports']:
        require_true(row, ['surfing_before_and_after', 'controller_return_blocked',
                           'no_coordinates_or_elevation_writes_during_approach'])
        water, dry = row['water'], row['dry_pier']
        assert water[0] == dry[0]
        assert [dry[1] - water[1], dry[2] - water[2]] == {
            16: [1, 0], 32: [-1, 0], 64: [0, -1], 128: [0, 1]}[row['inward_key']]
    images = {}
    for capture in reference['captures']:
        capture_path, _ = pinned_file(capture)
        assert capture_path.parent == path.parent
        images[capture_path.name] = capture
        with Image.open(capture_path) as screenshot:
            assert screenshot.size == (240, 160)
    assert len(reference['captures']) == len(images) == 7
    assert set(images) == {island.lower() + '-blocked-surf-return.png' for island in ISLANDS}
    return report


def verify_visibility_captures(report, directory):
    expected = {row['label'] + '.png' for row in report['samples']}
    assert len(report['captures']) == len(expected)
    assert {Path(row['file']).name for row in report['captures']} == expected
    samples = {row['label']: row for row in report['samples']}
    images = verify_captures(report['captures'], directory)
    for file, pixels in images.items():
        path = Path(file)
        row = samples[path.stem]
        hat_pixels = [pixels.getpixel((x, y)) for y in range(48, 96) for x in range(104, 136)]
        body_pixels = [pixels.getpixel((x, y)) for y in range(78, 89) for x in range(114, 126)]
        red_hat = sum(red > 140 and red > green * 1.8 and red > blue * 1.8
                      for red, green, blue in hat_pixels)
        lower_body = sum(max(rgb) < 75 for rgb in body_pixels)
        assert red_hat == row['red_hat_pixels'] and lower_body == row['lower_body_pixels']


def verify_native_avatar_pixels(proof, screenshot):
    require_true(proof, ['exact_current_vram_frame_compared',
                         'background_color_coincidence_not_used'])
    assert 0 <= proof['hardware_oam_index'] < 128
    x, y, width, height = proof['screen_rectangle']
    assert 0 <= x < x + width <= 240 and 0 <= y < y + height <= 160
    projected = proof['expected_scanout_pixels']
    assert len(projected) == proof['expected_opaque_pixels'] >= 100
    assert len({(row[0], row[1]) for row in projected}) == len(projected)
    first_y, last_y = min(row[1] for row in projected), max(row[1] for row in projected)
    bands = [dict(expected=0, matched=0) for _ in range(3)]
    matched = exclusive = exclusive_matched = 0
    for px, py, red, green, blue, band, unique in projected:
        assert all(type(value) is int for value in [px, py, red, green, blue, band])
        assert all(0 <= value <= 248 and value % 8 == 0 for value in [red, green, blue])
        assert type(unique) is bool
        assert x <= px < x + width and y <= py < y + height
        assert band == min(2, (py - first_y) * 3 // (last_y - first_y + 1))
        visible = all(abs(actual - expected) <= 7
                      for actual, expected in zip(screenshot.getpixel((px, py)), [red, green, blue]))
        matched += visible
        bands[band]['expected'] += 1
        bands[band]['matched'] += visible
        if unique:
            exclusive += 1
            exclusive_matched += visible
    assert matched == proof['matching_scanout_pixels'] >= len(projected) * 0.85
    assert bands == proof['head_body_feet_bands']
    assert all(band['expected'] >= 8 and band['matched'] >= band['expected'] * 0.75 for band in bands)
    assert exclusive == proof['exclusive_obj_palette_pixels']
    assert exclusive_matched == proof['exclusive_obj_palette_pixels_visible']
    if exclusive >= 8:
        assert exclusive_matched >= exclusive * 0.85


def verify_integrated_piers(report, directory):
    images = verify_captures(report['captures'], directory)
    if 'video_sha256' in report:
        path = Path(report['video'])
        assert not path.is_absolute() and '..' not in path.parts
        assert hashlib.sha256((directory / path).read_bytes()).hexdigest() == report['video_sha256']
        require_true(report, ['continuous_controller_video'])
        assert report['video_frames'] > 0 and report['video_native_frames'] >= report['video_frames']
    assert len(report['ports']) == 7
    assert {port['island'] for port in report['ports']} == ISLANDS
    require_true(report, ['no_midtrip_coordinate_or_elevation_writes',
                          'placements_progress_party_are_fixtures',
                          'native_avatar_pixels_checked',
                          'exact_current_vram_frame_compared',
                          'sprite_flags_alone_not_sufficient'])
    assert report['full_campaign_playthrough'] is False
    seams = []
    for port in report['ports']:
        require_true(port, ['controller_terminal_roundtrip',
                            'terminal_physically_connected_to_town',
                            'no_town_to_detached_harbor_warp',
                            'town_terminal_trip_walked_entirely_on_dry_land',
                            'surf_departure_and_reboard',
                            'reboard_foot_elevation3', 'surf_elevation1',
                            'sprite_visible_above_pier',
                            'dry_walking_cannot_enter_water',
                            'previous_separate_port_cleared',
                            'native_surf_prompt', 'native_disembark',
                            'controller_door_roundtrip', 'foot_blocks_walls',
                            'indoor_captain_interacted',
                            'network_arrival_inside_terminal',
                            'network_return_to_original_terminal',
                            'save_continue_on_pier', 'save_continue_on_water'])
        for key, surfing, elevation in [('saved_pier', False, 3), ('saved_water', True, 1)]:
            checkpoint = port[key]
            require_true(checkpoint, ['native_save_continue', 'controls_settled_before_save'])
            assert checkpoint['neutral_frames_before_save'] >= 60
            before, after = checkpoint['before'], checkpoint['after']
            assert (before['map'], before['tile']) == (after['map'], after['tile'])
            for state in [before, after]:
                assert state['surfing'] is surfing and state['elevation'] == elevation
        departure, reboarded = port['departure_pier_state'], port['reboarded_state']
        assert (departure['map'], departure['tile']) == (reboarded['map'], reboarded['tile'])
        for state, capture_name in [
                (departure, port['island'].lower() + '-pier-departure-avatar.png'),
                (reboarded, port['island'].lower() + '-surf-reboarded-same-pier.png')]:
            assert state['surfing'] is False and state['elevation'] == 3
            require_true(state, ['sprite_visible', 'object_visible'])
            assert state['capture_file'] == capture_name
            verify_native_avatar_pixels(state['native_avatar_pixels'], images[capture_name])
        assert port['departure_water_state']['surfing'] is True
        assert port['departure_water_state']['elevation'] == 1
        assert port['boats_omitted_for_clearance'] is (port['island'] == 'Six')
        assert len(port['boats']) == (0 if port['island'] == 'Six' else 2)
        require_true(port, ['boat_hulls_blocked_over_water'])
        for boat in port['boats']:
            require_true(boat, ['blocked_over_water'])
            assert boat['native_hull_cells']
            assert all(tile >> 12 == 1 and tile & 0xC00 for x, y, tile in boat['native_hull_cells'])
        expected_seams = {'One': 4, 'Two': 2, 'Three': 3, 'Four': 4,
                          'Five': 4, 'Six': 4, 'Seven': 4}[port['island']]
        assert len(port['affected_seams']) == expected_seams
        for seam in port['affected_seams']:
            assert seam['island'] == port['island']
            require_true(seam, ['outbound_and_return', 'surf_preserved'])
            assert seam['native_controller_crossings'] == 2
            seams.append(seam)
    assert len(seams) == len(report['affected_seams']) == 25
    assert seams == report['affected_seams']
    assert len({(row['map'], row['direction'], row['destination'], row['offset'])
                for row in seams}) == 25
    clearance = report['old_port_clearance']
    assert len(clearance) == 7 and {row['island'] for row in clearance} == ISLANDS
    for row in clearance:
        require_true(row, ['former_terminal_and_boats_removed',
                           'no_invisible_structure_collision'])
        cells = row['native_loaded_water_cells']
        assert len(cells) == row['original_terminal_deck_and_boat_cells_checked'] >= 42
        assert len({(x, y) for x, y, tile in cells}) == len(cells)
        assert all(tile >> 12 == 1 and not tile & 0xC00 for x, y, tile in cells)


def verify_surf(report):
    require_true(report, ['all_usable_outdoor_surf_connections_covered',
                          'no_midcrossing_warps_or_coordinate_writes'])
    assert len(report['links']) == report['usable_reciprocal_water_links'] > 150
    assert report['crossings'] == 2 * len(report['links']) + len(report['native_current_links'])
    for row in report['links']:
        require_true(row, ['outbound_and_return', 'surf_preserved'])
    assert report['visible_outer_rock_checks']
    for row in report['visible_outer_rock_checks']:
        require_true(row, ['visible_rock_blocks_controller'])
    for row in report['native_current_links']:
        require_true(row, ['native_one_way_current_preserved', 'surf_preserved'])


def verify_dewford(report, directory):
    require_true(report, ['native_dewford_route107_bidirectional',
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
                          'initial_party_badges_trainers_and_first_placement_are_fixtures'])
    assert report['bridge_rails_checked'] == len(report['rail_checks']) == 22
    assert report['prices_checked'] == 71
    assert report['dry_landings'] and report['neighbor_checks']
    channels = {tuple(pair) for pair in report['channels_bidirectional']}
    assert len(channels) >= 6
    assert all((destination, source) in channels for source, destination in channels)
    if 'video_sha256' in report:
        path = Path(report['video'])
        assert not path.is_absolute() and '..' not in path.parts
        assert hashlib.sha256((directory / path).read_bytes()).hexdigest() == report['video_sha256']
        assert report['video_frames'] > 0 and report['video_seconds'] > 0


def verify_caves(report):
    assert len(report['caves']) == 9
    assert {cave['surface'] for cave in report['caves']} == {
        f'JourneyWorldSea{number:02d}' for number in range(9)}
    require_true(report, ['all_nine_native_mountains_complete',
                          'all_nine_controller_entries_and_returns',
                          'all_nine_native_surf_landings_and_reembarkations',
                          'two_roundtrips_per_cave', 'atlas_events_and_warps_unchanged',
                          'no_internal_warps_or_coordinate_writes',
                          'initial_positions_and_party_are_fixtures'])
    for cave in report['caves']:
        assert cave['native_mountain_cells_checked'] == 81
        require_true(cave, ['complete_native_mountain_loaded',
                            'controller_door_roundtrip',
                            'native_surf_landing_and_reembarkation',
                            'foot_state_inside'])
        assert len(cave['cycles']) == 2
        assert len(cave['native_controller_transitions']) == 4
        assert len(cave['native_surf_prompts']) == 2
        assert cave['walked_tiles']


def verify_beach_visibility(report, baseline):
    require_true(report, ['native_avatar_pixels_checked',
                          'sprite_flags_alone_not_sufficient',
                          'player_movement_uses_controller_input',
                          'no_coordinates_or_elevation_writes_after_initial_placement',
                          'source_map_dimensions_terrain_and_vendors_unchanged'])
    assert report['expected_broken_baseline'] is False and report['bug_reproduced'] is False
    samples = {row['label']: row for row in report['samples']}
    assert len(samples) == len(report['samples']) == 6
    assert set(samples) == {'ordinary-sand-visible-reference',
                            'east-beach-corner-avatar', 'east-side-of-bridge-footing',
                            'west-side-of-bridge-footing', 'west-beach-curve',
                            'returned-to-original-beach'}
    reference = samples['ordinary-sand-visible-reference']
    assert reference['red_hat_pixels'] >= 12 and reference['lower_body_pixels'] >= 12
    for row in samples.values():
        assert row['elevation'] == 3 and row['surf'] is False
        assert row['priority'] == 2 and row['ground_layer'] == 1
        assert row['sprite_enabled'] is True and row['object_enabled'] is True
        assert row['red_hat_pixels'] >= reference['red_hat_pixels'] * 0.75
        assert row['lower_body_pixels'] >= reference['lower_body_pixels'] * 0.75
    broken = {row['label']: row for row in baseline['samples']}
    for label, tile in [('east-beach-corner-avatar', [7, 16]),
                        ('east-side-of-bridge-footing', [7, 15])]:
        assert samples[label]['tile'] == broken[label]['tile'] == tile
        assert broken[label]['lower_body_pixels'] == 0
        assert samples[label]['lower_body_pixels'] > 8
    assert broken['east-beach-corner-avatar']['red_hat_pixels'] == 0
    attributes = {row['metatile']: row['attribute'] for row in report['compiled_ground_attributes']}
    old_attributes = {row['metatile']: row['attribute'] for row in baseline['compiled_ground_attributes']}
    expected = {0x201, 0x202, 0x207, 0x221, 0x22A, 0x238,
                0x240, 0x241, 0x244, 0x245, 0x246}
    assert len(report['compiled_ground_attributes']) == len(baseline['compiled_ground_attributes']) == 11
    assert set(attributes) == set(old_attributes) == expected
    for tile in expected:
        assert old_attributes[tile] >> 12 == 0
        assert attributes[tile] == ((old_attributes[tile] & 0x0FFF) | 0x1000)


def verify_source(report, info, old):
    assert report['layers'] == info['integration_layers']
    assert report['parent_rom_sha256'] == old['parent_rom_sha256']
    assert report['compiled_rom'] is True and report['preflight'] is False
    assert len(report['changed_files']) == len(set(report['changed_files'])) == len(ALLOWED_SOURCE_FILES) == 108
    assert set(report['changed_files']) == set(report['allowed_changed_files']) == ALLOWED_SOURCE_FILES
    assert report['source_hashes_checked'] > 30000
    require_true(report, ['independent_replay', 'idempotent',
                          'unrelated_source_files_unchanged',
                          'gyms_and_campaign_unchanged',
                          'atlas_graphics_unchanged', 'save_and_link_abi_unchanged',
                          'authorized_port_warp_changes_only',
                          'all_seven_terminals_at_town_bridge_ends',
                          'all_seven_separate_terminals_removed',
                          'surf_reboarding_uses_native_state_transition',
                          'original_tm_hm_and_item_numbers_preserved'])
    assert len(report['ports']) == 7
    assert {row['island'] for row in report['ports']} == ISLANDS
    assert report['extra_gyms_preserved'] == 8
    assert report['compiled_item_constants_preserved'] > 50
    ocean = report['ocean']
    require_true(ocean, ['passed', 'only_graphics_464_to_467_water_underlays_retargeted',
                         'all_native_attributes_and_behavior_tables_unchanged',
                         'original_shared_banks_unchanged',
                         'original_primary_palette_graphics_and_callback_reused',
                         'exact_private_before_tables_reconstructed'])
    assert ocean['water_table_words_checked'] > 1000
    assert ocean['native_upper_body_words_preserved'] * 2 == ocean['water_table_words_checked']
    six = report['six_landscape']
    require_true(six, ['source_tree_objects_complete', 'cliff_outline_complete'])
    assert six['complete_tree_count'] == len(six['objects']) == 18
    assert six['dimensions'] == [24, 30]
    assert len(six['preserved_buildings']) == 4
    for row in six['preserved_buildings']:
        require_true(row, ['complete_native_footprint_unchanged'])


def verify_six_landscape(report, directory):
    assert report['preflight'] is False
    require_true(report, ['source_tree_objects_complete', 'cliff_outline_complete',
                          'loaded_blocks_match_source', 'initial_travel_and_progress_are_fixtures',
                          'player_movement_uses_controller_input',
                          'no_position_or_elevation_writes_after_initial_placement'])
    assert report['dimensions'] == [24, 30]
    assert report['complete_tree_count'] == len(report['objects']) == 18
    owned = set()
    for tree in report['objects']:
        require_true(tree, ['crown_middle_and_base_complete'])
        x, y, width, height = tree['bounds']
        assert width == 2 and height == 3 and 0 <= x <= 22 and 0 <= y <= 27
        cells = {(x + dx, y + dy) for dy in range(3) for dx in range(2)}
        assert not owned & cells
        owned.update(cells)
        assert tree['native_rows'][:2] == [[0x300E, 0x300F], [0x041E, 0x041F]]
        left, right = tree['native_rows'][2]
        assert left in [0x0424, 0x0426] and right in [0x0425, 0x0427]
    assert len(report['cliff_cells']) == 25
    assert len({tuple(row['position']) for row in report['cliff_cells']}) == 25
    assert report['loaded_cell_count'] == 720
    assert len(report['dry_controller_routes']) == 7
    assert len(report['doors_tested']) == 5
    assert {row['warp_id'] for row in report['doors_tested']} == set(range(5))
    assert len({row['destination'] for row in report['doors_tested']}) == 5
    assert len(report['collision_checks']) == 7
    for row in report['dry_controller_routes']:
        require_true(row, ['complete', 'dry', 'controller_input'])
    for row in report['doors_tested']:
        require_true(row, ['entered', 'exited', 'dry_return', 'controller_input'])
    for row in report['collision_checks']:
        require_true(row, ['blocked', 'native_collision', 'controller_input'])
    assert len(report['captures']) == 18
    verify_captures(report['captures'], directory)
    assert len(report['source_review_images']) == 2
    assert {row['state'] for row in report['source_review_images']} == {'before', 'after'}
    for row in report['source_review_images']:
        path = Path(row['file'])
        assert not path.is_absolute() and '..' not in path.parts
        assert hashlib.sha256((directory / path).read_bytes()).hexdigest() == row['sha256']
        with Image.open(directory / path) as screenshot:
            assert screenshot.size == (624, 728)


def verify_ocean_seams(report, directory):
    assert report['kind'] == 'sevii-integrated-ocean-seams'
    assert report['preflight'] is False and report['full_campaign_playthrough'] is False
    require_true(report, ['compiled_rom', 'loaded_metatiles_palettes_and_vram_checked',
                          'attributes_and_native_object_body_words_preserved',
                          'ocean_palette_identical_at_all_checked_seams',
                          'all_affected_surface_connections_covered',
                          'no_midcrossing_warps_or_coordinate_writes',
                          'initial_positions_avatar_modes_party_and_progress_are_fixtures',
                          'fast_water_semantics_checked_per_map'])
    assert len(report['target_maps']) == len(set(report['target_maps'])) == 18
    assert report['surface_seams'] == len(report['seams']) == 26
    assert report['native_controller_crossings'] == 52
    assert report['surf_seams'] + report['land_seams'] == 26
    assert report['walked_tiles'] > 0
    compiled = report['compiled_art']
    require_true(compiled, ['compiled_tables_match_source', 'compiled_attributes_shared',
                            'native_body_words_unchanged', 'graphics_palettes_and_callbacks_identical',
                            'ocean_fast_water_surf_dive_encounter_attributes_preserved'])
    assert len(compiled['compiled_metatile_tables']) == 7
    for row in compiled['compiled_metatile_tables']:
        require_true(row, ['attributes_pointer_preserved'])
        assert row['compiled_words'] > 0 and row['canonical_water_words'] > 0
        assert row['compiled_attribute_bytes'] > 0
    assert len(report['captures']) == len(report['loaded_checks']) == 78
    images = verify_captures(report['captures'], directory)
    loaded = {row['label']: row for row in report['loaded_checks']}
    assert len(loaded) == 78
    assert set(report['target_maps']) <= {row['map'] for row in loaded.values()}
    captures = {row['file']: row for row in report['captures']}
    for label, row in loaded.items():
        assert row['capture']['file'] == label + '.png'
        assert row['capture'] == captures[row['capture']['file']]
        assert row['capture']['file'] in images
        assert row['loaded_art']['map'] == row['map']
        require_true(row['loaded_art'], ['loaded_graphics_and_palette_verified',
                                        'native_map_buffer_unchanged', 'native_body_words_unchanged'])
        assert row['loaded_art']['canonical_lower_words'] == [16838, 16839, 16839, 16838]
        assert row['loaded_art']['native_ocean_palette'] == row['ocean_palette']
        assert len(row['ocean_palette']) == 4 and row['loaded_art']['valid_animation_phases']
    pairs, checked_labels = set(), set()
    surf = 0
    for seam in report['seams']:
        pair = tuple(seam['maps'])
        assert len(pair) == len(set(pair)) == 2 and pair == tuple(sorted(pair)) and pair not in pairs
        pairs.add(pair)
        require_true(seam, ['outbound_and_return', 'ocean_palette_identical',
                            'no_midcrossing_warps_or_coordinate_writes'])
        assert seam['native_controller_crossings'] == len(seam['transitions']) == 2
        assert seam['available_reciprocal_passages'] > 0
        assert seam['mode'] in ['surf', 'foot']
        surfing = seam['mode'] == 'surf'
        surf += surfing
        assert seam['surf_preserved'] is surfing
        assert seam['native_foot_mode_preserved'] is (not surfing)
        source, destination = seam['source'][0], seam['destination'][0]
        assert set(pair) == {source, destination}
        outbound, returned = seam['transitions']
        assert [outbound['source'][0], outbound['destination'][0]] == [source, destination]
        assert [returned['source'][0], returned['destination'][0]] == [destination, source]
        labels = seam['loaded_checks']
        assert len(labels) == 3 and len(set(labels)) == 3 and not checked_labels & set(labels)
        checked_labels.update(labels)
        before, after, returned = [loaded[label] for label in labels]
        assert [before['map'], after['map'], returned['map']] == [source, destination, source]
        assert all(row['surfing'] is surfing for row in [before, after, returned])
        assert before['ocean_palette'] == after['ocean_palette'] == returned['ocean_palette']
    assert checked_labels == set(loaded)
    assert surf == report['surf_seams']


def verify_update(directory, info):
    directory = Path(directory)
    old = previous_release(info)
    assert old['validated'] and old['validation_scope'] == 'dewford-coast-safety'
    assert old['integration_layers'] + [SCOPE] == info['integration_layers']
    assert info['historical_validation'] == old['historical_validation']
    assert info['previous_validation'] == old['previous_validation']
    assert info['full_campaign_playthrough'] is False
    assert info['previous_features_retested_on_current_rom'] is False
    _, previous_review = pinned_file(info['previous_review_validation'])
    previous_save, save_bytes = pinned_file(info['previous_review_save_validation'])
    assert len(save_bytes) == 131072
    visibility_path, visibility_raw = pinned_file(info['baseline_dewford_visibility'])
    visibility_baseline = json.loads(visibility_raw)
    assert visibility_baseline['passed'] is False
    assert visibility_baseline['expected_broken_baseline'] is True
    assert visibility_baseline['bug_reproduced'] is True
    assert visibility_baseline['rom_sha256'] == old['parent_rom_sha256']
    require_true(visibility_baseline, ['native_avatar_pixels_checked',
                                     'sprite_flags_alone_not_sufficient',
                                     'player_movement_uses_controller_input',
                                     'no_coordinates_or_elevation_writes_after_initial_placement'])
    verify_visibility_captures(visibility_baseline, visibility_path.parent)
    verify_reboarding_baseline(info['baseline_sevii_reboarding'], old['parent_rom_sha256'])
    test = verify_review(ROOT / 'roms/rom-de-teste',
                         directory / 'Pokemon-Journey-Gen1-9-Normal.gba')
    expected = {'common': info['parent_rom_sha256'], 'test': test['sha256'],
                **{row['file']: row['sha256'] for row in info['variants']}}
    required = {('common', 'sevii-integrated-source'), ('common', 'all-surf-links')}
    required |= {(target, kind) for target in expected if target != 'common'
                 for kind in EDITION_KINDS}
    assert len(required) == 42
    covered = set()
    for proof in info['proofs']:
        key = proof['target'], proof['kind']
        assert key in required and key not in covered, key
        covered.add(key)
        path = Path(proof['file'])
        assert not path.is_absolute() and '..' not in path.parts
        raw = (directory / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == proof['sha256']
        report = current_report(raw, expected[proof['target']], key)
        kind = proof['kind']
        if proof['target'] == 'Pokemon-Journey-Gen1-9-Normal.gba' and kind in {'integrated-piers', 'dewford-coast'}:
            assert 'video_sha256' in report, ('Missing current native recording', key)
        if kind in EDITION_KINDS and kind not in {'coastal-cave-finishing', 'cold-boot'}:
            assert report['review_mode'] is (proof['target'] == 'test')
        if kind == 'sevii-integrated-source':
            verify_source(report, info, old)
        elif kind == 'all-surf-links':
            verify_surf(report)
        elif kind == 'integrated-piers':
            verify_integrated_piers(report, directory / path.parent)
        elif kind == 'six-landscape':
            verify_six_landscape(report, directory / path.parent)
        elif kind == 'ocean-seams':
            verify_ocean_seams(report, directory / path.parent)
        elif kind == 'dewford-coast':
            verify_dewford(report, directory / path.parent)
        elif kind == 'coastal-cave-finishing':
            verify_caves(report)
        elif kind == 'dewford-beach-visibility':
            verify_beach_visibility(report, visibility_baseline)
            verify_visibility_captures(report, directory / path.parent)
        elif kind == 'cold-boot':
            require_true(report, ['fresh_rom_boot_to_title', 'fresh_rom_title_to_new_game',
                                  'no_assert_screen', 'controllers_only',
                                  'no_game_memory_writes'])
            if proof['target'] == 'test':
                assert report['bundled_save_continue_to_field'] is True
                current_save = ROOT / 'roms/rom-de-teste/Pokemon-Journey-TESTE.sav'
                assert hashlib.sha256(current_save.read_bytes()).hexdigest() == report['bundled_save_sha256']
        elif kind == 'review-mode':
            assert report['fixture_wild_encounters_disabled'] is False
            checks = report['checks']
            assert bool(checks['trainer_approach_result']) == (proof['target'] != 'test')
            if proof['target'] == 'test':
                assert checks['random_wild_attempts'] >= 200
                require_true(checks, ['native_flash_save_exported', 'no_random_encounters',
                                      'no_fishing_encounters', 'no_sweet_scent_encounters',
                                      'no_rock_smash_encounters',
                                      'no_automatic_approach_after_600_frames'])
                current_save = ROOT / 'roms/rom-de-teste/Pokemon-Journey-TESTE.sav'
                assert hashlib.sha256(current_save.read_bytes()).hexdigest() == checks['save_sha256']
        else:
            raise AssertionError(('Unsupported proof contract', kind))
    assert covered == required
    assert all((directory / row['file']).read_bytes()[test['review_mode_offset']] == 0
               for row in info['variants'])
    from verify_dewford_coast_update import verify_update as verify_previous
    verify_previous(directory, old, historical_review=json.loads(previous_review),
                    historical_save=previous_save)
