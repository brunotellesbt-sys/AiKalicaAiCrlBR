"""Execute physical-halo C against independent cell and topology oracles.

Engine shims model headers/connections; this does not prove ROM behavior.
"""
import ctypes
import json
from pathlib import Path
import random
import shutil
import subprocess
import tempfile
import unittest

from atlas_surf_physical import stage
from atlas_surf_runtime import render_runtime


PLAN = dict(scale=8, chunks=[
    dict(name='A', group='Atlas', number=0, origin=[8, 8], width=2, height=2),
    dict(name='B', group='Atlas', number=1, origin=[10, 8], width=3, height=2),
    dict(name='D', group='Atlas', number=2, origin=[10, 10], width=2, height=2),
    dict(name='W', group='Atlas', number=3, origin=[7, 8], width=1, height=2)])


class FixtureLayer:
    def __init__(self):
        self.outputs = {
            'data/maps/map_groups.json': json.dumps(dict(group_order=['Native', 'Atlas'],
                                                         Native=['Coast'], Atlas=['A', 'B', 'D', 'W'])).encode(),
            'data/layouts/layouts.json': json.dumps(dict(layouts=[dict(id='LAYOUT_'+n) for n in ['Coast', 'A', 'B', 'D', 'W']])).encode(),
            'src/fieldmap.c': b'''#include "global.h"
#include "data/journey_atlas_runtime.h"
#include "wild_encounter.h"
static void InitBackupMapLayoutConnections(struct MapHeader *mapHeader);
void InitMap(struct MapHeader *mapHeader) {
        InitBackupMapLayoutConnections(mapHeader);
}
static void FillConnection(int x, int y, struct MapHeader const *connectedMapHeader, int x2, int y2, int width, int height)
{
    int mapWidth;
    mapWidth = connectedMapHeader->mapLayout->width;
    LegacyCopy();
}
enum Connection GetMapBorderIdAt(int x, int y)
{
    return LegacyBorder(x, y);
}
'''}
        self.outputs.update({f'data/maps/{n}/map.json': json.dumps(dict(layout='LAYOUT_'+n)).encode()
                             for n in ['A', 'B', 'D', 'W']})

    def stage(self, path, content):
        self.outputs[path] = content.encode() if isinstance(content, str) else content


