"""Compile the rival badge gates and check every historical visit mask."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

from prepare_crossover_badges import PROGRESSION


class CrossoverBadgesTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('cc'), 'A host C compiler is required')
    def test_regional_milestones_and_old_saves(self):
        progression = PROGRESSION.read_text()
        names = sorted(set(re.findall(r'\b(?:MAP|OBJ_EVENT_GFX)_\w+', progression)))
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'rivals.c'
            program = source.with_suffix('')
            source.write_text('''
#include <assert.h>
#include <stdint.h>
typedef uint8_t u8, bool8;
typedef uint16_t u16;
typedef uint32_t u32;
#define TRUE 1
#define FALSE 0
#define ARRAY_COUNT(a) (sizeof(a) / sizeof((a)[0]))
#define COMPOUND_STRING(name) ((const u8 *)(name))
static u8 totalBadges;
static u8 JourneyTotalBadgeCount(void) { return totalBadges; }
''' + 'enum {' + ', '.join(names) + '};\n' + progression + '''
int main(void)
{
    const u8 bits[2][4]={{0,3,2,12},{9,7,10,13}};
    const u8 thresholds[2][4]={{1,5,13,20},{2,7,11,15}};
    assert(ARRAY_COUNT(sJourneyCrossoverLocations)==8);
    for (u32 mask=0; mask<16384; mask++)
        for (u32 hero=0; hero<2; hero++)
        {
            u32 wins=0, next=8;
            for (u32 bit=0;bit<6;bit++) wins+=(mask>>(hero*6+bit))&1;
            wins+=(mask>>(12+hero))&1;
            assert(JourneyCrossoverWon(hero, mask)==wins);
            for (u32 rank=0;rank<4;rank++)
            {
                if (wins < 4 && (wins < 3 || rank==3 || (mask & (1u<<(12+hero))))
                    && !(mask & (1u<<bits[hero][rank])))
                { next=hero*4+rank; break; }
            }
            assert(JourneyCrossoverNext(hero,mask)==next);
            for (totalBadges=0; totalBadges<=24; totalBadges++)
                for (u32 rank=0;rank<4;rank++)
                    assert(JourneyCrossoverReady(hero*4+rank,mask)
                        == (next==hero*4+rank && totalBadges>=thresholds[hero][rank]));
        }
    return 0;
}
''')
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', str(source), '-o', str(program)], check=True)
            subprocess.run([str(program)], check=True)
