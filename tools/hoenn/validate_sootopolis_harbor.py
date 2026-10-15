"""Walk the bridge, use both doors and travel through the real world-port menus.

Initial story state, party and first placement are fixtures. Walking, talking,
door transitions and the network roundtrip use controller input in mGBA.
"""
import hashlib
import json
import re
from pathlib import Path

from prepare_sootopolis_harbor import ARRIVAL, HARBOR

ROOT = Path(__file__).resolve().parents[2]
bootstrap = (ROOT/'tools/hoenn/validate_abilities.py').read_text().split('\nability_field,')[0]
exec(compile(bootstrap, str(ROOT/'tools/hoenn/validate_abilities.py'), 'exec'))


def idle():
    return lib.read32(s['gMain']+4) & ~1 == s['CB2_Overworld'] and not lib.read8(s['sLockFieldControls'])


def walk_to(x, y):
    for axis, target, positive, negative in [(0, x, 16, 32), (1, y, 128, 64)]:
        for _ in range(800):
            if position()[axis] == target:
                step(20)
                break
            step(1, positive if position()[axis] < target else negative)
        else:
            picture('walk-failure')
            raise AssertionError(('Blocked walkway', location(), position(), (x, y)))


def change_map(key, name):
    for _ in range(400):
        if location() == map_id(name):
            step(180)
            assert idle(), (name, 'Arrival controls locked')
            return
        step(1, key)
    picture('door-failure')
    raise AssertionError(('Door did not change map', name, location(), position()))


def menu():
    return task('Task_HandleMultichoiceInput')


def await_menu():
    for _ in range(500):
        if menu():
            step(20)
            return
        press(1)
    raise AssertionError(('No world-port menu', location(), position()))


getter = s['Menu_GetCursorPos']
ldr = lib.read16(getter)
assert ldr & 0xF800 == 0x4800
cursor = lib.read32(((getter+4) & ~3)+(ldr & 255)*4)+2


def choose(index):
    await_menu()
    for _ in range(12):
        current = lib.read8(cursor)
        if current == index:
            press(1)
            return
        press(64 if current > index else 128)
    raise AssertionError(('Menu selection failed', index))


def talk_up():
    step(4, 64)
    step(20)
    press(1)
    await_menu()


def voyage(name, xy):
    scene = 0
    for _ in range(1200):
        if task('Task_Seagallop_1'):
            scene += 1
            step(8)
        elif location() == map_id(name) and idle():
            break
        else:
            press(1)
    assert scene >= 5, ('Missing world-port animation', scene)
    assert location() == map_id(name) and position() == xy, (name, location(), position(), xy)
    x, y = xy
    assert native('MapGridGetCollisionAt', x+7, y+7) == 0
    behavior = native('MapGridGetMetatileBehaviorAt', x+7, y+7)
    assert not native('MetatileBehavior_IsSurfableWaterOrUnderwater', behavior)
    return dict(destination=name, arrival=list(xy), native_animation_observations=scene)


# Disable Sootopolis cutscenes only in the test fixture, preserving game scripts.
flags = (source/'include/constants/flags.h').read_text()
variables = (source/'include/constants/vars.h').read_text()
for name in ['FLAG_HIDE_SOOTOPOLIS_CITY_STEVEN', 'FLAG_HIDE_SOOTOPOLIS_CITY_GROUDON',
             'FLAG_HIDE_SOOTOPOLIS_CITY_KYOGRE', 'FLAG_HIDE_SOOTOPOLIS_CITY_RAYQUAZA']:
    match = re.search(r'^#define\s+'+name+r'\s+(0x[0-9A-Fa-f]+)', flags, re.M)
    if match:
        native('FlagSet', int(match[1], 16))
for name, value in [('VAR_SOOTOPOLIS_CITY_STATE', 0), ('VAR_SLATEPORT_HARBOR_STATE', 2)]:
    match = re.search(r'^#define\s+'+name+r'\s+(0x[0-9A-Fa-f]+)', variables, re.M)
    assert match, name
    native('VarSet', int(match[1], 16), value)

