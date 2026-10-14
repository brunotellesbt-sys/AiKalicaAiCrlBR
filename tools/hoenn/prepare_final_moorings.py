"""Place the last compact moorings and preserve functional native warp behaviors."""
import argparse,io,json,re,struct
from pathlib import Path
from PIL import Image
from candidate_layer import Layer
from prepare_atlas_route_tracking import PRIOR,LAYER as PREVIOUS
from pack_crossover_assets import fit,indexed
LAYER='final-moorings';PRIOR=PRIOR+[PREVIOUS];ROOT=Path(__file__).resolve().parents[2]
def prepare(source):
 layer=Layer(source,LAYER,PRIOR)
 if r:=layer.existing():return r
 s=layer.source;ls={l['id']:l for l in json.loads((s/'data/layouts/layouts.json').read_text())['layouts']}
 def load(n):
  m=json.loads((s/f'data/maps/{n}/map.json').read_text());l=ls[m['layout']];v=list(struct.unpack('<'+'H'*(l['width']*l['height']),(s/l['blockdata_filepath']).read_bytes()));return m,l,v
 def save(m,l,v):layer.stage(f'data/maps/{m["name"]}/map.json',json.dumps(m,indent=2)+'\n');layer.stage(l['blockdata_filepath'],struct.pack('<'+'H'*len(v),*v))
 scripts=(s/'data/scripts/journey_campaign_gates.inc').read_text()
 def destination(pid,x,y):
  nonlocal scripts
  a=scripts.index('LavenderNetwork_Destination'+str(pid)+'::');b=scripts.index('\n\n',a);chunk=scripts[a:b];chunk=re.sub(r'(setvar VAR_0x8009, )\d+',lambda m:m[1]+str(x),chunk);chunk=re.sub(r'(setvar VAR_0x800A, )\d+',lambda m:m[1]+str(y),chunk);scripts=scripts[:a]+chunk+scripts[b:]
 # Native attribute storage is u16 even for FRLG's packed 32-bit entries.
 p='src/data/tilesets/metatiles.h';t=(s/p).read_text();layer.stage(p,t.replace('const u32 gMetatileAttributes_JourneyAppliances[]=INCBIN_U32','const u16 gMetatileAttributes_JourneyAppliances[]=INCBIN_U16'))
 # Move Cinnabar's cottage up one row so its entire floor rests on native land.
 m,l,v=load('CinnabarIsland_Frlg');w=l['width'];original=struct.unpack('<480H',(ROOT/'tools/hoenn/data/cinnabar-original.bin').read_bytes());house=[v[(12+dy)*w+8+dx] for dy in range(4) for dx in range(4)];left,right=v[16*w+9],v[16*w+10]
 for y in range(11,19):
  for x in range(8,14):v[y*w+x]=original[y*w+x]
 for dy in range(4):
  for dx in range(4):v[(11+dy)*w+8+dx]=house[dy*4+dx]
 for y in range(15,18):v[y*w+9]=left;v[y*w+10]=right
 for o in m['object_events']:
  if o['script']=='Journey_FerryPort19':o.update(x=9,y=16,movement_type='MOVEMENT_TYPE_FACE_RIGHT')
  if o['graphics_id']=='OBJ_EVENT_GFX_MR_BRINEYS_BOAT':o.update(x=12,y=17,movement_type='MOVEMENT_TYPE_FACE_LEFT')
 for y in [16,17]:
  for x in [11,12,13]:assert original[y*w+x]>>12==1;v[y*w+x]=0x152B
 for warp in m['warp_events']:
  if warp['dest_map']=='MAP_JOURNEYCINNABARSAILORSLODGE':warp.update(x=9,y=14)
 save(m,l,v);destination(19,10,16)
 # Tiny Sevii harbors use a two-wide, three-long pier and a completed beach.
 m,l,v=load('OneIsland_Harbor_Frlg')
 # Use a pinned native warp behavior with the plain native sand graphic.
 # No runtime dependency on the local reproduction directory.
 native_folder=Path('data/tilesets/secondary/island_harbor_frlg');primary=Path('data/tilesets/primary/general_frlg')
 meta=bytearray((s/native_folder/'metatiles.bin').read_bytes());attrs=bytearray((s/native_folder/'metatile_attributes.bin').read_bytes());warp_id=640+len(meta)//16;native_warp_attr=attrs[(0x2C9-640)*4:(0x2C9-640+1)*4];assert len(native_warp_attr)==4
 meta+=(s/primary/'metatiles.bin').read_bytes()[0x115*16:(0x115+1)*16];attrs+=native_warp_attr;layer.stage(str(native_folder/'metatiles.bin'),meta);layer.stage(str(native_folder/'metatile_attributes.bin'),attrs)
 # Installed bridge IDs from layer118, shared by all seven harbor maps.
 previous=v[:];wood_left=previous[3*l['width']+7];wood_right=previous[3*l['width']+9]
 for island,pid in zip(['One','Two','Three','Four','Five','Six','Seven'],range(2,9)):
  m,l,v=load(island+'Island_Harbor_Frlg');w=l['width'];v[:]=[0x112B]*len(v)
  for y in range(4):
   for x in range(6,11):v[y*w+x]=0x3000+([0x114,0x115,0x116][0 if x==6 else 2 if x==10 else 1] if y<3 else [0x11C,0x11D,0x11E][0 if x==6 else 2 if x==10 else 1])
  v[2*w+8]=0x3000|warp_id
  for y in range(4,7):v[y*w+7]=wood_left;v[y*w+8]=wood_right
  for o in m['object_events']:
   if o['script']=='Journey_FerryPort'+str(pid):o.update(x=8,y=5,movement_type='MOVEMENT_TYPE_FACE_RIGHT')
   if o['graphics_id']=='OBJ_EVENT_GFX_MR_BRINEYS_BOAT':o.update(x=10,y=6,movement_type='MOVEMENT_TYPE_FACE_LEFT')
  for y in [5,6]:
   for x in [9,10,11]:v[y*w+x]=0x152B
  save(m,l,v);destination(pid,7,5)
 p='include/journey_birth_arrivals.h';t=(s/p).read_text()
 for island in ['One','Two','Three','Four','Five','Six','Seven']:
  t,n=re.subn(r'\{MAP_'+island.upper()+r'_ISLAND_HARBOR, \d+, \d+, \d+, \d+, TRUE\}','{MAP_'+island.upper()+'_ISLAND_HARBOR, 10, 6, 7, 5, TRUE}',t);assert n==1
 layer.stage(p,t);layer.stage('data/scripts/journey_campaign_gates.inc',scripts)
 # Technical encoding trims pixels that become transparent in the GBA palette.
 im=Image.open(ROOT/'tools/hoenn/data/sootopolis-submarine-source.png').convert('RGBA');box=im.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox();frame=indexed(fit(im.crop(box),32,32));sheet=Image.new('P',(32,288));sheet.putpalette(frame.getpalette())
 for i in range(9):sheet.paste(frame,(0,32*i))
 out=io.BytesIO();sheet.save(out,format='PNG');layer.stage('graphics/object_events/pics/journey/submarine.png',out.getvalue());colors=frame.getpalette()[:48];layer.stage('graphics/object_events/pics/journey/submarine.pal','JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,colors[i:i+3])) for i in range(0,48,3))+'\n')
 return layer.finish(cinnabar_house_floor_on_native_land=True,cinnabar_existing_land_preserved=True,sevii_pier_size=[2,3],sevii_native_exit_warp_behavior_preserved=True,submarine_sprite_size=[32,32],submarine_collision_tiles=6)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
