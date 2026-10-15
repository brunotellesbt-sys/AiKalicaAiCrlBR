"""Reconcile existing tile GPS at newly connected coasts, preserving valid values."""
import re
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra


def reconcile(header, projections, maps, fixed_maps=()):
    packed=np.array(list(map(int,re.search(r'sWorldNavigationPixels\[\] = \{([^}]+)',header)[1].split(','))),dtype=np.int32)
    old=np.stack([packed&255,packed>>8],axis=1)
    grids={};offset=0;edges=[]
    for p in projections:
        w,h=p['width'],p['height'];a=np.arange(offset,offset+w*h).reshape(h,w);grids[p['map']]=a;offset+=w*h
        edges.extend([np.stack([a[:,:-1].ravel(),a[:,1:].ravel()]),np.stack([a[:-1,:].ravel(),a[1:,:].ravel()])])
    assert offset==len(old)
    interior=sum(e.shape[1] for e in edges);byid={m['id']:n for n,m in maps.items()};seams=[]
    for n,a in grids.items():
        h,w=a.shape
        for c in maps[n].get('connections') or []:
            o=byid.get(c['map']);d=c['direction'];off=c['offset']
            if o not in grids or d not in ['left','right','up','down']:continue
            b=grids[o];oh,ow=b.shape
            for t in range(max(0,off),min(h if d in ['left','right'] else w,off+(oh if d in ['left','right'] else ow))):
                x,y=(0 if d=='left' else w-1,t) if d in ['left','right'] else (t,0 if d=='up' else h-1)
                xx,yy=(ow-1 if d=='left' else 0,t-off) if d in ['left','right'] else (t-off,oh-1 if d=='up' else 0)
                seams.append((a[y,x],b[yy,xx]))
    edges.append(np.array(seams).T);e=np.concatenate(edges,axis=1);cost=np.full(e.shape[1],2.0);cost[interior:]=0
    n=len(old);rows=np.concatenate([e[0],e[1],np.full(n,n)]);cols=np.concatenate([e[1],e[0],np.arange(n)]);axes=[]
    for axis in [0,1]:
        bounds=[]
        for values in [old[:,axis],255-old[:,axis]]:
            matrix=coo_matrix((np.concatenate([cost,cost,values]),(rows,cols)),shape=(n+1,n+1)).tocsr()
            bounds.append(dijkstra(matrix,directed=True,indices=n)[:n])
        axes.append(np.floor((bounds[0]+255-bounds[1])/2+0.5).astype(np.int16))
    final=np.stack(axes,axis=1)
    if fixed_maps:
        fixed=np.concatenate([grids[name].ravel() for name in fixed_maps])
        fixed_rows=np.concatenate([e[0],e[1],np.full(len(fixed),n)])
        fixed_cols=np.concatenate([e[1],e[0],fixed])
        for axis in [0,1]:
            bounds=[]
            for values in [old[fixed,axis],255-old[fixed,axis]]:
                matrix=coo_matrix((np.concatenate([cost,cost,values]),(fixed_rows,fixed_cols)),shape=(n+1,n+1)).tocsr()
                bounds.append(dijkstra(matrix,directed=True,indices=n)[:n])
            lower,upper=255-bounds[1],bounds[0]
            assert np.all(lower<=upper),('Inconsistent authored route coordinates',axis)
            # Clipping a Lipschitz field between Lipschitz bounds retains the
            # step limit while keeping the authored passage coordinates fixed.
            final[:,axis]=np.clip(final[:,axis],lower,upper).astype(np.int16)
        assert np.array_equal(final[fixed],old[fixed])
    maximum=int(abs(final[e[0]]-final[e[1]]).max());seam_delta=int(abs(final[e[0,interior:]]-final[e[1,interior:]]).max())
    assert maximum<=2 and seam_delta==0
    result=re.sub(r'(sWorldNavigationPixels\[\] = \{)[^}]+',lambda m:m[1]+','.join(str(int(x)|(int(y)<<8)) for x,y in final),header)
    changed={name:int((old[a.ravel()]!=final[a.ravel()]).any(axis=1).sum()) for name,a in grids.items()}
    return result,dict(compiled_gps_tiles=n,changed_tiles=sum(changed.values()),changed_maps={k:v for k,v in changed.items() if v},maximum_neighbor_pixel_step=maximum,maximum_seam_delta=seam_delta,linked_border_tiles=len(seams))
