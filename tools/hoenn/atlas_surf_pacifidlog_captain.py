"""Move Pacifidlog's ferry captain off the bridge into the nearest house.

Keep the ferry script/port11, flags, boat and all native numeric object IDs.
The house's existing residents and exit corridor remain available.
"""
from copy import deepcopy
import hashlib
import json

from atlas_surf_object_ids import native_local_id,validate_object_ids
from badge_story_layer import read

TOWN='PacifidlogTown'
HOUSE='PacifidlogTown_House3'
SCRIPT='Journey_FerryPort11'
POSITION=(7,6)


def stage(layer,inputs):
    paths=[f'data/maps/{name}/map.json' for name in (TOWN,HOUSE)]
    raw=[read(layer,path) for path in paths];town,house=map(json.loads,raw)
    found=[(i,event) for i,event in enumerate(town['object_events']) if event.get('script')==SCRIPT]
    if len(found)!=1:raise ValueError('Pacifidlog ferry captain must have exactly one outdoor source')
    index,captain=found[0]
    if (captain['x'],captain['y'],captain['graphics_id'])!=(11,27,'OBJ_EVENT_GFX_SAILOR'):
        raise ValueError('Pacifidlog captain differs from the obstructing bridge actor')
    closest=min((warp for warp in town['warp_events'] if warp['dest_map'].startswith('MAP_PACIFIDLOG_TOWN_HOUSE')),
                key=lambda w:abs(w['x']-captain['x'])+abs(w['y']-captain['y']))
    if closest['dest_map']!=house['id'] or (closest['x'],closest['y'])!=(12,24):
        raise ValueError('Pacifidlog House3 is no longer the nearest native house')
    if any(e.get('script')==SCRIPT for e in house['object_events']):
        raise ValueError('Pacifidlog indoor captain would be duplicated')
    for x,y in [(4,6),(5,6),(6,6),POSITION,(4,7),(5,7)]:
        word=inputs.word(HOUSE,x,y)
        if word&0xc00 or word>>12!=3 or inputs.water(HOUSE,x,y):
            raise ValueError('Pacifidlog captain approach is not native dry floor')
        if any(e['x']==x and e['y']==y for e in house['object_events']):
            raise ValueError('Pacifidlog captain approach overlaps a resident')
    for i,event in enumerate(town['object_events']):event['native_local_id']=native_local_id(event,i)
    moved=deepcopy(town['object_events'].pop(index))
    if moved['native_local_id'] in validate_object_ids(house['object_events']):
        raise ValueError('Pacifidlog captain numeric local ID collides inside nearest house')
    moved.update(x=POSITION[0],y=POSITION[1],movement_type='MOVEMENT_TYPE_FACE_LEFT')
    house['object_events'].append(moved)
    validate_object_ids(town['object_events']);validate_object_ids(house['object_events'])
    after=[]
    for path,value in zip(paths,(town,house)):
        encoded=(json.dumps(value,indent=2)+'\n').encode();layer.stage(path,encoded);after.append(encoded)
    return dict(kind='pacifidlog-ferry-captain-inside-nearest-house',source_map=TOWN,source_tile=[11,27],
        destination_map=HOUSE,destination_tile=list(POSITION),door=[12,24],numeric_local_id=moved['native_local_id'],
        script=SCRIPT,port_number=11,bridge_freed=True,boat_and_all_other_actors_preserved=True,
        house_residents_and_warps_preserved=True,terrain_unchanged=True,native_ROM_validated=False,
        before_sha256={p:hashlib.sha256(b).hexdigest() for p,b in zip(paths,raw)},
        after_sha256={p:hashlib.sha256(b).hexdigest() for p,b in zip(paths,after)})
