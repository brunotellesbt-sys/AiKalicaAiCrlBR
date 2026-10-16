"""Render each Sevii terminal and the matching permanent ship interior."""
import argparse,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from render_sea_maps import MapRenderer


def render(source,output):
    source,output=Path(source),Path(output);output.mkdir(exist_ok=True,parents=True)
    r=MapRenderer(source);report=json.loads((source/'.journey-sevii-harbors').read_text());panels=[]
    for p in report['ports']:
        for key in ['exterior','interior']:
            im,_=r.render(p[key],npcs=True);im=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST);im.save(output/(p[key]+'.png'))
            if key=='exterior':panels.append((p['island'],im))
    w=max(im.width for _,im in panels);h=max(im.height for _,im in panels)+36
    sheet=Image.new('RGB',(w*4,h*2),'#182030');d=ImageDraw.Draw(sheet);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
    for i,(name,im) in enumerate(panels):
        x=i%4*w;y=i//4*h;d.text((x+8,y+5),name+' Island',fill='white',font=font);sheet.paste(im,(x,y+36))
    sheet.save(output/'all-seven.png')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();render(a.source,a.output)
