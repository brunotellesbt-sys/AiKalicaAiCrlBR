"""Compile the exact ROM competition scheduler for exhaustive host checks."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


class QualifierSchedulerTests(unittest.TestCase):
    def test_every_draw_and_group_result_with_both_defeat_policies(self):
        with tempfile.TemporaryDirectory(prefix='badge-qualifier-core-') as temporary:
            directory = Path(temporary)
            (directory / 'global.h').write_text('''#include <stdint.h>
#include <string.h>
typedef uint8_t u8; typedef uint16_t u16; typedef uint32_t u32;
typedef int8_t s8; typedef int32_t s32; typedef uint8_t bool8; typedef uint32_t bool32;
#define TRUE 1
#define FALSE 0
''')
            shutil.copyfile(HERE / 'qualifier_core.h', directory / 'journey_qualifier_core.h')
            binary = directory / 'qualifier-checks'
            build = subprocess.run([
                'cc', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=undefined', '-fno-sanitize-recover=all',
                '-I', str(directory), str(HERE / 'qualifier_core.c'),
                str(HERE / 'fixture_badge_qualifier_core.c'), '-o', str(binary),
            ], capture_output=True, text=True)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            checked = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            self.assertIn('30720 tournaments passed', checked.stdout)
            self.assertIn('1000 full-tie draws', checked.stdout)


if __name__ == '__main__':
    unittest.main()
