"""Draw orthogonal marine paths from actual connected maps, preserving land art."""
import argparse,heapq,json,re,struct
from pathlib import Path
from candidate_layer import Layer
from prepare_rival_walk_and_coast_audit import PRIOR,LAYER as PREVIOUS
from prepare_world_dex_map import decode,encode
from world_projection import project
LAYER='connected-sea-chart';PRIOR=PRIOR+[PREVIOUS]

def route(image,old,a,b,sea):
 # Land and town artwork stay intact. Endpoints approach the nearest sea pixel.
 def water(p):return p in sea
 def nearest(p):return min(sea,key=lambda q:(abs(q[0]-p[0])+abs(q[1]-p[1]),q))
 a,b=nearest(a),nearest(b);start=(*a,4);cost={start:0};previous={};queue=[(abs(a[0]-b[0])+abs(a[1]-b[1]),0,start)]
 while queue:
  _,g,node=heapq.heappop(queue)
  if g!=cost[node]:continue
  x,y,d=node
  if (x,y)==b:
   path=[(x,y)]
   while node in previous:node=previous[node];path.append(node[:2])
   path.reverse();corners=[path[0]]
   for i in range(1,len(path)-1):
    if (path[i][0]-path[i-1][0],path[i][1]-path[i-1][1])!=(path[i+1][0]-path[i][0],path[i+1][1]-path[i][1]):corners.append(path[i])
   if corners[-1]!=path[-1]:corners.append(path[-1])
   return path,corners
  for nd,(dx,dy) in enumerate([(1,0),(-1,0),(0,1),(0,-1)]):
   nx,ny=x+dx,y+dy
   if not water((nx,ny)):continue
   nxt=(nx,ny,nd);ng=g+(3 if old.getpixel((nx,ny))==2 else 5)+(8 if d not in [nd,4] else 0)
   if ng<cost.get(nxt,10**9):cost[nxt]=ng;previous[nxt]=node;heapq.heappush(queue,(ng+3*(abs(nx-b[0])+abs(ny-b[1])),ng,nxt))
 raise ValueError(('Disconnected chart water',a,b))

def prepare(source):
 layer=Layer(source,LAYER,PRIOR)
 if old:=layer.existing():return old
 s=layer.source;ld=json.loads((s/'data/layouts/layouts.json').read_text());ls={l['id']:l for l in ld['layouts']}
 # The original connected sea grid reserves exactly 17 columns per harbor.
 # Retain the approved cottage/rim/pier; discard only the added water column.
 h=ls['LAYOUT_ISLAND_HARBOR_FRLG'];assert h['width']==18;w=h['width'];v=list(struct.unpack('<'+'H'*w*h['height'],(s/h['blockdata_filepath']).read_bytes()))
 assert all(v[y*w+17]==0x112B for y in range(h['height']))
 v=[t for y in range(h['height']) for t in v[y*w:y*w+17]];h['width']=17
 layer.stage(h['blockdata_filepath'],struct.pack('<'+'H'*len(v),*v));layer.stage('data/layouts/layouts.json',json.dumps(ld,indent=2)+'\n')
 maps={p.parent.name:json.loads(p.read_text()) for p in (s/'data/maps').glob('*/map.json')};byid={m['id']:n for n,m in maps.items()}
 old=json.loads((s/'.journey-port-orientation-finish').read_text());coords={p['map']:tuple(p['center']) for p in old['projections']};geometry=project(maps,ls,coords);layer.stage('src/data/journey_world_position.h',geometry.pop('data'))
 p='src/data/journey_world_map.h';header=(s/p).read_text();before=decode(header);im=before.copy()
 for y in range(112):
  for x in range(224):
   if im.getpixel((x,y))==2:im.putpixel((x,y),1)
 edges=[];seen=set();records=[]
 def marine(n):return maps[n]['map_type']=='MAP_TYPE_OCEAN_ROUTE' or n.startswith('Journey') and maps[n]['map_type']=='MAP_TYPE_ROUTE' or 'Harbor' in n
 for n,m in sorted(maps.items()):
  for c in m.get('connections') or []:
   other=byid.get(c['map'])
   if c['direction'] not in ['up','down','left','right'] or n not in coords or other not in coords or not(marine(n) or marine(other)):continue
   pair=tuple(sorted([n,other]))
   if pair in seen:continue
   seen.add(pair);edges.append(pair)
 # Registered remote caves receive a spur from their actual entrance map.
 for n,m in sorted(maps.items()):
  if n not in coords or not marine(n):continue
  for warp in m.get('warp_events') or []:
   other=byid.get(warp['dest_map'])
   if other not in coords or not other.startswith('JourneySanctuary'):continue
   pair=tuple(sorted([n,other]))
   if pair not in seen:seen.add(pair);edges.append(pair)
 unseen={(x,y) for y in range(112) for x in range(224) if im.getpixel((x,y)) in [1,2,14]};components=[]
 while unseen:
  start=unseen.pop();component={start};queue=[start]
  while queue:
   x,y=queue.pop()
   for q in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
    if q in unseen:unseen.remove(q);component.add(q);queue.append(q)
  components.append(component)
 sea=max(components,key=len);paths={}
 for a,b in edges:
  endpoints=tuple(sorted([coords[a],coords[b]]))
  if endpoints not in paths:paths[endpoints]=route(im,before,*endpoints,sea)
  path,corners=paths[endpoints]
  for xy in path:
   if before.getpixel(xy) in [1,2]:im.putpixel(xy,2)
  records.append(dict(source=a,destination=b,centers=[coords[a],coords[b]],polyline=corners,actual_connection=True))
 assert all(before.getpixel((x,y))==im.getpixel((x,y)) for y in range(112) for x in range(224) if before.getpixel((x,y)) not in [1,2])
 assert all(a[0]==b[0] or a[1]==b[1] for r in records for a,b in zip(r['polyline'],r['polyline'][1:]))
 layer.stage(p,encode(header,im))
 return layer.finish(orthogonal_marine_paths=records,distinct_drawn_paths=len(paths),all_land_and_town_art_preserved=True,sea_links_derived_from_actual_connections=True,shared_menu_pokedex_wall_atlas=True,approved_cottage_and_pier_tiles_preserved=True,sevii_original_connected_width_restored=17,cottages=old['cottages'],**geometry)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
