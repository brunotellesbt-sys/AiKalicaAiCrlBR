"""Render real coast tiles, sandbanks, border reefs and existing NPC sprites."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
from render_sea_maps import MapRenderer

def render(source,output):
 source=Path(source);output=Path(output);output.mkdir(parents=True,exist_ok=True);r=MapRenderer(source)
 report=json.loads((source/'.journey-kanto-open-sea').read_text());rows=report['landscape'];metadata=[]
 audit=json.loads((output.parent/'playable-validation/coast-connectivity/coast-connectivity.json').read_text())
 all_rows=audit['terrain'];known={row['map'] for row in rows}
 rows=rows+[row for row in all_rows if row['map'] not in known]
 for row in rows:
  name=row['map'];im,_=r.render(name,npcs=True);im.save(output/(name+'.png'))
  metadata.append(dict(row,blockdata_sha256=hashlib.sha256((source/r.layouts[json.loads((source/'data/maps'/name/'map.json').read_text())['layout']]['blockdata_filepath']).read_bytes()).hexdigest()))
 for filename,items in [('coast-overview.png',rows[:9]),('channels-overview.png',rows[9:27]),('all-seas-overview.png',all_rows)]:
  canvas=Image.new('RGB',(960,240*((len(items)+2)//3)),(16,24,32));draw=ImageDraw.Draw(canvas)
  for i,row in enumerate(items):
   im=Image.open(output/(row['map']+'.png'));im.thumbnail((304,208),Image.Resampling.NEAREST);x=(i%3)*320;y=(i//3)*240
   draw.text((x+4,y+3),row['map'].removeprefix('Journey'),fill='white');canvas.paste(im,(x,y+24))
  canvas.save(output/filename)
 (output/'terrain.json').write_text(json.dumps(dict(rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),source_metatiles=True,npc_sprites=True,maps=metadata),indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True);p.add_argument('--output',required=True);a=p.parse_args();render(a.source,a.output)
