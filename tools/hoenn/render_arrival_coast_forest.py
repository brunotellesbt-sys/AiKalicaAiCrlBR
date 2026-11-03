"""Whole native-source Fuchsia and its actual connected forest/sea neighbors.

Source renders, not emulator captures. --staged previews the standalone forest
helper without editing or building the immutable input snapshot.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

from PIL import Image

from arrival_coast_forest import MAPS, repair, unpack
from candidate_layer import Layer
from prepare_arrival_coast_review import LAYER, PRIOR
from render_sea_maps import MapRenderer

PLACES = {'FuchsiaCity_Frlg':(0,0),'Route15_Frlg':(48,10),
    'JourneyFuchsiaInlet':(48,30),'JourneyKantoSouthSea':(84,30),
    'Route19_Frlg':(12,40),'JourneyKantoSouthWestSea':(36,40),
    'Route14_Frlg':(120,-30),'JourneyRoute13Coast':(144,-10),
    'Route13_Frlg':(144,-30)}


def render(source, output, staged=False):
    source,output = Path(source),Path(output)
    output.mkdir(parents=True,exist_ok=True)
    layer = Layer(source,LAYER,PRIOR)
    metadata = repair(layer) if staged else None
    renderer = MapRenderer(source)
    if staged:
        renderer.layouts = {r['id']:r for r in json.loads(layer.outputs['data/layouts/layouts.json'])['layouts']}
    # Existing private marine bank changes made by other layer167 helpers can
    # be previewed too, without writing files or modifying the frozen source.
    needed={json.loads((source/f'data/maps/{name}/map.json').read_text())['layout'] for name in PLACES}
    for name in [renderer.layouts[key] for key in needed]:
        for bank in (name['primary_tileset'],name['secondary_tileset']):
            if bank in renderer.cache: continue
            tiles,colors,words = renderer.tileset(bank)
            body = re.search(r'const struct Tileset '+bank+r'\s*=\s*\{(.*?)\};',renderer.headers,re.S)[1]
            symbol = re.search(r'\.metatiles\s*=\s*(\w+)',body)[1]
            path = re.search(r'\b'+symbol+r'\[\].*?"([^"]+)"',renderer.metas)[1]
            if path in layer.outputs: renderer.cache[bank]=(tiles,colors,unpack(layer.outputs[path]))
    records = {}
    top=-30
    connected=Image.new('RGB',(216*16,130*16),'#263642')
    for name,(x,y) in PLACES.items():
        mapping=json.loads((source/f'data/maps/{name}/map.json').read_text())
        layout=renderer.layouts[mapping['layout']]
        path=layout['blockdata_filepath']; raw=layer.outputs.get(path,(source/path).read_bytes())
        image,_=renderer.render(name,values=unpack(raw),npcs=False)
        actors=[]
        for actor in sorted(mapping['object_events'],key=lambda a:a['y']):
            if str(actor.get('flag','0')) != '0': continue
            graphic=actor['graphics_id']
            # Native city OnTransition selects Kabuto unless the dome fossil
            # flag is set. State this fixture; it changes no actual game event.
            if name=='FuchsiaCity_Frlg' and graphic=='OBJ_EVENT_GFX_VAR_0': graphic='OBJ_EVENT_GFX_KABUTO'
            frame=2 if graphic=='OBJ_EVENT_GFX_MR_BRINEYS_BOAT' and actor.get('movement_type') in ('MOVEMENT_TYPE_FACE_LEFT','MOVEMENT_TYPE_FACE_RIGHT') else 0
            sprite=renderer.sprite(graphic,frame);dx,dy=renderer.sprite_offset(graphic)
            image.paste(sprite,(actor['x']*16+8-sprite.width//2+dx,actor['y']*16+16-sprite.height+dy),sprite)
            actors.append(dict(position=[actor['x'],actor['y']],graphics_id=graphic))
        image.save(output/(name+'-whole-source.png'))
        connected.paste(image,(x*16,(y-top)*16))
        records[name]=dict(origin=[x,y],dimensions=[layout['width'],layout['height']],
            blockdata_sha256=hashlib.sha256(raw).hexdigest(),permanent_actors=actors,
            map_json_sha256=hashlib.sha256((source/f'data/maps/{name}/map.json').read_bytes()).hexdigest(),
            primary=layout['primary_tileset'],secondary=layout['secondary_tileset'])
    connected.save(output/'Fuchsia-connected-whole-source.png')
    connected.crop((40*16,(23-top)*16,64*16,(43-top)*16)).resize((768,640),Image.Resampling.NEAREST).save(output/'Fuchsia-video-seam-source.png')
    connected.crop((44*16,(23-top)*16,124*16,(34-top)*16)).save(output/'Route15-whole-south-coast-source.png')
    for filename,bounds in [('Route14-south-forest-foot-source.png',(116,24,148,35)),
                            ('Route14-east-forest-foot-source.png',(136,-14,152,-4))]:
        left,upper,right,bottom=bounds
        crop=connected.crop((left*16,(upper-top)*16,right*16,(bottom-top)*16))
        crop.resize((crop.width*2,crop.height*2),Image.Resampling.NEAREST).save(output/filename)
    result=dict(source_map_renders_not_emulator_captures=True,staged=staged,
        maps=records,forest=metadata,conditional_event_state='permanent actors only; Fuchsia fossil Kabuto',
        all_six_affected_whole_maps_and_actual_neighbors=True,
        rendered_images_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(output.glob('*.png'))},
        layouts_json_sha256=hashlib.sha256(layer.outputs.get('data/layouts/layouts.json',
            (source/'data/layouts/layouts.json').read_bytes())).hexdigest())
    marker=source/('.journey-'+LAYER)
    if marker.exists():
        result['prepared_layer_marker_sha256']=hashlib.sha256(marker.read_bytes()).hexdigest()
    (output/'review.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--staged',action='store_true')
    a=p.parse_args();r=render(a.source,a.output,a.staged);print(a.output/'review.json')
