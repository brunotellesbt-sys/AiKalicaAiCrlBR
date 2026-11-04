"""Verify complete controller-only new-game arrivals, not menu-only boots.

The aggregate retains every full case as a hashed component. Its summaries
cannot substitute for the input log, callback transitions and native captures.
The compiled table hash is recomputed here; the release verifier also binds it
to the independently replayed compiled-source proof.
"""
import hashlib
import json
from pathlib import Path
import re
import struct

from verify_sevii_integrated_piers_update import require_true, verify_captures

EXPECTED_HOMES = {
    **{city+1: ('kanto', city) for city in range(9)},
    **{city+10: ('sevii', city) for city in range(7)},
    **{city+17: ('hoenn', city) for city in range(1, 15)},
}
MODIFIED_BOAT_HOMES = frozenset({*range(10, 17), 21, 29, 31})
BOAT_HOMES = MODIFIED_BOAT_HOMES | {30}
CAPTURE_NAMES = frozenset({
    '01-region-menu.png', '02-avatar-menu.png', '03-city-menu.png',
    '04-city-confirmation.png', '05-truck.png', '06-mother-welcome.png',
    '07-home-bedroom.png',
})
COMMON_TRUE = ('actual_cold_boot', 'controllers_only', 'no_game_memory_writes',
               'no_callback_or_script_injection')
CASE_TRUE = (*COMMON_TRUE, 'passed', 'actual_city_selection_and_confirmation',
    'native_truck_door_crossed', 'arrival_player_and_mother_dry',
    'compiled_selected_destination_observed', 'actor_elevations_match_physical_ground',
    'no_existing_npc_overlap', 'native_home_bedroom_reached')


def _integer(value, low, high):
    assert type(value) is int and low <= value <= high, value
    return value


def _coordinate(value):
    assert isinstance(value, list) and len(value) == 2
    return [_integer(axis, 0, 32767) for axis in value]


def _sha(value):
    assert isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), value
    return value


def _relative(directory, name):
    path = Path(name)
    assert not path.is_absolute() and '..' not in path.parts and path.parts
    target = Path(directory)/path
    assert target.resolve().is_relative_to(Path(directory).resolve()), name
    return target


def _dry_terrain(row):
    value = _integer(row['block'], 0, 65535)
    assert row['elevation'] == value >> 12 >= 3
    assert row['collision'] == (value >> 10) & 3 == 0
    _integer(row['behavior'], 0, 511)
    assert row['surfable'] is False and row['dry'] is True


def _bedroom(home):
    if home == 1:
        return 'PalletTown_PlayersHouse_2F_Frlg'
    if home < 17:
        return f'JourneyFamilyBedroom{home-1:02d}'
    return f'JourneyHoennBedroom{home-17:02d}'


def _matching_terrain(observed, compiled, home):
    for field in ('elevation', 'collision', 'behavior', 'surfable', 'dry'):
        assert observed[field] == compiled[field]
    if observed['block'] != compiled['block']:
        # Native PacifidlogBridgePerStepCallback immediately submerges both
        # halves when the player initially stands on this floating log pair.
        # This exact graphical state change keeps native dry collision/height.
        assert home == 31
        assert (compiled['block'], observed['block']) in ((0x3258, 0x325A), (0x3260, 0x3262))


def _census(census):
    require_true(census, ['compiled_source_table_equal', 'all_player_and_mother_cells_dry',
                         'direct_compiled_map_layout_blockdata_and_attribute_reads'])
    assert census['row_count'] == len(census['rows']) == 31
    assert [row['home_index'] for row in census['rows']] == list(range(1, 32))
    raw = bytearray()
    rows = {}
    for row in census['rows']:
        home = row['home_index']
        assert isinstance(row['map'], str) and row['map']
        assert isinstance(row['map_id'], list) and len(row['map_id']) == 2
        group, number = [_integer(axis, 0, 255) for axis in row['map_id']]
        tx, ty = _coordinate(row['truck'])
        lx, ly = _coordinate(row['player']['tile'])
        assert type(row['boat']) is bool and row['boat'] is (home in BOAT_HOMES)
        expected_mother = [lx, ly-1] if row['boat'] else [tx+2, ty-1]
        assert row['mother']['tile'] == expected_mother
        for actor in ('player', 'mother'):
            _coordinate(row[actor]['tile'])
            _dry_terrain(row[actor])
        raw += struct.pack('<HhhhhBx', (group << 8) | number, tx, ty, lx, ly, row['boat'])
        rows[home] = row
    assert hashlib.sha256(raw).hexdigest() == _sha(census['compiled_table_sha256'])
    return rows


