"""Prove the mandatory rescue through native controller input in mGBA."""
import hashlib
import json
from pathlib import Path
import re

from validate_atlas_candidate_batteries_native import save_menu
from validate_cold_boot import validate as cold_boot

ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / 'tools/hoenn/validate_team_missions.py'
exec(compile(BOOTSTRAP.read_text().split('\nwins, completed =')[0], str(BOOTSTRAP), 'exec'))

CITY = 'SootopolisCity'
PORT = 'JourneySootopolisHarbor'
AREA = 'JourneySootopolisRescue'
GYM = 'SootopolisCity_Gym_1F'
RESCUE = 0x40E5
variables = (source / 'include/constants/vars.h').read_text()
opponents = (source / 'include/constants/opponents.h').read_text()
def constant(data, name):
    return int(re.search(r'^#define\s+' + name + r'\s+(0x[0-9A-Fa-f]+|\d+)\b', data, re.M)[1], 0)

def var(name, value):
    native('VarSet', constant(variables, name), value)

def stage():
    return native('VarGet', RESCUE)

def wait_for(predicate, label, key=1):
    for _ in range(220):
        if predicate():
            return
        press(key)
    picture('failed-' + label)
    raise AssertionError((label, location(), position(), stage()))

def talk_up():
    step(4, 64)
    step(20)
    press(1)

def active_actor(local_id):
    return any(
        lib.read8(s['gObjectEvents'] + 36 * slot) & 1
        and lib.read8(s['gObjectEvents'] + 36 * slot + 8) == local_id
        for slot in range(16)
    )

for index, flag_value in enumerate(hoenn_flags):
    rawflag(flag_value, index != 7)
for trainer in stories['trainers']:
    rawflag(0x500 + trainer['id'], True)
for name in [
    'FLAG_DEFEATED_EVIL_TEAM_MT_CHIMNEY', 'FLAG_HIDE_SAFFRON_ROCKETS',
    'FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT', 'FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE',
    'FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN',
]:
    rawflag(flag_id(name), True)
rawflag(0x500 + constant(opponents, 'TRAINER_MATT'), True)
var('VAR_MOSSDEEP_SPACE_CENTER_STATE', 3)
var('VAR_SOOTOPOLIS_CITY_STATE', 6)
var('VAR_SKY_PILLAR_STATE', 2)
galactic_first = bool(lib.read8(s['gJourneyBuildRules'] + 2))
var('VAR_JOURNEY_GALACTIC_STATE', 7 if galactic_first else 0)
native('ScriptSetMonMoveSlot', 0, 57, 2)
native('DisableWildEncounters', 1)
assert stage() == 0
rawflag(abi[111], True)
native('JourneySootopolisRescueStatus')
assert not lib.read16(s['gSpecialVar_Result']) and pending(False) == 14
rawflag(abi[111], False)
rawflag(hoenn_flags[7], True)
assert pending(False) == 0, 'An old save must keep its eight Hoenn badges'
native('JourneySootopolisRescueStatus')
assert lib.read16(s['gSpecialVar_Result']) == 1, 'Old saves can play the rescue'
rawflag(hoenn_flags[7], False)
assert pending(False) == 24
doors = [door_probe(CITY, True)]
# The other native Rayquaza arrival and the seven other gym choices use the same gate.
var('VAR_SKY_PILLAR_STATE', 3)
for missing in range(8):
    for index, flag_value in enumerate(hoenn_flags):
        rawflag(flag_value, index != missing)
    assert pending(False) == 24, missing
    lib.write16(s['gSpecialVar_0x8004'], missing)
    native('JourneySootopolisRescueGymGuard')
    assert lib.read16(s['gSpecialVar_Result']) == 24
for index, flag_value in enumerate(hoenn_flags):
    rawflag(flag_value, index != 7)

names = [CITY, PORT, AREA, GYM]
allowed = set()
walk_prefix = 'sootopolis-rescue'
walk_max_ticks = 3500
walk_transition_pictures = False
exec(compile((ROOT / 'tools/hoenn/native_water_walk.py').read_text(),
             'sootopolis-rescue-native-walker', 'exec'))
