"""Deterministically encode generated art into the GBA's indexed sprite format.

This performs technical cropping, nearest-neighbor fitting and palette indexing;
character designs remain the generated source images stored alongside the metadata.
"""
import hashlib, json
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'tools/hoenn/data/crossover'
NAMES = ['EREN','LUFFY','CYRUS','MARS','JUPITER','SATURN','CHARON','GALACTIC_GRUNT_M','GALACTIC_GRUNT_F']
FRONT_BOXES = [(0,0,330,335),(330,0,640,335),(640,0,960,335),(960,0,1254,335),
               (0,335,330,690),(330,335,640,690),(640,335,960,690),(960,335,1254,690),(0,690,315,1000)]
def fit(sprite, width, height):
    sprite = sprite.crop(sprite.getbbox())
    ratio = min((width-2)/sprite.width,(height-2)/sprite.height)
    scaled = sprite.resize((max(1,round(sprite.width*ratio)),max(1,round(sprite.height*ratio))), Image.Resampling.NEAREST)
    canvas = Image.new('RGBA',(width,height))
    canvas.alpha_composite(scaled,((width-scaled.width)//2,height-scaled.height))
    return canvas
def indexed(sprite):
    # Reserve index zero for transparency. Quantize only opaque source colors.
    rgb = sprite.convert('RGB')
    palette_image = rgb.quantize(colors=15,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    palette = palette_image.getpalette()[:45]
    indexed_image = Image.new('P',sprite.size)
    indexed_image.putpalette([0,0,0]+palette+[0]*(768-48))
    alpha = sprite.getchannel('A').getdata()
    indexed_image.putdata([value+1 if opacity>=128 else 0 for value,opacity in zip(palette_image.getdata(),alpha)])
    indexed_image.info['transparency'] = 0
    return indexed_image

def encode(output):
    output = Path(output); output.mkdir(parents=True,exist_ok=True)
    front = Image.open(DATA/'trainer-sheet.png').convert('RGBA')
    walking = Image.open(DATA/'overworld-sheet.png').convert('RGBA')
    records=[]
    for i,name in enumerate(NAMES+['EREN_TITAN']):
        sprite = Image.open(DATA/'eren-titan.png').convert('RGBA') if i==9 else front.crop(FRONT_BOXES[i])
        target = output/(name.lower()+'-front.png')
        indexed(fit(sprite,64,64)).save(target)
        records.append(dict(name=name,front=target.name,size=[64,64],colors=16))
        if i==9:continue
        col,bank = i%3,i//3
        # The approved sheet orders the middle row as Mars, Jupiter, Saturn.
        xs = [[60,172,270,370],[455,558,656,766],[850,952,1056,1158]][col]
        ys = [0,157,263,377,488] if bank==0 else [494,641,752,872] if bank==1 else [876,1008,1120,1237]
        if bank==0:
            cells=[walking.crop((xs[c],ys[r],xs[c+1],ys[r+1])) for r,c in [(0,1),(1,1),(2,1),(0,0),(0,2),(1,0),(1,2),(2,0),(2,2)]]
        else:
            # These static administrators/grunts have front/back/side poses;
            # repeat idle frames rather than using inconsistent generated rows.
            cells=[walking.crop((xs[c],ys[r],xs[c+1],ys[r+1])) for r,c in [(0,0),(1,1),(1,0),(0,0),(0,2),(1,1),(1,1),(1,0),(1,2)]]
        canvas=Image.new('RGBA',(16,32*9))
        for frame,cell in enumerate(cells):canvas.alpha_composite(fit(cell,16,32),(0,32*frame))
        target=output/(name.lower()+'-walking.png');indexed(canvas).save(target)
        records[-1]['overworld']=target.name
    return records
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(encode(a.output),indent=2))
