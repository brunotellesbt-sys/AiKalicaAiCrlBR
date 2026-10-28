"""Hardware animation evidence must correspond to visible emulator pixels."""
import ctypes
import struct
import unittest

from audit_generated_shore_animation import visible_graphic_pixels


class NativeShorePixelEvidence(unittest.TestCase):
    def fixture(self, actual_rgb):
        memory=bytearray(65536)
        memory[416*32:417*32]=bytes([0x22])*32
        for address in range(31*2048,32*2048,2):
            struct.pack_into('<H',memory,address,416|(1<<12))
        pixels=ctypes.create_string_buffer(bytes([*actual_rgb,255])*(240*160))
        class FakeHardware:
            def read16(self,address):
                if address==0x04000000:return 0x100  # BG0, tiled mode0.
                if address==0x04000008:return 31<<8
                if address==0x05000000+18*2:return 2|(3<<5)|(4<<10)
                return 0
            def image(self):
                return ctypes.addressof(pixels)
        def read(address,size):
            return bytes(memory[address-0x06000000:address-0x06000000+size])
        return read,FakeHardware()

    def test_graphics_slot_counts_only_when_its_native_color_is_visible(self):
        read,hardware=self.fixture((16,24,32))
        evidence=visible_graphic_pixels(read,hardware,{'sGpuRegBuffer':0x1000},{416})
        self.assertEqual(len(evidence),240*160)
        self.assertEqual(evidence[(0,0)],(416,(16,24,32)))

    def test_hidden_or_covered_background_cannot_be_claimed_as_visible_water(self):
        read,hardware=self.fixture((240,0,0))
        self.assertEqual(visible_graphic_pixels(read,hardware,{'sGpuRegBuffer':0x1000},{416}),{})

    def test_other_visible_graphics_do_not_certify_the_animated_slot(self):
        read,hardware=self.fixture((16,24,32))
        self.assertEqual(visible_graphic_pixels(read,hardware,{'sGpuRegBuffer':0x1000},{417}),{})


if __name__=='__main__':
    unittest.main()
