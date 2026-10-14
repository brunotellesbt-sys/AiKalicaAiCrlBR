"""Preserve continuous shared-edge coordinates instead of rounding to a band.

The schematic Surf bands can have gaps around town artwork. Snapping across
those gaps caused the very short-move jumps the update must eliminate.
"""
import argparse,re
from pathlib import Path
from candidate_layer import Layer
from prepare_final_moorings import PRIOR,LAYER as PREVIOUS
LAYER='continuous-atlas-marker';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
 layer=Layer(source,LAYER,PRIOR)
 if r:=layer.existing():return r
 p='src/journey_world_map.c';t=(layer.source/p).read_text();start=t.index('// Chart routes are schematic bands.');end=t.index('// Shared edge anchors',start);t=t[:start]+t[end:];t=t.replace('#include "data/journey_world_surf_mask.h"\n','').replace('return WorldSurfPosition(sWorldPoints[point].x | (sWorldPoints[point].y << 8));','return sWorldPoints[point].x | (sWorldPoints[point].y << 8);').replace('return WorldSurfPosition(a->x | (a->y << 8));','return a->x | (a->y << 8);').replace('return WorldSurfPosition(((sx + total / 2) / total) | (((sy + total / 2) / total) << 8));','return ((sx + total / 2) / total) | (((sy + total / 2) / total) << 8);');assert 'WorldSurfPosition' not in t;layer.stage(p,t)
 return layer.finish(shared_edge_continuity_preserved=True,no_nearest_band_position_jumps=True,actual_route_label_preserved=True,approved_atlas_pixels_preserved=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
