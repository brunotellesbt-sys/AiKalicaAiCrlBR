"""Unify transport menus, omit the current port, and name Lavender Port."""
import argparse,copy,hashlib,json,re
from pathlib import Path
from prepare_route12_port import PRECEDING
LAYER='lavender-network'
CHAIN=PRECEDING+['early-story-tools','mandatory-native-missions','sixteen-badge-leagues','rusturf-reunion','sea-landscapes','eastern-sea-union','ever-grande-entrance','route12-port']
# Stable IDs preserve the earlier ferry's port IDs and its saved origin variable.
PORTS=[('JourneyRoute12Shipyard','LAVENDER PORT','KANTO',(23,39),(24,39)),('SlateportCity_Harbor','SLATEPORT','HOENN',(16,13),(16,14))]
PORTS += [(n+'Island_Harbor_Frlg',n.upper()+' ISLAND','SEVII',(9,5),(8,5)) for n in ['One','Two','Three','Four','Five','Six','Seven']]
PORTS += [('DewfordTown','DEWFORD','HOENN',(13,11),(13,12)),('LilycoveCity_Harbor','LILYCOVE','HOENN',(3,13),(4,13)),('PacifidlogTown','PACIFIDLOG','HOENN',(14,14),(15,14)),('Route104','PETALBURG COAST','HOENN',(15,52),(16,52)),('Route109','SLATEPORT BEACH','HOENN',(22,22),(23,22)),('VermilionCity_Frlg','VERMILION','KANTO',(24,33),(23,33)),('BattleFrontier_OutsideWest','BATTLE FRONTIER','HOENN',(19,68),(20,68)),('MossdeepCity','MOSSDEEP','HOENN',(16,4),(17,4)),('SootopolisCity','SOOTOPOLIS','HOENN',(21,37),(22,37))]

