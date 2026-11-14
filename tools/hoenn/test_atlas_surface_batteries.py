"""Execute the emitted migration C against persisted-save fixtures.

These host fixtures test versioning and serialized records. They are not
emulator batteries or native Continue/menu-save evidence.
"""
import copy
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

from atlas_surface_batteries import migration_source, normalize_relocations


RELOCATIONS = [dict(old_map='MAP_OLD', destination_map='MAP_NEW',
                    source_rect=[0, 0, 10, 10], destination_origin=[20, 30],
                    mode='surf', elevation=1,
                    warp_relocations=[dict(old_warp_id=0, destination_warp_id=3)])]

PREFIX = r'''
#include <stdint.h>
#include <string.h>
typedef uint8_t u8; typedef uint16_t u16; typedef uint32_t u32;
typedef int16_t s16; typedef int8_t s8; typedef uint8_t bool8; typedef uint32_t bool32;
#define EWRAM_DATA
#define TRUE 1
#define FALSE 0
#define ARRAY_COUNT(x) (sizeof(x)/sizeof((x)[0]))
#define MAP_GROUP(x) ((x)>>8)
#define MAP_NUM(x) ((x)&255)
#define MAP_ONE_ISLAND_TREASURE_BEACH 0x0102
#define MAP_OLD 0x0203
#define MAP_NEW 0x0304
#define VAR_JOURNEY_SEVII_GEOMETRY_VERSION 0x40DC
#define OBJECT_EVENTS_COUNT 4
#define OBJECT_EVENT_TEMPLATES_COUNT 4
#define OBJ_EVENT_ID_FOLLOWER 250
#define OBJ_EVENT_ID_NPC_FOLLOWER 251
#define FNPC_ENABLE_NPC_FOLLOWERS 0
#define PLAYER_AVATAR_STATE_SURFING 2
#define PLAYER_AVATAR_STATE_NORMAL 0
struct Coords { s16 x,y; };
struct WarpData { s8 mapGroup,mapNum,warpId; s16 x,y; };
struct ObjectEvent {
    u8 isPlayer,active,localId,mapGroup,mapNum;
    struct Coords initialCoords,currentCoords,previousCoords;
    u8 currentElevation,previousElevation;
    u16 graphicsId; u8 spriteId;
};
struct Template { u8 localId; s16 x,y; };
struct Save {
    struct Coords pos;
    struct WarpData location,continueGameWarp,dynamicWarp,lastHealLocation,escapeWarp;
    struct ObjectEvent objectEvents[OBJECT_EVENTS_COUNT];
    struct Template objectEventTemplates[OBJECT_EVENT_TEMPLATES_COUNT];
    u16 mapView[16], mapLayoutId;
};
struct Save2 { u8 playerGender; };
struct MapHeader { u16 mapLayoutId; };
static struct Save saved; static struct Save2 saved2;
static struct Save *gSaveBlock1Ptr=&saved;
static struct Save2 *gSaveBlock2Ptr=&saved2;
static u16 version;
static u16 VarGet(u16 id) { (void)id; return version; }
static void VarSet(u16 id,u16 value) { (void)id; version=value; }
static void CpuFill16(u16 value,void *data,u32 size) { (void)value; memset(data,0,size); }
static u16 GetPlayerAvatarGraphicsIdByStateIdAndGender(u16 state,u16 gender)
{ return 0x100+state+gender; }
static const struct MapHeader *Overworld_GetMapHeaderByGroupAndId(u8 group,u8 num)
{ static struct MapHeader h={99}; (void)group; (void)num; return &h; }
'''

