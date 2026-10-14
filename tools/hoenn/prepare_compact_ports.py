"""Compact moorings with complete coastlines and full hull collision."""
import argparse,copy,hashlib,json,re,struct
from pathlib import Path
from candidate_layer import Layer
from import_native_pier import import_pier
from prepare_visible_crossover import PRIOR,LAYER as PREVIOUS
LAYER='compact-ports';PRIOR=PRIOR+[PREVIOUS];ROOT=Path(__file__).resolve().parents[2]
def prepare(source):
 layer=Layer(source,LAYER,PRIOR)
 if old:=layer.existing():return old
 s=layer.source;layout_data=json.loads((s/'data/layouts/layouts.json').read_text());layouts={l['id']:l for l in layout_data['layouts']};maps={};blocks={};boats=[];ports=[];restored=[]
 def readmap(n):
  if n not in maps:maps[n]=json.loads((s/f'data/maps/{n}/map.json').read_text())
  return maps[n]
 def terrain(n):
  m=readmap(n);l=layouts[m['layout']];p=l['blockdata_filepath']
  if p not in blocks:blocks[p]=list(struct.unpack('<'+'H'*(l['width']*l['height']),(s/p).read_bytes()))
  return l,blocks[p]
 def put(n,x,y,t):
  l,v=terrain(n);assert 0<=x<l['width'] and 0<=y<l['height'],(n,x,y);v[y*l['width']+x]=t
 def npc(x,y,script,gfx='OBJ_EVENT_GFX_SAILOR_FRLG',elevation=3):
  return dict(graphics_id=gfx,x=x,y=y,elevation=elevation,movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',script=script,flag='0')
 def boat(n,x,y,gfx='OBJ_EVENT_GFX_MR_BRINEYS_BOAT'):
  # A 32x32 sprite is centered on x+8, bottom-aligned to y+16:
  # three tile columns and two rows, not just its central object-event cell.
  m=readmap(n);l,v=terrain(n);water=0x112B if l['layout_version']=='frlg' else 0x1170
  if n=='SootopolisCity':water=0x1279
  footprint=[]
  for yy in [y-1,y]:
   for xx in [x-1,x,x+1]:
    original=v[yy*l['width']+xx]
    assert original>>12==1,(n,xx,yy,hex(original),'boat must be on existing water')
    put(n,xx,yy,original|0x400);footprint.append([xx,yy])
  m['object_events'].append(npc(x,y,'JourneyCompactPort_Boat',gfx,1));boats.append(dict(map=n,anchor=[x,y],footprint=footprint,graphics=gfx))
 dock_ids={}
 def frlg_pier(n,x0,x1,y0,y1):
  lo=layouts[readmap(n)['layout']];target=lo['secondary_tileset']
  if target not in dock_ids:
   ids,files=import_pier(s,target,emerald=lo['layout_version']=='emerald',overrides=layer.outputs);dock_ids[target]=ids
   for p,raw in files.items():layer.stage(p,raw)
  for y in range(y0,y1+1):
   for x in range(x0,x1+1):put(n,x,y,0x3000+dock_ids[target][0x2F3 if x==x0 else 0x2F5 if x==x1 else 0x2F4])
 def register(n,pid,title,captain,arrival,anchor):
  m=readmap(n);existing=next((o for o in m['object_events'] if o['script']=='Journey_FerryPort'+str(pid)),None)
  if existing:existing.update(x=captain[0],y=captain[1],elevation=3)
  else:m['object_events'].append(npc(*captain,'Journey_FerryPort'+str(pid),'OBJ_EVENT_GFX_SAILOR_FRLG' if n.endswith('_Frlg') else 'OBJ_EVENT_GFX_SAILOR'))
  ports.append(dict(map=n,id=pid,title=title,captain=list(captain),arrival=list(arrival),boat=list(anchor)))
 # Restore the terrain cut out by the old Cinnabar channel. No land deletion.
 n='CinnabarIsland_Frlg';l,v=terrain(n);baseline=ROOT/'tools/hoenn/data/cinnabar-original.bin';raw=baseline.read_bytes();old=struct.unpack('<'+'H'*(l['width']*l['height']),raw)
 pin=json.loads((s/'.journey-westsea').read_text())['original_sha256'][l['blockdata_filepath']];assert hashlib.sha256(raw).hexdigest()==pin,'Unexpected pre-channel Cinnabar donor'
 for y in range(14,20):
  for x in range(8,16):
   i=y*l['width']+x
   if old[i]>>12==3 or old[i]&1023 in [0x121,0x122,0x123,0x124,0x12A,0x12C,0x130,0x131]:v[i]=old[i];restored.append([x,y])
 # Copy a complete five-by-four native house, with its exact door position.
 moss_before=struct.unpack('<3200H',(ROOT/'tools/hoenn/data/mossdeep-before-dock.bin').read_bytes())
 house=[moss_before[(6+dy)*80+26+dx] for dy in range(4) for dx in range(5)]
 houseids,files=import_pier(s,layouts[readmap(n)['layout']]['secondary_tileset'],donor='gTileset_Mossdeep',mids=sorted({v&1023 for v in house}),donor_emerald=True)
 for p,raw in files.items():layer.stage(p,raw)
 for dy in range(4):
  for dx in range(5):
   v=house[dy*5+dx];put(n,17+dx,12+dy,(v&~1023)|houseids[v&1023])
 lodge=copy.deepcopy(json.loads((s/'data/maps/JourneyRoute12SailorsLodge/map.json').read_text()));lodge.update(id='MAP_JOURNEYCINNABARSAILORSLODGE',name='JourneyCinnabarSailorsLodge',region_map_section='MAPSEC_CINNABAR_ISLAND',object_events=[npc(5,4,'JourneyShipyard_LodgeKeeper',elevation=4)],bg_events=[],coord_events=[])
 for warp in lodge['warp_events']:warp.update(dest_map=readmap(n)['id'],dest_warp_id=str(len(readmap(n)['warp_events'])))
 readmap(n)['warp_events'].append(dict(x=19,y=15,elevation=3,dest_map=lodge['id'],dest_warp_id='1'));maps[lodge['name']]=lodge
 frlg_pier(n,19,20,16,17);boat(n,22,17);register(n,19,'CINNABAR PORT',(19,17),(19,16),(22,17))
 # Pallet: preserve the native south shore; a narrow eastern-side jetty.
 n='PalletTown_Frlg';frlg_pier(n,11,12,17,18);boat(n,9,19);register(n,18,'PALLET PORT',(11,18),(12,17),(9,19))
 # Fuchsia: western part of Route19 beach, well away from the sign.
 n='Route19_Frlg';l,v=terrain(n)
 for x,y in [(5,11),(1,22)]:
  for dy in range(2):
   for dx in range(2):put(n,x+dx,y+dy,0x112B)
 # A horizontal walkway from existing sand; a short finger into the sea.
 frlg_pier(n,7,10,12,13);frlg_pier(n,7,8,14,17);boat(n,5,17);register(n,20,'FUCHSIA PORT',(7,16),(8,15),(5,17))
 # Route25: farther east of Bill, local blocked inlet only, never a Surf exit.
 n='Route25_Frlg'
 for yy in range(9,17):
  for xx in range(63,70):put(n,xx,yy,0x152B)
 frlg_pier(n,61,65,10,11);boat(n,65,13);register(n,21,'CERULEAN PORT',(64,11),(63,11),(65,13))
 l,v=terrain(n)
 for y in range(9,17):
  for x in range(63,70):
   if not (10<=y<=11 and 61<=x<=65) and [x,y] not in boats[-1]['footprint']:put(n,x,y,0x152B)
 # Mossdeep: native west island restored; house and small pier on south coast.
 n='MossdeepCity';m=readmap(n);m['object_events']=[o for o in m['object_events'] if o['graphics_id']!='OBJ_EVENT_GFX_MR_BRINEYS_BOAT'];l,v=terrain(n)
 native=(ROOT/'tools/hoenn/data/mossdeep-before-dock.bin').read_bytes();old=struct.unpack('<'+'H'*(len(native)//2),native)
 for y in range(20,31):
  for x in range(15):put(n,x,y,old[y*l['width']+x])
 for dy in range(4):
  for dx in range(5):put(n,2+dx,26+dy,old[(6+dy)*l['width']+26+dx])
 # Native house exterior, its matching door warp and a boatman's interior.
 moss_lodge=copy.deepcopy(json.loads((s/'data/maps/MossdeepCity_House1/map.json').read_text()));moss_lodge.update(id='MAP_JOURNEYMOSSDEEPSAILORSLODGE',name='JourneyMossdeepSailorsLodge',object_events=[npc(4,4,'JourneyShipyard_LodgeKeeper','OBJ_EVENT_GFX_SAILOR',3)],bg_events=[],coord_events=[])
 for warp in moss_lodge['warp_events']:warp.update(dest_map=m['id'],dest_warp_id=str(len(m['warp_events'])))
 m['warp_events'].append(dict(x=4,y=29,elevation=0,dest_map=moss_lodge['id'],dest_warp_id='0'));maps[moss_lodge['name']]=moss_lodge
 frlg_pier(n,4,5,30,31);boat(n,5,33);register(n,16,'MOSSDEEP',(5,30),(4,30),(5,33))
 # Pacifidlog retains its native platforms. Undo the generic added platform.
 n='PacifidlogTown';m=readmap(n);m['object_events']=[o for o in m['object_events'] if o['graphics_id']!='OBJ_EVENT_GFX_MR_BRINEYS_BOAT'];l,v=terrain(n)
 donor=ROOT/'tools/hoenn/data/pacifidlog-before-dock.bin';old=struct.unpack('<'+'H'*(l['width']*l['height']),donor.read_bytes())
 for y in range(25,29):
  for x in range(10,15):put(n,x,y,old[y*l['width']+x])
 # Existing lower footbridge ends at (11,27); moor along its east side.
 boat(n,12,29);register(n,11,'PACIFIDLOG',(11,27),(10,27),(12,29))
 # Shared Sevii harbor: one short complete pier and one small moored ship.
 for island,pid in zip(['One','Two','Three','Four','Five','Six','Seven'],range(2,9)):
  n=island+'Island_Harbor_Frlg';m=readmap(n);l,v=terrain(n);v[:]=[0x112B]*len(v)
  for y in range(0,3):
   for x in range(6,11):put(n,x,y,0x3115)
  frlg_pier(n,7,9,3,8)
  m['object_events']=[o for o in m['object_events'] if not ('SEAGALLOP' in o['graphics_id'] or 'LavenderNetwork_Service' in o['script'] or 'Journey_FerryPort' in o['script'])]
  boat(n,11,8);register(n,pid,island.upper()+' ISLAND',(8,7),(8,6),(11,8))
 # Remove duplicate world-ferry service from Slateport Beach. Briney keeps
 # his distinct original story voyage, without a second world ferry menu.
 n='Route109';m=readmap(n);m['object_events']=[o for o in m['object_events'] if o['script']!='Journey_FerryPort13']
 for o in m['object_events']:
  if o['script']=='LavenderNetwork_Route109':o['script']='Route109_EventScript_MrBriney'
 # Boat hulls elsewhere are collision-marked across their visible footprint.
 for n in ['JourneyRoute12Shipyard']:
  m=readmap(n);l,v=terrain(n)
  for o in m['object_events']:
   if o['graphics_id'] not in ['OBJ_EVENT_GFX_MR_BRINEYS_BOAT','OBJ_EVENT_GFX_SEAGALLOP']:continue
   x,y=o['x'],o['y'];fw,fh=(6,4) if 'SEAGALLOP' in o['graphics_id'] else (3,2)
   for yy in range(y-fh+1,y+1):
    for xx in range(x-fw//2,x+(fw+1)//2):
     if 0<=xx<l['width'] and 0<=yy<l['height']:put(n,xx,yy,0x152B)
 # Append new lodge to existing map group (do not alter existing map numbers).
 p='data/maps/map_groups.json';g=json.loads((s/p).read_text());group=next(k for k in g['group_order'] if 'JourneyRoute12SailorsLodge' in g[k]);g[group].extend([lodge['name'],moss_lodge['name']]);layer.stage(p,json.dumps(g,indent=2)+'\n')
 layer.stage('data/maps/JourneyCinnabarSailorsLodge/scripts.inc','JourneyCinnabarSailorsLodge_MapScripts::\n\t.byte 0\n')
 layer.stage('data/maps/JourneyMossdeepSailorsLodge/scripts.inc','JourneyMossdeepSailorsLodge_MapScripts::\n\t.byte 0\n')
 p='data/event_scripts.s';layer.stage(p,(s/p).read_text()+'\n\t.include "data/maps/JourneyCinnabarSailorsLodge/scripts.inc"\n\t.include "data/maps/JourneyMossdeepSailorsLodge/scripts.inc"\n')
 # Regenerate transport submenus with stable IDs. 13 aliases Slateport and
 # is omitted from lists; new ports use 18..21. Existing local wrappers survive.
 p='data/scripts/journey_campaign_gates.inc';t=(s/p).read_text()
 def arrivals(pid,n,x,y):
  nonlocal t
  label='LavenderNetwork_Destination'+str(pid)+'::';a=t.index(label);b=t.find('\n\n',a);b=len(t) if b<0 else b;part=t[a:b]
  part=re.sub(r'(setvar VAR_0x8009, )\d+',lambda z:z[1]+str(x),part);part=re.sub(r'(setvar VAR_0x800A, )\d+',lambda z:z[1]+str(y),part);t=t[:a]+part+t[b:]
 for port in ports:
  pid=port['id'];n=port['map'];x,y=port['arrival']
  if pid<18:arrivals(pid,n,x,y)
  else:
   ident=readmap(n)['id'];t+=f'\nJourney_FerryPort{pid}::\n\tsetvar VAR_0x8008, {pid}\n\tgoto Journey_Ferry\n\nLavenderNetwork_Destination{pid}::\n\tgoto_if_eq VAR_0x8008, {pid}, Journey_Ferry_AlreadyHere\n\tmsgbox Journey_Ferry_BoardText, MSGBOX_DEFAULT\n\tclosemessage\n\tsetvar VAR_0x8004, MAP_GROUP({ident})\n\tsetvar VAR_0x8005, MAP_NUM({ident})\n\tsetvar VAR_0x8006, 65535\n\tsetvar VAR_0x8007, 0\n\tsetvar VAR_0x8009, {x}\n\tsetvar VAR_0x800A, {y}\n\tfadescreen FADE_TO_BLACK\n\tspecial DoSeagallopFerryScene\n\twaitstate\n\tend\n'
 # Add route25/fuchsia/pallet/cinnabar to Kanto menus and extend origin dispatch.
 titles={0:'LAVENDER PORT',14:'VERMILION',18:'PALLET PORT',19:'CINNABAR PORT',20:'FUCHSIA PORT',21:'CERULEAN PORT'}
 constants=[];declarations=[];entries=[]
 for origin in range(22):
  dest=[i for i in titles if i!=origin];enum=f'MULTI_COMPACT_KANTO_{origin}';constants.append(enum);arr=f'sCompactKanto{origin}';declarations.append('static const struct MenuAction '+arr+'[]={'+','.join('{COMPOUND_STRING("'+titles[i]+'")}' for i in dest)+',{COMPOUND_STRING("BACK")}};\n');entries.append(f'    [{enum}] = MULTICHOICE({arr}),\n')
  label=f'LavenderNetwork_KANTO_{origin}::';body=label+f'\n\tmultichoice 0, 0, {enum}, FALSE\n\tswitch VAR_RESULT\n'+''.join(f'\tcase {j}, LavenderNetwork_Destination{i}\n' for j,i in enumerate(dest))+'\tgoto LavenderNetwork_Menu\n'
  if origin<18:
   a=t.index(label);b=t.index('\n\n',a);t=t[:a]+body+t[b:]
  else:t+='\n'+body
 for label in ['LavenderNetwork_KANTO','LavenderNetwork_HOENN','LavenderNetwork_HOENN_WEST','LavenderNetwork_HOENN_EAST','LavenderNetwork_SEVII']:
  a=t.index(label+'::');b=t.index('\tgoto Journey_Ferry_Cancel',a)
  for pid in range(18,22):t=t[:b]+f'\tcase {pid}, '+('LavenderNetwork_HoennRegions0' if label=='LavenderNetwork_HOENN' else label+'_0' if label!='LavenderNetwork_KANTO' else label+'_'+str(pid))+'\n'+t[b:];b=t.index('\tgoto Journey_Ferry_Cancel',a)
 # Remove the beach entry from existing west-coast choices, preserve back.
 for match in list(re.finditer(r'LavenderNetwork_HOENN_WEST_\d+::.*?(?=\n\n)',t,re.S))[::-1]:
  part=match[0];dest=[int(x) for x in re.findall(r'case \d+, LavenderNetwork_Destination(\d+)',part) if int(x)!=13];origin=int(re.search(r'WEST_(\d+)',part)[1]);enum=f'MULTI_COMPACT_WEST_{origin}';constants.append(enum);arr=f'sCompactWest{origin}';names={1:'SLATEPORT',9:'DEWFORD',12:'PETALBURG COAST'};declarations.append('static const struct MenuAction '+arr+'[]={'+','.join('{COMPOUND_STRING("'+names[i]+'")}' for i in dest)+',{COMPOUND_STRING("BACK")}};\n');entries.append(f'    [{enum}] = MULTICHOICE({arr}),\n');new=f'LavenderNetwork_HOENN_WEST_{origin}::\n\tmultichoice 0, 0, {enum}, FALSE\n\tswitch VAR_RESULT\n'+''.join(f'\tcase {j}, LavenderNetwork_Destination{i}\n' for j,i in enumerate(dest))+'\tgoto LavenderNetwork_Menu';t=t[:match.start()]+new+t[match.end():]
 t+='\nJourneyCompactPort_Boat::\n\tmsgbox JourneyCompactPort_BoatText, MSGBOX_NPC\n\tend\nJourneyCompactPort_BoatText::\n\t.string "A boat moored safely at the pier.$"\n';layer.stage(p,t)
 p='include/constants/script_menu.h';body=(s/p).read_text();pos=body.index('\n};');body=body[:pos]+''.join('\n    '+n+',' for n in constants)+body[pos:];assert len(re.findall(r'^\s*MULTI_\w+\s*,',body,re.M))<255;layer.stage(p,body)
 p='src/data/script_menu.h';body=(s/p).read_text();anchor='static const struct MultichoiceListStruct sMultichoiceLists[] =\n';body=body.replace(anchor,''.join(declarations)+'\n'+anchor).replace('sMultichoiceLists[] =\n{\n','sMultichoiceLists[] =\n{\n'+''.join(entries));layer.stage(p,body)
 p='include/journey_birth_arrivals.h';body=(s/p).read_text()
 for ident,values in [('MAP_MOSSDEEP_CITY',[5,33,4,30]),('MAP_PACIFIDLOG_TOWN',[12,29,10,27])]+[('MAP_'+island.upper()+'_ISLAND_HARBOR',[11,8,8,6]) for island in ['One','Two','Three','Four','Five','Six','Seven']]:body,count=re.subn(r'\{'+ident+r', \d+, \d+, \d+, \d+, TRUE\}',lambda z:'{'+ident+', '+', '.join(map(str,values))+', TRUE}',body);assert count==1,ident
 layer.stage(p,body)
 for n,m in maps.items():layer.stage(f'data/maps/{n}/map.json',json.dumps(m,indent=2)+'\n')
 for p,v in blocks.items():layer.stage(p,struct.pack('<'+'H'*len(v),*v))
 return layer.finish(ports=ports,boats=boats,cinnabar_restored_tiles=restored,cinnabar_pre_channel_sha256=pin,all_ferries_animated=True,route25_surrounding_water_blocked=True,slateport_beach_world_ferry_removed=True,pacifidlog_native_platform_restored=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
