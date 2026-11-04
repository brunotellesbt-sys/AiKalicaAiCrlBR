"""Regression: animated water exists above the lower metatile layer too."""
import struct
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from arrival_coast_water import WATER_SLOTS, normalize_upper, orphan_above_terminal


def packed(words):
    return struct.pack('<' + 'H' * len(words), *words)


class UpperMarineWater(unittest.TestCase):
    def test_water_corners_above_boulders_are_normalized(self):
        for graphic in WATER_SLOTS:
            with self.subTest(graphic=graphic):
                words = [0x41C6, 0x41C7, 0x41C7, 0x41C6,
                         graphic | 0x6C00, 0x20AD, 0, 0x20AE]
                result, changes = normalize_upper(packed(words))
                after = list(struct.unpack('<8H', result))
                expected = words.copy()
                expected[4] ^= 0x2000
                self.assertEqual(after, expected)
                self.assertEqual(changes, [dict(word_index=4, graphic=graphic,
                                                before=words[4], after=expected[4])])

    def test_current_sand_object_and_lower_words_are_not_recolored(self):
        words = [0x61AE, 0x61AF, 0x61B0, 0x61B1,
                 0x61A0, 0x61A1, 0x20AD, 0x20AE]
        raw = packed(words)
        self.assertEqual(normalize_upper(raw), (raw, []))

    def test_already_normalized_water_has_no_second_change(self):
        raw = packed([0, 0, 0, 0, 0x41AE, 0x41AF, 0x41B0, 0x41B1])
        self.assertEqual(normalize_upper(raw), (raw, []))


class ClippedTerminalBoulder(unittest.TestCase):
    def fixture(self, root, *, complete=True, roof=True):
        class Staging:
            source = root
            outputs = {}
            expected = {}
            def stage(self, path, blob): self.outputs[path] = blob
        layer = Staging()
        layouts = []
        for name, height in [('OneIsland_Frlg', 20), ('OneIsland_TreasureBeach_Frlg', 40)]:
            words = [0x112B] * (24 * height)
            if height == 20:
                words[18 * 24 + 16] = 0x11CB
                for x, mid in [(2, 0x1CB), (3, 0x1CC), (18, 0x1CB), (19, 0x1CC)]:
                    words[19 * 24 + x] = 0x1000 | mid
            else:
                words[2], words[3] = 0x5D3, 0x5D4 if complete else 0x112B
                words[18] = words[19] = 0x7A5 if roof else 0x5D3
            files = {f'data/maps/{name}/map.json': json.dumps(dict(layout=name)).encode(),
                     f'data/layouts/{name}/map.bin': packed(words)}
            layouts.append(dict(id=name, width=24, height=height,
                                blockdata_filepath=f'data/layouts/{name}/map.bin'))
            for path, blob in files.items():
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(blob)
                layer.expected[path] = hashlib.sha256(blob).hexdigest()
        path = 'data/layouts/layouts.json'
        blob = json.dumps(dict(layouts=layouts)).encode()
        (root / path).write_bytes(blob)
        layer.expected[path] = hashlib.sha256(blob).hexdigest()
        return layer

    def test_removes_three_fragments_and_keeps_whole_neighbor_rock(self):
        with tempfile.TemporaryDirectory() as directory:
            layer = self.fixture(Path(directory))
            row = orphan_above_terminal(layer)
            before = (layer.source / row['file']).read_bytes()
            after = layer.outputs[row['file']]
            left = struct.unpack('<480H', before)
            right = struct.unpack('<480H', after)
            self.assertEqual([i for i, (a, b) in enumerate(zip(left, right)) if a != b],
                             [18 * 24 + 16, 19 * 24 + 18, 19 * 24 + 19])
            self.assertEqual([right[19 * 24 + x] for x in (18, 19)], [0x112B, 0x112B])
            self.assertEqual([right[19 * 24 + x] for x in (2, 3)], [0x11CB, 0x11CC])

    def test_refuses_to_hide_an_unrelated_rock_or_break_the_complete_donor(self):
        for arguments in [dict(complete=False), dict(roof=False)]:
            with self.subTest(arguments=arguments), tempfile.TemporaryDirectory() as directory:
                layer = self.fixture(Path(directory), **arguments)
                with self.assertRaises(AssertionError): orphan_above_terminal(layer)
                self.assertFalse(layer.outputs)


if __name__ == '__main__':
    unittest.main()
