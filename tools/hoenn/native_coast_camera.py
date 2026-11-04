"""Read-only comparison of connected terrain, hardware BG words and scanout."""
import ctypes


def observe(ns):
    lib,s = ns['lib'],ns['s']
    read=lambda a,n:bytes(lib.read8(a+i) for i in range(n))
    vram=read(0x06000000,65536)
    image=ctypes.string_at(lib.image(),240*160*4)
    palettes=[lib.read16(0x05000000+2*i)&32767 for i in range(256)]
    rgb=[tuple(((v>>shift)&31)<<3 for shift in (0,5,10)) for v in palettes]
    current=ns['by_location'][ns['location']()]
    mapping=ns['maps'][current];layout=ns['layouts'][mapping['layout']]
    save=lib.read32(s['gSaveBlock1Ptr'])
    origin=[lib.read16(save+i) for i in (0,2)]
    camera=s['sFieldCameraOffset']
    ring=[lib.read8(camera+i) for i in (2,3)]
    controls={b:lib.read16(0x04000008+2*b) for b in range(4)}
    scroll={b:[lib.read16(s['sGpuRegBuffer']+0x10+4*b)&511,
               lib.read16(s['sGpuRegBuffer']+0x12+4*b)&511] for b in range(4)}
    display=lib.read16(0x04000000);assert display&7==0
    dims=[[(8,8),(16,16),(32,32),(64,64)],[(16,8),(32,8),(32,16),(64,32)],[(8,16),(8,32),(16,32),(32,64)]]
    sprites=[]
    for i in range(128):
        at=0x07000000+8*i;a0,a1=lib.read16(at),lib.read16(at+2)
        if a0&0x300==0x200 or a0>>14>2:continue
        w,h=dims[a0>>14][a1>>14];x,y=a1&511,a0&255
        if x>=256:x-=512
        if y>=160:y-=256
        sprites.append((x,y,w,h))

    def bg_word(bg,x,y):
        ctl=controls[bg];assert not ctl&128
        size=ctl>>14;width=512 if size in (1,3) else 256;height=512 if size in (2,3) else 256
        xx,yy=(x+scroll[bg][0])%width,(y+scroll[bg][1])%height
        tx,ty=xx//8,yy//8
        at=((ctl>>8)&31)*2048+((ty//32)*(width//256)+tx//32)*2048+((ty%32)*32+tx%32)*2
        return int.from_bytes(vram[at:at+2],'little'),xx%8,yy%8

    def color(bg,word,px,py):
        if word&1024:px=7-px
        if word&2048:py=7-py
        at=((controls[bg]>>2)&3)*16384+(word&1023)*32+py*4+px//2
        index=(vram[at]>>(4*(px&1)))&15
        return None if not index else rgb[(word>>12)*16+index]

    def canonical(x,y):
        if 0<=x<layout['width'] and 0<=y<layout['height']:return current,x,y
        for c in mapping.get('connections') or []:
            d,off=c['direction'],c['offset']
            if not ((d=='left' and x<0) or (d=='right' and x>=layout['width'])
                    or (d=='up' and y<0) or (d=='down' and y>=layout['height'])):continue
            name=ns['by_id'][c['map']]
            other=ns['layouts'][ns['maps'][name]['layout']];w,h=other['width'],other['height']
            if d=='left' and x<0:xx,yy=x+w,y-off
            elif d=='right' and x>=layout['width']:xx,yy=x-layout['width'],y-off
            elif d=='up' and y<0:xx,yy=x-off,y+h
            elif d=='down' and y>=layout['height']:xx,yy=x-off,y-layout['height']
            else:continue
            if 0<=xx<w and 0<=yy<h:return name,xx,yy
        return None

    def definition(name,word):
        l=ns['layouts'][ns['maps'][name]['layout']];mid=word&1023
        assert l['layout_version']=='frlg'
        bank=s[l['primary_tileset' if mid<640 else 'secondary_tileset']]
        index=mid if mid<640 else mid-640
        words=[lib.read16(lib.read32(bank+12)+index*16+2*i) for i in range(8)]
        layer=(lib.read32(lib.read32(bank+16)+index*4)>>29)&3
        assert layer in (0,1,2)
        return words,layer

    definitions={};samples={};checked=neighbor=0;ids=set();water=0
    for y in range(2,160,4):
        for x in range(2,240,4):
            if any(xx<=x<xx+w and yy<=y<yy+h for xx,yy,w,h in sprites):continue
            if display&256:
                word,px,py=bg_word(0,x,y)
                if color(0,word,px,py) is not None:continue
            xx=(x+scroll[1][0])%256;yy=(y+scroll[1][1])%256
            dx=((xx//8-ring[0])%32)//2;dy=((yy//8-ring[1])%32)//2
            gx,gy=origin[0]+dx,origin[1]+dy
            place=canonical(gx-7,gy-7)
            if place is None:continue
            name,mx,my=place;width=ns['blocks'][name][0];word=ns['blocks'][name][2][my*width+mx]
            key=(name,word&1023)
            if key not in definitions:definitions[key]=definition(name,word)
            words,layer=definitions[key]
            q=(((yy//8-ring[1])%32)%2)*2+(((xx//8-ring[0])%32)%2)
            expected={0:{1:words[4+q],2:words[q],3:0x3014},
                      1:{1:0,2:words[4+q],3:words[q]},
                      2:{1:words[4+q],2:0,3:words[q]}}[layer]
            for bg,value in expected.items():
                actual,_,_=bg_word(bg,x,y)
                assert actual==value,('Connected terrain drawn with wrong BG words',current,name,[mx,my],hex(word),bg,hex(actual),hex(value))
            top=None
            for bg in sorted(expected,key=lambda b:(controls[b]&3,b)):
                actual,px,py=bg_word(bg,x,y);candidate=color(bg,actual,px,py)
                if candidate is not None:
                    top=candidate
                    if actual&1023 in (454,455):
                        assert actual>>12==4,('Ocean palette mismatch',current,actual)
                        water+=1
                    break
            if top is None:continue
            actual=image[(y*240+x)*4:(y*240+x)*4+3]
            assert all(abs(a-b)<=7 for a,b in zip(top,actual)),('Native BG/scanout mismatch',current,x,y,top,list(actual))
            checked+=1
            if name!=current:neighbor+=1;ids.add(word&1023)
            samples.setdefault((name,word&1023),[x,y,*top,name,word&1023])
    assert checked>=300 and water>=50,(current,checked,water)
    return dict(map=current,checked_scanout_samples=checked,neighbor_scanout_samples=neighbor,
                neighbor_metatiles=sorted(ids),water_samples=water,palette=4,
                samples=list(samples.values()),canonical_neighbor_rom_bg_words_checked=True,
                actual_hardware_bg_vram_palette_scanout_checked=True,
                sprites_and_opaque_ui_explicitly_excluded=True,mismatches_not_discarded=True)
