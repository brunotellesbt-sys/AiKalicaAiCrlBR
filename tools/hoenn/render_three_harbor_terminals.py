"""Render the actual Cinnabar, Cerulean and Petalburg terminal tiles and ships."""
import argparse
import json
from pathlib import Path
from PIL import Image
from render_sea_maps import MapRenderer


def render(source,output):
    source,output=Path(source),Path(output);output.mkdir(parents=True,exist_ok=True);r=MapRenderer(source)
    ports=json.loads((source/'.journey-three-harbor-terminals').read_text())['ports']
    for p in ports:
        for name,box in [(p['exterior'],p['crop']),(p['interior'],[0,0,24,15])]:
            im,m=r.render(name,npcs=False)
            for o in sorted(m['object_events'],key=lambda o:o['y']):
                if str(o['flag'])!='0' or not ('FerryPort' in o['script'] or o['script']=='ThreeHarbors_PetalburgCaptain' or o['script']=='JourneyCompactPort_Boat' or o['graphics_id']=='OBJ_EVENT_GFX_SS_TIDAL'):continue
                sprite=r.sprite(o['graphics_id'],0);dx,dy=r.sprite_offset(o['graphics_id'])
                im.paste(sprite,(o['x']*16+8-sprite.width//2+dx,o['y']*16+16-sprite.height+dy),sprite)
            im=im.crop(tuple(v*16 for v in box))
            im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST).save(output/(name+'.png'))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();render(a.source,a.output)
