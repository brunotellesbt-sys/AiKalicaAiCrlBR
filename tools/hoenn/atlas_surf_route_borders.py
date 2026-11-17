"""Plan thin reef limits with ordinary water beyond, preserving playable cells.

Only the authenticated generated reef fill is eligible. Native stamp cores,
doors, objects and every formerly passable word are preserved. Native adapter
faces and the undefined visual border need separate treatment; this staged
proposal is not a release or a native movement certificate.
"""
from copy import deepcopy
import hashlib
import struct

from atlas_surf_overlay import OverlaySource
from badge_story_layer import read


def stage_undefined_drawing(layer,metadata,identities):
    """Change only undefined-cell artwork; physical border APIs stay intact."""
    records={r['map']:r for r in metadata['geometry']['chunks']}
    rows=sorted((identities[c['name']],records[c['name']]['water_word']&1023,
                 records[c['name']]['reef_word']&1023) for c in metadata['geometry_plan']['chunks']
                if c['kind'] not in ('adapter','dive'))
    helper='''
static bool8 JourneyAtlasUndefinedWater(s32 x, s32 y, u16 *result)
{
    static const struct { u16 map,water,reef; } limits[]={
'''+''.join('{'+','.join(map(str,row))+'},\n' for row in rows)+'''};
    u16 map=((u16)(u8)gSaveBlock1Ptr->location.mapGroup<<8)|(u8)gSaveBlock1Ptr->location.mapNum;
    const struct MapLayout *layout=gMapHeader.mapLayout;
    u32 lo=0,hi=ARRAY_COUNT(limits),mid;
    s32 xx=x,yy=y;
    bool8 edge=FALSE;
    while(lo<hi) { mid=lo+(hi-lo)/2; if(limits[mid].map<map) lo=mid+1; else hi=mid; }
    if(lo==ARRAY_COUNT(limits) || limits[lo].map!=map || layout==NULL) return FALSE;
    if(x==-1 && y>=0 && y<layout->height) {xx=0;edge=TRUE;}
    if(x==layout->width && y>=0 && y<layout->height) {xx=layout->width-1;edge=TRUE;}
    if(y==-1 && x>=0 && x<layout->width) {yy=0;edge=TRUE;}
    if(y==layout->height && x>=0 && x<layout->width) {yy=layout->height-1;edge=TRUE;}
    *result=(edge && !(layout->map[yy*layout->width+xx]&MAPGRID_COLLISION_MASK))
        ?limits[lo].reef:limits[lo].water;
    return TRUE;
}
'''
    path='src/fieldmap.c';text=read(layer,path).decode()
    signature='static bool8 JourneyAtlasVisualBlock(s32 x, s32 y, u16 *result)\n{'
    if text.count(signature)!=1 or text.count('    if (owner == NULL)\n        return FALSE;')!=1:
        raise ValueError('Unreviewed undefined drawing anchors')
    text=text.replace(signature,helper+'\n'+signature,1)
    text=text.replace('    if (owner == NULL)\n        return FALSE;',
        '    if (owner == NULL)\n        return JourneyAtlasUndefinedWater(x, y, result);',1)
    layer.stage(path,text)
    return dict(maps=len(rows),only_undefined_metatile_artwork_changed=True,
        collision_elevation_and_GetMapBorderIdAt_unchanged=True,native_cameras_pending=True)


def _native_core_rectangles(inputs,row):
    kind=row['kind']
    if kind=='ordinary':return []
    if kind not in ('stamp','cave'):return [[0,0,row['width'],row['height']]]
    if 'source_rect' in row:
        _,_,w,h=row['source_rect'];x,y=row['stamp_offset']
        return [[x,y,x+w,y+h]]
    components=row.get('evidence',{}).get('whole_components') or []
    if not components or len({c['parent_map'] for c in components})!=1:
        raise ValueError(('Native scenery lacks one authenticated shared source footprint',row['name']))
    fringes={r['stamp']:r for r in row.get('native_water_evidence',{}).get('authenticated_native_fringe',[])}
    if len(components)>1:
        result=[]
        if len(row['member_stamps'])!=len(components):raise ValueError('Native scenery member inventory changed')
        for stamp,component in zip(row['member_stamps'],components):
            fringe=fringes.get(stamp);cells=fringe.get('cells',[]) if fringe else []
            if not cells:
                # Some native objects have no wet fringe or actor. Locate
                # their complete authenticated rectangle, preserving every
                # identical occurrence rather than guessing a single origin.
                source=component['parent_map'];sx,sy,w,h=component['source_rect']
                pattern=[inputs.word(source,sx+x,sy+y) for y in range(h) for x in range(w)]
                raw=struct.pack('<'+'H'*len(pattern),*pattern)
                if hashlib.sha256(raw).hexdigest()!=component['word_sha256']:
                    raise ValueError(('Native whole object source changed',source,stamp))
                matches=[]
                for yy in range(row['height']-h+1):
                    for xx in range(row['width']-w+1):
                        if all(inputs.word(row['name'],xx+x,yy+y)==pattern[y*w+x] for y in range(h) for x in range(w)):
                            matches.append([xx,yy,xx+w,yy+h])
                if not matches:raise ValueError(('Whole native object has no exact target rectangle',row['name'],stamp))
                result.extend(matches);continue
            deltas={(c['target_tile'][0]-c['source_tile'][0],c['target_tile'][1]-c['source_tile'][1]) for c in cells}
            if len(deltas)!=1:raise ValueError('Native scenery fringe has conflicting translations')
            dx,dy=next(iter(deltas));x,y,w,h=component['source_rect'];rect=[x+dx,y+dy,x+dx+w,y+dy+h]
            if not 0<=rect[0]<rect[2]<=row['width'] or not 0<=rect[1]<rect[3]<=row['height']:
                raise ValueError('Native protected core lies outside its actual reservation')
            result.append(rect)
        return result
    left=min(c['source_rect'][0] for c in components);top=min(c['source_rect'][1] for c in components)
    right=max(c['source_rect'][0]+c['source_rect'][2] for c in components)
    bottom=max(c['source_rect'][1]+c['source_rect'][3] for c in components)
    halo=row['evidence']['camera_halo']
    if [right-left+2*halo,bottom-top+2*halo]!=[row['width'],row['height']]:
        raise ValueError(('Native scenery camera/core bounds changed',row['name']))
    return [[c['source_rect'][0]-left+halo,c['source_rect'][1]-top+halo,
             c['source_rect'][0]-left+halo+c['source_rect'][2],
             c['source_rect'][1]-top+halo+c['source_rect'][3]] for c in components]


