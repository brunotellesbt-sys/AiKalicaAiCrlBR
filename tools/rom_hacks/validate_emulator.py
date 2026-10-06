#!/usr/bin/env python3
"""mGBA field movement checks. Test-only RAM/ROM injection never touches the delivered ROM."""
import argparse
import ctypes
import json
from pathlib import Path
import struct
import zlib
from remove_hm_walls import ROOT, REFERENCE

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--library', type=Path, required=True, help='Compiled mgba_bridge shared library')
parser.add_argument('--screenshots', type=Path, required=True)
args = parser.parse_args()
lib = ctypes.CDLL(str(args.library.resolve()))
lib.start.argtypes = [ctypes.c_char_p]
lib.image.restype = ctypes.c_void_p
ref = json.loads(REFERENCE.read_text())
symbols = ref['debug_symbols']
assert lib.start(str(ROOT / 'mods/no-hm-walls/LeafGreen-No-HM-Walls.gba').encode())
args.screenshots.mkdir(parents=True, exist_ok=True)

def step(n, keys=0):
    lib.frames(n, keys)

def screenshot(name):
    data = ctypes.string_at(lib.image(), 240*160*4)
    raw = b''.join(b'\0' + bytes(v for i,v in enumerate(data[y*960:(y+1)*960]) if i%4 != 3) for y in range(160))
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind+data))
    (args.screenshots / (name+'.png')).write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB',240,160,8,2,0,0,0)) + chunk(b'IDAT',zlib.compress(raw)) + chunk(b'IEND',b''))

# Reach the normal introduction, then initialize a fresh save through the game's
# own CB2_NewGame. No party, badges, HMs, or obstacle flags are granted.
step(180)
for _ in range(12):
    step(10,8); step(120)
lib.write8(lib.read32(symbols['gSaveBlock1Ptr'])+0x3A4C,0xFF)
lib.write8(lib.read32(symbols['gSaveBlock2Ptr']),0xFF)
lib.write32(symbols['gMain'],0)
lib.write8(symbols['gMain']+0x438,0)
lib.write32(symbols['gMain']+4,symbols['CB2_NewGame']|1)
step(300)
screenshot('new-game')

def warp(name,x,y):
    group,number = next((g,n) for g,names in enumerate(ref['groups']) for n,v in enumerate(names) if v==name)
    code = b'\x39'+bytes([group,number,255])+struct.pack('<HH',x,y)+b'\x27\x6b\x02'
    for i,v in enumerate(code): lib.raw8(0x08800000+i,v)
    context = symbols['sGlobalScriptContext']
    for i in range(116): lib.write8(context+i,0)
    lib.write8(context+1,1)
    lib.write32(context+8,0x08800000)
    lib.write32(context+92,symbols['gScriptCmdTable'])
    lib.write32(context+96,symbols['gScriptCmdTableEnd'])
    lib.write8(symbols['sGlobalScriptContextStatus'],0)
    lib.write8(symbols['sLockFieldControls'],1)
    step(900)

def position():
    obj = symbols['gObjectEvents'] + lib.read8(symbols['gPlayerAvatar']+5)*36
    return lib.read16(obj+16)-7, lib.read16(obj+18)-7

results = []
for name, origin, frames, key, expected, label in [
    ('PalletTown',(10,15),24,128,(10,16),'water-still-requires-surf'),
    ('Route2',(16,61),20,128,(16,63),'cut-tree-removed'),
    ('OneIsland_KindleRoad',(8,103),20,128,(8,105),'rock-smash-removed'),
    ('VictoryRoad_1F',(7,17),20,128,(7,19),'strength-boulder-removed'),
    ('VictoryRoad_1F',(12,16),40,64,(12,14),'victory-road-gate-open')]:
    warp(name,*origin)
    assert position() == origin, (label, position(), origin)
    step(frames,key); step(30)
    assert position() == expected, (label, position(), expected)
    screenshot(label)
    results.append({'check':label,'map':name,'from':origin,'to':position(),'passed':True})
for floor in (3,4):
    warp(f'SeafoamIslands_B{floor}F',8,10)
    save = lib.read32(symbols['gSaveBlock1Ptr'])
    actual = lib.read16(save+0x32)
    expected = ref['constants'][f'LAYOUT_SEAFOAM_ISLANDS_B{floor}F_CURRENT_STOPPED']
    assert actual == expected, (floor,actual,expected)
    screenshot(f'seafoam-b{floor}f-calm')
    results.append({'check':f'seafoam-b{floor}f-calm-layout','passed':True})
lib.stop()
(args.screenshots / 'results.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
