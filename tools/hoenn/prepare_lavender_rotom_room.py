"""Use Lavender Tower's native floor, walls and palettes for Rotom's archive."""
import argparse,io,json,re,struct
from pathlib import Path
from PIL import Image
from candidate_layer import Layer
from prepare_compact_ports import PRIOR,LAYER as PREVIOUS
LAYER='lavender-rotom-room';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
 layer=Layer(source,LAYER,PRIOR)
 if r:=layer.existing():return r
 s=layer.source;headers=(s/'src/data/tilesets/headers.h').read_text();metas=(s/'src/data/tilesets/metatiles.h').read_text();h=re.search(r'const struct Tileset gTileset_PokemonTower\s*=\s*\{(.*?)\};',headers,re.S)[1];sym=re.search(r'\.metatiles = (\w+)',h)[1];path=Path(re.search(r'\b'+sym+r'\[\].*?"([^"]+)"',metas)[1]);native=path.parent;folder=Path('data/tilesets/secondary/journey_appliances')
 base=Image.open(s/native/'tiles.png');old=Image.open(s/folder/'tiles.png');tiles=Image.new('P',(128,96));tiles.putpalette(base.getpalette());tiles.paste(base,(0,0));tiles.paste(old.crop((0,224,128,256)),(0,64));data=io.BytesIO();tiles.save(data,format='PNG');layer.stage(str(folder/'tiles.png'),data.getvalue())
 for i in range(16):
  if i!=12:layer.stage(str(folder/f'palettes/{i:02}.pal'),(s/native/f'palettes/{i:02}.pal').read_bytes())
 words=list(struct.unpack('<'+'H'*((s/native/'metatiles.bin').stat().st_size//2),(s/native/'metatiles.bin').read_bytes()));count=len(words)//8;ids=[];oldwords=struct.unpack('<'+'H'*((s/folder/'metatiles.bin').stat().st_size//2),(s/folder/'metatiles.bin').read_bytes())
 for i in range(12):
  ids.append(640+len(words)//8)
  for word in oldwords[(400+i)*8:(401+i)*8]:words.append((word&~1023)|((word&1023)-960+768))
 attrs=bytearray((s/native/'metatile_attributes.bin').read_bytes());assert len(attrs)==count*4;attrs+=bytes(12*4)
 layer.stage(str(folder/'metatiles.bin'),struct.pack('<'+'H'*len(words),*words));layer.stage(str(folder/'metatile_attributes.bin'),attrs)
 # Switch only this added tileset to the native FRLG attributes/primary bank.
 p='src/data/tilesets/metatiles.h';t=(s/p).read_text();t=t.replace('const u16 gMetatileAttributes_JourneyAppliances[]=INCBIN_U16','const u32 gMetatileAttributes_JourneyAppliances[]=INCBIN_U32');layer.stage(p,t)
 p='data/layouts/layouts.json';d=json.loads((s/p).read_text());l=next(x for x in d['layouts'] if x['id']=='LAYOUT_JOURNEY_LAVENDER_WORKSHOP');l.update(primary_tileset='gTileset_BuildingFrlg',layout_version='frlg',border_width=2,border_height=2);layer.stage(p,json.dumps(d,indent=2)+'\n')
 w,h=18,12;v=[0x3282]*(w*h)
 for y in range(h):
  for x in range(w):
   if y==0:v[y*w+x]=0x0681
   elif y==1:v[y*w+x]=0x0698
   elif y==2:v[y*w+x]=0x06A0
   elif x==0:v[y*w+x]=0x068A
   elif x==w-1:v[y*w+x]=0x068B
   elif y==h-1:v[y*w+x]=0x0681
 # Door and columns come from the actual tower's entrance, never a house.
 tower=struct.unpack('<480H',(s/'data/layouts/PokemonTower_1F_Frlg/map.bin').read_bytes());v[10*w+8]=tower[18*24+11]
 # Existing interaction coordinates remain stable for the six appliances.
 for i,x in enumerate([2,5,8,11,14,8]):
  y=3 if i<5 else 7;v[y*w+x]=0x3C00|ids[2*i];v[(y+1)*w+x]=0x3C00|ids[2*i+1]
 layer.stage(l['blockdata_filepath'],struct.pack('<'+'H'*len(v),*v));layer.stage(l['border_filepath'],struct.pack('<4H',*([0x0681]*4)))
 p='data/maps/JourneyLavenderWorkshop/map.json';m=json.loads((s/p).read_text());m['object_events'][0]['graphics_id']='OBJ_EVENT_GFX_BALDING_MAN';m['object_events'][1]['graphics_id']='OBJ_EVENT_GFX_CHANNELER';layer.stage(p,json.dumps(m,indent=2)+'\n')
 return layer.finish(native_lavender_tower_floor_walls_and_palette=True,platinum_inspiration=['Old Chateau television encounter','Eterna Galactic appliance room'],interaction_coordinates_preserved=True,appliance_metatiles=ids)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
