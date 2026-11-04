"""The door must establish a foot level without changing the Surf underpass."""
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

from coastal_followup_pier import BRIDGE_HELPER, RECOVERY_OLD, RECOVERY_NEW, repair


class CinnabarDoor(unittest.TestCase):
    def test_door_level_changes_without_erasing_bridge_or_warp(self):
        with tempfile.TemporaryDirectory() as directory:
            class Layer:
                source = Path(directory)
                outputs = {}
                expected = {}
                def stage(self, name, data):
                    self.outputs[name] = data.encode() if isinstance(data, str) else data
            layer = Layer()
            words = [0x112B]*(24*20)
            words[14*24+7] = 0x03F6
            words[15*24+6:15*24+12] = [0xF3F8, *[0xF3F9]*4, 0xF3FA]
            movement = '''enum Collision GetCollisionAtCoords(struct ObjectEvent *objectEvent, s16 x, s16 y, enum Direction dir)
{
    u8 currentBehavior = MapGridGetMetatileBehaviorAt(objectEvent->currentCoords.x, objectEvent->currentCoords.y);
    u8 nextBehavior = MapGridGetMetatileBehaviorAt(x, y);
    enum Collision collision;
}
// The whole dry approach must stay above the adjacent high quay, too.
void update(void) {
    JourneyDewfordBridgeRestoreLevel(objEvent);
}
'''
            files = {
                'data/layouts/layouts.json': json.dumps({'layouts':[{'id':'CINNABAR','width':24,'height':20,'blockdata_filepath':'data/map.bin'}]}).encode(),
                'data/maps/CinnabarIsland_Frlg/map.json': json.dumps({'layout':'CINNABAR','warp_events':[{'x':7,'y':14,'dest_map':'MAP_JOURNEY_CINNABAR_HARBOR'}]}).encode(),
                'data/map.bin': struct.pack('<'+'H'*len(words), *words),
                'src/overworld.c': ('before\n'+RECOVERY_OLD+'\nremaining guarded recovery').encode(),
                'src/event_object_movement.c': movement.encode(),
            }
            for name, raw in files.items():
                p=layer.source/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
                layer.expected[name]=hashlib.sha256(raw).hexdigest()
            report=repair(layer)
            result=struct.unpack('<'+'H'*len(words),layer.outputs['data/map.bin'])
            self.assertEqual([(i,a,b) for i,(a,b) in enumerate(zip(words,result)) if a!=b],[(14*24+7,0x03F6,0x33F6)])
            self.assertEqual(set(layer.outputs),{'data/map.bin','src/overworld.c','src/event_object_movement.c'})
            self.assertEqual(layer.outputs['src/overworld.c'].decode().replace(RECOVERY_NEW,RECOVERY_OLD),files['src/overworld.c'].decode())
            self.assertTrue(report['door']['behavior_graphics_and_warp_unchanged'])
            self.assertEqual((layer.source/'data/map.bin').read_bytes(),files['data/map.bin'])

    def test_native_bridge_recovery_is_limited_to_invalid_old_pedestrians(self):
        compiler=shutil.which('cc')
        self.assertIsNotNone(compiler)
        declarations='''#include <assert.h>
typedef short s16;
#define MAP_OFFSET 7
#define ELEVATION_TRANSITION 0
#define ELEVATION_DEFAULT 3
#define ELEVATION_MULTI_LEVEL 15
#define PLAYER_AVATAR_FLAG_ON_FOOT 1
#define PLAYER_AVATAR_FLAG_SURFING 8
#define MAP_CINNABAR_ISLAND 0x2405
#define MAP_GROUP(x) ((x)>>8)
#define MAP_NUM(x) ((x)&255)
struct ObjectEvent {int isPlayer,currentElevation,previousElevation; struct {s16 x,y;} currentCoords;};
struct {int flags;} gPlayerAvatar;
struct Save {struct {int mapGroup,mapNum;} location;} saved;
struct Save *gSaveBlock1Ptr=&saved;
int height=15,behavior=0x71;
int MapGridGetElevationAt(int x,int y){return height;}
int MapGridGetMetatileBehaviorAt(int x,int y){return behavior;}
int MetatileBehavior_IsBridgeOverWater(int b){return b==0x71;}
'''
        cases='''int main(void){
 for(int test=0;test<12;test++){
  struct ObjectEvent actor={1,0,0,{14,22}};
  gPlayerAvatar.flags=1;saved.location.mapGroup=0x24;saved.location.mapNum=5;height=15;behavior=0x71;
  switch(test){case 1:actor.isPlayer=0;break;case 2:actor.currentElevation=1;break;
   case 3:actor.currentElevation=3;break;case 4:gPlayerAvatar.flags=8;break;
   case 5:gPlayerAvatar.flags=9;break;case 6:saved.location.mapNum=6;break;
   case 7:actor.currentCoords.x=12;break;case 8:actor.currentCoords.y=23;break;
   case 9:height=3;break;case 10:behavior=0;break;case 11:saved.location.mapGroup=0x25;break;}
  int before=actor.currentElevation,previous=actor.previousElevation;
  JourneyCinnabarLegacyBridgeLevel(&actor);
  assert(actor.currentElevation==(test==0?3:before));
  assert(actor.previousElevation==(test==0?3:previous));
 }
 return 0;
}
'''
        with tempfile.TemporaryDirectory() as directory:
            c=Path(directory)/'check.c';binary=Path(directory)/'check'
            c.write_text(declarations+BRIDGE_HELPER+cases)
            subprocess.run([compiler,'-std=c11',str(c),'-o',str(binary)],check=True,capture_output=True)
            subprocess.run([str(binary)],check=True,capture_output=True)


if __name__=='__main__':unittest.main()
