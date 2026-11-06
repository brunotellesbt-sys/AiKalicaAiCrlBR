"""Strict exported evidence contract for native Sevii corners and southern access."""
import hashlib
import json
from pathlib import Path

import sevii_route_boundaries_contract as contract
from publish_coastal_closures import report_dependencies
from sevii_boundary_camera import REPRO_CASES
from verify_coastal_closures_update import verify_cold_boot
from verify_sevii_integrated_piers_update import require_true, verify_captures, verify_native_avatar_pixels

BEACH = 'OneIsland_TreasureBeach_Frlg'
START = ['JourneySurfLink03505', 8, 14]
BUMP_MAPS = ['OneIsland_Frlg', 'TwoIsland_Frlg', 'ThreeIsland_Port_Frlg',
             'FourIsland_Frlg', 'FiveIsland_Frlg', 'SixIsland_Frlg', 'SevenIsland_Frlg',
             'JourneySurfLink03502']
FORWARD = [['OneIsland_Harbor_Frlg', 8, 6], ['JourneySurfLink05001', 8, 6],
           ['JourneySurfLink05000', 12, 11], [BEACH, 4, 1], [BEACH, 4, 43],
           [BEACH, 35, 43], [BEACH, 35, 14], [BEACH, 29, 14], [BEACH, 29, 6],
           [BEACH, 25, 6], ['OneIsland_Frlg', 12, 17]]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha(value):
    assert isinstance(value, str) and len(value) == 64 and set(value) <= set('0123456789abcdef')


def player(state, *, point=None, surfing=None, check_blob=True):
    assert state['sprite_visible'] is state['object_visible'] is True
    assert state['surfing'] is True or state['surfing'] is False
    assert state['elevation'] == (1 if state['surfing'] else 3)
    assert state['priority'] == 2
    if check_blob:assert state['active_surf_blobs']==int(state['surfing'])
    assert len(state['tile']) == 2 and all(type(value) is int for value in state['tile'])
    if point is not None:
        assert [state['map'], *state['tile']] == point
    if surfing is not None:
        assert state['surfing'] is surfing


def verify_pixels(info, attachment, captures, images, cell, expected_mid):
    require_true(info, ['undefined_cells_included', 'actual_hardware_bg_words_and_scanout_checked',
                        'sprites_and_opaque_ui_explicitly_excluded', 'mismatches_not_discarded'])
    assert len(info['cells']) == 1
    row = info['cells'][0]
    assert row['cell'] == cell and row['expected_metatile'] == row['native_metatile'] == expected_mid
    assert row['quadrants'] == [0, 1, 2, 3] and row['checked_pixels'] >= 32
    words = row['definition_words']
    assert len(words) == 8 and all(type(word) is int and 0 <= word <= 65535 for word in words)
    assert row['layer'] in (0, 1, 2)
    actual = row['actual_bg_words']
    assert len(actual) == 4 and [item['quadrant'] for item in actual] == [0, 1, 2, 3]
    for item in actual:
        q = item['quadrant']
        expected = {0: [words[4+q], words[q], 0x3014],
                    1: [0, words[4+q], words[q]],
                    2: [words[4+q], 0, words[q]]}[row['layer']]
        assert item['words'] == expected, 'Reported BG words differ from the loaded metatile definition'
    assert captures[attachment['file']] == attachment['sha256']
    image = images[attachment['file']]
    samples = row['samples']
    assert len(samples) == 16 and {sample[5] for sample in samples} == set(range(4))
    assert len({tuple(sample[:2]) for sample in samples}) == len(samples)
    for x, y, red, green, blue, quadrant in samples:
        assert all(type(value) is int for value in (x, y, red, green, blue, quadrant))
        assert 0 <= x < 240 and 0 <= y < 160 and 0 <= quadrant < 4
        assert all(0 <= value <= 248 and value%8 == 0 for value in (red, green, blue))
        assert all(abs(a-b) <= 7 for a, b in zip(image.getpixel((x, y)), (red, green, blue))), 'Native corner pixels differ from the attached capture'


