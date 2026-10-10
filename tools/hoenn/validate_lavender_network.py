"""Native captain menus and a full network cycle; campaign setup is a fixture."""
from pathlib import Path
import hashlib,json,re
from prepare_lavender_network import PORTS
ROOT=Path(__file__).resolve().parents[2]
prefix=(ROOT/'tools/hoenn/validate_eastern_union.py').read_text().split('exec(compile((ROOT/')[0]
prefix=prefix.replace("names=[r['map'] for r in report['rectangles']]", "names=[r['map'] for r in report['rectangles']]+"+repr([p[0] for p in PORTS]+['Route104_MrBrineysHouse']))
exec(compile(prefix,str(ROOT/'tools/hoenn/validate_eastern_union.py'),'exec'))
def warp(name,x,y):
 g,n=map_id(name);script(b'\x39'+bytes([g,n,255])+struct.pack('<HH',x,y)+b'\x27\x6b\x02',frames=240)
 for _ in range(60):
  if idle():break
  step(8)
 assert idle() and location()==(g,n) and position()==(x,y)
network=json.loads((source/'.journey-lavender-network').read_text())
getter=s['Menu_GetCursorPos'];ldr=lib.read16(getter);assert ldr&0xF800==0x4800
cursor=lib.read32(((getter+4)&~3)+(ldr&255)*4)+2

def menu():return task('Task_HandleMultichoiceInput')
def await_menu():
 for _ in range(500):
  if menu():return
  press(1)
 raise AssertionError(('No ferry menu',location(),position()))
def choose(i):
 step(16)
 for _ in range(16):
  if lib.read8(cursor)==i:break
  press(64 if lib.read8(cursor)>i else 128)
 assert lib.read8(cursor)==i,(i,lib.read8(cursor));press(1)
def choices():
 tid=next(i for i in range(16) if lib.read8(s['gTasks']+i*40+4) and lib.read32(s['gTasks']+i*40)&~1==s['Task_HandleMultichoiceInput'])
 mid=lib.read16(s['gTasks']+tid*40+8+14);info=s['sMultichoiceLists']+mid*8;count=lib.read8(info+4);items=lib.read32(info)
 labels=[]
 for i in range(count):
  ptr=lib.read32(items+i*8);label=''
  for offset in range(40):
   v=lib.read8(ptr+offset)
   if v==255:break
   label+=' ' if v==0 else chr(ord('A')+v-0xBB) if 0xBB<=v<=0xD4 else '?'
  labels.append(label)
 return labels

def talk(origin):
 name,_,_,npc,arrival=PORTS[origin]
 assert location()==map_id(name) and position()==arrival,(origin,location(),position(),arrival)
 dx,dy=npc[0]-arrival[0],npc[1]-arrival[1];assert abs(dx)+abs(dy)==1
 step(4,{(-1,0):32,(1,0):16,(0,-1):64,(0,1):128}[(dx,dy)]);step(20);press(1);await_menu()
 if choices()==['WORLD PORTS','LOCAL SERVICES','CANCEL']:choose(0);await_menu()
def travel(origin,destination):
 talk(origin);picture(f'port-{origin}-regions')
 region=PORTS[destination][2];choose(['KANTO','HOENN','SEVII'].index(region));await_menu()
 if region=='HOENN':
  choose(2 if destination==15 else 0 if destination in [1,9,12,13] else 1)
  if destination==15:row=None
  else:
   await_menu();region='HOENN_WEST' if destination in [1,9,12,13] else 'HOENN_EAST'
 if destination!=15:row=next(m for m in network['menus'] if m['origin']==origin and m['region']==region)
 if row:assert origin not in row['destinations']
 picture(f'port-{origin}-destinations')
 if row:choose(row['destinations'].index(destination))
 saw_scene=False;scene_frames=0
 for _ in range(500):
  if task('Task_Seagallop_1'):
   saw_scene=True;scene_frames+=1
   if scene_frames==8:picture(f'port-{origin}-voyage')
  if location()==map_id(PORTS[destination][0]) and idle():break
  if task('Task_Seagallop_1'):step(8)
  else:press(1)
 assert saw_scene and scene_frames>=5,(origin,destination,'Missing native boat animation',scene_frames)
 return_animation=dict(origin=origin,destination=destination,scene_observations=scene_frames)
 assert location()==map_id(PORTS[destination][0]) and position()==PORTS[destination][4],(origin,destination,location(),position())
 x,y=position();assert native('MapGridGetCollisionAt',x+7,y+7)==0
 behavior=native('MapGridGetMetatileBehaviorAt',x+7,y+7)
 assert not native('MetatileBehavior_IsSurfableWaterOrUnderwater',behavior),(destination,'Arrival is water')
 picture(f'port-{destination}-arrival')
 return return_animation
