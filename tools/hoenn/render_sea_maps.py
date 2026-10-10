"""Render actual map blockdata and source tilesets; no invented terrain."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

class MapRenderer:
    def __init__(self,source):
        self.source=Path(source)
        self.layouts={x['id']:x for x in json.loads((self.source/'data/layouts/layouts.json').read_text())['layouts']}
        self.headers=(self.source/'src/data/tilesets/headers.h').read_text()
        self.metas=(self.source/'src/data/tilesets/metatiles.h').read_text()
        self.cache={}
        self.tile_images={}
        self.sprites={}

    def sprite(self,graphics_id):
        if graphics_id in self.sprites:return self.sprites[graphics_id]
        root=self.source/'src/data/object_events'
        pointers=(root/'object_event_graphics_info_pointers.h').read_text()
        symbol=re.search(r'\['+re.escape(graphics_id)+r'\]\s*=\s*&([A-Za-z0-9_]+)',pointers)[1]
        info=re.search(r'const struct ObjectEventGraphicsInfo '+symbol+r' = \{(.*?)\};',(root/'object_event_graphics_info.h').read_text(),re.S)[1]
        pic=re.search(r'\.images = (\w+)',info)[1]
        table=re.search(r'static const struct SpriteFrameImage '+pic+r'\[\] = \{(.*?)\};',(root/'object_event_pic_tables.h').read_text(),re.S)[1]
        graphic=re.search(r'(?:overworld_(?:ascending_frames|frame)|obj_frame_tiles)\((\w+)',table)[1]
        path=re.search(r'\b'+graphic+r'\[\].*?"([^"]+)"',(root/'object_event_graphics.h').read_text())[1]
        width=int(re.search(r'\.width = (\d+)',info)[1]);height=int(re.search(r'\.height = (\d+)',info)[1])
        original=Image.open((self.source/path).with_suffix('.png'))
        # PNG palette is the same indexed source consumed by the native build.
        palette_tag=re.search(r'\.paletteTag = (\w+)',info)[1]
        palette_symbol=re.search(r'\{(gObjectEventPal_\w+),\s*'+palette_tag+r'\}',(self.source/'src/event_object_movement.c').read_text())[1]
        palette_path=re.search(r'\b'+palette_symbol+r'\[\].*?"([^"]+)"',(root/'object_event_graphics.h').read_text())[1]
        palette_lines=(self.source/palette_path).with_suffix('.pal').read_text().splitlines()[3:]
        native_palette=[int(v) for line in palette_lines for v in line.split()]
        frame=original.crop((0,0,width,height));frame.putpalette(native_palette)
        sprite=frame.convert('RGBA')
        for y in range(height):
            for x in range(width):
                if original.getpixel((x,y))==0:sprite.putpixel((x,y),(0,0,0,0))
        self.sprites[graphics_id]=sprite
        return sprite

    def tileset(self,name):
        if name in self.cache:return self.cache[name]
        h=re.search(r'const struct Tileset '+name+r'\s*=\s*\{(.*?)\};',self.headers,re.S)[1]
        symbol=re.search(r'\.metatiles = (\w+)',h)[1]
        path=re.search(r'\b'+symbol+r'\[\].*?"([^"]+)"',self.metas)[1]
        folder=(self.source/path).parent
        tiles=Image.open(folder/'tiles.png');assert tiles.mode=='P'
        colors=[]
        for p in sorted((folder/'palettes').glob('*.pal'))[:16]:
            lines=p.read_text().splitlines();colors.append([tuple(map(int,l.split())) for l in lines[3:] if l.strip()])
        words=struct.unpack('<'+'H'*((self.source/path).stat().st_size//2),(self.source/path).read_bytes())
        self.cache[name]=(tiles,colors,words)
        return self.cache[name]
    def render(self,name, values=None, dimensions=None, npcs=True):
        m=json.loads((self.source/f'data/maps/{name}/map.json').read_text());l=self.layouts[m['layout']]
        primary=self.tileset(l['primary_tileset']);secondary=self.tileset(l['secondary_tileset'])
        cutoff=640 if l['layout_version']=='frlg' else 512
        palcut=7 if l['layout_version']=='frlg' else 6
        l=dict(l)
        if dimensions:l['width'],l['height']=dimensions
        if values is None:values=struct.unpack('<'+'H'*(l['width']*l['height']),(self.source/l['blockdata_filepath']).read_bytes())
        result=Image.new('RGB',(l['width']*16,l['height']*16))
        for cell,block in enumerate(values):
            mid=block&1023
            key=(l['primary_tileset'],l['secondary_tileset'],mid)
            if key in self.tile_images:
                result.paste(self.tile_images[key],(cell%l['width']*16,cell//l['width']*16));continue
            tile_image=Image.new('RGB',(16,16))
            words=(primary if mid<cutoff else secondary)[2]
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
                            tile_image.putpixel((quadrant%2*8+x,quadrant//2*8+y),colors[value])
            self.tile_images[key]=tile_image
            result.paste(tile_image,(cell%l['width']*16,cell//l['width']*16))
        if npcs:
            for event in sorted(m['object_events'],key=lambda e:e['y']):
                sprite=self.sprite(event['graphics_id'])
                result.paste(sprite,(event['x']*16+8-sprite.width//2,event['y']*16+16-sprite.height),sprite)
        return result,m

def generate(source, output):
    source=Path(source); output=Path(output);output.mkdir(parents=True,exist_ok=True)
    renderer=MapRenderer(source); layouts=renderer.layouts
    groups={
        'oeste-kanto-hoenn':['JourneyCinnabarSouthSea','JourneyWestRiver','JourneyRustboroCoast','JourneyRustboroGate','JourneyDewfordCoast','JourneyDewfordGate'],
        'leste-hoenn-sevii':['JourneyHoennNorthSea','JourneyHoennMiddleSea','JourneyHoennSouthSea','JourneyPacifidlogSea','JourneyFuchsiaSea'],
        'mar-sevii':['JourneyWorldSea%02d'%i for i in range(10)],
        'cavernas-remotas':[x['map'] for x in json.loads((source/'.journey-sanctuaries').read_text())['sites']],
        'canais-sevii':['JourneyWorldLane'+i for i in ['10','11','20','21','30','31']]}
    report={}
    for title,names in groups.items():
        panels=[]
        for name in names:
            img,m=renderer.render(name)
            img.save(output/(name+'.png'))
            scale=min(1,650/img.width,450/img.height)
            img=img.resize((int(img.width*scale),int(img.height*scale)),Image.Resampling.NEAREST)
            label=name.removeprefix('Journey')
            connections=' / '.join(c['map'].removeprefix('MAP_') for c in (m.get('connections') or []))
            panels.append((img,label,connections))
            report[name]=dict(map_sha256=hashlib.sha256((source/f'data/maps/{name}/map.json').read_bytes()).hexdigest(), blockdata_sha256=hashlib.sha256((source/layouts[m['layout']]['blockdata_filepath']).read_bytes()).hexdigest(), width_tiles=layouts[m['layout']]['width'],height_tiles=layouts[m['layout']]['height'],connections=m.get('connections'),object_events=m['object_events'],terrain_only=False)
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
    (output/'maps.json').write_text(json.dumps(dict(rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(), maps=report, terrain_only=False, campaign_validation=False),indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True);p.add_argument('--output',required=True);a=p.parse_args();generate(a.source,a.output)
