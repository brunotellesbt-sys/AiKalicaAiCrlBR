"""Scenery classification must not hide a playable or one-way escape."""
import unittest
import ctypes
from pathlib import Path
import subprocess
import tempfile

from atlas_surf_background import cells,render
from atlas_surf_reachability import audit
from test_atlas_surf_reachability import Terrain


class BackgroundWater(unittest.TestCase):
    def fixture(self):
        source=Terrain();source.add('A',width=5,height=3,word=0x1401)
        for y in range(3):
            source.set('A',0,y,0x1001);source.set('A',4,y,0x1001)
        plan=dict(chunks=[dict(name='A',origin=[0,0],width=5,height=3,
                              decorative_water_runs=[[y,4,5] for y in range(3)])])
        requirements=dict(complete=True,ports=[],caves=[],dives=[],adapters=[],native_pixels=[])
        return source,plan,requirements

    def test_real_reef_separates_passable_background(self):
        source,plan,requirements=self.fixture()
        result=audit(source,plan=plan,requirements=requirements)
        self.assertTrue(result['passed'],result['errors'])
        self.assertEqual(result['generated_water_cells'],3)
        self.assertEqual(result['decorative_water_isolation']['cells'],3)
        self.assertEqual(result['decorative_water_isolation']['directed_reachable_cells'],0)

    def test_gap_in_reef_is_rejected_even_when_declared_decorative(self):
        source,plan,requirements=self.fixture()
        for x in range(1,4):source.set('A',x,1,0x1001)
        result=audit(source,plan=plan,requirements=requirements)
        self.assertIn('playable-ocean-can-reach-decorative-water',{r['kind'] for r in result['errors']})

    def test_one_way_warp_to_background_is_not_hidden_by_scc_filter(self):
        source,plan,requirements=self.fixture()
        source.set('A',0,1,0x3002)
        source.maps['A']['warp_events']=[dict(x=0,y=1,elevation=3,dest_map='MAP_B',dest_warp_id=0)]
        source.add('B',width=2,height=3,word=0x1001)
        # B is outside the declared background. A one-way walk/surf path
        # through this third region reaches A's far water via its real edge.
        source.maps['B']['warp_events']=[dict(x=0,y=1,elevation=1,dest_map='MAP_B',dest_warp_id=0)]
        source.connect('A','B',direction='right');requirements['transit_maps']=['B']
        result=audit(source,plan=plan,requirements=requirements)
        self.assertEqual(result['generated_water_sccs'],1)
        self.assertIn('playable-ocean-can-reach-decorative-water',{r['kind'] for r in result['errors']})

    def test_bad_or_overlapping_bounds_rejected(self):
        for runs in ([[0,0,6]],[[0,1,3],[0,2,4]],[['0',1,3]],[[1,1,2],[0,1,2]]):
            with self.assertRaises(ValueError):cells(dict(width=5,height=3,decorative_water_runs=runs))

    def test_water_label_cannot_hide_a_blocked_rock(self):
        source,plan,requirements=self.fixture();source.set('A',4,1,0x1401)
        result=audit(source,plan=plan,requirements=requirements)
        self.assertIn('decorative-water-is-not-native-surf-water',{r['kind'] for r in result['errors']})


class CompiledBackgroundLookup(unittest.TestCase):
    def test_emitted_C_lookup_respects_map_row_and_exclusive_endpoint(self):
        plan=dict(chunks=[dict(name='A',width=12,height=8,decorative_water_runs=[[0,0,3],[0,7,12],[3,1,9]]),
                          dict(name='B',width=9,height=4,decorative_water_runs=[[0,2,7],[3,0,9]])])
        header,rows=render(plan,dict(A=23040,B=23345))
        code='''#include <stdint.h>
typedef uint16_t u16;typedef uint32_t u32;typedef uint8_t u8;typedef int32_t s32;typedef uint8_t bool8;
#define TRUE 1
#define FALSE 0
#define ARRAY_COUNT(a) (sizeof(a)/sizeof((a)[0]))
#define STATIC_ASSERT(c,n) _Static_assert(c,#n)
'''+header+'\nint request(int m,int x,int y){return JourneyAtlasBackground(m,x,y);}\n'
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory);(p/'probe.c').write_text(code)
            subprocess.run(['gcc','-shared','-fPIC','-Wall','-Wextra','-Werror',str(p/'probe.c'),'-o',str(p/'probe.so')],check=True,capture_output=True)
            lib=ctypes.CDLL(str(p/'probe.so'));lib.request.argtypes=[ctypes.c_int]*3
            for m in (0,23039,23040,23041,23345,65535):
                for y in range(-1,10):
                    for x in range(-1,15):
                        expected=any(mm==m and yy==y and a<=x<b for mm,yy,a,b in rows)
                        self.assertEqual(bool(lib.request(m,x,y)),expected,(m,x,y))
            for x,y in [(128,0),(-1,0),(0,128),(0,-1)]:self.assertFalse(lib.request(23040,x,y))
            arm=Path(__file__).resolve().parents[2]/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'
            if arm.exists():
                subprocess.run([str(arm),'-S','-mabi=apcs-gnu','-mcpu=arm7tdmi','-mthumb',str(p/'probe.c'),'-o',str(p/'probe.s')],check=True,capture_output=True)


if __name__=='__main__':unittest.main()
