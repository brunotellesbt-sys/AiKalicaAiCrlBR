"""Finish Slateport's two clipped boulders without erasing the cliff below.

The native cliff and beach composites can each contain pieces of a larger
boulder. Remove their complete orphan fragments and continue the native
shore below, retaining physical flags. Intact rocks, including objects split
across the actual Route109 connection, remain complete and unchanged.
"""
import hashlib
import struct

from badge_story_layer import read

NAME='SlateportCity'
ANCHORS=((36,6),(38,15))
HORIZONTAL=((35,17),(36,17))
BEACH=((3,57),(4,57))
# Every General metatile whose eight-word definition uses the native large
# grey rock graphics 0x1B0..0x1BF, including fused beach/cliff variants.
LARGE_ROCK_IDS=frozenset((0x150,0x151,0x152,0x153,0x154,0x155,0x158,0x159,
    0x15a,0x15b,0x15c,0x15d,0x160,0x161,0x162,0x163,0x164,0x165,0x168,0x169,
    0x16a,0x16b,0x16c,0x16d))
COMPLETE_PATTERNS=((0x150,0x151,0x158,0x159),(0x152,0x153,0x158,0x159))


def census(inputs,override=None):
    """Account for every large-rock piece in Slateport, across native seams."""
    override=override or {};seen=set();complete=[];covered=set();pieces=[]
    def resolve(name,x,y):
        layout=inputs.layout(name)
        if 0<=x<layout['width'] and 0<=y<layout['height']:return name,x,y
        direction='left' if x<0 else 'right' if x>=layout['width'] else 'up' if y<0 else 'down'
        for c in inputs.maps[name].get('connections') or []:
            if c['direction']!=direction:continue
            other=inputs.by_id[c['map']];l=inputs.layout(other);offset=c['offset']
            xx=x-offset if direction in ('up','down') else x+l['width'] if direction=='left' else x-layout['width']
            yy=y-offset if direction in ('left','right') else y+l['height'] if direction=='up' else y-layout['height']
            if 0<=xx<l['width'] and 0<=yy<l['height']:
                if (l['primary_tileset'],l['secondary_tileset'],l['layout_version'])!=(
                        layout['primary_tileset'],layout['secondary_tileset'],layout['layout_version']):
                    raise ValueError('Slateport whole boulder crosses a different graphics bank')
                return other,xx,yy
        return None
    def word(p):
        name,x,y=p
        return override[name][y*inputs.layout(name)['width']+x] if name in override else inputs.word(name,x,y)
    layout=inputs.layout(NAME)
    for y in range(layout['height']):
        for x in range(layout['width']):
            p=NAME,x,y;mid=word(p)&1023
            if mid not in LARGE_ROCK_IDS:continue
            pieces.append(p)
            for pattern in COMPLETE_PATTERNS:
                for q,m in enumerate(pattern):
                    if m!=mid:continue
                    a,b=x-q%2,y-q//2
                    cells=[resolve(NAME,a+dx,b+dy) for dy in range(2) for dx in range(2)]
                    if any(c is None for c in cells) or tuple(word(c)&1023 for c in cells)!=pattern:continue
                    key=tuple(cells)
                    if key not in seen:
                        seen.add(key);complete.append(dict(cells=[list(c) for c in cells],metatiles=list(pattern)))
                    covered.update(cells)
    return dict(kind='all-used-Slateport-General-large-rock-composites',
        pieces=[list(p) for p in pieces],complete_objects=complete,
        orphan_pieces=[list(p) for p in pieces if p not in covered],
        actual_native_connections_reviewed=True,other_maps_and_graphics_families_not_certified=True)


def stage(layer,inputs):
    layout=inputs.layout(NAME)
    if (layout['width'],layout['height'],layout['primary_tileset'],layout['secondary_tileset'])!=(
            40,60,'gTileset_General','gTileset_Slateport'):
        raise ValueError('Slateport coast bank or dimensions changed')
    path=layout['blockdata_filepath'];before=read(layer,path)
    values=list(struct.unpack('<2400H',before));changes=[]
    before_census=census(inputs,{NAME:values})
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
    for cells,expected,target,donor in [
            (HORIZONTAL,(0x055a,0x055b),0x189,(34,17,0x1189)),
            (BEACH,(0x0552,0x0553),0x12c,(6,58,0x112c))]:
        if inputs.word(NAME,*donor[:2])!=donor[2]:raise ValueError('Slateport native shoreline donor changed')
        for (x,y),old in zip(cells,expected):
            index=y*40+x
            if values[index]!=old:raise ValueError('Slateport horizontal/beach boulder fragment changed')
            if any(e['x']==x and e['y']==y for field in ('object_events','warp_events','coord_events','bg_events')
                    for e in inputs.maps[NAME].get(field,[])):
                raise ValueError('Slateport shoreline repair overlaps an event')
            result=(old&~1023)|target;values[index]=result
            changes.append(dict(tile=[x,y],before=old,after=result))
    after_census=census(inputs,{NAME:values})
    if after_census['orphan_pieces']:raise ValueError('Slateport still contains a large-rock fragment')
    if before_census['complete_objects']!=after_census['complete_objects']:
        raise ValueError('Slateport repair changed an intact native rock')
    after=struct.pack('<2400H',*values);layer.stage(path,after)
    return dict(kind='slateport-complete-cliff-without-boulder-slices',map=NAME,
        complete_visible_slices_removed=[list(p) for p in ANCHORS],cells=changes,
        horizontal_slice_removed=[list(p) for p in HORIZONTAL],beach_slice_removed=[list(p) for p in BEACH],
        before_census=before_census,after_census=after_census,
        straight_cliff_donor=[36,5],collision_elevation_events_and_water_routes_preserved=True,
        before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(after).hexdigest(),
        native_ROM_validated=False)
