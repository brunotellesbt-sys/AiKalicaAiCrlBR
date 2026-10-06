"""Run: python3 -m unittest discover -s tools/rom_hacks -v"""
import json
from pathlib import Path
import struct
import unittest
import zlib

from remove_hm_walls import BASE, Maps, OBSTACLES, REFERENCE, ROOT, bps, sha, transform


def apply_bps(source, patch):
    if patch[:4] != b'BPS1' or zlib.crc32(patch[:-4]) != struct.unpack_from('<I', patch, len(patch)-4)[0]:
        raise ValueError('Invalid patch')
    source_crc, target_crc = struct.unpack_from('<II', patch, len(patch)-12)
    if zlib.crc32(source) != source_crc:
        raise ValueError('Wrong source')
    cursor = 4
    def number():
        nonlocal cursor
        value, shift = 0, 1
        while True:
            byte = patch[cursor]; cursor += 1
            value += (byte & 127) * shift
            if byte & 128:
                return value
            shift <<= 7
            value += shift
    source_size, target_size, metadata_size = number(), number(), number()
    cursor += metadata_size
    if source_size != len(source):
        raise ValueError('Wrong source size')
    target = bytearray()
    while len(target) < target_size:
        command = number()
        length, action = (command >> 2) + 1, command & 3
        if action == 0:
            target += source[len(target):len(target)+length]
        elif action == 1:
            target += patch[cursor:cursor+length]; cursor += length
        else:
            raise ValueError('Unexpected action')
    if cursor != len(patch)-12 or zlib.crc32(target) != target_crc:
        raise ValueError('Wrong output')
    return bytes(target)


class ROMTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ref = json.loads(REFERENCE.read_text())
        cls.source = (ROOT / 'Pokemon - Leaf Green Version (U) (V1.1).gba').read_bytes()
        cls.target, cls.report = transform(cls.source, cls.ref)
        cls.before, cls.after = Maps(cls.source, cls.ref), Maps(cls.target, cls.ref)

    def test_outputs_and_bps_roundtrip(self):
        directory = ROOT / 'mods/no-hm-walls'
        self.assertEqual(self.target, (directory / 'LeafGreen-No-HM-Walls.gba').read_bytes())
        self.assertEqual(self.report, json.loads((directory / 'manifest.json').read_text()))
        patch = (directory / 'LeafGreen-No-HM-Walls.bps').read_bytes()
        self.assertEqual(patch, bps(self.source, self.target))
        self.assertEqual(self.target, apply_bps(self.source, patch))
        self.assertEqual(len(self.target), 16 * 1024 * 1024)
        self.assertEqual(self.source[:0xC0], self.target[:0xC0])

    def test_all_maps_keep_other_objects_and_local_ids(self):
        removed = {95: 0, 96: 0, 97: 0}
        for name, _, _, header in self.before.headers():
            events = self.before.ptr(header + 4)
            count = self.source[events]
            if count:
                start = self.before.ptr(events + 4)
                original = [self.source[start+i*24:start+(i+1)*24] for i in range(count)]
                retained = [row for row in original if row[1] not in OBSTACLES]
                for row in original:
                    if row[1] in removed: removed[row[1]] += 1
                actual = [self.target[start+i*24:start+(i+1)*24] for i in range(self.target[events])]
                self.assertEqual(retained, actual, name)
                self.assertFalse(any(row[1] in OBSTACLES for row in actual), name)
            self.assertEqual(self.source[events+1:events+20], self.target[events+1:events+20], name)
        self.assertEqual(removed, {95:55, 96:97, 97:58})

    def test_surf_waterfall_and_encounters_preserved(self):
        for table in self.ref['attribute_tables']:
            start, size = table['address'] - BASE, table['count']*4
            self.assertEqual(self.source[start:start+size], self.target[start:start+size], table['symbol'])
        script = self.ref['symbols']['SeafoamIslands_B4F_EventScript_WarpInOnCurrent'] - BASE
        self.assertEqual(self.source[script:script+8], self.target[script:script+8])

    def test_layouts_only_change_eight_victory_road_cells(self):
        changed = []
        for name, layout in self.before.layouts():
            for kind, offset in self.before.blocks(layout):
                if self.before.u16(offset) != self.after.u16(offset):
                    changed.append((name, kind, self.after.u16(offset)))
        self.assertEqual(len(changed), 8)
        self.assertTrue(all(name in ('VictoryRoad_1F','VictoryRoad_2F','VictoryRoad_3F') and kind == 'map' and tile == 0x299 for name,kind,tile in changed))

    def test_flash_and_articuno(self):
        dark = []
        for name, _, _, header in self.before.headers():
            if self.source[header+21]: dark.append(name)
            self.assertEqual(self.target[header+21], 0)
        self.assertEqual(set(dark), {'RockTunnel_1F', 'RockTunnel_B1F'})
        offset = self.ref['symbols']['SeafoamIslands_B4F_OnTransition'] - BASE
        self.assertEqual(self.source[offset:offset+9], self.target[offset:offset+9])
        self.assertEqual(len(self.report['scripts']), 10)

    def test_wrong_rom_and_corrupt_patch_rejected(self):
        source = bytearray(self.source); source[0xBC] ^= 1
        with self.assertRaises(ValueError): transform(source, self.ref)
        patch = bytearray(bps(self.source, self.target))
        with self.assertRaises(ValueError): apply_bps(source, patch)
        patch[-1] ^= 1
        with self.assertRaises(ValueError): apply_bps(self.source, patch)


if __name__ == '__main__':
    unittest.main()
