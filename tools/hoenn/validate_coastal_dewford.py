"""Walk the formerly separated Dewford beach and terminal floor in native mGBA.

The baseline supplies the actual 29 former level-four/level-three boundaries.
Only the initial placement, party, badges and defeated trainers are fixtures.
All subsequent travel, stairs, Surf, doors and vendor interactions use controls.
"""
import argparse
from collections import deque
import ctypes
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

from dewford_coast_view import MAPS

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--library', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--baseline', type=Path, default=ROOT / '.local/sevii-integrated-src')
options = parser.parse_args()
baseline = options.baseline.resolve()
initial_sha = hashlib.sha256((options.source / 'pokeemerald.gba').read_bytes()).hexdigest()
baseline_sha = hashlib.sha256((baseline / 'pokeemerald.gba').read_bytes()).hexdigest()
assert baseline_sha == '08fc8a08b95e8e3a923e3342b4f1a31bbaccd1582cbc67ea010021191c43fd6e'
assert initial_sha != baseline_sha, 'Layer 162 evidence cannot validate the new repair'
sys.argv = [sys.argv[0], '--source', str(options.source), '--library', str(options.library),
            '--output', str(options.output)]
exec(compile((ROOT / 'tools/hoenn/validate_sootopolis_harbor.py').read_text().split(
    '\n# Disable Sootopolis')[0], __file__, 'exec'))


