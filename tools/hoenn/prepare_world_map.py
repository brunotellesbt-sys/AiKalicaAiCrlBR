"""Native world-map screen with current routes, ports and real player placement."""
import argparse, hashlib, json, re, struct
from pathlib import Path
from PIL import Image,ImageDraw
from prepare_lavender_network import CHAIN as BASE, LAYER as LAST
ROOT=Path(__file__).resolve().parents[2]
LAYER='world-map'; CHAIN=BASE+[LAST]
PANELS={'kanto':(2,0,96,62),'hoenn':(0,66,130,46),'sevii_123':(132,17,88,39),'sevii_45':(162,59,60,26),'sevii_67':(162,88,60,24)}
NAMES={'JourneyRoute12Shipyard':'LAVENDER PORT','JourneyRoute12OuterSea':'LAVENDER OUTER SEA','JourneyCinnabarSouthSea':'CINNABAR SOUTH SEA','JourneyWestRiver':'WESTERN RIVER','JourneyRustboroCoast':'RUSTBORO COAST','JourneyDewfordCoast':'DEWFORD COAST','JourneyRustboroGate':'RUSTBORO CHANNEL','JourneyDewfordGate':'DEWFORD CHANNEL','JourneyFuchsiaSea':'FUCHSIA SEA','JourneyHoennCrossing':'KANTO-HOENN CROSSING'}

