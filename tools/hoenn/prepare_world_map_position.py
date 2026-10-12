"""Track actual tile position with shared anchors at every outdoor connection."""
import argparse, hashlib, json, re
from pathlib import Path
from prepare_adaptive_gym_teams import PRIOR, LAYER as PREVIOUS
LAYER='world-map-position'; PRIOR=PRIOR+[PREVIOUS]
# Position data only: the approved palette, tiles and tilemap are untouched.
CORRECTIONS={'JourneyMossdeepOuterSea':(135,83), 'JourneyMossdeepOuterEastSea':(145,83),
 'JourneyHoennMiddleSea':(135,89),'JourneyHoennMiddleEastSea':(145,89),
 'JourneyEverGrandeBackSea':(147,94),'JourneyEverGrandeBackSouthSea':(147,98),
 'JourneyHoennSouthSea':(135,100),'JourneyHoennSouthEastSea':(145,100),
 'JourneyPacifidlogSea':(128,95),'JourneyHoennNorthSea':(135,60)}
def prepare(source):
 source=Path(source);marker=source/('.journey-'+LAYER)
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in r['prepared_sha256'].items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  return r
 expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
 for layer in PRIOR:expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 outputs={};originals={}
 def stage(p,text):
  old=(source/p).read_bytes() if (source/p).exists() else None
  h=hashlib.sha256(old).hexdigest() if old is not None else None
  assert h==expected.get(p),p
  if h is not None:originals[p]=h
  outputs[p]=text.encode()
 points={};header=(source/'src/data/journey_world_map.h').read_text()
 pattern=r'\{\(MAP_GROUP\((MAP_\w+)\)<<8\)\|MAP_NUM\(\1\), (MAPSEC_\w+), (\d+), (\d+), COMPOUND_STRING\("([^"]+)"\)\}'
 atlas={k:hashlib.sha256(re.search(k+r'\[\] = \{[^}]+\}',header)[0].encode()).hexdigest() for k in ['sWorldPalette','sWorldTiles','sWorldTilemap']}
 for m in re.finditer(pattern,header):points[m[1]]=(int(m[3]),int(m[4]))
 layouts={l['id']:l for l in json.loads((source/'data/layouts/layouts.json').read_text())['layouts']}
 maps={p.parent.name:json.loads(p.read_text()) for p in (source/'data/maps').glob('*/map.json')}
 section_points={}
 for m in re.finditer(pattern,header):section_points.setdefault(m[2],(int(m[3]),int(m[4])))
 by_id={m['id']:n for n,m in maps.items()}
 outdoor={n:m for n,m in maps.items() if m['map_type'] in ['MAP_TYPE_TOWN','MAP_TYPE_CITY','MAP_TYPE_ROUTE','MAP_TYPE_OCEAN_ROUTE'] or ('Harbor' in n and m.get('connections'))}
 coords={n:points.get(m['id'],section_points.get(m['region_map_section'])) for n,m in outdoor.items()}
 coords={n:p for n,p in coords.items() if p is not None};coords.update(CORRECTIONS)
 # Keep table order stable for Fly and the existing map lookup ABI.
 for n,xy in CORRECTIONS.items():
  ident=maps[n]['id']
  header,count=re.subn(r'(\{\(MAP_GROUP\('+ident+r'\).*?, MAPSEC_\w+, )\d+, \d+,',lambda m:m[1]+f'{xy[0]}, {xy[1]},',header);assert count==1,n
 assert atlas=={k:hashlib.sha256(re.search(k+r'\[\] = \{[^}]+\}',header)[0].encode()).hexdigest() for k in atlas}
 stage('src/data/journey_world_map.h',header)
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
 stage('src/data/journey_world_position.h',data)
 p='src/journey_world_map.c';text=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "field_player_avatar.h"\n#include "fieldmap.h"',1)
 text=text.replace('#include "data/journey_world_map.h"','#include "data/journey_world_map.h"\n#include "data/journey_world_position.h"')
 text=text.replace('u8 x, y, state, fly;','u8 x, y, state, fly, playerX, playerY;')
 text=text.replace('static void WorldDraw(void)',Path(__file__).with_name('world_map_position.c').read_text()+'\nstatic void WorldDraw(void)')
 text=text.replace('    const struct JourneyWorldPoint *player=&sWorldPoints[sJourneyWorldMap->player];','')
 text=text.replace('    sJourneyWorldMap->selected=best;','    if (sJourneyWorldMap->x == sJourneyWorldMap->playerX && sJourneyWorldMap->y == sJourneyWorldMap->playerY)\n        best = sJourneyWorldMap->player;\n    sJourneyWorldMap->selected=best;')
 text=text.replace('player->x-1,player->y-1','sJourneyWorldMap->playerX-1,sJourneyWorldMap->playerY-1')
 text=text.replace('x=sWorldPoints[sJourneyWorldMap->player].x;y=sWorldPoints[sJourneyWorldMap->player].y;','x=sJourneyWorldMap->playerX;y=sJourneyWorldMap->playerY;')
 text=text.replace('    SetVBlankCallback(NULL);\n    sJourneyWorldMap=','    u16 position = JourneyWorldMapPosition();\n    SetVBlankCallback(NULL);\n    sJourneyWorldMap=',1)
 text=text.replace('sJourneyWorldMap->x=sWorldPoints[sJourneyWorldMap->player].x;sJourneyWorldMap->y=sWorldPoints[sJourneyWorldMap->player].y;','sJourneyWorldMap->x=sJourneyWorldMap->playerX=position & 255;sJourneyWorldMap->y=sJourneyWorldMap->playerY=position >> 8;')
 stage(p,text)
 p='include/journey_world_map.h';stage(p,(source/p).read_text().replace('u16 JourneyWorldMapPlayerPoint(void);','u16 JourneyWorldMapPlayerPoint(void);\nu16 JourneyWorldMapPosition(void);'))
 r=dict(layer=LAYER,projections=projections,seams=seams,anchors=anchors,corrected_route_centers=CORRECTIONS,shared_boundary_positions=True,boundary_nodes=len(roots),maximum_neighbor_pixel_step=max_step,atlas_pixels_unchanged=True,atlas_arrays_sha256=atlas,original_sha256=originals,prepared_sha256={p:hashlib.sha256(v).hexdigest() for p,v in outputs.items()})
 for p,raw in outputs.items():(source/p).write_bytes(raw)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.source),indent=2))
