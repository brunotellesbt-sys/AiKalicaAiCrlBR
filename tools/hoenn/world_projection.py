"""Build one continuous, shared projection for the native outdoor map graph."""

def project(maps, layouts, coords):
 by_id={m['id']:n for n,m in maps.items()}
 seams=[];dimensions={n:(layouts[maps[n]['layout']]['width'],layouts[maps[n]['layout']]['height']) for n in coords}
 parent={}
 def root(k):
  parent.setdefault(k,k)
  while parent[k]!=k:parent[k]=parent[parent[k]];k=parent[k]
  return k
 def join(a,b):
  a,b=root(a),root(b)
  if a!=b:parent[b]=a
 for n in sorted(coords):
  m=maps[n];w,h=dimensions[n];cx,cy=coords[n]
  for c in m.get('connections') or []:
   other=by_id.get(c['map'],c['map']);direction=c['direction'];offset=c['offset']
   if other not in coords or direction not in ['left','right','up','down']:continue
   ow,oh=dimensions[other]
   if direction in ['left','right']:
    lo,hi=max(0,offset),min(h-1,offset+oh-1)
    if lo>hi:continue
    edge=0 if direction=='left' else w-1;box=[edge,lo,edge,hi]
    pairs=[((n,edge,y),(other,ow-1 if direction=='left' else 0,y-offset)) for y in range(lo,hi+1)]
   else:
    lo,hi=max(0,offset),min(w-1,offset+ow-1)
    if lo>hi:continue
    edge=0 if direction=='up' else h-1;box=[lo,edge,hi,edge]
    pairs=[((n,x,edge),(other,x-offset,oh-1 if direction=='up' else 0)) for x in range(lo,hi+1)]
   for aa,bb in pairs:join(aa,bb)
   ox,oy=coords[other]
   seams.append(dict(map=n,other=other,direction=direction,offset=offset,box=box,position=[(cx+ox)//2,(cy+oy)//2]))
 # Every connected border tile shares one node, including three/four-way corners.
 members={}
 for k in sorted(parent):members.setdefault(root(k),[]).append(k)
 roots=sorted(members);index={k:i for i,k in enumerate(roots)};neighbors=[set() for _ in roots];targets=[]
 for k in roots:
  centers=[coords[n] for n in sorted({v[0] for v in members[k]})]
  targets.append(tuple(sum(v[axis] for v in centers)/len(centers) for axis in [0,1]))
 for k in sorted(parent):
  n,x,y=k;i=index[root(k)]
  for dx,dy in [(1,0),(0,1)]:
   other=(n,x+dx,y+dy)
   if other in parent:
    j=index[root(other)]
    if i!=j:neighbors[i].add(j);neighbors[j].add(i)
 # Smooth changes along a shore as well as across it. The weak centre prior
 # keeps the approved atlas anchors, without an abrupt change at T junctions.
 edges=[sorted(v) for v in neighbors];values=targets[:];prior=1/256
 for _ in range(1024):
  values=[tuple((prior*targets[i][axis]+sum(values[j][axis] for j in near))/(prior+len(near)) if near else targets[i][axis] for axis in [0,1]) for i,near in enumerate(edges)]
 positions=[tuple(round(v) for v in xy) for xy in values]
 max_step=max((max(abs(positions[i][axis]-positions[j][axis]) for axis in [0,1]) for i,near in enumerate(edges) for j in near),default=0)
 assert max_step<=2,('Abrupt shore projection',max_step)
 border={n:[] for n in coords}
 for k in sorted(parent):
  n,x,y=k;xx,yy=positions[index[root(k)]];border[n].append([x,y,x,y,xx,yy])
 anchors=[];projections=[]
 for n in sorted(coords):
  m=maps[n];w,h=dimensions[n];first=len(anchors);cx,cy=coords[n]
  anchors.append([w//2,h//2,w//2,h//2,cx,cy]);anchors.extend(border[n])
  projections.append(dict(map=n,id=m['id'],first=first,count=len(border[n]),width=w,height=h,center=[cx,cy]))
 data='struct JourneyWorldAnchor { s16 left, top, right, bottom; u8 x, y; };\nstruct JourneyWorldProjection { u32 first; u16 map, count; };\nstatic const struct JourneyWorldAnchor sWorldAnchors[] = {\n'+''.join('{'+','.join(map(str,a))+'},\n' for a in anchors)+'};\nstatic const struct JourneyWorldProjection sWorldProjections[] = {\n'+''.join('{'+str(p['first'])+', (MAP_GROUP('+p['id']+')<<8)|MAP_NUM('+p['id']+'), '+str(p['count'])+'},\n' for p in projections)+'};\n'
 return dict(anchors=anchors,projections=projections,seams=seams,boundary_nodes=len(roots),maximum_neighbor_pixel_step=max_step,data=data)
