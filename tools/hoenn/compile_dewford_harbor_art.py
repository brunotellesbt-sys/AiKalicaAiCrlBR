"""Compile the original generated harbor art into indexed GBA map graphics."""
import io,struct
from pathlib import Path
from PIL import Image


def quantized(path,size):
    art=Image.open(path).convert('RGBA')
    bounds=art.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
    assert bounds, path
    # Compile the large terminal at the same coarse pixel density as GBA towns.
    logical=(size[0]//2,size[1]//2) if path.stem=='terminal' else size
    art=art.crop(bounds).resize(logical,Image.Resampling.NEAREST).resize(size,Image.Resampling.NEAREST)
    rgb=art.convert('RGB');q=rgb.quantize(colors=11 if path.stem=='terminal' else 15,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    rgb_palette=(q.getpalette()+[0]*45)[:45]
    palette=[(0,0,0)]+[tuple((c//8)*8 for c in rgb_palette[i:i+3]) for i in range(0,45,3)]
    out=Image.new('P',size);out.putpalette([c for color in palette for c in color]+[0]*(768-48))
    out.putdata([v+1 if a[3]>=128 else 0 for v,a in zip(q.getdata(),art.getdata())])
    return out,palette


def compile_art(renderer,used_mids):
    """Retain every referenced native graphic, including the animated flag."""
    root=Path(__file__).parent/'data/dewford-harbor';s=renderer.source
    tiles,palettes,old_words=renderer.tileset('gTileset_Dewford')
    folder=s/'data/tilesets/secondary/dewford'
    old_attrs=(folder/'metatile_attributes.bin').read_bytes()
    words=list(old_words);attrs=bytearray(old_attrs)
    used_graphics={v&1023 for mid in used_mids if mid>=512 for v in old_words[(mid-512)*8:(mid-511)*8] if v&1023>=512}|set(range(682,688))
    canvas=tiles.copy();free_graphics=iter(i for i in range(512,1024) if i not in used_graphics)
    free_mids=iter(i for i in range(512,512+len(words)//8) if i not in used_mids)
    cache={};allocations={};art_palettes={}
    for mid in range(512,512+len(words)//8):
        if mid not in used_mids:words[(mid-512)*8:(mid-511)*8]=[0]*8;attrs[(mid-512)*2:(mid-511)*2]=b'\0\0'
    def graphic(tile,bank):
        key=(tile.tobytes(),bank)
        if key in cache:return cache[key]
        for transpose,flags in [(Image.Transpose.FLIP_LEFT_RIGHT,0x400),(Image.Transpose.FLIP_TOP_BOTTOM,0x800)]:
            mirror=(tile.transpose(transpose).tobytes(),bank)
            if mirror in cache:return cache[mirror]^flags
        try:slot=next(free_graphics)
        except StopIteration:raise AssertionError('Custom harbor exceeds GBA graphics bank')
        canvas.paste(tile,((slot-512)%16*8,(slot-512)//16*8));cache[key]=slot|(bank<<12);return cache[key]
    def metatile(im,px,py,bank,base,behavior=0):
        try:mid=next(free_mids)
        except StopIteration:raise AssertionError('Custom harbor exceeds GBA metatile bank')
        top=[graphic(im.crop((px+qx*8,py+qy*8,px+qx*8+8,py+qy*8+8)),bank) for qy in range(2) for qx in range(2)]
        words[(mid-512)*8:(mid-511)*8]=list(base)+top
        struct.pack_into('<H',attrs,(mid-512)*2,behavior)
        return mid
    primary=renderer.tileset('gTileset_General')[2]
    for name,size,bank in [('terminal',(208,144),6),('arched-bridge',(64,176),7)]:
        art,colors=quantized(root/(name+'.png'),size);art_palettes[bank]=colors
        cells=[]
        for y in range(size[1]//16):
            for x in range(size[0]//16):
                tile=art.crop((x*16,y*16,x*16+16,y*16+16))
                if not any(tile.getdata()):continue
                ground=0x124 if name=='terminal' else 0x170
                mid=metatile(art,x*16,y*16,bank,primary[ground*8:ground*8+4],0x70 if name=='arched-bridge' else 0)
                cells.append((x,y,mid))
        allocations[name]=dict(cells=cells,image=art)
    # The plan is straight and two tiles wide. The curve is in its elevation.
    allocations['arched-bridge']['walk']=[(x,y) for y in range(11) for x in (1,2)]
    out=io.BytesIO();canvas.save(out,format='PNG')
    files={'tiles.png':out.getvalue(),'metatiles.bin':struct.pack('<'+'H'*len(words),*words),'metatile_attributes.bin':bytes(attrs)}
    for bank in range(16):
        if bank in art_palettes:
            colors=art_palettes[bank];files[f'palettes/{bank:02}.pal']=('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in colors)+'\n').encode()
        else:files[f'palettes/{bank:02}.pal']=(folder/f'palettes/{bank:02}.pal').read_bytes()
    return files,allocations,len(cache)