warp('SootopolisCity', 16, 44)
native('SetPlayerAvatarTransitionFlags', 1)
step(30)
for y in (45, 46):
    shore_mid = native('MapGridGetMetatileIdAt', 16+7, y+7)
    assert shore_mid >= 512, 'Wooden bridge end was replaced or moved'
    shore_background = s['gMetatiles_Sootopolis']+(shore_mid-512)*16
    grass_background = s['gMetatiles_General']+16
    assert [lib.read16(shore_background+i*2) for i in range(4)] == [
        lib.read16(grass_background+i*2) for i in range(4)], 'Shore end does not use native grass'
    assert native('MapGridGetCollisionAt', 16+7, y+7) == 0
for x in range(19, 27):
    assert native('MapGridGetCollisionAt', x+7, 47+7) == 0, 'Extra bridge row remains'
    behavior = native('MapGridGetMetatileBehaviorAt', x+7, 47+7)
    assert native('MetatileBehavior_IsSurfableWaterOrUnderwater', behavior)
walk_to(16, 45)
walk_to(23, 45)
assert not lib.read8(s['gPlayerAvatar']) & 8, 'Bridge requires Surf'
picture('exterior-bridge-walked')
change_map(64, HARBOR)
picture('interior-entered')
walk_to(*ARRIVAL)
assert position() == ARRIVAL
graphics = s['gObjectEventGraphicsInfo_JourneySubmarine']
assert lib.read16(graphics+6) == 2048
assert [lib.read16(graphics+8), lib.read16(graphics+10)] == [64, 64]
for x, y in json.loads((source/'.journey-sootopolis-harbor').read_text())['hull']:
    assert native('MapGridGetCollisionAt', x+7, y+7) != 0
    behavior = native('MapGridGetMetatileBehaviorAt', x+7, y+7)
    assert native('MetatileBehavior_IsSurfableWaterOrUnderwater', behavior)

# Sootopolis -> Slateport -> Sootopolis, with physical captain interaction.
talk_up()
picture('sootopolis-world-port-menu')
choose(1)  # HOENN
choose(0)  # WEST COAST
choose(0)  # SLATEPORT
trips = [voyage('SlateportCity_Harbor', (16, 14))]
picture('slateport-network-arrival')
talk_up()
choose(1)  # HOENN
choose(1)  # EAST COAST
choose(3)  # SOOTOPOLIS
trips.append(voyage(HARBOR, ARRIVAL))
picture('sootopolis-network-return')
walk_to(11, 13)
change_map(128, 'SootopolisCity')
walk_to(16, 45)
walk_to(16, 44)
assert not lib.read8(s['gPlayerAvatar']) & 8
picture('exterior-return-to-land')
# The same bridge and warp must survive the native alternate crisis layout.
state = int(re.search(r'^#define\s+VAR_SOOTOPOLIS_CITY_STATE\s+(0x[0-9A-Fa-f]+)', variables, re.M)[1], 16)
native('VarSet', state, 2)
warp('SootopolisCity', 16, 44)
walk_to(16, 45)
walk_to(23, 45)
picture('crisis-layout-bridge')
change_map(64, HARBOR)
walk_to(11, 13)
change_map(128, 'SootopolisCity')
walk_to(16, 45)
walk_to(16, 44)
report = dict(passed=True, rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
              bridge_walked_without_surf=True, controller_entry_and_exit=True,
              captain_interacted_physically=True, submarine_hull_blocked_over_water=True,
              submarine_sprite_size=[64, 64], crisis_layout_controller_access=True,
              shore_end_uses_native_grass=True, extra_bottom_bridge_row_removed=True,
              bridge_end_stays_in_original_tile=True,
              trips=trips, returned_to_original_land=True,
              initial_story_state_and_first_placement_are_fixtures=True,
              full_campaign_playthrough=False)
lib.stop()
(args.output/'sootopolis-harbor.json').write_text(json.dumps(report, indent=2)+'\n')
print('Sootopolis: bridge, doors, submarine collision and world-port roundtrip passed.')
