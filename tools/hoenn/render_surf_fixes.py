"""Render selected native coastal terrain before and after removing rock banks.
NPCs are validated separately in native emulator screenshots.
"""
import argparse,json,struct
from pathlib import Path
from PIL import Image,ImageDraw
from render_sea_maps import MapRenderer

def render(source,output):
    source=Path(source);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    r=MapRenderer(source);report=json.loads((source/'.journey-surf-passages').read_text())
    selected=['MossdeepCity','Route124','Route125','Route127','Route128','Route131','Route106','Route20_Frlg']
    canvas=Image.new('RGB',(960,len(selected)*260),(16,24,32));d=ImageDraw.Draw(canvas)
    for row in report['maps']:
        n=row['map']
        if n not in selected and n!='FiveIsland_Frlg':continue
        im,_=r.render(n,npcs=False);im.save(output/(n+'.png'))
        if n not in selected:continue
        l=r.layouts[json.loads((source/'data/maps'/n/'map.json').read_text())['layout']]
        w,h=l['width'],l['height'];old=list(struct.unpack('<'+'H'*(w*h),(source/l['blockdata_filepath']).read_bytes()))
        for tile in row['tiles']:old[tile['y']*w+tile['x']]=tile['old']
        before,_=r.render(n,values=old,npcs=False)
        y=selected.index(n)*260;d.text((8,y+4),n+' — before / after',fill='white')
        for col,picture in enumerate([before,im]):
            picture.thumbnail((464,224),Image.Resampling.NEAREST);canvas.paste(picture,(col*480+8,y+28))
    canvas.save(output/'before-after.png')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();render(a.source,a.output)
