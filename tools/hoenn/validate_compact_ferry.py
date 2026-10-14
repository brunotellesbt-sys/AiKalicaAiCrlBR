"""Sail Pallet–Route25–Pallet through actual captain menus and native animation."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_trainer_levels.py'),'exec'))
native('VarSet',0x40FE,7)
t=(ROOT/'tools/hoenn/validate_lavender_network.py').read_text();functions='getter='+t.split('getter=',1)[1].split('\ndef talk(origin):',1)[0];exec(compile(functions,'native-ferry-menu-helpers','exec'))
warp('PalletTown_Frlg',12,18);step(60);trips=[]
for name,player,npc,destination,target,landing in [('PalletTown_Frlg',(12,18),(11,18),'CERULEAN PORT','Route25_Frlg',(63,11)),('Route25_Frlg',(63,11),(64,11),'PALLET PORT','PalletTown_Frlg',(12,17))]:
 assert location()==map_id(name) and position()==player,(name,location(),position())
 dx,dy=npc[0]-player[0],npc[1]-player[1];step(4,{(-1,0):32,(1,0):16,(0,-1):64,(0,1):128}[(dx,dy)]);step(20);press(1);await_menu();labels=choices();assert 'KANTO' in labels,labels;choose(labels.index('KANTO'));await_menu();labels=choices();assert destination in labels,labels;picture(name+'-new-destinations');choose(labels.index(destination));seen=0
 for _ in range(500):
  if task('Task_Seagallop_1'):seen+=1;step(8)
  elif location()==map_id(target) and idle():break
  else:press(1)
 assert seen>=5 and location()==map_id(target) and position()==landing,(target,seen,location(),position(),landing)
 x,y=landing;assert native('MapGridGetCollisionAt',x+7,y+7)==0
 assert not native('MetatileBehavior_IsSurfableWaterOrUnderwater',native('MapGridGetMetatileBehaviorAt',x+7,y+7))
 trips.append(dict(origin=name,destination=target,arrival=list(landing),animation_observations=seen));picture(target+'-ferry-arrival')
lib.stop();(args.output/'compact-ferry.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),trips=trips,native_controller_menus=True,native_boat_animation=True,arrivals_on_accessible_dry_pier=True,initial_travel_and_campaign_state_are_fixtures=True),indent=2)+'\n')
