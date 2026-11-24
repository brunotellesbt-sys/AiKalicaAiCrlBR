"""Verify the mandatory rescue against the five reproduced ROMs."""
import unittest

from verify_sootopolis_rescue import verify


class SootopolisRescue(unittest.TestCase):
    def test_edition_patches_bind_the_native_hoenn_gate_and_rescue(self):
        self.assertEqual(len(verify()['editions']), 5)
