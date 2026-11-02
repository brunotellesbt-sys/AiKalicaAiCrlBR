"""Constrain the palette repair to actual lower-layer ocean graphics."""
import struct
import unittest
from coastal_ecology_ocean import normalize


class OceanUnderlayTest(unittest.TestCase):
    def test_only_lower_water_palette_six_changes(self):
        before=[0x61C6,0x65C7,0x69C6,0x6DC7,0x61C6,0x65C7,0x69C6,0x6DC7]
        after, changes=normalize(struct.pack('<8H',*before))
        self.assertEqual(struct.unpack('<8H',after),tuple([x^0x2000 for x in before[:4]]+before[4:]))
        self.assertEqual([r['word_index'] for r in changes],[0,1,2,3])
        self.assertEqual(normalize(after),(after,[]))

    def test_does_not_recolor_objects_other_palettes_or_graphics(self):
        before=[0x41C6,0x51C7,0x61C5,0x61C8,0x61C6,0x61C7,0x6DC6,0x6DC7]
        blob=struct.pack('<8H',*before)
        self.assertEqual(normalize(blob),(blob,[]))


if __name__=='__main__':
    unittest.main()
