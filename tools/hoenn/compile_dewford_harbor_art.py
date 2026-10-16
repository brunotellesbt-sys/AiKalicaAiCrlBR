"""Compile the original generated harbor art into indexed GBA map graphics."""
import io,struct
from pathlib import Path
from PIL import Image

# Copy the beach underlay without replacing the suspension bridge above it.
BRIDGE_GROUND={(4,4):0x12C,(5,4):0x12C,(6,4):0x12C,(7,4):'inner-sw',
               (7,5):0x123,(7,6):0x12B}
SHORE=(0x11B,0x11C,0x11D,0x123,0x124,0x125,0x12B,0x12C,0x12D)


def finish_beach(image):
    """Keep native shoreline silhouettes, with a continuous two-pixel wet rim."""
    result=image.copy()
    water={(x,y) for y in range(16) for x in range(16)
           if image.getpixel((x,y))[2]>180}
    for y in range(16):
        for x in range(16):
            if (x,y) in water:continue
            distance=min((max(abs(x-xx),abs(y-yy)) for xx,yy in water),default=99)
            if distance==1:result.putpixel((x,y),(248,240,192))
            elif distance==2:result.putpixel((x,y),(238,230,164))
    return result


def inner_beaches(renderer):
    """Round inward shore corners with the same native sand and blue water."""
    sand=renderer.render('Route107',values=[0x124],dimensions=(1,1),npcs=False)[0]
    sea=renderer.render('Route107',values=[0x170],dimensions=(1,1),npcs=False)[0]
    sw=sand.copy()
    for y in range(16):
        for x in range(16):
            distance=(x+1)**2+(16-y)**2
            if distance<=64:sw.putpixel((x,y),sea.getpixel((x,y)))
            elif distance<=90:sw.putpixel((x,y),(213,180,106))
    sw=finish_beach(sw)
    return {'inner-sw':sw,'inner-se':sw.transpose(Image.Transpose.FLIP_LEFT_RIGHT),
            'inner-nw':sw.transpose(Image.Transpose.FLIP_TOP_BOTTOM),
            'inner-ne':sw.transpose(Image.Transpose.FLIP_LEFT_RIGHT).transpose(Image.Transpose.FLIP_TOP_BOTTOM)}


def quantized(path,size):
    art=Image.open(path).convert('RGBA')
    bounds=art.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
    assert bounds, path
    # Keep one source pixel per GBA pixel, including windows and roof details.
    art=art.crop(bounds).resize(size,Image.Resampling.NEAREST)
    rgb=art.convert('RGB');q=rgb.quantize(colors=9 if path.stem=='terminal' else 15,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
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
    beach_images=inner_beaches(renderer)
    beach_images[0x170]=renderer.render('Route107',values=[0x170],dimensions=(1,1),npcs=False)[0]
    for mid in SHORE:
        beach_images[mid]=finish_beach(renderer.render('Route107',values=[mid],dimensions=(1,1),npcs=False)[0])
    shore_colors=sorted({c for im in beach_images.values() for c in im.getdata()})
    assert len(shore_colors)<=15
    # Bank 9 is unused by the retained Dewford graphics. It keeps both the sea
    # and sand colors when their native two-layer tiles become bridge underlays.
    native_banks={v>>12 for mid in used_mids if mid>=512 for v in old_words[(mid-512)*8:(mid-511)*8]}
    assert 9 not in native_banks
    art_palettes[9]=[(0,0,0)]+shore_colors+[(0,0,0)]*(15-len(shore_colors))
    ground_words={}
    allocations['beach-inner']={}
    allocations['beach-outer']={}
    for mid,im in beach_images.items():
        indexed=Image.new('P',(16,16));indexed.putdata([shore_colors.index(c)+1 for c in im.getdata()])
        ground_words[mid]=[graphic(indexed.crop((x,y,x+8,y+8)),9) for y in (0,8) for x in (0,8)]
        if isinstance(mid,str):allocations['beach-inner'][mid]=metatile(indexed,0,0,9,primary[0x170*8:0x170*8+4])
        elif mid in SHORE and mid!=0x124:allocations['beach-outer'][mid]=metatile(indexed,0,0,9,primary[0x170*8:0x170*8+4])
    for name,size,bank in [('terminal',(208,144),6),('arched-bridge',(64,176),7)]:
        art,colors=quantized(root/(name+'.png'),size);art_palettes[bank]=colors
        cells=[]
        for y in range(size[1]//16):
            for x in range(size[0]//16):
                tile=art.crop((x*16,y*16,x*16+16,y*16+16))
                if not any(tile.getdata()):continue
                ground=0x124 if name=='terminal' else 0x170
                if name=='terminal' and x==12:ground=0x170
                base=ground_words[BRIDGE_GROUND[(x+4,y+4)]] if name=='arched-bridge' and (x+4,y+4) in BRIDGE_GROUND else ground_words[0x170] if name=='terminal' and x==12 else primary[ground*8:ground*8+4]
                mid=metatile(art,x*16,y*16,bank,base,0x70 if name=='arched-bridge' else 0)
                cells.append((x,y,mid))
        allocations[name]=dict(cells=cells,image=art)
    # The plan is straight and two tiles wide. The curve is in its elevation.
    allocations['arched-bridge']['walk']=[(x,y) for y in range(11) for x in (1,2)]
    # Two short native risers, recolored to the bridge footing's wood palette.
    native_stairs=renderer.render('MossdeepCity',values=[0x330,0x331],dimensions=(2,1),npcs=False)[0]
    short=native_stairs.crop((0,8,32,16));colored=Image.new('P',(32,8))
    colored.putdata([0 if max(c)-min(c)>55 else 11 if sum(c)//3<90 else 9 if sum(c)//3<135 else 7 if sum(c)//3<165 else 2 if sum(c)//3<190 else 1 for c in short.getdata()])
    north_stairs=Image.new('P',(32,16));north_stairs.paste(colored,(0,8))
    south_stairs=Image.new('P',(32,16));south_stairs.paste(colored,(0,0))
    allocations['stairs']=dict(cells=[(x,0,metatile(north_stairs,x*16,0,7,primary[0x124*8:0x124*8+4])) for x in (0,1)],south_cells=[(x,0,metatile(south_stairs,x*16,0,7,ground_words[0x11C])) for x in (0,1)])
    # A complete inward NE beach bend joins both adjacent shores at the landing.
    allocations['marked-shore']=allocations['beach-inner']['inner-ne']
    out=io.BytesIO();canvas.save(out,format='PNG')
    files={'tiles.png':out.getvalue(),'metatiles.bin':struct.pack('<'+'H'*len(words),*words),'metatile_attributes.bin':bytes(attrs)}
    for bank in range(16):
        if bank in art_palettes:
            colors=art_palettes[bank];files[f'palettes/{bank:02}.pal']=('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in colors)+'\n').encode()
        else:files[f'palettes/{bank:02}.pal']=(folder/f'palettes/{bank:02}.pal').read_bytes()
    return files,allocations,len(cache)
