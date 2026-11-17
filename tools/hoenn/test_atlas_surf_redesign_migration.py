"""Execute the emitted version4 save wrapper, including old-NPC overlap."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

from atlas_surf_redesign_migration import wrapper


class RedesignRestore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary=tempfile.TemporaryDirectory();p=Path(cls.temporary.name)
        code=r'''
#include <stdint.h>
#include <string.h>
typedef uint8_t u8;typedef int8_t s8;typedef uint16_t u16;typedef uint32_t u32;
#define FALSE 0
#define TRUE 1
#define ARRAY_COUNT(a) (sizeof(a)/sizeof((a)[0]))
#define OBJECT_EVENTS_COUNT 4
#define OBJ_EVENT_ID_FOLLOWER 253
#define OBJ_EVENT_ID_NPC_FOLLOWER 254
#define MAP_OFFSET 7
#define VAR_JOURNEY_SEVII_GEOMETRY_VERSION 1
#define FNPC_ENABLE_NPC_FOLLOWERS 0
struct Coords {int x,y;};
struct WarpData {s8 mapGroup,mapNum,warpId;int x,y;};
struct ObjectEvent {int isPlayer,localId,active;struct Coords initialCoords,currentCoords,previousCoords;};
struct Save {struct WarpData location,continueGameWarp,dynamicWarp,lastHealLocation,escapeWarp;
 struct Coords pos;struct ObjectEvent objectEvents[4];u8 objectEventTemplates[32],mapView[32],flags[32];u16 mapLayoutId;};
static struct Save save;static struct Save *gSaveBlock1Ptr=&save;
static int version,oldCalls,sJourneyAtlasReloadSavedObjects;
struct Header {u16 mapLayoutId;};static const struct Header header={123};
static const struct Header *Overworld_GetMapHeaderByGroupAndId(int group,int number){(void)group;(void)number;return &header;}
static int VarGet(int id){(void)id;return version;}
static void VarSet(int id,int value){(void)id;version=value;}
#define CpuFill16(v,d,n) memset(d,v,n)
static void JourneyMigrateSeviiSaveGeometryVersion3(void){if(version<3){oldCalls++;version=3;}}
'''+wrapper([23040,23041],[(23040,4,5,-1,0)])+r'''
void setup(int v,int map,int x,int y,int warpId){
 int i;memset(&save,0,sizeof(save));version=v;oldCalls=0;sJourneyAtlasReloadSavedObjects=0;
 save.location=(struct WarpData){map>>8,map&255,-1,111,112};save.pos=(struct Coords){x,y};
 save.continueGameWarp=(struct WarpData){map>>8,map&255,warpId,x,y};save.dynamicWarp=save.continueGameWarp;
 save.lastHealLocation=(struct WarpData){-1,-1,-1,-1,-1};save.escapeWarp=(struct WarpData){map>>8,map&255,-1,-1,-1};
 for(i=0;i<4;i++) {save.objectEvents[i].active=1;save.objectEvents[i].localId=i;
 save.objectEvents[i].initialCoords=save.objectEvents[i].currentCoords=save.objectEvents[i].previousCoords=(struct Coords){70+i,80+i};}
 save.objectEvents[0].isPlayer=1;save.objectEvents[1].localId=253;save.objectEvents[2].localId=254;
 memset(save.objectEventTemplates,0xAA,32);memset(save.mapView,0xBB,32);memset(save.flags,0xCC,32);
}
void restore(void){JourneyMigrateSeviiSaveGeometry();}
int field(int id){switch(id){case 0:return version;case 1:return oldCalls;case 2:return save.pos.x;case 3:return save.pos.y;
 case 4:return sJourneyAtlasReloadSavedObjects;case 5:return save.objectEvents[3].active;
 case 6:return save.objectEvents[0].currentCoords.x;case 7:return save.objectEvents[1].currentCoords.x;
 case 8:return save.continueGameWarp.x;case 9:return save.lastHealLocation.x;case 10:return save.escapeWarp.x;
 case 11:return save.objectEventTemplates[0];case 12:return save.mapView[0];case 13:return save.location.x;
 case 14:return save.flags[0];default:return -999;}}
'''
        (p/'probe.c').write_text(code)
        subprocess.run(['gcc','-std=gnu89','-shared','-fPIC','-Wall','-Wextra','-Werror',str(p/'probe.c'),'-o',str(p/'probe.so')],check=True,capture_output=True)
        cls.lib=ctypes.CDLL(str(p/'probe.so'));cls.lib.setup.argtypes=[ctypes.c_int]*5;cls.lib.field.argtypes=[ctypes.c_int]

    @classmethod
    def tearDownClass(cls):cls.temporary.cleanup()

    def test_old_geometry_runs_once_then_current_NPC_overlap_is_rescued(self):
        for version in (0,1,2,3):
            self.lib.setup(version,23040,4,5,-1);self.lib.restore();f=self.lib.field
            self.assertEqual([f(i) for i in (0,1,2,3,4,5)],[4,int(version<3),3,5,1,0])
            self.assertEqual(f(6),10)  # Player coordinates use authoritative saved pos.
            self.assertEqual(f(7),70)  # Follower keeps its relative offset.
            self.assertEqual([f(i) for i in (8,9,10,11,12,13,14)],[3,-1,-1,0,0,3,0xCC])
            before=[f(i) for i in range(15)];self.lib.restore()
            self.assertEqual([f(i) for i in range(15)],before)

    def test_future_saves_and_unrelated_native_NPCs_are_preserved(self):
        for version in (4,5,65535):
            self.lib.setup(version,23040,4,5,-1);before=[self.lib.field(i) for i in range(15)]
            self.lib.restore();self.assertEqual([self.lib.field(i) for i in range(15)],before)
        self.lib.setup(3,7,4,5,-1);self.lib.restore()
        self.assertEqual([self.lib.field(i) for i in (0,1,2,4,5,11,12,14)],[4,0,4,0,1,0xAA,0,0xCC])

    def test_event_warps_keep_their_native_ID_and_unset_positions_stay_unset(self):
        self.lib.setup(3,23040,4,5,2);self.lib.restore()
        self.assertEqual(self.lib.field(8),4)
        self.assertEqual(self.lib.field(9),-1);self.assertEqual(self.lib.field(10),-1)


if __name__=='__main__':unittest.main()
