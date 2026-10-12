"""Keep prisoners fully inside the cells and visible behind the energy lattice."""
import argparse,io,json
from pathlib import Path
from PIL import Image
from candidate_layer import Layer
from prepare_final_balance import PRIOR,LAYER as PREVIOUS
LAYER='prison-visibility';PRIOR=PRIOR+[PREVIOUS]


def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if result:=layer.existing():return result
    source=layer.source
    folder='data/tilesets/secondary/journey_galactic_prison'
    colors=[tuple(map(int,line.split())) for line in (source/(folder+'/palettes/15.pal')).read_text().splitlines()[3:]]
    p=folder+'/tiles.png';tiles=Image.open(source/p)
    for prop in [0,1,4,7]:
        for tile in range(16):
            number=352+prop*16+tile
            for y in range(8):
                for x in range(8):
                    px=number%16*8+x;py=number//16*8+y
                    if max(colors[tiles.getpixel((px,py))])<100:tiles.putpixel((px,py),0)
    buf=io.BytesIO();tiles.save(buf,format='PNG');layer.stage(p,buf.getvalue())
    p='data/maps/JourneyGalacticHall/map.json';m=json.loads((source/p).read_text())
    for o in m['object_events']:
        if o['graphics_id'].startswith('OBJ_EVENT_GFX_SPECIES('):o['y']=5
    layer.stage(p,json.dumps(m,indent=2)+'\n')
    return layer.finish(prisoners_fully_within_cell_bounds=True,transparent_energy_lattice=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
