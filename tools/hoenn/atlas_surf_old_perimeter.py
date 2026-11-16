"""Remove whole obsolete outer reefs where Titans' authored route crosses.

The scenery extraction included the old sea map's two-column perimeter in
the complete cave stamp. In its new position this outer limit is inside the
route. Each 0x243 metatile is one complete small reef over native water;
none belongs to the mountain, beach, actors or portal.
"""
import hashlib
import struct

from atlas_surf_geometry import rasterize
from badge_story_layer import read

PARENT='JourneyWorldSea03'
PARENT_SHA256='9f4eddbfc5acbfa3a37f9d1bee6acfc362a0a33c66d03ad967ee692dab7f772b'
STAMP='JourneyWorldSea03:000'
SOURCE_CELLS=tuple((x,y) for y in range(19,25) for x in (62,63))


def stage(layer,inputs,plan,placements):
    layout=inputs.layout(PARENT)
    if hashlib.sha256(inputs.read(layout['blockdata_filepath'])).hexdigest()!=PARENT_SHA256:
        raise ValueError('Titans parent perimeter changed')
    if (layout['width'],layout['height'])!=(64,48):
        raise ValueError('Titans obsolete boundary dimensions changed')
    row=next(r for r in placements if r['stamp']==STAMP)
    chunk=next(r for r in plan['chunks'] if r['name']==row['name'])
    if (row['stamp_offset'],row['origin'])!=([9,9],[1585,421]):
        raise ValueError('Titans whole cave was relocated')
    donor=[61,19];water=inputs.word(PARENT,*donor)
    if water!=0x112b or not inputs.water(PARENT,*donor):
        raise ValueError('Titans native water donor changed')
    route=rasterize(set(map(tuple,plan['route_pixels'])))
    path=f'data/layouts/{row["name"]}/map.bin'
    raw=read(layer,path);words=list(struct.unpack('<'+'H'*(len(raw)//2),raw));repairs=[]
    for x,y in SOURCE_CELLS:
        target=x-33+9,y+9
        global_tile=chunk['origin'][0]+target[0],chunk['origin'][1]+target[1]
        old=inputs.word(PARENT,x,y)
        if old!=0x1643 or words[target[1]*chunk['width']+target[0]]!=old:
            raise ValueError('Titans former outer reef is not intact')
        if global_tile not in route:
            raise ValueError('Titans obsolete reef is outside authenticated route water')
        if any(e['x']==x and e['y']==y for field in ('object_events','warp_events','coord_events','bg_events')
               for e in inputs.maps[PARENT].get(field,[])):
            raise ValueError('Titans old perimeter repair would alter an event')
        words[target[1]*chunk['width']+target[0]]=water
        repairs.append(dict(source_tile=[x,y],target_tile=list(target),global_tile=list(global_tile),
                            old_word=old,new_word=water))
    after=struct.pack('<'+'H'*len(words),*words);layer.stage(path,after)
    return dict(kind='whole-obsolete-outer-reef-removal',map=row['name'],stamp=STAMP,
        parent_map=PARENT,parent_sha256=PARENT_SHA256,water_donor=donor,
        before_sha256=hashlib.sha256(raw).hexdigest(),after_sha256=hashlib.sha256(after).hexdigest(),
        cells=repairs,mountain_beach_events_and_portal_preserved=True,native_ROM_validated=False)
