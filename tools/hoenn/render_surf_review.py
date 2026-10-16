"""Show all eight actual cave islands and their different native interiors."""
import argparse,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from render_sea_maps import MapRenderer

def render(source,output):
    source,output=Path(source),Path(output);output.mkdir(parents=True,exist_ok=True);r=json.loads((source/'.journey-surf-review').read_text());renderer=MapRenderer(source)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
    panels=[]
    for b in r['branches']:
        if b['existing_cave']:continue
        ext=renderer.render(b['surface'],npcs=False)[0];cx,cy=b['entry'];ext=ext.crop(((cx-11)*16,(cy-9)*16,(cx+12)*16,(cy+12)*16))
        inside=renderer.render(b['map'],npcs=False)[0]
        native=Path(__file__).resolve().parents[2]/'mods/hoenn/surf-review-validation/native'/(b['theme']+'-inside.png')
        if native.exists():inside=Image.open(native).convert('RGB')
        canvas=Image.new('RGB',(1024,580),'#12202e');d=ImageDraw.Draw(canvas)
        d.text((16,12),b['theme']+' · '+b['species'][0].removeprefix('SPECIES_').replace('_',' '),font=font,fill='white')
        for i,im in enumerate([ext,inside]):
            scale=min(480/im.width,500/im.height);im=im.resize((int(im.width*scale),int(im.height*scale)),Image.Resampling.NEAREST);canvas.paste(im,(i*512+(512-im.width)//2,55+(500-im.height)//2))
        canvas.save(output/(b['theme']+'.png'));panels.append(canvas)
    summary=Image.new('RGB',(2048,4*580),'#12202e')
    for i,p in enumerate(panels):summary.paste(p,((i%2)*1024,(i//2)*580))
    summary.save(output/'oito-cavernas.png')
    (output/'localizacoes.json').write_text(json.dumps(r['branches'],indent=2,ensure_ascii=False)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();render(a.source,a.output)
