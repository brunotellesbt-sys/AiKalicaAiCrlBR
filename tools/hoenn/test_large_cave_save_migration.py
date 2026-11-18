"""Execute the actual version8 rescue C for all 1728 changed old positions."""
import base64
import ctypes
import gzip
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import unittest

from render_sea_maps import _braced


class LargeCaveSavedPositions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=Path(__file__).parent/'data/large-cave-save-source-fixture.json.gz'
        cls.fixture=json.loads(gzip.decompress(path.read_bytes()))
        source=cls.fixture['load_save_c']
        if hashlib.sha256(source.encode()).hexdigest()!=cls.fixture['source_sha256']:
            raise ValueError('Compiled rescue C source fixture changed')
        def function(name):
            signature='static void '+name+'(void)\n{'
            start=source.index(signature)
            return signature+_braced(source,start+len(signature)-1)+'}\n'
        helper=function('JourneyRescueExpandedCavePositions')
        wrapper=function('JourneyMigrateSeviiSaveGeometry')
        names=set(re.findall(r'\bMAP_[A-Z0-9_]+\b',helper+wrapper))-{'MAP_GROUP','MAP_NUM','MAP_OFFSET'}
        defines='\n'.join('#define '+name+' '+str(cls.fixture['map_ids'][name]) for name in sorted(names))
        shim=r'''
#include <stdint.h>
#include <string.h>
typedef uint8_t u8;typedef int8_t s8;typedef uint16_t u16;typedef int16_t s16;typedef uint32_t u32;
#define TRUE 1
#define FALSE 0
#define ARRAY_COUNT(a) (sizeof(a)/sizeof((a)[0]))
#define MAP_GROUP(m) ((m)>>8)
#define MAP_NUM(m) ((m)&255)
#define MAP_OFFSET 7
#define OBJECT_EVENTS_COUNT 16
#define OBJ_EVENT_ID_FOLLOWER 0xFE
#define OBJ_EVENT_ID_NPC_FOLLOWER 0xFD
#define FNPC_ENABLE_NPC_FOLLOWERS 1
#define VAR_JOURNEY_SEVII_GEOMETRY_VERSION 0x40DC
#define CpuFill16(v,p,n) memset((p),0,(n))
struct Coords{s16 x,y;};
struct WarpData{s8 mapGroup,mapNum,warpId;s16 x,y;};
struct ObjectEvent{u8 isPlayer,localId,active;struct Coords initialCoords,currentCoords,previousCoords;};
struct Save{struct Coords pos;struct WarpData location,continueGameWarp,dynamicWarp,lastHealLocation,escapeWarp;
 struct ObjectEvent objectEvents[16];u8 objectEventTemplates[256];u16 mapView[256];u16 mapLayoutId;};
struct Save3{struct {u8 inProgress;struct Coords log;}NPCfollower;};
static struct Save saved;static struct Save3 saved3;
static struct Save *gSaveBlock1Ptr=&saved;static struct Save3 *gSaveBlock3Ptr=&saved3;
static u16 version;static int sJourneyAtlasReloadSavedObjects,older_calls;
static u16 VarGet(u16 v){return version;}
static void VarSet(u16 v,u16 x){version=x;}
static void JourneyMigrateSeviiSaveGeometryVersion7(void){older_calls++;if(version<7)version=7;}
struct MapHeader{u16 mapLayoutId;};
static const struct MapHeader *Overworld_GetMapHeaderByGroupAndId(int g,int n){static const struct MapHeader h={42};return &h;}
'''
        driver=r'''
static void put_warp(struct WarpData *w,int map,int x,int y,int event){w->mapGroup=map>>8;w->mapNum=map&255;w->warpId=event?5:-1;w->x=x;w->y=y;}
void run_case(int map,int x,int y,int oldversion,int event,int *out)
{
 unsigned i,k=0;struct WarpData *warps[]={&saved.continueGameWarp,&saved.dynamicWarp,&saved.lastHealLocation,&saved.escapeWarp};
 memset(&saved,0,sizeof(saved));memset(&saved3,0,sizeof(saved3));version=oldversion;older_calls=0;sJourneyAtlasReloadSavedObjects=0;
 saved.pos=(struct Coords){x,y};put_warp(&saved.location,map,x,y,0);
 put_warp(warps[0],map,x,y,event);put_warp(warps[1],map,x,y,event);
 put_warp(warps[2],0,x,y,0);put_warp(warps[3],map,-1,-1,1);
 for(i=0;i<4;i++){
  saved.objectEvents[i].active=1;saved.objectEvents[i].isPlayer=i==0;
  saved.objectEvents[i].localId=i==1?0xFE:i==2?0xFD:3;
  saved.objectEvents[i].initialCoords=saved.objectEvents[i].currentCoords=saved.objectEvents[i].previousCoords=(struct Coords){x+7+i,y+7+i};
 }
 memset(saved.objectEventTemplates,0xAA,sizeof(saved.objectEventTemplates));
 for(i=0;i<256;i++)saved.mapView[i]=0xCAFE;
 saved3.NPCfollower.inProgress=1;saved3.NPCfollower.log=(struct Coords){x+3,y+3};saved.mapLayoutId=11;
 JourneyMigrateSeviiSaveGeometry();
 out[k++]=saved.pos.x;out[k++]=saved.pos.y;out[k++]=saved.location.x;out[k++]=saved.location.y;
 out[k++]=saved.location.warpId;out[k++]=version;out[k++]=saved.mapLayoutId;out[k++]=sJourneyAtlasReloadSavedObjects;
 for(i=0;i<3;i++){
  out[k++]=saved.objectEvents[i].initialCoords.x;out[k++]=saved.objectEvents[i].initialCoords.y;
  out[k++]=saved.objectEvents[i].currentCoords.x;out[k++]=saved.objectEvents[i].currentCoords.y;
  out[k++]=saved.objectEvents[i].previousCoords.x;out[k++]=saved.objectEvents[i].previousCoords.y;
 }
 out[k++]=saved3.NPCfollower.log.x;out[k++]=saved3.NPCfollower.log.y;
 for(i=0;i<4;i++){out[k++]=warps[i]->x;out[k++]=warps[i]->y;}
 for(i=0;i<4;i++)out[k++]=saved.objectEvents[i].active;
 out[k++]=saved.mapView[0];out[k++]=saved.mapView[255];out[k++]=older_calls;
 out[k++]=saved.objectEvents[3].currentCoords.x;out[k++]=saved.objectEvents[3].currentCoords.y;
 out[k++]=saved.objectEventTemplates[0];
}
'''
        cls.temp=tempfile.TemporaryDirectory(prefix='actual-large-cave-rescue-c-')
        cls.addClassCleanup(cls.temp.cleanup)
        root=Path(cls.temp.name);code=root/'rescue.c';code.write_text(shim+'\n'+defines+'\n'+helper+wrapper+driver)
        subprocess.run(['cc','-O2','-fPIC','-shared','-Wall','-Werror',str(code),'-o',str(root/'rescue.so')],check=True,capture_output=True)
        cls.lib=ctypes.CDLL(str(root/'rescue.so'))
        cls.lib.run_case.argtypes=[ctypes.c_int]*5+[ctypes.POINTER(ctypes.c_int)]
        cls.maps={name:dict(row,old=struct.unpack('<1089H',base64.b64decode(row['old'])),new=struct.unpack('<1089H',base64.b64decode(row['new']))) for name,row in cls.fixture['maps'].items()}

    def run_case(self,map_id,x,y,version=7,event=0):
        out=(ctypes.c_int*64)();self.lib.run_case(map_id,x,y,version,event,out)
        return list(out)

    def test_every_invalid_old_cell_has_exactly_one_same_mode_local_refuge(self):
        expected={}
        for name,row in self.maps.items():
            for i,(old,new) in enumerate(zip(row['old'],row['new'])):
                if old&0xC00:
                    continue
                if new&0xC00 or (old>>12==1)!=(new>>12==1):
                    expected[name,i%33,i//33]=old>>12==1
        declared={(r['map'].removeprefix('MAP_'),*r['from_tile']):r for r in self.fixture['rescues']}
        translated={(name,*r['from_tile']):r for name in self.maps for r in self.fixture['rescues'] if r['map']=='MAP_'+name.upper()}
        self.assertEqual(len(declared),1728)
        self.assertEqual(set(expected),set(translated))
        for key,surfing in expected.items():
            r=translated[key];row=self.maps[key[0]];x,y=r['to_tile'];word=row['new'][y*33+x]
            self.assertFalse(word&0xC00,key);self.assertEqual(word>>12==1,surfing,key)
            self.assertNotEqual([x,y],row['entrance'])
            if surfing:
                self.assertTrue(any(yy==y and a<=x<b for yy,a,b in row['water_runs']),key)

    def test_actual_C_moves_all1728_positions_once_and_keeps_followers_and_native_IDs(self):
        ids=self.fixture['map_ids']
        for r in self.fixture['rescues']:
            x,y=r['from_tile'];tx,ty=r['to_tile'];out=self.run_case(ids[r['map']],x,y)
            self.assertEqual(out[:8],[tx,ty,tx,ty,-1,8,42,1],r)
            for slot in range(3):
                self.assertEqual(out[8+6*slot:14+6*slot],[tx+7+slot,ty+7+slot]*3,r)
            self.assertEqual(out[26:36],[tx+3,ty+3,tx,ty,tx,ty,x,y,-1,-1],r)
            self.assertEqual(out[36:43],[1,1,1,0,0,0,1],r)
            self.assertEqual(out[43:46],[x+10,y+10,0],r)

    def test_event_warp_IDs_and_unset_coordinates_are_preserved(self):
        for r in self.fixture['rescues'][::31]:
            x,y=r['from_tile'];out=self.run_case(self.fixture['map_ids'][r['map']],x,y,event=1)
            self.assertEqual(out[28:36],[x,y,x,y,x,y,-1,-1],r)

    def test_current_and_future_versions_do_not_reapply_translation_or_refresh(self):
        for version in (8,9,0xFFFF):
            for r in self.fixture['rescues'][::17]:
                x,y=r['from_tile'];out=self.run_case(self.fixture['map_ids'][r['map']],x,y,version)
                self.assertEqual(out[:8],[x,y,x,y,-1,version,11,0],r)
                self.assertEqual(out[36:43],[1,1,1,1,0xCAFE,0xCAFE,0],r)
                self.assertEqual(out[45],0xAA)

    def test_unrelated_native_map_keeps_objects_positions_and_followers(self):
        out=self.run_case(0,12,14)
        self.assertEqual(out[:8],[12,14,12,14,-1,8,11,0])
        self.assertEqual(out[26:36],[15,17,12,14,12,14,12,14,-1,-1])
        self.assertEqual(out[36:43],[1,1,1,1,0,0,1])