def world_grid(directory):
    ls = {row['id']: row for row in json.loads((directory / 'data/layouts/layouts.json').read_text())['layouts']}
    world, warps = {}, set()
    for name, (ox, oy) in MAPS.items():
        mapping = json.loads((directory / f'data/maps/{name}/map.json').read_text())
        layout = ls[mapping['layout']]
        raw = (directory / layout['blockdata_filepath']).read_bytes()
        values = struct.unpack('<' + 'H' * (len(raw) // 2), raw)
        for i, block in enumerate(values):
            x, y = i % layout['width'], i // layout['width']
            world[x + ox, y + oy] = dict(map=name, tile=[x, y], block=block)
        warps.update((row['x'] + ox, row['y'] + oy) for row in mapping['warp_events'])
    return world, warps


old_world, _ = world_grid(baseline)
new_world, warp_points = world_grid(source)
changed, complete_rock_changes = [], []
approved_rocks = {}
audit_marker = source / '.journey-generated-world-audit'
if audit_marker.exists():
    for rock in json.loads(audit_marker.read_text())['marine']['rocks']:
        for cell, before, after in zip(rock['cells'], rock['before'], rock['after']):
            assert before & ~0x3FF == after & ~0x3FF
            if before != after:
                approved_rocks[tuple(cell)] = (before, after)
for point, row in old_world.items():
    after = new_world[point]['block']
    if after != row['block']:
        cell = (row['map'], *row['tile'])
        if approved_rocks.get(cell) == (row['block'], after):
            complete_rock_changes.append(dict(map=row['map'], tile=row['tile'],
                                             before=row['block'], after=after))
            continue
        assert row['block'] >> 12 == 4 and after == (row['block'] & 0xFFF) | 0x3000
        changed.append(dict(map=row['map'], tile=row['tile'], before=row['block'], after=after))
assert len(changed) == 76
former_edges = []
for point, row in old_world.items():
    if row['block'] >> 12 != 4 or row['block'] & 0xC00:
        continue
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        neighbor = point[0] + dx, point[1] + dy
        other = old_world.get(neighbor)
        if (other is not None and other['block'] >> 12 == 3 and not other['block'] & 0xC00
                and new_world[point]['block'] >> 12 == new_world[neighbor]['block'] >> 12 == 3):
            former_edges.append((point, neighbor))
assert len(former_edges) == 29
foot_nodes = {point for point, row in new_world.items()
              if not row['block'] & 0xC00 and row['block'] >> 12 in [3, 4]
              and point not in warp_points}
foot_nodes |= {(x, y) for x in [5, 6] for y in range(4, 15)}
# The route planner must respect the bridge's genuine stair approaches. A
# collision-free sand tile beside a level-four stair is not a lateral exit.
stair_edges = {frozenset((ground, stair)) for ground, stair in [
    ((4, 3), (5, 3)), ((7, 3), (6, 3)),
    ((5, 2), (5, 3)), ((6, 2), (6, 3)),
    ((5, 16), (5, 15)), ((6, 16), (6, 15))]}


def foot_edge(origin, target):
    levels = [new_world[point]['block'] >> 12 for point in (origin, target)]
    levels = [4 if level == 15 else level for level in levels]
    return levels[0] == levels[1] or frozenset((origin, target)) in stair_edges


by_location = {map_id(name): name for name in MAPS}
samples, captures, save_checks = [], [], []

# The comparator reads this emulator's actual OBJ frame, hardware OAM, OBJ
# palette and scanout. Reusing its implementation does not reuse any old RAM,
# capture or result. Enabled sprite flags alone cannot prove visible feet.
visibility = (ROOT / 'tools/hoenn/validate_integrated_piers.py').read_text()
visibility = visibility[visibility.index('def visible_avatar_pixels():'):
                        visibility.index('def assert_foot(')]
exec(compile(visibility, 'current-dewford-native-avatar-pixels', 'exec'), globals())


def current_world():
    name = by_location[location()]
    ox, oy = MAPS[name]
    x, y = position()
    return x + ox, y + oy


def observe(label, elevation, surfing=False, capture=False, ui=False):
    x, y = position()
    obj = s['gObjectEvents'] + lib.read8(s['gPlayerAvatar'] + 5) * 36
    sprite = s['gSprites'] + lib.read8(obj + 35) * 68
    # Read the exact fields used by PlayerGetElevation/MapGridGetMetatileIdAt.
    # An injected field-script getter cannot execute in the party-menu CB2,
    # and must not replace the vendor's real waiting script context.
    grid = s['gBackupMapLayout']
    block = lib.read16(lib.read32(grid + 8) + 2 * ((y + 7) * lib.read32(grid) + x + 7))
    row = dict(label=label, map=by_location.get(location(), 'JourneyDewfordHarbor'),
               tile=[x, y], elevation=lib.read8(obj + 11) >> 4,
               surf=bool(lib.read8(s['gPlayerAvatar']) & 8),
               priority=(lib.read16(sprite + 4) >> 10) & 3,
               sprite_visible=not bool(lib.read16(sprite + 0x3E) & 4),
               object_visible=not bool(lib.read8(obj + 1) & 0x20),
               metatile=block & 0x3FF)
    assert row['elevation'] == elevation and row['surf'] is surfing, row
    if ui:
        menu_task = {'competitive-vendor-menu': 'Task_HandleScrollingMultichoiceInput',
                     'hyper-training-vendor-menu': 'Task_HandleChooseMonInput'}[label]
        assert task(menu_task), row
        row.update(capture_mode='native-vendor-ui', native_menu_task=menu_task,
                   native_menu_task_active=True,
                   native_main_callback=lib.read32(s['gMain'] + 4) & ~1,
                   field_sprite_applicable=False)
        callback = ('CB2_UpdatePartyMenu' if label == 'hyper-training-vendor-menu'
                    else 'CB2_Overworld')
        row['native_main_callback_symbol'] = callback
        row['expected_main_callback'] = s[callback]
        assert row['native_main_callback'] == s[callback], row
    else:
        assert row['priority'] == (1 if elevation == 4 else 2), row
        assert row['sprite_visible'] and row['object_visible'], row
    samples.append(row)
    if capture:
        file = 'dewford-movement-' + label
        if not surfing and not ui:
            row['native_avatar_pixels'] = visible_avatar_pixels()
        picture(file)
        row['capture_file'] = file + '.png'
        captures.append(dict(file=file + '.png', sha256=hashlib.sha256(
            (args.output / (file + '.png')).read_bytes()).hexdigest()))
    return row


def one_step(destination):
    origin = current_world()
    dx, dy = destination[0] - origin[0], destination[1] - origin[1]
    key = {(1, 0): 16, (-1, 0): 32, (0, -1): 64, (0, 1): 128}[dx, dy]
    for _ in range(140):
        step(1, key)
        if current_world() == destination:
            step(30)
            assert idle()
            return
    picture('dewford-movement-blocked')
    raise AssertionError(('Dry movement blocked', origin, destination, current_world()))


def foot_walk(goal):
    origin = current_world()
    queue, previous = deque([origin]), {origin: None}
    while queue and goal not in previous:
        x, y = queue.popleft()
        for target in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
            if (target in foot_nodes and target not in previous
                    and foot_edge((x, y), target)):
                previous[target] = (x, y)
                queue.append(target)
    assert goal in previous, ('Disconnected dry target', origin, goal)
    path, point = [], goal
    while point != origin:
        path.append(point)
        point = previous[point]
    for point in reversed(path):
        one_step(point)


def finish(limit=500):
    for _ in range(limit):
        if idle():
            step(45)
            return
        press(1)
    raise AssertionError(('Dialogue did not finish', location(), position()))


def continue_here(label, elevation, surfing=False):
    """Reload the game's own battery through its real Continue callback."""
    before_map, before_tile = location(), position()
    assert idle()
    step(60)
    assert native('TrySavingData', 0, max_frames=6000) == 1
    assert native('LoadGameSave', 0, max_frames=6000) == 1
    lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
    step(1500)
    assert idle() and location() == before_map and position() == before_tile
    row = observe(label, elevation, surfing, capture=True)
    save_checks.append(dict(label=label, state=row, same_map_and_position=True,
                            native_battery_reload_and_continue=True,
                            no_coordinate_or_elevation_repair=True))


native('RtcInitLocalTimeOffset', 12, 0)
assert native('ScriptGiveMon', 260, 50, 0) == 0
native('ScriptSetMonMoveSlot', 0, 57, 0)
for flag in [lib.read16(s['gBadgeFlags'] + i * 2) for i in range(8)] + list(range(0x1AB0, 0x1AB8)):
    native('FlagSet', flag)
native('VarSet', 0x40FE, 7)
trainer_ids = {}
for path in ['include/constants/opponents.h', 'include/constants/opponents_frlg.h']:
    trainer_ids.update({name: int(number) for name, number in re.findall(
        r'^#define\s+(TRAINER_\w+)\s+(\d+)\b', (source / path).read_text(), re.M)})
for name in ['Route106', 'Route107', 'Route108']:
    scripts = (source / f'data/maps/{name}/scripts.inc').read_text()
    for trainer in set(re.findall(r'trainerbattle_[a-z_]+\s+(TRAINER_\w+)', scripts)):
        native('SetTrainerFlag', trainer_ids[trainer])
warp('Route107', 2, 5)
native('SetPlayerAvatarTransitionFlags', 1)
step(120)
observe('initial-unified-sand', 3, capture=True)
continue_here('unified-sand-save-continue', 3)
compiled_stair_caps = []
for mid, quadrant in [(0x2DF, 7), (0x2E1, 5)]:
    word = lib.read16(s['gMetatiles_JourneyDewfordHarbor'] + (mid - 512) * 16 + quadrant * 2)
    assert word == 0x73FB, ('Missing complete native stair cap', hex(mid), hex(word))
    compiled_stair_caps.append(dict(metatile=mid, quadrant=quadrant, word=word))
boundary_checks = []
for index, (interior, shore) in enumerate(former_edges):
    foot_walk(interior)
    before = observe(f'boundary-{index:02}-interior', 3)
    one_step(shore)
    outside = observe(f'boundary-{index:02}-shore', 3, capture=True)
    one_step(interior)
    returned = observe(f'boundary-{index:02}-returned', 3)
    boundary_checks.append(dict(interior=before, shore=outside, returned=returned,
                                native_controller_roundtrip=True))

# Preserve every former dry approach to both northern stair lanes.
stair_checks = []
for ground, stair in [((4, 3), (5, 3)), ((7, 3), (6, 3)),
                      ((5, 16), (5, 15)), ((6, 16), (6, 15))]:
    foot_walk(ground)
    before = observe('stair-dry-approach', 3)
    one_step(stair)
    upper = observe('stair-upper-' + str(len(stair_checks)), 4, capture=True)
    one_step(ground)
    lower = observe('stair-dry-return', 3)
    stair_checks.append(dict(before=before, upper=upper, returned=lower,
                              native_controller_roundtrip=True))
foot_walk((6, 3))
step(90, 64)
step(45)
assert current_world() == (6, 3), 'The wall beside the terminal door became walkable'
terminal_wall = observe('terminal-wall-remains-blocked', 4, capture=True)
foot_walk((5, 3))
change_map(64, 'JourneyDewfordHarbor')
# The unchanged terminal doorway is the native elevation-zero warp threshold
# (0x0206), not the level-three floor one tile inside it.
assert native('MapGridGetElevationAt', 11 + 7, 14 + 7) == 0
observe('terminal-controller-entry', 0, capture=True)
walk_to(11, 13)
observe('terminal-controller-inner-floor', 3, capture=True)
change_map(128, 'Route107')
assert position() == (5, 3)
observe('terminal-controller-return', 4, capture=True)
rails = []
for y in range(4, 15):
    for x, key in [(5, 32), (6, 16)]:
        foot_walk((x, y))
        before = current_world()
        step(90, key)
        step(45)
        assert current_world() == before
        rails.append(observe(f'rail-{x}-{y}', 4))
foot_walk((5, 9))
observe('upper-bridge-visible', 4, capture=True)
continue_here('upper-bridge-save-continue', 4)
foot_walk((7, 16))
step(90, 16)
step(45)
assert position() == (7, 16) and not lib.read8(s['gPlayerAvatar']) & 8
assert native('IsPlayerFacingSurfableFishableWater')
press(1)
finish()
step(90)
walk_to(8, 16)
observe('native-surf-departure', 1, True, capture=True)
continue_here('lower-surf-save-continue', 1, True)
allowed = set()
names = list(MAPS)
walk_prefix, walk_max_ticks = 'dewford-movement', 2000
walk_transition_pictures, walk_surf_under_bridges = False, True
exec(compile((ROOT / 'tools/hoenn/native_water_walk.py').read_text(), __file__, 'exec'))
for name, (_, _, tiles) in blocks.items():
    passable[name] = {index for index in passable[name]
                      if tiles[index] >> 12 in [1, 15]
                      and water_behaviors[behaviors[name][index]]}
walk(('Route107', 3, 8))
walk(('Route107', 8, 8))
observe('surf-under-both-bridge-rails', 1, True, capture=True)
walk(('Route107', 3, 7))
walk_to(3, 6)
step(90)
observe('native-disembark-northern-island', 3, capture=True)
foot_walk((2, 5))
observe('shore-to-terminal-interior-after-disembark', 3, capture=True)


def wait_task(name):
    for _ in range(500):
        if task(name):
            step(30)
            return
        press(1)
    raise AssertionError(('Vendor interaction absent', name))


def leave_shop():
    for _ in range(30):
        if idle():
            return
        press(2)
        step(30)
        if idle():
            return
        if not any(task(name) for name in ['Task_BuyMenu', 'Task_ShopMenu', 'Task_HandleScrollingMultichoiceInput']):
            press(1)
    raise AssertionError('Vendor did not release controls')


foot_walk((2, 16))
observe('competitive-vendor-approach', 3, capture=True)
step(4, 64)
step(20)
press(1)
wait_task('Task_HandleScrollingMultichoiceInput')
observe('competitive-vendor-menu', 3, capture=True, ui=True)
leave_shop()
observe('competitive-vendor-return', 3, capture=True)
foot_walk((1, 16))
observe('hyper-training-vendor-approach', 3, capture=True)
step(4, 64)
step(20)
press(1)
wait_task('Task_HandleChooseMonInput')
observe('hyper-training-vendor-menu', 3, capture=True, ui=True)
press(2)
finish()
observe('hyper-training-vendor-return', 3, capture=True)
foot_walk((-3, 16))
assert location() == map_id('DewfordTown') and position() == (17, 16)
observe('returned-to-original-dewford', 3, capture=True)
review_mode = bool(lib.read8(s['gJourneyReviewMode']))
lib.stop()
assert hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest() == initial_sha
result = dict(passed=True, kind='dewford-movement', rom_sha256=initial_sha, baseline_rom_sha256=baseline_sha,
              review_mode=review_mode, changed_floor_blocks=changed,
              separately_reviewed_complete_rock_cells=complete_rock_changes,
              former_invisible_boundary_count=29, boundary_checks=boundary_checks,
              all_former_dry_boundaries_controller_roundtrip=True,
              ground_and_shore_level3=True, stair_checks=stair_checks,
              compiled_complete_native_stair_caps=compiled_stair_caps,
              both_north_and_south_stairs_controller_roundtrip=True,
              terminal_wall_preserved=True,
              terminal_wall_sample=terminal_wall,
              upper_bridge_foot_level4_priority1=True,
              lower_bridge_surf_level1_priority2=True,
              both_bridge_rails_surfed_under=True,
              bridge_rails_checked=len(rails), all_bridge_rails_block_foot=True,
              native_surf_prompt_and_northern_disembark=True,
              shore_to_terminal_dry_access_after_disembark=True,
              terminal_door_controller_roundtrip=True,
              two_original_vendors_interacted=True,
              returned_to_original_dewford=True,
              save_continue_checks=save_checks,
              dry_upper_and_surf_save_continue=True,
              no_midtrip_warps_or_coordinate_or_elevation_writes=True,
              initial_placement_party_badges_trainers_are_fixtures=True,
              dry_terrain_captures_compare_current_hardware_avatar_pixels=True,
              sprite_flags_alone_not_used_for_dry_visibility=True,
              full_campaign_playthrough=False, samples=samples, captures=captures)
(args.output / 'dewford-movement.json').write_text(json.dumps(result, indent=2) + '\n')
print('Dewford movement: 29 former invisible boundaries, both stair ends, 22 rails, Surf, terminal and both vendors passed.', flush=True)
