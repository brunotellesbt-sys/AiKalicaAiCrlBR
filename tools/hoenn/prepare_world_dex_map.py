"""Align the western chart to real connections and show all regions in Dex AREA."""
import argparse,hashlib,json,re,struct
from pathlib import Path
from PIL import Image,ImageDraw
from world_projection import project
from prepare_world_map_position import PRIOR,LAYER as PREVIOUS
LAYER='world-dex-map';PRIOR=PRIOR+[PREVIOUS];ROOT=Path(__file__).resolve().parents[2]
COLORS=[(16,24,32),(112,184,232),(48,104,176),(24,112,0),(48,152,0),(80,200,0),(120,224,0),(184,240,64),(216,248,112),(184,120,8),(224,168,16),(248,208,56),(248,232,136),(248,72,24),(248,248,240),(96,80,72)]
def decode(header):
 def values(k):return [int(v) for v in re.search(k+r'\[\] = \{([^}]+)\}',header)[1].split(',')]
 tiles=values('sWorldTiles');tm=values('sWorldTilemap');im=Image.new('P',(224,112));im.putpalette([v for c in COLORS for v in c]+[0]*720)
 for ty in range(14):
  for tx in range(28):
   at=tm[(ty+3)*32+tx+1]*32
   for y in range(8):
    for x in range(0,8,2):
     b=tiles[at+y*4+x//2];im.putpixel((tx*8+x,ty*8+y),b&15);im.putpixel((tx*8+x+1,ty*8+y),b>>4)
 return im
def encode(header,im):
 tiles=[bytes(32)];lookup={tiles[0]:0};tm=[0]*1024
 for ty in range(14):
  for tx in range(28):
   tile=bytes(im.getpixel((tx*8+x,ty*8+y))|(im.getpixel((tx*8+x+1,ty*8+y))<<4) for y in range(8) for x in range(0,8,2))
   if tile not in lookup:lookup[tile]=len(tiles);tiles.append(tile)
   tm[(ty+3)*32+tx+1]=lookup[tile]
 for key,vals in [('sWorldTiles',b''.join(tiles)),('sWorldTilemap',tm)]:
  header,n=re.subn(r'('+key+r'\[\] = \{)[^}]+(\})',lambda m:m[1]+','.join(map(str,vals))+m[2],header);assert n==1
 return header
PAT=r'\{\(MAP_GROUP\((MAP_\w+)\)<<8\)\|MAP_NUM\(\1\), (MAPSEC_\w+), (\d+), (\d+), COMPOUND_STRING\("([^"]+)"\)\}'
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
  old=(source/p).read_bytes() if (source/p).exists() else None;h=hashlib.sha256(old).hexdigest() if old else None
  assert h==expected.get(p),p
  if h:originals[p]=h
  outputs[p]=text.encode()
 maps={p.parent.name:json.loads(p.read_text()) for p in (source/'data/maps').glob('*/map.json')};byid={m['id']:n for n,m in maps.items()}
 layouts={l['id']:l for l in json.loads((source/'data/layouts/layouts.json').read_text())['layouts']}
 header=(source/'src/data/journey_world_map.h').read_text();points={byid[m[1]]:dict(id=m[1],section=m[2],x=int(m[3]),y=int(m[4])) for m in re.finditer(PAT,header)}
 # The physical canal is west of Route105. Its old point was east of it.
 route=points['Route105'];western=points['JourneyRustboroCoast'];r115=points['Route115']
 corrected={'JourneyDewfordCoast':(western['x'],route['y']), 'JourneyDewfordGate':((western['x']+route['x'])//2,route['y']), 'JourneyRustboroGate':((western['x']+r115['x'])//2,r115['y'])}
 corrected.update(JourneySanctuaryAbismo=(western['x']+3,route['y']+3))
 before=decode(header);im=before.copy();native=Image.open(ROOT/'web/atlas/hoenn.png').convert('RGB')
 for y in range(native.height):
  for x in range(native.width):
   r,g,b=native.getpixel((x,y))
   if b>r+20 and b>g-30:native.putpixel((x,y),COLORS[1])
 native=native.resize((124,46),Image.Resampling.NEAREST);pal=Image.new('P',(1,1));pal.putpalette([v for c in COLORS for v in c]+[0]*720);native=native.quantize(palette=pal,dither=Image.Dither.NONE)
 box=[11,70,60,111]
 for y in range(box[1],box[3]+1):
  for x in range(box[0],box[2]+1):
   pixel=native.getpixel((x-17,y-66)) if 17<=x<141 and 66<=y<112 else 1
   if pixel==1:im.putpixel((x,y),1)
 # Restore native route water footprints on their original chart coordinates.
 sections=json.loads((source/'src/data/region_map/region_map_sections.json').read_text())['map_sections'];bysec={s['id']:s for s in sections}
 draw=ImageDraw.Draw(im)
 for sec in sections:
  if sec['id'] not in ['MAPSEC_ROUTE_'+str(i) for i in range(105,110)]:continue
  a=round(17+sec['x']*8*124/224);b=round(66+sec['y']*8*46/136);c=round(17+(sec['x']+sec['width'])*8*124/224);d=round(66+(sec['y']+sec['height'])*8*46/136)
  for y in range(max(box[1],b),min(box[3]+1,d)):
   for x in range(max(box[0],a),min(box[2]+1,c)):
    if im.getpixel((x,y))==1:im.putpixel((x,y),2)
 # Remove the old shrine marker where its misplaced coast point put it.
 old=points['JourneySanctuaryAbismo']
 for y in range(old['y']-1,old['y']+2):
  for x in range(old['x']-1,old['x']+2):
   if 17<=x<141 and 66<=y<112:im.putpixel((x,y),native.getpixel((x-17,y-66)))
 for name,xy in corrected.items():
  p=points[name];header,n=re.subn(r'(\{\(MAP_GROUP\('+p['id']+r'\).*?, MAPSEC_\w+, )\d+, \d+,',lambda m:m[1]+f'{xy[0]}, {xy[1]},',header);assert n==1;points[name].update(x=xy[0],y=xy[1])
 # Draw only real connections. All three coastal maps form the same north/south strip.
 strips=[[(western['x'],70),(western['x'],route['y'])],[(western['x'],route['y']),(route['x'],route['y'])],[(western['x'],r115['y']),(r115['x'],r115['y'])],[(western['x'],route['y']+3),corrected['JourneySanctuaryAbismo']]]
 dim=points['JourneySanctuaryDimensoes'];strips.append([(western['x'],dim['y']),(dim['x'],dim['y'])])
 for strip in strips:
  overlay=im.copy();ImageDraw.Draw(overlay).line(strip,fill=2,width=2)
  for y in range(box[1],box[3]+1):
   for x in range(box[0],box[2]+1):
    if im.getpixel((x,y)) in [1,2]:im.putpixel((x,y),overlay.getpixel((x,y)))
 for name in ['JourneySanctuaryAbismo','JourneySanctuaryDimensoes']:
  p=points[name];draw.rectangle((p['x']-1,p['y']-1,p['x']+1,p['y']+1),fill=14);draw.point((p['x'],p['y']),fill=1)
 changed=[(x,y) for y in range(112) for x in range(224) if im.getpixel((x,y))!=before.getpixel((x,y))]
 assert all(box[0]<=x<=box[2] and box[1]<=y<=box[3] for x,y in changed)
 header=encode(header,im);stage('src/data/journey_world_map.h',header)
 section_points={}
 for m in re.finditer(PAT,header):section_points.setdefault(m[2],(int(m[3]),int(m[4])))
 coords={n:(p['x'],p['y']) for n,p in points.items()}
 outdoors={n:m for n,m in maps.items() if m['map_type'] in ['MAP_TYPE_TOWN','MAP_TYPE_CITY','MAP_TYPE_ROUTE','MAP_TYPE_OCEAN_ROUTE'] or ('Harbor' in n and m.get('connections'))}
 geometry=project(maps,layouts,{n:coords.get(n,section_points.get(m['region_map_section'])) for n,m in outdoors.items() if n in coords or m['region_map_section'] in section_points})
 stage('src/data/journey_world_position.h',geometry.pop('data'))
 # Resolve interior habitats to their actual surface/section, not the current region.
 panels=json.loads((source/'.journey-coastal-world-map').read_text())['panels'];known={p['id']:p['panel'] for p in json.loads((ROOT/'web/world-layout.json').read_text())['points'] if p['panel'] in panels};secindex={d['id']:i for i,d in enumerate(sections)}
 regions=(source/'src/regions.c').read_text()
 for key,panel in [('SEVII123','sevii_123'),('SEVII45','sevii_45'),('SEVII67','sevii_67')]:
  block=re.search(r'\[KANTO_SUBREGION_'+key+r'\]\s*=\s*\{(.*?)\}',regions,re.S)[1]
  for sec in re.findall(r'MAPSEC_\w+',block):
   if sec!='MAPSEC_NONE':known[sec]=panel
 def location(name):
  if name in coords:return coords[name]
  m=maps[name];sec=m['region_map_section']
  for c in m.get('connections') or []:
   if c['direction']=='emerge' and c['map'] in byid:return location(byid[c['map']])
  if sec in section_points:return section_points[sec]
  d=bysec[sec];panel=known.get(sec,'hoenn' if secindex[sec]<secindex['MAPSEC_PALLET_TOWN'] else 'kanto');x,y,w,h=panels[panel];sw,sh=Image.open(ROOT/'web/atlas'/(panel+'.png')).size
  return max(4,min(219,round(x+(d['x']+d['width']/2)*8*w/sw))),max(4,min(107,round(y+(d['y']+d['height']/2)*8*h/sh)))
 habitats=(source/'include/journey_habitat_data.h').read_text();locations={};records={}
 for ident,members in re.findall(r'\{(MAP_\w+), \d+, \{([^}]+)\}\}',habitats):
  xy=location(byid[ident])
  for species in members.split(', '):
   locations.setdefault(species,set()).add(xy);records.setdefault((species,xy),(ident,False))
 for c in json.loads((source/'.journey-sanctuaries').read_text())['captures']:
  xy=location(c['map']);locations.setdefault(c['species'],set()).add(xy);records.setdefault((c['species'],xy),(maps[c['map']]['id'],True))
 body='struct JourneyWorldDexLocation { u16 species, map; u8 x, y, fixed; };\nstatic const struct JourneyWorldDexLocation sWorldDexLocations[] = {\n'+''.join('{'+species+','+records[(species,(x,y))][0]+','+str(x)+','+str(y)+','+str(int(records[(species,(x,y))][1]))+'},\n' for species,places in sorted(locations.items()) for x,y in sorted(places))+'};\n'
 stage('src/data/journey_world_dex_locations.h',body);stage('src/journey_world_dex.c',(ROOT/'tools/hoenn/world_dex.c').read_text())
 stage('include/journey_world_dex.h','#ifndef GUARD_JOURNEY_WORLD_DEX_H\n#define GUARD_JOURNEY_WORLD_DEX_H\nvoid JourneyWorldDexOpen(u16,u8 *);\nu32 JourneyWorldDexLocationCount(u16);\n#endif\n')
 p='src/pokedex_area_screen.c';text=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_world_dex.h"',1);needle='    u8 taskId;\n\n    sPokedexAreaScreen = AllocZeroed';assert text.count(needle)==1
 text=text.replace(needle,'    JourneyWorldDexOpen(species, screenSwitchState);\n    return;\n    u8 taskId;\n\n    sPokedexAreaScreen = AllocZeroed',1);stage(p,text)
 r=dict(layer=LAYER,corrected_points=corrected,changed_pixels=len(changed),changed_rect=box,locations={k:[list(p) for p in sorted(v)] for k,v in locations.items()},species_with_locations=len(locations),**geometry,original_sha256=originals,prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()})
 for p,raw in outputs.items():(source/p).write_bytes(raw)
 marker.write_text(json.dumps(r,indent=2)+'\n')
 gallery=ROOT/'mods/hoenn/world-map-gallery';im.convert('RGB').resize((896,448),Image.Resampling.NEAREST).save(gallery/'world-map-art.png')
 return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.source),indent=2))
