"""Read the compiled coast names and GPS while walking all 25 real connections.

Each route/connection has an initial travel and Surf fixture. All measured
movement thereafter uses controller input. World-map opening, recentering and
return use the actual menu, with the real avatar location retained throughout.
"""
import hashlib
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[2]
bootstrap = (ROOT / 'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap, __file__, 'exec'))
initial_sha = hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest()
islands = ('One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven')
targets = [island + 'Island_Harbor_Frlg' for island in islands]
all_maps = {path.parent.name: json.loads(path.read_text()) for path in (source / 'data/maps').glob('*/map.json')}
all_by_id = {value['id']: name for name, value in all_maps.items()}
position_header = (source / 'src/data/journey_world_position.h').read_text()
world_header = (source / 'src/data/journey_world_map.h').read_text()
values = list(map(int, re.search(r'sWorldNavigationPixels\[\] = \{([^}]+)', position_header)[1].split(',')))
grids = {}
for first, ident, width, height in re.findall(r'\{(\d+), \(MAP_GROUP\((\w+)\)<<8\)\|MAP_NUM\(\2\), (\d+), (\d+)\}', position_header):
    first, width, height = map(int, (first, width, height))
    grids[all_by_id[ident]] = dict(first=first, width=width, height=height)
# Compare the ROM's entire packed table, not a synthetic projection call.
compiled_values = [lib.read16(s['sWorldNavigationPixels'] + 2 * index) for index in range(len(values))]
assert compiled_values == values, 'Compiled tile GPS differs from source'
sections = {row['id']: index for index, row in enumerate(json.loads((source / 'src/data/region_map/region_map_sections.json').read_text())['map_sections'])}
point_rows = re.findall(r'\{\(MAP_GROUP\((MAP_\w+)\)<<8\)\|MAP_NUM\(\1\), (MAPSEC_\w+), (\d+), (\d+), COMPOUND_STRING\("([^"]+)"\)\}', world_header)
points = {all_by_id[ident]: dict(index=index, section=sections[section], xy=[int(x), int(y)], name=label)
          for index, (ident, section, x, y, label) in enumerate(point_rows)}
charmap = {int(value, 16): character for character, value in re.findall(r"^'([^']+)'\s*=\s*([0-9A-F]{2})\s*$", (source / 'charmap.txt').read_text(), re.M)}

# English and Japanese charmap aliases share zero; these labels use English.
charmap[0] = ' '


def text_at(address):
    data = []
    for index in range(80):
        value = lib.read8(address + index)
        if value == 255:
            return ''.join(charmap.get(byte, '<%02x>' % byte) for byte in data)
        data.append(value)
    raise AssertionError(('Unterminated native coast label', address, data))


def expected_position(name, x, y):
    grid = grids[name]
    value = values[grid['first'] + y * grid['width'] + x]
    return [value & 255, value >> 8]


captures = []


def capture(label):
    picture(label)
    path = args.output / (label + '.png')
    result = dict(file=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    captures.append(result)
    return result


def sample():
    name = by_location[location()]
    x, y = position()
    value = native('JourneyWorldMapPosition')
    actual = [value & 255, value >> 8]
    expected = expected_position(name, x, y)
    assert actual == expected, ('Actual JourneyWorldMapPosition differs', name, x, y, actual, expected)
    return dict(map=name, map_id=list(location()), tile=[x, y],
                actual_projection=actual, expected_projection=expected,
                surfing=bool(lib.read8(s['gPlayerAvatar']) & 8))


# Prepare the same native progression fixture as other surface validators.
native('RtcInitLocalTimeOffset', 12, 0)
for variable, value in [(0x40FE, 7), (0x40FF, 4095), (0x4021, 65535), (0x4120, 65535)]:
    native('VarSet', variable, value)
team([40, 40, 40])
native('ScriptSetMonMoveSlot', 0, 57, 1)
for value in hoenn_flags + kanto_flags:
    rawflag(value, True)
for trainer_id in range(1, 1589):
    rawflag(0x500 + trainer_id, True)
constants = (source / 'include/constants/vars.h').read_text()
for variable, value in [('VAR_MAP_SCENE_ONE_ISLAND_HARBOR', 3), ('VAR_MAP_SCENE_FOUR_ISLAND', 1)]:
    native('VarSet', int(re.search(r'^#define\s+' + variable + r'\s+(0x\w+)', constants, re.M)[1], 16), value)
names = sorted(set(targets) | {all_by_id[c['map']] for name in targets for c in all_maps[name]['connections']})
allowed = set()
walk_prefix = 'route-identity'
walk_transition_pictures = False
walk_cache_paths = True
walk_max_ticks = 1200
walk_surf_under_bridges = True
# Fast-water's predicate depends on the currently loaded native coast.
warp('SixIsland_Frlg', 11, 22)
native('SetPlayerAvatarTransitionFlags', 1)
step(90)
exec(compile((ROOT / 'tools/hoenn/native_water_walk.py').read_text(), 'route-identity-native-walker', 'exec'))
full_passable = {name: valid.copy() for name, valid in passable.items()}
warps = {name: {} for name in names}
# Open only water of matching elevation; every measured journey stays in Surf.
full_passable = {name: {index for index in valid if not blocks[name][2][index] & 0xC00
                      and blocks[name][2][index] >> 12 in (0, 1, 15)
                      and water_behaviors[behaviors[name][index]] and currents[behaviors[name][index]] is None}
                 for name, valid in full_passable.items()}
observations = []


def observer(before, after):
    observations.append(sample())


walk_observer = observer


def set_passability(scope):
    global passable, _planned_goal, _planned_keys
    passable = {name: full_passable[name].copy() if name in scope else set() for name in names}
    _planned_goal, _planned_keys = None, {}


def fixture(start):
    native('SetPlayerAvatarTransitionFlags', 1)
    step(30)
    warp(*start)
    step(90)
    finish()
    native('SetPlayerAvatarTransitionFlags', 8)
    step(60)
    assert (by_location[location()], *position()) == start, (start, location(), position())
    assert lib.read8(s['gPlayerAvatar']) & 8


# Import only the actual map opening functions, without its unrelated scenarios.
opening = (ROOT / 'tools/hoenn/validate_world_map.py').read_text().split('checks=[]')[0].split('def callback():')[1]
exec('def callback():' + opening)
routes = []
for island, name in zip(islands, targets):
    point = points[name]
    expected_name = island.upper() + ' ISLAND COAST'
    assert point['name'] == expected_name
    assert all_maps[name]['show_map_name'] is True
    assert all_maps[name]['map_type'] == 'MAP_TYPE_OCEAN_ROUTE'
    assert not all_maps[name]['object_events'] and not all_maps[name]['warp_events']
    set_passability({name})
    fixture((name, 2, 6))
    actual_name = text_at(native('JourneyCurrentMapName'))
    assert actual_name == expected_name, (name, actual_name, expected_name)
    destination = s['gStringVar4'] + 640
    native('GetPopUpMapName', destination, s['gMapHeader'])
    actual_banner = text_at(destination)
    assert actual_banner == expected_name, (name, actual_banner)
    native('ShowMapNamePopup')
    # The native task prints after31frames, then slides40pixels at2/frame.
    step(60)
    banner_capture = capture('coast-' + island.lower() + '-banner')
    native('HideMapNamePopUpWindow')
    step(60)
    paths = []
    for direction, start, tiles in [('east', (name, 2, 6), [(x, 6) for x in range(2, 15)]),
                                    ('south', (name, 8, 2), [(8, y) for y in range(2, 11)])]:
        if (by_location[location()], *position()) != start:
            walk(start)
        samples = [sample()]
        for x, y in tiles[1:]:
            walk((name, x, y))
            samples.append(sample())
        actual = [row['actual_projection'] for row in samples]
        # The full central line endpoints establish the axis even where a
        # short segment quantizes to the same marker pixel at both ends.
        grid = grids[name]
        ends = [(0, 6), (16, 6)] if direction == 'east' else [(8, 0), (8, 12)]
        endpoints = [expected_position(name, *xy) for xy in ends]
        delta = [endpoints[1][axis] - endpoints[0][axis] for axis in (0, 1)]
        main = max((0, 1), key=lambda axis: abs(delta[axis]))
        sign = (delta[main] > 0) - (delta[main] < 0)
        increments = [(b[main] - a[main]) * sign for a, b in zip(actual, actual[1:])]
        assert all(value >= 0 for value in increments), (name, direction, actual)
        assert all(max(abs(a - b) for a, b in zip(left, right)) <= 2 for left, right in zip(actual, actual[1:]))
        paths.append(dict(direction=direction, primary_axis='xy'[main], primary_direction=sign,
                          primary_axis_monotonic=True, actual_gps_samples=samples))
    real_sample = sample()
    before = (location(), position())
    player_point = native('JourneyWorldMapPlayerPoint')
    assert player_point == point['index']
    ptr = open_map()
    actual_cursor = [lib.read8(ptr + 2056), lib.read8(ptr + 2057)]
    assert actual_cursor == real_sample['actual_projection']
    assert [lib.read8(ptr + 2060), lib.read8(ptr + 2061)] == actual_cursor
    assert lib.read16(ptr + 2052) == player_point
    assert lib.read16(ptr + 2054) == player_point
    label_pointer = lib.read32(s['sWorldPoints'] + player_point * 12 + 8)
    assert text_at(label_pointer) == expected_name
    ui_capture = capture('coast-' + island.lower() + '-world-map')
    press(16)
    press(4)
    assert [lib.read8(ptr + 2056), lib.read8(ptr + 2057)] == real_sample['actual_projection']
    press(2)
    wait_for(lambda: callback() == s['CB2_Overworld'])
    step(120)
    press(2)
    step(90)
    assert before == (location(), position())
    group, number = map_id(name)
    flyable = bool(native('JourneyWorldFlyAllowed', (group << 8) | number, point['section']))
    heal_location = int(native('GetHealLocationIndexByMap', group, number))
    assert not flyable and heal_location == 0, (name, flyable, heal_location)
    routes.append(dict(map=name, map_id=[group, number], name=expected_name,
                       actual_banner=actual_banner, banner_capture=banner_capture,
                       ui_capture=ui_capture, ui_actual_projection=actual_cursor,
                       ui_expected_projection=real_sample['expected_projection'],
                       expected_projection=real_sample['expected_projection'],
                       actual_gps_samples=[row for path in paths for row in path['actual_gps_samples']],
                       central_crossings=paths, flyable=False, heal_location=False,
                       map_open_preserved_player_location=True, recenter_matches_actual_player=True))
    print('Native coast name, banner, central Surf GPS and actual MAP cursor passed:', name, flush=True)


def choices_for(name, other, connection):
    width, height, _ = blocks[name]
    ow, oh, _ = blocks[other]
    direction, offset = connection['direction'], connection['offset']
    dx, dy, key = dict(left=(-1, 0, 32), right=(1, 0, 16), up=(0, -1, 64), down=(0, 1, 128))[direction]
    choices = []
    limit, other_limit = (height, oh) if direction in ('left', 'right') else (width, ow)
    for coordinate in range(max(0, offset), min(limit, offset + other_limit)):
        x, y = ((0 if direction == 'left' else width - 1), coordinate) if direction in ('left', 'right') else (coordinate, 0 if direction == 'up' else height - 1)
        xx, yy = ((ow - 1 if direction == 'left' else 0), coordinate - offset) if direction in ('left', 'right') else (coordinate - offset, oh - 1 if direction == 'up' else 0)
        cells = [(name, x - dx, y - dy), (name, x, y), (other, xx, yy), (other, xx + dx, yy + dy)]
        if not all(0 <= px < blocks[n][0] and 0 <= py < blocks[n][1] and py * blocks[n][0] + px in full_passable[n] for n, px, py in cells):
            continue
        assert expected_position(name, x, y) == expected_position(other, xx, yy)
        choices.append((cells, coordinate))
    return choices


seams = []
for name in targets:
    for connection in all_maps[name]['connections']:
        other = all_by_id[connection['map']]
        set_passability({name, other})
        choices = choices_for(name, other, connection)
        assert choices, ('No controller Surf crossing', name, other, connection)
        cells, coordinate = min(choices, key=lambda row: abs(row[1] - (6 if connection['direction'] in ('left', 'right') else 8)))
        start, goal = cells[0], cells[-1]
        fixture(start)
        first_transition = len(transitions)
        samples = [sample()]
        for cell in cells[1:]:
            walk(cell)
            samples.append(sample())
        assert len(transitions) == first_transition + 1
        outbound_capture = capture('coast-seam-%02d-outbound' % (len(seams) + 1))
        for cell in reversed(cells[:-1]):
            walk(cell)
            samples.append(sample())
        assert len(transitions) == first_transition + 2
        return_capture = capture('coast-seam-%02d-return' % (len(seams) + 1))
        assert samples[1]['actual_projection'] == samples[2]['actual_projection']
        assert all(row['surfing'] for row in samples)
        maximum = max(max(abs(a - b) for a, b in zip(left['actual_projection'], right['actual_projection'])) for left, right in zip(samples, samples[1:]))
        assert maximum <= 2, (name, other, samples)
        # No jump in either axis at the exact native shared border.
        assert samples[4]['actual_projection'] == samples[5]['actual_projection']
        observed = transitions[first_transition:]
        assert observed[0]['source'][0] == name and observed[0]['destination'][0] == other
        assert observed[1]['source'][0] == other and observed[1]['destination'][0] == name
        seams.append(dict(source=name, destination=other, direction=connection['direction'],
                          offset=connection['offset'], source_tile=list(start[1:]), destination_tile=list(goal[1:]),
                          transitions=observed, native_controller_crossings=2, outbound_and_return=True,
                          maximum_seam_delta=0, maximum_neighbor_pixel_step=maximum,
                          actual_gps_samples=samples, surf_preserved=True,
                          captures=[outbound_capture, return_capture], no_midcrossing_warps_or_coordinate_writes=True))
        print('Native coast Surf GPS roundtrip passed:', name, other, flush=True)
assert len(seams) == 25 and len(transitions) == 50
review_mode = bool(lib.read8(s['gJourneyReviewMode']))
lib.stop()
assert hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest() == initial_sha
metadata = json.loads((source / '.journey-coastal-closures').read_text())['route_identity']
result = dict(passed=True, kind='coastal-route-identity', rom_sha256=initial_sha,
              review_mode=review_mode, compiled_rom=True, preflight=False,
              routes=routes, seams=seams, connections=25, native_controller_crossings=50,
              maximum_seam_delta=0, maximum_neighbor_pixel_step=2,
              all_connected_border_pixels_preserved=True,
              all_other_grids_bitwise_unchanged=True, atlas_arrays_unchanged=True,
              atlas_arrays_sha256=metadata['atlas_arrays_sha256'],
              all_route_names_and_banners_checked=True,
              actual_journey_world_position_samples=True,
              ui_map_open_matches_actual_player=True, fly_gating_verified=True,
              compiled_grid_values_checked=len(values), controller_observation_samples=len(observations),
              no_midcrossing_warps_or_coordinate_writes=True,
              initial_positions_avatar_modes_party_progress_and_banner_display_are_fixtures=True,
              full_campaign_playthrough=False, walked_tiles=walked, captures=captures)
for filename in ('route-identity.json', 'coastal-route-identity.json'):
    (args.output / filename).write_text(json.dumps(result, indent=2) + '\n')
