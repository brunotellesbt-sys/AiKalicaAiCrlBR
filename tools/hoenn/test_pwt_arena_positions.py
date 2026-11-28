"""Prevent a correct player position from certifying a missing PWT opponent."""
from copy import deepcopy
import gzip
import json
import unittest

from pwt_catalog import load
from verify_pwt_arena_positions import DIRECTORY, presentation, verify_cup


class StadiumEntrance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = DIRECTORY / 'Pokemon-Journey-Gen1-4-Normal'
        cls.evidence = json.loads(gzip.decompress((cls.folder / 'native.json.gz').read_bytes()))

    def test_final_prompt_with_old_coordinates_is_rejected(self):
        row = deepcopy(self.evidence['after'])
        row['entrance']['opponent'] = [6, -1]
        with self.assertRaises(AssertionError):
            presentation(self.folder / 'after', row, row['rom_sha256'], row['elf_sha256'], False)

    def test_each_round_needs_its_scheduled_opponent_on_the_lane(self):
        cup = self.evidence['cup']
        rows = load()
        verify_cup(cup, cup['rom_sha256'], 4, False, 1, rows)
        for key, wrong in [('catalog_id', -1), ('opponent_start', [10, -1]), ('opponent', [6, -1])]:
            changed = deepcopy(cup)
            changed['actual_battles'][-1]['entrance'][key] = wrong
            with self.subTest(key=key), self.assertRaises((AssertionError, KeyError)):
                verify_cup(changed, cup['rom_sha256'], 4, False, 1, rows)
