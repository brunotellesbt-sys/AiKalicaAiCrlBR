"""Finish Slateport's two clipped boulders without erasing the cliff below.

The right cliff face contains a two-tile slice of a larger boulder at each
anchor. The missing pieces are forest/building ground, so extending a rock
would overwrite the existing coast. Remove each complete visible slice and
continue the native straight cliff face. Preserve all physical flags.
"""
import hashlib
import struct

from badge_story_layer import read

NAME='SlateportCity'
ANCHORS=((36,6),(38,15))


def stage(layer,inputs):
    layout=inputs.layout(NAME)
    if (layout['width'],layout['height'],layout['primary_tileset'],layout['secondary_tileset'])!=(
            40,60,'gTileset_General','gTileset_Slateport'):
        raise ValueError('Slateport coast bank or dimensions changed')
    path=layout['blockdata_filepath'];before=read(layer,path)
    values=list(struct.unpack('<2400H',before));changes=[]
    if inputs.word(NAME,36,5)!=0x1190:
        raise ValueError('Slateport native straight cliff donor changed')
    for x,y in ANCHORS:
        for dy,expected in ((0,0x0564),(1,0x056c)):
            index=(y+dy)*40+x
            if values[index]!=expected:raise ValueError('Slateport clipped boulder differs from reviewed whole-map slice')
            if any(e['x']==x and e['y']==y+dy for field in ('object_events','warp_events','coord_events','bg_events')
                   for e in inputs.maps[NAME].get(field,[])):
                raise ValueError('Slateport clipped boulder repair would alter an event')
            result=(expected&~1023)|0x190
            values[index]=result;changes.append(dict(tile=[x,y+dy],before=expected,after=result))
    after=struct.pack('<2400H',*values);layer.stage(path,after)
    return dict(kind='slateport-complete-cliff-without-boulder-slices',map=NAME,
        complete_visible_slices_removed=[list(p) for p in ANCHORS],cells=changes,
        straight_cliff_donor=[36,5],collision_elevation_events_and_water_routes_preserved=True,
        before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(after).hexdigest(),
        native_ROM_validated=False)
