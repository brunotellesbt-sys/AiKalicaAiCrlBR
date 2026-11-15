"""Connect fixed Dive glyphs to their actual adjacent route ink.

The deep patch is only 5x3 tiles. Its approach must also cross the one-tile
pixel margin; Origens approaches from above because the pixel below is land.
Only authenticated glyph pixels, blue ink and real ocean may carry this short
native feature access. The map artwork and the deep patch stay unchanged.
"""
from collections import deque
from copy import deepcopy

from atlas_surf_geometry import rasterize
from atlas_surf_scenery import _runs


def attach_accesses(truth,reservations,route_pixels):
    route=rasterize(route_pixels);result=[]
    for original in reservations:
        row=deepcopy(original);site=row['dive_site'];ax,ay=site['atlas']
        glyph={(ax,ay),(ax-1,ay),(ax+1,ay),(ax,ay-1)}
        expected={(ax,ay):0,(ax-1,ay):15,(ax+1,ay):15,(ax,ay-1):15}
        if any(truth.pixel(p)!=color for p,color in expected.items()):
            raise ValueError(('Fixed Dive glyph changed; do not invent an ocean approach',site['name']))
        ox,oy=row['origin'];right,bottom=ox+row['width'],oy+row['height']
        start=(8*ax+4,8*ay+6)
        def allowed(p):
            x,y=p
            if not (ox<=x<right and oy<=y<bottom):return False
            pixel=x//8,y//8
            return pixel in glyph or truth.pixel(pixel) in (1,2)
        def stroke(p,dx,dy):
            return {(p[0]+(k if dy else 0),p[1]+(k if dx else 0)) for k in range(-2,3)}
        previous={start:None};todo=deque([start]);goal=None
        while todo:
            p=todo.popleft()
            if p in route:goal=p;break
            for dx,dy in ((0,1),(0,-1),(-1,0),(1,0)):
                q=p[0]+dx,p[1]+dy
                if q in previous:continue
                paint=stroke(q,dx,dy)
                if all(allowed(c) for c in paint):previous[q]=(p,paint);todo.append(q)
        if goal is None:
            raise ValueError(('Fixed Dive patch lacks a short real-ink approach inside its reservation',site['name']))
        path=[goal];paint=set();p=goal
        while previous[p] is not None:
            p,cells=previous[p];paint.update(cells);path.append(p)
        path.reverse()
        deep={(8*ax+2+x,8*ay+5+y) for y in range(3) for x in range(5)}
        paint|=deep
        runs={(ox+x,oy+y) for y,a,b in row.get('additional_water_runs',[]) for x in range(a,b)}
        runs|=paint;row['additional_water_runs']=_runs((x-ox,y-oy) for x,y in runs)
        evidence=dict(kind='fixed-Dive-glyph-to-adjacent-blue-ink',
                      art_sha256=dict(truth.array_sha256),fixed_atlas=site['atlas'],
                      glyph_pixels=[dict(atlas=list(p),color=truth.pixel(p)) for p in sorted(glyph)],
                      path_global_tiles=[list(p) for p in path],
                      reached_route_tile=list(goal),reached_blue_pixel=[goal[0]//8,goal[1]//8],
                      approach_width=5,deep_patch_cells=15,
                      painted_cells=[list(p) for p in sorted(paint,key=lambda p:(p[1],p[0]))],
                      land_pixels_crossed=False,native_validated=False)
        row['native_water_evidence']['authenticated_approach']=evidence
        row['evidence']['authenticated_approach']=evidence
        result.append(row)
    return result
