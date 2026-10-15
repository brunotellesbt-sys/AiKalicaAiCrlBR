"""Render Pallet's current native terminal and its permanent ship and captain."""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from render_sea_maps import MapRenderer


def render(source, output):
    source, output = Path(source), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    r = MapRenderer(source)
    panels = []
    for name, title, box in [('PalletTown_Frlg', 'Pallet — exterior', (0, 12, 26, 30)),
                             ('JourneyPalletHarbor', 'Pallet — interior', (0, 0, 24, 15))]:
        im, m = r.render(name, npcs=False)
        for o in sorted(m['object_events'], key=lambda o:o['y']):
            if str(o['flag']) != '0' or not ('FerryPort' in o['script'] or
                    o['graphics_id'] in {'OBJ_EVENT_GFX_MR_BRINEYS_BOAT', 'OBJ_EVENT_GFX_SS_TIDAL'}):
                continue
            frame = 2 if o['graphics_id'] == 'OBJ_EVENT_GFX_MR_BRINEYS_BOAT' else 0
            sprite = r.sprite(o['graphics_id'], frame)
            dx, dy = r.sprite_offset(o['graphics_id'])
            im.paste(sprite, (o['x']*16+8-sprite.width//2+dx,
                              o['y']*16+16-sprite.height+dy), sprite)
        im = im.crop(tuple(x*16 for x in box))
        im = im.resize((im.width*3, im.height*3), Image.Resampling.NEAREST)
        im.save(output/(name+'.png'))
        panels.append((title, im))
    sheet = Image.new('RGB', (sum(im.width for _, im in panels)+12,
                              max(im.height for _, im in panels)+48), '#182030')
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22)
    x = 0
    for title, im in panels:
        draw.text((x+16, 10), title, fill='white', font=font)
        sheet.paste(im, (x, 48)); x += im.width+12
    sheet.save(output/'preview.png')
    return output/'preview.png'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(render(args.source, args.output))
