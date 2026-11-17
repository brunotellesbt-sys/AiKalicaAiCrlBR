"""Explicit inaccessible scenery water; never a playable save target.

SCC inequality alone cannot rule out a one-way path from the playable ocean.
"""
from collections import deque
import hashlib

HEADER='src/data/journey_atlas_background.h'
LOOKUP=r'''
static bool8 JourneyAtlasBackground(u16 map, s32 x, s32 y)
{
    u32 lo=0,hi=ARRAY_COUNT(sAtlasBackground),mid;
    const struct JourneyAtlasBackgroundRun *run;
    if(x<0 || y<0 || x>=128 || y>=128) return FALSE;
    while(lo<hi)
    {
        mid=lo+(hi-lo)/2;
        run=&sAtlasBackground[mid];
        if(run->map<map || (run->map==map && (run->y<y || (run->y==y && run->right<=x))))
            lo=mid+1;
        else hi=mid;
    }
    if(lo==ARRAY_COUNT(sAtlasBackground)) return FALSE;
    run=&sAtlasBackground[lo];
    return run->map==map && run->y==y && run->left<=x && x<run->right;
}
'''


def render(plan,identities):
    rows=sorted((identities[c['name']],y,left,right) for c in plan['chunks']
                for y,left,right in c.get('decorative_water_runs',[]))
    for chunk in plan['chunks']:cells(chunk)
    if not rows:raise ValueError('No background water to protect from Emerge')
    code='''// Physical Surf water beyond the blocking route reefs is scenery.
// Reject Dive/Emerge there; ordinary water collision is not changed.
struct __attribute__((packed)) JourneyAtlasBackgroundRun { u16 map; u8 y,left,right; };
STATIC_ASSERT(sizeof(struct JourneyAtlasBackgroundRun)==5,JourneyAtlasBackgroundRunSize);
static const struct JourneyAtlasBackgroundRun sAtlasBackground[]={
'''+''.join('{'+','.join(map(str,row))+'},\n' for row in rows)+'};\n'+LOOKUP
    return code,rows


def stage(layer,plan,identities):
    from badge_story_layer import read
    code,rows=render(plan,identities);layer.stage(HEADER,code)
    path='src/overworld.c';text=read(layer,path).decode()
    include='#include "data/journey_atlas_dives.h"'
    guard='            || !JourneyAtlasDiveSurfaceCell(target, xx, yy, FALSE))'
    down='        || !JourneyAtlasDiveSurfaceCell(&gMapHeader, x, y, TRUE))'
    if text.count(include)!=1 or text.count(guard)!=1 or text.count(down)!=1:
        raise ValueError('Unreviewed Dive/Emerge background guard anchors')
    text=text.replace(include,include+'\n#include "data/journey_atlas_background.h"')
    text=text.replace(guard,'            || JourneyAtlasBackground(chunk->map, xx, yy)\n'+guard)
    text=text.replace(down,'        || JourneyAtlasBackground(map, x, y)\n'+down)
    layer.stage(path,text)
    return dict(header_sha256=hashlib.sha256(code.encode()).hexdigest(),runs=len(rows),
                table_bytes=5*len(rows),water_collision_unchanged=True,
                native_Dive_Emerge_validation_pending=True)


def parsed(source):
    from atlas_surf_reachability import _literal_rows,_compact,_function_body
    raw=source.read(HEADER).decode()
    if _compact(_function_body(raw,'JourneyAtlasBackground'))!=_compact(_function_body(LOOKUP,'JourneyAtlasBackground')):
        raise ValueError('Unreviewed compiled background lookup')
    declaration='struct __attribute__((packed)) JourneyAtlasBackgroundRun { u16 map; u8 y,left,right; };'
    if _compact(declaration) not in _compact(raw):raise ValueError('Background table ABI changed')
    rows=_literal_rows(raw,'sAtlasBackground',4)
    if rows!=sorted(rows) or len({tuple(r) for r in rows})!=len(rows):raise ValueError('Background rows not sorted/unique')
    by_identity={v:k for k,v in source.identities.items()};points=set()
    for identity,y,left,right in rows:
        name=by_identity[identity];layout=source.layout(name)
        for x,yy in cells(dict(width=layout['width'],height=layout['height'],decorative_water_runs=[[y,left,right]])):
            point=(name,x,yy)
            if point in points:raise ValueError('Compiled background runs overlap')
            points.add(point)
    return points


def cells(chunk):
    result=set();previous=None
    for run in chunk.get('decorative_water_runs',[]):
        if not isinstance(run,list) or len(run)!=3 or any(type(v) is not int for v in run):
            raise ValueError('Malformed decorative water run')
        y,left,right=run
        if not 0<=y<chunk['height'] or not 0<=left<right<=chunk['width']:
            raise ValueError('Decorative water run lies outside its real map')
        if previous is not None and (y,left)<=(previous[0],previous[2]-1):
            raise ValueError('Decorative water runs overlap or are unordered')
        result.update((x,y) for x in range(left,right));previous=run
    return result


def audit_isolation(graph,background,ocean):
    """Reject any directed gameplay path into declared background cells."""
    reached=bytearray(len(graph.keys));queue=deque()
    for node,label in enumerate(graph.labels):
        if label==ocean:reached[node]=1;queue.append(node)
    while queue:
        node=queue.popleft()
        for target in graph.successors(graph.keys[node]):
            other=graph.index.get(target)
            if other is not None and not reached[other]:
                reached[other]=1;queue.append(other)
    leaks=set()
    for node,key in enumerate(graph.keys):
        cell=key//32
        if reached[node] and cell in background:leaks.add(cell)
    return dict(cells=len(background),directed_reachable_cells=len(leaks),
                leak_samples=[list(graph.location(c)) for c in sorted(leaks)[:16]],
                directed_paths_checked=True)
