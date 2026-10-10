"""Assemble source metatiles at the exact coordinates used by map connections."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from render_sea_maps import MapRenderer

def render(source,output,include_vermilion=False):
 source=Path(source);output=Path(output);output.mkdir(parents=True,exist_ok=True)
 report=json.loads((source/'.journey-eastern-sea-union').read_text());r=MapRenderer(source)
 rects=list(report['rectangles'])
 entrance=source/'.journey-ever-grande-entrance'
 if entrance.exists():
  overrides={r['map']:r for r in json.loads(entrance.read_text()).get('rectangle_overrides',[])}
  rects=[overrides.get(r['map'],r) for r in rects]
 if include_vermilion:
  # Native south connection offset 0: city sits directly above WorldSea00.
  rects.append(dict(map='VermilionCity_Frlg',x=190,y=-40,width=48,height=40))
  if entrance.exists():
   rects.extend([dict(map='Route19_Frlg',x=118,y=-60,width=24,height=60),dict(map='FuchsiaCity_Frlg',x=106,y=-100,width=48,height=40)])
 coastal=source/'.journey-route12-port'
 if coastal.exists():
  extra=json.loads(coastal.read_text())['rectangle_overrides']
  changes={r['map']:r for r in extra}
  rects=[changes.pop(r['map'],r) for r in rects]+list(changes.values())
 xmin=min(m['x'] for m in rects);ymin=min(m['y'] for m in rects)
 xmax=max(m['x']+m['width'] for m in rects);ymax=max(m['y']+m['height'] for m in rects)
 # Empty background remains labelled outside this rendered eastern-ocean section.
 scale=8;canvas=Image.new('RGB',((xmax-xmin)*scale,(ymax-ymin)*scale),(17,39,51))
 for m in rects:
  image,_=r.render(m['map'],npcs=m['map'].startswith('Journey'))
  canvas.paste(image.resize((m['width']*scale,m['height']*scale),Image.Resampling.NEAREST),((m['x']-xmin)*scale,(m['y']-ymin)*scale))
 canvas.save(output/'eastern-union-terrain.png')
 annotated=canvas.copy();draw=ImageDraw.Draw(annotated);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
 for m in rects:
  if 'Lane' in m['map']:continue
  x=(m['x']-xmin)*scale;y=(m['y']-ymin)*scale
  label=m['map'].replace('Journey','').replace('Hoenn','').replace('WorldSea','Sevii sea ')
  box=draw.textbbox((x+5,y+5),label,font=font);draw.rectangle((box[0]-2,box[1]-2,box[2]+2,box[3]+2),fill=(15,26,42));draw.text((x+5,y+5),label,font=font,fill='white')
 if include_vermilion and not coastal.exists():
  x=(190+34-xmin)*scale;y=(38-40-ymin)*scale
  draw.line([(x,y-45),(x,y+85)],fill=(255,65,45),width=5)
  draw.polygon([(x,y+85),(x-12,y+66),(x+12,y+66)],fill=(255,65,45))
  draw.text((x+18,y-35),'Vermilion: southeast Surf channel',font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',24),fill='white',stroke_width=2,stroke_fill='black')
 if include_vermilion and entrance.exists():
  points=[((140-xmin)*scale,(-12-ymin)*scale),((160-xmin)*scale,(-12-ymin)*scale),((160-xmin)*scale,(8-ymin)*scale)]
  draw.line(points,fill=(255,65,45),width=5)
  x,y=points[-1];draw.polygon([(x,y),(x-12,y-19),(x+12,y-19)],fill=(255,65,45))
  draw.text((points[0][0]+12,points[0][1]-38),'Fuchsia: Route 19 east channel',font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',24),fill='white',stroke_width=2,stroke_fill='black')
 if coastal.exists():
  points=[((317-xmin)*scale,(-16-ymin)*scale),((359-xmin)*scale,(-16-ymin)*scale),((359-xmin)*scale,(8-ymin)*scale)]
  draw.line(points,fill=(255,65,45),width=5)
  x,y=points[-1];draw.polygon([(x,y),(x-12,y-19),(x+12,y-19)],fill=(255,65,45))
  draw.text((points[0][0]+8,points[0][1]-35),'Route 12 shipyard -> Sevii / Hoenn',font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',24),fill='white',stroke_width=2,stroke_fill='black')
 annotated.save(output/'eastern-union-labelled.png')
 (output/'metadata.json').write_text(json.dumps(dict(rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),source_metatiles=True,tile_scale=scale,rectangles=rects,full_world_map=False,includes_vermilion=include_vermilion),indent=2)+'\n')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',required=True);p.add_argument('--include-vermilion',action='store_true');a=p.parse_args();render(a.source,a.output,a.include_vermilion)
