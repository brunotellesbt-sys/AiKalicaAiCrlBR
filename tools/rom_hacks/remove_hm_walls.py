#!/usr/bin/env python3
"""Reproducible, version-locked LeafGreen USA 1.1 map modification. Stdlib only."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / 'mods/no-hm-walls/reference.json'
OBSTACLES = {95: 'cut_tree', 96: 'rock_smash_rock', 97: 'strength_boulder'}
BASE = 0x08000000


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Maps:
    def __init__(self, rom, reference):
        self.rom, self.ref = rom, reference

    def u16(self, offset):
        return struct.unpack_from('<H', self.rom, offset)[0]

    def u32(self, offset):
        return struct.unpack_from('<I', self.rom, offset)[0]

    def ptr(self, offset):
        address = self.u32(offset)
        if not BASE <= address < BASE + len(self.rom):
            raise ValueError(f'Invalid ROM pointer at {offset:#x}: {address:#x}')
        return address - BASE

    def headers(self):
        table = self.ref['symbols']['gMapGroups'] - BASE
        for group, names in enumerate(self.ref['groups']):
            bank = self.ptr(table + group * 4)
            for number, name in enumerate(names):
                yield name, group, number, self.ptr(bank + number * 4)

    def layouts(self):
        table = self.ref['symbols']['gMapLayouts'] - BASE
        for index, name in enumerate(self.ref['layouts']):
            if self.u32(table + index * 4):
                layout = self.ptr(table + index * 4)
                if self.u32(layout + 16) and self.u32(layout + 20):
                    yield name, layout

    def attributes(self, layout, tile):
        secondary = tile >= 640
        tileset = self.ptr(layout + (20 if secondary else 16))
        return self.ptr(tileset + 20) + (tile - (640 if secondary else 0)) * 4

    def blocks(self, layout):
        for label, offset, count in [('map', 12, self.u32(layout) * self.u32(layout + 4)),
                                     ('border', 8, self.rom[layout + 24] * self.rom[layout + 25])]:
            start = self.ptr(layout + offset)
            for i in range(count):
                yield label, start + i * 2


def transform(source, ref):
    if sha(source) != ref['source']['baseline_sha256']:
        raise ValueError('Expected the unmodified Pokemon LeafGreen USA v1.1 ROM (SHA-256 in reference.json).')
    before = Maps(source, ref)
    result = bytearray(source)
    counts = Counter()
    affected = []
    for name, group, number, header in before.headers():
        events = before.ptr(header + 4)
        count = source[events]
        removed = Counter()
        if count:
            start = before.ptr(events + 4)
            retained = []
            for i in range(count):
                row = source[start + i * 24:start + (i + 1) * 24]
                graphics_id = int.from_bytes(row[1:1 + ref.get('object_graphics_bytes', 1)], 'little')
                if graphics_id in OBSTACLES:
                    removed[OBSTACLES[graphics_id]] += 1
                    x, y = struct.unpack_from('<hh', row, 4)
                    layout = before.ptr(header)
                    width, height = before.u32(layout), before.u32(layout + 4)
                    if 0 <= x < width and 0 <= y < height:
                        block_at = before.ptr(layout + 12) + (y * width + x) * 2
                        block = before.u16(block_at)
                        if block & 0xC00:
                            struct.pack_into('<H', result, block_at, block & ~0xC00)
                            counts['obstacle_floor_collisions_cleared'] += 1
                else:
                    retained.append(row)
            if removed:
                result[events] = len(retained)
                result[start:start + count * 24] = b''.join(retained).ljust(count * 24, b'\0')
                counts.update(removed)
        dark = bool(source[header + 21])
        if dark:
            result[header + 21] = 0
            counts['flash_maps'] += 1
        if removed or dark:
            affected.append({'map': name, 'group': group, 'number': number,
                             'removed': dict(removed), 'flash_removed': dark})

    # Surf, Waterfall, water collisions/elevations and aquatic encounters stay vanilla.
    gates = {'VictoryRoad_1F': [(12, 14), (12, 15)],
             'VictoryRoad_2F': [(13, 10), (13, 11), (33, 16), (33, 17)],
             'VictoryRoad_3F': [(12, 12), (12, 13)]}
    for name, _, _, header in before.headers():
        if name in gates:
            layout = before.ptr(header)
            for x,y in gates[name]:
                offset = before.ptr(layout + 12) + (y * before.u32(layout) + x) * 2
                # Cave floor replaces the two-tile puzzle barrier with level, walkable ground.
                struct.pack_into('<H', result, offset, 0x299)
                counts['victory_road_gate_cells_opened'] += 1

    constants = ref['constants']
    scripts = []
    def setvar(name, value):
        return b'\x16' + struct.pack('<HH', constants[name], value)
    def script(name, replacement, available):
        offset = ref['symbols'][name] - BASE
        if len(replacement) > available:
            raise ValueError(f'Replacement too long: {name}')
        result[offset:offset + len(replacement)] = replacement
        scripts.append({'symbol': name, 'offset': offset,
                        'before': source[offset:offset + len(replacement)].hex(),
                        'after': replacement.hex()})
    for floor, names in [(1, ['VAR_MAP_SCENE_VICTORY_ROAD_1F']),
                          (2, ['VAR_MAP_SCENE_VICTORY_ROAD_2F_BOULDER1', 'VAR_MAP_SCENE_VICTORY_ROAD_2F_BOULDER2']),
                          (3, ['VAR_MAP_SCENE_VICTORY_ROAD_3F'])]:
        script(f'VictoryRoad_{floor}F_OnLoad', b''.join(setvar(n, 100) for n in names) + b'\x02', 12 if floor != 2 else 23)
    for floor in (3, 4):
        name = f'SeafoamIslands_B{floor}F_OnTransition'
        prefix = source[ref['symbols'][name] - BASE:ref['symbols'][name] - BASE + 9] if floor == 4 else b''
        replacement = prefix + b'\x29' + struct.pack('<H', constants[f'FLAG_STOPPED_SEAFOAM_B{floor}F_CURRENT'])
        replacement += b'\xa7' + struct.pack('<H', constants[f'LAYOUT_SEAFOAM_ISLANDS_B{floor}F_CURRENT_STOPPED']) + b'\x02'
        script(name, replacement, 28 if floor == 4 else 19)
        script(f'SeafoamIslands_B{floor}F_EventScript_EnterByFalling', setvar('VAR_TEMP_1', 0) + b'\x6b\x02', 20)
    # The original boulder solution also replaces these two stair-adjacent water tiles.
    calm_stairs = b''.join(b'\xa2' + struct.pack('<HHHH', x, 14, 0x12B, 0) for x in (12, 13)) + b'\x02'
    script('SeafoamIslands_B4F_OnLoad', calm_stairs, 36)
    script('SeafoamIslands_B4F_EventScript_EnterOnCurrent', setvar('VAR_MAP_SCENE_SEAFOAM_ISLANDS_B4F', 0) + b'\x6b\x02', 18)
    script('SeafoamIslands_B4F_EventScript_UpwardCurrent', b'\x6b\x02', 2)
    result = bytes(result)
    report = {'source_sha256': sha(source), 'target_sha256': sha(result),
              'size': len(result), 'changed_bytes': sum(a != b for a,b in zip(source,result)),
              'maps_scanned': sum(map(len, ref['groups'])), 'layouts_scanned': len(list(before.layouts())),
              'counts': dict(counts), 'affected_maps': affected, 'scripts': scripts}
    return result, report


def number(value):
    out = bytearray()
    while True:
        byte = value & 127
        value >>= 7
        if not value:
            out.append(byte | 128)
            return out
        out.append(byte)
        value -= 1


def bps(source, target):
    patch = bytearray(b'BPS1') + number(len(source)) + number(len(target)) + number(0)
    start = 0
    while start < len(target):
        same = start < len(source) and source[start] == target[start]
        end = start + 1
        while end < len(target) and (end < len(source) and source[end] == target[end]) == same:
            end += 1
        patch += number(((end - start - 1) << 2) | (0 if same else 1))
        if not same:
            patch += target[start:end]
        start = end
    patch += struct.pack('<II', zlib.crc32(source), zlib.crc32(target))
    patch += struct.pack('<I', zlib.crc32(patch))
    return bytes(patch)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'mods/no-hm-walls')
    args = parser.parse_args()
    try:
        source = args.rom.read_bytes()
        target, report = transform(source, json.loads(REFERENCE.read_text()))
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'LeafGreen-No-HM-Walls.gba').write_bytes(target)
    (args.output_dir / 'LeafGreen-No-HM-Walls.bps').write_bytes(bps(source, target))
    (args.output_dir / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('affected_maps','scripts')}, indent=2))


if __name__ == '__main__':
    main()