self_audits=[]
def audit_current(origin):
 talk(origin);region=PORTS[origin][2];choose(['KANTO','HOENN','SEVII'].index(region));await_menu()
 if region=='HOENN' and origin!=15:
  choose(0 if origin in [1,9,12,13] else 1);await_menu()
 labels=choices();assert PORTS[origin][1] not in labels,(origin,labels)
 self_audits.append(dict(origin=origin,current=PORTS[origin][1],native_labels=labels))
 press(2);await_menu();press(2);finish()
sections=[x['id'] for x in json.loads((source/'src/data/region_map/region_map_sections.json').read_text())['map_sections']]
assert native('GetRegionMapType',sections.index('MAPSEC_LAVENDER_PORT'))==native('GetRegionMapType',sections.index('MAPSEC_ROUTE_12'))
# World transport is early. Frontier's pre-existing native prerequisites are fixtures.
champion_flag=abi[111]-0x2A+4;scott_flag=flag_id('FLAG_MET_SCOTT_ON_SS_TIDAL')
ticket=int(re.search(r'^\s*ITEM_SS_TICKET\s*=\s*(\d+)',(source/'include/constants/items.h').read_text(),re.M)[1])
warp(PORTS[0][0],*PORTS[0][4]);native('SetPlayerAvatarTransitionFlags',1);step(30)
frontier_guards=[]
for champion,has_ticket,scott in [(False,False,False),(False,True,True),(True,False,True),(True,True,False)]:
 native('FlagSet' if champion else 'FlagClear',champion_flag);native('FlagSet' if scott else 'FlagClear',scott_flag)
 while native('CheckBagHasItem',ticket,1):assert native('RemoveBagItem',ticket,1)
 assert not native('CheckBagHasItem',ticket,1)
 if has_ticket:assert native('AddBagItem',ticket,1)
 assert bool(native('CheckBagHasItem',ticket,1))==has_ticket
 print('Frontier guard:',champion,has_ticket,scott,flush=True)
 talk(0);choose(1);await_menu();choose(2);await_menu()
 assert choices()==['KANTO','HOENN','SEVII ISLANDS','CANCEL'] and location()==map_id(PORTS[0][0]) and position()==PORTS[0][4]
 frontier_guards.append(dict(champion=champion,ticket=has_ticket,scott=scott,blocked=True));press(2);finish()
native('FlagSet',champion_flag);native('FlagSet',scott_flag);assert native('AddBagItem',ticket,1)
trips=[]
for origin in range(len(PORTS)):
 audit_current(origin);destination=(origin+1)%len(PORTS);trips.append(travel(origin,destination))
 print('World ferry:',PORTS[origin][1],'->',PORTS[destination][1],flush=True)
assert native('TrySavingData',0,max_frames=6000)==1;step(60)
assert native('LoadGameSave',0,max_frames=6000)==1
lib.write32(s['gMain']+4,s['CB2_ContinueSavedGame']|1);step(1500);finish()
assert location()==map_id(PORTS[0][0]) and position()==PORTS[0][4];picture('lavender-return-continue')
# Also exercise the unchanged native destination branch in both directions.
# Script entry is a fixture; sailing and the destination warp are native.
legacy_trips=[]
for origin,dest,name,xy in [(0,1,PORTS[2][0],(8,5)),(1,0,PORTS[14][0],(23,32))]:
 native('VarSet',0x8004,origin);native('VarSet',0x8006,dest)
 script(b'\x05'+struct.pack('<I',s['EventScript_SetSail']),frames=1)
 observed=0
 for _ in range(2000):
  if task('Task_Seagallop_1'):observed+=1
  if location()==map_id(name) and idle():break
  step(8)
 assert observed>=5 and location()==map_id(name) and position()==xy,(origin,dest,observed,location(),position())
 legacy_trips.append(dict(origin=origin,destination=dest,map=name,position=list(xy),scene_observations=observed))
 picture(f'legacy-seagallop-{origin}-{dest}')
lib.stop()
(args.output/'lavender-network.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),trips=trips,frontier_guards=frontier_guards,self_audits=self_audits,legacy_seagallop_trips=legacy_trips,legacy_script_entry_is_fixture=True,all_ports_visited=True,all_world_voyages_animated=True,lavender_region_map_is_kanto=True,actual_captain_interactions=True,actual_menu_choices=True,current_port_excluded=True,no_midtrip_fixture_warps=True,all_arrivals_on_walkable_dry_tiles=True,save_continue=True,initial_party_and_trainer_flags_are_fixtures=True,frontier_championship_ticket_and_scott_flags_are_fixtures=True,full_campaign_playthrough=False),indent=2)+'\n')
