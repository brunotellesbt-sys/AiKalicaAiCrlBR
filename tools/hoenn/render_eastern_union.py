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
 if include_vermilion:
  # Native south connection offset 0: city sits directly above WorldSea00.
  rects.append(dict(map='VermilionCity_Frlg',x=190,y=-40,width=48,height=40))
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
 if include_vermilion:
  x=(190+34-xmin)*scale;y=(38-40-ymin)*scale
  draw.line([(x,y-45),(x,y+85)],fill=(255,65,45),width=5)
  draw.polygon([(x,y+85),(x-12,y+66),(x+12,y+66)],fill=(255,65,45))
  draw.text((x+18,y-35),'Vermilion: southeast Surf channel',font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',24),fill='white',stroke_width=2,stroke_fill='black')
 annotated.save(output/'eastern-union-labelled.png')
 (output/'metadata.json').write_text(json.dumps(dict(rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),source_metatiles=True,tile_scale=scale,rectangles=rects,full_world_map=False,includes_vermilion=include_vermilion),indent=2)+'\n')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',required=True);p.add_argument('--include-vermilion',action='store_true');a=p.parse_args();render(a.source,a.output,a.include_vermilion)
