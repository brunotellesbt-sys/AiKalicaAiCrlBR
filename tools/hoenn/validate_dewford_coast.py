"""Reproduce Dewford's original escape, or validate the repaired coast natively."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--library', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--expect-broken', action='store_true')
parser.add_argument('--video', action='store_true')
dewford_options = parser.parse_args()
initial_sha = hashlib.sha256((dewford_options.source / 'pokeemerald.gba').read_bytes()).hexdigest()
sys.argv = [sys.argv[0], '--source', str(dewford_options.source), '--library', str(dewford_options.library),
            '--output', str(dewford_options.output)]
bootstrap = (ROOT / 'tools/hoenn/validate_sootopolis_harbor.py').read_text().split('\n# Disable Sootopolis')[0]
exec(compile(bootstrap, __file__, 'exec'))


def player():
    return s['gObjectEvents'] + lib.read8(s['gPlayerAvatar'] + 5) * 36


def state():
    sprite = s['gSprites'] + lib.read8(player() + 35) * 68
    x, y = position()
    return dict(map=next((name for group in groups['group_order'] for name in groups[group]
                        if map_id(name) == location()), str(location())),
                tile=[x, y], surf=bool(lib.read8(s['gPlayerAvatar']) & 8),
                elevation=native('PlayerGetElevation'),
                map_elevation=native('MapGridGetElevationAt', x + 7, y + 7),
                priority=(lib.read16(sprite + 4) >> 10) & 3,
                sprite_visible=not bool(lib.read16(sprite + 0x3E) & 4),
                object_visible=not bool(lib.read8(player() + 1) & 0x20))


native('RtcInitLocalTimeOffset', 12, 0)
warp('DewfordTown', 17, 16)
native('SetPlayerAvatarTransitionFlags', 1)
step(90)
walk_to(19, 16)
change_map(16, 'Route107')
assert position() == (0, 16)
walk_to(4, 16)
assert not lib.read8(s['gPlayerAvatar']) & 8
picture('native-departure-from-dewford')

if dewford_options.expect_broken:
    departure = state()
    assert departure['elevation'] == 3, departure
    # The original transition-0 sand at (4,15) opens the side rail. Every
    # subsequent step is controller input, with no elevation/position fixture.
    walk_to(4, 15)
    transition = state()
    picture('old-transition-zero-sand')
    walk_to(4, 14)
    rail = state()
    picture('old-pedestrian-inside-bridge-rail')
    walk_to(8, 14)
    ocean = state()
    behavior = native('MapGridGetMetatileBehaviorAt', 8 + 7, 14 + 7)
    assert not ocean['surf'] and native('MetatileBehavior_IsSurfableWaterOrUnderwater', behavior), ocean
    picture('old-pedestrian-walking-on-ocean')
    result = dict(passed=False, expected_broken_baseline=True, bug_reproduced=True,
                  rom_sha256=initial_sha, departure=departure, transition=transition,
                  rail=rail, ocean=ocean, first_placement_only_is_fixture=True,
                  no_elevation_or_coordinate_writes_after_departure=True)
    lib.stop()
    assert hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest() == initial_sha
    (args.output / 'dewford-coast-bug-reproduced.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Original Dewford defect reproduced: land → transition-0 → rail → ocean, on foot.', flush=True)
    raise SystemExit(0)

coast = json.loads((source / '.journey-dewford-coast-safety').read_text())
harbor = json.loads((source / '.journey-dewford-island-harbor').read_text())
shop = json.loads((source / '.journey-dewford-competitive-shop').read_text())
DEWFORD_HARBOR = 'JourneyDewfordHarbor'
NORTH = 'JourneyDewfordPortIsland'
names = ['DewfordTown', 'Route106', 'Route107', 'Route108', NORTH, DEWFORD_HARBOR]
maps = {name: json.loads((source / f'data/maps/{name}/map.json').read_text()) for name in names}
by_location = {map_id(name): name for name in names}
samples, rail_checks = [], []
neighbor_checks = []
origins = {'DewfordTown': (-20, 0), 'Route106': (-80, -20),
           'Route107': (0, 0), NORTH: (0, -12)}
coast_blocks = {}
for name in origins:
    layout = layouts[maps[name]['layout']]
    raw_blocks = (source / layout['blockdata_filepath']).read_bytes()
    coast_blocks[name] = (layout['width'], layout['height'],
                         struct.unpack('<' + 'H' * (len(raw_blocks) // 2), raw_blocks))


def check_loaded_neighbors(label):
    """Inspect the actual RAM map buffer, including diagonal roof/coast tiles."""
    name = by_location[location()]
    if name not in origins:
        return
    width = lib.read32(s['gBackupMapLayout'])
    height = lib.read32(s['gBackupMapLayout'] + 4)
    buffer = lib.read32(s['gBackupMapLayout'] + 8)
    origin_x, origin_y = origins[name]
    checked = 0
    donors = {}
    for yy in range(height):
        world_y = yy - 7 + origin_y
        for xx in range(width):
            world_x = xx - 7 + origin_x
            for donor, (donor_x, donor_y) in origins.items():
                if donor == name:
                    continue
                x, y = world_x - donor_x, world_y - donor_y
                w, h, tiles = coast_blocks[donor]
                if not (0 <= x < w and 0 <= y < h):
                    continue
                actual = lib.read16(buffer + 2 * (yy * width + xx))
                expected = tiles[y * w + x]
                assert actual == expected, ('Broken loaded coastal/roof corner', label, name,
                    [xx - 7, yy - 7], donor, [x, y], hex(actual), hex(expected))
                checked += 1
                donors[donor] = donors.get(donor, 0) + 1
                break
    assert checked > 0
    neighbor_checks.append(dict(label=label, map=name, loaded_neighbor_tiles=checked, donors=donors))


def observe(label, elevation=None, surf=False, priority=None):
    row = state()
    row['label'] = label
    assert row['surf'] == surf, ('Wrong avatar state', row)
    assert row['sprite_visible'] and row['object_visible'], ('Hidden avatar', row)
    if elevation is not None:
        assert row['elevation'] == elevation, ('Wrong player elevation', row)
    if priority is not None:
        assert row['priority'] == priority, ('Wrong drawing priority', row)
    samples.append(row)
    return row


def hold_blocked(key, label, elevation, surf=False, priority=None):
    before = position()
    step(90, key)
    step(45)
    assert position() == before, ('Collision did not block native movement', label, before, position())
    return observe(label, elevation, surf, priority)


def finish(limit=500):
    for _ in range(limit):
        if idle():
            step(45)
            return
        press(1)
    picture('dialogue-failed')
    raise AssertionError(('Dialogue did not finish', location(), position()))


def continue_here(label, elevation, surf, priority):
    before = position()
    before_map = location()
    assert native('TrySavingData', 0, max_frames=6000) == 1
    assert native('LoadGameSave', 0, max_frames=6000) == 1
    lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
    step(1500)
    assert location() == before_map and position() == before
    observe(label, elevation, surf, priority)
    picture(label)


# Party, HM permissions and defeated route trainers are initial test state.
# Enemy parties, coordinates and elevation are never changed while travelling.
assert native('ScriptGiveMon', 260, 50, 0) == 0
native('ScriptSetMonMoveSlot', 0, 57, 0)
for flag_number in [lib.read16(s['gBadgeFlags'] + i * 2) for i in range(8)] + list(range(0x1AB0, 0x1AB8)):
    native('FlagSet', flag_number)
native('VarSet', 0x40FE, 7)
trainer_ids = {}
for path in ['include/constants/opponents.h', 'include/constants/opponents_frlg.h']:
    trainer_ids.update({name: int(number) for name, number in re.findall(
        r'^#define\s+(TRAINER_\w+)\s+(\d+)\b', (source / path).read_text(), re.M)})
for name in ['Route106', 'Route107', 'Route108']:
    scripts = (source / f'data/maps/{name}/scripts.inc').read_text()
    for trainer in set(re.findall(r'trainerbattle_[a-z_]+\s+(TRAINER_\w+)', scripts)):
        native('SetTrainerFlag', trainer_ids[trainer])

landings = []
for x, y in [(4, 15), (5, 16), (6, 16)]:
    assert native('MapGridGetElevationAt', x + 7, y + 7) == 3
    assert native('MapGridGetCollisionAt', x + 7, y + 7) == 0
    landings.append([x, y])

# Revisit the exact escape from the original ROM, starting on native sand 3.
walk_to(4, 15)
check_loaded_neighbors('route107-initial-corner-buffer')
observe('native-side-approach-from-sand', 3, priority=2)
hold_blocked(64, 'old-west-rail-escape-blocked', 3, priority=2)
picture('pedestrian-blocked-at-original-escape')
walk_to(4, 16)
walk_to(5, 16)
walk_to(5, 15)
observe('south-stair-one-up', 4, priority=1)
walk_to(5, 16)
observe('south-stair-one-down', 3, priority=2)
walk_to(6, 16)
walk_to(6, 15)
observe('south-stair-two-up', 4, priority=1)
walk_to(6, 16)
observe('south-stair-two-down', 3, priority=2)
walk_to(5, 16)
walk_to(5, 15)
for y in range(14, 3, -1):
    for x, target, key in [(5, 4, 32), (6, 7, 16)]:
        walk_to(x, y)
        row = hold_blocked(key, f'rail-{target}-{y}', 4, priority=1)
        assert native('MapGridGetMetatileIdAt', target + 7, y + 7) in harbor['bridge_rail_metatiles']
        rail_checks.append(dict(standing=[x, y], rail=[target, y], held_frames=90,
                                pedestrian_elevation=row['elevation']))
walk_to(5, 9)
picture('bridge-upper-visible')
continue_here('bridge-upper-save-continue', 4, False, 1)
hold_blocked(32, 'saved-upper-rail-remains-blocked', 4, priority=1)
walk_to(5, 3)
check_loaded_neighbors('terminal-neighboring-roof')
observe('north-stair-and-island', 4, priority=1)
change_map(64, DEWFORD_HARBOR)
picture('terminal-inside-controller-entry')
walk_to(11, 13)

# Record the requested continuous terminal -> bridge -> sellers -> Dewford
# trip. No warp, coordinate write or avatar-state fixture occurs in this video.
encoder = None
video_frames = 0
base_step = step
video = args.output / 'dewford-terminal-bridge-vendors.mp4'
if dewford_options.video:
    encoder_log = (args.output / 'video-ffmpeg.log').open('w')
    encoder = subprocess.Popen(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'warning',
        '-filter_threads', '1', '-f', 'rawvideo', '-pixel_format', 'rgba',
        '-video_size', '240x160', '-framerate', '30', '-i', 'pipe:0', '-an',
        '-vf', 'scale=960:640:flags=neighbor', '-c:v', 'libx264', '-preset', 'fast',
        '-threads', '1', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
        str(video)], stdin=subprocess.PIPE, stderr=encoder_log)

    def step(n, keys=0):
        global video_frames
        while n:
            chunk = min(n, 2)
            base_step(chunk, keys)
            n -= chunk
            encoder.stdin.write(ctypes.string_at(lib.image(), 240 * 160 * 4))
            video_frames += 1

change_map(128, 'Route107')
assert position() == (5, 3)
observe('terminal-controller-return', 4, priority=1)
picture('terminal-outside-native-return')
walk_to(5, 14)
walk_to(6, 14)
walk_to(6, 15)
walk_to(6, 16)
observe('bridge-to-native-sand', 3, priority=2)
walk_to(2, 16)


def wait_task(task_name, limit=500):
    for _ in range(limit):
        if task(task_name):
            step(30)
            return
        press(1)
    picture('missing-' + task_name)
    raise AssertionError(('Expected interaction did not open', task_name))


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
    raise AssertionError('Seller did not release controls')


step(4, 64)
step(20)
press(1)
wait_task('Task_HandleScrollingMultichoiceInput')
picture('dewford-competitive-seller-menu')
for _ in range(4):
    press(128)
press(1)
wait_task('Task_ShopMenu')
picture('dewford-competitive-stock')
leave_shop()
walk_to(1, 16)
step(4, 64)
step(20)
press(1)
wait_task('Task_HandleChooseMonInput')
picture('dewford-hyper-training-menu')
press(2)
finish()
walk_to(0, 16)
change_map(32, 'DewfordTown')
assert position() == (19, 16)
walk_to(17, 16)
check_loaded_neighbors('dewford-after-continuous-terminal-return')
observe('continuous-terminal-vendors-dewford-arrival', 3, priority=2)
picture('dewford-two-vendors-and-native-coast')
step(120)
if encoder is not None:
    encoder.stdin.close()
    assert encoder.wait() == 0
    encoder_log.close()
    step = base_step

# Return to the same route on foot, then invoke the game's ordinary Surf menu.
walk_to(19, 16)
change_map(16, 'Route107')
walk_to(7, 16)
observe('native-southeast-shore', 3, priority=2)
hold_blocked(16, 'water-blocks-foot-without-surf', 3, priority=2)
assert native('IsPlayerFacingSurfableFishableWater')
press(1)
finish()
step(90)
assert lib.read8(s['gPlayerAvatar']) & 8
walk_to(8, 16)
observe('native-surf-prompt', 1, True, 2)
walk_to(7, 16)
step(90)
observe('native-disembark', 3, priority=2)
picture('native-disembark-to-sand')
step(4, 16)
step(20)
press(1)
finish()
step(90)
walk_to(8, 16)

# Read the same compiled native attribute tables used by the route walker.
# The plan below admits water and the lower bridge only; all actual movement
# and seamless camera/map transitions run through controller input.
allowed = set()
walk_prefix = 'dewford-coast'
walk_max_ticks = 2000
walk_transition_pictures = False
walk_surf_under_bridges = True
exec(compile((ROOT / 'tools/hoenn/native_water_walk.py').read_text(), 'dewford-native-water-walker', 'exec'))
for name, (width, height, tiles) in blocks.items():
    passable[name] = {i for i in passable[name] if tiles[i] >> 12 in [1, 15]
                      and water_behaviors[behaviors[name][i]]}
walk(('Route107', 3, 8))
walk(('Route107', 5, 8))
observe('surf-below-bridge', 1, True, 2)
picture('bridge-lower-surf-visible')
continue_here('bridge-lower-save-continue', 1, True, 2)
walk(('Route107', 8, 8))
walk(('Route107', 3, 8))
walk(('Route107', 8, 8))
observe('under-bridge-controller-roundtrip', 1, True, 2)
# A boat below the bridge cannot enter either elevated stair or northern dry
# terminal. It may disembark only on native level-3 beach, as tested above.
walk(('Route107', 5, 14))
hold_blocked(128, 'upper-stair-blocks-lower-surf', 1, True, 2)
picture('surf-blocked-by-upper-stair')

# The restored southern corner is a separate real landing. Approach it from
# the open sea, disembark on native sand, then use the normal Surf prompt to
# return. A fixture on the dry corner would miss the original elevation bug.
walk(('Route107', 8, 18))
walk_to(7, 18)
step(90)
observe('southern-corner-native-disembark', 3, priority=2)
hold_blocked(128, 'southern-corner-whole-tree-blocks-foot', 3, priority=2)
picture('southern-corner-disembarked')
hold_blocked(16, 'southern-corner-water-blocks-foot', 3, priority=2)
assert native('IsPlayerFacingSurfableFishableWater')
press(1)
finish()
step(90)
walk_to(8, 18)
observe('southern-corner-native-surf-prompt', 1, True, 2)
hold_blocked(128, 'southern-corner-side-bank-blocks-surf', 1, True, 2)
picture('southern-corner-reembarked')

for goal in [('Route107', 15, 1), (NORTH, 15, 11), (NORTH, 15, 0),
             (NORTH, 0, 0), ('Route106', 79, 8), ('Route106', 70, 8),
             (NORTH, 0, 0), (NORTH, 15, 0), (NORTH, 15, 11),
             ('Route107', 15, 1), ('Route108', 1, 8), ('Route107', 58, 8)]:
    walk(goal)
    check_loaded_neighbors('channel-' + goal[0])
    observe('channel-' + goal[0], 1, True, 2)
    if goal[0] in [NORTH, 'Route106', 'Route108']:
        picture('surf-channel-' + goal[0])
channels = [(row['source'][0], row['destination'][0]) for row in transitions]
for a, b in [('Route107', NORTH), (NORTH, 'Route106'), ('Route107', 'Route108')]:
    assert (a, b) in channels and (b, a) in channels, ('Missing bidirectional Surf seam', a, b, channels)

# Verify every original competitive price without buying or changing money.
expressions = ['ITEM_' + item for item in shop['prices']]
code = '#include "global.h"\n#include "constants/items.h"\nconst u32 price_ids[]={' + ','.join(expressions) + '};'
assembly = subprocess.check_output([str(ROOT / '.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),
    '-S', '-mabi=apcs-gnu', '-iquote', str(source / 'include'), '-x', 'c', '-', '-o', '-'],
    input=code, text=True)
item_ids = [int(number) for number in re.findall(r'\.word\s+(\d+)',
            assembly.split('price_ids:', 1)[1].split('.size', 1)[0])]
assert len(item_ids) == len(shop['prices'])
for item, item_id in zip(shop['prices'], item_ids):
    assert native('GetItemPrice', item_id) == shop['prices'][item], item
assert len(rail_checks) == 22
assert hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest() == initial_sha
result = dict(passed=True, rom_sha256=initial_sha,
    review_mode=bool(lib.read8(s['gJourneyReviewMode'])),
    native_dewford_route107_bidirectional=True,
    foot_and_surf_states_preserved=True, land_blocks_surf=True, water_blocks_foot=True,
    controllers_only=True, bridge_rails_checked=len(rail_checks), all_bridge_rails_block_foot=True,
    three_transition_sands_are_level3=True, dry_landings=landings, stair_edges_3_to4_walked=True,
    foot_drawn_above_bridge=True, surf_drawn_below_bridge=True,
    save_continue_upper_and_lower=True, terminal_door_roundtrip=True,
    two_dewford_vendors_interacted=True, prices_checked=len(item_ids),
    channels_bidirectional=channels, rail_checks=rail_checks, samples=samples,
    loaded_diagonal_neighbors_match_source=True, neighbor_checks=neighbor_checks,
    native_surf_prompt=True, native_disembark=True, no_elevation_writes=True,
    native_southern_corner_landing_and_reembarkation=True,
    continuous_terminal_bridge_vendors_dewford_controller_trip=True,
    no_midroute_warp_or_coordinate_writes=True,
    initial_party_badges_trainers_and_first_placement_are_fixtures=True)
if dewford_options.video:
    result.update(video=video.name, video_sha256=hashlib.sha256(video.read_bytes()).hexdigest(),
                  video_frames=video_frames, video_fps=30, video_seconds=video_frames / 30)
lib.stop()
(args.output / 'dewford-coast.json').write_text(json.dumps(result, indent=2) + '\n')
print('Dewford coast: native foot/Surf separation, 22 rails, saves, vendors, doors and 3 bidirectional sea seams passed.', flush=True)
