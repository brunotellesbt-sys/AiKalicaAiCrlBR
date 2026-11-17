"""Retain Three's complete terminal and let Surf go around its southern end.

The old twenty-row map ends at the terminal floor. West coast and boarding
water cannot meet without crossing that building. Extend the existing ocean
south of it, with six water rows and a closed native reef perimeter. Existing
coordinates, actors, warps, bank definitions and the whole terminal stay put.
"""
import hashlib
import json
import struct

from badge_story_layer import read

NAME='ThreeIsland_Port_Frlg'
PARENT_SHA256='d72bd163410f3e487471f3b890578aafa55ea70df6d901d2a25b17fd84858145'
OPENINGS=tuple((x,19) for x in (*range(1,4),*range(14,20)))


def extend(words,width,height,water,reef):
    if (width,height)!=(48,20) or len(words)!=width*height:
        raise ValueError('Three port dimensions differ from the reviewed complete terminal')
    if water&0xc00 or water>>12!=1 or not reef&0xc00:
        raise ValueError('Three port requires native height-one water and a blocked whole reef')
    result=list(words)
    for x,y in OPENINGS:
        if result[y*width+x]!=reef:
            raise ValueError('Three port south opening is not its authenticated complete reef')
        result[y*width+x]=water
    for _ in range(6):result.extend([reef]+[water]*(width-2)+[reef])
    result.extend([reef]*width)
    return result,height+7


def stage(layer,inputs):
    mapping=inputs.maps[NAME];layout=inputs.layout(NAME)
    if (layout['primary_tileset'],layout['secondary_tileset'],layout['layout_version'])!=(
            'gTileset_JourneySeviiSea','gTileset_JourneySeviiIntegrated123','frlg'):
        raise ValueError('Three port native bank identity changed')
    path=layout['blockdata_filepath'];raw=read(layer,path)
    if hashlib.sha256(raw).hexdigest()!=PARENT_SHA256:
        raise ValueError('Three port differs from the reviewed intact terminal')
    water=inputs.word(NAME,15,18);reef=inputs.word(NAME,15,19)
    if not inputs.water(NAME,15,18) or (water,reef)!=(0x1273,0x1643):
        raise ValueError('Three port water/whole-reef donor changed')
    words=list(struct.unpack('<960H',raw))
    result,height=extend(words,48,20,water,reef)
    # No existing event is near a removed reef; nothing is relocated.
    for field in ('object_events','warp_events','coord_events','bg_events'):
        if any((e['x'],e['y']) in OPENINGS for e in mapping.get(field,[])):
            raise ValueError('Three port opening would alter an existing event')
    layers=json.loads(read(layer,'data/layouts/layouts.json'))
    actual=next(r for r in layers['layouts'] if r['id']==layout['id'])
    if actual!=layout:raise ValueError('Three port layout was unexpectedly altered before its coast repair')
    actual['height']=height
    layer.stage('data/layouts/layouts.json',json.dumps(layers,indent=2)+'\n')
    after=struct.pack('<'+'H'*len(result),*result);layer.stage(path,after)
    return dict(kind='three-native-southern-terminal-circumnavigation',map=NAME,
        before_dimensions=[48,20],after_dimensions=[48,height],six_tile_ocean_width=True,
        existing_openings=[list(p) for p in OPENINGS],water_donor=[15,18],water_word=water,
        whole_reef_donor=[15,19],reef_word=reef,
        terminal_and_all_other_original_cells_preserved=True,events_and_boats_preserved=True,
        existing_coordinates_unchanged=True,before_sha256=PARENT_SHA256,
        after_sha256=hashlib.sha256(after).hexdigest(),native_ROM_validated=False)