def verify_cold(report, directory, battery, rom_sha, expected, *, saved=False, avatar=False):
    assert report['passed'] is True and report['rom_sha256'] == rom_sha
    verify_cold_boot(report, True, battery)
    assert report['bundled_save_tested'] is True
    runs = report['runs']
    assert len(runs) == 2 and [row['battery'] for row in runs] == [False, True]
    assert all(row['frames'] >= 2000 and row['samples'] for row in runs)
    continued = runs[1]
    require_true(continued, ['bundled_save_continue_to_field', 'no_callback_script_or_native_call_injection'])
    assert continued['field_map'] == expected['map_id'] and continued['player_tile'] == expected['tile']
    assert continued['player_surfing'] is expected['surfing'] and continued['player_elevation'] == expected['elevation']
    images = verify_captures(report['captures'], directory)
    names = {'fresh-title.png', 'fresh-main-menu.png', 'fresh-new-game.png',
             'battery-title.png', 'battery-main-menu.png', 'battery-continued-to-field.png'}
    if avatar:
        names.add('battery-avatar-visible.png')
        verify_native_avatar_pixels(continued['native_avatar_pixels'], images['battery-avatar-visible.png'])
    if saved:
        names.add('migrated-dock-saved-through-menu.png')
        assert continued['saved_after_continue_with_controllers'] is True
        assert 'SaveReturnSuccessCallback' in continued['save_menu_callbacks']
        assert len(report['battery_saves']) == 1
        row = report['battery_saves'][0]
        assert row['file'] == 'layer169-migrated-dock.sav' and row['bytes'] == 131072
        assert digest(Path(directory)/row['file']) == row['sha256'] == continued['saved_battery_sha256']
    assert set(images) == names


