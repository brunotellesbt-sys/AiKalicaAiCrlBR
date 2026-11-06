"""Exercise connected scenery spawning against a small native C object harness."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from sevii_boundary_scenery_actor import C_HELPER, PATH, repair

HARNESS = r'''
#include <assert.h>
#include <stddef.h>
#include <stdint.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int16_t s16;
typedef int32_t s32;
#define CONNECTION_SOUTH 1
#define CONNECTION_NORTH 2
#define CONNECTION_WEST 3
#define CONNECTION_EAST 4
#define MAP_OFFSET 7
#define MAP_OFFSET_W 15
#define MAP_OFFSET_H 14
#define OBJECT_EVENTS_COUNT 16
#define OBJ_EVENT_GFX_JOURNEY_COAST_BOUNDARY_ROCK 177
struct ObjectEventTemplate {u8 localId; u16 graphicsId; s16 x,y; u16 flagId;};
struct MapLayout {s32 width,height;};
struct MapEvents {u8 objectEventCount; const struct ObjectEventTemplate *objectEvents;};
struct MapConnection {u8 direction; s32 offset; u8 mapGroup,mapNum;};
struct MapConnections {s32 count; const struct MapConnection *connections;};
struct MapHeader {const struct MapLayout *mapLayout; const struct MapEvents *events; const struct MapConnections *connections;};
struct SaveBlock {struct {s16 x,y;} pos;};
static struct SaveBlock saveBlock, *gSaveBlock1Ptr=&saveBlock;
static struct MapHeader gMapHeader, incoming;
static struct ObjectEventTemplate templates[2], captured;
static struct MapEvents events={2,templates};
static struct MapLayout here={16,13}, there={24,20};
static struct MapConnection connection={CONNECTION_EAST,-7,37,12};
static struct MapConnections connections={1,&connection};
static u8 active=0, capturedNum,capturedGroup;
static s16 capturedCameraX,capturedCameraY;
static int calls=0, hidden=0;
static const struct MapHeader *GetMapHeaderFromConnection(const struct MapConnection *c) {assert(c==&connection);return &incoming;}
static int FlagGet(u16 flag) {return flag && hidden;}
static u8 GetObjectEventIdByLocalIdAndMap(u8 id,u8 num,u8 group) {assert(id==4&&num==12&&group==37);return active?1:OBJECT_EVENTS_COUNT;}
static void TrySpawnObjectEventTemplate(const struct ObjectEventTemplate *t,u8 num,u8 group,s16 cameraX,s16 cameraY) {
 assert(!active);active=1;calls++;captured=*t;capturedNum=num;capturedGroup=group;capturedCameraX=cameraX;capturedCameraY=cameraY;
}
'''

CASES = r'''
int main(void) {
 incoming=(struct MapHeader){&there,&events,NULL};
 gMapHeader=(struct MapHeader){&here,NULL,&connections};
 templates[0]=(struct ObjectEventTemplate){4,177,0,7,0};
 templates[1]=(struct ObjectEventTemplate){5,23,0,7,0};
 saveBlock.pos.x=15;saveBlock.pos.y=1;
 JourneySpawnConnectedCoastScenery(31,-2);
 assert(calls==1&&captured.x==16&&captured.y==0);
 assert(captured.localId==4&&capturedNum==12&&capturedGroup==37);
 assert(capturedCameraX==31&&capturedCameraY==-2);
 assert(templates[0].x==0&&templates[0].y==7);
 // Repeated camera updates, including a return from the owning map, retain one identity.
 JourneySpawnConnectedCoastScenery(0,0); assert(calls==1);
 // Native range removal frees that same identity; a later fresh approach respawns it.
 active=0;saveBlock.pos.x=0;
 JourneySpawnConnectedCoastScenery(0,0);assert(calls==1);
 saveBlock.pos.x=15;JourneySpawnConnectedCoastScenery(0,0);assert(calls==2);
 // Existing event hide flags are respected before a neighboring spawn.
 active=0;templates[0].flagId=6;hidden=1;
 JourneySpawnConnectedCoastScenery(0,0);assert(calls==2);
 hidden=0;JourneySpawnConnectedCoastScenery(0,0);assert(calls==3);
 // West, north and south offsets transform the immutable donor coordinates.
 active=0;connection.direction=CONNECTION_WEST;connection.offset=3;
 templates[0].x=23;templates[0].y=1;saveBlock.pos.x=0;saveBlock.pos.y=4;
 JourneySpawnConnectedCoastScenery(0,0);assert(calls==4&&captured.x==-1&&captured.y==4);
 active=0;connection.direction=CONNECTION_NORTH;connection.offset=-3;
 templates[0].x=4;templates[0].y=19;saveBlock.pos.x=1;saveBlock.pos.y=0;
 JourneySpawnConnectedCoastScenery(0,0);assert(calls==5&&captured.x==1&&captured.y==-1);
 active=0;connection.direction=CONNECTION_SOUTH;connection.offset=5;
 templates[0].x=1;templates[0].y=0;saveBlock.pos.x=6;saveBlock.pos.y=12;
 JourneySpawnConnectedCoastScenery(0,0);assert(calls==6&&captured.x==6&&captured.y==13);
 // Vertical transitions and absent connections cannot acquire unrelated actors.
 active=0;connection.direction=5;JourneySpawnConnectedCoastScenery(0,0);assert(calls==6);
 gMapHeader.connections=NULL;JourneySpawnConnectedCoastScenery(0,0);assert(calls==6);
 return 0;
}
'''


class SceneryActorTests(unittest.TestCase):
    def test_native_coordinates_flags_identity_and_view_range(self):
        with tempfile.TemporaryDirectory(prefix='coast-scenery-unit-', dir='/tmp') as directory:
            directory = Path(directory)
            fixture = directory/'fixture.c'
            fixture.write_text(HARNESS+C_HELPER+CASES)
            subprocess.run(['cc', '-std=c99', '-Wall', '-Wextra', '-Werror', str(fixture),
                            '-o', str(directory/'fixture')], check=True, capture_output=True)
            subprocess.run([str(directory/'fixture')], check=True, capture_output=True)

    def test_repair_keeps_the_current_map_spawn_and_original_template(self):
        mapping = {'object_events':[{'graphics_id':'OTHER'}]*3+[dict(graphics_id='OBJ_EVENT_GFX_JOURNEY_COAST_BOUNDARY_ROCK',
            x=0,y=7,elevation=1,movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,
            movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',script='0',flag='0')]}
        original = ('void TrySpawnObjectEvents(s16 cameraX, s16 cameraY)\n'
                    '{\n    NativeCurrentMapSpawn();\n}\n\nvoid RemoveObjectEventsOutsideView(void)\n{}\n')
        class Layer:
            outputs = {'data/maps/OneIsland_Frlg/map.json':json.dumps(mapping).encode(), PATH:original.encode()}
            def stage(self, path, raw): self.outputs[path] = raw.encode() if isinstance(raw,str) else raw
        layer = Layer()
        result = repair(layer)
        modified = layer.outputs[PATH].decode()
        self.assertIn('NativeCurrentMapSpawn();', modified)
        self.assertEqual(modified.count('JourneySpawnConnectedCoastScenery(cameraX, cameraY);'), 1)
        self.assertEqual(json.loads(layer.outputs['data/maps/OneIsland_Frlg/map.json']), mapping)
        self.assertTrue(result['save_structure_and_event_ids_unchanged'])
        self.assertEqual(result['source_before_sha256'], hashlib.sha256(original.encode()).hexdigest())


if __name__ == '__main__':
    unittest.main()
