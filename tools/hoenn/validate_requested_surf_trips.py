"""Sail the requested Kanto/western Hoenn paths using native controller input.

Initial party, story/defeated flags and one departure placement are fixtures.
No player coordinates, map destinations or battle outcomes are written during
the trip. Surf, disembarking, map transitions and save/Continue are native.
"""
import hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_team_missions.py').read_text().split('\nassert pending(True) == 7')[0]
exec(compile(bootstrap,__file__,'exec'))
profile=args.output.name
PROFILES={
 'pallet-cinnabar-fuchsia':dict(start=('PalletTown_Frlg',10,10),legs=[('Route21_North_Frlg',12,25),('Route21_South_Frlg',12,25),('CinnabarIsland_Frlg',9,10),('Route20_Frlg',58,16),('Route19_Frlg',12,40),('FuchsiaCity_Frlg',30,30)]),
 'petalburg-dewford':dict(start=('Route104',12,56),legs=[('Route105',20,40),('Route106',20,10),('DewfordTown',10,10)]),
 'western-river-dewford':dict(start=('Route114',2,16),legs=[('JourneyWestRiver',24,7),('JourneyRustboroCoast',24,35),('JourneyDewfordCoast',24,40),('JourneyDewfordGate',6,12),('Route105',5,42),('Route106',20,10),('DewfordTown',10,10)]),
 'rustboro-dewford':dict(start=('RustboroCity',9,15),legs=[('Route115',3,35),('JourneyRustboroGate',6,12),('JourneyRustboroCoast',40,35),('JourneyDewfordCoast',40,40),('JourneyDewfordGate',6,12),('Route105',5,42),('Route106',20,10),('DewfordTown',10,10)],extra_maps=['Route104','PetalburgWoods']),
}
plan=PROFILES[profile];names=sorted({p[0] for p in [plan['start']]+plan['legs']+plan.get('return_legs',[])}|set(plan.get('extra_maps',[])))
allowed=set();walk_prefix=profile;walk_cache_paths=True
native('VarSet',0x40FE,7)
rawflag(lib.read16(s['gBadgeFlags'])-7,True)
for tid in range(1,1589):rawflag(0x500+tid,True)
native('ScriptSetMonMoveSlot',0,57,1)
native('AddBagItem',102,999);native('AddBagItem',116,999)
native('VarSet',0x4021,65535);native('VarSet',0x4120,65535)
exec(compile((ROOT/'tools/hoenn/native_water_walk.py').read_text(),'native-controller-walker','exec'))
# Keep doors outside the itinerary out of the planner. All other collisions,
# elevations and currents are observed by the native walker.
def usable(name,x,y,water=None):
 w,h,tiles=blocks[name];i=y*w+x
 return 0<=x<w and 0<=y<h and i in passable[name] and not tiles[i]&0xC00 and (x,y) not in warps[name] and (water is None or water_behaviors[behaviors[name][i]]==water)
def choose(target):
 name,x,y=target;w,h,_=blocks[name]
 water=maps[name]['map_type']=='MAP_TYPE_OCEAN_ROUTE' or name.startswith('Route') and name not in ['Route104','Route114']
 _,yy,xx=min((abs(xx-x)+abs(yy-y),yy,xx) for yy in range(1,h-1) for xx in range(1,w-1) if usable(name,xx,yy,water))
 return name,xx,yy
goals=[choose(p) for p in plan['legs']]
name,x,y=plan['start'];g,num=map_id(name)
assert usable(name,x,y),(profile,'Initial tile is blocked or a doorway',x,y)
script(b'\x39'+bytes([g,num,255])+struct.pack('<HH',x,y)+b'\x27\x6b\x02',frames=240)
step(60);assert idle() and location()==(g,num) and position()==(x,y),(profile,position())
if water_behaviors[behaviors[name][y*blocks[name][0]+x]]:native('SetPlayerAvatarTransitionFlags',8);step(30)
initial=(name,x,y);markers=[];arrivals=[]
def marker():
 p=native('JourneyWorldMapPosition');return[p&255,p>>8]
markers.append(dict(map=name,tile=[x,y],marker=marker()))
def walk_observer(before,after):
 p=marker();previous=markers[-1]
 delta=max(abs(a-b) for a,b in zip(p,previous['marker']))
 # A walking step or a border crossing must not jump across the world chart.
 assert delta<=2,('Map marker jumped during controller movement',before,after,previous,p)
 markers.append(dict(map=after[0],tile=list(after[1:]),marker=p,seam=before[0]!=after[0]))
return_goals=[choose(p) for p in plan['return_legs']] if 'return_legs' in plan else list(reversed(goals[:-1]))+[initial]
for direction,route in [('outbound',goals),('return',return_goals)]:
 for target in route:
  walk(target);picture(direction+'-'+target[0]);arrivals.append(dict(direction=direction,map=target[0],tile=list(position()),marker=markers[-1]['marker']))
  print(profile,direction,'arrived',target,flush=True)
assert (by_location[location()],*position())==initial
# Save while standing at the returned departure, then continue normally.
before=(location(),position(),lib.read8(s['gPlayerAvatar'])&25)
assert native('TrySavingData',0,max_frames=6000)==1
assert native('LoadGameSave',0,max_frames=6000)==1
lib.write32(s['gMain']+4,s['CB2_ContinueSavedGame']|1);step(1500);finish()
assert before==(location(),position(),lib.read8(s['gPlayerAvatar'])&25)
picture('saved-return')
lib.stop()
(args.output/(profile+'.json')).write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),profile=profile,arrivals=arrivals,transitions=transitions,walked_tiles=walked,marker_samples=markers,surf_prompts=surf_prompts,controller_roundtrip=True,no_midroute_warps_or_coordinate_writes=True,save_continue_preserves_location=True,initial_party_flags_and_position_are_fixtures=True,trainer_battles_and_balance_not_tested=True),indent=2)+'\n')
print('Controller roundtrip passed:',profile,walked,'tiles',len(transitions),'transitions',flush=True)
