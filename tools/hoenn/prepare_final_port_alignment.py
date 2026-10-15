"""Apply the reviewed horizontal Pallet mooring and complete Sevii beach rims."""
import argparse,hashlib,json,struct
from pathlib import Path
from candidate_layer import Layer
from world_projection import project
from prepare_port_houses_and_ships import PRIOR,LAYER as PREVIOUS
LAYER='final-port-alignment';PRIOR=PRIOR+[PREVIOUS];ROOT=Path(__file__).resolve().parents[2]

def prepare(source):
 layer=Layer(source,LAYER,PRIOR)
 if old:=layer.existing():return old
 s=layer.source;ld=json.loads((s/'data/layouts/layouts.json').read_text());ls={l['id']:l for l in ld['layouts']};maps={};blocks={}
 def load(n):
  if n not in maps:maps[n]=json.loads((s/f'data/maps/{n}/map.json').read_text())
  m=maps[n];l=ls[m['layout']];p=l['blockdata_filepath']
  if p not in blocks:
   raw=(s/p).read_bytes();blocks[p]=list(struct.unpack('<'+'H'*(len(raw)//2),raw))
  return m,l,blocks[p]
 def boat(n,x,y):
  m,l,v=load(n);o=next(o for o in m['object_events'] if o['graphics_id'] in ['OBJ_EVENT_GFX_MR_BRINEYS_BOAT','OBJ_EVENT_GFX_JOURNEY_SUBMARINE']);o.update(x=x,y=y,movement_type='MOVEMENT_TYPE_FACE_LEFT')
  for yy in [y-1,y]:
   for xx in [x-1,x,x+1]:
    at=yy*l['width']+xx;assert v[at]>>12==1,(n,xx,yy,hex(v[at]));v[at]|=0x400
 old=json.loads((s/'.journey-port-houses-and-ships').read_text());cottages=old['cottages']
 n='PalletTown_Frlg';m,l,v=load(n);w=l['width'];house=[v[(15+y)*w+2+x] for y in range(3) for x in range(5)];left,right=v[17*w+11],v[17*w+12]
 raw=(ROOT/'tools/hoenn/data/pallet-before-houses.bin').read_bytes();assert hashlib.sha256(raw).hexdigest()==old['original_sha256'][l['blockdata_filepath']]
 v[:]=struct.unpack('<480H',raw);l['height']=20
 # The cottage moves to the east bank. Clear the complete short fence and
 # its foreground plants on dry ground; retain the lab and the entire shore.
 for yy in range(16,20):
  for xx in range(13,21):
   assert v[yy*w+xx]>>12 in [0,3];v[yy*w+xx]=0x3001
 # Relocate the lab sign to its eastern end, clear of the cottage entrance.
 v[16*w+20]=0x402
 for bg in m['bg_events']:
  if bg['x']==16 and bg['y']==16:bg.update(x=20,y=16)
 for dy in range(3):
  for dx in range(5):v[(16+dy)*w+13+dx]=house[dy*5+dx]
 for yy in [17,18]:
  for xx in [10,11,12]:v[yy*w+xx]=left if xx==10 else right if xx==12 else (left&~1023)|((left&1023)+1)
 for yy in [18,19]:
  for xx in [8,9,10]:
   if v[yy*w+xx]>>12==1:v[yy*w+xx]&=~0x400
 boat(n,8,19)
 for warp in m['warp_events']:
  if warp['dest_map']=='MAP_JOURNEYPALLETTOWNPORTLODGE':warp.update(x=14,y=18)
 for c in cottages:
  if c['map']==n:c.update(house=[13,16,5,3],door=[14,18])
 # This is the nearest water-only placement: the row above contains the shore.
 n='SootopolisCity';m,l,v=load(n)
 for yy in [39,40]:
  for xx in [20,21,22]:v[yy*l['width']+xx]&=~0x400
 boat(n,21,39)
 n='Route104';m,l,v=load(n)
 for yy in [52,53]:
  for xx in [8,9,10]:v[yy*l['width']+xx]&=~0x400
 boat(n,9,52)
 # Complete the shared seven-island beach with a water-facing rim on all
 # sides. Each cottage has a full sand tile between its facade and the sea.
 resized=False
 for island in ['One','Two','Three','Four','Five','Six','Seven']:
  n=island+'Island_Harbor_Frlg';m,l,v=load(n)
  if not resized:
   w=l['width'];h=l['height'];v[:]=[t for yy in range(h) for t in v[yy*w:(yy+1)*w]+[0x112B]];l['width']=w+1;resized=True
  w=l['width'];warp=v[2*w+8];bridge=[v[4*w+7],v[4*w+8]]
  for yy in range(4):
   for xx in range(6,17):
    if 11<=xx<=15 and 1<=yy<=3:continue
    row=0 if yy==0 else 2 if yy==3 and xx<=9 else 1;col=0 if xx==6 else 2 if xx==16 else 1;v[yy*w+xx]=0x3000|[0x10C,0x10D,0x10E,0x114,0x115,0x116,0x11C,0x11D,0x11E][row*3+col]
  for xx in range(10,17):v[4*w+xx]=0x3000|[0x11C,0x11D,0x11E][0 if xx==10 else 2 if xx==16 else 1]
  v[2*w+8]=warp;v[3*w+7],v[3*w+8]=bridge
 layer.stage('data/layouts/layouts.json',json.dumps(ld,indent=2)+'\n')
 for n,m in maps.items():layer.stage(f'data/maps/{n}/map.json',json.dumps(m,indent=2)+'\n')
 for p,v in blocks.items():layer.stage(p,struct.pack('<'+'H'*len(v),*v))
 allmaps={p.parent.name:json.loads(p.read_text()) for p in (s/'data/maps').glob('*/map.json')};allmaps.update(maps);coords={p['map']:tuple(p['center']) for p in old['projections']};geometry=project(allmaps,ls,coords);layer.stage('src/data/journey_world_position.h',geometry.pop('data'))
 return layer.finish(cottages=cottages,pallet_horizontal_pier=[10,17,3,2],pallet_boat=[8,19],pallet_house=[13,16,5,3],pallet_original_shore_preserved=True,sootopolis_submarine=[21,39],petalburg_boat=[9,52],sevii_house_sand_rim=1,sevii_pier_extended_toward_sand=True,fuchsia_preserved=True,**geometry)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
