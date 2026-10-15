"""Render the implemented harbor's native tiles and permanent actors."""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from prepare_sootopolis_harbor import HARBOR
from render_sea_maps import MapRenderer


def render(source, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    renderer = MapRenderer(source)
    panels = []
    for name, title, box in [('SootopolisCity', 'EXTERIOR', (14, 33, 31, 49)),
                             (HARBOR, 'INTERIOR', (0, 0, 24, 15))]:
        im, m = renderer.render(name, npcs=False)
        for obj in m['object_events']:
            if str(obj['flag']) != '0' or not (
                    obj['script'] == 'Journey_FerryPort17'
                    or obj['graphics_id'] == 'OBJ_EVENT_GFX_JOURNEY_SUBMARINE'):
                continue
            sprite = renderer.sprite(obj['graphics_id'], 0)
            dx, dy = renderer.sprite_offset(obj['graphics_id'])
            im.paste(sprite, (obj['x']*16+8-sprite.width//2+dx,
                              obj['y']*16+16-sprite.height+dy), sprite)
        im = im.crop(tuple(v*16 for v in box))
        im = im.resize((im.width*3, im.height*3), Image.Resampling.NEAREST)
        im.save(output/(name+'.png'))
        panels.append((title, im))
    height = max(im.height for _, im in panels)+48
    sheet = Image.new('RGB', (sum(im.width for _, im in panels)+12, height), '#182030')
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22)
    x = 0
    for title, im in panels:
        draw.text((x+16, 10), title, fill='white', font=font)
        sheet.paste(im, (x, 48))
        x += im.width+12
    sheet.save(output/'preview.png')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    render(args.source, args.output)