SHIMS = r'''
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <assert.h>
typedef uint8_t u8; typedef uint16_t u16; typedef uint32_t u32;
typedef int16_t s16; typedef int32_t s32; typedef u8 bool8;
#define TRUE 1
#define FALSE 0
#define ARRAY_COUNT(a) (sizeof(a)/sizeof((a)[0]))
#define MAPGRID_UNDEFINED 0x3FF
#define MAPGRID_METATILE_ID_MASK 0x3FF
#define MAP_OFFSET 7
enum Connection { CONNECTION_NONE, CONNECTION_SOUTH, CONNECTION_NORTH, CONNECTION_WEST, CONNECTION_EAST };
struct MapLayout { int width, height; const u16 *map; int isFrlg; const void *primaryTileset, *secondaryTileset; };
struct MapConnection { int direction, offset; u8 mapGroup, mapNum; };
struct MapConnections { int count; const struct MapConnection *connections; };
struct MapHeader { const struct MapLayout *mapLayout; int mapLayoutId; const struct MapConnections *connections; };
struct Backup { int width, height; u16 *map; } gBackupMapLayout;
static u16 wordsA[] = {0x112B,0x112B,0x112B,0x112B};
static u16 wordsB[] = {0x15F9,0x1170,0x1170,0x1170,0x1170,0x1170};
static u16 wordsD[] = {0x312B,0x012B,0x1C43,0x012B};
static u16 wordsW[] = {0x15F9,0x15F9};
static u16 wordsCoast[] = {0x3000,0x3C00};
static struct MapLayout layouts[] = {
    {1,2,wordsCoast,1,(void*)1,(void*)1},
    {2,2,wordsA,1,(void*)1,(void*)1},
    {3,2,wordsB,1,(void*)1,(void*)1},
    {2,2,wordsD,1,(void*)1,(void*)1},
    {1,2,wordsW,1,(void*)1,(void*)1}
};
static struct MapConnection links[] = {{CONNECTION_WEST,0,0,0}, {CONNECTION_EAST,0,1,1}};
static struct MapConnections connections = {2,links};
static struct MapHeader headers[] = {{&layouts[0],1,NULL},{&layouts[1],2,&connections},
    {&layouts[2],3,NULL},{&layouts[3],4,NULL},{&layouts[4],5,NULL}};
struct MapHeader gMapHeader;
static u16 backup[17*16];
static const struct MapHeader *Overworld_GetMapHeaderByGroupAndId(int group,int number) {
    assert((group==0 && number==0)||(group==1 && number>=0 && number<4));
    return &headers[group==0 ? 0 : number+1];
}
static bool8 JourneyMarineViewCompatible(const struct MapLayout *from,u16 word,u16 *result) {
    if (from->primaryTileset == (void*)99) return FALSE;
    *result = from->isFrlg == gMapHeader.mapLayout->isFrlg ? (word&1023) : 0x170;
    return TRUE;
}
static bool8 JourneyMarineConnectionOrigin(const struct MapLayout *from,
    const struct MapConnection *c,const struct MapHeader **next,s32 *x,s32 *y) {
    *next = Overworld_GetMapHeaderByGroupAndId(c->mapGroup,c->mapNum); *x=*y=0;
    switch(c->direction) {
        case CONNECTION_WEST: *x=-(*next)->mapLayout->width; *y=c->offset;break;
        case CONNECTION_EAST: *x=from->width; *y=c->offset;break;
        case CONNECTION_NORTH:*x=c->offset;*y=-(*next)->mapLayout->height;break;
        case CONNECTION_SOUTH:*x=c->offset;*y=from->height;break;
        default:return FALSE;
    } return TRUE;
}
static const struct MapConnection *GetIncomingConnection(enum Connection dir,int x,int y) {
    int i, axis, limit;
    const struct MapConnection *c;
    const struct MapHeader *next;
    for(i=0;i<gMapHeader.connections->count;i++) {
        c=&gMapHeader.connections->connections[i];
        if(c->direction!=(int)dir)continue;
        next=Overworld_GetMapHeaderByGroupAndId(c->mapGroup,c->mapNum);
        axis=(dir==CONNECTION_WEST||dir==CONNECTION_EAST)?y:x;
        limit=(dir==CONNECTION_WEST||dir==CONNECTION_EAST)?next->mapLayout->height:next->mapLayout->width;
        if(axis>=c->offset&&axis<c->offset+limit)return c;
    }return NULL;
}
'''


