"""Native source assets and complete map rectangles; never a game capture.

The renderer currently shows the default static NPC frame. It does not
certify the four trainer facing animations or native camera seams.
"""
import sys,json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
from render_sea_maps import MapRenderer
import argparse
parser=argparse.ArgumentParser(description='Render whole source maps for the boundary/swimmer/species batch; no native-ROM certification.')
parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
a=parser.parse_args();source=a.source.resolve()
if a.output.resolve()==source or a.output.resolve().is_relative_to(source):raise ValueError('Render outside the private source')
m=json.loads((source/'.journey-atlas-surf-layout').read_bytes())
names=sorted({r['map'] for r in m['route_border_redesign']['maps']}|{r['map'] for r in m['legendary_appearance_redesign']['changes']})
r=MapRenderer(source);out=a.output;out.mkdir(exist_ok=True);rows=[]
for i,name in enumerate(names):
 im,_=r.render(name,npcs=True);path=out/(name+'.png');im.save(path)
 rows.append(dict(map=name,file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),pixels=list(im.size),NPCs=True))
 if i%64==0:print(i,len(names),name,flush=True)
for page,start in enumerate(range(0,len(rows),24)):
 sheet=Image.new('RGB',(1200,1500),(24,36,46));d=ImageDraw.Draw(sheet)
 for j,row in enumerate(rows[start:start+24]):
  im=Image.open(out/row['file']).convert('RGB');im.thumbnail((280,224),Image.Resampling.NEAREST)
  x=(j%4)*300;y=(j//4)*250;sheet.paste(im,(x+8,y+22));d.text((x+8,y+5),row['map'],fill='white')
 sheet.save(out/f'contact-{page:02d}.png')
(out/'renders.json').write_text(json.dumps(dict(kind='whole-map-source-render-review',maps=rows,sprite_sources=r.sprite_sources,native_ROM_capture=False),indent=2)+'\n')
print('DONE',len(rows),'whole source maps including NPCs',flush=True)
