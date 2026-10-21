"""Exercise physical Sevii terminals and native Surf departure/reboarding.

Each primary island trip receives one initial travel fixture. Everything after departure,
including the terminal doors, captain menus, voyages, disembarkation and return,
uses controller input. Party/progress, Repel and saved-game reload are explicit
test fixtures; this is a focused field test, not a complete campaign replay.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--library', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--video', action='store_true')
integrated_options = parser.parse_args()
sys.argv = [sys.argv[0], '--source', str(integrated_options.source), '--library', str(integrated_options.library),
            '--output', str(integrated_options.output)]
bootstrap = (ROOT / 'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap, __file__, 'exec'))
initial_sha = hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest()
captures = {}
native_picture = picture


def picture(name):
    """Bind each capture to the exact native frame written during this run."""
    native_picture(name)
    path = args.output / (name + '.png')
    captures[path.name] = dict(file=path.name,
                               sha256=hashlib.sha256(path.read_bytes()).hexdigest())


integration = json.loads((source / '.journey-sevii-integrated-piers').read_text())
geometry = integration['harbors']
ports = geometry['ports']
assert len(ports) == 7 and {p['island'] for p in ports} == {
    'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven'}
all_maps = {p.parent.name: json.loads(p.read_text())
            for p in (source / 'data/maps').glob('*/map.json')}
all_by_id = {m['id']: n for n, m in all_maps.items()}

# Include the unchanged adjacent ocean headers so their native boundary
# crossings are tested; no path may silently substitute a ferry warp.
names = set()
for port in ports:
    names.update([port['town'], port['interior'], port['old_exterior']])
    names.update(segment['map'] for segment in port['deck_segments'])
    names.update(cell[0] for cell in port['terminal_cells'])
    names.add(port['start'][0])
    names.add(port['outside_arrival'][0])
for name in list(names):
    for connection in all_maps[name].get('connections') or []:
        if connection['direction'] in ['left', 'right', 'up', 'down']:
            names.add(all_by_id[connection['map']])
names.add('JourneyPalletHarbor')
names = sorted(names)
allowed = set()
walk_prefix = 'integrated-piers'
walk_transition_pictures = False
walk_cache_paths = True
walk_max_ticks = 3000
walk_surf_under_bridges = True
native('RtcInitLocalTimeOffset', 12, 0)
native('VarSet', 0x40FE, 7)
native('VarSet', 0x40FF, 4095)
native('VarSet', 0x4021, 65535)
native('VarSet', 0x4120, 65535)
team([40, 40, 40])
native('ScriptSetMonMoveSlot', 0, 57, 1)
for flag_value in hoenn_flags + kanto_flags:
    rawflag(flag_value, True)
for trainer_id in range(1, 1589):
    rawflag(0x500 + trainer_id, True)
constants = (source / 'include/constants/vars.h').read_text()
for variable, value in [('VAR_MAP_SCENE_ONE_ISLAND_HARBOR', 3),
                         ('VAR_MAP_SCENE_FOUR_ISLAND', 1)]:
    native('VarSet', int(re.search(r'^#define\s+' + variable + r'\s+(0x\w+)',
                                 constants, re.M)[1], 16), value)
exec(compile((ROOT / 'tools/hoenn/native_water_walk.py').read_text(),
             'integrated-piers-native-walker', 'exec'))
full_passable = {name: valid.copy() for name, valid in passable.items()}


def player_state():
    obj = s['gObjectEvents'] + lib.read8(s['gPlayerAvatar'] + 5) * 36
    sprite = s['gSprites'] + lib.read8(obj + 35) * 68
    x, y = position()
    return dict(map=by_location[location()], tile=[x, y],
                surfing=bool(lib.read8(s['gPlayerAvatar']) & 8),
                elevation=native('PlayerGetElevation'),
                tile_elevation=native('MapGridGetElevationAt', x + 7, y + 7),
                priority=(lib.read16(sprite + 4) >> 10) & 3,
                sprite_visible=not bool(lib.read16(sprite + 0x3E) & 4),
                object_visible=not bool(lib.read8(obj + 1) & 0x20))


def visible_avatar_pixels():
    """Compare actual scanout with the exact OBJ frame loaded in VRAM.

    An enabled sprite, a good priority value, or a red roof behind the avatar
    cannot satisfy this check. The expected hat, body and feet pixels come
    from the player's current 4bpp graphics and OBJ palette, at hardware OAM
    coordinates, including flips. No visibility or world state is modified.
    """
    obj = s['gObjectEvents'] + lib.read8(s['gPlayerAvatar'] + 5) * 36
    sprite = s['gSprites'] + lib.read8(obj + 35) * 68
    source_attr2 = lib.read16(sprite + 4)
    dimensions = [
        [(8, 8), (16, 16), (32, 32), (64, 64)],
        [(16, 8), (32, 8), (32, 16), (64, 32)],
        [(8, 16), (8, 32), (16, 32), (32, 64)],
    ]
    candidates = []
    for index in range(128):
        address = 0x07000000 + 8 * index
        a0, a1, a2 = (lib.read16(address + 2 * offset) for offset in range(3))
        if (a0 & 0x0300) == 0x0200 or (a2 & 0xF3FF) != (source_attr2 & 0xF3FF):
            continue
        shape, size = a0 >> 14, a1 >> 14
        if shape > 2:
            continue
        width, height = dimensions[shape][size]
        x, y = a1 & 511, a0 & 255
        if x >= 256:
            x -= 512
        if y >= 160:
            y -= 256
        if 88 <= x + width // 2 <= 152 and 32 <= y + height // 2 <= 104:
            candidates.append((index, a0, a1, a2, x, y, width, height))
    assert len(candidates) == 1, ('Player hardware OAM not identified uniquely', candidates, hex(source_attr2))
    index, a0, a1, a2, x, y, width, height = candidates[0]
    assert not a0 & 0x0100 and not a0 & 0x2000, ('Unexpected affine/8bpp avatar', candidates[0])
    image = ctypes.string_at(lib.image(), 240 * 160 * 4)
    tile_base, palette = a2 & 1023, (a2 >> 12) & 15
    stride = width // 8 if lib.read16(0x04000000) & 0x40 else 32
    palette_rgb = {}
    for color_index in range(1, 16):
        packed = lib.read16(0x05000200 + 2 * (16 * palette + color_index)) & 0x7FFF
        palette_rgb[color_index] = tuple(((packed >> shift) & 31) << 3 for shift in (0, 5, 10))
    bg_colors = []
    for color_index in range(256):
        packed = lib.read16(0x05000000 + 2 * color_index) & 0x7FFF
        bg_colors.append(tuple(((packed >> shift) & 31) << 3 for shift in (0, 5, 10)))
    unique_colors = {index for index, rgb in palette_rgb.items()
                     if all(max(abs(a - b) for a, b in zip(rgb, bg)) > 12 for bg in bg_colors)}
    expected = matched = unique_expected = unique_matched = 0
    bands = [dict(expected=0, matched=0) for _ in range(3)]
    opaque_rows = []
    for py in range(height):
        source_y = height - 1 - py if a1 & 0x2000 else py
        for px in range(width):
            source_x = width - 1 - px if a1 & 0x1000 else px
            tile = tile_base + (source_y // 8) * stride + source_x // 8
            byte = lib.read8(0x06010000 + tile * 32 + (source_y % 8) * 4 + (source_x % 8) // 2)
            color = (byte >> (4 * (source_x & 1))) & 15
            if color == 0:
                continue
            assert 0 <= x + px < 240 and 0 <= y + py < 160, ('Avatar frame clipped offscreen', x, y, width, height)
            at = 4 * ((y + py) * 240 + x + px)
            actual = image[at:at + 3]
            # GBA 5-bit to RGB conversion can expand the low three bits;
            # tolerate only that representational difference, not a hue.
            visible = all(abs(a - b) <= 7 for a, b in zip(actual, palette_rgb[color]))
            expected += 1
            matched += visible
            opaque_rows.append((py, visible, x + px, y + py,
                                palette_rgb[color], color in unique_colors))
            if color in unique_colors:
                unique_expected += 1
                unique_matched += visible
    assert expected >= 100, ('Player OBJ frame has insufficient opaque pixels', expected)
    first_row = min(row[0] for row in opaque_rows)
    active_height = max(row[0] for row in opaque_rows) - first_row + 1
    expected_scanout_pixels = []
    for py, visible, screen_x, screen_y, rgb, exclusive in opaque_rows:
        band = min(2, (py - first_row) * 3 // active_height)
        bands[band]['expected'] += 1
        bands[band]['matched'] += visible
        expected_scanout_pixels.append([screen_x, screen_y, *rgb, band, exclusive])
    assert matched >= expected * 0.85, ('Avatar is covered by terrain', matched, expected, candidates[0])
    assert all(band['expected'] >= 8 and band['matched'] >= band['expected'] * 0.75 for band in bands), (
        'Hat, body or feet hidden by terrain', bands, candidates[0])
    if unique_expected >= 8:
        assert unique_matched >= unique_expected * 0.85, ('Player-only palette pixels occluded', unique_matched, unique_expected)
    return dict(hardware_oam_index=index, screen_rectangle=[x, y, width, height],
                expected_opaque_pixels=expected, matching_scanout_pixels=matched,
                head_body_feet_bands=bands,
                exclusive_obj_palette_pixels=unique_expected,
                exclusive_obj_palette_pixels_visible=unique_matched,
                expected_scanout_pixels=expected_scanout_pixels,
                exact_current_vram_frame_compared=True,
                background_color_coincidence_not_used=True)


def assert_foot(capture_label=None):
    value = player_state()
    assert not value['surfing'] and value['elevation'] == 3, value
    assert value['sprite_visible'] and value['object_visible'], value
    # The new low boardwalk is ordinary dry land. Its foreground planks must
    # be below the player's feet, rather than merely exposing the sprite flag.
    expected = 1 if value['tile_elevation'] == 15 else 2
    assert value['priority'] == expected, value
    value['native_avatar_pixels'] = visible_avatar_pixels()
    if capture_label is not None:
        picture(capture_label)
        value['capture_file'] = capture_label + '.png'
    return value


def assert_surf():
    value = player_state()
    assert value['surfing'] and value['elevation'] == 1, value
    assert value['priority'] == 2 and value['sprite_visible'] and value['object_visible'], value
    return value


def set_passability(allowed_maps=None, water_only=False, dry_only=False):
    global passable, _planned_goal, _planned_keys
    assert not (water_only and dry_only)
    passable = {name: ({i for i in valid
                        if water_behaviors[behaviors[name][i]]
                        and not blocks[name][2][i] & 0xC00}
                       if water_only else {i for i in valid if not water_behaviors[behaviors[name][i]]}
                       if dry_only else valid.copy())
                if allowed_maps is None or name in allowed_maps else set()
                for name, valid in full_passable.items()}
    _planned_goal, _planned_keys = None, {}


def save_continue(label, surfing):
    # Let the native ferry/Surf tasks finish with controls released before
    # taking the battery snapshot. This is elapsed gameplay, not a state fix.
    blocking_tasks = [name for name in s if name.startswith('Task_Seagallop_')
                      or name in {'Task_SurfFieldEffect', 'Task_FieldMoveShowMonOutdoors',
                                  'Task_FieldMoveShowMonIndoors'}]
    stable_frames = 0
    previous = (location(), position())
    for _ in range(750):
        step(4)
        current = (location(), position())
        if idle() and current == previous and not any(task(name) for name in blocking_tasks):
            stable_frames += 4
        else:
            stable_frames = 0
        previous = current
        if stable_frames >= 60:
            break
    else:
        picture(label + '-unsettled-before-save')
        raise AssertionError(('Travel did not settle before saving', player_state(),
                              [name for name in blocking_tasks if task(name)]))
    before = player_state()
    assert before['surfing'] == surfing
    assert native('TrySavingData', 0, max_frames=6000) == 1
    assert native('LoadGameSave', 0, max_frames=6000) == 1
    # Invoke the real Continue callback on the game's own reloaded battery.
    # No position, height or avatar mode is repaired after this operation.
    lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
    step(1500)
    finish()
    after = assert_surf() if surfing else assert_foot()
    assert (before['map'], before['tile'], before['surfing'], before['elevation']) == (
        after['map'], after['tile'], after['surfing'], after['elevation']), (before, after)
    picture(label)
    return dict(before=before, after=after, native_save_continue=True,
                controls_settled_before_save=True, neutral_frames_before_save=stable_frames)


def await_port_menu():
    for _ in range(500):
        if task('Task_HandleMultichoiceInput'):
            step(20)
            return
        press(1)
    raise AssertionError(('Port menu did not open', player_state()))


getter = s['Menu_GetCursorPos']
instruction = lib.read16(getter)
assert instruction & 0xF800 == 0x4800
menu_cursor = lib.read32(((getter + 4) & ~3) + (instruction & 255) * 4) + 2


def choose(index):
    await_port_menu()
    for _ in range(12):
        current = lib.read8(menu_cursor)
        if current == index:
            press(1)
            return
        press(64 if current > index else 128)
    raise AssertionError(('Could not choose port destination', index))


def talk_captain():
    step(4, 64)
    step(20)
    press(1)
    await_port_menu()


def voyage(name, arrival):
    animation_frames = 0
    for _ in range(1200):
        if task('Task_Seagallop_1'):
            animation_frames += 8
            step(8)
        elif location() == map_id(name) and idle():
            break
        else:
            press(1)
    assert animation_frames >= 40, ('Missing ferry animation', name, animation_frames)
    assert location() == map_id(name) and position() == tuple(arrival), (
        name, location(), position(), arrival)
    assert_foot()
    return dict(destination=name, arrival=list(arrival), native_animation_frames=animation_frames)


encoder = None
video_frames = 0
video_native_frames = 0
video_capture_pending = 0
video_path = args.output / 'sevii-integrated-piers.mp4'
base_step = step


def start_video():
    global encoder, step, encoder_log, video_frames, video_native_frames, video_capture_pending
    if not integrated_options.video:
        return
    encoder_log = (args.output / 'integrated-video-ffmpeg.log').open('w')
    encoder = subprocess.Popen([
        'ffmpeg', '-y', '-hide_banner', '-loglevel', 'warning', '-filter_threads', '1',
        '-f', 'rawvideo', '-pixel_format', 'rgba', '-video_size', '240x160',
        '-framerate', '30', '-i', 'pipe:0', '-an', '-vf', 'scale=960:640:flags=neighbor',
        '-c:v', 'libx264', '-preset', 'fast', '-threads', '1', '-crf', '18',
        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(video_path)],
        stdin=subprocess.PIPE, stderr=encoder_log)

    def recording_step(count, keys=0):
        global video_frames, video_native_frames, video_capture_pending
        while count:
            chunk = min(count, 2 - video_capture_pending)
            base_step(chunk, keys)
            count -= chunk
            video_native_frames += chunk
            video_capture_pending += chunk
            if video_capture_pending == 2:
                encoder.stdin.write(ctypes.string_at(lib.image(), 240 * 160 * 4))
                video_frames += 1
                video_capture_pending = 0

    step = recording_step


def finish_video():
    global encoder, step
    if encoder is None:
        return
    encoder.stdin.close()
    assert encoder.wait() == 0
    encoder_log.close()
    encoder = None
    step = base_step


visited = []


def walk_observer(before, after):
    visited.append(dict(source=list(before), destination=list(after)))


checks = []
try:
    for port in ports:
        island = port['island']
        island_index = ['One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven'].index(island)
        tag = island.lower()
        town, inside = port['town'], port['interior']
        start = tuple(port['start'])
        outside = tuple(port['outside_arrival'])
        captain_arrival = tuple(port['arrival'])
        set_passability(dry_only=True)
        warp(*start)
        native('SetPlayerAvatarTransitionFlags', 1)
        step(90)
        assert_foot()
        first_trip = len(transitions)
        first_samples = len(visited)
        unintended_surf_before = len(surf_prompts)
        walk(outside)
        assert_foot()
        picture(tag + '-integrated-terminal-front')
        # There is no town-to-detached-harbor warp on this trip: all outside
        # map changes must be real adjacent map connections.
        exterior_trip = transitions[first_trip:]
        for crossed in exterior_trip:
            origin, destination = crossed['source'][0], crossed['destination'][0]
            assert any(c['map'] == maps[destination]['id']
                       for c in maps[origin].get('connections') or []), crossed
        walk((inside, *captain_arrival))
        assert_foot()
        picture(tag + '-integrated-terminal-interior')
        assert len([o for o in maps[inside]['object_events']
                    if o['script'] == 'Journey_FerryPort' + str(port['pid'])]) == 1
        talk_captain()
        picture(tag + '-indoor-captain-network-menu')
        choose(0)
        choose(2)
        voyages = [voyage('JourneyPalletHarbor', (16, 13))]
        talk_captain()
        choose(2)
        choose(island_index)
        voyages.append(voyage(inside, captain_arrival))
        walk(outside)
        assert_foot()
        picture(tag + '-door-return-to-integrated-pier')
        wall_map, door_x, door_y = port['door']
        wall_probes = []
        for delta in (-2, 2):
            front = (wall_map, door_x + delta, door_y + 1)
            wall_x, wall_y = door_x + delta, door_y
            if front[2] == blocks[wall_map][1]:
                # Seven Island's apron is physically on the connected
                # Sevault Entrance header, directly beneath the town facade.
                front = connection_step(wall_map, door_x + delta, door_y, 128)
                assert front is not None, (island, 'Facade has no connected apron')
            walk(front)
            assert native('MapGridGetCollisionAt', front[1] + 7, front[2] - 1 + 7), (island, 'Incomplete terminal facade')
            before = (location(), position())
            step(90, 64)
            step(45)
            assert (location(), position()) == before, (island, 'Walked through terminal facade', before, player_state())
            assert_foot()
            wall_probes.append(dict(front=list(front), wall=[wall_map, wall_x, wall_y], blocked=True))
        # Exact dry/wet samples are selected by the authored layout so a
        # disconnected alternate beach cannot satisfy this regression test.
        dry = tuple(port['boarding']['dry'])
        water = tuple(port['boarding']['water'])
        direction = port['boarding']['outward_key']
        assert dry[0] == water[0]
        assert tuple(water[i] - dry[i] for i in (1, 2)) == next(
            (dx, dy) for dx, dy, key in keys if key == direction)
        walk(dry)
        pier_state = assert_foot(tag + '-pier-departure-avatar')
        boat_checks = []
        for boat in port['boats']:
            assert boat['map'] == dry[0], (island, 'Boat placed on disconnected header', boat)
            buffer_width = lib.read32(s['gBackupMapLayout'])
            buffer = lib.read32(s['gBackupMapLayout'] + 8)
            boat_width = blocks[boat['map']][0]
            hull_cells = []
            for hx, hy in boat['hull']:
                expected_tile = blocks[boat['map']][2][hy * boat_width + hx]
                loaded_tile = lib.read16(buffer + 2 * ((hy + 7) * buffer_width + hx + 7))
                assert loaded_tile == expected_tile, (island, 'Boat hull collision not loaded', hx, hy)
                assert expected_tile >> 12 == 1 and expected_tile & 0xC00, (island, 'Boat hull is not blocked water', hx, hy, expected_tile)
                assert water_behaviors[behaviors[boat['map']][hy * boat_width + hx]]
                hull_cells.append([hx, hy, loaded_tile])
            assert hull_cells
            boat_checks.append(dict(map=boat['map'], graphics=boat['event']['graphics_id'],
                                    native_hull_cells=hull_cells, blocked_over_water=True))
        assert len(boat_checks) == (0 if island == 'Six' else 2)
        assert bool(port['boats_omitted_for_clearance']) == (island == 'Six')
        saved_pier = save_continue(tag + '-pier-save-continue', False)
        assert len(surf_prompts) == unintended_surf_before, (island, 'Dry terminal trip used Surf')
        if island == 'Six':
            start_video()
        before = (location(), position())
        step(90, direction)
        step(45)
        assert (location(), position()) == before, (island, 'Foot walked into water', before, player_state())
        assert_foot()
        assert native('IsPlayerFacingSurfableFishableWater')
        prompt_before = len(surf_prompts)
        set_passability()
        walk(water)
        water_state = assert_surf()
        assert len(surf_prompts) > prompt_before, (island, 'No native Surf prompt')
        picture(tag + '-surf-departure-from-pier')
        walk(dry)
        step(60)
        reboarded = assert_foot(tag + '-surf-reboarded-same-pier')
        set_passability(dry_only=True)
        walk(outside)
        assert_foot()
        if island == 'Six':
            finish_video()
        set_passability()
        walk(water)
        assert_surf()
        saved_water = save_continue(tag + '-surf-save-continue', True)
        walk(dry)
        step(60)
        assert_foot()
        set_passability(dry_only=True)
        walk(start)
        assert_foot()
        assert (by_location[location()], *position()) == start
        picture(tag + '-surf-return-to-town')
        checks.append(dict(
            island=island, town=town, terminal=inside, start=list(start),
            outside_arrival=list(outside), exterior_transitions=exterior_trip,
            controller_terminal_roundtrip=True, controller_door_roundtrip=True,
            town_terminal_trip_walked_entirely_on_dry_land=True,
            terminal_physically_connected_to_town=True,
            no_town_to_detached_harbor_warp=True,
            indoor_captain_interacted=True, network_arrival_inside_terminal=True,
            network_return_to_original_terminal=True, voyages=voyages,
            native_surf_prompt=True, native_disembark=True,
            surf_departure_and_reboard=True, reboard_foot_elevation3=True,
            surf_elevation1=True, sprite_visible_above_pier=True,
            dry_walking_cannot_enter_water=True, save_continue_on_pier=True,
            foot_blocks_walls=True, wall_probes=wall_probes,
            save_continue_on_water=True, saved_pier=saved_pier, saved_water=saved_water,
            boats=boat_checks, boat_hulls_blocked_over_water=True,
            boats_omitted_for_clearance=bool(port['boats_omitted_for_clearance']),
            departure_pier_state=pier_state, departure_water_state=water_state,
            reboarded_state=reboarded, movement_samples=len(visited)-first_samples,
            no_midtrip_coordinate_or_elevation_writes=True))
        print('Integrated town terminal and native Surf reboarding passed:', island, flush=True)
finally:
    finish_video()

# Filled by the same run after the seven primary trips: old detached port
# footprints and all affected ocean edges are checked against loaded native
# metatiles and traversed with no ferry route in the ocean-only path planner.
seam_checks = []
clearance_checks = []
old_ports = {p['island']: p for p in json.loads(
    (source / '.journey-sevii-harbors').read_text())['ports']}
old_piers = {p['island']: p for p in json.loads(
    (source / '.journey-dewford-coast-safety').read_text())['piers']['low_piers']}


def water_tile(name, x, y):
    width, height, tiles = blocks[name]
    return (0 <= x < width and 0 <= y < height
            and y * width + x in passable[name]
            and tiles[y * width + x] >> 12 == 1
            and water_behaviors[behaviors[name][y * width + x]])


for port in ports:
    island = port['island']
    old = old_ports[island]
    name = port['old_exterior']
    assert old['exterior'] == name
    width, height, tiles = blocks[name]
    set_passability(water_only=True)
    candidates = [(name, x, y) for y in range(1, height - 1)
                  for x in range(1, width - 1) if water_tile(name, x, y)]
    assert candidates, (island, 'Old port left no open sea')
    departure = candidates[len(candidates) // 2]
    warp(*departure)
    native('SetPlayerAvatarTransitionFlags', 8)
    step(90)
    assert_surf()
    # Independently reconstruct the old structures from the historical
    # placement manifests, rather than trusting the new helper's clear list.
    tx, ty, tw, th = old['terminal']
    old_cells = {(x, y) for y in range(ty, ty + th) for x in range(tx, tx + tw)}
    for left, top, right, bottom in old_piers[island]['rectangles']:
        old_cells.update((x, y) for y in range(top, bottom + 1)
                         for x in range(left, right + 1))
    for hull in old['outside_hulls']:
        old_cells.update(map(tuple, hull))
    old_cells.add((8, 2))
    buffer_width = lib.read32(s['gBackupMapLayout'])
    buffer = lib.read32(s['gBackupMapLayout'] + 8)
    loaded_checks = []
    for x, y in sorted(old_cells):
        assert water_tile(name, x, y), (island, 'Detached port structure remains', [x, y], hex(tiles[y * width + x]))
        assert not tiles[y * width + x] & 0xC00, (island, 'Detached boat/structure collision remains', [x, y])
        loaded = lib.read16(buffer + 2 * ((y + 7) * buffer_width + x + 7))
        assert loaded == tiles[y * width + x], (island, 'Native old-port buffer differs from cleared sea', x, y, hex(loaded))
        loaded_checks.append([x, y, loaded])
    assert not maps[name]['object_events'], (island, 'Object remains at removed detached terminal')
    picture(island.lower() + '-former-detached-port-open-sea')
    clearance_checks.append(dict(island=island, map=name,
                                 original_terminal_deck_and_boat_cells_checked=len(loaded_checks),
                                 native_loaded_water_cells=loaded_checks,
                                 former_terminal_and_boats_removed=True,
                                 no_invisible_structure_collision=True))
    next(c for c in checks if c['island'] == island)['previous_separate_port_cleared'] = True
    for connection in old_piers[island]['surface_connections']:
        assert connection in (maps[name].get('connections') or []), (
            island, 'Existing surface connection was removed', connection)
        destination = all_by_id[connection['map']]
        dest_width, dest_height, _ = blocks[destination]
        direction, offset = connection['direction'], connection['offset']
        key = dict(left=32, right=16, up=64, down=128)[direction]
        reverse = {16: 32, 32: 16, 64: 128, 128: 64}[key]
        options = []
        for span in range(height if direction in ['left', 'right'] else width):
            if direction in ['left', 'right']:
                x, y = (0 if direction == 'left' else width - 1), span
                incoming_x, incoming_y = (dest_width - 1 if direction == 'left' else 0), span - offset
                dx, dy = (-1 if direction == 'left' else 1), 0
            else:
                x, y = span, (0 if direction == 'up' else height - 1)
                incoming_x, incoming_y = span - offset, (dest_height - 1 if direction == 'up' else 0)
                dx, dy = 0, (-1 if direction == 'up' else 1)
            start = (name, x - dx, y - dy)
            end = (destination, incoming_x + dx, incoming_y + dy)
            if not all([water_tile(*start), water_tile(name, x, y),
                        water_tile(destination, incoming_x, incoming_y), water_tile(*end)]):
                continue
            if connection_step(name, x, y, key) != (destination, incoming_x, incoming_y):
                continue
            if connection_step(destination, incoming_x, incoming_y, reverse) != (name, x, y):
                continue
            if any(currents[behaviors[n][yy * blocks[n][0] + xx]] is not None
                   for n, xx, yy in [start, end, (name, x, y),
                                     (destination, incoming_x, incoming_y)]):
                continue
            options.append((start, end))
        assert options, (island, 'No reciprocal Surf opening at preserved connection', connection)
        start, end = options[len(options) // 2]
        warp(*start)
        native('SetPlayerAvatarTransitionFlags', 8)
        step(90)
        first = len(transitions)
        walk(end)
        assert_surf()
        walk(start)
        assert_surf()
        observed = transitions[first:]
        assert len(observed) == 2, (island, 'Indirect path replaced physical Surf connection', connection, observed)
        assert observed[0]['source'][0] == name and observed[0]['destination'][0] == destination
        assert observed[1]['source'][0] == destination and observed[1]['destination'][0] == name
        seam_checks.append(dict(island=island, map=name, destination=destination,
                                direction=direction, offset=offset,
                                source=list(start), target=list(end),
                                outbound_and_return=True, surf_preserved=True,
                                native_controller_crossings=2, transitions=observed,
                                no_midcrossing_warps_or_coordinate_writes=True))
    print('Former detached terminal cleared and Surf seams preserved:', island, flush=True)
    next(c for c in checks if c['island'] == island)['affected_seams'] = [
        seam for seam in seam_checks if seam['island'] == island]

assert len(clearance_checks) == 7
assert len(seam_checks) == sum(len(p['surface_connections']) for p in old_piers.values())
assert len(seam_checks) == 25

assert len(checks) == 7
assert hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest() == initial_sha
review = bool(lib.read8(s['gJourneyReviewMode']))
lib.stop()
result = dict(passed=True, rom_sha256=initial_sha, review_mode=review,
              ports=checks, affected_seams=seam_checks,
              captures=list(captures.values()),
              old_port_clearance=clearance_checks,
              native_controller_terminal_roundtrip=True,
              native_surf_departure_and_reboard=True,
              native_avatar_pixels_checked=True,
              exact_current_vram_frame_compared=True,
              sprite_flags_alone_not_sufficient=True,
              no_midtrip_coordinate_or_elevation_writes=True,
              placements_progress_party_are_fixtures=True,
              full_campaign_playthrough=False)
if integrated_options.video:
    result.update(video=video_path.name,
                  video_sha256=hashlib.sha256(video_path.read_bytes()).hexdigest(),
                  video_frames=video_frames, video_native_frames=video_native_frames,
                  continuous_controller_video=True)
(args.output / 'integrated-piers.json').write_text(json.dumps(result, indent=2) + '\n')
