"""Keep Surf markers on the approved maritime chart and label the actual map."""
import argparse
from pathlib import Path
from candidate_layer import Layer
from prepare_coast_finish import PRIOR,LAYER as PREVIOUS
from prepare_world_dex_map import decode
LAYER='atlas-route-tracking';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
 layer=Layer(source,LAYER,PRIOR)
 if r:=layer.existing():return r
 s=layer.source;im=decode((s/'src/data/journey_world_map.h').read_text());mask=bytearray(28*112)
 for y in range(112):
  for x in range(224):
   if im.getpixel((x,y))==2:mask[y*28+x//8]|=1<<(x%8)
 layer.stage('src/data/journey_world_surf_mask.h','static const u8 sWorldSurfMask[] = {'+','.join(map(str,mask))+'};\n')
 p='src/journey_world_map.c';t=(s/p).read_text();t=t.replace('#include "data/journey_world_position.h"','#include "data/journey_world_position.h"\n#include "data/journey_world_surf_mask.h"')
 pos=t.index('// Shared edge anchors')
 helper='''// Chart routes are schematic bands. Quantize only Surf positions to the
// nearby band, preserving shared-border continuity and terrestrial positions.
static u16 WorldSurfPosition(u16 position)
{
    s16 x = position & 255, y = position >> 8, xx, yy;
    u32 best = 65535, distance;
    u16 result = position;
    if (!(gPlayerAvatar.flags & PLAYER_AVATAR_FLAG_SURFING)) return position;
    for (yy = max(0, y - 6); yy <= min(111, y + 6); yy++)
        for (xx = max(0, x - 6); xx <= min(223, x + 6); xx++)
            if (sWorldSurfMask[yy * 28 + xx / 8] & (1 << (xx % 8)))
            {
                distance = (xx - x) * (xx - x) + (yy - y) * (yy - y);
                if (distance < best) { best = distance; result = xx | (yy << 8); }
            }
    return result;
}

'''
 t=t[:pos]+helper+t[pos:];start=t.index('u16 JourneyWorldMapPosition(void)');end=t.index('static void WorldDraw',start);chunk=t[start:end];chunk=chunk.replace('return sWorldPoints[point].x | (sWorldPoints[point].y << 8);','return WorldSurfPosition(sWorldPoints[point].x | (sWorldPoints[point].y << 8));').replace('return a->x | (a->y << 8);','return WorldSurfPosition(a->x | (a->y << 8));').replace('return ((sx + total / 2) / total) | (((sy + total / 2) / total) << 8);','return WorldSurfPosition(((sx + total / 2) / total) | (((sy + total / 2) / total) << 8));');t=t[:start]+chunk+t[end:]
 needle='        best = sJourneyWorldMap->player;';assert t.count(needle)==1;t=t.replace(needle,'    {\n        best = sJourneyWorldMap->player;\n        distance = 0;\n    }');layer.stage(p,t)
 return layer.finish(actual_map_name_when_recentered=True,surf_marker_uses_local_projection_and_nearest_chart_band=True,maximum_snap_radius=6,approved_atlas_pixels_unchanged=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
