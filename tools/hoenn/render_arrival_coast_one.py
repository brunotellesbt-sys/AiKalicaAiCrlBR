"""Render all of One Island and its physical neighbors, with native objects.

Static source review, never emulator evidence. The boundary rock's alias uses
the exact existing pointer slot resolved by the native build.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

from render_sea_maps import MapRenderer

PLACES = {'OneIsland_Frlg': (16,120),
          'OneIsland_TreasureBeach_Frlg': (16,140),
          'JourneySurfLink05000': (0,127),
          'OneIsland_KindleRoad_Frlg': (40,0)}
ALIAS = 'OBJ_EVENT_GFX_JOURNEY_COAST_BOUNDARY_ROCK'
SLOT = 'OBJ_EVENT_GFX_UNUSED_NATU_DOLL'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def render(source, output):
    source,output = Path(source),Path(output)
    output.mkdir(parents=True,exist_ok=True)
    renderer = MapRenderer(source)
    canvas = Image.new('RGB',(64*16,180*16),'#263642')
    maps = {}
    for name,(x,y) in PLACES.items():
        picture,mapping = renderer.render(name,npcs=False)
        actors = []
        for actor in sorted(mapping['object_events'],key=lambda row:row['y']):
            if str(actor.get('flag','0')) != '0':
                continue
            graphic = actor['graphics_id']
            if graphic == ALIAS:
                header = (source/'include/constants/event_objects.h').read_text()
                assert '#define '+ALIAS+' '+SLOT in header
            frame = 2 if graphic == 'OBJ_EVENT_GFX_MR_BRINEYS_BOAT' and actor['movement_type'] in (
                'MOVEMENT_TYPE_FACE_LEFT','MOVEMENT_TYPE_FACE_RIGHT') else 0
            sprite = renderer.sprite(graphic,frame)
            dx,dy = renderer.sprite_offset(graphic)
            picture.paste(sprite,(actor['x']*16+8-sprite.width//2+dx,
                                 actor['y']*16+16-sprite.height+dy),sprite)
            actors.append(dict(tile=[actor['x'],actor['y']],graphics_id=actor['graphics_id']))
        picture.save(output/(name+'-whole-source.png'))
        canvas.paste(picture,(x*16,y*16))
        layout = renderer.layouts[mapping['layout']]
        maps[name] = dict(origin=[x,y],map_json_sha256=digest(source/f'data/maps/{name}/map.json'),
                          blockdata_sha256=digest(source/layout['blockdata_filepath']),
                          primary=layout['primary_tileset'],secondary=layout['secondary_tileset'],
                          dimensions=[layout['width'],layout['height']],permanent_actors=actors)
    canvas.save(output/'One-connected-whole-source.png')
    canvas.crop((12*16,120*16,26*16,144*16)).resize((448,768),Image.Resampling.NEAREST).save(
        output/'One-west-cape-source.png')
    metadata = dict(source_map_renders_not_emulator_captures=True,maps=maps,
                    conditional_event_state='permanent actors only; one static native animation frame',
                    layouts_json_sha256=digest(source/'data/layouts/layouts.json'),
                    images_sha256={p.name:digest(p) for p in sorted(output.glob('*.png'))})
    marker = source/'.journey-arrival-coast-review'
    if marker.exists():
        metadata['prepared_layer_marker_sha256'] = digest(marker)
    (output/'review.json').write_text(json.dumps(metadata,indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    render(args.source,args.output)
