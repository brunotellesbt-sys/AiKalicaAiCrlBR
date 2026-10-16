"""Keep stable native map IDs while extending the per-tile world cursor table."""
import re
import numpy as np


def rebuild(header, old_projections, projections, authored=None):
    authored=authored or {}
    packed=np.array(list(map(int,re.search(r'sWorldNavigationPixels\[\] = \{([^}]+)',header)[1].split(','))),dtype=np.int32)
    grids={};at=0
    for p in old_projections:
        w,h=p['width'],p['height'];grids[p['map']]=packed[at:at+w*h].reshape(h,w);at+=w*h
    assert at==len(packed)
    values=[];rows=[]
    for p in projections:
        n=p['map'];w,h=p['width'],p['height']
        if n in authored:a=np.array(authored[n],dtype=np.int32).reshape(h,w)
        elif n in grids:
            old=grids[n];yy=np.minimum(np.arange(h),old.shape[0]-1);xx=np.minimum(np.arange(w),old.shape[1]-1);a=old[np.ix_(yy,xx)]
        else:raise AssertionError(('Missing new map cursor grid',n))
        ident=p['id'];rows.append('{'+f'{len(values)}, (MAP_GROUP({ident})<<8)|MAP_NUM({ident}), {w}, {h}'+'},\n')
        p.update(first=len(values),count=w*h);values.extend(map(int,a.ravel()))
    header=re.sub(r'(sWorldNavigationPixels\[\] = \{)[^}]+',lambda m:m[1]+','.join(map(str,values)),header)
    start=header.index('sWorldTileGrids[] = {')+len('sWorldTileGrids[] = {');end=header.index('};',start)
    return header[:start]+'\n'+''.join(rows)+header[end:]
