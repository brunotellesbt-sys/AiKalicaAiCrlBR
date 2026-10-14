"""Finish generated sandy shore contours without replacing native towns or caves."""
import argparse,json,struct
from pathlib import Path
from candidate_layer import Layer
from prepare_live_gym_levels import PRIOR,LAYER as PREVIOUS
LAYER='coast-finish';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
 layer=Layer(source,LAYER,PRIOR)
 if r:=layer.existing():return r
 s=layer.source;ls={l['id']:l for l in json.loads((s/'data/layouts/layouts.json').read_text())['layouts']};changes=[]
 for p in sorted((s/'data/maps').glob('Journey*/map.json')):
  m=json.loads(p.read_text());l=ls[m['layout']]
  if m['map_type'] not in ['MAP_TYPE_ROUTE','MAP_TYPE_OCEAN_ROUTE'] or 'Island' in m['name'] or 'Shipyard' in m['name']:continue
  w,h=l['width'],l['height'];v=list(struct.unpack('<'+'H'*(w*h),(s/l['blockdata_filepath']).read_bytes()));old=v[:];frlg=l['layout_version']=='frlg'
  shore=[0x10C,0x10D,0x10E,0x114,0x115,0x116,0x11C,0x11D,0x11E] if frlg else [0x11B,0x11C,0x11D,0x123,0x124,0x125,0x12B,0x12C,0x12D];flat=shore[4];water=0x112B if frlg else 0x1170
  land={(i%w,i//w) for i,t in enumerate(v) if t&1023 in shore+[1]};grass=sum(t&1023==1 for t in v);added=set()
  # A one-cell extremity cannot display both opposing native shore edges.
  # Widen such ends using existing water, retaining every original land tile.
  for _ in range(2):
   extra=set()
   for x,y in sorted(land):
    options=[]
    if (x-1,y) not in land and (x+1,y) not in land:options.extend([(x-1,y),(x+1,y)])
    if (x,y-1) not in land and (x,y+1) not in land:options.extend([(x,y-1),(x,y+1)])
    choices=[(xx,yy) for xx,yy in options if 3<=xx<w-3 and 3<=yy<h-3 and v[yy*w+xx]==water]
    if choices:extra.add(max(choices,key=lambda q:(sum((q[0]+dx,q[1]+dy) in land for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]),-q[0],-q[1])))
   land|=extra;added|=extra
  for x,y in land:
   north=(x,y-1) not in land;south=(x,y+1) not in land;west=(x-1,y) not in land;east=(x+1,y) not in land
   row=0 if north else 2 if south else 1;col=0 if west else 2 if east else 1;mid=shore[row*3+col]
   # Never replace copied mountain or cavern metatiles; only the beach ring.
   v[y*w+x]=mid|((3 if frlg or row==col==1 else 1)<<12)
  for o in m['object_events']:
   if o['elevation']==3 and (o['x'],o['y']) in land:v[o['y']*w+o['x']]=0x3000|flat
  if v!=old:
   layer.stage(l['blockdata_filepath'],struct.pack('<'+'H'*len(v),*v));changes.append(dict(map=m['name'],grass_fragments_removed=grass,shore_tiles_finished=sum(a!=b for a,b in zip(old,v)),added_tip_tiles=len(added)))
 # Dynamic allies use buffered coordinates only when creating their object.
 p='src/journey_galactic.c';t=(s/p).read_text();needle='SpawnSpecialObjectEventParameterized(gfx,MOVEMENT_TYPE_FACE_UP,localId,x,y,3)';assert needle in t;layer.stage(p,t.replace(needle,'SpawnSpecialObjectEventParameterized(gfx,MOVEMENT_TYPE_FACE_UP,localId,x+MAP_OFFSET,y+MAP_OFFSET,3)'))
 return layer.finish(maps=changes,original_land_retained=True,native_towns_and_large_playable_islands_preserved=True,galactic_ally_spawn_offset_corrected=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