def _case(case, report, compiled, directory):
    assert case['kind'] == 'arrival-coast-landing-case' and case['diagnostic'] is False
    require_true(case, CASE_TRUE)
    assert case['rom_sha256'] == report['rom_sha256']
    assert case['elf_sha256'] == report['elf_sha256']
    home = case['home_index']
    assert (case['starting_region'], case['city_index']) == EXPECTED_HOMES[home]
    assert case['avatar_index'] == (3 if home == 10 else 0)
    welcome = case['welcome']
    assert welcome['map'] == case['expected_welcome_map'] == compiled['map']
    player, mother = welcome['player'], welcome['mother']
    expected_player = list(compiled['player']['tile'])
    if not compiled['boat']:
        expected_player[0] += 1  # actual native jump-right after the truck
    assert player['tile'] == case['expected_welcome_player_tile'] == expected_player
    assert mother['tile'] == case['expected_welcome_mother_tile'] == compiled['mother']['tile']
    assert player['local_id'] == 255 and mother['local_id'] == 251
    assert _integer(player['index'], 0, 15) != _integer(mother['index'], 0, 15)
    assert welcome['other_npc_overlaps'] == [] and player['surfing'] is False
    for actor in (player, mother):
        _dry_terrain(actor['terrain'])
        assert actor['elevation'] == actor['terrain']['elevation']
    _matching_terrain(mother['terrain'], compiled['mother'], home)
    if compiled['boat']:
        _matching_terrain(player['terrain'], compiled['player'], home)
    bedroom = case['bedroom']
    assert bedroom['map'] == _bedroom(home) and bedroom['surfing'] is False
    assert bedroom['player']['tile'] == [6, 6]
    assert bedroom['player']['local_id'] == 255 and bedroom['player']['elevation'] == 3
    frames = _integer(case['frames'], 1201, 1000000)
    inputs = case['input_log']
    assert isinstance(inputs, list) and len(inputs) >= 10
    assert [row['frame'] for row in inputs] == sorted({row['frame'] for row in inputs})
    for row in inputs:
        _integer(row['frame'], 0, frames)
        assert row['key'] in (1, 2, 8, 16, 32, 64, 128)
        _integer(row['held_frames'], 1, 120)
        _integer(row['pause_frames'], 0, 900)
        assert row['frame'] + row['held_frames'] + row['pause_frames'] <= frames
    assert inputs[0]['key'] == 8 and sum(row['key'] == 8 for row in inputs) >= 2
    assert any(row['key'] == 16 and row['held_frames'] == 8 for row in inputs)
    transitions = case['callback_transitions']
    assert len(transitions) >= 10
    assert [row['frame'] for row in transitions] == sorted({row['frame'] for row in transitions})
    for row in transitions:
        _integer(row['frame'], 0, frames)
        assert isinstance(row['callback'], str) and row['callback']
    callbacks = [row['callback'] for row in transitions]
    assert callbacks[0] == 'gInitialMainCB2'
    for name in ('CB2_MainMenu', 'CB2_NamingScreen', 'CB2_NewGame', 'CB2_Overworld'):
        assert name in callbacks
    assert callbacks.index('CB2_MainMenu') < callbacks.index('CB2_NamingScreen') < callbacks.index('CB2_NewGame') < callbacks.index('CB2_Overworld')
    boat_observed = any('SeaGallop' in value or 'Seagallop' in value for value in callbacks)
    assert case['native_boat_scene_observed'] is boat_observed is compiled['boat']
    verify_captures(case['captures'], directory, CAPTURE_NAMES)


def verify(report, directory):
    directory = Path(directory)
    assert report['kind'] == 'arrival-coast-landing' and report['passed'] is True
    assert report['diagnostic'] is False
    _sha(report['rom_sha256']); _sha(report['elf_sha256'])
    require_true(report, [*COMMON_TRUE, 'all_ten_modified_boat_starts_tested',
        'all_thirty_custom_start_cities_tested', 'original_littleroot_scene_covered_by_compiled_census_only'])
    assert report['full_new_game_controller_cases'] == len(report['cases']) == 30
    assert report['case_reports'] == report['components'] and len(report['components']) == 30
    compiled = _census(report['compiled_arrival_census'])
    components, homes, captures = set(), set(), []
    for summary, component in zip(report['cases'], report['components']):
        path = _relative(directory, component['file'])
        assert component['file'] not in components
        components.add(component['file'])
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == _sha(component['sha256'])
        case = json.loads(raw)
        home = case['home_index']
        assert home in EXPECTED_HOMES and home not in homes
        homes.add(home)
        expected_folder = f'{case["starting_region"]}-{case["city_index"]:02d}'
        assert Path(component['file']).as_posix() == expected_folder+'/arrival-coast-landing-case.json'
        assert summary == {key: value for key, value in case.items()
                           if key not in ('captures', 'input_log', 'callback_transitions')}
        _case(case, report, compiled[home], path.parent)
        for capture in case['captures']:
            captures.append(dict(capture, file=expected_folder+'/'+capture['file']))
    assert homes == set(EXPECTED_HOMES) and MODIFIED_BOAT_HOMES <= homes
    assert report['captures'] == captures
    verify_captures(report['captures'], directory)
    return report
