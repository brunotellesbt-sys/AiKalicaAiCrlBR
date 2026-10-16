"""Render the real connected island terminal tiles and bridge occlusion."""
import argparse,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from render_sea_maps import MapRenderer
from compile_dewford_harbor_art import quantized


def render(source,output):
    source,output=Path(source),Path(output);output.mkdir(parents=True,exist_ok=True);r=MapRenderer(source)
    rects=[('Route106',-80,-20),('DewfordTown',-20,0),('Route107',0,0),('JourneyDewfordPortIsland',0,-12)]
    left,top,right,bottom=-12,-12,18,20
    im=Image.new('RGB',((right-left)*16,(bottom-top)*16),(40,50,60))
    actors=[]
    for name,x,y in rects:
        part,m=r.render(name,npcs=False);im.paste(part,((x-left)*16,(y-top)*16))
        for o in m['object_events']:
            if str(o['flag'])=='0':actors.append((x,y,o))
    for x,y,o in sorted(actors,key=lambda p:p[1]+p[2]['y']):
        frame=2 if o['graphics_id']=='OBJ_EVENT_GFX_MR_BRINEYS_BOAT' and o['movement_type'] in ('MOVEMENT_TYPE_FACE_LEFT','MOVEMENT_TYPE_FACE_RIGHT') else 0
        sprite=r.sprite(o['graphics_id'],frame);dx,dy=r.sprite_offset(o['graphics_id']);im.paste(sprite,((x+o['x']-left)*16+8-sprite.width//2+dx,(y+o['y']-top)*16+16-sprite.height+dy),sprite)
    # Preserve the elevated bridge foreground, matching the GBA BG1 order.
    art,_=quantized(Path(__file__).parent/'data/dewford-harbor/arched-bridge.png',(64,176));rgba=art.convert('RGBA');rgba.putalpha(art.point(lambda p:255 if p else 0, mode='L'))
    im.paste(rgba,((4-left)*16,(4-top)*16),rgba)
    scale=3;im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST);im.save(output/'Dewford-island-harbor.png')
    grid=im.copy();d=ImageDraw.Draw(grid,'RGBA');font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
    for y in range(top,bottom):
        for x in range(left,right):
            px=(x-left)*48;py=(y-top)*48;d.rectangle((px,py,px+47,py+47),outline=(255,255,255,60));d.text((px+2,py+2),f'{x},{y}',font=font,fill='white',stroke_width=1,stroke_fill='black')
    grid.save(output/'Dewford-island-harbor-grid.png')
    room,_=r.render('JourneyDewfordHarbor');room.resize((room.width*3,room.height*3),Image.Resampling.NEAREST).save(output/'Dewford-harbor-interior.png')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True);p.add_argument('--output',required=True);a=p.parse_args();render(a.source,a.output)
