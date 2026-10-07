#!/usr/bin/env python3
"""Real mGBA seam checks for the experimental multiregion crossing, not a campaign test."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import zlib

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--library', type=Path, required=True)
parser.add_argument('--worldsea', action='store_true', help='Also exercise every edge of the experimental eastern ocean grid')
parser.add_argument('--westsea', action='store_true', help='Use the revised Cinnabar/Route114 crossing and validate the western coast')
parser.add_argument('--region-state', action='store_true', help='Exercise separate badge/champion/story banks and native flash save/reload')
parser.add_argument('--east-coast', action='store_true', help='Exercise the three eastern Hoenn exits and Fuchsia sea connection')
parser.add_argument('--gym-scaling', action='store_true', help='Generate actual gym parties at every regional badge count')
parser.add_argument('--output', type=Path, default=ROOT / 'mods/hoenn/integration-validation')
args = parser.parse_args(); source = args.source.resolve(); args.output.mkdir(parents=True, exist_ok=True)
raw = subprocess.check_output([str(ROOT / '.local/arm-binutils/usr/bin/arm-none-eabi-nm'), '-n', str(source / 'pokeemerald.elf')], text=True)
s = {name: int(address, 16) for address, kind, name in re.findall(r'^(\w+) (\w) (\S+)$', raw, re.M)}
groups = json.loads((source / 'data/maps/map_groups.json').read_text())
layouts = {l['id']: l for l in json.loads((source / 'data/layouts/layouts.json').read_text())['layouts']}
lib = ctypes.CDLL(str(args.library.resolve())); lib.start.argtypes = [ctypes.c_char_p]
lib.image.restype = ctypes.c_void_p; lib.read32.restype = ctypes.c_uint32
assert lib.start(str(source / 'pokeemerald.gba').encode())
results = []
call4 = None
abi = None
if args.gym_scaling:
    toolchain = ROOT / '.local/arm-gcc/usr/bin/arm-none-eabi-gcc'
    with tempfile.TemporaryDirectory(prefix='gym-fixture-', dir='/tmp') as directory:
        temp = Path(directory)
        subprocess.run([str(ROOT / '.local/arm-binutils/usr/bin/arm-none-eabi-as'), '-mthumb', '-march=armv4t', str(ROOT / 'tools/hoenn/fixture_call4.s'), '-o', str(temp / 'call.o')], check=True)
        subprocess.run([str(ROOT / '.local/arm-binutils/usr/bin/arm-none-eabi-objcopy'), '-O', 'binary', '-j', '.text', str(temp / 'call.o'), str(temp / 'call.bin')], check=True)
        call4 = (temp / 'call.bin').read_bytes()
        subprocess.run([str(toolchain), '-S', '-iquote', str(source / 'include'), '-DMODERN=1', '-DPOKEEMERALD', '-mthumb', '-march=armv4t', '-mabi=apcs-gnu', str(ROOT / 'tools/hoenn/fixture_gym_abi.c'), '-o', str(temp / 'abi.s')], check=True)
        abi = [int(n) for n in re.findall(r'\.word\s+(\d+)', (temp / 'abi.s').read_text())]

def step(n, keys=0): lib.frames(n, keys)
def save(): return lib.read32(s['gSaveBlock1Ptr'])
def location(): return lib.read8(save() + 4), lib.read8(save() + 5)
def map_id(name): return next((g, groups[label].index(name)) for g, label in enumerate(groups['group_order']) if name in groups[label])
def position():
    obj = s['gObjectEvents'] + lib.read8(s['gPlayerAvatar'] + 5) * 36
    return lib.read16(obj + 16) - 7, lib.read16(obj + 18) - 7

def picture(name):
    pixels = ctypes.string_at(lib.image(), 240 * 160 * 4)
    rgb = b''.join(b'\0' + bytes(v for i, v in enumerate(pixels[y*960:(y+1)*960]) if i % 4 != 3) for y in range(160))
    def chunk(kind, data): return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    (args.output / (name + '.png')).write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 240, 160, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(rgb)) + chunk(b'IEND', b''))

def script(code, frames=900):
    for i, byte in enumerate(code): lib.raw8(0x09f00000 + i, byte)
    context = s['sGlobalScriptContext']
    for i in range(116): lib.write8(context + i, 0)
    lib.write8(context + 1, 1); lib.write32(context + 8, 0x09f00000)
    lib.write32(context + 92, s['gScriptCmdTable']); lib.write32(context + 96, s['gScriptCmdTableEnd'])
    lib.write8(s['sGlobalScriptContextStatus'], 0); lib.write8(s['sLockFieldControls'], 1)
    step(frames)

def warp(name, x, y):
    g, n = map_id(name)
    script(b'\x39' + bytes([g, n, 255]) + struct.pack('<HH', x, y) + b'\x27\x6b\x02')
    assert location() == (g, n), (name, location())

def raw32(addr, value):
    for i, b in enumerate(struct.pack('<I', value)): lib.raw8(addr + i, b)

def native(name, *values, max_frames=200):
    code = bytearray(call4) if len(values) == 4 else bytearray.fromhex('00b505480549064a064b00f003f80649086000bd1847c0461111111122222222333333334444444455555555')
    scratch = s['gStringVar4'] + 960
    sentinels = [0x11111111, 0x22222222, 0x33333333, 0x44444444, 0x55555555]
    params = [*(list(values) + [0]*3)[:3], s[name] | 1, scratch]
    if len(values) == 4:
        sentinels += [0x66666666]; params = [*values, s[name] | 1, scratch]
    for sentinel, value in zip(sentinels, params):
        struct.pack_into('<I', code, code.index(struct.pack('<I', sentinel)), value)
    for i, b in enumerate(code): lib.raw8(0x09f00200 + i, b)
    hook = s['gSpecials']; original = lib.read32(hook); raw32(hook, 0x09f00201)
    lib.write32(scratch, 0xdeadc0de)
    try:
        script(b'\x25\0\0\x6b\x02', 3)
        for _ in range(max_frames):
            if lib.read32(scratch) != 0xdeadc0de: break
            step(1)
        assert lib.read32(scratch) != 0xdeadc0de, ('Native fixture failed', name)
        return lib.read32(scratch)
    finally: raw32(hook, original)

def cross(name, key):
    before = location()
    for _ in range(240):
        step(4, key)
        if location() == map_id(name):
            step(20)
            assert lib.read8(s['gPlayerAvatar']) & 8, ('Lost Surf', name, position())
            target_data = json.loads((source / f'data/maps/{name}/map.json').read_text())
            expected_frlg = layouts[target_data['layout']]['layout_version'] == 'frlg'
            assert lib.read8(s['isFrlg']) == expected_frlg, ('Wrong region format', name)
            results.append(dict(check='physical_surf_seam', source=before, target=name, passed=True))
            picture(name + '-arrival')
            print('Physical Surf seam passed:', name, flush=True)
            return
    picture('failed-' + name)
    raise AssertionError(('No seam transition', name, location(), position()))

step(900)
save2 = lib.read32(s['gSaveBlock2Ptr']); lib.write8(save2, 255); lib.write8(save2 + 8, 255)
lib.write32(s['gMain'], 0); lib.write8(s['gMain'] + 0x438, 0)
lib.write32(s['gMain'] + 4, s['CB2_NewGame'] | 1); step(300)
warp('Route127', 79, 42)
assert native('ScriptGiveMon', 7, 30, 0) == 0
native('ScriptSetMonMoveSlot', 0, 57, 0)
# The native candidate's badge gates are unchanged at this stage. This test
# isolates the camera/map seam, NOT early-HM unlocking or the custom story.
native('SetPlayerAvatarTransitionFlags', 8); step(30)
assert lib.read8(s['gPlayerAvatar']) & 8
if not args.westsea:
    cross('JourneyHoennCrossing', 16)
    warp('JourneyHoennCrossing', 47, 12)
    cross('Route21_South_Frlg', 16)
    cross('JourneyHoennCrossing', 32)
    warp('JourneyHoennCrossing', 0, 12)
    cross('Route127', 32)
warp('Route21_South_Frlg', 1, 22)
picture('Route21-direct-warp-control')
if args.region_state:
    regional = json.loads((source / '.journey-region-state').read_text())
    badges = [lib.read16(s['gBadgeFlags'] + i * 2) for i in range(8)]
    champion = 0xB5A  # compiled probe: SYSTEM_FLAGS + 4 on the pinned base
    event = regional['frlg_flags']['FLAG_HIDE_BULBASAUR_BALL']
    warp('VermilionCity_Frlg', 33, 39)
    trainer_before = native('FlagGet', event['original'])
    for badge in badges: native('FlagSet', badge)
    native('FlagSet', champion)
    native('FlagSet', event['allocated'])
    assert all(native('FlagGet', b) for b in badges)
    assert native('FlagGet', champion)
    assert native('FlagGet', event['original']) == trainer_before
    warp('Route131', 50, 35)
    assert all(not native('FlagGet', b) for b in badges), 'Kanto badge leaked into Hoenn'
    assert not native('FlagGet', champion), 'Kanto championship leaked into Hoenn'
    native('FlagSet', badges[0]); native('FlagSet', champion)
    warp('VermilionCity_Frlg', 33, 39)
    native('FlagClear', badges[0]); native('FlagToggle', badges[1])
    assert not native('FlagGet', badges[0]) and not native('FlagGet', badges[1])
    warp('Route131', 50, 35)
    assert native('FlagGet', badges[0]) and not native('FlagGet', badges[1])
    assert native('FlagGet', champion)
    # Save/reload only the emulator's own flash; no user save is loaded.
    assert native('TrySavingData', 0, max_frames=6000) == 1, 'Native flash save failed'
    native('FlagClear', badges[0]); native('FlagClear', champion)
    native('FlagClear', event['allocated'])
    assert native('LoadGameSave', 0) == 1, 'Native flash reload failed'
    assert native('FlagGet', badges[0]) and native('FlagGet', champion)
    assert native('FlagGet', event['allocated'])
    warp('VermilionCity_Frlg', 33, 39)
    assert not native('FlagGet', badges[0]) and not native('FlagGet', badges[1])
    assert all(native('FlagGet', b) for b in badges[2:])
    assert native('FlagGet', champion)
    results.append(dict(check='regional_flags_and_native_save_roundtrip', passed=True,
        kanto_badges_independent=True, champion_independent=True, trainer_flag_unchanged=True))
    print('Regional badges/champion/story bank and native flash roundtrip passed', flush=True)
if args.gym_scaling:
    scaling = json.loads((source / '.journey-gym-scaling').read_text())
    trainer_size, mon_size, pokemon_size, party_offset, class_offset, lvl_offset, level_data, species_data, leader, frlg_leader, battle_trainer, trainers_count, difficulty_normal = abi
    trainers_base = s['gTrainers'] + difficulty_normal * trainers_count * trainer_size
    ids = {}
    for path in ['include/constants/opponents.h', 'include/constants/opponents_frlg.h']:
        ids.update({n:int(v) for n,v in re.findall(r'#define\s+(TRAINER_\w+)\s+(\d+)\b', (source / path).read_text())})
    native_badges = [lib.read16(s['gBadgeFlags'] + 2*i) for i in range(8)]
    kanto_badges = list(range(0x1AB0,0x1AB8))
    def set_bank(flags, count):
        for i, flag in enumerate(flags):
            address = save()+4720+flag//8
            byte = lib.read8(address); mask = 1 << (flag & 7)
            lib.write8(address, byte | mask if i < count else byte & ~mask)
    parties_tested = 0
    # Avoid gym on-entry story scripts: fixtures set the current map identity
    # only. This isolates real party generation, not accessibility or battles.
    for gym in scaling['gyms']:
        group, number = map_id(gym['map'])
        lib.write8(save()+4,group); lib.write8(save()+5,number)
        lib.write8(s['isFrlg'], int(gym['kanto']))
        for count in range(8):
            set_bank(kanto_badges if gym['kanto'] else native_badges,count)
            set_bank(native_badges if gym['kanto'] else kanto_badges,7-count)
            assert native('JourneyGymBadgeCount',int(gym['kanto'])) == count
            for name in gym['trainers']:
                trainer = trainers_base+ids[name]*trainer_size
                party_ptr = lib.read32(trainer+party_offset)
                target_party = s['gParties']+6*pokemon_size
                size = native('CreateNPCTrainerPartyFromTrainer',target_party,trainer,0,battle_trainer)
                assert 1 <= size <= 6, (name,size)
                original = [lib.read8(party_ptr+i*mon_size+lvl_offset) for i in range(size)]
                highest = max(original)
                is_leader = lib.read8(trainer+class_offset) in [leader,frlg_leader]
                for i, level in enumerate(original):
                    expected = scaling['ace_levels'][count] - min(6,highest-level) - (0 if is_leader else 2)
                    actual = native('GetMonData3',target_party+i*pokemon_size,level_data,0)
                    assert actual == expected,(gym['map'],name,count,i,actual,expected)
                parties_tested += 1
        print('Gym generated parties passed:',gym['map'],flush=True)
    # Non-gym battles retain original levels.
    group,number=map_id('Route131'); lib.write8(save()+4,group); lib.write8(save()+5,number)
    trainer=trainers_base+ids['TRAINER_ROXANNE_1']*trainer_size
    assert native('JourneyGymLevel',trainer,15) == 15
    results.append(dict(check='native_gym_party_levels',passed=True,parties=parties_tested,
        maps=len(scaling['gyms']),badge_counts=list(range(8)),non_gym_level_preserved=True,
        access_or_free_order_validated=False))
if args.worldsea or args.westsea or args.east_coast:
    ocean = dict(connections={})
    if args.worldsea:
        ocean['connections'].update(json.loads((source / '.journey-worldsea').read_text())['connections'])
    if args.westsea:
        ocean['connections'].update(json.loads((source / '.journey-westsea').read_text())['connections'])
    if args.east_coast:
        ocean['connections'].update(json.loads((source / '.journey-east-coast').read_text())['connections'])
    by_id = {json.loads((source / f'data/maps/{name}/map.json').read_text())['id']: name
             for name in ocean['connections']}
    keys = dict(up=64, down=128, left=32, right=16)
    for origin, links in ocean['connections'].items():
        origin_data = json.loads((source / f'data/maps/{origin}/map.json').read_text())
        layout = layouts[origin_data['layout']]
        for link in links:
            if link['map'] not in by_id: continue  # native routes are not modified here
            target = by_id[link['map']]
            if not origin.startswith('Journey') and not target.startswith('Journey'):
                continue  # preserved land seams are not new Surf passages
            direction, offset = link['direction'], link['offset']
            target_data = json.loads((source / f'data/maps/{target}/map.json').read_text())
            target_layout = layouts[target_data['layout']]
            if direction in ['up', 'down']:
                low, high = max(0, offset), min(layout['width'], offset + target_layout['width'])
                x = (low + high) // 2
                # Safe opened lane beside the pier; Vermilion's ocean channel
                # is x33/34, not the midpoint of its city-wide connection.
                if origin == 'VermilionCity_Frlg': x = 33
                elif target == 'VermilionCity_Frlg': x = 33
                elif origin.endswith('_Harbor_Frlg'): x = 4
                elif target.endswith('_Harbor_Frlg'): x = offset + 4
                y = 0 if direction == 'up' else layout['height'] - 1
            else:
                low, high = max(0, offset), min(layout['height'], offset + target_layout['height'])
                y = (low + high) // 2
                x = 0 if direction == 'left' else layout['width'] - 1
            warp(origin, x, y)
            native('SetPlayerAvatarTransitionFlags', 8); step(30)
            cross(target, keys[direction])
lib.stop()
(args.output / ('connected-world.json' if args.westsea else 'worldsea.json' if args.worldsea else 'crossing.json')).write_text(json.dumps(dict(status='experimental_not_full_integration',
    rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
    checks=results, full_story_validated=False, custom_journey_migrated=False), indent=2) + '\n')
print(f'{sum(r["check"] == "physical_surf_seam" for r in results)} physical Surf seams passed', flush=True)
