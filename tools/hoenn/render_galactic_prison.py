"""Render the actual prison tiles, native sprites and foreground containment fields."""
import argparse,json,struct
from pathlib import Path
from PIL import Image
from render_sea_maps import MapRenderer


def render(source,output):
    source=Path(source);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    renderer=MapRenderer(source)
    room,m=renderer.render('JourneyGalacticHall',npcs=False)
    layout=renderer.layouts[m['layout']]
    for event in m['object_events']:
        gfx=event['graphics_id']
        if gfx.startswith('OBJ_EVENT_GFX_JOURNEY_'):
            key=gfx.removeprefix('OBJ_EVENT_GFX_JOURNEY_').lower()
            path=source/'graphics/object_events/pics/people'/('journey_'+key+'.png');w,h=16,32
        elif gfx.startswith('OBJ_EVENT_GFX_SPECIES('):
            key=gfx.split('(',1)[1].rstrip(')').lower()
            path=source/'graphics/pokemon'/key/'overworld.png';w=h=64
        else:continue
        frame=Image.open(path).crop((0,0,w,h));sprite=frame.convert('RGBA')
        if frame.mode=='P':
            mask=Image.new('L',frame.size);mask.putdata([0 if i==0 else 255 for i in frame.get_flattened_data()]);sprite.putalpha(mask)
        room.paste(sprite,(event['x']*16+8-w//2,event['y']*16+16-h),sprite)
    # Source rendering normally flattens the layers. Reapply only the cage's
    # transparent foreground, as the GBA does above the prisoner sprites.
    metas=renderer.tileset(layout['secondary_tileset'])
    blocks=struct.unpack('<'+'H'*(layout['width']*layout['height']),(source/layout['blockdata_filepath']).read_bytes())
    base=json.loads((source/'.journey-galactic-prison').read_text())['metatile_base']
    for cell,value in enumerate(blocks):
        mid=value&1023
        if not (base+4<=mid<base+8 or base+16<=mid<base+20):continue
        entries=metas[2][(mid-512)*8+4:(mid-512)*8+8]
        image=Image.new('RGBA',(16,16))
        for q,entry in enumerate(entries):
            tile=(entry&1023)-512;bank=entry>>12
            for y in range(8):
                for x in range(8):
                    xx=7-x if entry&1024 else x;yy=7-y if entry&2048 else y
                    index=metas[0].getpixel((tile%16*8+xx,tile//16*8+yy))
                    if index:image.putpixel((q%2*8+x,q//2*8+y),(*metas[1][bank][index],255))
        room.alpha_composite(image,(cell%layout['width']*16,cell//layout['width']*16)) if room.mode=='RGBA' else room.paste(image,(cell%layout['width']*16,cell//layout['width']*16),image)
    room.resize((room.width*2,room.height*2),Image.Resampling.NEAREST).save(output/'team-galactic-final-room.png')
    room.crop((16,0,480,208)).resize((928,416),Image.Resampling.NEAREST).save(output/'team-galactic-final-chamber.png')
    return output/'team-galactic-final-chamber.png'


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();print(render(a.source,a.output))
