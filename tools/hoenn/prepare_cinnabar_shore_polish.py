"""Finish marine rock graphics and keep the native resident off the new roof."""
import argparse,json,struct
from pathlib import Path
from candidate_layer import Layer
from prepare_continuous_atlas_marker import PRIOR,LAYER as PREVIOUS
LAYER='cinnabar-shore-polish';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
 layer=Layer(source,LAYER,PRIOR)
 if r:=layer.existing():return r
 s=layer.source;p='data/maps/CinnabarIsland_Frlg/map.json';m=json.loads((s/p).read_text());l=next(l for l in json.loads((s/'data/layouts/layouts.json').read_text())['layouts'] if l['id']==m['layout']);w=l['width'];v=list(struct.unpack('<480H',(s/l['blockdata_filepath']).read_bytes()))
 for y in [18,19]:
  for x in range(8,14):v[y*w+x]=0x112B
 # The distant edge boulder remains a complete native 2x2 obstruction.
 for dy in range(2):
  for dx in range(2):v[(18+dy)*w+22+dx]=[0x510,0x511,0x518,0x519][dy*2+dx]
 moved=[]
 for o in m['object_events']:
  if 8<=o['x']<=11 and 11<=o['y']<=14:
   moved.append(dict(graphics=o['graphics_id'],old=[o['x'],o['y']],new=[12,14]));o.update(x=12,y=14,movement_type='MOVEMENT_TYPE_FACE_LEFT',movement_range_x=0,movement_range_y=0)
 assert len(moved)==1,moved
 layer.stage(p,json.dumps(m,indent=2)+'\n');layer.stage(l['blockdata_filepath'],struct.pack('<480H',*v))
 return layer.finish(native_land_preserved=True,broken_marine_boulders_finished=True,residents_relocated=moved)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
