"""Check the observed Cinnabar door/bridge regression and two real old saves."""
import hashlib
import json
from pathlib import Path

from arrival_coast_review_contract import PARENT_ROM_SHA256
from verify_sevii_integrated_piers_update import (
    require_true, verify_captures, verify_native_avatar_pixels,
)

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT/'docs/design/arrival-coast-review/baseline/cinnabar-door'
TOWN = 'CinnabarIsland_Frlg'
DECK = [(x, 15) for x in range(6, 12)] + [(x, y) for y in (16, 17) for x in (9, 10)]
PERIMETER = [([6, 15], [5, 15], 32), ([6, 15], [6, 16], 128),
    ([7, 15], [7, 16], 128), ([8, 15], [8, 16], 128),
    ([11, 15], [12, 15], 16), ([9, 16], [8, 16], 32),
    ([9, 17], [8, 17], 32), ([9, 17], [9, 18], 128),
    ([10, 17], [10, 18], 128)]
UNDERPASS = [(8, 18), (8, 17), (8, 16), (8, 15)]
UNDERPASS += [(x, 15) for x in range(7, 5, -1)]
UNDERPASS += [(x, 15) for x in range(7, 17)]
UNDERPASS += [(16, 16), (16, 15)]
UNDERPASS += [(x, 15) for x in range(15, 5, -1)]
UNDERPASS += [(7, 15), (8, 15), (8, 16), (8, 17), (8, 18), (9, 18)]
LEGACY = {
    'bridge': ('cinnabar-door-level0',
        'a47e3f94b17b559c5da96bfeab2bbe51af412c26524772f1321f51136dac97fb',
        'c3c2f4a1d09d22842585c810886b684a974552fcd07ded8f5bf371acc474c515'),
    'water': ('cinnabar-door-walking-water',
        'b9bdae0d7eea112c9ff3e26f6b956838e9e7a2f5ddac3d7befe9a5893af9453a',
        '6e11f7ceaf680d8f665dce761d9ae116503d29dce79b11cc1197c13e693fd914'),
}


def legacy_baseline(kind):
    name, battery_sha, manifest_sha = LEGACY[kind]
    raw = (BASELINE/(name+'.json')).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == manifest_sha
    battery = (BASELINE/(name+'.sav')).read_bytes()
    assert len(battery) == 131072 and hashlib.sha256(battery).hexdigest() == battery_sha
    report = json.loads(raw)
    assert report['passed'] is True and report['rom_sha256'] == PARENT_ROM_SHA256
    assert report['battery_sha256'] == battery_sha and report['map_id'] == [37, 8]
    require_true(report, ['actual_terminal_entry_and_exit_reproduce_level0',
        'no_midtrip_coordinate_elevation_or_avatar_writes',
        'initial_placement_party_and_progress_are_fixtures'])
    assert not report['broken']['surfing']
    assert report['broken']['tile'] == ([7, 15] if kind == 'bridge' else [12, 15])
    assert report['broken']['elevation'] == (0 if kind == 'bridge' else 1)
    verify_captures(report['captures'], BASELINE)
    return battery_sha


def cold_run(report, parent, kind):
    require_true(report, ['passed', 'fresh_rom_boot_to_title', 'fresh_rom_title_to_new_game',
        'no_assert_screen', 'controllers_only', 'no_game_memory_writes',
        'bundled_save_tested', 'bundled_save_continue_to_field'])
    assert report['rom_sha256'] == parent['rom_sha256']
    assert report['legacy_parent_rom_sha256'] == PARENT_ROM_SHA256
    assert report['bundled_save_sha256'] == legacy_baseline(kind)
    assert len(report['runs']) == 2
    fresh, saved = report['runs']
    assert fresh['battery'] is False and saved['battery'] is True
    require_true(fresh, ['fresh_rom_boot_to_title', 'fresh_rom_title_to_new_game'])
    require_true(saved, ['bundled_save_continue_to_field', 'no_game_memory_writes'])
    assert saved['field_map'] == [37, 8] and saved['frames'] > 3000
    assert fresh['samples'] and saved['samples']
    assert saved['samples'][-1]['callback'] == 'CB2_Overworld'
    return saved


def legacy_state(state, tile, surfing, elevation, priority):
    assert state['tile'] == list(tile) and state['surfing'] is surfing
    assert state['elevation'] == elevation and state['priority'] == priority