def prepare(source, layer=LAYER, chain=CHAIN, refresh=False):
 panels=dict(PANELS)
 if refresh:panels.update(hoenn=(6,66,124,46),sevii_123=(118,17,88,39),sevii_45=(137,59,60,26),sevii_67=(137,88,60,24))
 source=Path(source);marker=source/('.journey-'+layer)
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in (r['prepared_sha256']|r['preserved_native_sha256']).items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  return r
 expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
 for prior in chain:expected.update(json.loads((source/('.journey-'+prior)).read_text())['prepared_sha256'])
 preserved={};originals={};outputs={};assets={}
 def read(p):
  raw=(source/p).read_bytes();h=hashlib.sha256(raw).hexdigest();assert h==expected[p],p;preserved[p]=h;return raw
 def stage(p,v):
  if p in expected:originals[p]=hashlib.sha256(read(p)).hexdigest();preserved.pop(p,None)
  else:assert not (source/p).exists(),p
  outputs[p]=v if isinstance(v,bytes) else v.encode()
 def asset(p):
  raw=(ROOT/p).read_bytes();assets[p]=hashlib.sha256(raw).hexdigest();return raw
 sections=json.loads(read('src/data/region_map/region_map_sections.json'))['map_sections'];bysec={x['id']:x for x in sections};secids={x['id']:i for i,x in enumerate(sections)}
 atlas=json.loads(asset('web/world-layout.json'));known={p['id']:p['panel'] for p in atlas['points'] if p['panel'] in panels}
 regions=read('src/regions.c').decode()
 for key,panel_name in [('SEVII123','sevii_123'),('SEVII45','sevii_45'),('SEVII67','sevii_67')]:
  block=re.search(r'\[KANTO_SUBREGION_'+key+r'\]\s*=\s*\{(.*?)\}',regions,re.S)[1]
  for sec in re.findall(r'MAPSEC_\w+',block):
   if sec!='MAPSEC_NONE':known[sec]=panel_name
 def panel(sec):
  if sec in known:return known[sec]
  if secids[sec]<secids['MAPSEC_PALLET_TOWN']:return 'hoenn'
  if secids['MAPSEC_ONE_ISLAND']<=secids[sec]<secids['MAPSEC_SEVII_ISLE_22']:return 'sevii_123'
  return 'kanto'
 def coord(sec):
  d=bysec[sec];p=panel(sec);x,y,w,h=panels[p];sw,sh=Image.open(ROOT/'web/atlas'/(p+'.png')).size if refresh else ((176,120) if p=='kanto' else (224,136))
  return (max(4,min(219,round(x+(d['x']+d['width']/2)*8*w/sw))),max(4,min(107,round(y+(d['y']+d['height']/2)*8*h/sh))))
 image=Image.new('RGB',(224,112),(112,184,232))
 for p,(x,y,w,h) in panels.items():
  asset('web/atlas/'+p+'.png');im=Image.open(ROOT/'web/atlas'/ (p+'.png')).convert('RGB')
  # Water is a single world color. Native dark strips are reconstructed as
  # navigable route rectangles below; regional water palettes do not survive.
  for yy in range(im.height):
   for xx in range(im.width):
    r,g,b=im.getpixel((xx,yy))
    if b>r+20 and b>g-30:im.putpixel((xx,yy),(112,184,232))
  if refresh and p!='hoenn':
   # Remove only the old region-switch UI component. Its clipped yellow frame
   # touches the right edge; neighboring native islands are left intact.
   sea=(112,184,232);todo=[(im.width-1,yy) for yy in range(im.height-24,im.height) if im.getpixel((im.width-1,yy))!=sea];seen=set()
   while todo:
    xx,yy=todo.pop()
    if (xx,yy) in seen or not(im.width-16<=xx<im.width and im.height-24<=yy<im.height) or im.getpixel((xx,yy))==sea:continue
    seen.add((xx,yy));im.putpixel((xx,yy),sea);todo.extend([(xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)])
  elif p=='kanto':ImageDraw.Draw(im).rectangle((im.width-10,im.height-10,im.width,im.height),fill=(112,184,232))
  image.paste(im.resize((w,h),Image.Resampling.NEAREST),(x,y))
 if refresh:
  terrain=ImageDraw.Draw(image)
  terrain.polygon([(27,66),(29,64),(34,65),(38,63),(43,64),(48,62),(53,63),(58,63),(63,64),(68,63),(74,65),(80,64),(84,66)],fill=(24,112,0))
  terrain.polygon([(30,66),(35,65),(39,64),(45,65),(49,63),(55,64),(62,65),(68,64),(74,66)],fill=(48,152,0))
 base_image=image.copy()
 draw=ImageDraw.Draw(image)
 # Retain the original sea-route positions using the sections' native bounds.
 for sec in sections:
  if re.fullmatch(r'MAPSEC_ROUTE_(19|20|21|10[5-9]|12[4-9]|13[0-4])',sec['id']):
   p=panel(sec['id']);x,y,w,h=panels[p];sw,sh=Image.open(ROOT/'web/atlas'/(p+'.png')).size if refresh else ((176,120) if p=='kanto' else (224,136))
   a=round(x+sec['x']*8*w/sw);b=round(y+sec['y']*8*h/sh)
   c=round(x+(sec['x']+sec['width'])*8*w/sw);d=round(y+(sec['y']+sec['height'])*8*h/sh)
   if a<c and b<d:draw.rectangle((a,b,c-1,d-1),fill=(48,104,176))
 maps={};groups=json.loads(read('data/maps/map_groups.json'))
 for group in groups['group_order']:
  for name in groups[group]:
   p='data/maps/'+name+'/map.json';d=json.loads(read(p))
   if d.get('map_type') in ['MAP_TYPE_TOWN','MAP_TYPE_CITY','MAP_TYPE_ROUTE','MAP_TYPE_OCEAN_ROUTE'] or name.startswith('JourneySanctuary') or (refresh and 'Harbor' in name and d.get('connections')):maps[name]=d
 points=[];loc={};native_cities=set()
 # One point per native outdoor section; new marine maps get separate points below.
 for name,d in maps.items():
  if name.startswith('Journey'):continue
  sec=d['region_map_section']
  if sec not in bysec:continue
  x,y=coord(sec)
  if refresh:loc[name]=(x,y)
  if sec in native_cities:continue
  native_cities.add(sec)
  points.append(dict(map=name,id=d['id'],section=sec,x=x,y=y,name=bysec[sec]['name'][:36]));loc[name]=(x,y)
 # Current eastern grid, in map-order: 1/2/3 above 4/5 above 6/7.
 east=json.loads((source/'.journey-eastern-sea-union').read_text())['rectangles']
 for r in east:
  if r['map'].startswith('Journey'):
   loc[r['map']]=(max(105,min(216,round(111+(r['x']+r['width']/2-190)*.36))),max(45,min(106,round(47+(r['y']+r['height']/2)*.23))))
 loc.update(JourneyRoute12Shipyard=(103,43),JourneyRoute12OuterSea=(105,35),JourneyFuchsiaSea=(88,52),JourneyHoennCrossing=(68,67),JourneyCinnabarSouthSea=(18,65),JourneyWestRiver=(12,75),JourneyRustboroCoast=(7,83),JourneyDewfordCoast=(21,100),JourneyRustboroGate=(12,86),JourneyDewfordGate=(29,103))
 if (source/'.journey-kanto-open-sea').exists():
  loc.update(JourneyFuchsiaSea=(63,60),JourneyKantoSouthWestSea=(66,60),JourneyKantoSouthSea=(76,60),JourneyRoute13Coast=(84,53),JourneyKantoCoastalBand=(77,60),JourneyLavenderApproach=(98,49),JourneyKantoEasternChannel=(90,61),JourneyOneIslandChannel=(84,59),JourneyFuchsiaInlet=(64,56),JourneyLavenderApproachSouth=(105,57),JourneyRoute12Shipyard=(85,40),JourneyRoute12OuterSea=(85,37))
  if refresh:loc.update(JourneyWestRiver=(2,75),JourneyRustboroCoast=(2,83),JourneyDewfordCoast=(18,100))
  # Depict the Fuchsia crossing as a narrow sea route, like Route 20.
  draw.line([(57,60),(105,60)],fill=(48,104,176),width=2)

  NAMES.update(JourneyKantoSouthWestSea='FUCHSIA COAST',JourneyKantoSouthSea='KANTO SOUTH SEA',JourneyRoute13Coast='ROUTE 13 COAST',JourneyKantoCoastalBand='KANTO COASTAL CHANNEL',JourneyLavenderApproach='LAVENDER APPROACH')
 # Shrines belong to their actual parent sea, rather than to a reused native section.
 sites=json.loads((source/'.journey-sanctuaries').read_text())['sites']
 shrine_names=['STORM','AURORA','VOLCANO','TITANS','FOREST','ECLIPSE','DRAGONS','STARS','CRYSTALS','TIDES','ORIGINS','DEPTHS','DIMENSIONS','ABYSS']
 for i,site in enumerate(sites):
  NAMES[site['map']]=shrine_names[i]+' SHRINE'
  base=loc.get(site['surface'],coord(maps[site['surface']]['region_map_section']));loc[site['map']]=(min(218,base[0]+3),min(106,base[1]+3))
 for name,d in maps.items():
  if not name.startswith('Journey'):continue
  sec=d['region_map_section'];xy=loc.get(name,coord(sec));loc[name]=xy
  label=NAMES.get(name)
  if label is None:
   label=re.sub(r'([a-z])([A-Z])',r'\1 \2',name.removeprefix('Journey')).upper()
   label=label.replace('WORLD SEA','SEVII SEA').replace('WORLD LANE','SEVII CHANNEL').replace('WORLD FILL','SEVII REEF').replace('SANCTUARY','SHRINE')
  points.append(dict(map=name,id=d['id'],section=sec,x=xy[0],y=xy[1],name=label[:36]))
 # Render only connections present in the actual current map headers. Shared
 # shores inside a region remain native artwork; added sea routes use blue paths.
 connections=[]
 for a,d in maps.items():
  if a not in loc:continue
  for c in d.get('connections',[]) or []:
   b=next((n for n,md in maps.items() if md['id']==c['map']),None)
   if b not in loc or a>=b or not(a.startswith('Journey') or b.startswith('Journey')):continue
   p,q=loc[a],loc[b];connections.append(dict(source=a,destination=b,direction=c['direction'],start=list(p),end=list(q)))
   if not any('WorldFill' in n for n in [a,b]):
    bridge=(source/'.journey-kanto-open-sea').exists() and {a,b} in [{'Route12_Frlg','JourneyRoute12OuterSea'},{'JourneyRoute12OuterSea','JourneyRoute12Shipyard'}]
    western=any(n in {'JourneyCinnabarSouthSea','JourneyWestRiver','JourneyRustboroCoast','JourneyDewfordCoast','JourneyRustboroGate','JourneyDewfordGate'} for n in [a,b])
    if not bridge and (not refresh or western):draw.line([p,(q[0],p[1]),q],fill=(48,104,176),width=2)
 if refresh:
  # Regional route strips follow the approved sketch. The surrounding ocean
  # stays light blue; only these corridors are marked, never a filled sea.
  corridors=[
   [(85,40),(156,40)],[(57,60),(188,60)],
   [(90,40),(90,77)],[(124,39),(124,80)],
   [(156,40),(156,100)],[(188,50),(188,100)],
   [(117,60),(117,83)],[(117,80),(188,80)],
   [(108,100),(188,100)],[(128,94),(128,100)],
   [(188,50),(192,50)],[(147,67),(156,67)],
   [(182,79),(188,79)],[(185,97),(188,97)],
   [(152,102),(156,102)],[(156,100),(156,102)]
  ]
  for strip in corridors:draw.line(strip,fill=(48,104,176),width=2)
  # Match the four-pixel native Route 20 band through the first crossing.
  draw.rectangle((57,58,91,61),fill=(48,104,176))
 if (source/'.journey-kanto-open-sea').exists():
  draw.line([(83,39),(85,39),(85,40)],fill=(248,208,56),width=1)
 # Route markings may recolor sea, never cover land or native city markers.
 for yy in range(image.height):
  for xx in range(image.width):
   if base_image.getpixel((xx,yy))!=(112,184,232):image.putpixel((xx,yy),base_image.getpixel((xx,yy)))
 for p in points:
  if p['map'].startswith('JourneySanctuary'):
   if refresh:
    navy=(48,104,176);x,y=p['x'],p['y']
    candidates=[(xx,yy) for yy in range(image.height) for xx in range(image.width) if image.getpixel((xx,yy))==navy]
    xx,yy=min(candidates,key=lambda q:abs(q[0]-x)+abs(q[1]-y))
    spur=image.copy();ImageDraw.Draw(spur).line([(x,y),(xx,y),(xx,yy)],fill=navy,width=2)
    for sy in range(max(0,min(y,yy)-1),min(image.height,max(y,yy)+2)):
     for sx in range(max(0,min(x,xx)-1),min(image.width,max(x,xx)+2)):
      if base_image.getpixel((sx,sy))==(112,184,232):image.putpixel((sx,sy),spur.getpixel((sx,sy)))
    draw.rectangle((x-1,y-1,x+1,y+1),fill=(248,248,240))
    draw.point((x,y),fill=(112,184,232))
   else:draw.rectangle((p['x']-1,p['y']-1,p['x']+1,p['y']+1),fill=(96,80,72))
  elif p['map']=='JourneyRoute12Shipyard' or (refresh and p['map'] in {'OneIsland_Frlg','TwoIsland_Frlg','ThreeIsland_Frlg','FourIsland_Frlg','FiveIsland_Frlg','SixIsland_Frlg','SevenIsland_Frlg'}):
   draw.rectangle((p['x']-1,p['y']-1,p['x']+1,p['y']+1),fill=(248,248,240) if refresh else (248,72,24))
   if refresh:draw.point((p['x'],p['y']),fill=(112,184,232))
 if refresh:
  compact=Image.new('RGB',(224,112),(16,24,32));compact.paste(image.crop((0,0,202,112)),(11,0));image=compact
  # Kanto's continent continues west beyond the original regional crop.
  west=ImageDraw.Draw(image)
  west.rectangle((0,0,10,111),fill=(112,184,232))
  mask=Image.new('1',image.size);ImageDraw.Draw(mask).polygon([(0,0),(11,0),(11,38),(8,41),(5,39),(7,34),(4,29),(6,25),(3,20),(5,15),(2,9),(0,7)],fill=1)
  for yy in range(42):
   adjacent=next((image.getpixel((xx,yy)) for xx in range(11,30) if image.getpixel((xx,yy))[1]>image.getpixel((xx,yy))[0] and image.getpixel((xx,yy))[2]<80),(24,112,0))
   for xx in range(12):
    if mask.getpixel((xx,yy)):image.putpixel((xx,yy),adjacent)
   # Close the two-pixel sea margin inherited from the cropped native atlas.
   shore=next((xx for xx in range(12,19) if image.getpixel((xx,yy))[1]>image.getpixel((xx,yy))[0] and image.getpixel((xx,yy))[2]<80),None)
   if shore is not None and mask.getpixel((11,yy)):
    for xx in range(11,shore):image.putpixel((xx,yy),image.getpixel((shore,yy)))
  for point in points:point['x']+=11
  for c in connections:c['start'][0]+=11;c['end'][0]+=11
  panels={k:(x+11,y,w,h) for k,(x,y,w,h) in panels.items()}
 # Palette-indexed native tiles, not a mock overlay in the browser.
 colors=[(16,24,32),(112,184,232),(48,104,176),(24,112,0),(48,152,0),(80,200,0),(120,224,0),(184,240,64),(216,248,112),(184,120,8),(224,168,16),(248,208,56),(248,232,136),(248,72,24),(248,248,240),(96,80,72)]
 pal=[v for c in colors for v in c];palette_image=Image.new('P',(1,1));palette_image.putpalette(pal+[0]*(768-len(pal)))
 quant=image.quantize(palette=palette_image,dither=Image.Dither.NONE)
 tiles=[bytes(32)];lookup={tiles[0]:0};tilemap=[0]*1024
 for ty in range(14):
  for tx in range(28):
   tile=bytearray()
   for yy in range(8):
    for xx in range(0,8,2):tile.append(quant.getpixel((tx*8+xx,ty*8+yy))|(quant.getpixel((tx*8+xx+1,ty*8+yy))<<4))
   tile=bytes(tile)
   if tile not in lookup:lookup[tile]=len(tiles);tiles.append(tile)
   tilemap[(ty+3)*32+tx+1]=lookup[tile]
 palette=[(pal[i]>>3)|((pal[i+1]>>3)<<5)|((pal[i+2]>>3)<<10) for i in range(0,48,3)]
 def array(name,vals,ctype):return 'static const '+ctype+' '+name+'[] = {'+','.join(str(v) for v in vals)+'};\n'
 body=array('sWorldTiles',b''.join(tiles),'u8')+array('sWorldTilemap',tilemap,'u16')+array('sWorldPalette',palette,'u16')
 body+='static const struct JourneyWorldPoint sWorldPoints[] = {\n'+''.join('    {(MAP_GROUP('+p['id']+')<<8)|MAP_NUM('+p['id']+'), '+p['section']+', '+str(p['x'])+', '+str(p['y'])+', COMPOUND_STRING("'+p['name'].replace('"','')+'")},\n' for p in points)+'};\n'
 stage('src/data/journey_world_map.h',body);stage('src/journey_world_map.c',asset('tools/hoenn/world_map_screen.c' if refresh else 'tools/hoenn/world_map_screen_base.c'))
 stage('include/journey_world_map.h','#ifndef GUARD_JOURNEY_WORLD_MAP_H\n#define GUARD_JOURNEY_WORLD_MAP_H\n#include "main.h"\nvoid JourneyWorldMapOpen(MainCallback callback);\nu16 JourneyWorldMapPlayerPoint(void);\nvoid CB2_JourneyWorldMap(void);\nvoid JourneyWorldMapOpenFly(void);\nbool8 JourneyWorldFlyAllowed(u16 map, u16 section);\nvoid JourneyWorldFlyDestination(u16 map, u16 section);\n#endif\n')
 if not refresh:
  p='src/field_region_map.c';body=read(p).decode();a=body.index('void FieldInitRegionMap(MainCallback callback)');b=body.index('\nstatic void MCB2_InitRegionMapRegisters(void)\n{',a)
  body=body[:a]+'void FieldInitRegionMap(MainCallback callback)\n{\n    JourneyWorldMapOpen(callback);\n}\n'+body[b:];body=body.replace('#include "global.h"','#include "global.h"\n#include "journey_world_map.h"',1);stage(p,body)
  p='src/start_menu.c';body=read(p).decode().replace('#include "global.h"','#include "global.h"\n#include "journey_world_map.h"',1)
  body=body.replace('    MENU_ACTION_DEXNAV,','    MENU_ACTION_DEXNAV,\n    MENU_ACTION_WORLD_MAP,',1)
  body=body.replace('static bool8 StartMenuPokeNavCallback(void);','static bool8 StartMenuPokeNavCallback(void);\nstatic bool8 StartMenuWorldMapCallback(void);',1)
  body=body.replace('static const u8 sText_MenuDebug[] = _("DEBUG");','static const u8 sText_MenuDebug[] = _("DEBUG");\nstatic const u8 sText_WorldMap[] = _("MAP");',1)
  body=body.replace('    [MENU_ACTION_POKENAV]','    [MENU_ACTION_WORLD_MAP] = {sText_WorldMap, {.u8_void = StartMenuWorldMapCallback}},\n    [MENU_ACTION_POKENAV]',1)
  a=body.index('static void BuildNormalStartMenu(void)\n{');b=body.index('\nstatic void BuildDebugStartMenu',a)
  section=body[a:b].replace('    AddStartMenuAction(MENU_ACTION_BAG);','    AddStartMenuAction(MENU_ACTION_BAG);\n    AddStartMenuAction(MENU_ACTION_WORLD_MAP);',1).replace('    AddStartMenuAction(MENU_ACTION_EXIT);','    // B still closes the menu; keep the native nine-row capacity.')
  body=body[:a]+section+body[b:]
  a=body.index('static bool8 StartMenuPokeNavCallback(void)\n{');b=body.index('\nstatic bool8 StartMenuPlayerNameCallback',a)
  callback=body[a:b].replace('StartMenuPokeNavCallback','StartMenuWorldMapCallback').replace('SetMainCallback2(CB2_InitPokeNav);  // Display PokéNav','JourneyWorldMapOpen(CB2_ReturnToFieldWithOpenMenu);')
  stage(p,body[:b]+'\n'+callback+body[b:])
  p='src/pokenav.c';body=read(p).decode().replace('#include "global.h"','#include "global.h"\n#include "journey_world_map.h"',1)
  old='        if (menuId == POKENAV_MENU_FUNC_EXIT)';assert body.count(old)==1;body=body.replace(old,'        if (menuId == POKENAV_REGION_MAP)\n        {\n            ShutdownPokenav();\n            tState = 6;\n        }\n        else if (menuId == POKENAV_MENU_FUNC_EXIT)')
  old='    case 5:\n        if (!WaitForPokenavShutdownFade())';assert body.count(old)==1;body=body.replace(old,'    case 6:\n        if (!WaitForPokenavShutdownFade())\n        {\n            FreeMenuHandlerSubstruct1();\n            FreePokenavResources();\n            DestroyTask(taskId);\n            JourneyWorldMapOpen(CB2_InitPokeNav);\n        }\n        break;\n    case 5:\n        if (!WaitForPokenavShutdownFade())');stage(p,body)
 if refresh:
  flag='FLAG_JOURNEY_LAVENDER_PORT_VISITED'
  p='include/constants/flags.h';body=read(p).decode();assert '0x1B39' not in body;stage(p,body+'\n#define '+flag+' 0x1B39\n')
  p='data/maps/JourneyRoute12Shipyard/scripts.inc';body=read(p).decode();old='JourneyRoute12Shipyard_MapScripts::\n\t.byte 0';assert old in body;stage(p,body.replace(old,'JourneyRoute12Shipyard_MapScripts::\n\tmap_script MAP_SCRIPT_ON_LOAD, JourneyShipyard_Visit\n\t.byte 0\nJourneyShipyard_Visit::\n\tsetflag '+flag+'\n\tend',1))
  p='src/region_map.c';body=read(p).decode().replace('#include "global.h"','#include "global.h"\n#include "journey_world_map.h"',1)
  body=body.replace('void CB2_OpenFlyMap(void)\n{','void CB2_OpenFlyMap(void)\n{\n    JourneyWorldMapOpenFly();\n    return;',1)
  body+='\nbool8 JourneyWorldFlyAllowed(u16 map, u16 section)\n{\n    if (map == ((MAP_GROUP(MAP_JOURNEYROUTE12SHIPYARD)<<8)|MAP_NUM(MAP_JOURNEYROUTE12SHIPYARD)))\n        return FlagGet('+flag+');\n    if (section >= MAPSEC_COUNT) return FALSE;\n    if (map != ((sMapHealLocations[section][0]<<8)|sMapHealLocations[section][1])) return FALSE;\n    return GetMapsecType(section) == MAPSECTYPE_CITY_CANFLY || GetMapsecType(section) == MAPSECTYPE_BATTLE_FRONTIER;\n}\n\nvoid JourneyWorldFlyDestination(u16 map, u16 section)\n{\n    struct RegionMap regionMap = {0};\n    if (map == ((MAP_GROUP(MAP_JOURNEYROUTE12SHIPYARD)<<8)|MAP_NUM(MAP_JOURNEYROUTE12SHIPYARD)))\n        SetWarpDestination(MAP_GROUP(MAP_JOURNEYROUTE12SHIPYARD), MAP_NUM(MAP_JOURNEYROUTE12SHIPYARD), WARP_ID_NONE, 24, 39);\n    else\n    {\n        regionMap.mapSecId = section;\n        regionMap.posWithinMapSec = 1;\n        SetFlyDestination(&regionMap);\n    }\n}\n'
  stage(p,body)
 for p in (['src/region_map.c'] if not refresh else [])+['src/journey_campaign_gates.c','src/journey_gym_scaling.c','src/journey_family.c','data/layouts/JourneyRoute12Shipyard/map.bin']:read(p)
 r=dict(layer=layer,points=points,connections=connections,tiles=len(tiles),panels={k:list(v) for k,v in panels.items()},field_map=True,pokenav_map=True,real_player_position=True,fly_engine_preserved=not refresh,integrated_fly=refresh,lavender_and_sevii_fly=refresh,caves_not_fly_destinations=refresh,asset_sha256=assets,original_sha256=originals,preserved_native_sha256=preserved,prepared_sha256={p:hashlib.sha256(v).hexdigest() for p,v in outputs.items()})
 for p,v in outputs.items():(source/p).parent.mkdir(parents=True,exist_ok=True);(source/p).write_bytes(v)
 marker.write_text(json.dumps(r,indent=2)+'\n')
 gallery=ROOT/'mods/hoenn/world-map-gallery';gallery.mkdir(parents=True,exist_ok=True);quant.convert('RGB').resize((896,448),Image.Resampling.NEAREST).save(gallery/'world-map-art.png')
 return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);print(json.dumps(prepare(p.parse_args().source),indent=2))