def verify_report(report, directory, expected_rom_sha256=None):
    directory = Path(directory)
    assert report['kind'] == 'sevii-route-boundaries-native'
    require_true(report, ['passed', 'compiled_rom', 'native_validation_performed',
        'initial_party_badges_progress_and_encounter_suppression_are_fixtures',
        'no_midtrip_position_elevation_camera_palette_or_vram_writes', 'no_callback_replacement',
        'gameplay_scripts_not_injected_after_placement', 'native_getter_trampoline_and_final_save_are_declared'])
    assert report['preflight'] is report['full_campaign_playthrough'] is False
    sha(report['rom_sha256'])
    sha(report['elf_sha256'])
    if expected_rom_sha256 is not None:
        assert report['rom_sha256'] == expected_rom_sha256
    captures = {row['file']: row['sha256'] for row in report['captures']}
    assert len(captures) == len(report['captures'])
    images = verify_captures(report['captures'], directory)
    expected_names = set()
    rows = report['corner_cases']
    assert len(rows) == len(REPRO_CASES) == 2
    for index, (row, fixture) in enumerate(zip(rows, REPRO_CASES)):
        case = row['case']
        for key, value in fixture.items():
            if key == 'expected_metatile':
                assert case['historical_expected_metatile'] == value
            else:
                assert case[key] == value
        sha(case['source_blockdata_sha256'])
        assert case['source_block']&1023 == case['expected_metatile']
        assert row['controlled_outbound_and_return'] is True
        for key, point, cell in [('before', [case['map'], *case['player']], case['cell']),
                                 ('after', [case['neighbor'], *case['target']], case['neighbor_cell']),
                                 ('returned', [case['map'], *case['player']], case['cell'])]:
            view = row[key]
            player(view['state'], point=point, surfing=True)
            grid = view['grid']
            if key == 'after':
                assert grid == dict(cell=cell, grid_block=1023, metatile=case['expected_metatile'],
                                    collision=1, elevation=0, border_id=0xFFFFFFFF)
            else:
                assert grid['cell'] == cell and grid['grid_block'] == case['source_block']
                assert grid['metatile'] == case['expected_metatile']
                assert grid['collision'] == (case['source_block']>>10)&3
                assert grid['elevation'] == case['source_block']>>12
                assert grid['border_id'] in (1,2,3,4)
            name = 'corner-%d-%s.png'%(index, 'return' if key == 'returned' else key)
            assert view['capture']['file'] == name
            expected_names.add(name)
            assert view['pixels']['map'] == point[0]
            verify_pixels(view['pixels'], view['capture'], captures, images, cell, case['expected_metatile'])
    bumps = report['boundary_bumps']
    assert len(bumps) == len(BUMP_MAPS) and [row['map'] for row in bumps] == BUMP_MAPS
    for index, row in enumerate(bumps):
        require_true(row, ['actual_directional_input_blocked'])
        assert row['collision'] == 1 and row['reef_metatile'] == 0x243
        before, after = row['before'], row['after']
        player(before, surfing=True)
        player(after, point=[before['map'], *before['tile']], surfing=True)
        assert before['map'] == row['map']
        dx, dy = {16: (1, 0), 32: (-1, 0), 64: (0, -1), 128: (0, 1)}[row['direction_key']]
        assert row['reef_cell'] == [before['tile'][0]+dx, before['tile'][1]+dy]
        assert row['held_input_frames'] == 120
        assert row['one_tile_controller_retreat'] is True
        player(row['scanout_viewpoint'],point=[row['map'],before['tile'][0]-dx,before['tile'][1]-dy],surfing=True)
        name = 'boundary-%02d-blocked.png'%index
        assert row['capture']['file'] == name
        expected_names.add(name)
        verify_pixels(row['pixels'], row['capture'], captures, images, row['reef_cell'], row['reef_metatile'])
    loop = report['southern_loop']
    require_true(loop, ['no_midtrip_warps_or_player_state_writes', 'original_endpoint_roundtrip'])
    player(loop['initial'], point=START, surfing=True)
    player(loop['final'], point=START, surfing=True)
    assert loop['forward_waypoints'] == FORWARD
    goals = [*FORWARD, *reversed([START, *FORWARD[:-1]])]
    assert len(loop['arrivals']) == len(goals)
    for index, (row, goal) in enumerate(zip(loop['arrivals'], goals)):
        assert row['goal'] == goal
        player(row['state'], point=goal)
        name = 'loop-%02d-arrival.png'%index
        assert row['capture']['file'] == name and captures[name] == row['capture']['sha256']
        expected_names.add(name)
    # The dock and town must be reached on foot, followed by a native Surf prompt.
    assert loop['arrivals'][9]['state']['surfing'] is False
    assert loop['arrivals'][10]['state']['surfing'] is False
    assert loop['surf_prompts'] and loop['walked_tiles'] > 250
    gps = loop['gps_samples']
    assert len(gps) > 250 and [gps[0]['map'], *gps[0]['tile']] == START
    assert [gps[-1]['map'], *gps[-1]['tile']] == START
    deltas, seams = [], []
    for previous, current in zip(gps, gps[1:]):
        assert len(current['marker']) == 2 and all(type(value) is int and 0 <= value <= 255 for value in current['marker'])
        delta = max(abs(a-b) for a, b in zip(previous['marker'], current['marker']))
        assert current['delta'] == delta <= 2
        assert current['seam'] is (current['map'] != previous['map'])
        if current['seam']:
            assert delta == 0
            seams.append((previous, current))
        deltas.append(delta)
    assert loop['maximum_gps_step'] == max(deltas) <= 2
    assert loop['maximum_seam_delta'] == 0 and len(seams) == 10
    transitions = loop['transitions']
    assert len(transitions) == len(seams)
    for row, (previous, current) in zip(transitions, seams):
        assert row == dict(source=[previous['map'], *previous['tile']], destination=[current['map'], *current['tile']])
    animation = report['shoreline_animation']
    assert animation['map'] == BEACH and animation['tile'] == [4,43]
    assert animation['callbacks_clocks_palettes_and_vram_not_written'] is True
    groups = {'ocean','upper_current','upper_sand'}
    assert set(animation['source_frames_sha256']) == groups
    assert animation['phases_observed'] == {group:list(range(8)) for group in groups}
    assert len(animation['samples']) == 16
    seen = {group:set() for group in groups}
    for group in groups:
        assert len(animation['source_frames_sha256'][group]) == 8
        for value in animation['source_frames_sha256'][group]:sha(value)
    for index,sample in enumerate(animation['samples']):
        assert set(sample['groups']) == groups
        name = 'southern-shore-phase-%02d.png'%index
        assert sample['capture'] == dict(file=name,sha256=captures[name])
        expected_names.add(name)
        for group,row in sample['groups'].items():
            assert row['matches'] and all(type(i) is int and 0<=i<8 for i in row['matches'])
            assert all(row['vram_sha256']==animation['source_frames_sha256'][group][i] for i in row['matches'])
            seen[group].update(row['matches'])
    assert all(values==set(range(8)) for values in seen.values())
    assert set(captures) == expected_names
    fixtures = report['fixtures']
    assert len(fixtures) == 11 and [row['case'] for row in fixtures] == [
        'corner-0', 'corner-1', *['boundary-'+str(index) for index in range(8)], 'continuous-south-loop']
    assert [fixtures[-1]['map'], *fixtures[-1]['tile']] == START
    assert report['inputs'] and all(row['frames'] > 0 and row['key'] in (0, 1, 2, 4, 8, 16, 32, 64, 128) for row in report['inputs'])
    assert any(row['phase'] == 'continuous-south-loop' and row['key'] in (16, 32, 64, 128) for row in report['inputs'])
    calls = report['native_calls']
    assert calls and sum(row['function'] == 'TrySavingData' for row in calls) == 1
    for row in calls:
        name = row['function']
        assert name.startswith(('MapGridGet', 'MetatileBehavior_Is')) or name in {
            'GetMapBorderIdAt', 'GetPlayerFacingDirection', 'IsPlayerFacingSurfableFishableWater',
            'PlayerGetElevation', 'JourneyWorldMapPosition', 'TrySavingData'}
        assert row['purpose'] == ('native-save' if name == 'TrySavingData' else 'read-only-query')
    battery = directory/'southern-surf-loop.sav'
    assert battery.stat().st_size == 131072
    assert report['battery_saves'] == [dict(file=battery.name, sha256=digest(battery), bytes=131072)]
    components = {row['kind']: row for row in report['components']}
    assert len(components) == len(report['components']) == 6
    expected_components = {'cold-boot': 'cold-continue/cold-boot.json',
        'camera-baseline': 'camera-baseline/camera-baseline.json',
        'legacy-save-fixture': 'legacy-parent/legacy-dock-fixture.json',
        'migration-first-continue': 'migration-first-continue/cold-boot.json',
        'migration-second-continue': 'migration-second-continue/cold-boot.json',
        'one-island-newgame': 'one-island-newgame/arrival-coast-landing-case.json'}
    loaded = {}
    for kind, name in expected_components.items():
        row = components[kind]
        assert row['file'] == name
        path = directory/name
        report_dependencies(path, expected_sha=row['sha256'])
        loaded[kind] = json.loads(path.read_bytes())
    baseline = loaded['camera-baseline']
    assert baseline == report['camera_baseline']
    assert baseline['kind'] == 'sevii-route-boundaries-camera-baseline'
    require_true(baseline, ['passed', 'expected_broken_baseline', 'bug_reproduced', 'native_validation_performed',
                          'initial_views_party_progress_and_encounter_suppression_are_fixtures'])
    assert baseline['rom_sha256'] == contract.PARENT_ROM_SHA256 and baseline['elf_sha256'] == contract.PARENT_ELF_SHA256
    baseline_folder = directory/'camera-baseline'
    baseline_images = verify_captures(baseline['captures'], baseline_folder)
    baseline_captures = {row['file']: row['sha256'] for row in baseline['captures']}
    assert len(baseline_images) == 4 and len(baseline['cases']) == 2
    for index, (row, fixture) in enumerate(zip(baseline['cases'], REPRO_CASES)):
        assert row['case'] == fixture
        require_true(row, ['same_world_cell', 'reproduced_metatile_disagreement'])
        for key, mid, point, cell in [('before', 299, [fixture['map'], *fixture['player']], fixture['cell']),
                                      ('after', 579, [fixture['neighbor'], *fixture['target']], fixture['neighbor_cell'])]:
            view = row[key]
            player(view['state'], point=point, surfing=True, check_blob=False)
            assert view['cell'] == cell and view['metatile'] == mid
            if key == 'after':
                assert view['collision'] == 1 and view['elevation'] == 0 and view['border_id'] == 0xFFFFFFFF
            else:
                assert view['collision'] == 0 and view['elevation'] == 1 and view['border_id'] in (1,2,3,4)
            assert view['initial_view_placement_is_a_fixture'] is True
            assert view['capture']['file'] == 'baseline-corner-%d-%s.png'%(index, key)
            verify_pixels(view['pixels'], view['capture'], baseline_captures, baseline_images, cell, mid)
    cold = loaded['cold-boot']
    assert cold == report['cold_continue']
    # The raw map id is bound between the fresh core and its declared fixture.
    loop_expected = dict(map_id=cold['runs'][1]['field_map'], tile=START[1:], surfing=True, elevation=1)
    verify_cold(cold, directory/'cold-continue', battery, report['rom_sha256'], loop_expected)
    migration = report['save_migration']
    require_true(migration, ['translation_applied_exactly_once', 'controller_save_between_cold_boots'])
    assert migration['old_tile'] == [12, 2] and migration['migrated_tile'] == [20, 2]
    legacy = loaded['legacy-save-fixture']
    assert legacy == migration['legacy']
    assert legacy['kind'] == 'sevii-route-boundaries-legacy-save-fixture'
    assert legacy['rom_sha256'] == contract.PARENT_ROM_SHA256 and legacy['elf_sha256'] == contract.PARENT_ELF_SHA256
    require_true(legacy, ['passed', 'initial_party_progress_and_placement_are_fixtures', 'actual_native_flash_export'])
    player(legacy['player'], point=[BEACH, 12, 2], surfing=False, check_blob=False)
    legacy_images = verify_captures(legacy['captures'], directory/'legacy-parent', ['legacy-168-dock.png'])
    verify_native_avatar_pixels(legacy['player']['native_avatar_pixels'], legacy_images['legacy-168-dock.png'])
    old_battery = directory/'legacy-parent/layer168-treasure-dock.sav'
    assert old_battery.stat().st_size == 131072
    assert legacy['battery_saves'] == [dict(file=old_battery.name, sha256=digest(old_battery), bytes=131072)]
    first, second = loaded['migration-first-continue'], loaded['migration-second-continue']
    assert first == migration['first_continue'] and second == migration['second_continue']
    expected = dict(map_id=legacy['map_id'], tile=[20, 2], surfing=False, elevation=3)
    verify_cold(first, directory/'migration-first-continue', old_battery, report['rom_sha256'], expected, saved=True, avatar=True)
    new_battery = directory/'migration-first-continue/layer169-migrated-dock.sav'
    verify_cold(second, directory/'migration-second-continue', new_battery, report['rom_sha256'], expected, avatar=True)
    from verify_arrival_coast_landing_proof import _census, _case
    arrival=report['one_island_newgame']
    assert arrival['case']==loaded['one-island-newgame']
    assert arrival['case']['starting_region']=='sevii' and arrival['case']['city_index']==0
    compiled=_census(arrival['compiled_arrival_census'])
    home=arrival['case']['home_index']
    _case(arrival['case'],report,compiled[home],directory/'one-island-newgame')
    return report