def verify(report, directory):
    directory = Path(directory)
    assert report['kind'] == 'cinnabar-door-exit'
    require_true(report, ['passed', 'compiled_rom', 'native_validation_performed',
        'controller_terminal_entry_and_exit',
        'dry_placement_does_not_replace_actual_door_exit',
        'all_exposed_pier_water_edges_block_pedestrians',
        'full_avatar_vram_pixels_after_door_exit',
        'native_surf_departure_underpass_and_reboard',
        'no_midtrip_coordinate_elevation_or_avatar_writes',
        'initial_placement_party_and_progress_are_fixtures',
        'movement_fixture_random_encounters_disabled',
        'legacy_actual_door_exit_battery_tested',
        'legacy_actual_walking_water_battery_tested'])
    assert report['full_campaign_playthrough'] is False
    assert len(report['rom_sha256']) == len(report['elf_sha256']) == 64
    assert report['rom_sha256'] != PARENT_ROM_SHA256
    names = {'initial-dry-land.png', 'terminal-interior.png',
        'door-exit-on-high-pier.png', 'native-surf-departure.png',
        'native-surf-reboarded.png', 'door-exit-after-surf-roundtrip.png',
        'final-bridge-water-blocked.png'}
    names |= {'deck-after-door-'+str(i)+'.png' for i in range(10)}
    names |= {'blocked-water-after-door-'+str(i)+'.png' for i in range(9)}
    names |= {'surf-underpass-'+str(i)+'.png' for i in range(34)}
    names |= {'legacy-continue/'+name+'.png' for name in (
        'battery-continued-to-field', 'legacy-bridge-restored', 'legacy-bridge-water-blocked')}
    names |= {'legacy-water-continue/'+name+'.png' for name in (
        'battery-continued-to-field', 'legacy-water-restored-native-surf',
        'legacy-water-reboarded-dry-pier')}
    assert len(names) == 66
    images = verify_captures(report['captures'], directory, names)

    def state(row, tile, label, surfing=False, priority=1, map_name=TOWN):
        assert row['map'] == map_name and row['tile'] == list(tile)
        assert row['surfing'] is surfing and row['elevation'] == (1 if surfing else 3)
        assert row['priority'] == priority
        require_true(row, ['sprite_visible', 'object_visible'])
        assert row['capture_file'] == label+'.png'
        if not surfing:
            verify_native_avatar_pixels(row['native_avatar_pixels'], images[label+'.png'])

    state(report['initial'], (11, 14), 'initial-dry-land', priority=2)
    state(report['interior'], (11, 13), 'terminal-interior', priority=2,
          map_name='JourneyCinnabarHarbor')
    state(report['door_exit'], (7, 15), 'door-exit-on-high-pier')
    assert report['door_exit']['tile_elevation'] == 15
    assert len(report['all_ten_dry_pier_cells']) == 10
    for i, (row, tile) in enumerate(zip(report['all_ten_dry_pier_cells'], DECK)):
        state(row, tile, 'deck-after-door-'+str(i))
        assert row['tile_elevation'] == (15 if tile[1] == 15 else 3)
    assert report['perimeter_edges'] == len(report['perimeter']) == 9
    assert [(r['dry'], r['water'], r['key']) for r in report['perimeter']] == PERIMETER
    for i, row in enumerate(report['perimeter']):
        assert row['walking_without_surf_blocked'] is True
        before = row['before']
        legacy_state(before, row['dry'], False, 3, 1)
        state(row['after'], row['dry'], 'blocked-water-after-door-'+str(i))
    state(report['departure'], (9, 18), 'native-surf-departure', True, 2)
    assert report['native_underpass_route'] == [list(p) for p in UNDERPASS]
    assert len(report['underpass']) == len(UNDERPASS) == 34
    for i, (row, tile) in enumerate(zip(report['underpass'], UNDERPASS)):
        state(row, tile, 'surf-underpass-'+str(i), True, 2)
    state(report['reboarded'], (9, 17), 'native-surf-reboarded')
    state(report['repeated_door_exit'], (7, 15), 'door-exit-after-surf-roundtrip')
    state(report['final'], (11, 15), 'final-bridge-water-blocked')

    saved = cold_run(report['legacy_continue'], report, 'bridge')
    assert report['legacy_continue']['legacy_actual_door_exit_battery_tested'] is True
    require_true(saved, ['legacy_bridge_level_restored', 'legacy_water_entry_blocked_by_controller'])
    legacy_state(saved['legacy_initial_state'], (7, 15), False, 3, 1)
    legacy_state(saved['legacy_final_state'], (11, 15), False, 3, 1)
    for key, label in [('legacy_initial_state', 'legacy-bridge-restored'),
                       ('legacy_final_state', 'legacy-bridge-water-blocked')]:
        verify_native_avatar_pixels(saved[key]['native_avatar_pixels'],
            images['legacy-continue/'+label+'.png'])

    saved = cold_run(report['legacy_water_continue'], report, 'water')
    assert report['legacy_water_continue']['legacy_actual_door_to_walking_water_battery_tested'] is True
    require_true(saved, ['legacy_walking_water_recovers_native_surf',
                         'legacy_controller_returned_to_pier'])
    legacy_state(saved['legacy_initial_state'], (12, 15), True, 1, 2)
    legacy_state(saved['legacy_final_state'], (9, 17), False, 3, 1)
    route = [((11,15),32),((10,15),32),((9,15),32),((8,15),32),
             ((8,16),128),((8,17),128),((8,18),128),((9,18),16),((9,17),64)]
    assert len(saved['legacy_controller_movements']) == len(route)
    last = (12, 15)
    for i, (move, (tile, key)) in enumerate(zip(saved['legacy_controller_movements'], route)):
        final = i == len(route)-1
        assert move['controller_input_only'] is True and move['direction_key'] == key
        assert 0 < move['held_input_frames'] < 180
        legacy_state(move['initial'], last, True, 1, 2)
        legacy_state(move['returned'], tile, not final, 3 if final else 1, 1 if final else 2)
        last = tile
    verify_native_avatar_pixels(saved['legacy_final_state']['native_avatar_pixels'],
        images['legacy-water-continue/legacy-water-reboarded-dry-pier.png'])
    return report