@unittest.skipUnless(shutil.which('gcc'), 'Host GCC required')
class PhysicalHaloTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='atlas-physical-')
        cls.root = Path(cls.temp.name)
        layer = FixtureLayer()
        cls.metadata = stage(layer, PLAN)
        text = layer.outputs['src/fieldmap.c'].decode()
        functions = text[text.index('static bool8 JourneyAtlasPhysicalWord('):text.index('static void FillConnection(')]
        bound = dict(PLAN, chunks=[dict(row, group_index=1) for row in PLAN['chunks']])
        runtime, _ = render_runtime(bound)
        code = SHIMS+'\n'+runtime+'\n'+layer.outputs['src/data/journey_atlas_physical.h'].decode()+functions+r'''
void init(void) {
    int i;gMapHeader=headers[1];
    gBackupMapLayout.width=17;gBackupMapLayout.height=16;gBackupMapLayout.map=backup;
    for(i=0;i<17*16;i++)backup[i]=0xBEEF;
    links[1].mapNum=1; connections.count=2;
}
int clipped(int x,int y,int sx,int sy,int width,int height,u16 *out) {
    static const u16 cells[]={0x312B,0x012B,0x1C43,0x212B,0x112B,0x1C43};
    struct MapLayout l={3,2,cells,1,(void*)1,(void*)1};
    struct MapHeader h={&l,0,NULL};
    init();JourneyAtlasCopyConnection(x,y,&h,sx,sy,width,height);
    memcpy(out,backup,sizeof(backup));return 0;
}
void halo(u16 *out) {
    init();JourneyAtlasFillPhysicalView(&gMapHeader);memcpy(out,backup,sizeof(backup));
}
int border(int x,int y,int wrong) {
    init(); if(wrong)links[1].mapNum=2;
    return JourneyAtlasBorderConnectionValid(x+7,y+7);
}
int no_links(void) {
    init();gMapHeader.connections=NULL;return JourneyAtlasBorderConnectionValid(6,7);
}
int native_unchanged(void) {
    int i;init();gMapHeader=headers[0];JourneyAtlasFillPhysicalView(&gMapHeader);
    for(i=0;i<17*16;i++)if(backup[i]!=0xBEEF)return 0;
    return 1;
}
int word(unsigned value,int unknown) {
    u16 result=0x3FF;
    struct MapLayout l={1,1,NULL,0,(void*)2,(void*)2};init();
    if(unknown)l.primaryTileset=(void*)99;
    JourneyAtlasPhysicalWord(&l,value,&result);return result;
}
int stale_header(void) {
    struct MapHeader stale=headers[1];stale.mapLayout=&layouts[2];
    return JourneyAtlasHeaderChunk(&stale)!=NULL;
}
'''
        (cls.root/'probe.c').write_text(code)
        subprocess.run(['gcc','-std=gnu89','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror',
                        '-Wno-unused-function',str(cls.root/'probe.c'),'-o',str(cls.root/'probe.so')],
                       check=True,capture_output=True,text=True)
        cls.lib=ctypes.CDLL(str(cls.root/'probe.so'))
        cls.array=ctypes.c_uint16*(17*16)
        cls.lib.clipped.argtypes=[ctypes.c_int]*6+[ctypes.POINTER(ctypes.c_uint16)]
        cls.lib.halo.argtypes=[ctypes.POINTER(ctypes.c_uint16)]

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_copy_intersection_matches_independent_cells_for_negative_origins(self):
        rng=random.Random(172)
        source=[0x312B,0x012B,0x1C43,0x212B,0x112B,0x1C43]
        for _ in range(500):
            x,y,sx,sy=[rng.randrange(-10,20) for _ in range(4)]
            width,height=[rng.randrange(-2,18) for _ in range(2)]
            expected=[0xBEEF]*(17*16)
            # Independent destination scan; no clipping arithmetic from C.
            for dy in range(16):
                for dx in range(17):
                    col,row=dx-x,dy-y
                    if 0<=col<width and 0<=row<height and 0<=sx+col<3 and 0<=sy+row<2:
                        expected[dy*17+dx]=source[(sy+row)*3+sx+col]
            actual=self.array();self.lib.clipped(x,y,sx,sy,width,height,actual)
            self.assertEqual(list(actual),expected,(x,y,sx,sy,width,height))

    def test_halo_preserves_current_runtime_cells_native_face_and_diagonal(self):
        actual=self.array();self.lib.halo(actual)
        self.assertEqual([actual[y*17+x] for y in (7,8) for x in (7,8)],[0xBEEF]*4)
        self.assertEqual(actual[7*17+6],0x3000) # native wins over Atlas reef
        self.assertEqual(actual[8*17+6],0x3C00)
        self.assertEqual(actual[7*17+9],0x15F9)
        self.assertEqual(actual[9*17+9],0x312B) # true diagonal owner, full word
        self.assertEqual(actual[9*17+10],0x012B)
        self.assertEqual(actual[10*17+9],0x1C43)
        self.assertEqual(actual[0],0x3FF) # no owner

    def test_halo_does_not_create_connection_or_accept_wrong_owner(self):
        self.assertTrue(self.lib.border(2,0,0))
        self.assertTrue(self.lib.border(-1,0,0))
        self.assertFalse(self.lib.border(2,2,0)) # diagonal has terrain, no edge
        self.assertFalse(self.lib.border(2,0,1)) # direct target disagrees with physical owner
        self.assertFalse(self.lib.no_links())
        self.assertFalse(self.lib.stale_header())
        self.assertTrue(self.lib.native_unchanged())

    def test_translation_preserves_height_collision_and_rejects_unknown(self):
        for high in range(64):
            self.assertEqual(self.lib.word((high<<10)|0x12B,0),(high<<10)|0x170)
            self.assertEqual(self.lib.word((high<<10)|0x12B,1),0x3FF)

    def test_stage_is_narrow_and_refuses_double_install(self):
        layer=FixtureLayer();stage(layer,PLAN)
        field=layer.outputs['src/fieldmap.c'].decode()
        self.assertIn('    mapWidth = connectedMapHeader->mapLayout->width;\n    LegacyCopy();',field)
        self.assertIn('    return LegacyBorder(x, y);',field)
        self.assertLess(field.index('#include "wild_encounter.h"'),field.index('#include "data/journey_atlas_physical.h"'))
        self.assertFalse(self.metadata['native_validated'])
        with self.assertRaisesRegex(ValueError,'already installed'):
            stage(layer,PLAN)


if __name__=='__main__':
    unittest.main()
