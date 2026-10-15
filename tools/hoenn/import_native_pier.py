"""Copy native Lavender bridge metatiles into each town's actual secondary bank."""
import io,re,struct
from pathlib import Path
from PIL import Image
from render_sea_maps import MapRenderer

def import_pier(source,target,emerald=False,donor="gTileset_LavenderTown",mids=None,donor_emerald=False,overrides=None,donor_palettes=None,transparent_colors=None):
 source=Path(source);r=MapRenderer(source);primary='gTileset_General' if emerald else 'gTileset_General_Frlg';cut=512 if emerald else 640
 donor_cut=512 if donor_emerald else 640
 source_primary=r.tileset('gTileset_General' if donor_emerald else 'gTileset_General_Frlg')
 overrides=overrides or {}
 def read(p):return overrides.get(str(p),(source/p).read_bytes())
 dt,dp,dw=r.tileset(donor);tt,tp,tw=r.tileset(target);pt,pp,pw=r.tileset(primary)
 def donor_colors(bank):return (donor_palettes or {}).get(bank,source_primary[1][bank] if bank<(6 if donor_emerald else 7) else dp[bank])
 folder=Path(re.search(r'"([^"]+)"',re.search(r'\b'+re.search(r'\.metatiles = (\w+)',re.search(r'const struct Tileset '+target+r'\s*=\s*\{(.*?)\};',r.headers,re.S)[1])[1]+r'\[\].*?;',r.metas,re.S)[0])[1]).parent
 if str(folder/'tiles.png') in overrides:
  tt=Image.open(io.BytesIO(read(folder/'tiles.png')));raw=read(folder/'metatiles.bin');tw=struct.unpack('<'+'H'*(len(raw)//2),raw)
 # Resolve donors via symbols rather than assuming their folder spelling.
 h=re.search(r'const struct Tileset '+donor+r'\s*=\s*\{(.*?)\};',r.headers,re.S)[1];symbol=re.search(r'\.metatileAttributes = (\w+)',h)[1];attr_path=Path(re.search(r'\b'+symbol+r'\[\].*?"([^"]+)"',r.metas)[1]);da=(source/attr_path).read_bytes()
 used={v&1023 for v in tw};canvas=Image.new('P',(128,256 if emerald else 192));canvas.putpalette(tt.getpalette());canvas.paste(tt,(0,0));spare=[i for i in range(cut,1024) if i not in used];palettes=[(i,pp[i] if i<(6 if emerald else 7) else tp[i]) for i in range(13)];mapping={};newwords=list(tw);attrs=bytearray(read(folder/'metatile_attributes.bin'));ids={};palette_files={}
 usedbanks={word>>12 for word in list(tw)+list(pw)}
 def metatile_words(mid):return source_primary[2][mid*8:(mid+1)*8] if mid<donor_cut else dw[(mid-donor_cut)*8:(mid-donor_cut+1)*8]
 # Reuse identical palettes before reserving scarce secondary palette slots.
 for pal in sorted({word>>12 for mid in (mids or [0x2F3,0x2F4,0x2F5]) for word in metatile_words(mid)}):
  incoming=donor_colors(pal)
  if any(entries==incoming for _,entries in palettes):continue
  free=[bank for bank in range(12,5 if emerald else 6,-1) if bank not in usedbanks]
  if free:
   bank=free[0];usedbanks.add(bank);colors=incoming;palettes=[(b,colors if b==bank else entries) for b,entries in palettes];palette_files[str(folder/f'palettes/{bank:02}.pal')]=('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in colors)+'\n').encode()
 for mid in (mids or [0x2F3,0x2F4,0x2F5]):
  ids[mid]=cut+len(newwords)//8
  for word in metatile_words(mid):
   tile=word&1023;pal=word>>12;key=(tile,pal)
   if key not in mapping:
    im=source_primary[0] if tile<donor_cut else dt;idx=tile if tile<donor_cut else tile-donor_cut;cols=im.width//8;colors=donor_colors(pal);values=[im.getpixel((idx%cols*8+x,idx//cols*8+y)) for y in range(8) for x in range(8)];options=[]
    values=[0 if v in (transparent_colors or {}).get(pal,()) else v for v in values]
    for bank,entries in palettes:
     conversion=[0]
     for c in colors[1:16]:conversion.append(1+min(range(15),key=lambda i:sum((a-b)**2 for a,b in zip(c,entries[i+1]))))
     error=sum(sum((a-b)**2 for a,b in zip(colors[v],entries[conversion[v]])) for v in values if v);options.append((error,bank,conversion))
    _,bank,conversion=min(options);assert spare;slot=spare.pop(0);mapping[key]=(slot,bank)
    for k,v in enumerate(values):canvas.putpixel(((slot-cut)%16*8+k%8,(slot-cut)//16*8+k//8),conversion[v])
   slot,bank=mapping[key];newwords.append(slot|(word&0xC00)|(bank<<12))
  if mid<donor_cut:
   ph=re.search(r'const struct Tileset '+('gTileset_General' if donor_emerald else 'gTileset_General_Frlg')+r'\s*=\s*\{(.*?)\};',r.headers,re.S)[1];symbol=re.search(r'\.metatileAttributes = (\w+)',ph)[1];pa=(source/re.search(r'\b'+symbol+r'\[\].*?"([^"]+)"',r.metas)[1]).read_bytes();idx=mid
  else:pa=da;idx=mid-donor_cut
  size=2 if donor_emerald else 4;value=int.from_bytes(pa[idx*size:(idx+1)*size],'little');behavior=value&(255 if donor_emerald else 511);kind=(value>>(12 if donor_emerald else 29))&3
  attrs.extend((behavior|(kind<<(12 if emerald else 29))).to_bytes(2 if emerald else 4,'little'))
 assert len(newwords)//8+cut<=1024 and len(attrs)==len(newwords)//8*(2 if emerald else 4)
 data=io.BytesIO();canvas.save(data,format='PNG')
 return ids,{str(folder/'tiles.png'):data.getvalue(),str(folder/'metatiles.bin'):struct.pack('<'+'H'*len(newwords),*newwords),str(folder/'metatile_attributes.bin'):attrs,**palette_files}
