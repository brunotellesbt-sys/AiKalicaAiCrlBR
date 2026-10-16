"""Show the current Lavender terminal and its shared Pallet-style interior."""
import argparse
from pathlib import Path
from PIL import Image
from render_sea_maps import MapRenderer


def render(source, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    r = MapRenderer(Path(source))
    for name, box in [('JourneyRoute12Shipyard', (0,24,33,56)),
                      ('JourneyLavenderHarbor', (0,0,24,15))]:
        im, _ = r.render(name, npcs=True)
        im = im.crop(tuple(v*16 for v in box))
        im.resize((im.width*3, im.height*3), Image.Resampling.NEAREST).save(output/(name+'.png'))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    render(a.source, a.output)