port_id = map_id(PORT)
area_id = map_id(AREA)
# Initial placement at the city side of the native harbor door.
harbor = next(row for row in maps[CITY]['warp_events'] if row['dest_map'] == maps[PORT]['id'])
warp(CITY, harbor['x'], harbor['y'] + 1)
refresh_loaded_warp_tiles()
walk((PORT, 8, 12))
talk_up()
wait_for(lambda: task('Task_HandleYesNoInput'), 'captain-offer')
picture('captain-offers-rescue')
press(1)
wait_for(lambda: location() == area_id and idle(), 'ferry-landing')
assert position() == (7, 19) and stage() == 1
assert not lib.read8(s['gPlayerAvatar']) & 8
picture('arrive-on-dry-sand')
walk((AREA, 8, 19))
talk_up()
finish()
walk((AREA, 12, 14))
assert lib.read8(s['gPlayerAvatar']) & 8
assert active_actor(3)
picture('surf-to-manaphy')
talk_up()
finish()
walk((AREA, 17, 8))
assert not lib.read8(s['gPlayerAvatar']) & 8 and active_actor(4) and active_actor(5)
picture('reach-castaways')
talk_up()
finish()
assert stage() == 2 and not active_actor(4) and not active_actor(5)
walk((AREA, 11, 14))
assert lib.read8(s['gPlayerAvatar']) & 8
checkpoint = args.output / 'escort-in-progress.sav'
save_menu(globals(), checkpoint)
picture('surf-escort-save')
assert native('LoadGameSave', 0, max_frames=6000) == 1
lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
step(950)
finish()
assert location() == area_id and position() == (11, 14)
assert lib.read8(s['gPlayerAvatar']) & 8 and stage() == 2
assert not active_actor(4) and not active_actor(5)
walk((AREA, 6, 19))
assert active_actor(8)
picture('raft-reaches-the-landing')
talk_up()
lugia = kyogre = False
for _ in range(220):
    if location() == area_id and active_actor(6) and not lugia:
        picture('lugia-shields-the-raft')
        lugia = True
    if location() == area_id and active_actor(7) and not kyogre:
        picture('kyogre-reacts-to-the-pulse')
        kyogre = True
    if location() == port_id and idle() and stage() == 4:
        break
    press(1)
assert lugia and kyogre
assert location() == port_id and position() == (8, 12) and stage() == 4
assert pending(False) == 0
picture('rescue-confirmed-at-the-harbor')
talk_up()
wait_for(lambda: task('Task_HandleMultichoiceInput'), 'usual-ferry')
picture('regular-ferry-preserved')
press(2)
finish()
doors.append(door_probe(CITY, False))
lib.stop()

cold = cold_boot(source, args.library, args.output / 'cold-continue', checkpoint,
                 expected_geometry_version=9)
resumed = cold['runs'][-1]
assert tuple(resumed['field_map']) == area_id and resumed['player_tile'] == [11, 14] and resumed['player_surfing']
report = dict(
    passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
    elf_sha256=hashlib.sha256((source / 'pokeemerald.elf').read_bytes()).hexdigest(),
    marker_sha256=hashlib.sha256((source / '.journey-sootopolis-rescue').read_bytes()).hexdigest(),
    required_for_eight_last_gym_choices=True, physical_gym_door_before_and_after=doors,
    galactic_completed_before_rescue=galactic_first, old_save_eight_badges_keep_access=True,
    offers_rescue_only_after_rayquaza=True, blocks_leader_inside_unwon_gym=True,
    native_port_entry_and_ferry=True, native_surf_both_directions=True,
    manaphy_and_two_castaways_seen=True, lugia_and_kyogre_seen=True,
    rescue_completion_state=4, controller_save_and_cold_continue=cold,
    restored_from_save_during_escort=True, regular_ferry_still_available=True,
    initial_mission_badges_and_placement_are_fixtures=True,
    capture_sha256={png.name: hashlib.sha256(png.read_bytes()).hexdigest()
                    for png in sorted(args.output.glob('*.png'))},
)
(args.output / 'sootopolis-rescue.json').write_text(json.dumps(report, indent=2) + '\n')
print('Native mandatory Sootopolis rescue, gym gate, Surf and Continue passed', flush=True)
