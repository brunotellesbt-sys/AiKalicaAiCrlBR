"""Compile the actual marker clipping; valid chart pixels must stay visible."""
import ctypes
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from atlas_surf_marker import HELPER,stage


@unittest.skipUnless(shutil.which('cc'),'C compiler required')
class MarkerClippingTests(unittest.TestCase):
    def test_real_c_clip_keeps_every_atlas_coordinate_visible_without_wrapped_rectangles(self):
        code='''#include <stdint.h>
typedef int16_t s16;
#define PIXEL_FILL(x) ((x)|((x)<<4))
static int count,rectangle[6];
static void FillWindowPixelRect(int window,int fill,int left,int top,int width,int height){
count++;rectangle[0]=window;rectangle[1]=fill;rectangle[2]=left;rectangle[3]=top;rectangle[4]=width;rectangle[5]=height;
}
'''+HELPER+'''
int probe(int x,int y,int *out){int i;count=0;JourneyAtlasDrawPlayerMarker(x,y);for(i=0;i<6;i++)out[i]=rectangle[i];return count;}
'''
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'probe.c').write_text(code)
            subprocess.run(['cc','-std=gnu17','-O2','-shared','-fPIC','-Wall','-Werror',str(root/'probe.c'),'-o',str(root/'probe.so')],check=True,capture_output=True)
            lib=ctypes.CDLL(str(root/'probe.so'));rect=(ctypes.c_int*6)()
            for y in range(-4,116):
                for x in range(-4,228):
                    calls=lib.probe(x,y,rect)
                    left,top,right,bottom=max(0,x-1),max(0,y-1),min(224,x+2),min(112,y+2)
                    visible=left<right and top<bottom
                    self.assertEqual(calls,int(visible))
                    if visible:self.assertEqual(list(rect),[2,0x55,left,top,right-left,bottom-top])

    def test_marker_drawn_above_cursor_without_changing_gps_or_art(self):
        class Layer:
            outputs={'src/journey_world_map.c':b'''u16 JourneyWorldMapPosition(void){return realGPS;}
static void WorldDraw(void)
{
    if(playerX>=1 && playerX<223 && playerY>=1 && playerY<111)FillWindowPixelRect(2,PIXEL_FILL(5),playerX-1,playerY-1,3,3);
    FillWindowPixelRect(2,PIXEL_FILL(2),cursorX,cursorY,1,1);
}
'''}
            def stage(self,path,text):self.outputs[path]=text.encode()
        layer=Layer();report=stage(layer);updated=layer.outputs['src/journey_world_map.c'].decode()
        self.assertIn('u16 JourneyWorldMapPosition(void){return realGPS;}',updated)
        self.assertGreater(updated.index('    JourneyAtlasDrawPlayerMarker(playerX,playerY);'),updated.index('cursorX,cursorY,1,1);'))
        self.assertFalse(report['position_or_cursor_coordinates_changed'])
        self.assertFalse(report['art_changed'])
        with self.assertRaises(ValueError):stage(layer)


if __name__=='__main__':unittest.main()
