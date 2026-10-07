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
import zlib

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--library', type=Path, required=True)
parser.add_argument('--output', type=Path, default=ROOT / 'mods/hoenn/integration-validation')
args = parser.parse_args(); source = args.source.resolve(); args.output.mkdir(parents=True, exist_ok=True)
raw = subprocess.check_output([str(ROOT / '.local/arm-binutils/usr/bin/arm-none-eabi-nm'), '-n', str(source / 'pokeemerald.elf')], text=True)
s = {name: int(address, 16) for address, kind, name in re.findall(r'^(\w+) (\w) (\S+)$', raw, re.M)}
groups = json.loads((source / 'data/maps/map_groups.json').read_text())
lib = ctypes.CDLL(str(args.library.resolve())); lib.start.argtypes = [ctypes.c_char_p]
lib.image.restype = ctypes.c_void_p; lib.read32.restype = ctypes.c_uint32
assert lib.start(str(source / 'pokeemerald.gba').encode())
results = []

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

def native(name, *values):
    code = bytearray.fromhex('00b505480549064a064b00f003f80649086000bd1847c0461111111122222222333333334444444455555555')
    scratch = s['gStringVar4'] + 960
    for sentinel, value in zip([0x11111111, 0x22222222, 0x33333333, 0x44444444, 0x55555555],
                                [*(list(values) + [0]*3)[:3], s[name] | 1, scratch]):
        struct.pack_into('<I', code, code.index(struct.pack('<I', sentinel)), value)
    for i, b in enumerate(code): lib.raw8(0x09f00200 + i, b)
    hook = s['gSpecials']; original = lib.read32(hook); raw32(hook, 0x09f00201)
    lib.write32(scratch, 0xdeadc0de)
    try:
        script(b'\x25\0\0\x6b\x02', 3)
        for _ in range(200):
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
            assert lib.read8(s['isFrlg']) == (name == 'Route21_South_Frlg'), ('Wrong region format', name)
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
cross('JourneyHoennCrossing', 16)
warp('JourneyHoennCrossing', 47, 12)
cross('Route21_South_Frlg', 16)
cross('JourneyHoennCrossing', 32)
warp('JourneyHoennCrossing', 0, 12)
cross('Route127', 32)
warp('Route21_South_Frlg', 1, 22)
picture('Route21-direct-warp-control')
lib.stop()
(args.output / 'crossing.json').write_text(json.dumps(dict(status='experimental_not_full_integration',
    rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
    checks=results, full_story_validated=False, custom_journey_migrated=False), indent=2) + '\n')
print('Four physical Surf seams passed', flush=True)
