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
static u8 badgeCount[2];
static u8 JourneyGymBadgeCount(bool8 kanto) { return badgeCount[kanto]; }
''' + 'enum {' + ', '.join(names) + '};\n' + progression + '''
int main(void)
{
    const u16 mapBySavedVisitBit[] = {
        MAP_ROUTE4, MAP_ROUTE10, MAP_ROUTE17, MAP_ROUTE112, MAP_ROUTE113, MAP_PETALBURG_WOODS,
        MAP_ROUTE6, MAP_ROUTE13, MAP_ROUTE20, MAP_ROUTE106, MAP_ABANDONED_SHIP_DECK, MAP_ROUTE125,
    };
    const u8 chronological[][6] = {{5, 9, 3, 10, 4, 11}, {0, 6, 1, 7, 2, 8}};
    assert(ARRAY_COUNT(sJourneyCrossoverLocations) == ARRAY_COUNT(mapBySavedVisitBit));
    for (u32 index = 0; index < ARRAY_COUNT(mapBySavedVisitBit); index++)
        assert(sJourneyCrossoverLocations[index].map == mapBySavedVisitBit[index]);
    for (u16 visits = 0; visits < 4096; visits++)
    {
        for (u32 region = 0; region < 2; region++)
        {
            u32 next = 12, lowerLimit = 9;
            for (u32 i = 0; i < 6; i++)
            {
                u32 slot = chronological[region][i];
                if (!(visits & (1 << slot)))
                {
                    next = slot;
                    lowerLimit = i + 1;
                    break;
                }
            }
            assert(JourneyCrossoverNext(region, visits) == next);
            for (u32 own = 0; own <= 8; own++)
            {
                badgeCount[region] = own;
                badgeCount[!region] = 8;
                for (u32 i = 0; i < 6; i++)
                {
                    u32 slot = chronological[region][i];
                    assert(JourneyCrossoverReady(slot, visits) == (slot == next && own >= lowerLimit));
                }
            }
        }
    }
    return 0;
}
''')
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', str(source), '-o', str(program)], check=True)
            subprocess.run([str(program)], check=True)