WRAPPERS = r'''
void reset(u16 v,u16 map,s16 x,s16 y)
{
    u32 i;
    memset(&saved,0,sizeof(saved)); version=v;
    sJourneyAtlasReloadSavedObjects=FALSE;
    saved.pos.x=x; saved.pos.y=y;
    saved.location.mapGroup=MAP_GROUP(map); saved.location.mapNum=MAP_NUM(map);
    saved.location.warpId=-1; saved.location.x=x; saved.location.y=y;
    saved.objectEvents[0].isPlayer=1; saved.objectEvents[0].active=1;
    saved.objectEvents[0].currentCoords.x=x+7; saved.objectEvents[0].currentCoords.y=y+7;
    saved.objectEvents[0].initialCoords=saved.objectEvents[0].previousCoords=saved.objectEvents[0].currentCoords;
    saved.objectEvents[1].localId=7; saved.objectEvents[1].active=1;
    saved.objectEventTemplates[0].localId=7; saved.objectEventTemplates[0].x=2;
    for(i=0;i<16;i++) saved.mapView[i]=0x1234;
    saved.continueGameWarp=saved.dynamicWarp=saved.lastHealLocation=saved.escapeWarp=saved.location;
}
void run(void) { JourneyMigrateSeviiSaveGeometry(); }
void set_event_warp(void) { saved.dynamicWarp.warpId=0; saved.dynamicWarp.x=-1; saved.dynamicWarp.y=-1; }
int get(int key)
{
    switch(key) {
    case 0:return version; case 1:return saved.pos.x; case 2:return saved.pos.y;
    case 3:return saved.location.mapGroup*256+saved.location.mapNum;
    case 4:return saved.objectEvents[0].currentCoords.x;
    case 5:return saved.objectEvents[0].currentCoords.y;
    case 6:return saved.objectEvents[0].currentElevation;
    case 7:return saved.objectEvents[1].active;
    case 8:return saved.mapView[0]; case 9:return saved.mapLayoutId;
    case 10:return saved.continueGameWarp.x; case 11:return saved.escapeWarp.y;
    case 12:return saved.dynamicWarp.mapGroup*256+saved.dynamicWarp.mapNum;
    case 13:return saved.dynamicWarp.warpId; case 14:return saved.dynamicWarp.x;
    case 15:return JourneyAtlasSavedObjectsNeedReload();
    case 16:return saved.objectEvents[0].graphicsId;
    case 17:return saved.objectEvents[0].spriteId;
    default:return -999;
    }
}
int consume(void) { return JourneyAtlasConsumeSavedObjectReload(); }
'''


class PersistedMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        root = Path(cls.temp.name)
        src = root/'migration.c'
        src.write_text(PREFIX+migration_source(RELOCATIONS)+WRAPPERS)
        subprocess.run(['gcc', '-shared', '-fPIC', '-std=gnu17', '-Wall', '-Wextra', '-Werror',
                        str(src), '-o', str(root/'migration.so')], check=True, capture_output=True)
        cls.native = ctypes.CDLL(str(root/'migration.so'))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_legacy_zero_migrates_treasure_once_and_version_one_does_not_repeat(self):
        for v, x, expected in ((0, 10, 18), (1, 18, 18), (2, 18, 18)):
            with self.subTest(version=v):
                self.native.reset(v, 0x0102, x, 5)
                self.native.run()
                self.assertEqual(self.native.get(1), expected)
                self.assertEqual(self.native.get(0), 2)
                self.native.run()
                self.assertEqual(self.native.get(1), expected)

    def test_retired_current_save_relocates_all_direct_records_and_preserved_player(self):
        self.native.reset(1, 0x0203, 4, 5)
        self.native.run()
        expected = {0:2, 1:24, 2:35, 3:0x0304, 4:31, 5:42, 6:1,
                    7:0, 8:0, 9:99, 10:24, 11:35, 15:1, 16:0x0201, 17:127}
        self.assertEqual({k:self.native.get(k) for k in expected}, expected)
        self.assertEqual(self.native.consume(), 1)
        self.assertEqual(self.native.consume(), 0)
        before = [self.native.get(k) for k in range(18)]
        self.native.run()
        self.assertEqual([self.native.get(k) for k in range(18)], before)

    def test_event_warp_ids_use_their_own_table_and_keep_unset_coordinates(self):
        self.native.reset(1, 0x0203, 4, 5)
        self.native.set_event_warp()
        self.native.run()
        self.assertEqual([self.native.get(k) for k in (12,13,14)], [0x0304,3,-1])

    def test_overlaps_and_retired_destinations_are_refused(self):
        rows = copy.deepcopy(RELOCATIONS)
        with self.assertRaisesRegex(ValueError, 'overlapping'):
            normalize_relocations(rows+rows)
        rows[0]['destination_map']='MAP_OLD'
        with self.assertRaises(ValueError):
            normalize_relocations(rows)


if __name__ == '__main__':
    unittest.main()
