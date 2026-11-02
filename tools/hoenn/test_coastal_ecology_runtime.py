"""Compile actual staged predicates and exercise their geographical boundaries."""
import ctypes
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from coastal_ecology_runtime import DEPTH_MAPS, NO_SURFACING_ROUTES, DEPTH_PREDICATE, repair


WATER_BEFORE = '''bool8 MetatileBehavior_IsWaterWildEncounter(u8 metatileBehavior)
{
    if (MetatileBehavior_IsSurfableWaterOrUnderwater(metatileBehavior) == TRUE
     && MetatileBehavior_IsEncounterTile(metatileBehavior) == TRUE)
        return TRUE;
    else
        return FALSE;
}
'''
WILD_BEFORE = '''#include "constants/weather.h"
bool8 StandardWildEncounter(u16 curMetatileBehavior, u16 prevMetatileBehavior)
{
    if (gJourneyReviewMode || sWildEncountersDisabled == TRUE)
        return FALSE;
    if (FALSE) return FALSE;
    else if (MetatileBehavior_IsWaterWildEncounter(curMetatileBehavior) == TRUE
                 || (TestPlayerAvatarFlags(PLAYER_AVATAR_FLAG_SURFING) && MetatileBehavior_IsBridgeOverWater(curMetatileBehavior) == TRUE))
        return TRUE;
}
bool8 SweetScentWildEncounter(void)
{
    if (gJourneyReviewMode) return FALSE;
    PlayerGetDestCoords(&x, &y);
    if (FALSE) return FALSE;
    else if (MetatileBehavior_IsWaterWildEncounter(MapGridGetMetatileBehaviorAt(x, y)) == TRUE)
        return TRUE;
}
'''


class RuntimePredicates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        root = Path(cls.temporary.name)
        source = root/'source'
        (source/'src').mkdir(parents=True)
        (source/'src/metatile_behavior.c').write_text(WATER_BEFORE)
        (source/'src/wild_encounter.c').write_text(WILD_BEFORE)
        class Layer:
            def __init__(self):
                self.source = source
                self.outputs = {}
                self.expected = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in source.rglob('*') if p.is_file()}
            def stage(self,path,raw):
                self.outputs[path] = raw.encode() if isinstance(raw,str) else raw
        cls.layer = Layer()
        cls.report = repair(cls.layer)
        cc = shutil.which('cc')
        if not cc:
            raise unittest.SkipTest('Native C compiler unavailable')
        water = cls.layer.outputs['src/metatile_behavior.c'].decode()
        constants = '\n'.join(f'#define {name} ((83 << 8) | {10+2*i})'
                              for i,name in enumerate(DEPTH_MAPS))
        constants += '\n' + '\n'.join(f'#define {name} ((24 << 8) | {50+i})'
                                        for i,name in enumerate(NO_SURFACING_ROUTES))
        prelude = '''typedef unsigned char bool8;
typedef unsigned char u8;
typedef unsigned short u16;
#define TRUE 1
#define FALSE 0
#define MB_NORMAL 0
#define MB_FAST_WATER 44
#define MB_NO_SURFACING 25
#define MAP_TYPE_UNDERWATER 5
struct {u8 mapType;} gMapHeader;
struct Save {struct {u8 mapGroup, mapNum;} location;} storage;
struct Save *gSaveBlock1Ptr = &storage;
static u8 openCoast;
void fixture(u8 group,u8 num,u8 type,u8 coast) {
    storage.location.mapGroup=group;storage.location.mapNum=num;
    gMapHeader.mapType=type;openCoast=coast;
}
bool8 JourneySeviiIsOpenCoast(void) {return openCoast;}
bool8 MetatileBehavior_IsSurfableWaterOrUnderwater(u8 value) {return value==21 || value==44;}
bool8 MetatileBehavior_IsEncounterTile(u8 value) {return value==21;}
'''
        c = root/'predicates.c'
        c.write_text(prelude+constants+'\n'+water+DEPTH_PREDICATE.replace('static bool8','bool8',1))
        library = root/'predicates.so'
        subprocess.run([cc,'-shared','-fPIC','-O2',str(c),'-o',str(library)],check=True,capture_output=True)
        cls.native = ctypes.CDLL(str(library))
        cls.native.fixture.argtypes = [ctypes.c_uint8]*4
        cls.native.MetatileBehavior_IsWaterWildEncounter.argtypes = [ctypes.c_uint8]
        cls.native.MetatileBehavior_IsWaterWildEncounter.restype = ctypes.c_uint8
        cls.native.JourneyCoastalDepthEncounterTile.argtypes = [ctypes.c_uint16]
        cls.native.JourneyCoastalDepthEncounterTile.restype = ctypes.c_uint8

    def test_fast_water_enabled_only_on_open_coast_and_native_ocean_preserved(self):
        for coast in (0,1):
            self.native.fixture(0,0,3,coast)
            self.assertEqual(self.native.MetatileBehavior_IsWaterWildEncounter(44),coast)
            self.assertEqual(self.native.MetatileBehavior_IsWaterWildEncounter(21),1)
            self.assertEqual(self.native.MetatileBehavior_IsWaterWildEncounter(0),0)

    def test_all_five_depth_floors_use_water_but_original_underwater_floor_stays_quiet(self):
        for index in range(5):
            self.native.fixture(83,10+index*2,5,0)
            self.assertEqual(self.native.JourneyCoastalDepthEncounterTile(0),1)
        for group,num in [(0,0),(83,20),(83,11),(24,1)]:
            self.native.fixture(group,num,5,0)
            self.assertEqual(self.native.JourneyCoastalDepthEncounterTile(0),0)

    def test_native_no_surfacing_routes_trigger_only_on_their_water_behavior(self):
        for index in range(4):
            for map_type in range(10):
                self.native.fixture(24,50+index,map_type,0)
                self.assertEqual(self.native.JourneyCoastalDepthEncounterTile(25),int(map_type==5))
                self.assertEqual(self.native.JourneyCoastalDepthEncounterTile(0),0)
            self.native.fixture(24,50+index,5,0)
            for behavior in range(256):
                self.assertEqual(self.native.JourneyCoastalDepthEncounterTile(behavior),int(behavior==25))
        for group,num in [(24,49),(24,54),(0,0),(83,10),(83,20)]:
            self.native.fixture(group,num,5,0)
            self.assertEqual(self.native.JourneyCoastalDepthEncounterTile(25),0)

    def test_depth_guard_rejects_other_map_types_and_non_floor_behaviors(self):
        for map_type in range(10):
            self.native.fixture(83,10,map_type,0)
            self.assertEqual(self.native.JourneyCoastalDepthEncounterTile(0),int(map_type==5))
        self.native.fixture(83,10,5,0)
        for behavior in range(1,256):
            self.assertEqual(self.native.JourneyCoastalDepthEncounterTile(behavior),0)

    def test_only_runtime_files_staged_and_existing_test_edition_guards_kept(self):
        self.assertEqual(set(self.layer.outputs),{'src/metatile_behavior.c','src/wild_encounter.c'})
        text = self.layer.outputs['src/wild_encounter.c'].decode()
        self.assertIn('if (gJourneyReviewMode || sWildEncountersDisabled == TRUE)\n        return FALSE;',text)
        self.assertIn('if (gJourneyReviewMode) return FALSE;\n    PlayerGetDestCoords(&x, &y);',text)
        self.assertEqual(text.count('JourneyCoastalDepthEncounterTile('),3)
        old = self.layer.outputs.copy()
        repair(self.layer)
        self.assertEqual(self.layer.outputs,old)


if __name__=='__main__':
    unittest.main()
