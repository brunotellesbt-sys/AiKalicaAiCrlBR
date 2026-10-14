"""Chart real traversable seas as continuous areas and remove GPS spikes."""
import argparse,hashlib,json,re
from pathlib import Path
from PIL import Image,ImageDraw
from candidate_layer import Layer
from prepare_complete_marine_atlas import PRIOR,LAYER as PREVIOUS,point_line,SURF_ROUTES
from prepare_world_dex_map import decode,encode,PAT,COLORS
from world_navigation_grid import build
ROOT=Path(__file__).resolve().parents[2]
LAYER='navigated-sea-atlas';PRIOR=PRIOR+[PREVIOUS]

def prepare(source):
 layer=Layer(source,LAYER,PRIOR)
 if old:=layer.existing():return old
 s=layer.source;old=json.loads((s/'.journey-complete-marine-atlas').read_text());ref=json.loads((ROOT/'tools/hoenn/data/route-navigation-reference.json').read_text())
 maps={p.parent.name:json.loads(p.read_text()) for p in (s/'data/maps').glob('*/map.json')};byid={m['id']:n for n,m in maps.items()};ls={l['id']:l for l in json.loads((s/'data/layouts/layouts.json').read_text())['layouts']}
 for n,h in ref['terrain_sha256'].items():assert hashlib.sha256((s/ls[maps[n]['layout']]['blockdata_filepath']).read_bytes()).hexdigest()==h,n
 header=(s/'src/data/journey_world_map.h').read_text();im=decode(header)
 ids,values,gridproof=build(old);assert gridproof['maximum_neighbor_pixel_step']<=2 and gridproof['maximum_seam_delta']==0
 def at(n,x,y):return tuple(map(int,values[ids[n][y,x]]))
 # The atlas uses one connected sea fill, not a road on every internal map seam.
 for y in range(112):
  for x in range(224):
   if im.getpixel((x,y))==2:im.putpixel((x,y),1)
 # Restore genuine blue town emblems from the regional source artwork.
 panels=json.loads((s/'.journey-coastal-world-map').read_text())['panels'];pal=Image.new('P',(1,1));pal.putpalette([v for c in COLORS for v in c]+[0]*720)
 waters={(164,180,255),(156,213,255),(74,156,230),(41,131,230),(82,148,213),(90,172,230)}
 detail=im.resize((448,224),Image.Resampling.NEAREST)
 for name,(x,y,w,h) in panels.items():
  native=Image.open(ROOT/'web/atlas'/(name+'.png')).convert('RGB')
  for yy in range(native.height):
   for xx in range(native.width):
    if native.getpixel((xx,yy)) in waters:native.putpixel((xx,yy),COLORS[1])
  if name!='hoenn':
   todo=[(native.width-1,yy) for yy in range(native.height-24,native.height) if native.getpixel((native.width-1,yy))!=COLORS[1]];seen=set()
   while todo:
    xx,yy=todo.pop()
    if (xx,yy) in seen or not(native.width-16<=xx<native.width and native.height-24<=yy<native.height) or native.getpixel((xx,yy))==COLORS[1]:continue
    seen.add((xx,yy));native.putpixel((xx,yy),COLORS[1]);todo.extend([(xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)])
  for scale,dest in [(1,im),(2,detail)]:
   art=native.resize((scale*w,scale*h),Image.Resampling.NEAREST).quantize(palette=pal,dither=Image.Dither.NONE)
   for yy in range(scale*h):
    for xx in range(scale*w):
     gx,gy=scale*x+xx,scale*y+yy
     if gx<dest.width and gy<dest.height and art.getpixel((xx,yy))!=1:dest.putpixel((gx,gy),art.getpixel((xx,yy)))
 shore=[]
 areas=[];active=[]
 for n,m in sorted(maps.items()):
  if n not in ids or n not in ref['compiled_water_masks']:continue
  generated=n.startswith('Journey') and m['map_type'] in ['MAP_TYPE_ROUTE','MAP_TYPE_OCEAN_ROUTE'] and m.get('connections')
  if not generated and n not in SURF_ROUTES:continue
  samples=[at(n,i%ids[n].shape[1],i//ids[n].shape[1]) for i,v in enumerate(ref['compiled_water_masks'][n]) if v=='1']
  if not samples:continue
  left=min(p[0] for p in samples);right=max(p[0] for p in samples);top=min(p[1] for p in samples);bottom=max(p[1] for p in samples)
  box=[left,top,right,bottom];areas.append(dict(map=n,rectangle=box,actual_compiled_water=True))
  if generated:active.append(n)
  for yy in range(top,bottom+1):
   for xx in range(left,right+1):
    if im.getpixel((xx,yy))==1:im.putpixel((xx,yy),2)
  for yy in range(2*top,2*bottom+2):
   for xx in range(2*left,2*right+2):
    if detail.getpixel((xx,yy))==1:detail.putpixel((xx,yy),2)
 # The disconnected prototype is not an available route and has no map icon.
 header=re.sub(r'^.*MAP_GROUP\(MAP_JOURNEYHOENNCROSSING\).*\n','',header,flags=re.M)
 existing={byid[m[1]] for m in re.finditer(PAT,header)};caves=[];added=[]
 def exits(n):
  todo=[n];seen={n};result=[]
  for current in todo:
   for warp in maps[current].get('warp_events') or []:
    other=byid.get(warp['dest_map'])
    if not other:continue
    if other in ids and maps[other]['map_type'] in ['MAP_TYPE_CITY','MAP_TYPE_TOWN','MAP_TYPE_ROUTE','MAP_TYPE_OCEAN_ROUTE']:
     try:w=maps[other]['warp_events'][int(warp['dest_warp_id'])]
     except (ValueError,IndexError):continue
     if 0<=w['x']<ids[other].shape[1] and 0<=w['y']<ids[other].shape[0]:result.append((other,w['x'],w['y']))
    elif other not in seen and maps[other]['region_map_section']==maps[n]['region_map_section']:seen.add(other);todo.append(other)
  return sorted(set(result))
 sections={}
 for n,m in sorted(maps.items()):
  if m['map_type']!='MAP_TYPE_UNDERGROUND' or n in existing:continue
  entries=exits(n)
  if not entries:continue
  xy=tuple(round(sum(at(a,x,y)[axis] for a,x,y in entries)/len(entries)) for axis in [0,1]);label=m['region_map_section'].removeprefix('MAPSEC_').replace('_',' ')
  added.append(point_line(m,xy,label));sections.setdefault(m['region_map_section'],dict(map=n,position=list(xy),entries=[list(e) for e in entries]));caves.append(dict(map=n,position=list(xy),entries=[list(e) for e in entries]))
 end=header.index('};',header.index('sWorldPoints'));header=header[:end]+''.join(added)+header[end:]
 allcaves=old['cave_entrances']+list(sections.values())
 for c in allcaves:
  x,y=c['position']
  for dx,dy,color in [(0,-1,15),(-1,0,15),(0,0,0),(1,0,15)]:im.putpixel((x+dx,y+dy),color)
  d=ImageDraw.Draw(detail);d.rectangle((2*x-2,2*y-2,2*x+3,2*y+1),fill=15);d.rectangle((2*x,2*y-1,2*x+1,2*y+1),fill=0)
 header=encode(header,im);packed=bytes(detail.getpixel((x,y))|(detail.getpixel((x+1,y))<<4) for y in range(224) for x in range(0,448,2))
 header=re.sub(r'(sWorldDetailPixels\[\] = \{)[^}]+(\})',lambda m:m[1]+','.join(map(str,packed))+m[2],header)
 layer.stage('src/data/journey_world_map.h',header)
 pos=(s/'src/data/journey_world_position.h').read_text().replace('sWorldAnchors[] =','sWorldAnchors[] __attribute__((used)) =');pos+='\nstruct JourneyWorldTileGrid { u32 first; u16 map, width, height; };\nstatic const u16 sWorldNavigationPixels[] = {'+','.join(str(int(x)|(int(y)<<8)) for x,y in values)+'};\nstatic const struct JourneyWorldTileGrid sWorldTileGrids[] = {\n'
 pos+=''.join('{'+str(int(ids[p['map']][0,0]))+', (MAP_GROUP('+p['id']+')<<8)|MAP_NUM('+p['id']+'), '+str(p['width'])+', '+str(p['height'])+'},\n' for p in old['projections'])+'};\n';layer.stage('src/data/journey_world_position.h',pos)
 code=(s/'src/journey_world_map.c').read_text();start=code.index('u16 JourneyWorldMapPosition(void)');end=code.index('\nstatic void WorldDraw',start)
 code=code[:start]+'''u16 JourneyWorldMapPosition(void)
{
    u16 map = (gSaveBlock1Ptr->location.mapGroup << 8) | gSaveBlock1Ptr->location.mapNum;
    u16 i, point;
    s16 x, y;
    PlayerGetDestCoords(&x, &y);
    x -= MAP_OFFSET; y -= MAP_OFFSET;
    for (i = 0; i < ARRAY_COUNT(sWorldTileGrids); i++)
    {
        const struct JourneyWorldTileGrid *grid = &sWorldTileGrids[i];
        if (grid->map != map) continue;
        if (x < 0) x = 0;
        if (y < 0) y = 0;
        if (x >= grid->width) x = grid->width - 1;
        if (y >= grid->height) y = grid->height - 1;
        return sWorldNavigationPixels[grid->first + y * grid->width + x];
    }
    point = JourneyWorldMapPlayerPoint();
    return sWorldPoints[point].x | (sWorldPoints[point].y << 8);
}
''' +code[end:];layer.stage('src/journey_world_map.c',code)
 dex=(s/'src/data/journey_world_dex_locations.h').read_text()
 for c in caves:
  ident=maps[c['map']]['id'];x,y=c['position'];dex=re.sub(r'(\{SPECIES_\w+,'+ident+r',)\d+,\d+,',lambda m:m[1]+f'{x},{y},',dex)
 layer.stage('src/data/journey_world_dex_locations.h',dex)
 return layer.finish(**gridproof,anchors=old['anchors'],projections=old['projections'],seams=old['seams'],boundary_nodes=old['boundary_nodes'],orthogonal_marine_paths=old['orthogonal_marine_paths'],marine_areas=areas,active_generated_seas=active,obsolete_unconnected_route_removed='JourneyHoennCrossing',native_cave_points=caves,shore_pixels_corrected_from_controller_water=sorted(set(map(tuple,shore))),all_internal_grid_lines_removed=True,reference_rom_sha256=ref['reference_rom_sha256'],controller_reference_steps=sum(t['walked_tiles'] for t in ref['trips']),no_terrain_or_ports_changed=True,detail_size=[448,224])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