def _neighbor(inputs,name,x,y,dx,dy):
    layout=inputs.layout(name);xx,yy=x+dx,y+dy
    if 0<=xx<layout['width'] and 0<=yy<layout['height']:return name,xx,yy
    direction='left' if xx<0 else 'right' if xx>=layout['width'] else 'up' if yy<0 else 'down'
    # Match the first real connection whose bounded rectangle owns this cell.
    for c in inputs.maps[name].get('connections') or []:
        if c['direction']!=direction:continue
        other=inputs.by_id[c['map']];target=inputs.layout(other);offset=c['offset']
        a=xx-offset if direction in ('up','down') else xx+target['width'] if direction=='left' else xx-layout['width']
        b=yy-offset if direction in ('left','right') else yy+target['height'] if direction=='up' else yy-layout['height']
        if 0<=a<target['width'] and 0<=b<target['height']:return other,a,b
    return None


def _runs(points):
    result=[]
    for y in sorted({y for x,y in points}):
        xs=sorted(x for x,yy in points if yy==y);start=previous=xs[0]
        for x in xs[1:]:
            if x!=previous+1:result.append([y,start,previous+1]);start=x
            previous=x
        result.append([y,start,previous+1])
    return result


def plan(inputs,metadata):
    records={r['map']:r for r in metadata['geometry']['chunks']};changes=[];summary=[];pending=[]
    for row in metadata['geometry_plan']['chunks']:
        name=row['name'];layout=inputs.layout(name);record=records[name]
        if row['kind'] in ('adapter','dive'):
            pending.append(dict(map=name,reason='preserve complete native coast face or Dive patch until separate review'))
            continue
        if [layout['primary_tileset'],layout['secondary_tileset']]!=record['donor_banks']:
            raise ValueError(('Reef/water donor bank differs from the actual map',name))
        reef,water=record['reef_word'],record['water_word']
        if not reef&0xc00 or water&0xc00 or water>>12!=1:
            raise ValueError('Border proposal requires the exact blocked whole reef and native Surf donor')
        flags=inputs.behavior_flags;behavior=inputs.behavior(name,water)
        if behavior>=len(flags['values']) or not flags['values'][behavior]&flags['surf_flag']:
            raise ValueError(('Background donor is not actual native water',name))
        cores=_native_core_rectangles(inputs,row);before=inputs.words(name);after=list(before);cleared=[];kept=[]
        for y in range(layout['height']):
            for x in range(layout['width']):
                if before[y*layout['width']+x]!=reef:continue
                if any(a<=x<c and b<=y<d for a,b,c,d in cores):continue
                neighbors=[_neighbor(inputs,name,x,y,dx,dy) for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]]
                if any(p is not None and not inputs.word(*p)&0xc00 for p in neighbors):
                    kept.append((x,y));continue
                after[y*layout['width']+x]=water;cleared.append((x,y))
        if any(a!=b for a,b in zip(before,after) if not a&0xc00):
            raise ValueError('Thin-border proposal changed an existing playable cell')
        if cleared:
            raw=struct.pack('<'+'H'*len(after),*after)
            changes.append(dict(map=name,path=layout['blockdata_filepath'],raw=raw,
                before_sha256=hashlib.sha256(inputs.read(layout['blockdata_filepath'])).hexdigest(),
                after_sha256=hashlib.sha256(raw).hexdigest(),background_water_runs=_runs(cleared),
                retained_limit_reef_runs=_runs(kept),protected_native_core_rectangles=cores))
        summary.append(dict(map=name,ordinary_background_water_cells=len(cleared),
            retained_limit_reef_cells=len(kept),protected_native_core_rectangles=cores))
    inputs.assert_unchanged()
    return changes,dict(kind='thin-native-reef-boundary-source-proposal',maps=summary,
        background_water_cells=sum(r['ordinary_background_water_cells'] for r in summary),
        existing_playable_words_changed=0,complete_native_stamp_rectangles_preserved=True,
        remaining_native_face_reviews=pending,undefined_visual_border_treatment_pending=True,
        outside_water_must_be_proven_unreachable_from_playable_graph=True,
        source_graph_finalized=False,native_ROM_validated=False,final_release_validated=False)


def stage(layer,metadata):
    changes,report=plan(OverlaySource(layer),metadata)
    result=deepcopy(metadata);by_name={r['name']:r for r in result['geometry_plan']['chunks']}
    for row in changes:
        layer.stage(row['path'],row['raw'])
        by_name[row['map']]['decorative_water_runs']=row['background_water_runs']
    result['route_border_redesign']=report
    result.update(source_audit_passed=False,native_validated=False,release_eligible=False,
                  NATIVE_CONTRACT_FINALIZED=False,public_roms_updated=False)
    return result,report
