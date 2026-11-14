"""Register new map labels without changing a single atlas art array byte."""
import json

from atlas_surf_source import Source, POINT
from atlas_surf_truth import decode_atlas
from badge_story_layer import read


def stage(layer, plan, owner_mapping):
    path='src/data/journey_world_map.h'
    original=read(layer,path).decode()
    before=decode_atlas(original)
    parents=Source(layer.source)
    old_points=parents.anchors()
    existing_ids={match[1] for match in POINT.finditer(original)}
    extra=[];rows=[]
    for chunk in plan['chunks']:
        name=chunk['name'];mapping=json.loads(read(layer,f'data/maps/{name}/map.json'))
        owner=owner_mapping.get(name,chunk.get('ecology_owner'))
        if owner not in parents.maps or mapping['id'] in existing_ids:
            raise ValueError(('New chart label lacks a real owner or replaces an existing point',name,owner))
        parent=old_points.get(owner)
        label=chunk.get('atlas_label',parent['label'] if parent else 'OPEN SEA')
        if not isinstance(label,str) or any(c in label for c in ('"','\\','\n','\r')):
            raise ValueError('Unsafe atlas label')
        ox,oy=chunk['origin']
        points=[(x,y) for y,left,right in chunk['water_runs'] for x in range(left,right)]
        if points:
            cx,cy=min(points,key=lambda p:(abs(2*p[0]-chunk['width'])+abs(2*p[1]-chunk['height']),p[1],p[0]))
        else:cx,cy=chunk['width']//2,chunk['height']//2
        atlas=[(ox+cx)//8,(oy+cy)//8]
        if not (0<=atlas[0]<224 and 0<=atlas[1]<112):
            raise ValueError(('New atlas label lies outside immutable chart',name,atlas))
        ident=mapping['id'];section=mapping['region_map_section']
        extra.append('    {(MAP_GROUP('+ident+')<<8)|MAP_NUM('+ident+'), '+section+', '
                     +str(atlas[0])+', '+str(atlas[1])+', COMPOUND_STRING("'+label+'")},\n')
        existing_ids.add(ident)
        rows.append(dict(map=name,owner=owner,atlas=atlas,label=label))
    start=original.find('sWorldPoints[]')
    if start<0:
        raise ValueError('Native world point registry missing')
    end=original.find('};',start)
    if end<0:
        raise ValueError('Native world point registry truncated')
    updated=original[:end]+''.join(extra)+original[end:]
    if dict(decode_atlas(updated).array_sha256)!=dict(before.array_sha256):
        raise AssertionError('Map label registration changed immutable artwork')
    parents.assert_unchanged()
    layer.stage(path,updated)
    return dict(kind='atlas-new-map-label-registry',points=rows,
                art_sha256=dict(before.array_sha256),historical_points_preserved=True,
                labels_are_not_player_location_proof=True,native_validated=False)
