"""Dry island encounters cannot spill into other maps, water or heights."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

from atlas_sand_habitats import SCENES, CALL, function, verify_hooks


class SandHabitatGuards(unittest.TestCase):
    def test_compiled_predicate_restricts_map_behavior_and_elevation(self):
        codes={s:0x5A00+i for i,s in enumerate(SCENES)}
        prefix='typedef unsigned short u16;typedef unsigned char u8;typedef unsigned int bool32;\n'
        prefix+='#define TRUE 1\n#define FALSE 0\n#define MB_SAND 33\n'
        prefix+=''.join('#define MAP_JOURNEYATLASSCENE%03d %d\n' % (s,n) for s,n in codes.items())
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'land.c';library=source.with_suffix('.so')
            source.write_text(prefix+function())
            subprocess.run(['cc','-Wall','-Wextra','-Werror','-shared','-fPIC',str(source),'-o',str(library)],check=True)
            query=ctypes.CDLL(str(library)).JourneyAtlasLandEncounter
            for number in range(65536):
                self.assertEqual(bool(query(number,33,3)),number in codes.values())
            for number in codes.values():
                for behavior in range(512):
                    for height in range(16):
                        self.assertEqual(bool(query(number,behavior,height)),behavior==33 and height==3)

    def test_both_real_call_sites_are_required(self):
        hooks='\n'.join('if (MetatileBehavior_IsLandWildEncounter('+b+') == TRUE\n'
                         '            || '+CALL % b+')'
                         for b in ('curMetatileBehavior','MapGridGetMetatileBehaviorAt(x, y)'))
        verify_hooks(hooks)
        for old in ('PlayerGetElevation()', 'curMetatileBehavior', 'MapGridGetMetatileBehaviorAt(x, y)'):
            with self.assertRaises(ValueError):
                verify_hooks(hooks.replace(old,'0'))
