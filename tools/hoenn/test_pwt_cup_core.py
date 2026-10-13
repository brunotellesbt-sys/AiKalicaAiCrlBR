"""Exercise the exact cup scheduler compiled for host, with UB checking."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent

class CupSchedulerTests(unittest.TestCase):
    def test_every_entrant_count_and_elimination_path(self):
        with tempfile.TemporaryDirectory(prefix='pwt-cup-') as folder:
            directory = Path(folder)
            (directory/'global.h').write_text('''#include <stdint.h>
#include <string.h>
typedef uint8_t u8; typedef uint16_t u16; typedef uint32_t u32;
typedef int8_t s8; typedef int32_t s32; typedef uint8_t bool8; typedef uint32_t bool32;
#define TRUE 1
#define FALSE 0
#define ARRAY_COUNT(a) (sizeof(a)/sizeof((a)[0]))
#define max(a,b) ((a)>(b)?(a):(b))
''')
            (directory/'random.h').write_text('u16 Random(void);\n')
            shutil.copyfile(HERE/'pwt_cup.h', directory/'journey_pwt_cup.h')
            binary = directory/'cup-checks'
            build = subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror',
                                    '-fsanitize=undefined','-fno-sanitize-recover=all',
                                    '-I',str(directory),str(HERE/'pwt_cup.c'),
                                    str(HERE/'fixture_pwt_cup_core.c'),'-o',str(binary)],
                                   text=True,capture_output=True)
            self.assertEqual(build.returncode,0,build.stdout+build.stderr)
            checked = subprocess.run([str(binary)],text=True,capture_output=True)
            self.assertEqual(checked.returncode,0,checked.stdout+checked.stderr)
            self.assertIn('5020 tournaments passed',checked.stdout)

if __name__ == '__main__':
    unittest.main()