def prepare(source):
 source=Path(source);marker=source/('.journey-'+LAYER)
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in (r['prepared_sha256']|r['preserved_native_sha256']).items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  return r
 expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
 for layer in CHAIN:expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 originals={};preserved={};outputs={}
 def read(p):
  raw=(source/p).read_bytes();h=hashlib.sha256(raw).hexdigest();assert h==expected[p],p;preserved[p]=h;return raw
 def stage(p,v):
  originals[p]=hashlib.sha256(read(p)).hexdigest();preserved.pop(p,None);outputs[p]=v if isinstance(v,bytes) else v.encode()
 def enc(x):return json.dumps(x,indent=2)+'\n'
 # JSON is the source of truth for generated region-map constants and entries.
 p='src/data/region_map/region_map_sections.json';d=json.loads(read(p));section=copy.deepcopy(next(x for x in d['map_sections'] if x['id']=='MAPSEC_ROUTE_12'));section.update(id='MAPSEC_LAVENDER_PORT',name='LAVENDER PORT',y=10,height=1);d['map_sections'].append(section);stage(p,enc(d))
 p='include/regions.h';body=read(p).decode();old='if (sectionId >= KANTO_MAPSEC_START && sectionId < MAPSEC_SPECIAL_AREA)';assert body.count(old)==1;stage(p,body.replace(old,'if (sectionId == MAPSEC_LAVENDER_PORT || (sectionId >= KANTO_MAPSEC_START && sectionId < MAPSEC_SPECIAL_AREA))'))
 p='src/map_name_popup.c';body=read(p).decode();old='    if (regionMapSectionId >= KANTO_MAPSEC_START)';assert body.count(old)==1;stage(p,body.replace(old,'    if (regionMapSectionId == MAPSEC_LAVENDER_PORT)\n        regionMapSectionId = 0; // Existing Kanto banner theme.\n    else if (regionMapSectionId >= KANTO_MAPSEC_START)'))
 # The native Seagallop scene normally selects a fixed Sevii landing. A
 # sentinel selects explicit world-network coordinates; native trips stay intact.
 p='src/seagallop.c';body=read(p).decode()
 old='    if (gSpecialVar_0x8006 >= NELEMS(sSeag))\n        gSpecialVar_0x8006 = 0;\n\n    warpInfo = sSeag[gSpecialVar_0x8006];\n    SetWarpDestination(warpInfo[0], warpInfo[1], -1, warpInfo[2], warpInfo[3]);'
 new='    if (gSpecialVar_0x8006 == 0xFFFF)\n    {\n        // World ferry: group, map, x, y supplied by the destination script.\n        SetWarpDestination(gSpecialVar_0x8004, gSpecialVar_0x8005, -1, gSpecialVar_0x8009, gSpecialVar_0x800A);\n    }\n    else\n    {\n        if (gSpecialVar_0x8006 >= NELEMS(sSeag))\n            gSpecialVar_0x8006 = 0;\n        warpInfo = sSeag[gSpecialVar_0x8006];\n        SetWarpDestination(warpInfo[0], warpInfo[1], -1, warpInfo[2], warpInfo[3]);\n    }'
 assert body.count(old)==1;body=body.replace(old,new)
 old='static bool8 GetDirectionOfTravel(void)\n{'
 assert body.count(old)==1;body=body.replace(old,old+'\n    if (gSpecialVar_0x8006 == 0xFFFF)\n        return gSpecialVar_0x8007 ? DIRN_EASTBOUND : DIRN_WESTBOUND;')
 stage(p,body)
 declarations=[];entries=[];ids=[];script=[];menus=[];wrappers=[];changes=[];menu_cache={}
 def menu(name,labels):
  key=tuple(labels)
  if key in menu_cache:return menu_cache[key]
  enum='MULTI_LAVENDER_'+name.upper();menu_cache[key]=enum;ids.append(enum);entries.append(f'    [{enum}] = MULTICHOICE(sLavender{name}),\n')
  declarations.append(f'static const struct MenuAction sLavender{name}[] = {{\n'+''.join('    {COMPOUND_STRING("'+l+'")},\n' for l in labels)+'};\n');return enum
 service=menu('Services',['WORLD PORTS','LOCAL SERVICES','CANCEL'])
 # Separate regional submenus keep each list within the native eight-line limit.
 root=menu('Regions',['KANTO','HOENN','SEVII ISLANDS','CANCEL'])
 script.append('LavenderNetwork_Menu::\n\tmsgbox LavenderNetwork_Where, MSGBOX_DEFAULT\n\tclosemessage\n\tmultichoice 0, 0, '+root+', FALSE\n\tswitch VAR_RESULT\n\tcase 0, LavenderNetwork_KANTO\n\tcase 1, LavenderNetwork_HOENN\n\tcase 2, LavenderNetwork_SEVII\n\tgoto Journey_Ferry_Cancel\n')
 groups={'KANTO':[0,14],'HOENN_WEST':[1,9,12,13],'HOENN_EAST':[10,11,16,17],'SEVII':list(range(2,9))}
 script.append('LavenderNetwork_HOENN::\n\tswitch VAR_0x8008\n'+''.join(f'\tcase {i}, LavenderNetwork_HoennRegions{i}\n' for i in range(len(PORTS)))+'\tgoto Journey_Ferry_Cancel\n')
 for origin in range(len(PORTS)):
  enum=menu('HoennRegions'+str(origin),['WEST COAST','EAST COAST']+(['BATTLE FRONTIER'] if origin!=15 else [])+['BACK'])
  script.append(f'LavenderNetwork_HoennRegions{origin}::\n\tmultichoice 0, 0, {enum}, FALSE\n\tswitch VAR_RESULT\n\tcase 0, LavenderNetwork_HOENN_WEST\n\tcase 1, LavenderNetwork_HOENN_EAST\n'+('\tcase 2, LavenderNetwork_Destination15\n' if origin!=15 else '')+'\tgoto LavenderNetwork_Menu\n')
 for region in groups:
  script.append('LavenderNetwork_'+region+'::\n\tswitch VAR_0x8008\n'+''.join(f'\tcase {i}, LavenderNetwork_{region}_{i}\n' for i in range(len(PORTS)))+'\tgoto Journey_Ferry_Cancel\n')
  for origin in range(len(PORTS)):
   dest=[i for i in groups[region] if i!=origin]
   enum=menu(region+str(origin),[PORTS[i][1] for i in dest]+['BACK'])
   script.append(f'LavenderNetwork_{region}_{origin}::\n\tmultichoice 0, 0, {enum}, FALSE\n\tswitch VAR_RESULT\n'+''.join(f'\tcase {choice}, LavenderNetwork_Destination{i}\n' for choice,i in enumerate(dest))+'\tgoto LavenderNetwork_Menu\n')
   menus.append(dict(origin=origin,region=region,destinations=dest,menu=enum))
 for i,(name,title,region,npc,arrival) in enumerate(PORTS):
  p=f'data/maps/{name}/map.json';m=json.loads(read(p));old=copy.deepcopy(m)
  if i==0:m.update(region_map_section='MAPSEC_LAVENDER_PORT',show_map_name=True)
  target=next((e for e in m['object_events'] if (e['x'],e['y'])==npc),None)
  if target is None:
   target=dict(type='object',graphics_id='OBJ_EVENT_GFX_SAILOR',x=npc[0],y=npc[1],elevation=3,movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',flag='0');m['object_events'].append(target)
  # Always-available world transport, separate from quest-bound Briney appearances.
  original_script=target.get('script','')
  target['script']='Journey_FerryPort'+str(i)
  if '_EventScript_' in original_script:
   wrap=f'LavenderNetwork_Service{i}_{len(wrappers)}';wrappers.append(dict(label=wrap,native=original_script,origin=i));target['script']=wrap
  for e in m['object_events']:
   label=e.get('script','')
   if label=='JourneyBirth_Captain':e['script']='Journey_FerryPort'+str(i)
   elif (label.endswith('_EventScript_Sailor') and 'Island_Harbor' in label) or label.endswith('_EventScript_FerryAttendant') or label in ['VermilionCity_EventScript_FerrySailor','DewfordTown_EventScript_Briney']:
    wrap=f'LavenderNetwork_Service{i}_{len(wrappers)}';wrappers.append(dict(label=wrap,native=label,origin=i));e['script']=wrap
  stage(p,enc(m));changes.append(dict(map=name,npc=list(npc),arrival=list(arrival),origin=i,title=title,region=region,original_events=len(old['object_events'])))
  if i>=9:script.append(f'Journey_FerryPort{i}::\n\tsetvar VAR_0x8008, {i}\n\tgoto Journey_Ferry\n')
  guard=''
  if i==15:
   guard='\tcheckitem ITEM_SS_TICKET\n\tgoto_if_eq VAR_RESULT, FALSE, LavenderNetwork_FrontierLocked\n\tgoto_if_unset FLAG_SYS_GAME_CLEAR, LavenderNetwork_FrontierLocked\n\tgoto_if_unset FLAG_MET_SCOTT_ON_SS_TIDAL, LavenderNetwork_FrontierLocked\n'
  script.append(f'LavenderNetwork_Destination{i}::\n\tgoto_if_eq VAR_0x8008, {i}, Journey_Ferry_AlreadyHere\n'+guard+'\tmsgbox Journey_Ferry_BoardText, MSGBOX_DEFAULT\n\tclosemessage\n'+f'\tsetvar VAR_0x8004, MAP_GROUP({m["id"]})\n\tsetvar VAR_0x8005, MAP_NUM({m["id"]})\n\tsetvar VAR_0x8006, 65535\n\tsetvar VAR_0x8007, {0 if region == "KANTO" else 1}\n\tsetvar VAR_0x8009, {arrival[0]}\n\tsetvar VAR_0x800A, {arrival[1]}\n\tfadescreen FADE_TO_BLACK\n\tspecial DoSeagallopFerryScene\n\twaitstate\n\tend\n')
 # Mr. Briney's cottage and Route109 retain their local voyages as an option.
 for name,label,origin in [('Route104_MrBrineysHouse','Route104_MrBrineysHouse_EventScript_Briney',12),('Route109','Route109_EventScript_MrBriney',13)]:
  p=f'data/maps/{name}/map.json';m=json.loads(outputs[p] if p in outputs else read(p))
  e=next(e for e in m['object_events'] if e['script']==label);wrap='LavenderNetwork_'+name;wrappers.append(dict(label=wrap,native=label,origin=origin));e['script']=wrap;stage(p,enc(m))
 for w in wrappers:
  script.append(w['label']+'::\n\tlock\n\tfaceplayer\n\tmsgbox LavenderNetwork_ServiceText, MSGBOX_DEFAULT\n\tclosemessage\n\tmultichoice 0, 0, '+service+', FALSE\n\tswitch VAR_RESULT\n\tcase 0, '+w['label']+'_World\n\tcase 1, '+w['label']+'_Local\n\trelease\n\tend\n'+w['label']+'_World::\n\trelease\n\tgoto Journey_FerryPort'+str(w['origin'])+'\n'+w['label']+'_Local::\n\trelease\n\tgoto '+w['native']+'\n')
 script.append('LavenderNetwork_Where::\n\t.string "Which region would you like to visit?$"\nLavenderNetwork_ServiceText::\n\t.string "World ports or the local service?$"\nLavenderNetwork_FrontierLocked::\n\tmsgbox LavenderNetwork_FrontierText, MSGBOX_DEFAULT\n\tgoto LavenderNetwork_Menu\nLavenderNetwork_FrontierText::\n\t.string "Use the local S.S. TIDAL service\\n"\n\t.string "for your first FRONTIER visit.\\p"\n\t.string "Become HOENN CHAMPION and bring\\n"\n\t.string "your S.S. TICKET to board.$"\n')
 p='src/data/script_menu.h';body=read(p).decode();body=body.replace('ROUTE 12 YARD','LAVENDER PORT');anchor='static const struct MultichoiceListStruct sMultichoiceLists[] =\n';assert body.count(anchor)==1;body=body.replace(anchor,'\n'.join(declarations)+'\n'+anchor);body=body.replace('sMultichoiceLists[] =\n{\n','sMultichoiceLists[] =\n{\n'+''.join(entries));stage(p,body)
 p='include/constants/script_menu.h';body=read(p).decode();pos=body.index('\n};');assert len(re.findall(r'^\s*MULTI_\w+\s*,',body[:pos],re.M))+len(ids)<255;stage(p,body[:pos]+''.join('\n    '+i+',' for i in ids)+body[pos:])
 p='data/scripts/journey_campaign_gates.inc';body=read(p).decode();a=body.index('Journey_Ferry_Menu::\n');b=body.index('Journey_Ferry_Islands::\n',a);body=body[:a]+'Journey_Ferry_Menu::\n\tgoto LavenderNetwork_Menu\n'+body[b:];stage(p,body+'\n'+'\n'.join(script))
 for p in [f'data/maps/{port[0]}/scripts.inc' for port in PORTS]+['data/maps/Route104_MrBrineysHouse/scripts.inc','src/journey_campaign_gates.c','src/journey_gym_scaling.c','src/journey_pwt.c','data/maps/SSTidalCorridor/scripts.inc','data/maps/SSAnne_CaptainsOffice_Frlg/scripts.inc','data/layouts/JourneyRoute12Shipyard/map.bin','data/maps/Route12_Frlg/scripts.inc']:
  read(p)
 r=dict(layer=LAYER,ports=changes,menus=menus,native_service_wrappers=wrappers,current_port_omitted=True,frontier_first_native_voyage_preserved=True,lavender_port_name=True,all_world_voyages_animated=True,shipyard_terrain_preserved=True,original_sha256=originals,preserved_native_sha256=preserved,prepared_sha256={p:hashlib.sha256(v).hexdigest() for p,v in outputs.items()})
 for p,v in outputs.items():(source/p).write_bytes(v)
 marker.write_text(enc(r));return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);print(json.dumps(prepare(p.parse_args().source),indent=2))
