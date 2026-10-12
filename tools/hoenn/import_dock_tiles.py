"""Copy native Pacifidlog platform metatiles into unused Mossdeep tile slots."""
import io,struct
from pathlib import Path
from PIL import Image
from render_sea_maps import MapRenderer
def import_dock(source):
 source=Path(source);r=MapRenderer(source);dt,dp,dw=r.tileset('gTileset_Pacifidlog');tt,tp,tw=r.tileset('gTileset_Mossdeep');pt,pp,pw=r.tileset('gTileset_General')
 used={v&1023 for v in tw};spare=[i for i in range(512,1024) if i not in used and all(tt.getpixel(((i-512)%16*8+x,(i-512)//16*8+y))==0 for y in range(8) for x in range(8))]
 palettes=[(i,pp[i] if i<6 else tp[i]) for i in range(13)];mapping={};images=tt.copy();newwords=list(tw);ids={};donors=[0x220,0x221,0x224,0x228,0x229,0x22c]
 for mid in donors:
  ids[mid]=512+len(newwords)//8
  for word in dw[(mid-512)*8:(mid-512+1)*8]:
   tile=word&1023;pal=word>>12;key=(tile,pal)
   if key not in mapping:
    original=pt if tile<512 else dt;local=tile if tile<512 else tile-512;colors=pp[pal] if pal<6 else dp[pal]
    values=[original.getpixel((local%16*8+x,local//16*8+y)) for y in range(8) for x in range(8)]
    options=[]
    for bank,entries in palettes:
     conversion=[0];error=0
     for c in colors[1:16]:
      distances=[sum((a-b)**2 for a,b in zip(c,v)) for v in entries[1:16]];best=min(range(15),key=lambda i:distances[i]);conversion.append(best+1)
     for v in values:
      if v:error+=sum((a-b)**2 for a,b in zip(colors[v],entries[conversion[v]]))
     options.append((error,bank,conversion))
    _,bank,conversion=min(options);assert spare,'No safely unused graphics tile slots';target=spare.pop();mapping[key]=(target,bank)
    for k,v in enumerate(values):images.putpixel(((target-512)%16*8+k%8,(target-512)//16*8+k//8),conversion[v])
   target,bank=mapping[key];newwords.append(target|(word&0xc00)|(bank<<12))
 stream=io.BytesIO();images.save(stream,format='PNG');base='data/tilesets/secondary/mossdeep/';donor='data/tilesets/secondary/pacifidlog/'
 attrs=(source/(base+'metatile_attributes.bin')).read_bytes();dattrs=(source/(donor+'metatile_attributes.bin')).read_bytes();assert len(attrs)==len(tw)//8*2
 attrs+=b''.join(dattrs[(mid-512)*2:(mid-512+1)*2] for mid in donors)
 return ids,{base+'tiles.png':stream.getvalue(),base+'metatiles.bin':struct.pack('<'+'H'*len(newwords),*newwords),base+'metatile_attributes.bin':attrs}
