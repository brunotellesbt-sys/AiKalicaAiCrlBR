"""Guard the small display-only fix and exercise its C predicate semantically."""
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

from coastal_ecology_pier_priority import ANCHOR, APPROACHES, HELPER, NEW, OLD, PATH, repair


class CoastalPierPriority(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        source = Path(temporary.name)
        def write(path, value):
            target = source/path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(value)
        layouts = []
        for name, map_id, bounds in APPROACHES:
            words = [0x3001] * (26*30)
            bridges = [(x,15) for x in range(6,12)] if name.startswith('Cinnabar') else [(18,25)]
            for x,y in bridges:
                words[y*26+x] = 0xF305
            layout = dict(id=name,width=26,height=30,layout_version='frlg',
                blockdata_filepath=f'data/layouts/{name}/map.bin')
            layouts.append(layout)
            write(layout['blockdata_filepath'],struct.pack('<780H',*words))
            write(f'data/maps/{name}/map.json',json.dumps(dict(id=map_id,layout=name)).encode())
        write('data/layouts/layouts.json',json.dumps(dict(layouts=layouts)).encode())
        write(PATH,('untouched before\n'+ANCHOR+'\n    u8 displayElevation;\n'+OLD+'\n}\nuntouched after\n').encode())
        class Stage:
            def __init__(self):
                self.source,self.outputs=source,{}
                self.expected={p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in source.rglob('*') if p.is_file()}
            def stage(self,path,raw):
                self.outputs[path]=raw.encode() if isinstance(raw,str) else raw
        return Stage()

    def test_only_stages_priority_code_and_never_mutates_inputs(self):
        stage=self.fixture()
        before={p.relative_to(stage.source).as_posix():p.read_bytes()
                for p in stage.source.rglob('*') if p.is_file()}
        result=repair(stage)
        self.assertEqual(set(stage.outputs),{PATH})
        after=stage.outputs[PATH].decode()
        self.assertEqual(after.replace(HELPER,'').replace(NEW,OLD),before[PATH].decode())
        self.assertEqual(before,{p.relative_to(stage.source).as_posix():p.read_bytes()
                                for p in stage.source.rglob('*') if p.is_file()})
        self.assertEqual([len(r['dry_approach_cells']) for r in result['reviewed_approaches']],[4,12])
        self.assertEqual(repair(stage)['changed_paths'],[])

    def test_rejects_changed_dry_surface(self):
        stage=self.fixture()
        path='data/layouts/CinnabarIsland_Frlg/map.bin'
        raw=bytearray((stage.source/path).read_bytes())
        struct.pack_into('<H',raw,2*(16*26+9),0x1001)
        stage.outputs[path]=bytes(raw)
        with self.assertRaises(AssertionError):repair(stage)
        self.assertNotIn(PATH,stage.outputs)

    def test_rejects_lost_surf_underpass(self):
        stage=self.fixture()
        path='data/layouts/PalletTown_Frlg/map.bin'
        raw=bytearray((stage.source/path).read_bytes())
        struct.pack_into('<H',raw,2*(25*26+18),0x3305)
        stage.outputs[path]=bytes(raw)
        with self.assertRaises(AssertionError):repair(stage)
        self.assertNotIn(PATH,stage.outputs)

    def test_rejects_changed_native_priority_anchor(self):
        stage=self.fixture()
        stage.outputs[PATH]=(stage.source/PATH).read_bytes().replace(b'displayElevation = 4;',b'displayElevation = 6;')
        with self.assertRaises(AssertionError):repair(stage)

    def test_twelve_compiled_semantic_guards(self):
        compiler=shutil.which('cc')
        self.assertIsNotNone(compiler,'A host C compiler is required for the guard check')
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            code='''#include <stdint.h>
typedef uint8_t bool8; typedef uint8_t u8; typedef int16_t s16;
#define FALSE 0
#define MAP_OFFSET 7
#define ELEVATION_DEFAULT 3
#define PLAYER_AVATAR_FLAG_ON_FOOT 1
#define PLAYER_AVATAR_FLAG_SURFING 8
#define MAP_CINNABAR_ISLAND 0x0102
#define MAP_PALLET_TOWN 0x0103
#define MAP_GROUP(m) ((m)>>8)
#define MAP_NUM(m) ((m)&255)
struct ObjectEvent { struct { s16 x,y; } currentCoords; u8 isPlayer,currentElevation; };
struct { struct { u8 mapGroup,mapNum; } location; } saveBlock;
__typeof__(saveBlock) *gSaveBlock1Ptr=&saveBlock;
struct { u8 flags; } gPlayerAvatar;
'''+HELPER+'''
struct Case { int map,x,y,player,elevation,flags,wanted; };
int main(void) {
    struct Case cases[] = {
        {0x0102,9,16,1,3,1,1}, {0x0102,9,16,1,3,0,0},
        {0x0102,8,16,1,3,1,0}, {0x0102,9,18,1,3,1,0},
        {0x0104,9,16,1,3,1,0}, {0x0103,11,26,1,3,1,1},
        {0x0103,22,26,1,3,1,1}, {0x0103,10,26,1,3,1,0},
        {0x0103,18,26,1,3,2,0}, {0x0102,9,16,0,3,1,0},
        {0x0102,9,16,1,1,1,0}, {0x0102,9,16,1,3,9,0},
    };
    for (unsigned i=0;i<sizeof(cases)/sizeof(cases[0]);i++) {
        struct Case c=cases[i];
        struct ObjectEvent object={{c.x+7,c.y+7},c.player,c.elevation};
        saveBlock.location.mapGroup=c.map>>8;saveBlock.location.mapNum=c.map&255;
        gPlayerAvatar.flags=c.flags;
        if (JourneyCoastalPierFootPriority(&object)!=c.wanted) return i+1;
    }
    return 0;
}
'''
            (root/'guards.c').write_text(code)
            subprocess.run([compiler,'-std=gnu99','-Wall','-Wextra','-Werror',str(root/'guards.c'),'-o',str(root/'guards')],check=True)
            subprocess.run([str(root/'guards')],check=True)


if __name__=='__main__':unittest.main()
