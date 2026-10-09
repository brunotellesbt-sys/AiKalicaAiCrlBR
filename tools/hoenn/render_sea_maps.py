"""Render actual map blockdata and source tilesets; no invented terrain."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def generate(source, output):
    source=Path(source); output=Path(output);output.mkdir(parents=True,exist_ok=True)
    layouts={x['id']:x for x in json.loads((source/'data/layouts/layouts.json').read_text())['layouts']}
    headers=(source/'src/data/tilesets/headers.h').read_text()
    metas=(source/'src/data/tilesets/metatiles.h').read_text()
    cache={}
    def tileset(name):
        if name in cache:return cache[name]
        h=re.search(r'const struct Tileset '+name+r'\s*=\s*\{(.*?)\};',headers,re.S)[1]
        symbol=re.search(r'\.metatiles = (\w+)',h)[1]
        path=re.search(r'\b'+symbol+r'\[\].*?"([^"]+)"',metas)[1]
        folder=(source/path).parent
        tiles=Image.open(folder/'tiles.png');assert tiles.mode=='P'
        colors=[]
        for p in sorted((folder/'palettes').glob('*.pal'))[:16]:
            lines=p.read_text().splitlines();colors.append([tuple(map(int,l.split())) for l in lines[3:] if l.strip()])
        words=struct.unpack('<'+'H'*((source/path).stat().st_size//2),(source/path).read_bytes())
        cache[name]=(tiles,colors,words)
        return cache[name]
    def render(name):
        m=json.loads((source/f'data/maps/{name}/map.json').read_text());l=layouts[m['layout']]
        primary=tileset(l['primary_tileset']);secondary=tileset(l['secondary_tileset'])
        cutoff=640 if l['layout_version']=='frlg' else 512
        palcut=7 if l['layout_version']=='frlg' else 6
        values=struct.unpack('<'+'H'*(l['width']*l['height']),(source/l['blockdata_filepath']).read_bytes())
        result=Image.new('RGB',(l['width']*16,l['height']*16))
        for cell,block in enumerate(values):
            mid=block&1023;words=(primary if mid<cutoff else secondary)[2]
            index=mid if mid<cutoff else mid-cutoff
            entries=words[index*8:(index+1)*8];assert len(entries)==8
            for layer in range(2):
                for quadrant in range(4):
                    entry=entries[layer*4+quadrant];tid=entry&1023;bank=entry>>12
                    tiles=(primary if tid<cutoff else secondary)[0];tid=tid if tid<cutoff else tid-cutoff
                    cols=tiles.width//8; colors=(primary if bank<palcut else secondary)[1][bank]
                    for y in range(8):
                        for x in range(8):
                            xx=7-x if entry&1024 else x; yy=7-y if entry&2048 else y
                            value=tiles.getpixel((tid%cols*8+xx,tid//cols*8+yy))
                            if layer and value==0:continue
                            result.putpixel((cell%l['width']*16+quadrant%2*8+x,cell//l['width']*16+quadrant//2*8+y),colors[value])
        result.save(output/(name+'.png'))
        return result,m
    groups={
        'oeste-kanto-hoenn':['JourneyCinnabarSouthSea','JourneyWestRiver','JourneyRustboroCoast','JourneyDewfordCoast'],
        'leste-hoenn-sevii':['JourneyHoennNorthSea','JourneyHoennMiddleSea','JourneyHoennSouthSea','JourneyPacifidlogSea','JourneyFuchsiaSea'],
        'mar-sevii':['JourneyWorldSea%02d'%i for i in range(10)],
        'canais-sevii':['JourneyWorldLane'+i for i in ['10','11','20','21','30','31']]}
    report={}
    for title,names in groups.items():
        panels=[]
        for name in names:
            img,m=render(name)
            scale=min(1,650/img.width,450/img.height)
            img=img.resize((int(img.width*scale),int(img.height*scale)),Image.Resampling.NEAREST)
            label=name.removeprefix('Journey')
            connections=' / '.join(c['map'].removeprefix('MAP_') for c in (m.get('connections') or []))
            panels.append((img,label,connections))
            report[name]=dict(map_sha256=hashlib.sha256((source/f'data/maps/{name}/map.json').read_bytes()).hexdigest(), blockdata_sha256=hashlib.sha256((source/layouts[m['layout']]['blockdata_filepath']).read_bytes()).hexdigest(), width_tiles=layouts[m['layout']]['width'],height_tiles=layouts[m['layout']]['height'],connections=m.get('connections'),terrain_only=True)
        rows=(len(panels)+1)//2
        canvas=Image.new('RGB',(1360,rows*525),(15,32,45));draw=ImageDraw.Draw(canvas)
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
        small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
        for i,(img,label,connections) in enumerate(panels):
            x=20+(i%2)*680;y=15+(i//2)*525
            draw.text((x,y),label,font=font,fill='white');canvas.paste(img,(x,y+30))
            # Exact identifiers can be long; details also appear in JSON/doc.
            draw.text((x,y+490),connections[:92],font=small,fill=(180,220,240))
        canvas.save(output/(title+'.png'))
    (output/'maps.json').write_text(json.dumps(dict(rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(), maps=report, terrain_only=True, campaign_validation=False),indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True);p.add_argument('--output',required=True);a=p.parse_args();generate(a.source,a.output)
