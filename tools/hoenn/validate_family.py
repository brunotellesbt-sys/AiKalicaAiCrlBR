"""Exercise each native starting-city menu and home in an isolated mGBA process.

Uses the same ARM call trampoline and ABI as the world validator. Injected
warps shorten travel; city/starter menus, stairs, doors and NPC scripts are real.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--source', type=Path, required=True)
p.add_argument('--library', type=Path, required=True)
p.add_argument('--output', type=Path, default=ROOT / 'mods/hoenn/integration-validation')
p.add_argument('--city', type=int, choices=range(31))
p.add_argument('--hoenn-control', action='store_true')
options = p.parse_args()
if options.city is None:
    samples = []
    with tempfile.TemporaryDirectory(prefix='family-emulator-', dir='/tmp') as directory:
        for city in list(range(16)) + list(range(17,31)):
            out = Path(directory) / str(city)
            child = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                '--source', str(options.source.resolve()), '--library', str(options.library.resolve()),
                '--output', str(out), '--city', str(city)], capture_output=True, text=True)
            assert child.returncode == 0, child.stdout + child.stderr
            samples.append(json.loads((out / 'family.json').read_text()))
            options.output.mkdir(parents=True, exist_ok=True)
            for pic in out.glob('family-*.png'):
                (options.output / pic.name).write_bytes(pic.read_bytes())
            print('Native starting home passed:', samples[-1]['city'], flush=True)
        out = Path(directory) / 'hoenn'
        child = subprocess.run([sys.executable, str(Path(__file__).resolve()),
            '--source', str(options.source.resolve()), '--library', str(options.library.resolve()),
            '--output', str(out), '--city', '16', '--hoenn-control'], capture_output=True, text=True)
        assert child.returncode == 0, child.stdout + child.stderr
        control = json.loads((out / 'family.json').read_text())
    (options.output / 'family.json').write_text(json.dumps(dict(passed=True,
        rom_sha256=hashlib.sha256((options.source / 'pokeemerald.gba').read_bytes()).hexdigest(),
        cities=samples, hoenn_origin_control=control, full_story_validated=False), indent=2) + '\n')
    sys.exit(0)

city = options.city
hoenn_control = options.hoenn_control
# Reuse only the initialization and helpers, never execute the world tests.
sys.argv = [sys.argv[0], '--source', str(options.source), '--library', str(options.library),
            '--output', str(options.output), '--water-hms', '--westsea']
common = (ROOT / 'tools/hoenn/validate_crossing.py').read_text().split('\nstep(900)\n')[0]
exec(compile(common, str(ROOT / 'tools/hoenn/validate_crossing.py'), 'exec'))
home = json.loads((source / '.journey-birth').read_text())['homes'][city]
hoenn = city >= 16
starter_species = abi[52:55] if hoenn else [1, 4, 7]

def press(key, pause=30):
    step(1, key); step(pause)

def task(name):
    return any(lib.read8(s['gTasks'] + i * 40 + 4) and
        lib.read32(s['gTasks'] + i * 40) & ~1 == s[name] for i in range(16))

def advance_until(predicate, limit=180):
    for _ in range(limit):
        if predicate(): return
        press(1, 40)
    picture(f'family-{city:02d}-failure')
    raise AssertionError(('Dialogue did not reach target', city, location(), position()))

def event(label, talked=1):
    lib.write16(s['gSpecialVar_LastTalked'], talked)
    script(b'\x05' + struct.pack('<I', s[label]), 45)

def finish():
    advance_until(lambda: not lib.read8(s['sLockFieldControls']))

def var(number): return native('VarGet', number)

step(900)
save2 = lib.read32(s['gSaveBlock2Ptr'])
lib.write8(save2, 255); lib.write8(save2 + 8, 255)
lib.write8(save2 + abi[32], city % 2)
lib.write8(save2 + abi[45], abi[51] if hoenn else abi[46])
lib.write32(s['gMain'], 0); lib.write8(s['gMain'] + 0x438, 0)
lib.write32(s['gMain'] + 4, s['CB2_NewGame'] | 1)
step(300)
if hoenn_control:
    advance_until(lambda: task('Task_HandleMultichoiceGridInput'))
    press(1)
    step(1500)
    assert location() == map_id('InsideOfTruck')
    step(90, 16); step(200)
    finish()
    assert location() == map_id('LittlerootTown_BrendansHouse_1F')
    event('Journey_Family'); finish()
    assert all(native('CountTotalItemQuantityInBag', item) == 1 for item in abi[17:20])
    warp('PalletTown_PlayersHouse_2F_Frlg', 6, 6)
    step(300)
    assert not task('Task_HandleMultichoiceGridInput')
    assert not lib.read8(s['sLockFieldControls'])
    assert var(0x40F7) == 17 and var(0x40FA) == 1
    assert lib.read8(s['gPartiesCount']) == 0
    warp('PalletTown_PlayersHouse_2F_Frlg', 6, 6)
    assert not task('Task_HandleMultichoiceGridInput')
    lib.stop()
    (args.output / 'family.json').write_text(json.dumps(dict(passed=True,
        native_hoenn_start_not_replaced=True, no_late_city_chooser=True)) + '\n')
    sys.exit(0)
advance_until(lambda: task('Task_HandleMultichoiceGridInput'))
if city == 0: picture('family-city-menu')
choice = city - 16 if hoenn else city
columns = 3 if hoenn else 2
for _ in range(choice // columns): press(128)
for _ in range(choice % columns): press(16)
press(1)
step(1500)
assert location() == map_id('InsideOfTruck')
step(90, 16); step(200)
if city in [0, 9, 28, 30]: picture(f'family-{city:02d}-arrival')
finish()
assert var(0x40F7) == city + 1, ('Wrong city', city, var(0x40F7))
assert lib.read8(s['gPartiesCount']) == 0
assert native('JourneyGymBadgeCount', 0) == native('JourneyGymBadgeCount', 1) == 0
bedname = f'JourneyHoennBedroom{city-16:02d}' if hoenn else 'PalletTown_PlayersHouse_2F_Frlg' if city == 0 else f'JourneyFamilyBedroom{city:02d}'
assert location() == map_id(bedname), ('Wrong bedroom', home, location())
original = json.loads((source / f'data/maps/{home["house"]}/map.json').read_text())
# Only this house aliases to a new interior; the other fifteen keep their headers.
for other in json.loads((source / '.journey-birth').read_text())['homes']:
    group, num = map_id(other['house'])
    assert bool(native('JourneyFamilyHomeHeader', group, num)) == (other['index'] == city + 1 and city != 0)

def stairs(name):
    stair_x, stair_y = (7, 1) if hoenn and name == bedname else (8, 2) if hoenn else (10, 2)
    warp(name, stair_x, stair_y + 1)
    behavior = native('MapGridGetMetatileBehaviorAt', stair_x+7, stair_y+7)
    west = native('IsDirectionalStairWarpMetatileBehavior', behavior, 3)
    east = native('IsDirectionalStairWarpMetatileBehavior', behavior, 4)
    if west or east:
        warp(name, stair_x+1 if west else stair_x-1, stair_y)
        step(40, 32 if west else 16)
    else:
        step(40, 64)
    step(150)

stairs(bedname)
assert location() == map_id(home['house']), ('Stairs did not enter living room', city, location(), position(), lib.read8(s['sLockFieldControls']), lib.read8(s['gPlayerAvatar']))
living_name = f'JourneyHoennLiving{city-16:02d}' if hoenn else 'PalletTown_PlayersHouse_1F_Frlg' if city == 0 else f'JourneyFamilyLiving{city:02d}'
living = json.loads((source / f'data/maps/{living_name}/map.json').read_text())
if city in [1, 6, 15, 17, 28, 30]: picture(f'family-{city:02d}-oak-living-room')
if city:
    warp(home['house'], 8 if hoenn else 4, 7)
    step(20, 128); step(60)
    finish()
    assert location() == map_id(home['house']) and var(0x40F9) == 1
    assert position()[1] < 8, 'Exit before starter was not blocked'

water = abi[17:20]
expected_gifts = 0
for person in range(home['people']):
    event('Journey_Family', person + 1); finish()
    assigned = 7 if home['people'] == 1 else (3 if person == 0 else 4) if home['people'] == 2 else 1 << person
    received = var(0x40F8)
    expected_gifts |= assigned
    assert received == expected_gifts
    before = [native('CountTotalItemQuantityInBag', item) for item in water]
    event('Journey_Family', person + 1); finish()
    assert before == [native('CountTotalItemQuantityInBag', item) for item in water]
assert all(native('CountTotalItemQuantityInBag', item) == 1 for item in water)
assert native('FlagGet', 0x1ABD)

if city == 3:
    # This one-person home gives all three HMs. Force partial capacity in the
    # encrypted TM pocket, then retry the actual NPC event without duplicates.
    pocket = s['gBagPockets'] + 2 * 8
    capacity = lib.read16(pocket + 4) & 1023
    slots = lib.read32(pocket)
    saved_slots = bytes(lib.read8(slots + i) for i in range(capacity * 4))
    for i in range(capacity * 4): lib.write8(slots + i, 0)
    native('VarSet', 0x40F8, 0)
    native('FlagClear', 0x1ABD)
    assert native('AddBagItem', 582, 1)
    filler = bytes(lib.read8(slots + i) for i in range(4))
    for index in range(capacity):
        for i, byte in enumerate(filler): lib.write8(slots + index * 4 + i, byte)
    event('Journey_Family'); finish()
    assert var(0x40F8) == 0 and not native('FlagGet', 0x1ABD)
    for i in range(4): lib.write8(slots + (capacity - 1) * 4 + i, 0)
    event('Journey_Family'); finish()
    assert var(0x40F8) == 1 and not native('FlagGet', 0x1ABD)
    assert native('CountTotalItemQuantityInBag', water[0]) == 1
    for index in range(capacity - 3, capacity - 1):
        for i in range(4): lib.write8(slots + index * 4 + i, 0)
    event('Journey_Family'); finish()
    assert var(0x40F8) == 7 and native('FlagGet', 0x1ABD)
    assert all(native('CountTotalItemQuantityInBag', item) == 1 for item in water)
    for i, byte in enumerate(saved_slots): lib.write8(slots + i, byte)

starter = city % 3
if city:
    event('Journey_Oak', home['people'] + 1)
    advance_until(lambda: task('Task_HandleMultichoiceInput'))
    for _ in range(starter): press(128)
    press(1)
    finish()
    assert native('FlagGet', 0x1ABE) and native('FlagGet', 0x1ABF)
    assert lib.read8(s['gPartiesCount']) == 1
    assert native('GetMonData3', s['gParties'], abi[7], 0) == starter_species[starter]
    assert native('GetMonData3', s['gParties'], abi[6], 0) == 5
    assert var(0x40F9) == 2
    assert var(abi[55] if hoenn else abi[49]) == (starter if hoenn else [0, 2, 1][starter])
    assert native('FlagGet', abi[50])
    # The converted mother runs the canonical post-starter healing event.
    hp = native('GetMonData3', s['gParties'], abi[48], 0)
    scratch_data = s['gStringVar4'] + 800
    lib.write16(scratch_data, 1)
    native('SetMonData', s['gParties'], abi[47], scratch_data)
    event('Journey_Family'); finish()
    assert native('GetMonData3', s['gParties'], abi[47], 0) == hp
    # One visit cannot give another Pokemon; starter choice is fixed in FRLG's bank.
    native('JourneyFamilyGiveStarter')
    assert lib.read8(s['gPartiesCount']) == 1
    warp(home['house'], 8 if hoenn else 4, 7)
    step(50, 128); step(150)
    exterior = next(w['dest_map'] for w in original['warp_events'] if not w['dest_map'].endswith('ROOM2'))
    by_id = {json.loads((source / f'data/maps/{n}/map.json').read_text())['id']: n
        for group in groups['group_order'] for n in groups[group] if (source / f'data/maps/{n}/map.json').exists()}
    assert location() == map_id(by_id[exterior]), ('Front door exit failed', city, location(), exterior, position(), var(0x40F9), lib.read8(s['sLockFieldControls']), native('MapGridGetMetatileBehaviorAt',12,15), native('PlayerGetElevation'))
    # Preserve and finish any native outdoor arrival event (e.g. Four Island's rival).
    finish()
    outdoor = json.loads((source / f'data/maps/{by_id[exterior]}/map.json').read_text())
    exit_warp = next(w for w in original['warp_events'] if w['dest_map'] == exterior)
    front = outdoor['warp_events'][int(exit_warp['dest_warp_id'])]
    warp(by_id[exterior], front['x'], front['y'] + 1)
    # Re-enter through the original outdoor warp destination.
    step(50, 64); step(150)
    assert location() == map_id(home['house']), ('Exterior re-entry failed', city, location(), position(), native('MapGridGetMetatileBehaviorAt',position()[0]+7,position()[1]+6))
    assert native('FlagGet', 0x1ABF)
    stairs(home['house'])
    assert location() == map_id(bedname), ('Return stairs failed', city, location())
    assert native('TrySavingData', 0, max_frames=6000) == 1
    native('VarSet', 0x40F7, 0)
    native('VarSet', 0x40F8, 0)
    assert native('LoadGameSave', 0) == 1
    step(30)  # Allow the field script to settle after save-block relocation.
    assert var(0x40F7) == city + 1 and var(0x40F8) == 7
    assert native('FlagGet', 0x1ABE)
assert native('JourneyGymBadgeCount', 0) == native('JourneyGymBadgeCount', 1) == 0
lib.stop()
(args.output / 'family.json').write_text(json.dumps(dict(passed=True, city=home['city'],
    house=home['house'], people=home['people'], roles=home['roles'], player_gender=city % 2,
    vehicle=json.loads((source / '.journey-birth').read_text())['arrivals'][city]['vehicle'],
    real_city_menu=True, selection_before_motion=True, fixed_house_alias_only=True, actual_stairs_and_door=True,
    family_gifts_once=True, starter_species=None if city == 0 else starter_species[starter],
    starter_level=None if city == 0 else 5, original_pallet_intro=city == 0,
    native_save_roundtrip=city != 0, original_mother_heal=city != 0,
    full_bag_and_partial_retry=city == 3,
    full_story_validated=False), indent=2) + '\n')
