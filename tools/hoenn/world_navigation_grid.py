"""Bound atlas movement over the complete tile graph, including shared borders.

For each coordinate, take the midpoint of its lower/upper 2-Lipschitz
 envelopes. A multi-source shortest-path transform computes both envelopes.
This preserves already consistent positions while removing local spikes.
Dependencies numpy/scipy are needed only when preparing a new source layer.
"""
def build(r):
    import numpy as np
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import dijkstra
    ps=r['projections'];values=[];edges=[];ids={};offset=0
    for p in ps:
     w,h=p['width'],p['height'];grid=np.arange(offset,offset+w*h).reshape(h,w);ids[p['map']]=grid;offset+=w*h
     aa=np.array(r['anchors'][p['first']:p['first']+p['count']+1]);y,x=np.indices((h,w));x=x.flatten();y=y.flatten()
     dx=np.maximum(np.maximum(aa[:,0,None]-x,x-aa[:,2,None]),0);dy=np.maximum(np.maximum(aa[:,1,None]-y,y-aa[:,3,None]),0);dist=dx*dx+dy*dy
     weights=1048576//np.maximum(dist,1);z=((weights.T@aa[:,4:6]+weights.sum(axis=0)[:,None]//2)//weights.sum(axis=0)[:,None]).astype(np.int16)
     for ai,a in enumerate(aa):
      mask=dist[ai]==0;z[mask]=a[4:6]
     values.extend(z);edges.extend([np.stack([grid[:,:-1].ravel(),grid[:,1:].ravel()]),np.stack([grid[:-1,:].ravel(),grid[1:,:].ravel()])])
    for link in r['seams']:
     a,b=ids[link['map']],ids[link['other']];l,t,rr,bb=link['box'];xs=np.arange(l,rr+1);ys=np.arange(t,bb+1)
     if link['direction'] in ['left','right']:ys=np.arange(t,bb+1);xs=np.full(len(ys),l);ox=np.full(len(ys),b.shape[1]-1 if link['direction']=='left' else 0);oy=ys-link['offset']
     else:xs=np.arange(l,rr+1);ys=np.full(len(xs),t);ox=xs-link['offset'];oy=np.full(len(xs),b.shape[0]-1 if link['direction']=='up' else 0)
     edges.append(np.stack([a[ys,xs],b[oy,ox]]))
    N=offset;v=np.array(values);e=np.concatenate(edges,axis=1);cost=np.full(e.shape[1],2.0)
    # Linked border tiles represent exactly the same geographic point.
    # Every following edge joins duplicate boundary tiles at zero distance.
    interior=sum(item.shape[1] for item in edges[:len(ps)*2]);cost[interior:]=0.0
    rows=np.concatenate([e[0],e[1],np.full(N,N)]);cols=np.concatenate([e[1],e[0],np.arange(N)])
    def bound(v):
        out=[]
        for axis in [0,1]:
            curves=[]
            for f in [v[:,axis],255-v[:,axis]]:
                mat=coo_matrix((np.concatenate([cost,cost,f]),(rows,cols)),shape=(N+1,N+1)).tocsr()
                curves.append(dijkstra(mat,directed=True,indices=N)[:N])
            out.append(np.floor((curves[0]+255-curves[1])/2+0.5).astype(np.int16))
        return np.stack(out,axis=1)
    new=bound(v)
    return ids,new,dict(tiles=N,changed_tiles=int((new!=v).any(axis=1).sum()),maximum_neighbor_pixel_step=int(np.abs(new[e[0]]-new[e[1]]).max()),maximum_seam_delta=int(np.abs(new[e[0,interior:]]-new[e[1,interior:]]).max()))
